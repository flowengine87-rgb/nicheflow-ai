# -*- coding: utf-8 -*-
"""
NicheFlow AI — app.py
Beautiful multi-page SaaS with Supabase auth and full generator backend.
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
.stApp{background:#faf6ef!important;overflow:hidden;}
iframe{border:none!important;display:block;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "page": "home",
        "dash_tab": "overview",
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
#  URL NAVIGATION — handle query params set by the postMessage listener
# ─────────────────────────────────────────────────────────────────────────────
query_params = st.query_params

if "nav" in query_params:
    nav_target = query_params.get("nav", "")
    email      = query_params.get("email", "")
    password   = query_params.get("pass", "")
    confirm    = query_params.get("confirm", "")

    from urllib.parse import unquote
    email    = unquote(email)
    password = unquote(password)
    confirm  = unquote(confirm)

    if nav_target == "login" and email and password:
        # Handle login form submission
        pass  # handled below in do_login flow
    elif nav_target == "signup" and email and password and confirm:
        pass  # handled below
    
    if nav_target in ("home", "login", "signup", "docs", "dashboard"):
        if nav_target == "dashboard" and not st.session_state.user_id:
            st.session_state.page = "login"
        else:
            st.session_state.page = nav_target
        st.query_params.clear()
        st.rerun()

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
    except Exception:
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
    except Exception:
        return False

def db_increment_stat(user_id: str, field: str, amount: int = 1):
    if not DB_OK or not user_id: return
    try:
        current = db_load_settings(user_id).get(field, 0) or 0
        db_save_settings(user_id, {field: int(current) + amount})
    except Exception:
        pass

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
        if key in ["gen_logs","gen_results","wp_categories","internal_links"]:
            st.session_state[key] = []
        elif key in ["user_id","user_email"]:
            st.session_state[key] = None
        elif key == "user_plan":
            st.session_state[key] = "basic"
        else:
            st.session_state[key] = {}
    st.session_state.page = "home"

def save_settings_to_db():
    db_save_settings(st.session_state.user_id, st.session_state.settings)
    st.session_state.save_ok = True

# ─────────────────────────────────────────────────────────────────────────────
#  NAVIGATION HELPERS
#  
#  THE FIX: Instead of window.parent.location.href (blocked by Streamlit's
#  iframe sandbox), we use window.parent.postMessage to send a nav event UP
#  to the parent window. A zero-height listener component sits above each
#  page and catches those messages, then does the actual URL redirect.
# ─────────────────────────────────────────────────────────────────────────────

def _nav_js():
    """
    JS injected into every iframe page.
    window.top.location.href is allowed on user-initiated clicks by
    Streamlit's iframe sandbox (allow-top-navigation-by-user-activation).
    This navigates the real browser window directly — reliable on every click.
    """
    return """
<script>
function goPage(p) {
  var base = window.top.location.href.split('?')[0];
  window.top.location.href = base + '?nav=' + p;
}
</script>"""

def _nav_listener():
    pass  # not needed — window.top handles it directly

def _nav_listener_with_forms():
    pass  # not needed — window.top handles it directly

# ─────────────────────────────────────────────────────────────────────────────
#  HANDLE FORM SUBMISSIONS (login / signup via query params)
# ─────────────────────────────────────────────────────────────────────────────
if "nav" in st.query_params:
    nav_target = st.query_params.get("nav","")
    email      = st.query_params.get("email","")
    password   = st.query_params.get("pass","")
    confirm    = st.query_params.get("confirm","")

    from urllib.parse import unquote
    email    = unquote(email)
    password = unquote(password)
    confirm  = unquote(confirm)

    if nav_target == "login" and email and password:
        do_login(email, password)
        st.query_params.clear()
        st.rerun()
    elif nav_target == "signup" and email and password and confirm:
        do_signup(email, password, confirm)
        st.query_params.clear()
        st.rerun()
    elif nav_target in ("home","login","signup","docs","dashboard"):
        if nav_target == "dashboard" and not st.session_state.user_id:
            st.session_state.page = "login"
        else:
            st.session_state.page = nav_target
        st.query_params.clear()
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  FULL HTML PAGES — design completely unchanged, only goPage() JS updated
# ─────────────────────────────────────────────────────────────────────────────

def _common_styles():
    return """
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700;9..144,800;9..144,900&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --cream:#faf6ef;--cream2:#f2e8d4;--gold:#c9892a;--gold2:#e8a83e;
  --dark:#0f0d09;--dark2:#1c1810;--text:#1a1510;--text2:#5a5040;
  --text3:#8a7a60;--border:#dfd4bc;--white:#ffffff;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html{scroll-behavior:smooth;}
body{font-family:'Outfit',sans-serif;background:var(--cream);color:var(--text);overflow-x:hidden;}
nav{position:sticky;top:0;z-index:999;display:flex;align-items:center;justify-content:space-between;
    padding:0 5vw;height:66px;background:rgba(250,246,239,0.96);backdrop-filter:blur(14px);
    border-bottom:1px solid var(--border);}
.nav-logo{font-family:'Fraunces',serif;font-size:21px;font-weight:800;color:var(--text);cursor:pointer;}
.nav-logo em{color:var(--gold);font-style:normal;}
.nav-links{display:flex;align-items:center;gap:28px;}
.nav-links a{font-size:14px;font-weight:500;color:var(--text2);text-decoration:none;cursor:pointer;transition:color .2s;}
.nav-links a:hover{color:var(--gold);}
.nav-cta{background:var(--dark)!important;color:#fff!important;padding:9px 22px;border-radius:100px;
         font-weight:600!important;font-size:13px!important;transition:all .2s!important;}
.nav-cta:hover{background:var(--dark2)!important;transform:translateY(-1px);}
.btn-primary{background:var(--dark);color:#fff;padding:14px 30px;border-radius:100px;font-size:15px;
             font-weight:600;border:none;cursor:pointer;font-family:'Outfit',sans-serif;transition:all .2s;}
.btn-primary:hover{background:var(--dark2);transform:translateY(-2px);box-shadow:0 8px 28px rgba(0,0,0,.18);}
.btn-outline{background:transparent;color:var(--text);padding:14px 30px;border-radius:100px;font-size:15px;
             font-weight:600;border:1.5px solid var(--border);cursor:pointer;font-family:'Outfit',sans-serif;transition:all .2s;}
.btn-outline:hover{border-color:var(--gold);color:var(--gold);transform:translateY(-2px);}
.back-nav{display:inline-flex;align-items:center;gap:7px;font-size:13px;font-weight:600;color:var(--text3);
          cursor:pointer;padding:8px 14px;border-radius:100px;border:1px solid var(--border);
          background:rgba(255,255,255,.8);transition:all .2s;margin:16px 0 0 16px;text-decoration:none;}
.back-nav:hover{color:var(--gold);border-color:var(--gold);}
.back-nav svg{width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2.5;
              stroke-linecap:round;stroke-linejoin:round;}
