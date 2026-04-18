import streamlit as st
import streamlit.components.v1 as components
import hashlib, json, time
from datetime import datetime

# ─── Supabase ───────────────────────────────────────────────────────────────
try:
    from supabase import create_client, Client
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    DB_OK = True
except Exception as _e:
    DB_OK = False
    supabase = None

# ─── Generator ──────────────────────────────────────────────────────────────
try:
    from generator import (
        run_full_pipeline, test_groq_key, test_goapi_key, test_wordpress,
        fetch_wp_categories, generate_pinterest_pin, fetch_internal_links
    )
    GEN_OK = True
except Exception:
    GEN_OK = False

# ─── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NicheFlow AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
#MainMenu,footer,header,
[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],[data-testid="collapsedControl"],
section[data-testid="stSidebar"]{display:none!important;}
.block-container{padding:0!important;max-width:100%!important;}
.stApp{background:#faf6ef!important;}
iframe{border:none!important;display:block;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "page": "home",          # home | login | signup | dashboard | docs
        "dash_tab": "overview",  # overview | generate | settings | prompts | design | billing | docs
        "user_id": None,
        "user_email": None,
        "user_plan": "basic",
        "settings": {},
        "gen_logs": [],
        "gen_running": False,
        "gen_results": [],
        "wp_categories": [],
        "internal_links": [],
        "auth_error": "",
        "auth_success": "",
        "save_ok": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─────────────────────────────────────────────────────────────────────────────
#  DB HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def db_create_user(email: str, password: str, plan: str = "basic"):
    if not DB_OK: return {"success": False, "error": "Database not connected"}
    try:
        existing = supabase.table("users").select("id").eq("email", email).execute()
        if existing.data:
            return {"success": False, "error": "Email already registered"}
        result = supabase.table("users").insert({
            "email": email,
            "password_hash": hash_password(password),
            "plan": plan
        }).execute()
        user_id = result.data[0]["id"]
        # Create empty settings row
        supabase.table("user_settings").insert({"user_id": user_id}).execute()
        return {"success": True, "user_id": user_id, "plan": plan}
    except Exception as e:
        return {"success": False, "error": str(e)}


def db_login_user(email: str, password: str):
    if not DB_OK: return {"success": False, "error": "Database not connected"}
    try:
        result = supabase.table("users").select("*").eq("email", email).eq(
            "password_hash", hash_password(password)
        ).execute()
        if not result.data:
            return {"success": False, "error": "Invalid email or password"}
        user = result.data[0]
        return {"success": True, "user_id": user["id"], "email": user["email"], "plan": user.get("plan","basic")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def db_load_settings(user_id: str) -> dict:
    if not DB_OK or not user_id: return {}
    try:
        result = supabase.table("user_settings").select("*").eq("user_id", user_id).execute()
        if result.data:
            row = result.data[0]
            s = {}
            for key in ["groq_key","wp_url","wp_password","mj_key","mj_template",
                        "article_prompt","html_structure","card_prompt","pinterest_token",
                        "pinterest_board","pinterest_prompt","publish_status","show_card",
                        "card_clickable","use_images","use_internal_links","max_links",
                        "schedule_days","schedule_time","schedule_timezone",
                        "design_main_color","design_accent_color","design_font_family",
                        "articles_generated","images_created","posts_published","pins_posted"]:
                if key in row and row[key] is not None:
                    s[key] = row[key]
            return s
        return {}
    except Exception as e:
        return {}


def db_save_settings(user_id: str, settings: dict) -> bool:
    if not DB_OK or not user_id: return False
    try:
        existing = supabase.table("user_settings").select("id").eq("user_id", user_id).execute()
        payload = {"user_id": user_id, **settings, "updated_at": datetime.utcnow().isoformat()}
        if existing.data:
            supabase.table("user_settings").update(payload).eq("user_id", user_id).execute()
        else:
            supabase.table("user_settings").insert(payload).execute()
        return True
    except Exception as e:
        return False


def db_increment_stat(user_id: str, field: str, amount: int = 1):
    if not DB_OK or not user_id: return
    try:
        current = db_load_settings(user_id).get(field, 0) or 0
        db_save_settings(user_id, {field: int(current) + amount})
    except Exception:
        pass


def db_get_plan(user_id: str) -> str:
    if not DB_OK or not user_id: return "basic"
    try:
        r = supabase.table("users").select("plan").eq("id", user_id).execute()
        return r.data[0].get("plan", "basic") if r.data else "basic"
    except: return "basic"


# ─────────────────────────────────────────────────────────────────────────────
#  AUTH ACTIONS
# ─────────────────────────────────────────────────────────────────────────────
def do_login(email, password):
    result = db_login_user(email.strip().lower(), password)
    if result["success"]:
        st.session_state.user_id    = result["user_id"]
        st.session_state.user_email = result["email"]
        st.session_state.user_plan  = result["plan"]
        st.session_state.settings   = db_load_settings(result["user_id"])
        st.session_state.page       = "dashboard"
        st.session_state.dash_tab   = "overview"
        st.session_state.auth_error = ""
    else:
        st.session_state.auth_error = result["error"]


def do_signup(email, password, confirm):
    if password != confirm:
        st.session_state.auth_error = "Passwords do not match"; return
    if len(password) < 6:
        st.session_state.auth_error = "Password must be at least 6 characters"; return
    result = db_create_user(email.strip().lower(), password)
    if result["success"]:
        st.session_state.auth_error   = ""
        st.session_state.auth_success = "Account created! You can now sign in."
        st.session_state.page         = "login"
    else:
        st.session_state.auth_error = result["error"]


def do_logout():
    for key in ["user_id","user_email","user_plan","settings","gen_logs","gen_results","wp_categories","internal_links"]:
        st.session_state[key] = [] if key in ["gen_logs","gen_results","wp_categories","internal_links"] else (None if "id" in key or "email" in key or "plan" in key else {})
    st.session_state.page = "home"


def save_settings_to_db():
    s = st.session_state.settings
    db_save_settings(st.session_state.user_id, s)
    st.session_state.save_ok = True


# ─────────────────────────────────────────────────────────────────────────────
#  HTML SHELL — landing + login + signup + docs (pure HTML pages)
# ─────────────────────────────────────────────────────────────────────────────
LANDING_HTML = """<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>NicheFlow AI</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700;9..144,800;9..144,900&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--cream:#faf6ef;--cream2:#f2e8d4;--gold:#c9892a;--gold2:#e8a83e;--dark:#0f0d09;--dark2:#1c1810;--text:#1a1510;--text2:#5a5040;--text3:#8a7a60;--border:#dfd4bc;}
*{box-sizing:border-box;margin:0;padding:0;}body{font-family:'Outfit',sans-serif;background:var(--cream);color:var(--text);overflow-x:hidden;}
nav{position:sticky;top:0;z-index:999;display:flex;align-items:center;justify-content:space-between;padding:0 5vw;height:66px;background:rgba(250,246,239,0.96);backdrop-filter:blur(14px);border-bottom:1px solid var(--border);}
.nav-logo{font-family:'Fraunces',serif;font-size:21px;font-weight:800;color:var(--text);}
.nav-logo em{color:var(--gold);font-style:normal;}
.nav-links{display:flex;align-items:center;gap:28px;}
.nav-links a{font-size:14px;font-weight:500;color:var(--text2);text-decoration:none;cursor:pointer;transition:color .2s;}
.nav-links a:hover{color:var(--gold);}
.nav-cta{background:var(--dark)!important;color:#fff!important;padding:9px 22px;border-radius:100px;font-weight:600!important;font-size:13px!important;}
.hero{background:linear-gradient(160deg,#fdfaf4 0%,#f5e8cc 55%,#ecdbb8 100%);padding:96px 5vw 80px;text-align:center;border-bottom:1px solid var(--border);}
.hero-badge{display:inline-flex;align-items:center;gap:7px;background:rgba(255,255,255,.7);border:1px solid rgba(201,137,42,.35);color:#8a6020;padding:7px 18px;border-radius:100px;font-size:12.5px;font-weight:600;margin-bottom:28px;}
.hero h1{font-family:'Fraunces',serif;font-size:clamp(46px,8vw,90px);font-weight:900;line-height:1.03;margin-bottom:24px;}
.hero h1 em{font-style:normal;color:var(--gold);}
.hero p{font-size:clamp(15px,1.7vw,19px);color:var(--text2);max-width:580px;margin:0 auto 44px;line-height:1.78;}
.hero-btns{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;}
.btn-primary{background:var(--dark);color:#fff;padding:14px 30px;border-radius:100px;font-size:15px;font-weight:600;border:none;cursor:pointer;font-family:'Outfit',sans-serif;transition:all .2s;}
.btn-primary:hover{background:var(--dark2);transform:translateY(-2px);}
.btn-outline{background:transparent;color:var(--text);padding:14px 30px;border-radius:100px;font-size:15px;font-weight:600;border:1.5px solid var(--border);cursor:pointer;font-family:'Outfit',sans-serif;transition:all .2s;}
.btn-outline:hover{border-color:var(--gold);color:var(--gold);}
.hero-stats{display:flex;flex-wrap:wrap;justify-content:center;gap:clamp(24px,5vw,68px);margin-top:60px;padding-top:48px;border-top:1px solid rgba(0,0,0,.09);}
.stat-num{font-family:'Fraunces',serif;font-size:clamp(32px,4.5vw,48px);font-weight:800;color:var(--gold);}
.stat-lbl{font-size:13px;color:var(--text3);margin-top:5px;font-weight:500;}
.section{padding:clamp(60px,8vw,108px) clamp(24px,6vw,96px);background:var(--cream);}
.section-alt{background:var(--cream2);padding:clamp(60px,8vw,108px) clamp(24px,6vw,96px);}
.section-dark{background:var(--dark);padding:clamp(60px,8vw,108px) clamp(24px,6vw,96px);}
.section-center{text-align:center;}
.eyebrow{font-size:11px;font-weight:700;color:var(--gold);text-transform:uppercase;letter-spacing:3.5px;margin-bottom:14px;display:block;}
.eyebrow-light{color:rgba(201,137,42,.9)!important;}
.section-title{font-family:'Fraunces',serif;font-size:clamp(30px,4.5vw,52px);font-weight:800;line-height:1.12;color:var(--text);margin-bottom:14px;}
.section-title-light{font-family:'Fraunces',serif;font-size:clamp(30px,4.5vw,52px);font-weight:800;line-height:1.12;color:#fdf6e8;margin-bottom:14px;}
.section-sub{font-size:clamp(14px,1.4vw,17px);color:var(--text2);line-height:1.72;margin-bottom:clamp(36px,6vw,68px);max-width:560px;}
.section-sub-light{font-size:clamp(14px,1.4vw,17px);color:rgba(253,246,232,.5);line-height:1.72;margin-bottom:clamp(36px,6vw,68px);max-width:560px;}
.section-center .section-sub,.section-center .section-sub-light{margin-left:auto;margin-right:auto;}
.feat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;}
@media(max-width:900px){.feat-grid{grid-template-columns:1fr 1fr;}}
@media(max-width:560px){.feat-grid{grid-template-columns:1fr;}}
.feat-card{background:#fff;border:1px solid var(--border);border-radius:20px;padding:clamp(22px,3vw,36px);transition:transform .25s,box-shadow .25s,border-color .25s;}
.feat-card:hover{transform:translateY(-4px);box-shadow:0 14px 44px rgba(0,0,0,.07);border-color:rgba(201,137,42,.45);}
.feat-icon{width:50px;height:50px;background:#fff8ec;border:1px solid rgba(201,137,42,.2);border-radius:13px;display:flex;align-items:center;justify-content:center;font-size:22px;margin-bottom:16px;}
.feat-card h3{font-size:15.5px;font-weight:700;margin-bottom:8px;}
.feat-card p{font-size:13.5px;color:var(--text3);line-height:1.76;}
.pricing-grid{display:grid;grid-template-columns:1fr 1fr;gap:22px;max-width:840px;margin:0 auto;}
@media(max-width:640px){.pricing-grid{grid-template-columns:1fr;}}
.plan-card{background:#fff;border:2px solid var(--border);border-radius:26px;padding:clamp(30px,4vw,50px) clamp(26px,3.5vw,42px);text-align:center;transition:transform .25s;}
.plan-card:hover{transform:translateY(-3px);box-shadow:0 14px 44px rgba(0,0,0,.07);}
.plan-card.pro{background:linear-gradient(158deg,#211808,#0f0d09);border-color:rgba(201,137,42,.55);}
.plan-label{font-size:11px;font-weight:700;color:var(--text3);text-transform:uppercase;letter-spacing:2.5px;margin-bottom:16px;}
.plan-card.pro .plan-label{color:rgba(232,168,62,.75);}
.plan-price{font-family:'Fraunces',serif;font-size:clamp(50px,7vw,70px);font-weight:900;color:var(--text);line-height:1;}
.plan-card.pro .plan-price{color:#fff;}
.plan-period{font-size:14px;color:var(--text3);margin-bottom:28px;margin-top:4px;}
.plan-card.pro .plan-period{color:rgba(253,246,232,.4);}
.plan-feat{font-size:13.5px;color:var(--text2);padding:10px 0;border-bottom:1px solid #f0e8d8;text-align:left;}
.plan-card.pro .plan-feat{color:rgba(253,246,232,.8);border-bottom-color:rgba(255,255,255,.07);}
.plan-feat.no{opacity:.5;}
.plan-btn{width:100%;margin-top:26px;padding:13px;border-radius:100px;font-size:14px;font-weight:700;cursor:pointer;border:2px solid var(--dark);background:transparent;color:var(--dark);font-family:'Outfit',sans-serif;transition:all .2s;}
.plan-btn:hover{background:var(--dark);color:#fff;}
.plan-card.pro .plan-btn{background:var(--gold);border-color:var(--gold);color:#fff;}
.steps-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;}
@media(max-width:900px){.steps-grid{grid-template-columns:1fr 1fr;}}
.step-card{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.11);border-radius:20px;padding:clamp(24px,3vw,36px);}
.step-num{font-family:'Fraunces',serif;font-size:clamp(44px,5.5vw,60px);font-weight:900;color:var(--gold);line-height:1;margin-bottom:16px;}
.step-card h4{font-size:16px;font-weight:700;color:#fdf6e8;margin-bottom:9px;}
.step-card p{font-size:13.5px;color:rgba(253,246,232,.5);line-height:1.76;}
.cta-banner{background:var(--dark);border-radius:26px;padding:clamp(52px,7vw,92px) clamp(28px,6vw,80px);text-align:center;margin:0 clamp(14px,4vw,60px) clamp(52px,6vw,80px);}
footer{text-align:center;padding:clamp(36px,5vw,56px);border-top:1px solid var(--border);}
footer .f-logo{font-family:'Fraunces',serif;font-size:21px;font-weight:800;margin-bottom:9px;}
footer p{font-size:13px;color:var(--text3);margin-bottom:3px;}
</style></head><body>
<nav>
  <div class="nav-logo">✦ <em>Niche</em>Flow AI</div>
  <div class="nav-links">
    <a href="#features">Features</a>
    <a href="#pricing">Pricing</a>
    <a href="#how">How It Works</a>
    <a class="nav-cta" onclick="window.parent.postMessage({action:'goto',page:'login'},'*')">Sign In →</a>
  </div>
</nav>
<section class="hero">
  <div class="hero-badge">✦ AI-Powered Content Platform</div>
  <h1>Write Less.<br>Publish More.<br><em>Grow on Autopilot.</em></h1>
  <p>NicheFlow AI writes full SEO articles, generates stunning Midjourney images, publishes to WordPress, and pins to Pinterest — completely automatically. You paste a title. We handle everything.</p>
  <div class="hero-btns">
    <button class="btn-primary" onclick="window.parent.postMessage({action:'goto',page:'signup'},'*')">Get Started Free →</button>
    <button class="btn-outline" onclick="window.parent.postMessage({action:'goto',page:'docs'},'*')">View Documentation</button>
  </div>
  <div class="hero-stats">
    <div><div class="stat-num">3×</div><div class="stat-lbl">Faster Publishing</div></div>
    <div><div class="stat-num">100%</div><div class="stat-lbl">Autopilot Content</div></div>
    <div><div class="stat-num">4</div><div class="stat-lbl">Images Per Article</div></div>
    <div><div class="stat-num">2</div><div class="stat-lbl">Platforms at Once</div></div>
  </div>
</section>
<section class="section" id="features">
  <div class="section-center">
    <span class="eyebrow">Features</span>
    <h2 class="section-title">Everything Your Blog Needs</h2>
    <p class="section-sub">One platform handles your entire content pipeline — from idea to published post.</p>
  </div>
  <div class="feat-grid">
    <div class="feat-card"><div class="feat-icon">✍️</div><h3>AI Article Writer</h3><p>Groq AI writes full long-form SEO articles. Your prompt, your niche, your voice — no defaults forced on you.</p></div>
    <div class="feat-card"><div class="feat-icon">🎨</div><h3>Midjourney Images</h3><p>4 stunning images auto-generated per article. Converted to WebP and uploaded directly to your WordPress media library.</p></div>
    <div class="feat-card"><div class="feat-icon">🌐</div><h3>WordPress Publisher</h3><p>Articles publish directly to your site with images and full formatting. No copy-pasting or manual uploads ever.</p></div>
    <div class="feat-card"><div class="feat-icon">📌</div><h3>Pinterest Auto-Post</h3><p>After every WordPress publish, post optimized Pins using the featured image. Pro plan only.</p></div>
    <div class="feat-card"><div class="feat-icon">🃏</div><h3>Custom Info Cards</h3><p>Add beautifully styled cards to every article — recipe, travel, health, or any niche. Fully customizable.</p></div>
    <div class="feat-card"><div class="feat-icon">🎨</div><h3>Article Design Studio</h3><p>Control your article's colors, fonts, and HTML structure. Every article matches your brand.</p></div>
  </div>
</section>
<section class="section-alt" id="pricing">
  <div class="section-center">
    <span class="eyebrow">Pricing</span>
    <h2 class="section-title">Simple, Honest Pricing</h2>
    <p class="section-sub">No hidden fees. No shared quotas. Cancel anytime.</p>
  </div>
  <div class="pricing-grid">
    <div class="plan-card">
      <div class="plan-label">Basic</div>
      <div class="plan-price">$30</div>
      <div class="plan-period">per month</div>
      <div>
        <div class="plan-feat">✅ AI Article Generation</div>
        <div class="plan-feat">✅ Midjourney Images (4/article)</div>
        <div class="plan-feat">✅ WordPress Auto-Publish</div>
        <div class="plan-feat">✅ Custom Article &amp; Card Prompts</div>
        <div class="plan-feat">✅ Article Design Studio</div>
        <div class="plan-feat">✅ Draft or Live Publishing</div>
        <div class="plan-feat no">✗ Pinterest Auto-Post</div>
      </div>
      <button class="plan-btn" onclick="window.parent.postMessage({action:'goto',page:'signup'},'*')">Get Started →</button>
    </div>
    <div class="plan-card pro">
      <div class="plan-label">Pro · Most Popular</div>
      <div class="plan-price">$40</div>
      <div class="plan-period">per month</div>
      <div>
        <div class="plan-feat">✅ Everything in Basic</div>
        <div class="plan-feat">✅ Pinterest Auto-Post</div>
        <div class="plan-feat">✅ Pinterest Keyword Optimizer</div>
        <div class="plan-feat">✅ Custom Pinterest Prompt</div>
        <div class="plan-feat">✅ Auto Pin from Featured Image</div>
        <div class="plan-feat">✅ Pinterest Post Scheduler</div>
        <div class="plan-feat">✅ Priority Support</div>
      </div>
      <button class="plan-btn" onclick="window.parent.postMessage({action:'goto',page:'signup'},'*')">Get Pro →</button>
    </div>
  </div>
</section>
<section class="section-dark" id="how">
  <div class="section-center">
    <span class="eyebrow eyebrow-light">How It Works</span>
    <h2 class="section-title-light">From Zero to Published in Minutes</h2>
    <p class="section-sub-light" style="margin:0 auto 60px;">No technical skills needed. If you can paste a title, you can use NicheFlow AI.</p>
  </div>
  <div class="steps-grid">
    <div class="step-card"><div class="step-num">01</div><h4>Sign Up &amp; Choose Plan</h4><p>Create your account and pick Basic or Pro.</p></div>
    <div class="step-card"><div class="step-num">02</div><h4>Add Your Credentials</h4><p>Enter your Groq API key, Midjourney key, and WordPress app password once.</p></div>
    <div class="step-card"><div class="step-num">03</div><h4>Write Your Prompts</h4><p>Customize article and card prompts to match your niche voice and audience.</p></div>
    <div class="step-card"><div class="step-num">04</div><h4>Paste Titles &amp; Go</h4><p>Drop in article titles and hit Generate. NicheFlow writes, designs, and publishes.</p></div>
  </div>
</section>
<section class="section">
  <div class="cta-banner">
    <span class="eyebrow eyebrow-light">Start Today</span>
    <h2 class="section-title" style="color:#fdf6e8;">Ready to Automate Your Content?</h2>
    <p class="section-sub" style="color:rgba(253,246,232,.5);margin:0 auto 36px;">Join bloggers who publish more, stress less, and grow faster.</p>
    <button class="btn-primary" style="background:#c9892a;" onclick="window.parent.postMessage({action:'goto',page:'signup'},'*')">Get Started Free →</button>
  </div>
</section>
<footer>
  <div class="f-logo">✦ NicheFlow AI</div>
  <p>AI-powered blog &amp; Pinterest content generator</p>
  <p style="color:#b0a080;margin-top:14px;">© 2026 NicheFlow AI · All rights reserved</p>
</footer>
<script>
window.addEventListener('message',function(e){
  if(e.data&&e.data.action==='goto'){
    window.parent.postMessage(e.data,'*');
  }
});
</script>
</body></html>"""


# ─────────────────────────────────────────────────────────────────────────────
#  MESSAGE LISTENER (receives postMessage from iframe)
# ─────────────────────────────────────────────────────────────────────────────
# We inject a small JS bridge into the Streamlit app
JS_BRIDGE = """
<script>
window.addEventListener('message', function(e) {
    if (e.data && e.data.action === 'goto') {
        const page = e.data.page;
        const form = document.createElement('form');
        form.method = 'GET';
        const inp = document.createElement('input');
        inp.name = '_nf_nav';
        inp.value = page;
        form.appendChild(inp);
        document.body.appendChild(form);
        // Use Streamlit's query param mechanism via URL
        const url = new URL(window.location.href);
        url.searchParams.set('nf_nav', page);
        window.location.href = url.toString();
    }
});
</script>
"""

# Check URL query param for navigation
query_params = st.query_params
if "nf_nav" in query_params:
    nav_target = query_params["nf_nav"]
    if nav_target in ("login", "signup", "docs", "home", "dashboard"):
        if nav_target == "dashboard" and not st.session_state.user_id:
            st.session_state.page = "login"
        else:
            st.session_state.page = nav_target
    st.query_params.clear()
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
#  RENDER HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def card(title, value, icon, color="#c9892a"):
    st.markdown(f"""
    <div style="background:#fff;border:1px solid #dfd4bc;border-radius:14px;padding:20px;text-align:center;">
        <div style="font-size:22px;margin-bottom:8px;">{icon}</div>
        <div style="font-family:'Georgia',serif;font-size:32px;font-weight:800;color:{color};line-height:1;">{value}</div>
        <div style="font-size:11.5px;color:#8a7a60;margin-top:4px;">{title}</div>
    </div>""", unsafe_allow_html=True)


def section_header(title, subtitle=""):
    st.markdown(f"""
    <div style="padding:20px 0 16px 0;border-bottom:1px solid #dfd4bc;margin-bottom:24px;">
        <h1 style="font-family:'Georgia',serif;font-size:22px;font-weight:800;color:#1a1510;margin:0;">{title}</h1>
        {f'<p style="font-size:13px;color:#8a7a60;margin:4px 0 0 0;">{subtitle}</p>' if subtitle else ''}
    </div>""", unsafe_allow_html=True)


def info_box(msg, color="#fff8ec", border="#c9892a", text="#7a5820"):
    st.markdown(f'<div style="background:{color};border-left:4px solid {border};border-radius:0 8px 8px 0;padding:10px 14px;font-size:13px;color:{text};margin-bottom:12px;">{msg}</div>', unsafe_allow_html=True)


def success_box(msg):
    st.markdown(f'<div style="background:#f0faf4;border:1px solid #a4d8b8;color:#1a6e38;border-radius:9px;padding:10px 14px;font-size:13px;margin-bottom:12px;">✅ {msg}</div>', unsafe_allow_html=True)


def error_box(msg):
    st.markdown(f'<div style="background:#fff0f0;border:1px solid #ffd0d0;color:#c03030;border-radius:9px;padding:10px 14px;font-size:13px;margin-bottom:12px;">❌ {msg}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
def render_sidebar():
    s = st.session_state
    plan_label = "Pro Plan · $40/mo" if s.user_plan == "pro" else "Basic Plan · $30/mo"
    plan_color = "#e8a83e" if s.user_plan == "pro" else "rgba(253,246,232,.4)"

    with st.sidebar:
        st.markdown(f"""
        <div style="background:#0f0d09;min-height:100vh;margin:-1rem -1rem 0 -1rem;padding:0;">
          <div style="padding:22px 22px 18px;font-family:'Georgia',serif;font-size:19px;font-weight:800;
               color:#fdf6e8;border-bottom:1px solid rgba(255,255,255,.07);">✦ <em style="color:#c9892a;font-style:normal;">Niche</em>Flow AI</div>
          <div style="padding:15px 22px;border-bottom:1px solid rgba(255,255,255,.07);">
            <div style="font-size:13.5px;font-weight:600;color:#fdf6e8;">{s.user_email or 'User'}</div>
            <div style="font-size:11.5px;color:{plan_color};margin-top:3px;">{plan_label}</div>
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        tabs = [
            ("overview",  "📊", "Overview"),
            ("generate",  "✍️", "Generate"),
            ("settings",  "⚙️", "Settings"),
            ("prompts",   "📝", "Prompts"),
            ("design",    "🎨", "Design"),
            ("pinterest", "📌", "Pinterest"),
            ("billing",   "💳", "Billing"),
            ("docs",      "📖", "Documentation"),
        ]
        for key, icon, label in tabs:
            active = s.dash_tab == key
            bg = "rgba(255,255,255,.09)" if active else "transparent"
            color = "#e8a83e" if active else "rgba(253,246,232,.55)"
            if st.button(f"{icon}  {label}", key=f"nav_{key}",
                         use_container_width=True):
                s.dash_tab = key
                st.rerun()

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        if st.button("🚪  Sign Out", use_container_width=True):
            do_logout(); st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD TABS
# ─────────────────────────────────────────────────────────────────────────────
def tab_overview():
    section_header("Overview", "Your NicheFlow AI dashboard")
    s  = st.session_state.settings
    c1, c2, c3, c4 = st.columns(4)
    with c1: card("Articles Generated",  s.get("articles_generated",  0), "✍️")
    with c2: card("Images Created",       s.get("images_created",      0), "🎨")
    with c3: card("Posts Published",      s.get("posts_published",     0), "🌐")
    with c4: card("Pins Posted",          s.get("pins_posted",         0), "📌")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;">
          <h3 style="font-size:14.5px;font-weight:700;color:#1a1510;margin:0 0 16px 0;
               padding-bottom:12px;border-bottom:1px solid #f0e6d4;">🚀 Quick Start</h3>
          <p style="font-size:13.5px;color:#5a5040;line-height:1.7;margin-bottom:12px;">
          1. Add your API keys in <strong>Settings</strong><br>
          2. Write your prompts in <strong>Prompts</strong><br>
          3. Style your articles in <strong>Design</strong><br>
          4. Go to <strong>Generate</strong> and paste titles</p>
        </div>""", unsafe_allow_html=True)
    with c2:
        plan = st.session_state.user_plan
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1c1810,#0f0d09);border:1px solid rgba(201,137,42,.3);
             border-radius:18px;padding:24px;color:#fdf6e8;">
          <h3 style="font-size:14.5px;font-weight:700;color:#e8a83e;margin:0 0 12px 0;">
               {'⭐ Pro Plan' if plan=='pro' else '📦 Basic Plan'}</h3>
          <p style="font-size:13px;color:rgba(253,246,232,.6);line-height:1.7;">
          {'All features unlocked including Pinterest Auto-Post and Scheduler.' if plan=='pro'
           else 'Upgrade to Pro ($40/mo) to unlock Pinterest Auto-Post, Scheduler, and priority support.'}</p>
          {'<p style="font-size:12px;color:rgba(201,137,42,.8);margin-top:10px;">✅ All Pro features active</p>'
           if plan=='pro' else ''}
        </div>""", unsafe_allow_html=True)


def tab_settings():
    section_header("Settings", "API credentials and publishing preferences")
    s = st.session_state.settings

    if st.session_state.save_ok:
        success_box("Settings saved successfully!")
        st.session_state.save_ok = False

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;">', unsafe_allow_html=True)
        st.markdown('<h3 style="font-size:14.5px;font-weight:700;color:#1a1510;margin:0 0 18px 0;padding-bottom:13px;border-bottom:1px solid #f0e6d4;">🔑 API Credentials</h3>', unsafe_allow_html=True)

        groq_key = st.text_input("Groq API Key", value=s.get("groq_key",""), type="password",
                                  placeholder="gsk_...", help="Free at console.groq.com")
        c_test1, c_status1 = st.columns([1,2])
        with c_test1:
            if st.button("Test Groq", key="test_groq"):
                r = test_groq_key(groq_key) if groq_key else {"success":False,"message":"Enter a key first"}
                st.session_state["groq_test"] = r
        with c_status1:
            if "groq_test" in st.session_state:
                r = st.session_state.groq_test
                st.markdown(f'<div style="font-size:12px;padding:6px 0;color:{"#1a6e38" if r["success"] else "#c03030"};">{r["message"]}</div>', unsafe_allow_html=True)

        goapi_key = st.text_input("Midjourney API Key (GoAPI)", value=s.get("mj_key",""), type="password",
                                   placeholder="Your GoAPI key", help="Get at goapi.ai")
        c_test2, c_status2 = st.columns([1,2])
        with c_test2:
            if st.button("Test GoAPI", key="test_goapi"):
                r = test_goapi_key(goapi_key) if goapi_key else {"success":False,"message":"Enter a key first"}
                st.session_state["goapi_test"] = r
        with c_status2:
            if "goapi_test" in st.session_state:
                r = st.session_state.goapi_test
                st.markdown(f'<div style="font-size:12px;padding:6px 0;color:{"#1a6e38" if r["success"] else "#c03030"};">{r["message"]}</div>', unsafe_allow_html=True)

        wp_url = st.text_input("WordPress Site URL", value=s.get("wp_url",""),
                                placeholder="https://yoursite.com")
        wp_password = st.text_input("WordPress App Password", value=s.get("wp_password",""),
                                     type="password", placeholder="Username:xxxx xxxx xxxx xxxx",
                                     help="WP Dashboard → Users → Profile → Application Passwords")
        c_test3, c_status3 = st.columns([1,2])
        with c_test3:
            if st.button("Test WordPress", key="test_wp"):
                r = test_wordpress(wp_url, wp_password) if (wp_url and wp_password) else {"success":False,"message":"Enter URL and password first"}
                st.session_state["wp_test"] = r
                if r["success"]:
                    cats = fetch_wp_categories(wp_url, wp_password)
                    st.session_state.wp_categories = cats
        with c_status3:
            if "wp_test" in st.session_state:
                r = st.session_state.wp_test
                st.markdown(f'<div style="font-size:12px;padding:6px 0;color:{"#1a6e38" if r["success"] else "#c03030"};">{r["message"]}</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;">', unsafe_allow_html=True)
        st.markdown('<h3 style="font-size:14.5px;font-weight:700;color:#1a1510;margin:0 0 18px 0;padding-bottom:13px;border-bottom:1px solid #f0e6d4;">⚙️ Publishing Preferences</h3>', unsafe_allow_html=True)

        publish_status = st.selectbox("Publish Status", ["draft","publish"],
                                       index=0 if s.get("publish_status","draft")=="draft" else 1)
        info_box("💡 Start with <strong>Draft</strong> — review articles before they go live.")

        use_images  = st.toggle("Generate Midjourney Images", value=s.get("use_images", True))
        show_card   = st.toggle("Include Info Card in Articles", value=s.get("show_card", True))
        card_click  = st.toggle("Card Clickable in WordPress", value=s.get("card_clickable", False),
                                 help="Card will link to the article URL when clicked")

        st.markdown('<h3 style="font-size:13.5px;font-weight:700;color:#1a1510;margin:18px 0 10px 0;">🎞️ Midjourney Prompt Template</h3>', unsafe_allow_html=True)
        mj_template = st.text_area("Midjourney Template", value=s.get("mj_template",""),
                                    placeholder="Close up {recipe_name}, food photography, natural light --ar 2:3 --v 6.1",
                                    height=80,
                                    help="Use {recipe_name} as placeholder for the article title")

        st.markdown('<h3 style="font-size:13.5px;font-weight:700;color:#1a1510;margin:18px 0 10px 0;">🔗 Internal Links</h3>', unsafe_allow_html=True)
        use_int_links = st.toggle("Enable Internal Linking", value=s.get("use_internal_links", False))
        if use_int_links:
            max_links = st.slider("Max links per article", 1, 8, int(s.get("max_links", 4)))
        else:
            max_links = int(s.get("max_links", 4))

        # WP Categories
        cats = st.session_state.wp_categories
        selected_cats = []
        if cats:
            st.markdown('<h3 style="font-size:13.5px;font-weight:700;color:#1a1510;margin:18px 0 10px 0;">📁 WordPress Categories</h3>', unsafe_allow_html=True)
            cat_options = {c["name"]: c["id"] for c in cats}
            sel_names = st.multiselect("Assign to categories", options=list(cat_options.keys()))
            selected_cats = [cat_options[n] for n in sel_names]

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    if st.button("💾 Save Settings", type="primary"):
        st.session_state.settings.update({
            "groq_key": groq_key, "mj_key": goapi_key,
            "wp_url": wp_url, "wp_password": wp_password,
            "publish_status": publish_status,
            "use_images": use_images, "show_card": show_card,
            "card_clickable": card_click,
            "mj_template": mj_template,
            "use_internal_links": use_int_links,
            "max_links": max_links,
        })
        save_settings_to_db()
        st.rerun()


def tab_prompts():
    section_header("Prompts", "Customize how your content is generated")
    s = st.session_state.settings

    if st.session_state.save_ok:
        success_box("Prompts saved successfully!")
        st.session_state.save_ok = False

    info_box("⚠️ <strong>Token Warning:</strong> Keep your article prompt under 2000 tokens (roughly 1500 words) to avoid Groq rate limits. Short, clear instructions work best.")

    tab1, tab2, tab3 = st.tabs(["✍️ Article Prompt", "🃏 Card Prompt", "📌 Pinterest Prompt"])

    with tab1:
        st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;">', unsafe_allow_html=True)
        st.markdown("""<p style="font-size:13.5px;color:#5a5040;line-height:1.7;margin-bottom:16px;">
        Write your article prompt below. This tells the AI exactly how to write for your niche, audience, and style.
        <strong>Leave it blank</strong> if you want to write raw — but we recommend customizing it for your niche.
        </p>""", unsafe_allow_html=True)

        article_prompt = st.text_area(
            "Your Article Prompt",
            value=s.get("article_prompt",""),
            height=200,
            placeholder=(
                "Example — Travel blog:\n"
                "Write an inspiring travel guide in second person. Open with a vivid sensory scene. "
                "Cover top 5 attractions, local food, best time to visit, budget, and 5 practical tips. "
                "Target budget adventurers aged 25-40. Use H2 headings for each section. 1200-1500 words.\n\n"
                "Example — Recipe blog:\n"
                "Write a warm, personal recipe article in first person. Open with a nostalgic story. "
                "Include a 'Why You'll Love This' section, 6 expert tips, variations, and 3 FAQs. "
                "Friendly tone for home cooks. 1200 words."
            )
        )

        st.markdown('<h3 style="font-size:13.5px;font-weight:700;color:#1a1510;margin:20px 0 10px 0;">🏗️ Custom HTML Structure (optional)</h3>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:13px;color:#8a7a60;margin-bottom:10px;">Paste your HTML/CSS template here. The AI will follow this structure for every article.</p>', unsafe_allow_html=True)
        html_structure = st.text_area(
            "HTML Structure Template",
            value=s.get("html_structure",""),
            height=160,
            placeholder='<h2 style="color:MAIN_COLOR;">Section Title</h2>\n<div style="background:#f9f9f9;border-left:4px solid MAIN_COLOR;padding:16px;">...</div>'
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;">', unsafe_allow_html=True)
        st.markdown("""<p style="font-size:13.5px;color:#5a5040;line-height:1.7;margin-bottom:16px;">
        Describe the card you want inserted in every article. This can be a recipe card, travel card, health summary, product card — anything. 
        The AI will generate the data and the card will be inserted automatically.
        </p>""", unsafe_allow_html=True)
        card_prompt = st.text_area(
            "Your Card Prompt",
            value=s.get("card_prompt",""),
            height=180,
            placeholder=(
                "Example — Recipe card:\n"
                "Create a recipe card with prep time, cook time, total time, servings, calories per serving, "
                "protein, carbs, fat, a list of ingredients with quantities, and step-by-step instructions.\n\n"
                "Example — Travel card:\n"
                "Create a destination quick-reference card with best time to visit, average daily budget in USD, "
                "official language, currency, visa required (yes/no), and top 3 must-see attractions."
            )
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        if st.session_state.user_plan != "pro":
            st.markdown("""
            <div style="background:linear-gradient(135deg,#1c1810,#0f0d09);border:1px solid rgba(201,137,42,.38);
                 border-radius:18px;padding:28px;text-align:center;color:#fdf6e8;">
              <div style="font-size:34px;margin-bottom:10px;">📌</div>
              <h3 style="font-family:'Georgia',serif;font-size:22px;font-weight:800;color:#fdf6e8;margin:0 0 8px 0;">Pinterest Prompt</h3>
              <p style="font-size:13.5px;color:rgba(253,246,232,.5);line-height:1.7;">
              Available on the <span style="color:#e8a83e;font-weight:600;">Pro plan ($40/month)</span>.<br>
              Upgrade to write your Pinterest prompt and auto-post optimized pins after every article.</p>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;">', unsafe_allow_html=True)
            st.markdown("""<p style="font-size:13.5px;color:#5a5040;line-height:1.7;margin-bottom:16px;">
            Describe your Pinterest niche and audience. The AI will use this to generate optimized Pin titles, 
            descriptions, and alt text after every article is published.
            </p>""", unsafe_allow_html=True)
            pinterest_prompt = st.text_area(
                "Your Pinterest Prompt",
                value=s.get("pinterest_prompt",""),
                height=160,
                placeholder=(
                    "Example:\nMy audience is busy moms who love quick weeknight dinner recipes. "
                    "Write Pinterest pin descriptions that are warm and conversational, using keywords like "
                    "family dinner, easy recipes, weeknight meals. Keep under 200 characters with a call to action."
                )
            )
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    if st.button("💾 Save Prompts", type="primary"):
        updates = {
            "article_prompt": article_prompt,
            "html_structure": html_structure,
            "card_prompt": card_prompt,
        }
        if st.session_state.user_plan == "pro":
            updates["pinterest_prompt"] = pinterest_prompt
        st.session_state.settings.update(updates)
        save_settings_to_db()
        st.rerun()


def tab_design():
    section_header("Design Studio", "Customize how your articles look")
    s = st.session_state.settings

    if st.session_state.save_ok:
        success_box("Design settings saved!")
        st.session_state.save_ok = False

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;">', unsafe_allow_html=True)
        st.markdown('<h3 style="font-size:14.5px;font-weight:700;color:#1a1510;margin:0 0 18px 0;padding-bottom:13px;border-bottom:1px solid #f0e6d4;">🎨 Color Theme</h3>', unsafe_allow_html=True)

        main_color   = st.color_picker("Main Color (headings, accents)", value=s.get("design_main_color","#333333"))
        accent_color = st.color_picker("Accent / Highlight Color",        value=s.get("design_accent_color","#ea580c"))

        font_opts = ["inherit","'Georgia',serif","'Arial',sans-serif","'Verdana',sans-serif",
                     "'Trebuchet MS',sans-serif","'Times New Roman',serif","'Courier New',monospace"]
        font_labels = ["Site default","Georgia (serif)","Arial","Verdana","Trebuchet MS","Times New Roman","Courier New"]
        cur_font = s.get("design_font_family","inherit")
        font_idx = font_opts.index(cur_font) if cur_font in font_opts else 0
        font_family = font_opts[st.selectbox("Article Font", options=range(len(font_labels)),
                                              format_func=lambda i: font_labels[i], index=font_idx)]

        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;">', unsafe_allow_html=True)
        st.markdown('<h3 style="font-size:14.5px;font-weight:700;color:#1a1510;margin:0 0 18px 0;padding-bottom:13px;border-bottom:1px solid #f0e6d4;">👁️ Preview</h3>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="font-family:{font_family};border:1px solid #eee;border-radius:12px;padding:20px;background:#fff;">
          <h2 style="color:{main_color};font-size:18px;font-weight:800;margin:0 0 10px 0;">Your Article Title</h2>
          <p style="font-size:14px;color:#444;line-height:1.7;margin:0 0 14px 0;">This is how your article intro paragraph will look with your chosen font and colors applied.</p>
          <div style="background:#f9f9f9;border-left:4px solid {accent_color};border-radius:0 8px 8px 0;padding:12px 16px;">
            <ul style="margin:0;padding-left:16px;line-height:2.2;font-size:13px;color:#444;">
              <li>Expert tip or key point</li>
              <li>Why readers will love this</li>
              <li>Important detail or fact</li>
            </ul>
          </div>
        </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    if st.button("💾 Save Design", type="primary"):
        st.session_state.settings.update({
            "design_main_color":   main_color,
            "design_accent_color": accent_color,
            "design_font_family":  font_family,
        })
        save_settings_to_db()
        st.rerun()


def tab_generate():
    section_header("Generate Articles", "Paste titles and publish automatically")
    s = st.session_state.settings

    # Check required settings
    missing = []
    if not s.get("groq_key"): missing.append("Groq API key")
    if not s.get("wp_url"):   missing.append("WordPress URL")
    if not s.get("wp_password"): missing.append("WordPress App Password")
    if not s.get("article_prompt"): missing.append("Article Prompt (in Prompts tab)")

    if missing:
        error_box(f"Please configure first: <strong>{', '.join(missing)}</strong> — go to Settings and Prompts tabs.")
        return

    st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;margin-bottom:18px;">', unsafe_allow_html=True)
    st.markdown('<h3 style="font-size:14.5px;font-weight:700;color:#1a1510;margin:0 0 6px 0;">📋 Article Titles</h3>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13px;color:#8a7a60;margin-bottom:16px;">One title per line. NicheFlow will write, design, and publish each article automatically.</p>', unsafe_allow_html=True)

    titles_input = st.text_area(
        "Titles", height=160,
        placeholder="How to Travel Europe on a Budget\n10 Best Hiking Trails in Colorado\nMediterranean Grilled Chicken Recipe",
        label_visibility="collapsed"
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        gen_images = st.toggle("Generate Images", value=s.get("use_images", True), key="gen_use_images")
    with c2:
        gen_card   = st.toggle("Include Card",    value=s.get("show_card", True),  key="gen_show_card")
    with c3:
        gen_links  = st.toggle("Internal Links",  value=s.get("use_internal_links", False), key="gen_int_links")
    with c4:
        delay_sec  = st.number_input("Delay (sec)", min_value=0, max_value=30, value=5, key="gen_delay")

    show_logs = st.checkbox("Show processing logs", value=False)
    st.markdown('</div>', unsafe_allow_html=True)

    col_btn, col_spacer = st.columns([1, 3])
    with col_btn:
        generate_clicked = st.button("🚀 Generate & Publish All", type="primary", use_container_width=True)

    if generate_clicked and titles_input.strip():
        titles = [t.strip() for t in titles_input.strip().splitlines() if t.strip()]
        if not titles:
            error_box("Please enter at least one title."); return

        log_container = st.empty()
        results_container = st.container()

        pipeline_settings = {
            "groq_key":            s.get("groq_key",""),
            "goapi_key":           s.get("mj_key",""),
            "wp_url":              s.get("wp_url",""),
            "wp_password":         s.get("wp_password",""),
            "publish_status":      s.get("publish_status","draft"),
            "mj_template":         s.get("mj_template",""),
            "use_images":          gen_images and bool(s.get("mj_key","")),
            "show_card":           gen_card,
            "card_clickable":      s.get("card_clickable", False),
            "use_internal_links":  gen_links,
            "max_links":           int(s.get("max_links", 4)),
            "user_article_prompt": s.get("article_prompt",""),
            "user_html_structure": s.get("html_structure",""),
            "user_card_prompt":    s.get("card_prompt",""),
            "user_design": {
                "main_color":   s.get("design_main_color","#333333"),
                "accent_color": s.get("design_accent_color","#ea580c"),
                "font_family":  s.get("design_font_family","inherit"),
            },
        }

        all_logs = []
        results  = []

        for i, title in enumerate(titles):
            st.markdown(f'<div style="background:#fff8ec;border-left:4px solid #c9892a;border-radius:0 8px 8px 0;padding:10px 14px;font-size:13px;color:#7a5820;margin-bottom:8px;">⏳ Processing <strong>{i+1}/{len(titles)}</strong>: {title}</div>', unsafe_allow_html=True)

            def log_fn(msg, _logs=all_logs, _container=log_container, _show=show_logs):
                _logs.append(msg)
                if _show:
                    _container.markdown(
                        '<div style="background:#1a1510;border-radius:10px;padding:14px;font-family:monospace;font-size:12px;color:#a0c080;max-height:200px;overflow-y:auto;">' +
                        '<br>'.join(_logs[-20:]) + '</div>',
                        unsafe_allow_html=True
                    )

            result = run_full_pipeline(title, pipeline_settings, log_fn=log_fn) if GEN_OK else {"success": False, "error": "Generator not available"}
            results.append({"title": title, **result})

            if result.get("success"):
                st.markdown(f'<div style="background:#f0faf4;border:1px solid #a4d8b8;color:#1a6e38;border-radius:9px;padding:10px 14px;font-size:13px;margin-bottom:8px;">✅ <strong>{title}</strong> published → <a href="{result.get("post_url","")}" target="_blank">{result.get("post_url","view post")}</a></div>', unsafe_allow_html=True)
                db_increment_stat(st.session_state.user_id, "articles_generated")
                db_increment_stat(st.session_state.user_id, "posts_published")
                ic = result.get("image_count", 0)
                if ic: db_increment_stat(st.session_state.user_id, "images_created", ic)
            else:
                error_box(f"<strong>{title}</strong>: {result.get('error','Unknown error')}")

            if i < len(titles) - 1 and delay_sec > 0:
                time.sleep(delay_sec)

        st.session_state.gen_results = results
        st.session_state.settings = db_load_settings(st.session_state.user_id)


def tab_pinterest():
    section_header("Pinterest Auto-Post", "Configure Pinterest integration")
    s = st.session_state.settings

    if st.session_state.user_plan != "pro":
        st.markdown("""
        <div style="background:linear-gradient(135deg,#1c1810,#0f0d09);border:1px solid rgba(201,137,42,.38);
             border-radius:18px;padding:32px;text-align:center;color:#fdf6e8;margin-bottom:22px;">
          <div style="font-size:40px;margin-bottom:12px;">📌</div>
          <h3 style="font-family:'Georgia',serif;font-size:24px;font-weight:800;color:#fdf6e8;margin:0 0 10px 0;">Pinterest Auto-Post</h3>
          <p style="font-size:14px;color:rgba(253,246,232,.5);line-height:1.7;max-width:480px;margin:0 auto 20px;">
          Available on the <span style="color:#e8a83e;font-weight:700;">Pro plan ($40/month)</span>.<br>
          Automatically post optimized Pins after every WordPress publish — using your featured image and AI-generated descriptions.</p>
          <div style="background:rgba(201,137,42,.15);border:1px solid rgba(201,137,42,.3);border-radius:10px;padding:16px;max-width:360px;margin:0 auto;">
            <p style="font-size:13px;color:rgba(253,246,232,.7);margin:0;">✅ Pinterest Keyword Optimizer<br>✅ Custom Pinterest Prompt<br>✅ Post Scheduler (day + time)<br>✅ Auto Pin from Featured Image</p>
          </div>
        </div>""", unsafe_allow_html=True)

        if st.button("⬆️ Upgrade to Pro", type="primary"):
            st.session_state.dash_tab = "billing"; st.rerun()
        return

    if st.session_state.save_ok:
        success_box("Pinterest settings saved!")
        st.session_state.save_ok = False

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;">', unsafe_allow_html=True)
        st.markdown('<h3 style="font-size:14.5px;font-weight:700;color:#1a1510;margin:0 0 18px 0;padding-bottom:13px;border-bottom:1px solid #f0e6d4;">🔑 Pinterest Credentials</h3>', unsafe_allow_html=True)
        pin_token = st.text_input("Pinterest Access Token", value=s.get("pinterest_token",""), type="password")
        pin_board = st.text_input("Pinterest Board ID", value=s.get("pinterest_board",""), placeholder="Your board ID")
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;">', unsafe_allow_html=True)
        st.markdown('<h3 style="font-size:14.5px;font-weight:700;color:#1a1510;margin:0 0 18px 0;padding-bottom:13px;border-bottom:1px solid #f0e6d4;">📌 Pinterest Prompt</h3>', unsafe_allow_html=True)
        pin_prompt = st.text_area("Your Pinterest Prompt", value=s.get("pinterest_prompt",""), height=160,
                                   placeholder="My audience is busy moms who love quick dinner recipes. Write warm, conversational pin descriptions using family food keywords.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Scheduler
    st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:26px;margin-top:18px;">', unsafe_allow_html=True)
    st.markdown('<h3 style="font-size:14.5px;font-weight:700;color:#1a1510;margin:0 0 6px 0;padding-bottom:13px;border-bottom:1px solid #f0e6d4;">📅 Pinterest Post Scheduler</h3>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13px;color:#8a7a60;margin-bottom:16px;">Choose which days and time your Pins are automatically posted after each article is published.</p>', unsafe_allow_html=True)

    days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    saved_days_str = s.get("schedule_days","")
    saved_days = saved_days_str.split(",") if saved_days_str else []

    st.markdown("**Post on these days:**")
    day_cols = st.columns(7)
    selected_days = []
    for i, day in enumerate(days):
        with day_cols[i]:
            if st.checkbox(day[:3], value=(day in saved_days), key=f"day_{day}"):
                selected_days.append(day)

    tc1, tc2 = st.columns(2)
    with tc1:
        schedule_time = st.time_input("Posting Time", value=datetime.strptime(s.get("schedule_time","09:00"), "%H:%M").time())
    with tc2:
        tz_options = ["UTC","America/New_York","America/Los_Angeles","Europe/London",
                      "Europe/Paris","Asia/Dubai","Africa/Casablanca","Asia/Tokyo"]
        cur_tz = s.get("schedule_timezone","UTC")
        tz_idx = tz_options.index(cur_tz) if cur_tz in tz_options else 0
        schedule_tz = st.selectbox("Timezone", tz_options, index=tz_idx)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    if st.button("💾 Save Pinterest Settings", type="primary"):
        st.session_state.settings.update({
            "pinterest_token":    pin_token,
            "pinterest_board":    pin_board,
            "pinterest_prompt":   pin_prompt,
            "schedule_days":      ",".join(selected_days),
            "schedule_time":      schedule_time.strftime("%H:%M"),
            "schedule_timezone":  schedule_tz,
        })
        save_settings_to_db()
        st.rerun()


def tab_billing():
    section_header("Billing", "Manage your plan and subscription")
    plan = st.session_state.user_plan

    c1, c2 = st.columns(2)
    with c1:
        active_style = "border:2px solid #c9892a;box-shadow:0 4px 20px rgba(201,137,42,.2);"
        st.markdown(f"""
        <div style="background:#fff;{active_style if plan=='basic' else 'border:2px solid #dfd4bc;'}border-radius:26px;padding:40px 36px;text-align:center;">
          {'<div style="font-size:10px;font-weight:700;color:#c9892a;text-transform:uppercase;letter-spacing:2px;margin-bottom:12px;">✦ Current Plan</div>' if plan=='basic' else ''}
          <div style="font-size:11px;font-weight:700;color:#8a7a60;text-transform:uppercase;letter-spacing:2px;margin-bottom:16px;">Basic</div>
          <div style="font-family:Georgia,serif;font-size:64px;font-weight:900;color:#1a1510;line-height:1;">$30</div>
          <div style="font-size:14px;color:#8a7a60;margin-bottom:24px;">per month</div>
          <div style="text-align:left;font-size:13.5px;color:#5a5040;line-height:2.2;">
            ✅ AI Article Generation<br>✅ Midjourney Images (4/article)<br>✅ WordPress Auto-Publish<br>
            ✅ Custom Prompts &amp; Design<br>✅ Internal Linking<br>❌ Pinterest Auto-Post
          </div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div style="background:linear-gradient(158deg,#211808,#0f0d09);{active_style if plan=='pro' else 'border:2px solid rgba(201,137,42,.3);'}border-radius:26px;padding:40px 36px;text-align:center;">
          {'<div style="font-size:10px;font-weight:700;color:#e8a83e;text-transform:uppercase;letter-spacing:2px;margin-bottom:12px;">✦ Current Plan</div>' if plan=='pro' else ''}
          <div style="font-size:11px;font-weight:700;color:rgba(232,168,62,.7);text-transform:uppercase;letter-spacing:2px;margin-bottom:16px;">Pro · Most Popular</div>
          <div style="font-family:Georgia,serif;font-size:64px;font-weight:900;color:#fff;line-height:1;">$40</div>
          <div style="font-size:14px;color:rgba(253,246,232,.4);margin-bottom:24px;">per month</div>
          <div style="text-align:left;font-size:13.5px;color:rgba(253,246,232,.8);line-height:2.2;">
            ✅ Everything in Basic<br>✅ Pinterest Auto-Post<br>✅ Pinterest Keyword Optimizer<br>
            ✅ Custom Pinterest Prompt<br>✅ Pinterest Post Scheduler<br>✅ Priority Support
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;">', unsafe_allow_html=True)
    st.markdown('<h3 style="font-size:14.5px;font-weight:700;color:#1a1510;margin:0 0 12px 0;">💳 Payment</h3>', unsafe_allow_html=True)
    st.markdown("""<p style="font-size:13.5px;color:#5a5040;line-height:1.7;">
    To upgrade or manage your subscription, contact us at <strong>support@nicheflow.ai</strong> or use the upgrade link below.
    Payments are processed securely via Stripe.</p>""", unsafe_allow_html=True)

    if plan == "basic":
        if st.button("⬆️ Upgrade to Pro ($40/mo)", type="primary"):
            info_box("Contact support@nicheflow.ai to upgrade your account.")
    else:
        success_box("You are on the Pro plan. Contact support@nicheflow.ai to manage your subscription.")
    st.markdown('</div>', unsafe_allow_html=True)


def tab_docs():
    section_header("Documentation", "Setup guide and best practices")
    st.markdown("""
    <div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:26px;margin-bottom:18px;">
      <h2 style="font-family:Georgia,serif;font-size:19px;font-weight:800;color:#1a1510;margin:0 0 14px 0;">
        🔑 1. Get Your Groq API Key</h2>
      <ol style="font-size:13.5px;color:#5a5040;line-height:2;padding-left:20px;">
        <li>Go to <strong>console.groq.com</strong> and create a free account</li>
        <li>Click <strong>API Keys</strong> in the left sidebar</li>
        <li>Click <strong>Create API Key</strong> and name it "NicheFlow"</li>
        <li>Copy the key — it starts with <strong>gsk_</strong></li>
        <li>Paste it in <strong>Settings → Groq API Key</strong></li>
      </ol>
      <div style="background:#fff8ec;border-left:3px solid #c9892a;border-radius:0 8px 8px 0;padding:10px 14px;font-size:13px;color:#7a5820;">
        Groq's free tier: 14,400 requests per day — more than enough for daily publishing.</div>
    </div>
    <div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:26px;margin-bottom:18px;">
      <h2 style="font-family:Georgia,serif;font-size:19px;font-weight:800;color:#1a1510;margin:0 0 14px 0;">
        🎨 2. Get Your Midjourney API Key</h2>
      <ol style="font-size:13.5px;color:#5a5040;line-height:2;padding-left:20px;">
        <li>Go to <strong>goapi.ai</strong> and create an account</li>
        <li>Choose a plan (pay-as-you-go works well)</li>
        <li>Navigate to <strong>Dashboard → API Keys</strong></li>
        <li>Copy your key and paste it in <strong>Settings → Midjourney API Key</strong></li>
      </ol>
    </div>
    <div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:26px;margin-bottom:18px;">
      <h2 style="font-family:Georgia,serif;font-size:19px;font-weight:800;color:#1a1510;margin:0 0 14px 0;">
        🌐 3. Connect WordPress</h2>
      <ol style="font-size:13.5px;color:#5a5040;line-height:2;padding-left:20px;">
        <li>Log in to your <strong>WordPress Dashboard</strong></li>
        <li>Go to <strong>Users → Your Profile</strong></li>
        <li>Scroll to <strong>Application Passwords</strong></li>
        <li>Enter name: <strong>NicheFlow AI</strong> → click <strong>Add New</strong></li>
        <li>Copy the generated password (format: xxxx xxxx xxxx xxxx)</li>
        <li>In Settings, enter URL as <strong>https://yoursite.com</strong></li>
        <li>Enter password as <strong>YourUsername:xxxx xxxx xxxx xxxx</strong></li>
      </ol>
      <div style="background:#fff8ec;border-left:3px solid #c9892a;border-radius:0 8px 8px 0;padding:10px 14px;font-size:13px;color:#7a5820;">
        URL must include https:// and must not have a trailing slash.</div>
    </div>
    <div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:26px;margin-bottom:18px;">
      <h2 style="font-family:Georgia,serif;font-size:19px;font-weight:800;color:#1a1510;margin:0 0 14px 0;">
        ✍️ 4. Write Great Prompts</h2>
      <p style="font-size:13.5px;color:#5a5040;line-height:1.7;margin-bottom:14px;">Your article prompt is the most important setting. 
      Write it like you're briefing a journalist — explain your niche, audience, tone, and structure.</p>
      <div style="background:#f8f3ea;border:1px solid #e4d8c4;border-radius:10px;padding:13px 16px;font-size:13px;color:#5a4a34;font-style:italic;margin-bottom:12px;">
        Travel example: "Write an inspiring travel guide in second person. Open with a vivid sensory scene. Cover top 5 attractions, local food, best time to visit, budget, and 5 practical tips."</div>
      <div style="background:#fff8ec;border-left:3px solid #c9892a;border-radius:0 8px 8px 0;padding:10px 14px;font-size:13px;color:#7a5820;">
        ⚠️ Keep prompts under 2000 tokens to avoid Groq rate limits.</div>
    </div>
    <div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:26px;margin-bottom:18px;">
      <h2 style="font-family:Georgia,serif;font-size:19px;font-weight:800;color:#1a1510;margin:0 0 14px 0;">
        💡 5. Best Practices</h2>
      <ul style="font-size:13.5px;color:#5a5040;line-height:2;padding-left:20px;">
        <li><strong>Use descriptive titles</strong> — "Easy Creamy Tuscan Chicken Pasta" beats "Pasta Recipe"</li>
        <li><strong>Set 5-10 second delay</strong> between articles during bulk runs</li>
        <li><strong>Start with Draft</strong> to review before going live</li>
        <li><strong>Test with one article first</strong> before running a batch of 10+</li>
        <li><strong>Keep API keys private</strong> — never share them</li>
      </ul>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  AUTH PAGES (Streamlit native — no iframe needed)
# ─────────────────────────────────────────────────────────────────────────────
def render_auth_page(mode="login"):
    # Back button
    if st.button("← Back to Home"):
        st.session_state.page = "home"
        st.session_state.auth_error = ""
        st.session_state.auth_success = ""
        st.rerun()

    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        st.markdown(f"""
        <div style="background:#fff;border:1px solid #dfd4bc;border-radius:26px;padding:48px 44px;
             box-shadow:0 12px 56px rgba(0,0,0,.08);">
          <div style="font-family:Georgia,serif;font-size:20px;font-weight:800;color:#1a1510;
               text-align:center;margin-bottom:28px;">✦ <em style="color:#c9892a;font-style:normal;">NicheFlow</em> AI</div>
          <h2 style="font-family:Georgia,serif;font-size:28px;font-weight:800;color:#1a1510;
               text-align:center;margin:0 0 6px 0;">{'Welcome Back' if mode=='login' else 'Create Account'}</h2>
          <p style="font-size:14px;color:#8a7a60;text-align:center;margin:0 0 28px 0;">
               {'Sign in to your NicheFlow AI account' if mode=='login' else 'Start automating your content today'}</p>
        </div>""", unsafe_allow_html=True)

        if st.session_state.auth_error:
            error_box(st.session_state.auth_error)
        if st.session_state.auth_success:
            success_box(st.session_state.auth_success)
            st.session_state.auth_success = ""

        email    = st.text_input("Email Address", placeholder="your@email.com")
        password = st.text_input("Password", type="password", placeholder="Your password")

        if mode == "signup":
            confirm = st.text_input("Confirm Password", type="password", placeholder="Repeat password")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        if mode == "login":
            if st.button("Sign In →", type="primary", use_container_width=True):
                if email and password:
                    do_login(email, password)
                    st.rerun()
                else:
                    st.session_state.auth_error = "Please fill in both fields"
                    st.rerun()
            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1,2,1])
            with c2:
                if st.button("Don't have an account? Sign Up", use_container_width=True):
                    st.session_state.page = "signup"
                    st.session_state.auth_error = ""
                    st.rerun()
        else:
            if st.button("Create Account →", type="primary", use_container_width=True):
                if email and password and confirm:
                    do_signup(email, password, confirm)
                    st.rerun()
                else:
                    st.session_state.auth_error = "Please fill in all fields"
                    st.rerun()
            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1,2,1])
            with c2:
                if st.button("Already have an account? Sign In", use_container_width=True):
                    st.session_state.page = "login"
                    st.session_state.auth_error = ""
                    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
def render_dashboard():
    render_sidebar()

    tab = st.session_state.dash_tab

    with st.container():
        st.markdown("""
        <style>
        section[data-testid="stSidebar"]{display:flex!important;background:#0f0d09!important;}
        [data-testid="stSidebarContent"]{background:#0f0d09!important;}
        </style>""", unsafe_allow_html=True)

        if   tab == "overview":  tab_overview()
        elif tab == "settings":  tab_settings()
        elif tab == "prompts":   tab_prompts()
        elif tab == "design":    tab_design()
        elif tab == "generate":  tab_generate()
        elif tab == "pinterest": tab_pinterest()
        elif tab == "billing":   tab_billing()
        elif tab == "docs":      tab_docs()


# ─────────────────────────────────────────────────────────────────────────────
#  ROUTER
# ─────────────────────────────────────────────────────────────────────────────
page = st.session_state.page

if page == "home":
    st.markdown(JS_BRIDGE, unsafe_allow_html=True)
    components.html(LANDING_HTML, height=4800, scrolling=True)

elif page == "login":
    render_auth_page("login")

elif page == "signup":
    render_auth_page("signup")

elif page == "dashboard":
    if not st.session_state.user_id:
        st.session_state.page = "login"; st.rerun()
    else:
        render_dashboard()

elif page == "docs":
    if st.button("← Back to Home"):
        st.session_state.page = "home"; st.rerun()
    if st.session_state.user_id:
        st.session_state.dash_tab = "docs"
        st.session_state.page = "dashboard"
        st.rerun()
    else:
        tab_docs()