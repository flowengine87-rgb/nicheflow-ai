# -*- coding: utf-8 -*-
"""
NicheFlow AI — app.py
Full SaaS: Supabase auth + real generator + working navigation via st.query_params
"""

import streamlit as st
import hashlib, json, time, re
from datetime import datetime

st.set_page_config(
    page_title="NicheFlow AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── GLOBAL CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu, footer, header, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"] { display:none !important; }
.block-container { padding:0 !important; max-width:100% !important; }
.stApp { background:#0a0a0a; }
section[data-testid="stSidebar"] { display:none !important; }
div[data-testid="stVerticalBlock"] > div { padding:0 !important; }
</style>
""", unsafe_allow_html=True)

# ─── SUPABASE via requests (no supabase package needed) ───────────────────────
import requests as _req

def _sb_url():
    try: return st.secrets["SUPABASE_URL"].rstrip("/")
    except: return "MISSING"

def _sb_secret():
    try: return st.secrets["SUPABASE_SECRET"]
    except:
        try: return st.secrets["SUPABASE_KEY"]
        except: return "MISSING"

def _sb_h():
    k = _sb_secret()
    return {"apikey": k, "Authorization": f"Bearer {k}",
            "Content-Type": "application/json", "Prefer": "return=representation"}

def sb_select(table, qs=""):
    try:
        r = _req.get(f"{_sb_url()}/rest/v1/{table}?{qs}", headers=_sb_h(), timeout=10)
        return r.json() if r.status_code == 200 else []
    except: return []

def sb_insert(table, data):
    try:
        r = _req.post(f"{_sb_url()}/rest/v1/{table}", headers=_sb_h(), json=data, timeout=10)
        j = r.json()
        return j[0] if isinstance(j, list) and j else j if isinstance(j, dict) else None
    except: return None

def sb_update(table, qs, data):
    try:
        r = _req.patch(f"{_sb_url()}/rest/v1/{table}?{qs}", headers=_sb_h(), json=data, timeout=10)
        return r.status_code in [200, 204]
    except: return False

# ─── AUTH ─────────────────────────────────────────────────────────────────────
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

def signup_user(email, pw):
    if not email or "@" not in email: return {"ok": False, "err": "Invalid email"}
    if len(pw) < 6: return {"ok": False, "err": "Password must be at least 6 characters"}
    ex = sb_select("users", f"email=eq.{email}&select=id")
    if ex: return {"ok": False, "err": "Email already registered"}
    u = sb_insert("users", {"email": email, "password_hash": hash_pw(pw), "plan": "basic"})
    if u and u.get("id"):
        sb_insert("user_settings", {"user_id": u["id"]})
        return {"ok": True, "user": u}
    return {"ok": False, "err": "Signup failed — check Supabase connection"}

def login_user(email, pw):
    rows = sb_select("users", f"email=eq.{email}&select=id,email,plan,password_hash")
    if not rows: return {"ok": False, "err": "Email not found"}
    u = rows[0]
    if u.get("password_hash") != hash_pw(pw): return {"ok": False, "err": "Wrong password"}
    return {"ok": True, "user": u}

def get_settings(user_id):
    rows = sb_select("user_settings", f"user_id=eq.{user_id}&select=*")
    return rows[0] if rows else {}

def save_settings(user_id, data):
    data["user_id"] = user_id
    data["updated_at"] = datetime.utcnow().isoformat()
    existing = sb_select("user_settings", f"user_id=eq.{user_id}&select=id")
    if existing:
        return sb_update("user_settings", f"user_id=eq.{user_id}", data)
    else:
        return sb_insert("user_settings", data)

# ─── SESSION STATE ─────────────────────────────────────────────────────────────
def init_session():
    for k, v in {
        "user": None, "page": "home", "gen_logs": [],
        "gen_result": None, "last_settings": {},
        "wp_categories": [], "pinterest_boards": [],
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ─── NAVIGATION via query params (no iframe — works on Streamlit Cloud!) ───────
nav_param = st.query_params.get("nav", "home")
if nav_param != st.session_state.page:
    st.session_state.page = nav_param

def go(page):
    st.query_params["nav"] = page
    st.session_state.page = page
    st.rerun()

# ─── TOKEN COUNTER ────────────────────────────────────────────────────────────
def count_tokens(text):
    return max(1, len(text.split()) * 4 // 3) if text else 0

def token_warning(text, label="Prompt"):
    n = count_tokens(text)
    if n >= 3000:
        st.error(f"🚨 **{label} is very long (~{n} tokens).** Groq limit is 4096 tokens — trim your prompt or it WILL fail!")
    elif n >= 2000:
        st.warning(f"⚠️ **{label} is getting long (~{n} tokens).** Consider shortening to stay safely under the 4096 token limit.")

# ─── COLORS ───────────────────────────────────────────────────────────────────
GOLD   = "#c9a84c"
CREAM  = "#f5f0e8"
DARK   = "#0a0a0a"
DARK2  = "#111111"
DARK3  = "#1a1a1a"
CARD   = "#141414"
BORDER = "#2a2a2a"
GREEN  = "#22c55e"
RED    = "#ef4444"

# ═══════════════════════════════════════════════════════════════════════════════
#  LANDING PAGE
# ═══════════════════════════════════════════════════════════════════════════════
def page_home():
    st.markdown(f"""
<style>
.nf-nav{{display:flex;align-items:center;justify-content:space-between;
         padding:20px 60px;border-bottom:1px solid {BORDER};background:{DARK};}}
.nf-logo{{font-size:22px;font-weight:900;color:{CREAM};letter-spacing:-0.5px;}}
.nf-logo span{{color:{GOLD};}}
.nf-hero{{text-align:center;padding:120px 40px 80px;background:{DARK};}}
.nf-hero h1{{font-size:clamp(40px,6vw,80px);font-weight:900;color:{CREAM};
             margin:0 0 24px;line-height:1.05;letter-spacing:-2px;}}
.nf-hero h1 em{{color:{GOLD};font-style:normal;}}
.nf-hero p{{font-size:20px;color:#888;max-width:600px;margin:0 auto 48px;line-height:1.6;}}
.nf-btn{{display:inline-block;background:{GOLD};color:{DARK};
         padding:16px 40px;border-radius:50px;font-weight:800;
         font-size:16px;text-decoration:none;margin:8px;}}
.nf-btn-outline{{background:transparent;color:{CREAM};border:2px solid {BORDER};}}
.nf-features{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
              gap:24px;padding:80px 60px;background:{DARK2};}}
.nf-feat{{background:{CARD};border:1px solid {BORDER};border-radius:16px;padding:32px;}}
.nf-feat .icon{{font-size:36px;margin-bottom:16px;}}
.nf-feat h3{{color:{CREAM};font-size:18px;font-weight:700;margin:0 0 10px;}}
.nf-feat p{{color:#666;font-size:14px;line-height:1.6;margin:0;}}
.nf-pricing{{padding:80px 60px;background:{DARK};}}
.nf-pricing h2{{text-align:center;color:{CREAM};font-size:42px;
                font-weight:900;margin:0 0 60px;letter-spacing:-1px;}}
.nf-plans{{display:grid;grid-template-columns:1fr 1fr;gap:24px;max-width:800px;margin:0 auto;}}
.nf-plan{{background:{CARD};border:1px solid {BORDER};border-radius:20px;padding:40px;text-align:center;}}
.nf-plan.pro{{border-color:{GOLD};}}
.nf-plan .badge{{background:{GOLD};color:{DARK};font-size:11px;font-weight:800;
                 padding:4px 14px;border-radius:50px;display:inline-block;margin-bottom:20px;}}
.nf-plan h3{{color:{CREAM};font-size:24px;font-weight:800;margin:0 0 8px;}}
.nf-plan .price{{font-size:56px;font-weight:900;color:{GOLD};margin:16px 0 8px;}}
.nf-plan .price span{{font-size:18px;color:#666;font-weight:400;}}
.nf-plan ul{{list-style:none;padding:0;margin:24px 0 32px;text-align:left;}}
.nf-plan ul li{{color:#999;font-size:14px;padding:8px 0;border-bottom:1px solid {BORDER};}}
.nf-plan ul li::before{{content:"✦ ";color:{GOLD};}}
.nf-footer{{background:{DARK2};border-top:1px solid {BORDER};
            padding:40px 60px;text-align:center;color:#444;font-size:14px;}}
</style>

<div class="nf-nav">
  <div class="nf-logo">Niche<span>Flow</span> AI</div>
  <div>
    <a class="nf-btn nf-btn-outline" href="?nav=docs" style="color:{CREAM};text-decoration:none;padding:10px 24px;font-size:14px;">Docs</a>
    <a class="nf-btn nf-btn-outline" href="?nav=login" style="color:{CREAM};text-decoration:none;padding:10px 24px;font-size:14px;margin-left:8px;">Login</a>
    <a class="nf-btn" href="?nav=signup" style="color:{DARK};text-decoration:none;padding:10px 24px;font-size:14px;margin-left:8px;">Get Started Free</a>
  </div>
</div>

<div class="nf-hero">
  <h1>AI Content Engine<br>for <em>Niche Sites</em></h1>
  <p>Generate SEO articles, info cards, and Midjourney images — published directly to WordPress. On autopilot.</p>
  <a class="nf-btn" href="?nav=signup" style="color:{DARK};text-decoration:none;">Start Free Today ✦</a>
  <a class="nf-btn nf-btn-outline" href="?nav=docs" style="color:{CREAM};text-decoration:none;">See How It Works</a>
</div>

<div class="nf-features">
  <div class="nf-feat"><div class="icon">✍️</div><h3>AI Article Generator</h3><p>Write complete SEO-optimized articles using Groq's fastest models. Customize the HTML structure or just use a prompt — your choice.</p></div>
  <div class="nf-feat"><div class="icon">🖼️</div><h3>Midjourney Images</h3><p>Generate 4 professional images per article with GoAPI. Auto-uploaded to your WordPress media library.</p></div>
  <div class="nf-feat"><div class="icon">🃏</div><h3>Custom Info Cards</h3><p>Beautiful recipe cards, travel cards, product cards — fully customizable design and fields for any niche.</p></div>
  <div class="nf-feat"><div class="icon">🔗</div><h3>Internal Linking</h3><p>Automatically links to your existing posts, loaded fresh from WordPress each run to stay always up to date.</p></div>
  <div class="nf-feat"><div class="icon">📌</div><h3>Pinterest Publisher</h3><p>Auto-generate optimized pins and publish directly to your boards. Schedule posts for maximum reach. (Pro)</p></div>
  <div class="nf-feat"><div class="icon">⚡</div><h3>Zero Setup</h3><p>Add your API keys once. Generate and publish in one click. No technical knowledge required.</p></div>
</div>

<div class="nf-pricing">
  <h2>Simple Pricing</h2>
  <div class="nf-plans">
    <div class="nf-plan">
      <div class="badge">BASIC</div>
      <h3>Basic</h3>
      <div class="price">$30<span>/mo</span></div>
      <ul>
        <li>Unlimited article generation</li>
        <li>3 Groq AI models auto-fallback</li>
        <li>Midjourney images via GoAPI</li>
        <li>WordPress auto-publish</li>
        <li>Custom HTML templates</li>
        <li>Internal linking system</li>
      </ul>
      <a class="nf-btn" href="?nav=signup" style="color:{DARK};text-decoration:none;display:block;">Get Started</a>
    </div>
    <div class="nf-plan pro">
      <div class="badge">⭐ PRO</div>
      <h3>Pro</h3>
      <div class="price">$40<span>/mo</span></div>
      <ul>
        <li>Everything in Basic</li>
        <li>Pinterest auto-publishing</li>
        <li>Pinterest board scheduler</li>
        <li>Pinterest prompt customizer</li>
        <li>Pinterest post status tracking</li>
        <li>Priority support</li>
      </ul>
      <a class="nf-btn" href="?nav=signup" style="color:{DARK};text-decoration:none;display:block;">Go Pro</a>
    </div>
  </div>
</div>

<div class="nf-footer">✦ NicheFlow AI — Built for content creators worldwide</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  LOGIN PAGE
# ═══════════════════════════════════════════════════════════════════════════════
def page_login():
    st.markdown(f"""
<style>.stApp{{background:{DARK};}}</style>
<div style="background:{DARK};min-height:100vh;padding:40px 20px;">
<a href="?nav=home" style="color:{GOLD};text-decoration:none;font-size:14px;
   display:block;text-align:center;margin-bottom:24px;">← Back to Home</a>
<div style="background:{CARD};border:1px solid {BORDER};border-radius:24px;
            padding:48px;max-width:440px;margin:0 auto;">
<div style="text-align:center;font-size:28px;font-weight:900;color:{CREAM};margin-bottom:8px;">
  Niche<span style="color:{GOLD};">Flow</span> AI</div>
<div style="text-align:center;color:#666;font-size:14px;margin-bottom:36px;">
  Welcome back — sign in to your workspace</div>
""", unsafe_allow_html=True)

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="you@example.com")
        pw    = st.text_input("Password", type="password", placeholder="••••••••")
        sub   = st.form_submit_button("Sign In ✦", use_container_width=True)
        if sub:
            if not email or not pw:
                st.error("Please fill in all fields")
            else:
                with st.spinner("Signing in..."):
                    res = login_user(email.strip().lower(), pw)
                if res["ok"]:
                    st.session_state.user = res["user"]
                    st.session_state.last_settings = {}
                    go("dashboard")
                else:
                    st.error(f"❌ {res['err']}")

    st.markdown(f"""
<div style="text-align:center;margin-top:24px;color:#666;font-size:14px;">
  Don't have an account?
  <a href="?nav=signup" style="color:{GOLD};text-decoration:none;">Sign up free</a>
</div></div></div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  SIGNUP PAGE
# ═══════════════════════════════════════════════════════════════════════════════
def page_signup():
    st.markdown(f"""
<style>.stApp{{background:{DARK};}}</style>
<div style="background:{DARK};min-height:100vh;padding:40px 20px;">
<a href="?nav=home" style="color:{GOLD};text-decoration:none;font-size:14px;
   display:block;text-align:center;margin-bottom:24px;">← Back to Home</a>
<div style="background:{CARD};border:1px solid {BORDER};border-radius:24px;
            padding:48px;max-width:440px;margin:0 auto;">
<div style="text-align:center;font-size:28px;font-weight:900;color:{CREAM};margin-bottom:8px;">
  Niche<span style="color:{GOLD};">Flow</span> AI</div>
<div style="text-align:center;color:#666;font-size:14px;margin-bottom:36px;">
  Create your free account — no credit card required</div>
""", unsafe_allow_html=True)

    with st.form("signup_form"):
        email = st.text_input("Email", placeholder="you@example.com")
        pw    = st.text_input("Password", type="password", placeholder="Min 6 characters")
        pw2   = st.text_input("Confirm Password", type="password", placeholder="Repeat password")
        sub   = st.form_submit_button("Create Account ✦", use_container_width=True)
        if sub:
            if not email or not pw:
                st.error("Please fill in all fields")
            elif pw != pw2:
                st.error("Passwords do not match")
            else:
                with st.spinner("Creating account..."):
                    res = signup_user(email.strip().lower(), pw)
                if res["ok"]:
                    st.session_state.user = res["user"]
                    st.session_state.last_settings = {}
                    st.success("✅ Account created! Welcome!")
                    time.sleep(1)
                    go("dashboard")
                else:
                    st.error(f"❌ {res['err']}")

    st.markdown(f"""
<div style="text-align:center;margin-top:24px;color:#666;font-size:14px;">
  Already have an account?
  <a href="?nav=login" style="color:{GOLD};text-decoration:none;">Sign in</a>
</div></div></div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  DOCS PAGE
# ═══════════════════════════════════════════════════════════════════════════════
def page_docs():
    st.markdown(f"""
<style>.stApp{{background:{DARK};}}</style>
<div style="background:{DARK};min-height:100vh;padding:40px 60px;max-width:900px;margin:0 auto;">
<a href="?nav=home" style="color:{GOLD};text-decoration:none;font-size:14px;
   display:inline-block;margin-bottom:32px;">← Back to Home</a>
<h1 style="color:{CREAM};font-size:42px;font-weight:900;margin:0 0 16px;letter-spacing:-1px;">Documentation</h1>
<p style="color:#666;font-size:16px;margin:0 0 48px;">Everything you need to set up and use NicheFlow AI.</p>
""", unsafe_allow_html=True)

    sections = [
        ("🔑 Groq API Key (Free)", f"""
<b style="color:{CREAM};">What it is:</b> Your AI writing engine. Free at <a href="https://console.groq.com" target="_blank" style="color:{GOLD};">console.groq.com</a><br><br>
<b style="color:{CREAM};">How to get it:</b><br>
1. Go to console.groq.com → sign up free<br>
2. Click "API Keys" in the left sidebar<br>
3. Click "Create API Key" → copy it (starts with <code>gsk_</code>)<br>
4. Paste in Settings tab → Groq API Key field<br><br>
<b style="color:{CREAM};">Free limits:</b> 14,400 requests/day · 6,000 tokens/min per model<br>
<b style="color:{CREAM};">Auto-fallback:</b> If one model is rate-limited, the app automatically tries the next one.
        """),
        ("🖼️ GoAPI Key (Midjourney Images)", f"""
<b style="color:{CREAM};">What it is:</b> API for generating Midjourney images. Paid at <a href="https://goapi.ai" target="_blank" style="color:{GOLD};">goapi.ai</a><br><br>
<b style="color:{CREAM};">How to get it:</b><br>
1. Create account at goapi.ai<br>
2. Add credits to your account<br>
3. Go to API Keys → copy your key<br>
4. Paste in Settings → GoAPI Key field<br><br>
<b style="color:{CREAM};">Optional:</b> Leave empty to generate articles without images. Everything else still works.
        """),
        ("🌐 WordPress Connection", f"""
<b style="color:{CREAM};">Format:</b> WordPress URL + Application Password<br><br>
<b style="color:{CREAM};">Create an Application Password:</b><br>
1. Go to WP Admin → Users → Your Profile<br>
2. Scroll to "Application Passwords" section<br>
3. Enter name "NicheFlow" → click "Add New Application Password"<br>
4. Copy the generated password (only shown once!)<br><br>
<b style="color:{CREAM};">Enter in Settings as:</b><br>
<code style="background:{DARK3};padding:4px 8px;border-radius:6px;">YourUsername:xxxx xxxx xxxx xxxx xxxx xxxx</code><br><br>
<b style="color:{CREAM};">URL format:</b> <code>https://yoursite.com</code> (no trailing slash)
        """),
        ("✍️ Article Prompt", f"""
<b style="color:{CREAM};">What it does:</b> Tells the AI your niche, style, and what to include in every article.<br><br>
<b style="color:{CREAM};">Example:</b> "Write a detailed food blog post. Use a warm friendly tone. Include preparation tips, variations, and serving suggestions. Target home cooks. Use short paragraphs and subheadings."<br><br>
<b style="color:{CREAM};">HTML Mode:</b> Enable "Custom HTML Structure" to paste your own HTML template. The AI fills it with real content following your exact design.<br><br>
<b style="color:{CREAM};">⚠️ Token limit:</b> Keep under 2000 tokens (~1500 words). A warning appears at 2000, and error at 3000.
        """),
        ("🃏 Card Prompt", f"""
<b style="color:{CREAM};">What it does:</b> Tells the AI what info to extract for the styled card below each article.<br><br>
<b style="color:{CREAM};">Recipe card example:</b> "Extract recipe name, prep time, cook time, total time, servings, calories, all ingredients, step-by-step instructions."<br><br>
<b style="color:{CREAM};">Travel card example:</b> "Extract best time to visit, budget estimate, language, currency, top 5 attractions."<br><br>
<b style="color:{CREAM};">Custom card:</b> You can use the color pickers to match your brand colors. The card renders inside the article with interactive ingredient checkboxes.<br><br>
<b style="color:{CREAM};">No card:</b> Uncheck "Show Info Card" to skip it entirely.
        """),
        ("🔗 Internal Links", f"""
<b style="color:{CREAM};">What it does:</b> Automatically adds links to your existing published posts inside new articles.<br><br>
<b style="color:{CREAM};">How it works:</b><br>
1. System fetches your last 100 published posts from WordPress (fresh each run)<br>
2. Finds relevant phrases in the new article matching your post titles<br>
3. Adds clickable links styled in your brand color<br><br>
<b style="color:{CREAM};">Setting:</b> Enable in Settings → choose max links per article (1-10, default 4).
        """),
        ("📌 Pinterest (Pro Only)", f"""
<b style="color:{CREAM};">What it does:</b> After publishing to WordPress, auto-creates and posts a Pinterest pin.<br><br>
<b style="color:{CREAM};">Pinterest Token:</b><br>
1. Go to <a href="https://developers.pinterest.com/apps/" target="_blank" style="color:{GOLD};">developers.pinterest.com/apps</a><br>
2. Create an app → Go to Access tokens<br>
3. Enable scopes: <code>boards:read, pins:write, pins:read</code><br>
4. Copy token → paste in Pinterest tab<br><br>
<b style="color:{CREAM};">Boards:</b> Click "Load Boards" to see all your boards → select which to post to.<br><br>
<b style="color:{CREAM};">Pinterest Prompt:</b> Tell the AI how to write pins. E.g. "Casual inspiring tone. 5 hashtags. Target home cooks 25-45."<br><br>
<b style="color:{CREAM};">Scheduler:</b> Choose days + time + timezone for auto-posting.
        """),
    ]

    for title, content in sections:
        with st.expander(title, expanded=False):
            st.markdown(f"<div style='color:#aaa;font-size:14px;line-height:1.8;'>{content}</div>",
                       unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def page_dashboard():
    user = st.session_state.user
    if not user:
        go("login")
        return

    uid    = user["id"]
    plan   = user.get("plan", "basic")
    email  = user.get("email", "")
    is_pro = plan == "pro"

    # Load settings once per session
    if not st.session_state.last_settings:
        st.session_state.last_settings = get_settings(uid)
    sett = st.session_state.last_settings

    # ── TOP NAV ────────────────────────────────────────────────────────────────
    st.markdown(f"""
<style>
.stTabs [data-baseweb="tab-list"]{{
  background:{DARK2};gap:0;border-bottom:1px solid {BORDER};padding:0 40px;}}
.stTabs [data-baseweb="tab"]{{
  background:transparent;color:#666;padding:14px 24px;font-size:14px;
  font-weight:600;border:none;border-bottom:2px solid transparent;}}
.stTabs [aria-selected="true"]{{
  color:{GOLD};border-bottom:2px solid {GOLD} !important;background:transparent;}}
.stTabs [data-baseweb="tab-panel"]{{background:{DARK};padding:0;}}
.stTextInput input,.stTextArea textarea{{
  background:{DARK3} !important;border:1px solid {BORDER} !important;
  color:{CREAM} !important;border-radius:10px !important;}}
.stSelectbox [data-baseweb="select"]{{background:{DARK3} !important;border:1px solid {BORDER} !important;}}
.stButton>button{{
  background:{GOLD} !important;color:{DARK} !important;
  border:none !important;border-radius:10px !important;font-weight:700 !important;}}
.stButton>button:hover{{background:{CREAM} !important;}}
.stCheckbox span{{color:{CREAM} !important;}}
.metric-card{{background:{CARD};border:1px solid {BORDER};border-radius:14px;
              padding:20px 24px;margin-bottom:16px;}}
.metric-card h4{{color:#666;font-size:11px;font-weight:700;
                 text-transform:uppercase;letter-spacing:1px;margin:0 0 8px;}}
.guide-box{{background:{DARK3};border-left:3px solid {GOLD};
            border-radius:0 10px 10px 0;padding:14px 18px;
            margin:8px 0 20px;font-size:13px;color:#888;line-height:1.7;}}
.log-box{{background:{DARK3};border:1px solid {BORDER};border-radius:10px;
          padding:16px;font-family:monospace;font-size:12px;
          color:#aaa;max-height:320px;overflow-y:auto;white-space:pre-wrap;}}
</style>
<div style="display:flex;align-items:center;justify-content:space-between;
            padding:16px 40px;border-bottom:1px solid {BORDER};background:{DARK2};
            position:sticky;top:0;z-index:100;">
  <div style="font-size:20px;font-weight:900;color:{CREAM};">
    Niche<span style="color:{GOLD};">Flow</span> AI</div>
  <div style="display:flex;align-items:center;gap:16px;">
    <span style="color:#666;font-size:13px;">{email}</span>
    <span style="background:{'#c9a84c' if is_pro else DARK3};
                 color:{'#0a0a0a' if is_pro else GOLD};
                 border:1px solid {GOLD}40;padding:4px 12px;
                 border-radius:50px;font-size:12px;font-weight:700;">
      {'⭐ PRO' if is_pro else 'BASIC'} — ${'40' if is_pro else '30'}/mo</span>
    <a href="?nav=home" style="color:#555;text-decoration:none;font-size:13px;">← Exit</a>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── TABS ───────────────────────────────────────────────────────────────────
    tab_labels = ["🏠 Overview", "⚙️ Settings", "✍️ Generate", "📊 History"]
    if is_pro:
        tab_labels.append("📌 Pinterest")

    tabs = st.tabs(tab_labels)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 1 — OVERVIEW
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[0]:
        st.markdown(f"<div style='padding:32px 40px;'>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='color:{CREAM};font-weight:800;margin:0 0 8px;'>Welcome back 👋</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#666;margin:0 0 32px;'>Your workspace status and connected services.</p>", unsafe_allow_html=True)

        groq_key = sett.get("groq_key","")
        wp_url   = sett.get("wp_url","")
        wp_pass  = sett.get("wp_password","")
        mj_key   = sett.get("mj_key","")

        col1, col2, col3 = st.columns(3)
        with col1:
            if not groq_key:
                gs, gc = "⬜ Not configured", "#444"
            elif groq_key.startswith("gsk_"):
                gs, gc = "✅ Key configured", GREEN
            else:
                gs, gc = "❌ Invalid (needs gsk_...)", RED
            st.markdown(f"""<div class="metric-card">
              <h4>Groq AI</h4>
              <p style="color:{gc};font-weight:700;margin:0 0 8px;">{gs}</p>
              <p style="color:#555;font-size:12px;margin:0;">Auto-fallback across 3 models</p>
            </div>""", unsafe_allow_html=True)

        with col2:
            if not wp_url or not wp_pass:
                ws, wc = "⬜ Not configured", "#444"
            elif ":" not in wp_pass:
                ws, wc = "⚠️ Wrong password format", GOLD
            else:
                ws, wc = "✅ Credentials saved", GREEN
            st.markdown(f"""<div class="metric-card">
              <h4>WordPress</h4>
              <p style="color:{wc};font-weight:700;margin:0 0 8px;">{ws}</p>
              <p style="color:#555;font-size:12px;margin:0;">Format: Username:app-password</p>
            </div>""", unsafe_allow_html=True)

        with col3:
            ms = ("✅ GoAPI key saved", GREEN) if mj_key else ("⬜ Not configured (optional)", "#444")
            st.markdown(f"""<div class="metric-card">
              <h4>Midjourney Images</h4>
              <p style="color:{ms[1]};font-weight:700;margin:0 0 8px;">{ms[0]}</p>
              <p style="color:#555;font-size:12px;margin:0;">4 images per article via GoAPI</p>
            </div>""", unsafe_allow_html=True)

        # Groq Models
        st.markdown(f"<h3 style='color:{CREAM};font-weight:700;margin:24px 0 16px;'>🤖 Groq Models — Auto-Fallback</h3>", unsafe_allow_html=True)
        m_col1, m_col2, m_col3 = st.columns(3)
        models = [
            ("Primary", "llama-3.3-70b-versatile", "Best quality. Used first for all articles. If rate-limited → switches to Model 2."),
            ("Fallback", "llama-4-scout-17b-16e", "Fast + capable. Used if Model 1 fails. If rate-limited → switches to Model 3."),
            ("Last Resort", "llama-3.1-8b-instant", "Fastest model. Also used for card generation. Rarely rate-limited."),
        ]
        for col, (label, model, desc) in zip([m_col1, m_col2, m_col3], models):
            with col:
                st.markdown(f"""<div class="metric-card">
                  <h4>Model {models.index((label,model,desc))+1} — {label}</h4>
                  <p style="color:{GOLD};font-weight:700;font-size:13px;margin:0 0 6px;">{model}</p>
                  <p style="color:#555;font-size:12px;margin:0;">{desc}</p>
                </div>""", unsafe_allow_html=True)

        # Quick start
        st.markdown(f"""
<div style="background:{CARD};border:1px solid {BORDER};border-radius:14px;padding:24px;margin-top:8px;">
  <h3 style="color:{CREAM};font-weight:700;margin:0 0 16px;">⚡ Quick Start Guide</h3>
  <div style="color:#888;font-size:14px;line-height:2.2;">
    <b style="color:{GOLD};">Step 1</b> → <b style="color:{CREAM};">Settings</b> tab → Add Groq key + WordPress credentials<br>
    <b style="color:{GOLD};">Step 2</b> → Settings → Write your Article Prompt and Card Prompt (your niche, tone, style)<br>
    <b style="color:{GOLD};">Step 3</b> → <b style="color:{CREAM};">Generate</b> tab → Enter article title → Click Generate & Publish<br>
    <b style="color:{GOLD};">Step 4</b> → Article is published to WordPress automatically ✦<br>
    <b style="color:{GOLD};">Pro Tip</b> → Enable Internal Linking to automatically connect your articles to each other
  </div>
</div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 2 — SETTINGS
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[1]:
        st.markdown(f"<div style='padding:32px 40px;max-width:900px;'>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='color:{CREAM};font-weight:800;margin:0 0 32px;'>⚙️ Settings</h2>", unsafe_allow_html=True)

        with st.form("settings_form", clear_on_submit=False):

            # API KEYS
            st.markdown(f"<h3 style='color:{GOLD};font-weight:700;margin:0 0 4px;'>🔑 API Keys</h3>", unsafe_allow_html=True)
            st.markdown(f"<div class='guide-box'>Your keys are stored securely per your account. Never shared. Each user has their own isolated credentials.</div>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                groq_key_in = st.text_input("Groq API Key", value=sett.get("groq_key",""), type="password",
                    placeholder="gsk_...", help="Free at console.groq.com")
            with col2:
                mj_key_in = st.text_input("GoAPI Key (Midjourney)", value=sett.get("mj_key",""), type="password",
                    placeholder="goapi-...", help="Optional — skip for text-only articles")

            # WORDPRESS
            st.markdown(f"<h3 style='color:{GOLD};font-weight:700;margin:24px 0 4px;'>🌐 WordPress</h3>", unsafe_allow_html=True)
            st.markdown(f"""<div class='guide-box'>
<b>URL:</b> e.g. <code>https://yoursite.com</code><br>
<b>App Password format:</b> <code>YourUsername:xxxx xxxx xxxx xxxx xxxx xxxx</code><br>
Create in WP Admin → Users → Profile → Application Passwords
            </div>""", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                wp_url_in = st.text_input("WordPress URL", value=sett.get("wp_url",""),
                    placeholder="https://yoursite.com")
            with col2:
                wp_pass_in = st.text_input("App Password", value=sett.get("wp_password",""), type="password",
                    placeholder="Username:xxxx xxxx xxxx xxxx")
            pub_status = st.selectbox("Publish Status",
                ["draft","publish","pending"],
                index=["draft","publish","pending"].index(sett.get("publish_status","draft")))

            # ARTICLE PROMPT
            st.markdown(f"<h3 style='color:{GOLD};font-weight:700;margin:24px 0 4px;'>✍️ Article Prompt</h3>", unsafe_allow_html=True)
            st.markdown(f"""<div class='guide-box'>
Tell the AI your niche, writing style, tone, structure, what to include/avoid.<br>
<b>Example:</b> "Write a detailed food blog post. Warm friendly tone. Include tips, variations, and serving suggestions. Target home cooks. Short paragraphs and subheadings."
            </div>""", unsafe_allow_html=True)
            art_prompt_in = st.text_area("Article Prompt", value=sett.get("article_prompt",""), height=140,
                placeholder="Describe your niche, writing style, tone, and what to include in every article...")
            token_warning(art_prompt_in, "Article Prompt")

            use_html_in = st.checkbox("🎨 Use Custom HTML Structure Template",
                value=bool(sett.get("html_structure","")),
                help="Paste your own HTML template. AI fills it with real content.")
            html_struct_in = ""
            if use_html_in:
                st.markdown(f"""<div class='guide-box'>
Paste your HTML template. Use placeholder text the AI will replace with real content.
You can include inline CSS. The AI will follow your structure exactly.
                </div>""", unsafe_allow_html=True)
                html_struct_in = st.text_area("HTML Structure Template",
                    value=sett.get("html_structure",""), height=180,
                    placeholder="<article>\n  <h1>[TITLE]</h1>\n  <p>[INTRO PARAGRAPH]</p>\n  <h2>[SECTION 1]</h2>\n  ...\n</article>")
                token_warning(html_struct_in, "HTML Template")

            # CARD PROMPT
            st.markdown(f"<h3 style='color:{GOLD};font-weight:700;margin:24px 0 4px;'>🃏 Info Card</h3>", unsafe_allow_html=True)
            st.markdown(f"""<div class='guide-box'>
The card appears inside your article with structured info (recipe stats, ingredients, etc.).<br>
<b>Recipe example:</b> "Extract: prep time, cook time, servings, calories, all ingredients, step-by-step instructions."<br>
<b>Travel example:</b> "Extract: best time to visit, budget, language, currency, top 5 attractions."<br>
Leave empty or uncheck to skip the card.
            </div>""", unsafe_allow_html=True)
            show_card_in = st.checkbox("Show Info Card in Articles", value=sett.get("show_card", True))

            card_prompt_in = ""; main_color_in = sett.get("main_color","#c9a84c")
            accent_color_in = sett.get("accent_color","#ea580c"); card_click_in = False
            if show_card_in:
                card_prompt_in = st.text_area("Card Prompt", value=sett.get("card_prompt",""), height=110,
                    placeholder="What should the card show? E.g. prep time, ingredients, instructions...")
                token_warning(card_prompt_in, "Card Prompt")
                col1, col2, col3 = st.columns(3)
                with col1:
                    main_color_in = st.color_picker("Card Main Color", value=sett.get("main_color","#c9a84c"))
                with col2:
                    accent_color_in = st.color_picker("Card Accent Color", value=sett.get("accent_color","#ea580c"))
                with col3:
                    card_click_in = st.checkbox("Card links to article", value=sett.get("card_clickable", False))

            # MIDJOURNEY PROMPT
            st.markdown(f"<h3 style='color:{GOLD};font-weight:700;margin:24px 0 4px;'>🖼️ Midjourney Image Prompt</h3>", unsafe_allow_html=True)
            st.markdown(f"""<div class='guide-box'>
Template for image generation. Use <code>{{recipe_name}}</code> as placeholder for the article title.<br>
<b>Example:</b> <code>{{recipe_name}}, food photography, natural light, rustic table --ar 2:3 --v 6.1</code><br>
Leave empty for auto-generated prompts.
            </div>""", unsafe_allow_html=True)
            mj_template_in = st.text_area("Midjourney Prompt Template",
                value=sett.get("mj_template",""), height=70,
                placeholder="{recipe_name}, professional food photography, natural light --ar 2:3 --v 6.1")

            # INTERNAL LINKS
            st.markdown(f"<h3 style='color:{GOLD};font-weight:700;margin:24px 0 4px;'>🔗 Internal Linking</h3>", unsafe_allow_html=True)
            st.markdown(f"""<div class='guide-box'>
Automatically links phrases in new articles to your existing published WordPress posts.
Posts are loaded fresh from WordPress on every generation run — always up to date.
            </div>""", unsafe_allow_html=True)
            use_links_in = st.checkbox("Enable Internal Linking", value=sett.get("use_internal_links", False))
            max_links_in = 4
            if use_links_in:
                max_links_in = st.slider("Max internal links per article", 1, 10, int(sett.get("max_links", 4)))

            sub_sett = st.form_submit_button("💾 Save All Settings", use_container_width=True)

        if sub_sett:
            payload = {
                "groq_key":           groq_key_in.strip(),
                "mj_key":             mj_key_in.strip(),
                "wp_url":             wp_url_in.strip().rstrip("/"),
                "wp_password":        wp_pass_in.strip(),
                "publish_status":     pub_status,
                "article_prompt":     art_prompt_in,
                "html_structure":     html_struct_in,
                "show_card":          show_card_in,
                "card_prompt":        card_prompt_in if show_card_in else "",
                "main_color":         main_color_in,
                "accent_color":       accent_color_in,
                "card_clickable":     card_click_in,
                "mj_template":        mj_template_in,
                "use_internal_links": use_links_in,
                "max_links":          max_links_in,
            }
            with st.spinner("Saving settings..."):
                save_settings(uid, payload)
                st.session_state.last_settings.update(payload)
            st.success("✅ Settings saved successfully!")

        # TEST BUTTONS
        st.markdown(f"<h3 style='color:{GOLD};font-weight:700;margin:32px 0 12px;'>🧪 Test Connections</h3>", unsafe_allow_html=True)
        st.markdown(f"<div class='guide-box'>Test each connection before generating to catch any issues early.</div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        cur = st.session_state.last_settings

        with col1:
            if st.button("🔬 Test Groq Key", use_container_width=True):
                try:
                    from generator import test_groq_key
                    with st.spinner("Testing Groq..."):
                        r = test_groq_key(cur.get("groq_key",""))
                    if r["success"]: st.success(r["message"])
                    else: st.error(r["message"])
                except Exception as e: st.error(f"Error: {e}")

        with col2:
            if st.button("🔬 Test GoAPI", use_container_width=True):
                try:
                    from generator import test_goapi_key
                    with st.spinner("Testing GoAPI..."):
                        r = test_goapi_key(cur.get("mj_key",""))
                    if r["success"]: st.success(r["message"])
                    else: st.error(r["message"])
                except Exception as e: st.error(f"Error: {e}")

        with col3:
            if st.button("🔬 Test WordPress", use_container_width=True):
                try:
                    from generator import test_wordpress
                    with st.spinner("Testing WordPress..."):
                        r = test_wordpress(cur.get("wp_url",""), cur.get("wp_password",""))
                    if r["success"]: st.success(r["message"])
                    else: st.error(r["message"])
                except Exception as e: st.error(f"Error: {e}")

        st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 3 — GENERATE
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[2]:
        st.markdown(f"<div style='padding:32px 40px;max-width:900px;'>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='color:{CREAM};font-weight:800;margin:0 0 8px;'>✍️ Generate Article</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#666;margin:0 0 24px;'>Enter a title, choose your options, and click Generate. The article is published to WordPress automatically.</p>", unsafe_allow_html=True)

        cur = st.session_state.last_settings

        # Missing settings check
        missing = []
        if not cur.get("groq_key"): missing.append("Groq API Key")
        if not cur.get("wp_url"):   missing.append("WordPress URL")
        if not cur.get("wp_password"): missing.append("WordPress Password")
        if not cur.get("article_prompt"): missing.append("Article Prompt")
        if missing:
            st.warning(f"⚠️ Please configure in Settings first: **{', '.join(missing)}**")

        title_in = st.text_input("📝 Article Title", placeholder="E.g. Easy Homemade Pasta Recipe")
        col1, col2 = st.columns([3,1])
        with col1:
            use_images_in = st.checkbox("🖼️ Generate Midjourney Images",
                value=bool(cur.get("mj_key","")),
                disabled=not bool(cur.get("mj_key","")),
                help="Requires GoAPI key in Settings")
        with col2:
            show_proc_in = st.checkbox("👁️ Show Process Log",
                help="See live logs. Hidden by default for clean UX.")

        # Categories
        st.markdown(f"<p style='color:{GOLD};font-size:13px;font-weight:600;margin:16px 0 4px;'>📂 WordPress Categories (optional)</p>", unsafe_allow_html=True)
        cat_col1, cat_col2 = st.columns([4,1])
        with cat_col2:
            if st.button("🔄 Load", use_container_width=True, help="Load categories from WordPress"):
                if cur.get("wp_url") and cur.get("wp_password"):
                    try:
                        from generator import fetch_wp_categories
                        with st.spinner("Loading..."):
                            cats = fetch_wp_categories(cur["wp_url"], cur["wp_password"])
                        st.session_state.wp_categories = cats
                        if cats: st.success(f"✅ {len(cats)} categories")
                        else: st.warning("None found")
                    except Exception as e: st.error(str(e))
                else:
                    st.warning("Add WordPress credentials in Settings first")

        with cat_col1:
            cat_opts = {c["name"]: c["id"] for c in st.session_state.wp_categories}
            sel_cats = st.multiselect("Select categories",
                options=list(cat_opts.keys()),
                help="Click Load → then select. Categories load fresh from WordPress each time.")
            cat_ids = [cat_opts[n] for n in sel_cats] if sel_cats else None

        # GENERATE BUTTON
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        gen_disabled = bool(missing)

        if st.button("🚀 Generate & Publish to WordPress", use_container_width=True,
                     disabled=gen_disabled, type="primary"):
            if not title_in.strip():
                st.error("Please enter an article title")
            else:
                st.session_state.gen_logs = []
                st.session_state.gen_result = None

                def log_fn(msg):
                    st.session_state.gen_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

                settings_payload = {
                    "groq_key":           cur.get("groq_key",""),
                    "goapi_key":          cur.get("mj_key",""),
                    "wp_url":             cur.get("wp_url",""),
                    "wp_password":        cur.get("wp_password",""),
                    "publish_status":     cur.get("publish_status","draft"),
                    "mj_template":        cur.get("mj_template",""),
                    "use_images":         use_images_in and bool(cur.get("mj_key","")),
                    "show_card":          cur.get("show_card", True),
                    "card_clickable":     cur.get("card_clickable", False),
                    "use_internal_links": cur.get("use_internal_links", False),
                    "max_links":          cur.get("max_links", 4),
                    "category_ids":       cat_ids,
                    "user_article_prompt": cur.get("article_prompt",""),
                    "user_html_structure": cur.get("html_structure",""),
                    "user_card_prompt":   cur.get("card_prompt",""),
                    "user_design": {
                        "main_color":   cur.get("main_color","#c9a84c"),
                        "accent_color": cur.get("accent_color","#ea580c"),
                        "font_family":  "inherit",
                    }
                }

                with st.spinner("⏳ Generating... This takes 2-5 minutes when images are enabled. Please wait."):
                    try:
                        from generator import run_full_pipeline
                        result = run_full_pipeline(title_in.strip(), settings_payload, log_fn=log_fn)
                        st.session_state.gen_result = result
                    except Exception as e:
                        result = {"success": False, "error": str(e)}
                        st.session_state.gen_result = result

                if result.get("success"):
                    post_url = result.get("post_url","")
                    st.success(f"🎉 Article published successfully!")
                    if post_url:
                        st.markdown(f"<a href='{post_url}' target='_blank' style='color:{GOLD};font-weight:700;'>🔗 View Article on WordPress →</a>", unsafe_allow_html=True)
                    # Save history
                    try:
                        hist = json.loads(sett.get("history","[]") or "[]")
                        hist.insert(0, {
                            "title": title_in.strip(),
                            "url":    post_url,
                            "status": result.get("status",""),
                            "images": result.get("image_count", 0),
                            "date":   datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
                        })
                        hist = hist[:50]
                        save_settings(uid, {"history": json.dumps(hist)})
                        st.session_state.last_settings["history"] = json.dumps(hist)
                    except: pass
                else:
                    st.error(f"❌ {result.get('error','Unknown error')}")

        # Process log
        if show_proc_in and st.session_state.gen_logs:
            st.markdown(f"<h4 style='color:{CREAM};margin:24px 0 8px;'>📋 Process Log</h4>", unsafe_allow_html=True)
            log_text = "\n".join(st.session_state.gen_logs)
            st.markdown(f"<div class='log-box'>{log_text}</div>", unsafe_allow_html=True)
        elif show_proc_in and not st.session_state.gen_logs:
            st.info("Process log will appear here during generation.")

        st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 4 — HISTORY
    # ══════════════════════════════════════════════════════════════════════════
    with tabs[3]:
        st.markdown(f"<div style='padding:32px 40px;'>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='color:{CREAM};font-weight:800;margin:0 0 8px;'>📊 Generation History</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#666;margin:0 0 24px;'>Your last 50 generated articles.</p>", unsafe_allow_html=True)

        try:
            hist = json.loads(sett.get("history","[]") or "[]")
        except: hist = []

        if not hist:
            st.markdown(f"""
<div style="background:{CARD};border:1px solid {BORDER};border-radius:14px;
            padding:40px;text-align:center;color:#555;">
  No articles generated yet.<br>Go to the <b style="color:{GOLD};">Generate</b> tab to publish your first article!
</div>""", unsafe_allow_html=True)
        else:
            for item in hist:
                st_color = GREEN if item.get("status") == "publish" else GOLD
                url = item.get("url","")
                link_html = f'<a href="{url}" target="_blank" style="color:{GOLD};font-size:12px;text-decoration:none;white-space:nowrap;">View Post →</a>' if url else ""
                st.markdown(f"""
<div style="background:{CARD};border:1px solid {BORDER};border-radius:12px;
            padding:16px 20px;margin-bottom:10px;display:flex;
            align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
  <div>
    <div style="color:{CREAM};font-weight:600;font-size:14px;">{item.get('title','')}</div>
    <div style="color:#555;font-size:12px;margin-top:4px;">
      {item.get('date','')} &nbsp;·&nbsp;
      <span style="color:{st_color};">{item.get('status','')}</span> &nbsp;·&nbsp;
      🖼️ {item.get('images',0)} images
    </div>
  </div>
  {link_html}
</div>""", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 5 — PINTEREST (PRO ONLY)
    # ══════════════════════════════════════════════════════════════════════════
    if is_pro and len(tabs) > 4:
        with tabs[4]:
            st.markdown(f"<div style='padding:32px 40px;max-width:900px;'>", unsafe_allow_html=True)
            st.markdown(f"""
<h2 style='color:{CREAM};font-weight:800;margin:0 0 8px;'>📌 Pinterest Publisher</h2>
<p style='color:#666;margin:0 0 32px;'>Auto-publish optimized pins to Pinterest after each WordPress article.</p>
""", unsafe_allow_html=True)

            with st.form("pinterest_form"):
                # Token
                st.markdown(f"<h3 style='color:{GOLD};font-weight:700;margin:0 0 4px;'>🔑 Pinterest Access Token</h3>", unsafe_allow_html=True)
                st.markdown(f"""<div class='guide-box'>
<b>How to get:</b><br>
1. Go to <a href="https://developers.pinterest.com/apps/" target="_blank" style="color:{GOLD};">developers.pinterest.com/apps</a><br>
2. Create an app → Go to "Access tokens"<br>
3. Enable scopes: <code>boards:read, pins:write, pins:read</code><br>
4. Generate token → paste below
                </div>""", unsafe_allow_html=True)
                pin_token_in = st.text_input("Pinterest Access Token",
                    value=sett.get("pinterest_token",""), type="password",
                    placeholder="pina_xxxxxxxxxx...")

                # Board
                st.markdown(f"<h3 style='color:{GOLD};font-weight:700;margin:24px 0 4px;'>📋 Pinterest Board</h3>", unsafe_allow_html=True)
                st.markdown(f"""<div class='guide-box'>
Save your token → click "Load My Boards" below (outside this form) → select your board.
The board loads fresh each time so new boards appear automatically.
                </div>""", unsafe_allow_html=True)
                pin_board_in = st.text_input("Board ID",
                    value=sett.get("pinterest_board",""),
                    placeholder="Will be filled when you select a board below",
                    help="Click Load My Boards after saving token")

                # Pinterest Prompt
                st.markdown(f"<h3 style='color:{GOLD};font-weight:700;margin:24px 0 4px;'>✍️ Pinterest Pin Prompt</h3>", unsafe_allow_html=True)
                st.markdown(f"""<div class='guide-box'>
Tell the AI how to write your pin title and description.<br>
<b>Example:</b> "Write in a casual inspiring tone. Focus on quick results. Target home cooks aged 25-45. Include 5 hashtags."<br>
The AI generates: pin title (max 100 chars), description (max 500 chars), alt text, and keywords.
                </div>""", unsafe_allow_html=True)
                pin_prompt_in = st.text_area("Pinterest Pin Prompt",
                    value=sett.get("pinterest_prompt",""), height=110,
                    placeholder="Write engaging pin descriptions for my food blog. Casual tone. Include 3-5 hashtags. Target home cooks.")
                token_warning(pin_prompt_in, "Pinterest Prompt")

                # Scheduler
                st.markdown(f"<h3 style='color:{GOLD};font-weight:700;margin:24px 0 4px;'>📅 Post Scheduler</h3>", unsafe_allow_html=True)
                st.markdown(f"""<div class='guide-box'>
Choose which days of the week and what time to auto-post pins.
The scheduler queues pins from articles generated on those days.
                </div>""", unsafe_allow_html=True)
                days_opts = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
                saved_days_str = sett.get("pinterest_schedule_days","")
                saved_days = [d for d in saved_days_str.split(",") if d in days_opts] if saved_days_str else []
                sched_days_in = st.multiselect("Post Days", days_opts, default=saved_days)

                col1, col2 = st.columns(2)
                with col1:
                    try:
                        t_val = datetime.strptime(sett.get("pinterest_schedule_time","09:00"), "%H:%M").time()
                    except: t_val = datetime.strptime("09:00", "%H:%M").time()
                    sched_time_in = st.time_input("Post Time", value=t_val)
                with col2:
                    tzs = ["UTC","US/Eastern","US/Central","US/Pacific","Europe/London","Europe/Paris","Asia/Dubai","Asia/Tokyo"]
                    tz_saved = sett.get("pinterest_schedule_timezone","UTC")
                    sched_tz_in = st.selectbox("Timezone", tzs,
                        index=tzs.index(tz_saved) if tz_saved in tzs else 0)

                pin_sub = st.form_submit_button("💾 Save Pinterest Settings", use_container_width=True)

            if pin_sub:
                pin_payload = {
                    "pinterest_token":              pin_token_in.strip(),
                    "pinterest_board":              pin_board_in.strip(),
                    "pinterest_prompt":             pin_prompt_in,
                    "pinterest_schedule_days":      ",".join(sched_days_in),
                    "pinterest_schedule_time":      sched_time_in.strftime("%H:%M"),
                    "pinterest_schedule_timezone":  sched_tz_in,
                }
                with st.spinner("Saving..."):
                    save_settings(uid, pin_payload)
                    st.session_state.last_settings.update(pin_payload)
                st.success("✅ Pinterest settings saved!")

            # Load Boards (outside form)
            st.markdown(f"<h3 style='color:{GOLD};font-weight:700;margin:24px 0 8px;'>📋 Load Boards from Pinterest</h3>", unsafe_allow_html=True)
            st.markdown(f"<div class='guide-box'>Click below to load all your Pinterest boards fresh. Select which board to post to.</div>", unsafe_allow_html=True)

            col1, col2 = st.columns([1,2])
            with col1:
                if st.button("🔄 Load My Boards", use_container_width=True):
                    token_now = st.session_state.last_settings.get("pinterest_token","")
                    if not token_now:
                        st.warning("Save your Pinterest token first")
                    else:
                        with st.spinner("Loading boards from Pinterest..."):
                            try:
                                resp = _req.get(
                                    "https://api.pinterest.com/v5/boards",
                                    headers={"Authorization": f"Bearer {token_now}"},
                                    params={"page_size": 100}, timeout=15
                                )
                                if resp.status_code == 200:
                                    boards = resp.json().get("items",[])
                                    st.session_state.pinterest_boards = [{"id":b["id"],"name":b["name"]} for b in boards]
                                    st.success(f"✅ {len(boards)} boards loaded")
                                else:
                                    st.error(f"❌ Pinterest API error {resp.status_code}: {resp.text[:200]}")
                            except Exception as e:
                                st.error(f"❌ {e}")

            if st.session_state.pinterest_boards:
                with col2:
                    board_map = {b["name"]: b["id"] for b in st.session_state.pinterest_boards}
                    sel_board_name = st.selectbox("Select Board", list(board_map.keys()))
                    if st.button("✓ Set as Active Board", use_container_width=True):
                        bid = board_map[sel_board_name]
                        save_settings(uid, {"pinterest_board": bid})
                        st.session_state.last_settings["pinterest_board"] = bid
                        st.success(f"✅ Active board: {sel_board_name}")

            # Pinterest Status
            st.markdown(f"<h3 style='color:{GOLD};font-weight:700;margin:24px 0 8px;'>📊 Pinterest Status</h3>", unsafe_allow_html=True)
            cp = st.session_state.last_settings
            statuses = [
                ("Token",    "✅ Token saved" if cp.get("pinterest_token") else "❌ No token saved"),
                ("Board",    f"✅ {cp.get('pinterest_board','')}" if cp.get("pinterest_board") else "❌ No board selected"),
                ("Prompt",   "✅ Prompt configured" if cp.get("pinterest_prompt") else "⚠️ No prompt (will use defaults)"),
                ("Schedule", f"📅 {cp.get('pinterest_schedule_days','')} at {cp.get('pinterest_schedule_time','')} {cp.get('pinterest_schedule_timezone','')}" if cp.get("pinterest_schedule_days") else "⬜ No schedule set"),
            ]
            status_cols = st.columns(2)
            for i, (label, value) in enumerate(statuses):
                col = status_cols[i % 2]
                color = GREEN if value.startswith("✅") else (GOLD if value.startswith("⚠️") or value.startswith("📅") else RED if value.startswith("❌") else "#555")
                with col:
                    st.markdown(f"""
<div class="metric-card">
  <h4>{label}</h4>
  <p style="color:{color};font-size:13px;font-weight:600;margin:0;">{value}</p>
</div>""", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  ROUTER — reads st.query_params, no iframe needed
# ═══════════════════════════════════════════════════════════════════════════════
page = st.session_state.page

if page == "home":
    page_home()
elif page == "login":
    page_login()
elif page == "signup":
    page_signup()
elif page == "docs":
    page_docs()
elif page == "dashboard":
    if st.session_state.user:
        page_dashboard()
    else:
        go("login")
else:
    go("home")