footer{text-align:center;padding:clamp(36px,5vw,56px);border-top:1px solid var(--border);background:var(--cream);}
footer .f-logo{font-family:'Fraunces',serif;font-size:21px;font-weight:800;color:var(--text);margin-bottom:9px;}
footer p{font-size:13px;color:var(--text3);margin-bottom:3px;}
@media(max-width:768px){.nav-links{display:none;}}
</style>"""

# ── HOME PAGE ────────────────────────────────────────────────────────────────
def HOME_HTML():
    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>NicheFlow AI</title>
{_common_styles()}
<style>
.hero{{background:linear-gradient(160deg,#fdfaf4 0%,#f5e8cc 55%,#ecdbb8 100%);
       padding:96px 5vw 80px;text-align:center;border-bottom:1px solid var(--border);
       position:relative;overflow:hidden;}}
.hero::before{{content:'';position:absolute;top:-220px;left:-180px;width:560px;height:560px;
               background:radial-gradient(circle,rgba(201,137,42,.15) 0%,transparent 65%);border-radius:50%;}}
.hero::after{{content:'';position:absolute;bottom:-150px;right:-150px;width:480px;height:480px;
              background:radial-gradient(circle,rgba(201,137,42,.1) 0%,transparent 65%);border-radius:50%;}}
.hero-badge{{display:inline-flex;align-items:center;gap:7px;background:rgba(255,255,255,.7);
             border:1px solid rgba(201,137,42,.35);color:#8a6020;padding:7px 18px;border-radius:100px;
             font-size:12.5px;font-weight:600;letter-spacing:.4px;margin-bottom:28px;position:relative;z-index:1;}}
.hero h1{{font-family:'Fraunces',serif;font-size:clamp(46px,8vw,90px);font-weight:900;line-height:1.03;
          color:var(--text);margin-bottom:24px;position:relative;z-index:1;}}
.hero h1 em{{font-style:normal;color:var(--gold);}}
.hero p{{font-size:clamp(15px,1.7vw,19px);color:var(--text2);max-width:580px;margin:0 auto 44px;
         line-height:1.78;position:relative;z-index:1;}}
.hero-btns{{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;position:relative;z-index:1;}}
.hero-stats{{display:flex;flex-wrap:wrap;justify-content:center;gap:clamp(24px,5vw,68px);
             margin-top:60px;padding-top:48px;border-top:1px solid rgba(0,0,0,.09);position:relative;z-index:1;}}
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
.feat-card{{background:#fff;border:1px solid var(--border);border-radius:20px;padding:clamp(22px,3vw,36px);
            transition:transform .25s,box-shadow .25s,border-color .25s;}}
.feat-card:hover{{transform:translateY(-4px);box-shadow:0 14px 44px rgba(0,0,0,.07);border-color:rgba(201,137,42,.45);}}
.feat-icon{{width:50px;height:50px;background:#fff8ec;border:1px solid rgba(201,137,42,.2);border-radius:13px;
            display:flex;align-items:center;justify-content:center;font-size:22px;margin-bottom:16px;}}
.feat-card h3{{font-size:15.5px;font-weight:700;color:var(--text);margin-bottom:8px;}}
.feat-card p{{font-size:13.5px;color:var(--text3);line-height:1.76;}}
.pricing-grid{{display:grid;grid-template-columns:1fr 1fr;gap:22px;max-width:840px;margin:0 auto;}}
@media(max-width:640px){{.pricing-grid{{grid-template-columns:1fr;}}}}
.plan-card{{background:#fff;border:2px solid var(--border);border-radius:26px;padding:clamp(30px,4vw,50px) clamp(26px,3.5vw,42px);text-align:center;transition:transform .25s,box-shadow .25s;}}
.plan-card:hover{{transform:translateY(-3px);box-shadow:0 14px 44px rgba(0,0,0,.07);}}
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
.plan-btn{{width:100%;margin-top:26px;padding:13px;border-radius:100px;font-size:14px;font-weight:700;
           cursor:pointer;border:2px solid var(--dark);background:transparent;color:var(--dark);
           font-family:'Outfit',sans-serif;transition:all .2s;}}
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
.cta-banner{{background:var(--dark);border-radius:26px;padding:clamp(52px,7vw,92px) clamp(28px,6vw,80px);
             text-align:center;margin:0 clamp(14px,4vw,60px) clamp(52px,6vw,80px);position:relative;overflow:hidden;}}
.cta-banner::before{{content:'';position:absolute;top:-80px;left:50%;transform:translateX(-50%);width:500px;
                     height:280px;background:radial-gradient(circle,rgba(201,137,42,.2) 0%,transparent 65%);pointer-events:none;}}
</style>
</head><body>
{_nav_js()}
<nav>
  <div class="nav-logo" onclick="goPage('home')">✦ <em>Niche</em>Flow AI</div>
  <div class="nav-links">
    <a href="#features">Features</a>
    <a href="#pricing">Pricing</a>
    <a href="#how">How It Works</a>
    <a onclick="goPage('docs')">Documentation</a>
    <a class="nav-cta" onclick="goPage('login')">Sign In →</a>
  </div>
</nav>

<section class="hero">
  <div class="hero-badge">✦ AI-Powered Content Platform</div>
  <h1>Write Less.<br>Publish More.<br><em>Grow on Autopilot.</em></h1>
  <p>NicheFlow AI writes full SEO blog articles, generates stunning Midjourney images, publishes to WordPress, and pins to Pinterest — completely automatically. You paste a title. We handle everything.</p>
  <div class="hero-btns">
    <button class="btn-primary" onclick="goPage('signup')">Get Started Free →</button>
    <button class="btn-outline" onclick="goPage('docs')">View Documentation</button>
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
    <div class="feat-card"><div class="feat-icon">✍️</div><h3>AI Article Writer</h3><p>Groq AI writes full long-form SEO articles in seconds. Your prompt, your niche, your voice — zero defaults forced on you.</p></div>
    <div class="feat-card"><div class="feat-icon">🎨</div><h3>Midjourney Images</h3><p>4 stunning images auto-generated per article. Converted to WebP and uploaded directly to your WordPress media library.</p></div>
    <div class="feat-card"><div class="feat-icon">🌐</div><h3>WordPress Publisher</h3><p>Articles publish directly to your site with images and full formatting. No copy-pasting or manual uploads — ever.</p></div>
    <div class="feat-card"><div class="feat-icon">📌</div><h3>Pinterest Auto-Post</h3><p>After every WordPress publish, automatically create and post optimized Pins using the article's featured image. Pro plan.</p></div>
    <div class="feat-card"><div class="feat-icon">🃏</div><h3>Custom Niche Cards</h3><p>Add beautifully styled cards to every article — recipe, travel, health, or any niche. Fully customizable per user.</p></div>
    <div class="feat-card"><div class="feat-icon">🎨</div><h3>Article Design Studio</h3><p>Control your article colors, fonts, and HTML structure. Every article matches your brand — not a generic template.</p></div>
  </div>
</section>

<section class="section-alt" id="pricing">
  <div class="section-center">
    <span class="eyebrow">Pricing</span>
    <h2 class="section-title">Simple, Honest Pricing</h2>
    <p class="section-sub">No hidden fees. No shared quotas. Cancel anytime — no contracts or lock-in.</p>
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
        <div class="plan-feat">✅&nbsp; Custom Article &amp; Card Prompts</div>
        <div class="plan-feat">✅&nbsp; Article Design Studio</div>
        <div class="plan-feat">✅&nbsp; Draft or Live Publishing</div>
        <div class="plan-feat no">✗&nbsp; Pinterest Auto-Post</div>
      </div>
      <button class="plan-btn" onclick="goPage('signup')">Get Started →</button>
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
        <div class="plan-feat">✅&nbsp; Auto Pin from Featured Image</div>
        <div class="plan-feat">✅&nbsp; Pinterest Post Scheduler</div>
        <div class="plan-feat">✅&nbsp; Priority Support</div>
      </div>
      <button class="plan-btn" onclick="goPage('signup')">Get Pro →</button>
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
    <div class="step-card"><div class="step-num">01</div><h4>Sign Up &amp; Choose Plan</h4><p>Create your account and pick Basic or Pro — depending on whether you need Pinterest auto-posting.</p></div>
    <div class="step-card"><div class="step-num">02</div><h4>Add Your Credentials</h4><p>Enter your Groq API key, Midjourney key, and WordPress app password once in Settings.</p></div>
    <div class="step-card"><div class="step-num">03</div><h4>Write Your Prompts</h4><p>Customize your article and card prompts to match your niche voice, style, and target audience.</p></div>
    <div class="step-card"><div class="step-num">04</div><h4>Paste Titles &amp; Go</h4><p>Drop in your article titles and hit Generate. NicheFlow writes, designs, and publishes everything.</p></div>
  </div>
</section>

<section class="section">
  <div class="cta-banner">
    <span class="eyebrow eyebrow-light">Start Today</span>
    <h2 class="section-title" style="color:#fdf6e8;position:relative;z-index:1;">Ready to Automate Your Content?</h2>
    <p class="section-sub" style="color:rgba(253,246,232,.5);margin:0 auto 36px;position:relative;z-index:1;">Join bloggers who publish more, stress less, and grow faster with NicheFlow AI.</p>
    <button class="btn-primary" style="background:var(--gold);position:relative;z-index:1;" onclick="goPage('signup')">Get Started Free →</button>
  </div>
</section>

<footer>
  <div class="f-logo">✦ NicheFlow AI</div>
  <p>AI-powered blog &amp; Pinterest content generator</p>
  <p style="color:#b0a080;margin-top:14px;">© 2026 NicheFlow AI · All rights reserved</p>
</footer>
</body></html>"""

