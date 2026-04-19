# -*- coding: utf-8 -*-
"""
NicheFlow AI — app.py
Fix: window.top.location.href for navigation (postMessage was blocked by iframe sandbox).
"""

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
except Exception:
    DB_OK = False
    supabase = None

try:
    from generator import (
        run_full_pipeline, test_groq_key, test_goapi_key, test_wordpress,
        fetch_wp_categories, generate_pinterest_pin, fetch_internal_links
    )
    GEN_OK = True
except Exception:
    GEN_OK = False

st.set_page_config(page_title="NicheFlow AI", page_icon="✦", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
#MainMenu,footer,header,
[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],[data-testid="collapsedControl"],
section[data-testid="stSidebar"]{display:none!important;}
.block-container{padding:0!important;max-width:100%!important;}
.stApp{background:#faf6ef!important;}
iframe{border:none!important;display:block;}
.stForm{background:transparent!important;border:none!important;padding:0!important;}
</style>
""", unsafe_allow_html=True)

def init_state():
    defaults = {
        "page": "home", "dash_tab": "overview",
        "user_id": None, "user_email": None, "user_plan": "basic",
        "settings": {}, "auth_error": "", "auth_success": "",
        "save_ok": False, "save_msg": "", "wp_categories": [],
        "test_results": {}, "gen_logs": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

FONTS = '<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700;9..144,800;9..144,900&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">'

BASE_CSS = """
<style>
:root{--cream:#faf6ef;--cream2:#f2e8d4;--gold:#c9892a;--gold2:#e8a83e;--dark:#0f0d09;--dark2:#1c1810;--text:#1a1510;--text2:#5a5040;--text3:#8a7a60;--border:#dfd4bc;}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html,body{font-family:'Outfit',sans-serif;background:var(--cream);color:var(--text);overflow-x:hidden;}
a{cursor:pointer;}
nav{position:sticky;top:0;z-index:999;display:flex;align-items:center;justify-content:space-between;padding:0 5vw;height:66px;background:rgba(250,246,239,0.96);backdrop-filter:blur(14px);border-bottom:1px solid var(--border);}
.nav-logo{font-family:'Fraunces',serif;font-size:21px;font-weight:800;color:var(--text);cursor:pointer;}
.nav-logo em{color:var(--gold);font-style:normal;}
.nav-links{display:flex;align-items:center;gap:28px;}
.nav-links a{font-size:14px;font-weight:500;color:var(--text2);text-decoration:none;transition:color .2s;}
.nav-links a:hover{color:var(--gold);}
.nav-cta{background:var(--dark)!important;color:#fff!important;padding:9px 22px;border-radius:100px;font-weight:600!important;font-size:13px!important;transition:all .2s!important;}
.nav-cta:hover{background:var(--dark2)!important;transform:translateY(-1px);}
.back-nav{display:inline-flex;align-items:center;gap:7px;font-size:13px;font-weight:600;color:var(--text3);cursor:pointer;padding:8px 14px;border-radius:100px;border:1px solid var(--border);background:rgba(255,255,255,.8);transition:all .2s;margin:16px 0 0 16px;}
.back-nav:hover{color:var(--gold);border-color:var(--gold);}
.back-nav svg{width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round;}
.btn-primary{background:var(--dark);color:#fff;padding:14px 30px;border-radius:100px;font-size:15px;font-weight:600;border:none;cursor:pointer;font-family:'Outfit',sans-serif;transition:all .2s;}
.btn-primary:hover{background:var(--dark2);transform:translateY(-2px);box-shadow:0 8px 28px rgba(0,0,0,.18);}
.btn-outline{background:transparent;color:var(--text);padding:14px 30px;border-radius:100px;font-size:15px;font-weight:600;border:1.5px solid var(--border);cursor:pointer;font-family:'Outfit',sans-serif;transition:all .2s;}
.btn-outline:hover{border-color:var(--gold);color:var(--gold);}
footer{text-align:center;padding:clamp(36px,5vw,56px);border-top:1px solid var(--border);background:var(--cream);}
footer .f-logo{font-family:'Fraunces',serif;font-size:21px;font-weight:800;color:var(--text);margin-bottom:9px;}
footer p{font-size:13px;color:var(--text3);margin-bottom:3px;}
@media(max-width:768px){.nav-links{display:none;}}
</style>
"""

# THE FIX — this single JS function replaces all postMessage calls
NAV_JS = """
<script>
function nav(id) {
  window.top.location.href = window.top.location.href.split('?')[0] + '?nav=' + id;
}
</script>
"""

def send(page):
    st.session_state.page = page
    st.rerun()

# ── DB helpers ───────────────────────────────────────────────────────────────
def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

def db_login(email, password):
    if not DB_OK: return {"ok": False, "err": "Database not connected"}
    try:
        r = supabase.table("users").select("*").eq("email", email).eq("password_hash", hash_pw(password)).execute()
        if not r.data: return {"ok": False, "err": "Wrong email or password"}
        u = r.data[0]
        return {"ok": True, "user_id": u["id"], "email": u["email"], "plan": u.get("plan", "basic")}
    except Exception as e:
        return {"ok": False, "err": str(e)}

def db_signup(email, password, plan="basic"):
    if not DB_OK: return {"ok": False, "err": "Database not connected"}
    try:
        ex = supabase.table("users").select("id").eq("email", email).execute()
        if ex.data: return {"ok": False, "err": "Email already registered"}
        r = supabase.table("users").insert({"email": email, "password_hash": hash_pw(password), "plan": plan}).execute()
        uid = r.data[0]["id"]
        supabase.table("user_settings").insert({"user_id": uid}).execute()
        return {"ok": True, "user_id": uid}
    except Exception as e:
        return {"ok": False, "err": str(e)}

def db_load(uid):
    if not DB_OK or not uid: return {}
    try:
        r = supabase.table("user_settings").select("*").eq("user_id", uid).execute()
        if r.data:
            row = r.data[0]
            keys = ["groq_key","wp_url","wp_password","mj_key","mj_template",
                    "article_prompt","html_structure","card_prompt","pinterest_token",
                    "pinterest_board","pinterest_prompt","publish_status","show_card",
                    "card_clickable","use_images","use_internal_links","max_links",
                    "schedule_days","schedule_time","schedule_timezone",
                    "design_main_color","design_accent_color","design_font_family",
                    "articles_generated","images_created","posts_published","pins_posted"]
            return {k: row[k] for k in keys if k in row and row[k] is not None}
        return {}
    except: return {}

def db_save(uid, data):
    if not DB_OK or not uid: return False
    try:
        ex = supabase.table("user_settings").select("id").eq("user_id", uid).execute()
        payload = {"user_id": uid, **data, "updated_at": datetime.utcnow().isoformat()}
        if ex.data:
            supabase.table("user_settings").update(payload).eq("user_id", uid).execute()
        else:
            supabase.table("user_settings").insert(payload).execute()
        return True
    except: return False

def db_inc(uid, field, n=1):
    if not DB_OK or not uid: return
    try:
        cur = db_load(uid).get(field, 0) or 0
        db_save(uid, {field: int(cur) + n})
    except: pass

# ── Auth ─────────────────────────────────────────────────────────────────────
def do_login(email, password):
    r = db_login(email.strip().lower(), password)
    if r["ok"]:
        st.session_state.user_id = r["user_id"]
        st.session_state.user_email = r["email"]
        st.session_state.user_plan = r["plan"]
        st.session_state.settings = db_load(r["user_id"])
        st.session_state.page = "dashboard"
        st.session_state.dash_tab = "overview"
        st.session_state.auth_error = ""
    else:
        st.session_state.auth_error = r["err"]

def do_signup(email, password, confirm):
    if password != confirm:
        st.session_state.auth_error = "Passwords don't match"; return
    if len(password) < 6:
        st.session_state.auth_error = "Password must be at least 6 characters"; return
    r = db_signup(email.strip().lower(), password)
    if r["ok"]:
        st.session_state.auth_error = ""
        st.session_state.auth_success = "Account created! You can now sign in."
        st.session_state.page = "login"
    else:
        st.session_state.auth_error = r["err"]

def do_logout():
    st.session_state.user_id = None
    st.session_state.user_email = None
    st.session_state.user_plan = "basic"
    st.session_state.settings = {}
    st.session_state.page = "home"
    st.session_state.auth_error = ""

# ═══════════════════════════════════════════════════════════════════════════
#  HOME
# ═══════════════════════════════════════════════════════════════════════════
def page_home():
    html = f"""{FONTS}{BASE_CSS}
<style>
.hero{{background:linear-gradient(160deg,#fdfaf4 0%,#f5e8cc 55%,#ecdbb8 100%);padding:96px 5vw 80px;text-align:center;border-bottom:1px solid var(--border);position:relative;overflow:hidden;}}
.hero::before{{content:'';position:absolute;top:-220px;left:-180px;width:560px;height:560px;background:radial-gradient(circle,rgba(201,137,42,.15) 0%,transparent 65%);border-radius:50%;}}
.hero::after{{content:'';position:absolute;bottom:-150px;right:-150px;width:480px;height:480px;background:radial-gradient(circle,rgba(201,137,42,.1) 0%,transparent 65%);border-radius:50%;}}
.hero-badge{{display:inline-flex;align-items:center;gap:7px;background:rgba(255,255,255,.7);border:1px solid rgba(201,137,42,.35);color:#8a6020;padding:7px 18px;border-radius:100px;font-size:12.5px;font-weight:600;letter-spacing:.4px;margin-bottom:28px;position:relative;z-index:1;}}
.hero h1{{font-family:'Fraunces',serif;font-size:clamp(46px,8vw,90px);font-weight:900;line-height:1.03;color:var(--text);margin-bottom:24px;position:relative;z-index:1;}}
.hero h1 em{{font-style:normal;color:var(--gold);}}
.hero p{{font-size:clamp(15px,1.7vw,19px);color:var(--text2);max-width:580px;margin:0 auto 44px;line-height:1.78;position:relative;z-index:1;}}
.hero-btns{{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;position:relative;z-index:1;}}
.hero-stats{{display:flex;flex-wrap:wrap;justify-content:center;gap:clamp(24px,5vw,68px);margin-top:60px;padding-top:48px;border-top:1px solid rgba(0,0,0,.09);position:relative;z-index:1;}}
.stat-num{{font-family:'Fraunces',serif;font-size:clamp(32px,4.5vw,48px);font-weight:800;color:var(--gold);}}
.stat-lbl{{font-size:13px;color:var(--text3);margin-top:5px;font-weight:500;}}
.section{{padding:clamp(60px,8vw,108px) clamp(24px,6vw,96px);background:var(--cream);}}
.section-alt{{background:var(--cream2);padding:clamp(60px,8vw,108px) clamp(24px,6vw,96px);}}
.section-dark{{background:var(--dark);padding:clamp(60px,8vw,108px) clamp(24px,6vw,96px);}}
.section-center{{text-align:center;}}
.eyebrow{{font-size:11px;font-weight:700;color:var(--gold);text-transform:uppercase;letter-spacing:3.5px;margin-bottom:14px;display:block;}}
.eyebrow-light{{color:rgba(201,137,42,.9)!important;}}
.section-title{{font-family:'Fraunces',serif;font-size:clamp(30px,4.5vw,52px);font-weight:800;line-height:1.12;color:var(--text);margin-bottom:14px;}}
.section-title-light{{font-family:'Fraunces',serif;font-size:clamp(30px,4.5vw,52px);font-weight:800;line-height:1.12;color:#fdf6e8;margin-bottom:14px;}}
.section-sub{{font-size:clamp(14px,1.4vw,17px);color:var(--text2);line-height:1.72;margin-bottom:clamp(36px,6vw,68px);max-width:560px;}}
.section-sub-light{{font-size:clamp(14px,1.4vw,17px);color:rgba(253,246,232,.5);line-height:1.72;margin-bottom:clamp(36px,6vw,68px);max-width:560px;}}
.section-center .section-sub,.section-center .section-sub-light{{margin-left:auto;margin-right:auto;}}
.feat-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;}}
@media(max-width:900px){{.feat-grid{{grid-template-columns:1fr 1fr;}}}}
@media(max-width:560px){{.feat-grid{{grid-template-columns:1fr;}}}}
.feat-card{{background:#fff;border:1px solid var(--border);border-radius:20px;padding:clamp(22px,3vw,36px);transition:transform .25s,box-shadow .25s,border-color .25s;}}
.feat-card:hover{{transform:translateY(-4px);box-shadow:0 14px 44px rgba(0,0,0,.07);border-color:rgba(201,137,42,.45);}}
.feat-icon{{width:50px;height:50px;background:#fff8ec;border:1px solid rgba(201,137,42,.2);border-radius:13px;display:flex;align-items:center;justify-content:center;font-size:22px;margin-bottom:16px;}}
.feat-card h3{{font-size:15.5px;font-weight:700;color:var(--text);margin-bottom:8px;}}
.feat-card p{{font-size:13.5px;color:var(--text3);line-height:1.76;}}
.pricing-grid{{display:grid;grid-template-columns:1fr 1fr;gap:22px;max-width:840px;margin:0 auto;}}
@media(max-width:640px){{.pricing-grid{{grid-template-columns:1fr;}}}}
.plan-card{{background:#fff;border:2px solid var(--border);border-radius:26px;padding:clamp(30px,4vw,50px) clamp(26px,3.5vw,42px);text-align:center;}}
.plan-card.pro{{background:linear-gradient(158deg,#211808,#0f0d09);border-color:rgba(201,137,42,.55);box-shadow:0 8px 44px rgba(201,137,42,.2);}}
.plan-label{{font-size:11px;font-weight:700;color:var(--text3);text-transform:uppercase;letter-spacing:2.5px;margin-bottom:16px;}}
.plan-card.pro .plan-label{{color:rgba(232,168,62,.75);}}
.plan-price{{font-family:'Fraunces',serif;font-size:clamp(50px,7vw,70px);font-weight:900;color:var(--text);line-height:1;}}
.plan-card.pro .plan-price{{color:#fff;}}
.plan-period{{font-size:14px;color:var(--text3);margin-bottom:28px;margin-top:4px;}}
.plan-card.pro .plan-period{{color:rgba(253,246,232,.4);}}
.plan-feats{{text-align:left;}}
.plan-feat{{font-size:13.5px;color:var(--text2);padding:10px 0;border-bottom:1px solid #f0e8d8;}}
.plan-card.pro .plan-feat{{color:rgba(253,246,232,.8);border-bottom-color:rgba(255,255,255,.07);}}
.plan-feat.no{{color:#b8a888;opacity:.6;}}
.plan-card.pro .plan-feat.no{{color:rgba(253,246,232,.25);}}
.plan-btn{{width:100%;margin-top:26px;padding:13px;border-radius:100px;font-size:14px;font-weight:700;cursor:pointer;border:2px solid var(--dark);background:transparent;color:var(--dark);font-family:'Outfit',sans-serif;transition:all .2s;}}
.plan-btn:hover{{background:var(--dark);color:#fff;}}
.plan-card.pro .plan-btn{{background:var(--gold);border-color:var(--gold);color:#fff;}}
.plan-card.pro .plan-btn:hover{{background:var(--gold2);border-color:var(--gold2);}}
.steps-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;}}
@media(max-width:900px){{.steps-grid{{grid-template-columns:1fr 1fr;}}}}
@media(max-width:520px){{.steps-grid{{grid-template-columns:1fr;}}}}
.step-card{{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.11);border-radius:20px;padding:clamp(24px,3vw,36px);}}
.step-num{{font-family:'Fraunces',serif;font-size:clamp(44px,5.5vw,60px);font-weight:900;color:var(--gold);line-height:1;margin-bottom:16px;}}
.step-card h4{{font-size:16px;font-weight:700;color:#fdf6e8;margin-bottom:9px;}}
.step-card p{{font-size:13.5px;color:rgba(253,246,232,.5);line-height:1.76;}}
.cta-banner{{background:var(--dark);border-radius:26px;padding:clamp(52px,7vw,92px) clamp(28px,6vw,80px);text-align:center;margin:0 clamp(14px,4vw,60px) clamp(52px,6vw,80px);position:relative;overflow:hidden;}}
.cta-banner::before{{content:'';position:absolute;top:-80px;left:50%;transform:translateX(-50%);width:500px;height:280px;background:radial-gradient(circle,rgba(201,137,42,.2) 0%,transparent 65%);pointer-events:none;}}
</style>

<nav>
  <div class="nav-logo">✦ <em>Niche</em>Flow AI</div>
  <div class="nav-links">
    <a href="#features">Features</a>
    <a href="#pricing">Pricing</a>
    <a href="#how">How It Works</a>
    <a onclick="nav('docs')">Documentation</a>
    <a class="nav-cta" onclick="nav('login')">Sign In →</a>
  </div>
</nav>

<section class="hero">
  <div class="hero-badge">✦ AI-Powered Content Platform</div>
  <h1>Write Less.<br>Publish More.<br><em>Grow on Autopilot.</em></h1>
  <p>NicheFlow AI writes full SEO blog articles, generates stunning Midjourney images, publishes to WordPress, and pins to Pinterest — completely automatically.</p>
  <div class="hero-btns">
    <button class="btn-primary" onclick="nav('signup')">Get Started Free →</button>
    <button class="btn-outline" onclick="nav('docs')">View Documentation</button>
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
    <p class="section-sub">One platform handles your entire content pipeline — from idea to published post, images included.</p>
  </div>
  <div class="feat-grid">
    <div class="feat-card"><div class="feat-icon">✍️</div><h3>AI Article Writer</h3><p>Groq AI writes full long-form SEO articles. Your prompt, your niche, your voice — no defaults forced on you.</p></div>
    <div class="feat-card"><div class="feat-icon">🎨</div><h3>Midjourney Images</h3><p>4 stunning images auto-generated per article. Converted to WebP and uploaded to your WordPress media library.</p></div>
    <div class="feat-card"><div class="feat-icon">🌐</div><h3>WordPress Publisher</h3><p>Articles publish directly to your site with images and full formatting. No copy-pasting — ever.</p></div>
    <div class="feat-card"><div class="feat-icon">📌</div><h3>Pinterest Auto-Post</h3><p>After every WordPress publish, automatically create optimized Pins using the article's featured image. Pro plan.</p></div>
    <div class="feat-card"><div class="feat-icon">🃏</div><h3>Custom Niche Cards</h3><p>Add beautifully styled cards to every article — recipe, travel, health, or any niche. Fully customizable.</p></div>
    <div class="feat-card"><div class="feat-icon">🎨</div><h3>Article Design Studio</h3><p>Control colors, fonts, and HTML structure. Every article matches your brand — not a generic template.</p></div>
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
      <div class="plan-feats">
        <div class="plan-feat">✅&nbsp; AI Article Generation</div>
        <div class="plan-feat">✅&nbsp; Midjourney Images (4/article)</div>
        <div class="plan-feat">✅&nbsp; WordPress Auto-Publish</div>
        <div class="plan-feat">✅&nbsp; Custom Prompts &amp; Design</div>
        <div class="plan-feat">✅&nbsp; Internal Linking</div>
        <div class="plan-feat no">✗&nbsp; Pinterest Auto-Post</div>
      </div>
      <button class="plan-btn" onclick="nav('signup')">Get Started →</button>
    </div>
    <div class="plan-card pro">
      <div class="plan-label">Pro · Most Popular</div>
      <div class="plan-price">$40</div>
      <div class="plan-period">per month</div>
      <div class="plan-feats">
        <div class="plan-feat">✅&nbsp; Everything in Basic</div>
        <div class="plan-feat">✅&nbsp; Pinterest Auto-Post</div>
        <div class="plan-feat">✅&nbsp; Pinterest Keyword Optimizer</div>
        <div class="plan-feat">✅&nbsp; Custom Pinterest Prompt</div>
        <div class="plan-feat">✅&nbsp; Pinterest Post Scheduler</div>
        <div class="plan-feat">✅&nbsp; Priority Support</div>
      </div>
      <button class="plan-btn" onclick="nav('signup')">Get Pro →</button>
    </div>
  </div>
</section>

<section class="section-dark" id="how">
  <div class="section-center">
    <span class="eyebrow eyebrow-light">How It Works</span>
    <h2 class="section-title-light">From Zero to Published in Minutes</h2>
    <p class="section-sub-light" style="margin-left:auto;margin-right:auto;">No technical skills needed. If you can paste a title, you can use NicheFlow AI.</p>
  </div>
  <div class="steps-grid">
    <div class="step-card"><div class="step-num">01</div><h4>Sign Up &amp; Choose Plan</h4><p>Create your account and pick Basic or Pro.</p></div>
    <div class="step-card"><div class="step-num">02</div><h4>Add Your Credentials</h4><p>Enter your Groq key, Midjourney key, and WordPress password once in Settings.</p></div>
    <div class="step-card"><div class="step-num">03</div><h4>Write Your Prompts</h4><p>Customize article and card prompts to match your niche voice.</p></div>
    <div class="step-card"><div class="step-num">04</div><h4>Paste Titles &amp; Go</h4><p>Drop in titles and hit Generate. NicheFlow writes, designs, and publishes everything.</p></div>
  </div>
</section>

<section class="section">
  <div class="cta-banner">
    <span class="eyebrow eyebrow-light">Start Today</span>
    <h2 class="section-title" style="color:#fdf6e8;position:relative;z-index:1;">Ready to Automate Your Content?</h2>
    <p class="section-sub" style="color:rgba(253,246,232,.5);margin:0 auto 36px;position:relative;z-index:1;">Join bloggers who publish more, stress less, and grow faster.</p>
    <button class="btn-primary" onclick="nav('signup')" style="background:var(--gold);position:relative;z-index:1;">Get Started Free →</button>
  </div>
</section>

<footer>
  <div class="f-logo">✦ NicheFlow AI</div>
  <p>AI-powered blog &amp; Pinterest content generator</p>
  <p style="color:#b0a080;margin-top:14px;">© 2026 NicheFlow AI · All rights reserved</p>
</footer>

{NAV_JS}
"""
    components.html(html, height=4400, scrolling=True)


# ═══════════════════════════════════════════════════════════════════════════
#  LOGIN
# ═══════════════════════════════════════════════════════════════════════════
def page_login():
    error = st.session_state.auth_error
    success = st.session_state.auth_success

    html = f"""{FONTS}{BASE_CSS}
<style>
body{{min-height:100vh;background:linear-gradient(160deg,#fdfaf4 0%,#f0e3c8 100%);}}
.wrap{{display:flex;align-items:center;justify-content:center;min-height:calc(100vh - 60px);padding:40px 20px;}}
.card{{background:#fff;border:1px solid var(--border);border-radius:26px;padding:clamp(36px,5vw,56px) clamp(30px,4.5vw,52px);width:100%;max-width:450px;box-shadow:0 12px 56px rgba(0,0,0,.08);}}
.logo{{font-family:'Fraunces',serif;font-size:20px;font-weight:800;color:var(--text);margin-bottom:28px;text-align:center;}}
.logo em{{color:var(--gold);font-style:normal;}}
h2{{font-family:'Fraunces',serif;font-size:30px;font-weight:800;color:var(--text);margin-bottom:5px;text-align:center;}}
.sub{{font-size:14.5px;color:var(--text3);text-align:center;margin-bottom:28px;}}
.err{{background:#fff0f0;border:1px solid #ffd0d0;color:#c03030;border-radius:9px;padding:10px 14px;font-size:13.5px;margin-bottom:14px;}}
.suc{{background:#f0faf4;border:1px solid #a4d8b8;color:#1a6e38;border-radius:9px;padding:10px 14px;font-size:13.5px;margin-bottom:14px;}}
.foot{{text-align:center;margin-top:18px;font-size:13.5px;color:var(--text3);}}
.foot a{{color:var(--gold);font-weight:600;cursor:pointer;}}
.back-lnk{{display:block;text-align:center;margin-top:12px;font-size:13px;color:var(--text3);cursor:pointer;}}
.back-lnk:hover{{color:var(--gold);}}
</style>
<a class="back-nav" onclick="nav('home')">
  <svg viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>
  Back to Home
</a>
<div class="wrap">
  <div class="card">
    <div class="logo">✦ <em>NicheFlow</em> AI</div>
    <h2>Welcome Back</h2>
    <p class="sub">Sign in to your NicheFlow AI account</p>
    {'<div class="err">❌ ' + error + '</div>' if error else ''}
    {'<div class="suc">✅ ' + success + '</div>' if success else ''}
    <div style="min-height:220px;"></div>
    <p class="foot">No account? <a onclick="nav('signup')">Sign up free</a></p>
    <a class="back-lnk" onclick="nav('home')">← Back to home</a>
  </div>
</div>
{NAV_JS}
"""
    components.html(html, height=700, scrolling=False)

    st.markdown("""
<style>
.stTextInput > div > div > input {
  border: 1.5px solid #dfd4bc !important; border-radius: 11px !important;
  padding: 12px 15px !important; font-size: 14.5px !important;
  font-family: 'Outfit', sans-serif !important; background: #fdfaf5 !important; color: #1a1510 !important;
}
.stTextInput > div > div > input:focus { border-color: #c9892a !important; box-shadow: 0 0 0 3px rgba(201,137,42,.12) !important; }
.stTextInput label { font-size: 13px !important; font-weight: 600 !important; color: #5a5040 !important; font-family: 'Outfit', sans-serif !important; }
.stForm [data-testid="stFormSubmitButton"] button {
  width: 100% !important; padding: 13px !important; background: #0f0d09 !important;
  color: #fff !important; border: none !important; border-radius: 11px !important;
  font-size: 15px !important; font-weight: 700 !important; font-family: 'Outfit', sans-serif !important; margin-top: 6px !important;
}
.stForm [data-testid="stFormSubmitButton"] button:hover { background: #1c1810 !important; }
[data-testid="stForm"] {
  max-width: 450px !important; margin: -580px auto 0 auto !important;
  padding: 0 clamp(30px,4.5vw,52px) !important; background: transparent !important; border: none !important;
}
</style>
""", unsafe_allow_html=True)

    with st.form("login_form"):
        email = st.text_input("Email Address", placeholder="your@email.com")
        password = st.text_input("Password", type="password", placeholder="Your password")
        submitted = st.form_submit_button("Sign In →")
        if submitted:
            if not email or not password:
                st.session_state.auth_error = "Please fill in both fields."; st.rerun()
            else:
                st.session_state.auth_success = ""
                do_login(email, password); st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
#  SIGNUP
# ═══════════════════════════════════════════════════════════════════════════
def page_signup():
    error = st.session_state.auth_error

    html = f"""{FONTS}{BASE_CSS}
<style>
body{{min-height:100vh;background:linear-gradient(160deg,#fdfaf4 0%,#f0e3c8 100%);}}
.wrap{{display:flex;align-items:center;justify-content:center;min-height:calc(100vh - 60px);padding:40px 20px;}}
.card{{background:#fff;border:1px solid var(--border);border-radius:26px;padding:clamp(36px,5vw,56px) clamp(30px,4.5vw,52px);width:100%;max-width:450px;box-shadow:0 12px 56px rgba(0,0,0,.08);}}
.logo{{font-family:'Fraunces',serif;font-size:20px;font-weight:800;color:var(--text);margin-bottom:28px;text-align:center;}}
.logo em{{color:var(--gold);font-style:normal;}}
h2{{font-family:'Fraunces',serif;font-size:30px;font-weight:800;color:var(--text);margin-bottom:5px;text-align:center;}}
.sub{{font-size:14.5px;color:var(--text3);text-align:center;margin-bottom:28px;}}
.err{{background:#fff0f0;border:1px solid #ffd0d0;color:#c03030;border-radius:9px;padding:10px 14px;font-size:13.5px;margin-bottom:14px;}}
.foot{{text-align:center;margin-top:18px;font-size:13.5px;color:var(--text3);}}
.foot a{{color:var(--gold);font-weight:600;cursor:pointer;}}
.back-lnk{{display:block;text-align:center;margin-top:12px;font-size:13px;color:var(--text3);cursor:pointer;}}
</style>
<a class="back-nav" onclick="nav('home')">
  <svg viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>
  Back to Home
</a>
<div class="wrap">
  <div class="card">
    <div class="logo">✦ <em>NicheFlow</em> AI</div>
    <h2>Create Account</h2>
    <p class="sub">Start automating your content today</p>
    {'<div class="err">❌ ' + error + '</div>' if error else ''}
    <div style="min-height:260px;"></div>
    <p class="foot">Already have an account? <a onclick="nav('login')">Sign in</a></p>
    <a class="back-lnk" onclick="nav('home')">← Back to home</a>
  </div>
</div>
{NAV_JS}
"""
    components.html(html, height=780, scrolling=False)

    st.markdown("""
<style>
[data-testid="stForm"] {
  max-width: 450px !important; margin: -640px auto 0 auto !important;
  padding: 0 clamp(30px,4.5vw,52px) !important; background: transparent !important; border: none !important;
}
.stTextInput > div > div > input {
  border: 1.5px solid #dfd4bc !important; border-radius: 11px !important;
  padding: 12px 15px !important; font-size: 14.5px !important;
  font-family: 'Outfit', sans-serif !important; background: #fdfaf5 !important; color: #1a1510 !important;
}
.stTextInput > div > div > input:focus { border-color: #c9892a !important; box-shadow: 0 0 0 3px rgba(201,137,42,.12) !important; }
.stTextInput label { font-size: 13px !important; font-weight: 600 !important; color: #5a5040 !important; }
.stForm [data-testid="stFormSubmitButton"] button {
  width: 100% !important; padding: 13px !important; background: #0f0d09 !important;
  color: #fff !important; border: none !important; border-radius: 11px !important;
  font-size: 15px !important; font-weight: 700 !important; font-family: 'Outfit', sans-serif !important; margin-top: 6px !important;
}
</style>
""", unsafe_allow_html=True)

    with st.form("signup_form"):
        email = st.text_input("Email Address", placeholder="your@email.com")
        password = st.text_input("Password", type="password", placeholder="At least 6 characters")
        confirm = st.text_input("Confirm Password", type="password", placeholder="Repeat your password")
        submitted = st.form_submit_button("Create Account →")
        if submitted:
            st.session_state.auth_error = ""
            do_signup(email, password, confirm); st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
#  DOCS
# ═══════════════════════════════════════════════════════════════════════════
def page_docs():
    logged_in = bool(st.session_state.user_id)
    dest = 'dashboard' if logged_in else 'login'
    html = f"""{FONTS}{BASE_CSS}
<style>
.docs-layout{{display:grid;grid-template-columns:210px 1fr;gap:24px;align-items:start;padding:32px clamp(24px,6vw,96px) 80px;max-width:1200px;margin:0 auto;}}
@media(max-width:740px){{.docs-layout{{grid-template-columns:1fr;}}}}
.docs-toc{{background:#fff;border:1px solid var(--border);border-radius:14px;padding:18px;position:sticky;top:80px;}}
.docs-toc h4{{font-size:10.5px;font-weight:700;color:var(--text3);text-transform:uppercase;letter-spacing:2px;margin-bottom:12px;}}
.docs-toc a{{display:block;font-size:13px;color:var(--text2);padding:7px 9px;border-radius:7px;cursor:pointer;text-decoration:none;transition:all .2s;margin-bottom:1px;}}
.docs-toc a:hover,.docs-toc a.active{{background:#fff8ec;color:var(--gold);font-weight:600;}}
.docs-sec{{background:#fff;border:1px solid var(--border);border-radius:18px;padding:26px 30px;margin-bottom:16px;}}
.docs-sec h2{{font-family:'Fraunces',serif;font-size:19px;font-weight:800;color:var(--text);margin-bottom:14px;padding-bottom:12px;border-bottom:1px solid #f0e6d4;display:flex;align-items:center;gap:10px;}}
.docs-sec h3{{font-size:14px;font-weight:700;color:var(--text);margin:16px 0 7px;}}
.docs-sec p{{font-size:13.5px;color:var(--text2);line-height:1.8;margin-bottom:10px;}}
.docs-sec ol,.docs-sec ul{{padding-left:20px;margin:7px 0 10px;}}
.docs-sec li{{font-size:13.5px;color:var(--text2);line-height:1.8;margin-bottom:4px;}}
.docs-sec strong{{color:var(--text);}}
.doc-note{{background:#fff8ec;border-left:3px solid var(--gold);border-radius:0 9px 9px 0;padding:10px 14px;margin:10px 0;font-size:13px;color:#7a5820;line-height:1.7;}}
.doc-warn{{background:#fff4ec;border-left:3px solid #e8703a;border-radius:0 9px 9px 0;padding:10px 14px;margin:10px 0;font-size:13px;color:#8a3a10;line-height:1.7;}}
.doc-eg{{background:#f8f3ea;border:1px solid #e4d8c4;border-radius:10px;padding:13px 16px;margin:9px 0;font-size:13px;color:#5a4a34;line-height:1.75;font-style:italic;}}
.step-badge{{display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;min-width:26px;background:var(--dark);color:var(--cream);border-radius:50%;font-size:12px;font-weight:700;}}
.docs-header{{padding:32px clamp(24px,6vw,96px) 0;max-width:1200px;margin:0 auto;}}
</style>

<nav>
  <div class="nav-logo" onclick="nav('home')">✦ <em>Niche</em>Flow AI</div>
  <div class="nav-links">
    <a onclick="nav('home')">← Home</a>
    <a class="nav-cta" onclick="nav('{dest}')">{'Dashboard →' if logged_in else 'Sign In →'}</a>
  </div>
</nav>
<a class="back-nav" onclick="nav('home')">
  <svg viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>
  Back to Home
</a>
<div class="docs-header">
  <span style="font-size:11px;font-weight:700;color:var(--gold);text-transform:uppercase;letter-spacing:3.5px;">Documentation</span>
  <h2 style="font-family:'Fraunces',serif;font-size:clamp(28px,4vw,44px);font-weight:800;color:var(--text);margin:8px 0 6px;">Setup Guide</h2>
  <p style="font-size:16px;color:var(--text2);margin-bottom:32px;">Get fully set up and publishing in under 10 minutes.</p>
</div>
<div class="docs-layout">
  <div class="docs-toc">
    <h4>On This Page</h4>
    <a onclick="sDoc('d-groq',this)" class="active">1. Groq API Key</a>
    <a onclick="sDoc('d-mj',this)">2. Midjourney Key</a>
    <a onclick="sDoc('d-wp',this)">3. WordPress Setup</a>
    <a onclick="sDoc('d-pin',this)">4. Pinterest (Pro)</a>
    <a onclick="sDoc('d-prompt',this)">5. Article Prompts</a>
    <a onclick="sDoc('d-card',this)">6. Niche Cards</a>
    <a onclick="sDoc('d-design',this)">7. Design Studio</a>
    <a onclick="sDoc('d-pprompt',this)">8. Pinterest Prompt</a>
    <a onclick="sDoc('d-tips',this)">9. Best Practices</a>
  </div>
  <div>
    <div class="docs-sec" id="d-groq">
      <h2><span class="step-badge">1</span> Get Your Groq API Key (Free)</h2>
      <p>Groq is the AI engine that writes your articles. The free tier provides more than enough requests for daily publishing.</p>
      <ol>
        <li>Go to <strong>console.groq.com</strong> and create a free account</li>
        <li>In the left sidebar, click <strong>API Keys</strong></li>
        <li>Click <strong>Create API Key</strong> and name it "NicheFlow"</li>
        <li>Copy the key — it begins with <strong>gsk_</strong></li>
        <li>Paste it in your dashboard under <strong>Settings → Groq API Key</strong></li>
      </ol>
      <div class="doc-note">Groq's free tier provides 14,400 requests per day — more than enough for regular daily publishing.</div>
      <div class="doc-warn">⚠️ Keep your article prompt under 2000 tokens (~1500 words) to stay within Groq's rate limits.</div>
    </div>
    <div class="docs-sec" id="d-mj">
      <h2><span class="step-badge">2</span> Get Your Midjourney API Key</h2>
      <p>GoAPI connects NicheFlow to Midjourney so 4 images are generated and uploaded automatically for every article.</p>
      <ol>
        <li>Go to <strong>goapi.ai</strong> and create an account</li>
        <li>Choose a plan — pay-as-you-go works well for most users</li>
        <li>Navigate to <strong>Dashboard → API Keys</strong></li>
        <li>Copy your key and paste it in <strong>Settings → Midjourney API Key</strong></li>
      </ol>
      <div class="doc-note">Each article generates 4 images, each costing a few cents on GoAPI's pay-as-you-go plan.</div>
    </div>
    <div class="docs-sec" id="d-wp">
      <h2><span class="step-badge">3</span> Connect Your WordPress Site</h2>
      <ol>
        <li>Log in to your <strong>WordPress Dashboard</strong></li>
        <li>Go to <strong>Users → Your Profile</strong></li>
        <li>Scroll down to <strong>Application Passwords</strong></li>
        <li>Enter a name: <strong>NicheFlow AI</strong> → click <strong>Add New Application Password</strong></li>
        <li>Copy the generated password (format: xxxx xxxx xxxx xxxx)</li>
        <li>In Settings enter your URL as <strong>https://yoursite.com</strong></li>
        <li>Enter credentials as <strong>YourUsername:xxxx xxxx xxxx xxxx</strong></li>
      </ol>
      <div class="doc-note">Make sure your URL includes https:// and has no trailing slash.</div>
    </div>
    <div class="docs-sec" id="d-pin">
      <h2><span class="step-badge">4</span> Set Up Pinterest &nbsp;<span style="font-size:12px;font-weight:700;color:var(--gold);background:#fff8ec;padding:3px 10px;border-radius:100px;">Pro Plan</span></h2>
      <ol>
        <li>Go to <strong>developers.pinterest.com</strong> and log in</li>
        <li>Create a new app — enable permissions: <strong>boards:read</strong> and <strong>pins:write</strong></li>
        <li>Generate a <strong>User Access Token</strong></li>
        <li>Find your <strong>Board ID</strong> from your Pinterest board URL</li>
        <li>Paste both into the Pinterest tab along with your custom prompt</li>
      </ol>
      <div class="doc-note">The Pin image is automatically taken from your article's WordPress featured image.</div>
    </div>
    <div class="docs-sec" id="d-prompt">
      <h2><span class="step-badge">5</span> Write Your Article Prompt</h2>
      <p>Your prompt tells the AI exactly how to write for your niche. <strong>You write it — no defaults imposed.</strong></p>
      <h3>Food Blog Example</h3>
      <div class="doc-eg">Write a warm, personal recipe article in first person. Open with a nostalgic story. Include a "Why You'll Love This" section, 8 expert tips, variations, storage instructions, and 3 FAQs. Friendly tone for home cooks. 1200–1500 words.</div>
      <h3>Travel Blog Example</h3>
      <div class="doc-eg">Write an inspiring travel guide in second person. Open with a vivid sensory scene. Cover top 5 attractions, local food, best time to visit, budget, and 5 practical tips. Target budget adventurers aged 25–40.</div>
      <div class="doc-warn">⚠️ Keep prompts under 2000 tokens (roughly 1500 words) to avoid Groq rate limits.</div>
    </div>
    <div class="docs-sec" id="d-card">
      <h2><span class="step-badge">6</span> Customize Your Niche Card</h2>
      <p>The niche card is a styled block added inside every article. You define what data it shows.</p>
      <h3>Recipe Card Example</h3>
      <div class="doc-eg">Create a recipe card with: prep time, cook time, total time, servings, calories, a list of ingredients with quantities, and step-by-step instructions.</div>
      <h3>Travel Card Example</h3>
      <div class="doc-eg">Create a destination card with: best time to visit, average daily budget (USD), language, currency, visa required (yes/no), and top 3 attractions.</div>
      <div class="doc-note">Toggle the niche card on or off from the Generate tab. Card colors follow your Design Studio settings.</div>
    </div>
    <div class="docs-sec" id="d-design">
      <h2><span class="step-badge">7</span> Article Design Studio</h2>
      <p>Control the look of every article your NicheFlow publishes.</p>
      <ul>
        <li><strong>Main Color</strong> — used for headings and accents</li>
        <li><strong>Accent Color</strong> — used for highlighted boxes and borders</li>
        <li><strong>Font Family</strong> — choose the font for article body text</li>
        <li><strong>HTML Structure</strong> — paste a custom HTML/CSS template the AI will follow</li>
      </ul>
      <div class="doc-note">The live preview in Design Studio shows exactly how your articles will look before you generate.</div>
    </div>
    <div class="docs-sec" id="d-pprompt">
      <h2><span class="step-badge">8</span> Pinterest Prompt &nbsp;<span style="font-size:12px;font-weight:700;color:var(--gold);background:#fff8ec;padding:3px 10px;border-radius:100px;">Pro Plan</span></h2>
      <p>Your Pinterest prompt tells the AI about your audience so it generates optimized Pin titles, descriptions, and alt text.</p>
      <div class="doc-eg">My audience is busy moms who love quick weeknight dinner recipes. Write warm, conversational pin descriptions using keywords like family dinner, easy recipes, weeknight meals. Keep under 200 characters with a call to action.</div>
    </div>
    <div class="docs-sec" id="d-tips">
      <h2><span class="step-badge">9</span> Best Practices</h2>
      <ul>
        <li><strong>Use descriptive titles</strong> — "Easy Creamy Tuscan Chicken Pasta" gets far better results than "Pasta"</li>
        <li><strong>Set a 5–10 second delay</strong> between articles to stay within Groq's rate limits</li>
        <li><strong>Start with Draft status</strong> so you can review articles before they go live</li>
        <li><strong>Customize your article prompt</strong> — this has the biggest impact on quality</li>
        <li><strong>Test with one article first</strong> before running a bulk batch</li>
        <li><strong>Keep your API keys private</strong> — never share them or include them in screenshots</li>
        <li><strong>Enable Internal Linking</strong> to automatically link to your existing published posts</li>
      </ul>
    </div>
  </div>
</div>

<footer>
  <div class="f-logo">✦ NicheFlow AI</div>
  <p>AI-powered blog &amp; Pinterest content generator</p>
  <p style="color:#b0a080;margin-top:14px;">© 2026 NicheFlow AI · All rights reserved</p>
</footer>

<script>
function sDoc(id, el) {{
  document.getElementById(id).scrollIntoView({{behavior:'smooth',block:'start'}});
  document.querySelectorAll('.docs-toc a').forEach(x => x.classList.remove('active'));
  el.classList.add('active');
}}
</script>
{NAV_JS}
"""
    components.html(html, height=4600, scrolling=True)


# ═══════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════
def page_dashboard():
    s = st.session_state
    plan = s.user_plan
    cfg = s.settings

    st.markdown("""
<style>
section[data-testid="stSidebar"]{display:flex!important;background:#0f0d09!important;}
[data-testid="stSidebarContent"]{background:#0f0d09!important;padding:0!important;}
section[data-testid="stSidebar"] .stButton button{
  width:100%;text-align:left;background:transparent;border:none;
  color:rgba(253,246,232,.5);font-size:13.5px;font-weight:500;
  padding:10px 13px;border-radius:9px;font-family:'Outfit',sans-serif;transition:all .2s;margin-bottom:2px;
}
section[data-testid="stSidebar"] .stButton button:hover{background:rgba(255,255,255,.07);color:#fdf6e8;}
</style>
""", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,800&family=Outfit:wght@400;500;600&display=swap" rel="stylesheet">
<div style="padding:22px 22px 18px;font-family:'Fraunces',serif;font-size:19px;font-weight:800;color:#fdf6e8;border-bottom:1px solid rgba(255,255,255,.07);">
  ✦ <em style="color:#c9892a;font-style:normal;">Niche</em>Flow AI</div>
<div style="padding:15px 22px 15px;border-bottom:1px solid rgba(255,255,255,.07);">
  <div style="font-size:13.5px;font-weight:600;color:#fdf6e8;">{s.user_email or 'User'}</div>
  <div style="font-size:11.5px;color:{'#e8a83e' if plan=='pro' else 'rgba(253,246,232,.4)'};margin-top:3px;">
    {'⭐ Pro Plan · $40/mo' if plan=='pro' else '📦 Basic Plan · $30/mo'}</div>
</div>
<div style="padding:10px;"></div>
""", unsafe_allow_html=True)

        tabs = [
            ("overview","📊  Overview"), ("generate","✍️  Generate"),
            ("settings","⚙️  Settings"), ("prompts","📝  Prompts"),
            ("design","🎨  Design Studio"), ("pinterest","📌  Pinterest"),
            ("billing","💳  Billing"), ("docs","📖  Documentation"),
        ]
        for key, label in tabs:
            if st.button(label, key=f"sb_{key}"):
                s.dash_tab = key; st.rerun()

        st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
        if st.button("🚪  Sign Out", key="sb_logout"):
            do_logout(); st.rerun()

    tab = s.dash_tab
    tab_titles = {
        "overview":("Overview","Your NicheFlow AI dashboard"),
        "generate":("Generate Articles","Paste titles and publish automatically"),
        "settings":("Settings","API credentials and publishing preferences"),
        "prompts":("Prompts","Customize how your content is generated"),
        "design":("Design Studio","Control how your articles look"),
        "pinterest":("Pinterest","Configure Pinterest auto-posting"),
        "billing":("Billing","Manage your plan and subscription"),
        "docs":("Documentation","Setup guide and best practices"),
    }
    title, subtitle = tab_titles.get(tab, ("Dashboard",""))
    st.markdown(f"""
<style>
:root{{--gold:#c9892a;--gold2:#e8a83e;--dark:#0f0d09;--dark2:#1c1810;--text:#1a1510;--text2:#5a5040;--text3:#8a7a60;--border:#dfd4bc;--cream:#faf6ef;}}
.dash-top{{background:rgba(245,240,230,.97);border-bottom:1px solid var(--border);padding:20px 30px;margin:-1rem -1rem 24px -1rem;}}
.dash-top h1{{font-family:'Fraunces',serif;font-size:22px;font-weight:800;color:var(--text);margin:0;}}
.dash-top p{{font-size:12.5px;color:var(--text3);margin:4px 0 0;}}
.card{{background:#fff;border:1px solid var(--border);border-radius:18px;padding:24px;margin-bottom:18px;}}
.card h3{{font-size:14.5px;font-weight:700;color:var(--text);margin:0 0 16px;padding-bottom:13px;border-bottom:1px solid #f0e6d4;}}
.note{{background:#fff8ec;border-left:4px solid var(--gold);border-radius:0 8px 8px 0;padding:10px 14px;font-size:13px;color:#7a5820;margin-bottom:14px;}}
.warn{{background:#fff4ec;border-left:4px solid #e8703a;border-radius:0 8px 8px 0;padding:10px 14px;font-size:13px;color:#8a3a10;margin-bottom:14px;}}
.ok{{background:#f0faf4;border:1px solid #a4d8b8;color:#1a6e38;border-radius:9px;padding:10px 14px;font-size:13px;margin-bottom:12px;}}
.err{{background:#fff0f0;border:1px solid #ffd0d0;color:#c03030;border-radius:9px;padding:10px 14px;font-size:13px;margin-bottom:12px;}}
.stat-box{{background:#fff;border:1px solid var(--border);border-radius:14px;padding:20px;text-align:center;}}
.stat-v{{font-family:'Fraunces',serif;font-size:34px;font-weight:800;color:var(--gold);line-height:1;}}
.stat-l{{font-size:11.5px;color:var(--text3);margin-top:4px;}}
</style>
<div class="dash-top"><h1>{title}</h1><p>{subtitle}</p></div>
""", unsafe_allow_html=True)

    if tab == "overview":    dash_overview(cfg, plan)
    elif tab == "generate":  dash_generate(cfg, plan)
    elif tab == "settings":  dash_settings(cfg)
    elif tab == "prompts":   dash_prompts(cfg, plan)
    elif tab == "design":    dash_design(cfg)
    elif tab == "pinterest": dash_pinterest(cfg, plan)
    elif tab == "billing":   dash_billing(plan)
    elif tab == "docs":      page_docs()


def dash_overview(cfg, plan):
    c1,c2,c3,c4 = st.columns(4)
    for col,icon,val,label in [
        (c1,"✍️",cfg.get("articles_generated",0),"Articles Generated"),
        (c2,"🎨",cfg.get("images_created",0),"Images Created"),
        (c3,"🌐",cfg.get("posts_published",0),"Posts Published"),
        (c4,"📌",cfg.get("pins_posted",0),"Pins Posted"),
    ]:
        with col:
            st.markdown(f'<div class="stat-box"><div style="font-size:22px;margin-bottom:8px;">{icon}</div><div class="stat-v">{val}</div><div class="stat-l">{label}</div></div>', unsafe_allow_html=True)
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("""<div class="card"><h3>🚀 Quick Start</h3>
<p style="font-size:13.5px;color:#5a5040;line-height:2.2;">
1. Add your API keys in <strong>Settings</strong><br>
2. Write your prompts in <strong>Prompts</strong><br>
3. Style your articles in <strong>Design Studio</strong><br>
4. Go to <strong>Generate</strong> and paste titles</p></div>""", unsafe_allow_html=True)
    with c2:
        if plan == "pro":
            st.markdown('<div class="card" style="background:linear-gradient(135deg,#1c1810,#0f0d09);border-color:rgba(201,137,42,.3);"><h3 style="color:#e8a83e;border-color:rgba(255,255,255,.07);">⭐ Pro Plan Active</h3><p style="font-size:13px;color:rgba(253,246,232,.6);line-height:1.7;">All features unlocked — including Pinterest Auto-Post and Scheduler.</p></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="card" style="background:linear-gradient(135deg,#1c1810,#0f0d09);border-color:rgba(201,137,42,.3);"><h3 style="color:#e8a83e;border-color:rgba(255,255,255,.07);">📦 Basic Plan</h3><p style="font-size:13px;color:rgba(253,246,232,.6);line-height:1.7;">Upgrade to Pro ($40/mo) to unlock Pinterest Auto-Post, Scheduler, and priority support.</p></div>', unsafe_allow_html=True)
            if st.button("⬆️ Upgrade to Pro", key="ov_upgrade"):
                st.session_state.dash_tab = "billing"; st.rerun()


def dash_settings(cfg):
    s = st.session_state
    if s.save_ok:
        st.markdown(f'<div class="ok">✅ {s.save_msg}</div>', unsafe_allow_html=True)
        s.save_ok = False

    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div class="card"><h3>🔑 API Credentials</h3>', unsafe_allow_html=True)
        groq_key = st.text_input("Groq API Key", value=cfg.get("groq_key",""), type="password", placeholder="gsk_...")
        tc1,tc2 = st.columns([1,2])
        with tc1:
            if st.button("Test Groq", key="test_groq"):
                s.test_results["groq"] = test_groq_key(groq_key) if GEN_OK and groq_key else {"success":False,"message":"Enter a key first"}
        with tc2:
            if "groq" in s.test_results:
                r = s.test_results["groq"]
                st.markdown(f'<div style="font-size:12px;padding:6px 0;color:{"#1a6e38" if r["success"] else "#c03030"};">{r["message"]}</div>', unsafe_allow_html=True)

        mj_key = st.text_input("Midjourney API Key (GoAPI)", value=cfg.get("mj_key",""), type="password")
        tc1,tc2 = st.columns([1,2])
        with tc1:
            if st.button("Test GoAPI", key="test_goapi"):
                s.test_results["goapi"] = test_goapi_key(mj_key) if GEN_OK and mj_key else {"success":False,"message":"Enter a key first"}
        with tc2:
            if "goapi" in s.test_results:
                r = s.test_results["goapi"]
                st.markdown(f'<div style="font-size:12px;padding:6px 0;color:{"#1a6e38" if r["success"] else "#c03030"};">{r["message"]}</div>', unsafe_allow_html=True)

        wp_url = st.text_input("WordPress Site URL", value=cfg.get("wp_url",""), placeholder="https://yoursite.com")
        wp_password = st.text_input("WordPress App Password", value=cfg.get("wp_password",""), type="password", placeholder="Username:xxxx xxxx xxxx xxxx")
        tc1,tc2 = st.columns([1,2])
        with tc1:
            if st.button("Test WordPress", key="test_wp"):
                if GEN_OK and wp_url and wp_password:
                    r = test_wordpress(wp_url, wp_password)
                    s.test_results["wp"] = r
                    if r["success"]: s.wp_categories = fetch_wp_categories(wp_url, wp_password)
                else:
                    s.test_results["wp"] = {"success":False,"message":"Enter URL and password first"}
        with tc2:
            if "wp" in s.test_results:
                r = s.test_results["wp"]
                st.markdown(f'<div style="font-size:12px;padding:6px 0;color:{"#1a6e38" if r["success"] else "#c03030"};">{r["message"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="card"><h3>⚙️ Publishing Preferences</h3>', unsafe_allow_html=True)
        publish_status = st.selectbox("Publish Status", ["draft","publish"], index=0 if cfg.get("publish_status","draft")=="draft" else 1)
        st.markdown('<div class="note">💡 Start with <strong>Draft</strong> — review articles before they go live.</div>', unsafe_allow_html=True)
        use_images = st.toggle("Generate Midjourney Images", value=bool(cfg.get("use_images",True)))
        show_card  = st.toggle("Include Info Card in Articles", value=bool(cfg.get("show_card",True)))
        card_click = st.toggle("Card Clickable in WordPress", value=bool(cfg.get("card_clickable",False)))
        st.markdown("**🎞️ Midjourney Prompt Template**")
        mj_template = st.text_area("MJ Template", value=cfg.get("mj_template",""), height=80,
            placeholder="Close up {recipe_name}, food photography, natural light --ar 2:3 --v 6.1", label_visibility="collapsed")
        st.caption("Use `{recipe_name}` as placeholder for the article title")
        st.markdown("**🔗 Internal Linking**")
        use_links = st.toggle("Enable Internal Linking", value=bool(cfg.get("use_internal_links",False)))
        max_links = int(cfg.get("max_links",4))
        if use_links:
            max_links = st.slider("Max links per article", 1, 8, max_links)
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("💾 Save Settings", type="primary", key="save_settings"):
        new = {"groq_key":groq_key,"mj_key":mj_key,"wp_url":wp_url,"wp_password":wp_password,
               "publish_status":publish_status,"use_images":use_images,"show_card":show_card,
               "card_clickable":card_click,"mj_template":mj_template,"use_internal_links":use_links,"max_links":max_links}
        st.session_state.settings.update(new)
        db_save(st.session_state.user_id, new)
        st.session_state.save_ok = True; st.session_state.save_msg = "Settings saved successfully!"; st.rerun()


def dash_prompts(cfg, plan):
    s = st.session_state
    if s.save_ok:
        st.markdown(f'<div class="ok">✅ {s.save_msg}</div>', unsafe_allow_html=True)
        s.save_ok = False

    st.markdown('<div class="warn">⚠️ <strong>Token Warning:</strong> Keep your article prompt under 2000 tokens (~1500 words) to avoid Groq rate limits.</div>', unsafe_allow_html=True)
    t1,t2,t3 = st.tabs(["✍️ Article Prompt","🃏 Card Prompt","📌 Pinterest Prompt"])

    with t1:
        st.markdown('<div class="card"><h3>✍️ Article Writing Prompt</h3>', unsafe_allow_html=True)
        article_prompt = st.text_area("Article Prompt", value=cfg.get("article_prompt",""), height=200,
            placeholder="Example — Recipe blog:\nWrite a warm, personal recipe article in first person...\n\nExample — Travel blog:\nWrite an inspiring travel guide in second person...",
            label_visibility="collapsed")
        st.markdown("**🏗️ Custom HTML Structure** *(optional)*")
        html_structure = st.text_area("HTML Structure", value=cfg.get("html_structure",""), height=120,
            placeholder='<h2 style="color:MAIN_COLOR;">Section Title</h2>', label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

    with t2:
        st.markdown('<div class="card"><h3>🃏 Niche Card Prompt</h3>', unsafe_allow_html=True)
        card_prompt = st.text_area("Card Prompt", value=cfg.get("card_prompt",""), height=180,
            placeholder="Example — Recipe card:\nCreate a recipe card with prep time, cook time, total time, servings, calories...",
            label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

    with t3:
        if plan != "pro":
            st.markdown("""<div style="background:linear-gradient(135deg,#1c1810,#0f0d09);border:1px solid rgba(201,137,42,.38);border-radius:18px;padding:32px;text-align:center;color:#fdf6e8;">
<div style="font-size:36px;margin-bottom:10px;">📌</div>
<h3 style="font-family:'Fraunces',serif;font-size:22px;font-weight:800;color:#fdf6e8;margin:0 0 8px;">Pinterest Prompt</h3>
<p style="font-size:13.5px;color:rgba(253,246,232,.5);line-height:1.7;">Available on the <span style="color:#e8a83e;font-weight:600;">Pro plan ($40/month)</span>.</p>
</div>""", unsafe_allow_html=True)
            pinterest_prompt = cfg.get("pinterest_prompt","")
        else:
            st.markdown('<div class="card"><h3>📌 Pinterest Prompt</h3>', unsafe_allow_html=True)
            pinterest_prompt = st.text_area("Pinterest Prompt", value=cfg.get("pinterest_prompt",""), height=160,
                placeholder="My audience is busy moms who love quick weeknight dinner recipes...", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)

    try: ap = article_prompt
    except: ap = cfg.get("article_prompt","")
    try: hs = html_structure
    except: hs = cfg.get("html_structure","")
    try: cp = card_prompt
    except: cp = cfg.get("card_prompt","")

    if st.button("💾 Save Prompts", type="primary", key="save_prompts"):
        new = {"article_prompt":ap,"html_structure":hs,"card_prompt":cp}
        if plan == "pro": new["pinterest_prompt"] = pinterest_prompt
        st.session_state.settings.update(new)
        db_save(st.session_state.user_id, new)
        st.session_state.save_ok = True; st.session_state.save_msg = "Prompts saved!"; st.rerun()


def dash_design(cfg):
    s = st.session_state
    if s.save_ok:
        st.markdown(f'<div class="ok">✅ {s.save_msg}</div>', unsafe_allow_html=True)
        s.save_ok = False

    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div class="card"><h3>🎨 Color & Font</h3>', unsafe_allow_html=True)
        main_color   = st.color_picker("Main Color (headings, accents)", value=cfg.get("design_main_color","#333333"))
        accent_color = st.color_picker("Accent / Highlight Color", value=cfg.get("design_accent_color","#ea580c"))
        font_opts   = ["inherit","'Georgia',serif","'Arial',sans-serif","'Verdana',sans-serif","'Trebuchet MS',sans-serif","'Times New Roman',serif","'Courier New',monospace"]
        font_labels = ["Site default","Georgia (serif)","Arial","Verdana","Trebuchet MS","Times New Roman","Courier New"]
        cur = cfg.get("design_font_family","inherit")
        fi  = font_opts.index(cur) if cur in font_opts else 0
        font_family = font_opts[st.selectbox("Article Font", range(len(font_labels)), format_func=lambda i: font_labels[i], index=fi)]
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="card"><h3>👁️ Live Preview</h3>
<div style="font-family:{font_family};border:1px solid #eee;border-radius:12px;padding:20px;background:#fafafa;">
  <h2 style="color:{main_color};font-size:18px;font-weight:800;margin:0 0 10px;">Your Article Title Here</h2>
  <p style="font-size:14px;color:#444;line-height:1.7;margin:0 0 14px;">This is how your article body text will look with your chosen font and color settings.</p>
  <div style="background:#f9f9f9;border-left:4px solid {accent_color};border-radius:0 8px 8px 0;padding:12px 16px;">
    <ul style="margin:0;padding-left:16px;line-height:2.2;font-size:13px;color:#444;">
      <li>Key tip or expert insight</li><li>Why readers will love this</li><li>Important fact or detail</li>
    </ul>
  </div>
</div></div>""", unsafe_allow_html=True)

    if st.button("💾 Save Design", type="primary", key="save_design"):
        new = {"design_main_color":main_color,"design_accent_color":accent_color,"design_font_family":font_family}
        st.session_state.settings.update(new)
        db_save(st.session_state.user_id, new)
        st.session_state.save_ok = True; st.session_state.save_msg = "Design settings saved!"; st.rerun()


def dash_generate(cfg, plan):
    s = st.session_state
    missing = []
    if not cfg.get("groq_key"):       missing.append("Groq API key")
    if not cfg.get("wp_url"):         missing.append("WordPress URL")
    if not cfg.get("wp_password"):    missing.append("WordPress App Password")
    if not cfg.get("article_prompt"): missing.append("Article Prompt")
    if missing:
        st.markdown(f'<div class="err">❌ Please configure first: <strong>{", ".join(missing)}</strong></div>', unsafe_allow_html=True)
        return

    st.markdown('<div class="card"><h3>📋 Article Titles</h3>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13px;color:#8a7a60;margin-bottom:14px;">One title per line.</p>', unsafe_allow_html=True)
    titles_raw = st.text_area("Titles", height=160,
        placeholder="How to Travel Europe on a Budget\n10 Best Hiking Trails in Colorado", label_visibility="collapsed")
    c1,c2,c3,c4 = st.columns(4)
    with c1: gen_images = st.toggle("Generate Images", value=bool(cfg.get("use_images",True)), key="g_img")
    with c2: gen_card   = st.toggle("Include Card",    value=bool(cfg.get("show_card",True)),  key="g_card")
    with c3: gen_links  = st.toggle("Internal Links",  value=bool(cfg.get("use_internal_links",False)), key="g_links")
    with c4: delay_sec  = st.number_input("Delay (sec)", 0, 30, 5, key="g_delay")
    show_logs = st.checkbox("Show processing logs", value=False, key="g_logs")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🚀 Generate & Publish All", type="primary", key="gen_go") and titles_raw.strip():
        titles = [t.strip() for t in titles_raw.strip().splitlines() if t.strip()]
        pipeline_cfg = {
            "groq_key":cfg.get("groq_key",""),"goapi_key":cfg.get("mj_key",""),
            "wp_url":cfg.get("wp_url",""),"wp_password":cfg.get("wp_password",""),
            "publish_status":cfg.get("publish_status","draft"),"mj_template":cfg.get("mj_template",""),
            "use_images":gen_images and bool(cfg.get("mj_key","")),"show_card":gen_card,
            "card_clickable":bool(cfg.get("card_clickable",False)),"use_internal_links":gen_links,
            "max_links":int(cfg.get("max_links",4)),"user_article_prompt":cfg.get("article_prompt",""),
            "user_html_structure":cfg.get("html_structure",""),"user_card_prompt":cfg.get("card_prompt",""),
            "user_design":{"main_color":cfg.get("design_main_color","#333333"),
                           "accent_color":cfg.get("design_accent_color","#ea580c"),
                           "font_family":cfg.get("design_font_family","inherit")},
        }
        log_box = st.empty(); all_logs = []
        for i, title in enumerate(titles):
            st.markdown(f'<div class="note">⏳ Processing <strong>{i+1}/{len(titles)}</strong>: {title}</div>', unsafe_allow_html=True)
            def log_fn(msg, _logs=all_logs, _box=log_box, _show=show_logs):
                _logs.append(str(msg))
                if _show:
                    _box.markdown('<div style="background:#1a1510;border-radius:10px;padding:14px;font-family:monospace;font-size:12px;color:#a0c080;max-height:200px;overflow-y:auto;">'+'<br>'.join(_logs[-20:])+'</div>', unsafe_allow_html=True)
            result = run_full_pipeline(title, pipeline_cfg, log_fn=log_fn) if GEN_OK else {"success":False,"error":"generator.py not found"}
            if result.get("success"):
                post_url = result.get("post_url","")
                st.markdown(f'<div class="ok">✅ <strong>{title}</strong> → <a href="{post_url}" target="_blank">{post_url or "view post"}</a></div>', unsafe_allow_html=True)
                db_inc(s.user_id,"articles_generated"); db_inc(s.user_id,"posts_published")
                if result.get("image_count",0): db_inc(s.user_id,"images_created",result["image_count"])
            else:
                st.markdown(f'<div class="err">❌ <strong>{title}</strong>: {result.get("error","Unknown error")}</div>', unsafe_allow_html=True)
            if i < len(titles)-1 and delay_sec > 0: time.sleep(delay_sec)
        s.settings = db_load(s.user_id)


def dash_pinterest(cfg, plan):
    s = st.session_state
    if plan != "pro":
        st.markdown("""<div style="background:linear-gradient(135deg,#1c1810,#0f0d09);border:1px solid rgba(201,137,42,.38);border-radius:18px;padding:36px;text-align:center;color:#fdf6e8;margin-bottom:22px;">
<div style="font-size:44px;margin-bottom:14px;">📌</div>
<h3 style="font-family:'Fraunces',serif;font-size:26px;font-weight:800;color:#fdf6e8;margin:0 0 10px;">Pinterest Auto-Post</h3>
<p style="font-size:14px;color:rgba(253,246,232,.5);line-height:1.7;max-width:480px;margin:0 auto 20px;">
Available on the <span style="color:#e8a83e;font-weight:700;">Pro plan ($40/month)</span>.</p></div>""", unsafe_allow_html=True)
        if st.button("⬆️ Upgrade to Pro", key="pin_upgrade"):
            s.dash_tab = "billing"; st.rerun()
        return

    if s.save_ok:
        st.markdown(f'<div class="ok">✅ {s.save_msg}</div>', unsafe_allow_html=True)
        s.save_ok = False

    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div class="card"><h3>🔑 Pinterest Credentials</h3>', unsafe_allow_html=True)
        pin_token = st.text_input("Pinterest Access Token", value=cfg.get("pinterest_token",""), type="password")
        pin_board = st.text_input("Pinterest Board ID", value=cfg.get("pinterest_board",""), placeholder="Your board ID")
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card"><h3>📌 Pinterest Prompt</h3>', unsafe_allow_html=True)
        pin_prompt = st.text_area("Pinterest Prompt", value=cfg.get("pinterest_prompt",""), height=140,
            placeholder="My audience is busy moms who love quick dinner recipes...", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><h3>📅 Pinterest Post Scheduler</h3>', unsafe_allow_html=True)
    days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    saved = cfg.get("schedule_days","").split(",") if cfg.get("schedule_days") else []
    cols = st.columns(7); sel_days = []
    for i, day in enumerate(days):
        with cols[i]:
            if st.checkbox(day[:3], value=(day in saved), key=f"day_{day}"): sel_days.append(day)
    tc1,tc2 = st.columns(2)
    with tc1:
        try: t_val = datetime.strptime(cfg.get("schedule_time","09:00"),"%H:%M").time()
        except: t_val = datetime.strptime("09:00","%H:%M").time()
        sched_time = st.time_input("Posting Time", value=t_val)
    with tc2:
        tz_opts = ["UTC","America/New_York","America/Los_Angeles","Europe/London","Europe/Paris","Asia/Dubai","Africa/Casablanca","Asia/Tokyo"]
        cur_tz = cfg.get("schedule_timezone","UTC")
        sched_tz = st.selectbox("Timezone", tz_opts, index=tz_opts.index(cur_tz) if cur_tz in tz_opts else 0)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("💾 Save Pinterest Settings", type="primary", key="save_pinterest"):
        new = {"pinterest_token":pin_token,"pinterest_board":pin_board,"pinterest_prompt":pin_prompt,
               "schedule_days":",".join(sel_days),"schedule_time":sched_time.strftime("%H:%M"),"schedule_timezone":sched_tz}
        s.settings.update(new); db_save(s.user_id, new)
        s.save_ok = True; s.save_msg = "Pinterest settings saved!"; st.rerun()


def dash_billing(plan):
    c1,c2 = st.columns(2)
    with c1:
        active = "border:2px solid #c9892a;box-shadow:0 4px 20px rgba(201,137,42,.15);" if plan=="basic" else "border:2px solid #dfd4bc;"
        badge = '<div style="font-size:10px;font-weight:700;color:#c9892a;text-transform:uppercase;letter-spacing:2px;margin-bottom:12px;">✦ Current Plan</div>' if plan=="basic" else ""
        st.markdown(f"""<div style="background:#fff;{active}border-radius:26px;padding:40px 36px;text-align:center;">
{badge}<div style="font-size:11px;font-weight:700;color:#8a7a60;text-transform:uppercase;letter-spacing:2px;margin-bottom:16px;">Basic</div>
<div style="font-family:'Fraunces',serif;font-size:64px;font-weight:900;color:#1a1510;line-height:1;">$30</div>
<div style="font-size:14px;color:#8a7a60;margin-bottom:24px;">per month</div>
<div style="text-align:left;font-size:13.5px;color:#5a5040;line-height:2.4;">
✅ AI Article Generation<br>✅ Midjourney Images<br>✅ WordPress Auto-Publish<br>✅ Custom Prompts &amp; Design<br>✅ Internal Linking<br>❌ Pinterest Auto-Post</div></div>""", unsafe_allow_html=True)
    with c2:
        badge2 = '<div style="font-size:10px;font-weight:700;color:#e8a83e;text-transform:uppercase;letter-spacing:2px;margin-bottom:12px;">✦ Current Plan</div>' if plan=="pro" else ""
        st.markdown(f"""<div style="background:linear-gradient(158deg,#211808,#0f0d09);border:2px solid rgba(201,137,42,.55);box-shadow:0 8px 44px rgba(201,137,42,.2);border-radius:26px;padding:40px 36px;text-align:center;">
{badge2}<div style="font-size:11px;font-weight:700;color:rgba(232,168,62,.7);text-transform:uppercase;letter-spacing:2px;margin-bottom:16px;">Pro · Most Popular</div>
<div style="font-family:'Fraunces',serif;font-size:64px;font-weight:900;color:#fff;line-height:1;">$40</div>
<div style="font-size:14px;color:rgba(253,246,232,.4);margin-bottom:24px;">per month</div>
<div style="text-align:left;font-size:13.5px;color:rgba(253,246,232,.8);line-height:2.4;">
✅ Everything in Basic<br>✅ Pinterest Auto-Post<br>✅ Pinterest Keyword Optimizer<br>✅ Custom Pinterest Prompt<br>✅ Pinterest Post Scheduler<br>✅ Priority Support</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="card"><h3>💳 Payment</h3><p style="font-size:13.5px;color:#5a5040;line-height:1.7;">To upgrade or manage your subscription, contact us at <strong>support@nicheflow.ai</strong>. Payments processed securely via Stripe.</p></div>', unsafe_allow_html=True)
    if plan == "basic":
        if st.button("⬆️ Upgrade to Pro ($40/mo)", type="primary", key="billing_upgrade"):
            st.info("Contact support@nicheflow.ai to upgrade your account.")
    else:
        st.markdown('<div class="ok">✅ You are on the Pro plan. Contact support@nicheflow.ai to manage your subscription.</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#  QUERY PARAM ROUTER — reads ?nav=xxx set by window.top.location.href
# ═══════════════════════════════════════════════════════════════════════════
params = st.query_params
if "nav" in params:
    target = params["nav"]
    valid = {"home","login","signup","docs","dashboard"}
    if target in valid:
        if target == "dashboard" and not st.session_state.user_id:
            st.session_state.page = "login"
        else:
            st.session_state.page = target
    st.query_params.clear()
    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN ROUTER
# ═══════════════════════════════════════════════════════════════════════════
page = st.session_state.page
if page == "home":       page_home()
elif page == "login":    page_login()
elif page == "signup":   page_signup()
elif page == "docs":     page_docs()
elif page == "dashboard":
    if not st.session_state.user_id:
        st.session_state.page = "login"; st.rerun()
    else:
        page_dashboard()
else:
    st.session_state.page = "home"; st.rerun()