# ── LOGIN PAGE ───────────────────────────────────────────────────────────────
def LOGIN_HTML(error="", success=""):
    err_html = f'<div style="background:#fff0f0;border:1px solid #ffd0d0;color:#c03030;border-radius:9px;padding:10px 14px;font-size:13.5px;margin-bottom:14px;">❌ {error}</div>' if error else ""
    suc_html = f'<div style="background:#f0faf4;border:1px solid #a4d8b8;color:#1a6e38;border-radius:9px;padding:10px 14px;font-size:13.5px;margin-bottom:14px;">✅ {success}</div>' if success else ""
    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Sign In — NicheFlow AI</title>
{_common_styles()}
<style>
body{{min-height:100vh;background:linear-gradient(160deg,#fdfaf4 0%,#f0e3c8 100%);display:flex;flex-direction:column;}}
.login-wrap{{flex:1;display:flex;align-items:center;justify-content:center;padding:40px 20px;}}
.login-card{{background:#fff;border:1px solid var(--border);border-radius:26px;padding:clamp(36px,5vw,56px) clamp(30px,4.5vw,52px);
             width:100%;max-width:450px;box-shadow:0 12px 56px rgba(0,0,0,.08);}}
.login-logo{{font-family:'Fraunces',serif;font-size:20px;font-weight:800;color:var(--text);margin-bottom:28px;text-align:center;}}
.login-logo em{{color:var(--gold);font-style:normal;}}
.login-card h2{{font-family:'Fraunces',serif;font-size:30px;font-weight:800;color:var(--text);margin-bottom:5px;text-align:center;}}
.sub{{font-size:14.5px;color:var(--text3);text-align:center;margin-bottom:28px;}}
.field{{margin-bottom:16px;}}
.field label{{display:block;font-size:13px;font-weight:600;color:var(--text2);margin-bottom:6px;}}
.field input{{width:100%;padding:12px 15px;border:1.5px solid var(--border);border-radius:11px;font-size:14.5px;
              font-family:'Outfit',sans-serif;background:#fdfaf5;color:var(--text);outline:none;transition:border-color .2s,box-shadow .2s;}}
.field input:focus{{border-color:var(--gold);box-shadow:0 0 0 3px rgba(201,137,42,.12);}}
.login-btn{{width:100%;padding:13px;background:var(--dark);color:#fff;border:none;border-radius:11px;
            font-size:15px;font-weight:700;font-family:'Outfit',sans-serif;cursor:pointer;transition:all .2s;margin-top:6px;}}
.login-btn:hover{{background:var(--dark2);transform:translateY(-1px);box-shadow:0 6px 24px rgba(0,0,0,.14);}}
.login-foot{{text-align:center;margin-top:18px;font-size:13.5px;color:var(--text3);}}
.login-foot a{{color:var(--gold);font-weight:600;cursor:pointer;text-decoration:none;}}
.back-link{{display:block;text-align:center;margin-top:16px;font-size:13px;color:var(--text3);cursor:pointer;}}
.back-link:hover{{color:var(--gold);}}
</style>
</head><body>
{_nav_js()}
<a class="back-nav" onclick="goPage('home')" style="display:inline-flex;">
  <svg viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>
  Back to Home
</a>
<div class="login-wrap">
  <div class="login-card">
    <div class="login-logo">✦ <em>NicheFlow</em> AI</div>
    <h2>Welcome Back</h2>
    <p class="sub">Sign in to your NicheFlow AI account</p>
    {err_html}{suc_html}
    <form onsubmit="submitLogin(event)">
      <div class="field"><label>Email Address</label><input type="email" id="email" placeholder="your@email.com" required></div>
      <div class="field"><label>Password</label><input type="password" id="pass" placeholder="Your password" required></div>
      <button type="submit" class="login-btn">Sign In →</button>
    </form>
    <p class="login-foot">Don't have an account? <a onclick="goPage('signup')">Sign Up Free</a></p>
    <a class="back-link" onclick="goPage('home')">← Back to Home</a>
  </div>
</div>
<script>
function submitLogin(e) {{
  e.preventDefault();
  var email = document.getElementById('email').value;
  var pass  = document.getElementById('pass').value;
  var base  = window.top.location.href.split('?')[0];
  window.top.location.href = base + '?nav=login&email=' + encodeURIComponent(email) + '&pass=' + encodeURIComponent(pass);
}}
</script>
</body></html>"""

# ── SIGNUP PAGE ──────────────────────────────────────────────────────────────
def SIGNUP_HTML(error=""):
    err_html = f'<div style="background:#fff0f0;border:1px solid #ffd0d0;color:#c03030;border-radius:9px;padding:10px 14px;font-size:13.5px;margin-bottom:14px;">❌ {error}</div>' if error else ""
    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Sign Up — NicheFlow AI</title>
{_common_styles()}
<style>
body{{min-height:100vh;background:linear-gradient(160deg,#fdfaf4 0%,#f0e3c8 100%);display:flex;flex-direction:column;}}
.login-wrap{{flex:1;display:flex;align-items:center;justify-content:center;padding:40px 20px;}}
.login-card{{background:#fff;border:1px solid var(--border);border-radius:26px;padding:clamp(36px,5vw,56px) clamp(30px,4.5vw,52px);
             width:100%;max-width:450px;box-shadow:0 12px 56px rgba(0,0,0,.08);}}
.login-logo{{font-family:'Fraunces',serif;font-size:20px;font-weight:800;color:var(--text);margin-bottom:28px;text-align:center;}}
.login-logo em{{color:var(--gold);font-style:normal;}}
.login-card h2{{font-family:'Fraunces',serif;font-size:30px;font-weight:800;color:var(--text);margin-bottom:5px;text-align:center;}}
.sub{{font-size:14.5px;color:var(--text3);text-align:center;margin-bottom:28px;}}
.field{{margin-bottom:16px;}}
.field label{{display:block;font-size:13px;font-weight:600;color:var(--text2);margin-bottom:6px;}}
.field input{{width:100%;padding:12px 15px;border:1.5px solid var(--border);border-radius:11px;font-size:14.5px;
              font-family:'Outfit',sans-serif;background:#fdfaf5;color:var(--text);outline:none;transition:border-color .2s,box-shadow .2s;}}
.field input:focus{{border-color:var(--gold);box-shadow:0 0 0 3px rgba(201,137,42,.12);}}
.login-btn{{width:100%;padding:13px;background:var(--dark);color:#fff;border:none;border-radius:11px;
            font-size:15px;font-weight:700;font-family:'Outfit',sans-serif;cursor:pointer;transition:all .2s;margin-top:6px;}}
.login-btn:hover{{background:var(--dark2);transform:translateY(-1px);}}
.login-foot{{text-align:center;margin-top:18px;font-size:13.5px;color:var(--text3);}}
.login-foot a{{color:var(--gold);font-weight:600;cursor:pointer;}}
.back-link{{display:block;text-align:center;margin-top:16px;font-size:13px;color:var(--text3);cursor:pointer;}}
.back-link:hover{{color:var(--gold);}}
</style>
</head><body>
{_nav_js()}
<a class="back-nav" onclick="goPage('home')" style="display:inline-flex;">
  <svg viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>
  Back to Home
</a>
<div class="login-wrap">
  <div class="login-card">
    <div class="login-logo">✦ <em>NicheFlow</em> AI</div>
    <h2>Create Account</h2>
    <p class="sub">Start automating your content today</p>
    {err_html}
    <form onsubmit="submitSignup(event)">
      <div class="field"><label>Email Address</label><input type="email" id="email" placeholder="your@email.com" required></div>
      <div class="field"><label>Password</label><input type="password" id="pass" placeholder="At least 6 characters" required></div>
      <div class="field"><label>Confirm Password</label><input type="password" id="confirm" placeholder="Repeat password" required></div>
      <button type="submit" class="login-btn">Create Account →</button>
    </form>
    <p class="login-foot">Already have an account? <a onclick="goPage('login')">Sign In</a></p>
    <a class="back-link" onclick="goPage('home')">← Back to Home</a>
  </div>
</div>
<script>
function submitSignup(e) {{
  e.preventDefault();
  var email   = document.getElementById('email').value;
  var pass    = document.getElementById('pass').value;
  var confirm = document.getElementById('confirm').value;
  var base    = window.top.location.href.split('?')[0];
  window.top.location.href = base + '?nav=signup&email=' + encodeURIComponent(email) + '&pass=' + encodeURIComponent(pass) + '&confirm=' + encodeURIComponent(confirm);
}}
</script>
</body></html>"""

# ── DOCS PAGE ────────────────────────────────────────────────────────────────
def DOCS_HTML(logged_in=False):
    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Documentation — NicheFlow AI</title>
{_common_styles()}
<style>
.docs-layout{{display:grid;grid-template-columns:210px 1fr;gap:24px;align-items:start;
              padding:32px clamp(24px,6vw,96px) 80px;max-width:1200px;margin:0 auto;}}
@media(max-width:740px){{.docs-layout{{grid-template-columns:1fr;}}}}
.docs-toc{{background:#fff;border:1px solid var(--border);border-radius:14px;padding:18px;position:sticky;top:80px;}}
.docs-toc h4{{font-size:10.5px;font-weight:700;color:var(--text3);text-transform:uppercase;letter-spacing:2px;margin-bottom:12px;}}
.docs-toc a{{display:block;font-size:13px;color:var(--text2);padding:7px 9px;border-radius:7px;cursor:pointer;
             text-decoration:none;transition:all .2s;margin-bottom:1px;}}
.docs-toc a:hover,.docs-toc a.active{{background:#fff8ec;color:var(--gold);font-weight:600;}}
.docs-sec{{background:#fff;border:1px solid var(--border);border-radius:18px;padding:26px 30px;margin-bottom:16px;}}
.docs-sec h2{{font-family:'Fraunces',serif;font-size:19px;font-weight:800;color:var(--text);margin-bottom:14px;
              padding-bottom:12px;border-bottom:1px solid #f0e6d4;display:flex;align-items:center;gap:10px;}}
.docs-sec h3{{font-size:14px;font-weight:700;color:var(--text);margin:16px 0 7px;}}
.docs-sec p{{font-size:13.5px;color:var(--text2);line-height:1.8;margin-bottom:10px;}}
.docs-sec ol,.docs-sec ul{{padding-left:20px;margin:7px 0 10px;}}
.docs-sec li{{font-size:13.5px;color:var(--text2);line-height:1.8;margin-bottom:4px;}}
.docs-sec strong{{color:var(--text);}}
.doc-note{{background:#fff8ec;border-left:3px solid var(--gold);border-radius:0 9px 9px 0;
           padding:10px 14px;margin:10px 0;font-size:13px;color:#7a5820;line-height:1.7;}}
.doc-eg{{background:#f8f3ea;border:1px solid #e4d8c4;border-radius:10px;padding:13px 16px;
         margin:9px 0;font-size:13px;color:#5a4a34;line-height:1.75;font-style:italic;}}
.step-badge{{display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;
             min-width:26px;background:var(--dark);color:var(--cream);border-radius:50%;font-size:12px;font-weight:700;}}
.docs-header{{padding:32px clamp(24px,6vw,96px) 0;max-width:1200px;margin:0 auto;}}
</style>
</head><body>
{_nav_js()}
<nav>
  <div class="nav-logo" onclick="goPage('home')">✦ <em>Niche</em>Flow AI</div>
  <div class="nav-links">
    <a onclick="goPage('home')">← Home</a>
    {'<a onclick="goPage(\'dashboard\')">Dashboard</a>' if logged_in else ''}
    <a class="nav-cta" onclick="goPage('{'dashboard' if logged_in else 'login'}')">{'Dashboard →' if logged_in else 'Sign In →'}</a>
  </div>
</nav>
<a class="back-nav" onclick="goPage('home')">
  <svg viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>
  Back to Home
</a>
<div class="docs-header">
  <span style="font-size:11px;font-weight:700;color:var(--gold);text-transform:uppercase;letter-spacing:3.5px;">Documentation</span>
  <h2 style="font-family:'Fraunces',serif;font-size:clamp(28px,4vw,44px);font-weight:800;color:var(--text);margin:8px 0 6px;">Setup Guide</h2>
  <p style="font-size:16px;color:var(--text2);margin-bottom:32px;">Everything you need to get fully set up and publishing in under 10 minutes.</p>
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
    <a onclick="sDoc('d-pprompt',this)">7. Pinterest Prompt</a>
    <a onclick="sDoc('d-tips',this)">8. Best Practices</a>
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
      <div class="doc-note">Images cost a few cents each on GoAPI's pay-as-you-go plan. Each article generates 4 images.</div>
    </div>
    <div class="docs-sec" id="d-wp">
      <h2><span class="step-badge">3</span> Connect Your WordPress Site</h2>
      <p>This allows NicheFlow to publish articles directly to your WordPress site, including images and formatting.</p>
      <ol>
        <li>Log in to your <strong>WordPress Dashboard</strong></li>
        <li>Go to <strong>Users → Your Profile</strong></li>
        <li>Scroll down to <strong>Application Passwords</strong></li>
        <li>Enter a name: <strong>NicheFlow AI</strong> — then click <strong>Add New Application Password</strong></li>
        <li>Copy the generated password (format: xxxx xxxx xxxx xxxx)</li>
        <li>In Settings enter your URL as <strong>https://yoursite.com</strong></li>
        <li>Enter the password as <strong>YourUsername:xxxx xxxx xxxx xxxx</strong></li>
      </ol>
      <div class="doc-note">Make sure your URL includes https:// and does not have a trailing slash at the end.</div>
    </div>
    <div class="docs-sec" id="d-pin">
      <h2><span class="step-badge">4</span> Set Up Pinterest Auto-Post &nbsp;<span style="font-size:12px;font-weight:700;color:var(--gold);background:#fff8ec;padding:3px 10px;border-radius:100px;">Pro Plan</span></h2>
      <p>The Pinterest module automatically creates and posts an optimized Pin for every article you publish.</p>
      <ol>
        <li>Go to <strong>developers.pinterest.com</strong> and log in</li>
        <li>Create a new app under your account</li>
        <li>Enable permissions: <strong>boards:read</strong> and <strong>pins:write</strong></li>
        <li>Generate a <strong>User Access Token</strong></li>
        <li>Find your <strong>Board ID</strong> from your Pinterest board URL</li>
        <li>Paste both into the Pinterest tab, along with your custom Pinterest prompt</li>
      </ol>
      <div class="doc-note">The Pin image is automatically taken from your article's featured image — no extra steps needed.</div>
    </div>
    <div class="docs-sec" id="d-prompt">
      <h2><span class="step-badge">5</span> Write a Great Article Prompt</h2>
      <p>Your article prompt is the single most impactful setting. It tells the AI how to write for your specific niche and audience. <strong>You write it — no defaults imposed.</strong></p>
      <h3>Food Blog Example</h3>
      <div class="doc-eg">Write a warm, personal recipe article in first person. Open with a nostalgic story. Include a "Why You'll Love This" section, 8 expert tips, variations, storage instructions, and 3 FAQs. Friendly tone for home cooks. Target 1200–1500 words.</div>
      <h3>Travel Blog Example</h3>
      <div class="doc-eg">Write an inspiring travel guide in second person. Open with a vivid sensory scene. Cover top 5 attractions, local food, best time to visit, budget breakdown, and 5 practical tips. Target budget adventurers aged 25–40.</div>
      <div class="doc-note">⚠️ Keep prompts under 2000 tokens (roughly 1500 words) to stay within Groq's rate limits.</div>
    </div>
    <div class="docs-sec" id="d-card">
      <h2><span class="step-badge">6</span> Customize Your Niche Card</h2>
      <p>The niche card is a styled visual block added inside every article — recipe card, destination summary, or any format that fits your niche.</p>
      <h3>Recipe Card Example</h3>
      <div class="doc-eg">Create a recipe card with: prep time, cook time, total time, servings, calories per serving, a list of ingredients with quantities, and step-by-step instructions.</div>
      <h3>Travel Card Example</h3>
      <div class="doc-eg">Create a destination card with: best time to visit, average daily budget (USD), language, currency, visa required (yes/no), and top 3 attractions.</div>
      <div class="doc-note">You can toggle the niche card on or off per session from the Generate tab. Your card colors follow your Design Studio settings.</div>
    </div>
    <div class="docs-sec" id="d-pprompt">
      <h2><span class="step-badge">7</span> Write Your Pinterest Prompt &nbsp;<span style="font-size:12px;font-weight:700;color:var(--gold);background:#fff8ec;padding:3px 10px;border-radius:100px;">Pro Plan</span></h2>
      <p>Your Pinterest prompt tells the AI about your niche and audience so it generates optimized Pin titles, descriptions, and keywords for every article.</p>
      <h3>Example</h3>
      <div class="doc-eg">My audience is busy moms who love quick weeknight dinner recipes. Write Pinterest pin descriptions that are warm and conversational, using keywords like family dinner, easy recipes, weeknight meals. Keep under 200 characters with a call to action.</div>
    </div>
    <div class="docs-sec" id="d-tips">
      <h2><span class="step-badge">8</span> Best Practices</h2>
      <ul>
        <li><strong>Use descriptive titles</strong> — "Easy Creamy Tuscan Chicken Pasta" gets far better results than just "Pasta"</li>
        <li><strong>Set a 5–10 second delay</strong> between articles during bulk generation to stay within Groq's rate limits</li>
        <li><strong>Start with Draft status</strong> so you can review each article before it goes live</li>
        <li><strong>Customize your article prompt</strong> — this single setting has the biggest impact on quality</li>
        <li><strong>Test with one article first</strong> before running a bulk batch of 10 or more</li>
        <li><strong>Keep your API keys private</strong> — never share them or include them in screenshots</li>
        <li><strong>Pinterest descriptions</strong> should reference your specific audience for the most relevant pin content</li>
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
</body></html>"""

# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def stat_card(title, value, icon, color="#c9892a"):
    st.markdown(f"""
    <div style="background:#fff;border:1px solid #dfd4bc;border-radius:14px;padding:20px;text-align:center;">
      <div style="font-size:22px;margin-bottom:8px;">{icon}</div>
      <div style="font-family:Georgia,serif;font-size:32px;font-weight:800;color:{color};line-height:1;">{value}</div>
      <div style="font-size:11.5px;color:#8a7a60;margin-top:4px;">{title}</div>
    </div>""", unsafe_allow_html=True)

def section_header(title, subtitle=""):
    st.markdown(f"""
    <div style="padding:20px 0 16px 0;border-bottom:1px solid #dfd4bc;margin-bottom:24px;">
      <h1 style="font-family:Georgia,serif;font-size:22px;font-weight:800;color:#1a1510;margin:0;">{title}</h1>
      {f'<p style="font-size:13px;color:#8a7a60;margin:4px 0 0 0;">{subtitle}</p>' if subtitle else ''}
    </div>""", unsafe_allow_html=True)

def info_box(msg):
    st.markdown(f'<div style="background:#fff8ec;border-left:4px solid #c9892a;border-radius:0 8px 8px 0;padding:10px 14px;font-size:13px;color:#7a5820;margin-bottom:12px;">{msg}</div>', unsafe_allow_html=True)

def success_box(msg):
    st.markdown(f'<div style="background:#f0faf4;border:1px solid #a4d8b8;color:#1a6e38;border-radius:9px;padding:10px 14px;font-size:13px;margin-bottom:12px;">✅ {msg}</div>', unsafe_allow_html=True)

def error_box(msg):
    st.markdown(f'<div style="background:#fff0f0;border:1px solid #ffd0d0;color:#c03030;border-radius:9px;padding:10px 14px;font-size:13px;margin-bottom:12px;">❌ {msg}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
def render_sidebar():
    s = st.session_state
    plan_label = "Pro Plan · $40/mo" if s.user_plan == "pro" else "Basic Plan · $30/mo"
    plan_color = "#e8a83e" if s.user_plan == "pro" else "rgba(253,246,232,.4)"
    with st.sidebar:
        st.markdown(f"""
        <style>
        section[data-testid="stSidebar"]{{display:flex!important;}}
        [data-testid="stSidebarContent"]{{background:#0f0d09!important;}}
        </style>
        <div style="padding:22px 22px 18px;font-family:Georgia,serif;font-size:19px;font-weight:800;
             color:#fdf6e8;border-bottom:1px solid rgba(255,255,255,.07);">
          ✦ <em style="color:#c9892a;font-style:normal;">Niche</em>Flow AI</div>
        <div style="padding:15px 22px;border-bottom:1px solid rgba(255,255,255,.07);">
          <div style="font-size:13.5px;font-weight:600;color:#fdf6e8;">{s.user_email or 'User'}</div>
          <div style="font-size:11.5px;color:{plan_color};margin-top:3px;">{plan_label}</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        tabs = [
            ("overview",  "📊", "Overview"),
            ("generate",  "✍️", "Generate"),
            ("settings",  "⚙️", "Settings"),
            ("prompts",   "📝", "Prompts"),
            ("design",    "🎨", "Design Studio"),
            ("pinterest", "📌", "Pinterest"),
            ("billing",   "💳", "Billing"),
            ("docs",      "📖", "Documentation"),
        ]
        for key, icon, label in tabs:
            active = s.dash_tab == key
            if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
                s.dash_tab = key; st.rerun()

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        if st.button("🚪  Sign Out", use_container_width=True, key="nav_logout"):
            do_logout(); st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD TABS
# ─────────────────────────────────────────────────────────────────────────────
def tab_overview():
    section_header("Overview", "Your NicheFlow AI dashboard")
    s = st.session_state.settings
    c1,c2,c3,c4 = st.columns(4)
    with c1: stat_card("Articles Generated", s.get("articles_generated",0), "✍️")
    with c2: stat_card("Images Created",      s.get("images_created",0),     "🎨")
    with c3: stat_card("Posts Published",     s.get("posts_published",0),    "🌐")
    with c4: stat_card("Pins Posted",         s.get("pins_posted",0),        "📌")
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;">
          <h3 style="font-size:14.5px;font-weight:700;color:#1a1510;margin:0 0 16px 0;padding-bottom:12px;border-bottom:1px solid #f0e6d4;">🚀 Quick Start</h3>
          <p style="font-size:13.5px;color:#5a5040;line-height:2;">
            1. Add your API keys in <strong>Settings</strong><br>
            2. Write your prompts in <strong>Prompts</strong><br>
            3. Style your articles in <strong>Design Studio</strong><br>
            4. Go to <strong>Generate</strong> and paste titles
          </p>
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
        </div>""", unsafe_allow_html=True)


def tab_settings():
    section_header("Settings", "API credentials and publishing preferences")
    s = st.session_state.settings

    if st.session_state.save_ok:
        success_box("Settings saved successfully!")
        st.session_state.save_ok = False

    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;">', unsafe_allow_html=True)
        st.markdown('<h3 style="font-size:14.5px;font-weight:700;color:#1a1510;margin:0 0 18px 0;padding-bottom:13px;border-bottom:1px solid #f0e6d4;">🔑 API Credentials</h3>', unsafe_allow_html=True)
        groq_key   = st.text_input("Groq API Key",             value=s.get("groq_key",""),   type="password", placeholder="gsk_...", help="Free at console.groq.com")
        c1a,c1b    = st.columns([1,2])
        with c1a:
            if st.button("Test Groq", key="test_groq"):
                r = test_groq_key(groq_key) if (GEN_OK and groq_key) else {"success":False,"message":"Enter a key first"}
                st.session_state["groq_test"] = r
        with c1b:
            if "groq_test" in st.session_state:
                r = st.session_state.groq_test
                st.markdown(f'<div style="font-size:12px;padding:6px 0;color:{"#1a6e38" if r["success"] else "#c03030"};">{r["message"]}</div>', unsafe_allow_html=True)

        goapi_key  = st.text_input("Midjourney API Key (GoAPI)", value=s.get("mj_key",""),  type="password", placeholder="Your GoAPI key")
        c2a,c2b    = st.columns([1,2])
        with c2a:
            if st.button("Test GoAPI", key="test_goapi"):
                r = test_goapi_key(goapi_key) if (GEN_OK and goapi_key) else {"success":False,"message":"Enter a key first"}
                st.session_state["goapi_test"] = r
        with c2b:
            if "goapi_test" in st.session_state:
                r = st.session_state.goapi_test
                st.markdown(f'<div style="font-size:12px;padding:6px 0;color:{"#1a6e38" if r["success"] else "#c03030"};">{r["message"]}</div>', unsafe_allow_html=True)

        wp_url      = st.text_input("WordPress Site URL",       value=s.get("wp_url",""),     placeholder="https://yoursite.com")
        wp_password = st.text_input("WordPress App Password",   value=s.get("wp_password",""), type="password", placeholder="Username:xxxx xxxx xxxx xxxx")
        c3a,c3b     = st.columns([1,2])
        with c3a:
            if st.button("Test WordPress", key="test_wp"):
                r = test_wordpress(wp_url, wp_password) if (GEN_OK and wp_url and wp_password) else {"success":False,"message":"Enter URL and password first"}
                st.session_state["wp_test"] = r
                if r["success"] and GEN_OK:
                    st.session_state.wp_categories = fetch_wp_categories(wp_url, wp_password)
        with c3b:
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
        use_images = st.toggle("Generate Midjourney Images", value=bool(s.get("use_images",True)))
        show_card  = st.toggle("Include Info Card in Articles", value=bool(s.get("show_card",True)))
        card_click = st.toggle("Card Clickable in WordPress", value=bool(s.get("card_clickable",False)))

        st.markdown('<h3 style="font-size:13.5px;font-weight:700;color:#1a1510;margin:18px 0 10px 0;">🎞️ Midjourney Prompt Template</h3>', unsafe_allow_html=True)
        mj_template = st.text_area("Midjourney Template", value=s.get("mj_template",""), height=80,
                                    placeholder="Close up {recipe_name}, food photography, natural light --ar 2:3 --v 6.1",
                                    help="Use {recipe_name} as placeholder for article title")

        st.markdown('<h3 style="font-size:13.5px;font-weight:700;color:#1a1510;margin:18px 0 10px 0;">🔗 Internal Links</h3>', unsafe_allow_html=True)
        use_int_links = st.toggle("Enable Internal Linking", value=bool(s.get("use_internal_links",False)))
        max_links = int(s.get("max_links",4))
        if use_int_links:
            max_links = st.slider("Max links per article", 1, 8, max_links)

        cats = st.session_state.wp_categories
        selected_cats = []
        if cats:
            st.markdown('<h3 style="font-size:13.5px;font-weight:700;color:#1a1510;margin:18px 0 10px 0;">📁 WordPress Categories</h3>', unsafe_allow_html=True)
            cat_options = {c["name"]: c["id"] for c in cats}
            sel_names   = st.multiselect("Assign to categories", options=list(cat_options.keys()))
            selected_cats = [cat_options[n] for n in sel_names]
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    if st.button("💾 Save Settings", type="primary"):
        st.session_state.settings.update({
            "groq_key": groq_key, "mj_key": goapi_key,
            "wp_url": wp_url, "wp_password": wp_password,
            "publish_status": publish_status,
            "use_images": use_images, "show_card": show_card,
            "card_clickable": card_click, "mj_template": mj_template,
            "use_internal_links": use_int_links, "max_links": max_links,
        })
        save_settings_to_db(); st.rerun()


def tab_prompts():
    section_header("Prompts", "Customize how your content is generated")
    s = st.session_state.settings

    if st.session_state.save_ok:
        success_box("Prompts saved successfully!")
        st.session_state.save_ok = False

    info_box("⚠️ <strong>Token Warning:</strong> Keep your article prompt under 2000 tokens (roughly 1500 words) to avoid Groq rate limits. Short, clear instructions work best.")

    t1, t2, t3 = st.tabs(["✍️ Article Prompt", "🃏 Card Prompt", "📌 Pinterest Prompt"])

    with t1:
        st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;">', unsafe_allow_html=True)
        st.markdown('<p style="font-size:13.5px;color:#5a5040;line-height:1.7;margin-bottom:16px;">Write your article prompt. This tells the AI exactly how to write for your niche, audience, and style. <strong>Your prompt, your rules — no defaults.</strong></p>', unsafe_allow_html=True)
        article_prompt = st.text_area("Your Article Prompt", value=s.get("article_prompt",""), height=200,
            placeholder="Example — Travel blog:\nWrite an inspiring travel guide in second person. Open with a vivid sensory scene. Cover top 5 attractions, local food, best time to visit, budget, and 5 practical tips. Target budget adventurers aged 25-40. Use H2 headings for each section. 1200-1500 words.\n\nExample — Recipe blog:\nWrite a warm, personal recipe article in first person. Open with a nostalgic story. Include a 'Why You'll Love This' section, 6 expert tips, variations, and 3 FAQs. Friendly tone for home cooks. 1200 words.")
        st.markdown('<h3 style="font-size:13.5px;font-weight:700;color:#1a1510;margin:20px 0 10px 0;">🏗️ Custom HTML Structure (optional)</h3>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:13px;color:#8a7a60;margin-bottom:10px;">Paste your HTML/CSS style template. The AI will follow this structure for every article.</p>', unsafe_allow_html=True)
        html_structure = st.text_area("HTML Structure Template", value=s.get("html_structure",""), height=140,
            placeholder='<h2 style="color:MAIN_COLOR;">Section Title</h2>\n<div style="background:#f9f9f9;border-left:4px solid MAIN_COLOR;padding:16px;">...</div>')
        st.markdown('</div>', unsafe_allow_html=True)

    with t2:
        st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;">', unsafe_allow_html=True)
        st.markdown('<p style="font-size:13.5px;color:#5a5040;line-height:1.7;margin-bottom:16px;">Describe the card you want in every article — recipe card, travel card, health summary, product card, anything. The AI generates the data, you control the structure.</p>', unsafe_allow_html=True)
        card_prompt = st.text_area("Your Card Prompt", value=s.get("card_prompt",""), height=180,
            placeholder="Example — Recipe card:\nCreate a recipe card with prep time, cook time, total time, servings, calories per serving, protein, carbs, fat, a list of ingredients with quantities, and step-by-step instructions.\n\nExample — Travel card:\nCreate a destination quick-reference card with best time to visit, average daily budget in USD, official language, currency, visa required (yes/no), and top 3 must-see attractions.")
        st.markdown('</div>', unsafe_allow_html=True)

    with t3:
        if st.session_state.user_plan != "pro":
            st.markdown("""
            <div style="background:linear-gradient(135deg,#1c1810,#0f0d09);border:1px solid rgba(201,137,42,.38);
                 border-radius:18px;padding:28px;text-align:center;color:#fdf6e8;">
              <div style="font-size:34px;margin-bottom:10px;">📌</div>
              <h3 style="font-family:Georgia,serif;font-size:22px;font-weight:800;color:#fdf6e8;margin:0 0 8px 0;">Pinterest Prompt</h3>
              <p style="font-size:13.5px;color:rgba(253,246,232,.5);line-height:1.7;">
                Available on the <span style="color:#e8a83e;font-weight:600;">Pro plan ($40/month)</span>.<br>
                Upgrade to write your Pinterest prompt and auto-post optimized pins after every article.</p>
            </div>""", unsafe_allow_html=True)
            pinterest_prompt = s.get("pinterest_prompt","")
        else:
            st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;">', unsafe_allow_html=True)
            st.markdown('<p style="font-size:13.5px;color:#5a5040;line-height:1.7;margin-bottom:16px;">Describe your Pinterest niche and audience. The AI uses this to generate optimized Pin titles, descriptions, and alt text after every article is published.</p>', unsafe_allow_html=True)
            pinterest_prompt = st.text_area("Your Pinterest Prompt", value=s.get("pinterest_prompt",""), height=160,
                placeholder="My audience is busy moms who love quick weeknight dinner recipes. Write warm, conversational pin descriptions using keywords like family dinner, easy recipes, weeknight meals. Keep under 200 characters with a call to action.")
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    if st.button("💾 Save Prompts", type="primary"):
        updates = {"article_prompt": article_prompt, "html_structure": html_structure, "card_prompt": card_prompt}
        if st.session_state.user_plan == "pro":
            updates["pinterest_prompt"] = pinterest_prompt
        st.session_state.settings.update(updates)
        save_settings_to_db(); st.rerun()


def tab_design():
    section_header("Design Studio", "Customize how your articles look")
    s = st.session_state.settings

    if st.session_state.save_ok:
        success_box("Design settings saved!")
        st.session_state.save_ok = False

    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;">', unsafe_allow_html=True)
        st.markdown('<h3 style="font-size:14.5px;font-weight:700;color:#1a1510;margin:0 0 18px 0;padding-bottom:13px;border-bottom:1px solid #f0e6d4;">🎨 Color Theme</h3>', unsafe_allow_html=True)
        main_color   = st.color_picker("Main Color (headings, accents)", value=s.get("design_main_color","#333333"))
        accent_color = st.color_picker("Accent / Highlight Color",        value=s.get("design_accent_color","#ea580c"))
        font_opts    = ["inherit","'Georgia',serif","'Arial',sans-serif","'Verdana',sans-serif",
                        "'Trebuchet MS',sans-serif","'Times New Roman',serif","'Courier New',monospace"]
        font_labels  = ["Site default","Georgia (serif)","Arial","Verdana","Trebuchet MS","Times New Roman","Courier New"]
        cur_font     = s.get("design_font_family","inherit")
        font_idx     = font_opts.index(cur_font) if cur_font in font_opts else 0
        font_family  = font_opts[st.selectbox("Article Font", options=range(len(font_labels)),
                                               format_func=lambda i: font_labels[i], index=font_idx)]
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;">', unsafe_allow_html=True)
        st.markdown('<h3 style="font-size:14.5px;font-weight:700;color:#1a1510;margin:0 0 18px 0;padding-bottom:13px;border-bottom:1px solid #f0e6d4;">👁️ Live Preview</h3>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="font-family:{font_family};border:1px solid #eee;border-radius:12px;padding:20px;background:#fafafa;">
          <h2 style="color:{main_color};font-size:18px;font-weight:800;margin:0 0 10px 0;">Your Article Title Here</h2>
          <p style="font-size:14px;color:#444;line-height:1.7;margin:0 0 14px 0;">This is how your article body text and intro paragraphs will look with your chosen font and color settings applied.</p>
          <div style="background:#f9f9f9;border-left:4px solid {accent_color};border-radius:0 8px 8px 0;padding:12px 16px;">
            <ul style="margin:0;padding-left:16px;line-height:2.2;font-size:13px;color:#444;">
              <li>Key tip or expert insight</li>
              <li>Why readers will love this</li>
              <li>Important detail or fact</li>
            </ul>
          </div>
        </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    if st.button("💾 Save Design", type="primary"):
        st.session_state.settings.update({
            "design_main_color": main_color, "design_accent_color": accent_color, "design_font_family": font_family,
        })
        save_settings_to_db(); st.rerun()


def tab_generate():
    section_header("Generate Articles", "Paste titles and publish automatically")
    s = st.session_state.settings

    missing = []
    if not s.get("groq_key"):     missing.append("Groq API key")
    if not s.get("wp_url"):       missing.append("WordPress URL")
    if not s.get("wp_password"):  missing.append("WordPress App Password")
    if not s.get("article_prompt"): missing.append("Article Prompt (Prompts tab)")

    if missing:
        error_box(f"Please configure first: <strong>{', '.join(missing)}</strong>")
        return

    st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;margin-bottom:18px;">', unsafe_allow_html=True)
    st.markdown('<h3 style="font-size:14.5px;font-weight:700;color:#1a1510;margin:0 0 6px 0;">📋 Article Titles</h3>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13px;color:#8a7a60;margin-bottom:16px;">One title per line. NicheFlow writes, designs, and publishes each article automatically.</p>', unsafe_allow_html=True)

    titles_input = st.text_area("Titles", height=160,
        placeholder="How to Travel Europe on a Budget\n10 Best Hiking Trails in Colorado\nMediterranean Grilled Chicken Recipe",
        label_visibility="collapsed")

    c1,c2,c3,c4 = st.columns(4)
    with c1: gen_images = st.toggle("Generate Images",  value=bool(s.get("use_images",True)),           key="gen_use_images")
    with c2: gen_card   = st.toggle("Include Card",     value=bool(s.get("show_card",True)),             key="gen_show_card")
    with c3: gen_links  = st.toggle("Internal Links",   value=bool(s.get("use_internal_links",False)),   key="gen_int_links")
    with c4: delay_sec  = st.number_input("Delay (sec)", min_value=0, max_value=30, value=5, key="gen_delay")

    show_logs = st.checkbox("Show processing logs", value=False)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🚀 Generate & Publish All", type="primary") and titles_input.strip():
        titles = [t.strip() for t in titles_input.strip().splitlines() if t.strip()]
        if not titles: error_box("Enter at least one title."); return

        log_container = st.empty()
        pipeline_settings = {
            "groq_key": s.get("groq_key",""), "goapi_key": s.get("mj_key",""),
            "wp_url": s.get("wp_url",""), "wp_password": s.get("wp_password",""),
            "publish_status": s.get("publish_status","draft"),
            "mj_template": s.get("mj_template",""),
            "use_images": gen_images and bool(s.get("mj_key","")),
            "show_card": gen_card, "card_clickable": bool(s.get("card_clickable",False)),
            "use_internal_links": gen_links, "max_links": int(s.get("max_links",4)),
            "user_article_prompt": s.get("article_prompt",""),
            "user_html_structure": s.get("html_structure",""),
            "user_card_prompt": s.get("card_prompt",""),
            "user_design": {
                "main_color":   s.get("design_main_color","#333333"),
                "accent_color": s.get("design_accent_color","#ea580c"),
                "font_family":  s.get("design_font_family","inherit"),
            },
        }
        all_logs = []
        for i, title in enumerate(titles):
            st.markdown(f'<div style="background:#fff8ec;border-left:4px solid #c9892a;border-radius:0 8px 8px 0;padding:10px 14px;font-size:13px;color:#7a5820;margin-bottom:8px;">⏳ Processing <strong>{i+1}/{len(titles)}</strong>: {title}</div>', unsafe_allow_html=True)

            def log_fn(msg, _logs=all_logs, _c=log_container, _show=show_logs):
                _logs.append(msg)
                if _show:
                    _c.markdown(
                        '<div style="background:#1a1510;border-radius:10px;padding:14px;font-family:monospace;font-size:12px;color:#a0c080;max-height:200px;overflow-y:auto;">'
                        + '<br>'.join(_logs[-20:]) + '</div>', unsafe_allow_html=True)

            result = run_full_pipeline(title, pipeline_settings, log_fn=log_fn) if GEN_OK else {"success":False,"error":"Generator not available"}

            if result.get("success"):
                st.markdown(f'<div style="background:#f0faf4;border:1px solid #a4d8b8;color:#1a6e38;border-radius:9px;padding:10px 14px;font-size:13px;margin-bottom:8px;">✅ <strong>{title}</strong> → <a href="{result.get("post_url","")}" target="_blank">{result.get("post_url","view post")}</a></div>', unsafe_allow_html=True)
                db_increment_stat(st.session_state.user_id, "articles_generated")
                db_increment_stat(st.session_state.user_id, "posts_published")
                ic = result.get("image_count",0)
                if ic: db_increment_stat(st.session_state.user_id, "images_created", ic)
            else:
                error_box(f"<strong>{title}</strong>: {result.get('error','Unknown error')}")

            if i < len(titles)-1 and delay_sec > 0:
                time.sleep(delay_sec)

        st.session_state.settings = db_load_settings(st.session_state.user_id)


def tab_pinterest():
    section_header("Pinterest Auto-Post", "Configure Pinterest integration")
    s = st.session_state.settings

    if st.session_state.user_plan != "pro":
        st.markdown("""
        <div style="background:linear-gradient(135deg,#1c1810,#0f0d09);border:1px solid rgba(201,137,42,.38);
             border-radius:18px;padding:32px;text-align:center;color:#fdf6e8;margin-bottom:22px;">
          <div style="font-size:40px;margin-bottom:12px;">📌</div>
          <h3 style="font-family:Georgia,serif;font-size:24px;font-weight:800;color:#fdf6e8;margin:0 0 10px 0;">Pinterest Auto-Post</h3>
          <p style="font-size:14px;color:rgba(253,246,232,.5);line-height:1.7;max-width:480px;margin:0 auto 20px;">
            Available on the <span style="color:#e8a83e;font-weight:700;">Pro plan ($40/month)</span>.<br>
            Automatically post optimized Pins after every WordPress publish.</p>
          <div style="background:rgba(201,137,42,.15);border:1px solid rgba(201,137,42,.3);border-radius:10px;padding:16px;max-width:360px;margin:0 auto;">
            <p style="font-size:13px;color:rgba(253,246,232,.7);margin:0;line-height:2;">✅ Pinterest Keyword Optimizer<br>✅ Custom Pinterest Prompt<br>✅ Post Scheduler (day + time)<br>✅ Auto Pin from Featured Image</p>
          </div>
        </div>""", unsafe_allow_html=True)
        if st.button("⬆️ Upgrade to Pro", type="primary"):
            st.session_state.dash_tab = "billing"; st.rerun()
        return

    if st.session_state.save_ok:
        success_box("Pinterest settings saved!")
        st.session_state.save_ok = False

    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;">', unsafe_allow_html=True)
        st.markdown('<h3 style="font-size:14.5px;font-weight:700;color:#1a1510;margin:0 0 18px 0;padding-bottom:13px;border-bottom:1px solid #f0e6d4;">🔑 Pinterest Credentials</h3>', unsafe_allow_html=True)
        pin_token = st.text_input("Pinterest Access Token", value=s.get("pinterest_token",""), type="password")
        pin_board = st.text_input("Pinterest Board ID",     value=s.get("pinterest_board",""), placeholder="Your board ID")
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;">', unsafe_allow_html=True)
        st.markdown('<h3 style="font-size:14.5px;font-weight:700;color:#1a1510;margin:0 0 18px 0;padding-bottom:13px;border-bottom:1px solid #f0e6d4;">📌 Pinterest Prompt</h3>', unsafe_allow_html=True)
        pin_prompt = st.text_area("Your Pinterest Prompt", value=s.get("pinterest_prompt",""), height=160,
            placeholder="My audience is busy moms who love quick dinner recipes. Write warm, conversational pin descriptions using family food keywords.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:26px;margin-top:18px;">', unsafe_allow_html=True)
    st.markdown('<h3 style="font-size:14.5px;font-weight:700;color:#1a1510;margin:0 0 6px 0;padding-bottom:13px;border-bottom:1px solid #f0e6d4;">📅 Pinterest Post Scheduler</h3>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13px;color:#8a7a60;margin-bottom:16px;">Choose which days and time your Pins are posted after each article is published.</p>', unsafe_allow_html=True)

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

    tc1,tc2 = st.columns(2)
    with tc1:
        schedule_time = st.time_input("Posting Time", value=datetime.strptime(s.get("schedule_time","09:00"),"%H:%M").time())
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
            "pinterest_token": pin_token, "pinterest_board": pin_board,
            "pinterest_prompt": pin_prompt, "schedule_days": ",".join(selected_days),
            "schedule_time": schedule_time.strftime("%H:%M"), "schedule_timezone": schedule_tz,
        })
        save_settings_to_db(); st.rerun()


def tab_billing():
    section_header("Billing", "Manage your plan and subscription")
    plan = st.session_state.user_plan
    c1,c2 = st.columns(2)
    with c1:
        active = "border:2px solid #c9892a;box-shadow:0 4px 20px rgba(201,137,42,.2);" if plan=="basic" else "border:2px solid #dfd4bc;"
        st.markdown(f"""
        <div style="background:#fff;{active}border-radius:26px;padding:40px 36px;text-align:center;">
          {'<div style="font-size:10px;font-weight:700;color:#c9892a;text-transform:uppercase;letter-spacing:2px;margin-bottom:12px;">✦ Current Plan</div>' if plan=='basic' else ''}
          <div style="font-size:11px;font-weight:700;color:#8a7a60;text-transform:uppercase;letter-spacing:2px;margin-bottom:16px;">Basic</div>
          <div style="font-family:Georgia,serif;font-size:64px;font-weight:900;color:#1a1510;line-height:1;">$30</div>
          <div style="font-size:14px;color:#8a7a60;margin-bottom:24px;">per month</div>
          <div style="text-align:left;font-size:13.5px;color:#5a5040;line-height:2.4;">
            ✅ AI Article Generation<br>✅ Midjourney Images (4/article)<br>✅ WordPress Auto-Publish<br>
            ✅ Custom Prompts &amp; Design Studio<br>✅ Internal Linking<br>❌ Pinterest Auto-Post
          </div>
        </div>""", unsafe_allow_html=True)
    with c2:
        active2 = "box-shadow:0 8px 44px rgba(201,137,42,.25);" if plan=="pro" else ""
        pro_badge = '<div style="font-size:10px;font-weight:700;color:#e8a83e;text-transform:uppercase;letter-spacing:2px;margin-bottom:12px;">✦ Current Plan</div>' if plan=="pro" else ""
        st.markdown(f"""
        <div style="background:linear-gradient(158deg,#211808,#0f0d09);border:2px solid rgba(201,137,42,.55);{active2}border-radius:26px;padding:40px 36px;text-align:center;">
          {pro_badge}
          <div style="font-size:11px;font-weight:700;color:rgba(232,168,62,.7);text-transform:uppercase;letter-spacing:2px;margin-bottom:16px;">Pro · Most Popular</div>
          <div style="font-family:Georgia,serif;font-size:64px;font-weight:900;color:#fff;line-height:1;">$40</div>
          <div style="font-size:14px;color:rgba(253,246,232,.4);margin-bottom:24px;">per month</div>
          <div style="text-align:left;font-size:13.5px;color:rgba(253,246,232,.8);line-height:2.4;">
            ✅ Everything in Basic<br>✅ Pinterest Auto-Post<br>✅ Pinterest Keyword Optimizer<br>
            ✅ Custom Pinterest Prompt<br>✅ Pinterest Post Scheduler<br>✅ Priority Support
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:24px;">', unsafe_allow_html=True)
    st.markdown('<h3 style="font-size:14.5px;font-weight:700;color:#1a1510;margin:0 0 12px 0;">💳 Payment</h3>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13.5px;color:#5a5040;line-height:1.7;">To upgrade or manage your subscription, contact us at <strong>support@nicheflow.ai</strong>. Payments processed securely via Stripe.</p>', unsafe_allow_html=True)
    if plan == "basic":
        if st.button("⬆️ Upgrade to Pro ($40/mo)", type="primary"):
            info_box("Contact support@nicheflow.ai to upgrade your account.")
    else:
        success_box("You are on the Pro plan. Contact support@nicheflow.ai to manage your subscription.")
    st.markdown('</div>', unsafe_allow_html=True)


def tab_docs():
    section_header("Documentation", "Setup guide and best practices")
    components.html(DOCS_HTML(logged_in=True), height=3200, scrolling=True)


# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
def render_dashboard():
    render_sidebar()
    tab = st.session_state.dash_tab
    st.markdown("""
    <style>
    section[data-testid="stSidebar"]{display:flex!important;}
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
#  ROUTER  — render nav listener FIRST on every public page so clicks work
# ─────────────────────────────────────────────────────────────────────────────
page = st.session_state.page

if page == "home":
    _nav_listener()   # ← listens for postMessage, redirects via query param
    components.html(HOME_HTML(), height=4600, scrolling=True)

elif page == "login":
    _nav_listener_with_forms()   # ← handles nav + login form submission
    components.html(
        LOGIN_HTML(
            error=st.session_state.auth_error,
            success=st.session_state.auth_success
        ),
        height=700, scrolling=False
    )
    st.session_state.auth_success = ""

elif page == "signup":
    _nav_listener_with_forms()   # ← handles nav + signup form submission
    components.html(
        SIGNUP_HTML(error=st.session_state.auth_error),
        height=760, scrolling=False
    )

elif page == "docs":
    _nav_listener()
    components.html(DOCS_HTML(logged_in=bool(st.session_state.user_id)), height=4400, scrolling=True)

elif page == "dashboard":
    if not st.session_state.user_id:
        st.session_state.page = "login"; st.rerun()
    else:
        render_dashboard()