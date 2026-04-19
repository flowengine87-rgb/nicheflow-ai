# -*- coding: utf-8 -*-
"""
NicheFlow AI — app.py
All navigation via st.session_state + st.button — no iframe navigation hacks.
"""

import streamlit as st
import streamlit.components.v1 as components
import hashlib, time
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
st.set_page_config(page_title="NicheFlow AI", page_icon="✦", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700;9..144,800;9..144,900&family=Outfit:wght@300;400;500;600;700&display=swap');
:root{--cream:#faf6ef;--gold:#c9892a;--gold2:#e8a83e;--dark:#0f0d09;--text:#1a1510;--text2:#5a5040;--text3:#8a7a60;--border:#dfd4bc;}
#MainMenu,footer,header,[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],[data-testid="collapsedControl"],
section[data-testid="stSidebar"]{display:none!important;}
.block-container{padding:0!important;max-width:100%!important;}
.stApp{background:var(--cream)!important;}
iframe{border:none!important;display:block;}
.stButton>button{font-family:'Outfit',sans-serif!important;transition:all .2s!important;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
for k,v in {"page":"home","dash_tab":"overview","user_id":None,"user_email":None,
             "user_plan":"basic","settings":{},"gen_logs":[],"gen_results":[],
             "wp_categories":[],"auth_error":"","auth_success":"","save_ok":False}.items():
    if k not in st.session_state: st.session_state[k] = v

def go(page):
    st.session_state.page = page
    st.session_state.auth_error = ""
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  DB HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

def db_create_user(email, password):
    if not DB_OK: return {"success":False,"error":"Database not connected"}
    try:
        if supabase.table("users").select("id").eq("email",email).execute().data:
            return {"success":False,"error":"Email already registered"}
        r = supabase.table("users").insert({"email":email,"password_hash":hash_pw(password),"plan":"basic"}).execute()
        uid = r.data[0]["id"]
        supabase.table("user_settings").insert({"user_id":uid}).execute()
        return {"success":True,"user_id":uid}
    except Exception as e: return {"success":False,"error":str(e)}

def db_login(email, password):
    if not DB_OK: return {"success":False,"error":"Database not connected"}
    try:
        r = supabase.table("users").select("*").eq("email",email).eq("password_hash",hash_pw(password)).execute()
        if not r.data: return {"success":False,"error":"Invalid email or password"}
        u = r.data[0]
        return {"success":True,"user_id":u["id"],"email":u["email"],"plan":u.get("plan","basic")}
    except Exception as e: return {"success":False,"error":str(e)}

def db_load(uid):
    if not DB_OK or not uid: return {}
    try:
        r = supabase.table("user_settings").select("*").eq("user_id",uid).execute()
        if r.data:
            row = r.data[0]
            return {k:row[k] for k in row if row[k] is not None and k not in ("id","user_id")}
        return {}
    except: return {}

def db_save(uid, s):
    if not DB_OK or not uid: return False
    try:
        payload = {"user_id":uid,**s,"updated_at":datetime.utcnow().isoformat()}
        if supabase.table("user_settings").select("id").eq("user_id",uid).execute().data:
            supabase.table("user_settings").update(payload).eq("user_id",uid).execute()
        else:
            supabase.table("user_settings").insert(payload).execute()
        return True
    except: return False

def db_inc(uid, field, n=1):
    if not DB_OK or not uid: return
    try:
        cur = db_load(uid).get(field,0) or 0
        db_save(uid,{field:int(cur)+n})
    except: pass

def do_login(email, password):
    r = db_login(email.strip().lower(), password)
    if r["success"]:
        st.session_state.update({"user_id":r["user_id"],"user_email":r["email"],"user_plan":r["plan"],
                                   "settings":db_load(r["user_id"]),"page":"dashboard","dash_tab":"overview","auth_error":""})
    else: st.session_state.auth_error = r["error"]

def do_signup(email, password, confirm):
    if password != confirm: st.session_state.auth_error = "Passwords do not match"; return
    if len(password) < 6: st.session_state.auth_error = "Password must be at least 6 characters"; return
    r = db_create_user(email.strip().lower(), password)
    if r["success"]:
        st.session_state.auth_success = "Account created! Sign in now."
        st.session_state.page = "login"; st.session_state.auth_error = ""
    else: st.session_state.auth_error = r["error"]

def do_logout():
    st.session_state.update({"user_id":None,"user_email":None,"user_plan":"basic","settings":{},"page":"home"})

def save_db():
    db_save(st.session_state.user_id, st.session_state.settings)
    st.session_state.save_ok = True

# ─────────────────────────────────────────────────────────────────────────────
#  SHARED HTML/CSS for visual sections rendered in iframes (display only)
# ─────────────────────────────────────────────────────────────────────────────
CSS = """<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Outfit',sans-serif;background:#faf6ef;color:#1a1510;}
.hero{background:linear-gradient(160deg,#fdfaf4 0%,#f5e8cc 55%,#ecdbb8 100%);
      padding:80px 5vw 70px;text-align:center;position:relative;overflow:hidden;}
.hero::before{content:'';position:absolute;top:-180px;left:-150px;width:500px;height:500px;
              background:radial-gradient(circle,rgba(201,137,42,.15) 0%,transparent 65%);border-radius:50%;}
.hero::after{content:'';position:absolute;bottom:-120px;right:-120px;width:420px;height:420px;
             background:radial-gradient(circle,rgba(201,137,42,.1) 0%,transparent 65%);border-radius:50%;}
.badge{display:inline-flex;align-items:center;background:rgba(255,255,255,.7);border:1px solid rgba(201,137,42,.35);
       color:#8a6020;padding:7px 18px;border-radius:100px;font-size:12.5px;font-weight:600;margin-bottom:28px;position:relative;z-index:1;}
h1{font-family:'Fraunces',serif;font-size:clamp(42px,7vw,88px);font-weight:900;line-height:1.03;
   color:#1a1510;margin-bottom:22px;position:relative;z-index:1;}
h1 em{font-style:normal;color:#c9892a;}
.sub{font-size:clamp(15px,1.6vw,18px);color:#5a5040;max-width:560px;margin:0 auto 16px;line-height:1.78;position:relative;z-index:1;}
.stats{display:flex;flex-wrap:wrap;justify-content:center;gap:clamp(20px,4vw,60px);
       margin-top:52px;padding-top:44px;border-top:1px solid rgba(0,0,0,.09);position:relative;z-index:1;}
.sn{font-family:'Fraunces',serif;font-size:clamp(30px,4vw,46px);font-weight:800;color:#c9892a;}
.sl{font-size:13px;color:#8a7a60;margin-top:4px;font-weight:500;}
.sec{padding:clamp(52px,6vw,96px) clamp(20px,5vw,88px);background:#faf6ef;}
.sec-alt{background:#f2e8d4;padding:clamp(52px,6vw,96px) clamp(20px,5vw,88px);}
.sec-dark{background:#0f0d09;padding:clamp(52px,6vw,96px) clamp(20px,5vw,88px);}
.center{text-align:center;}
.eyebrow{font-size:11px;font-weight:700;color:#c9892a;text-transform:uppercase;letter-spacing:3.5px;margin-bottom:14px;display:block;}
.eyebrow-l{color:rgba(201,137,42,.9)!important;}
.title{font-family:'Fraunces',serif;font-size:clamp(28px,4vw,50px);font-weight:800;line-height:1.12;color:#1a1510;margin-bottom:14px;}
.title-l{font-family:'Fraunces',serif;font-size:clamp(28px,4vw,50px);font-weight:800;line-height:1.12;color:#fdf6e8;margin-bottom:14px;}
.desc{font-size:clamp(14px,1.3vw,16px);color:#5a5040;line-height:1.72;margin-bottom:clamp(30px,4vw,56px);max-width:540px;}
.desc-l{font-size:clamp(14px,1.3vw,16px);color:rgba(253,246,232,.5);line-height:1.72;margin-bottom:clamp(30px,4vw,56px);max-width:540px;}
.center .desc,.center .desc-l{margin-left:auto;margin-right:auto;}
.feat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;}
@media(max-width:860px){.feat-grid{grid-template-columns:1fr 1fr;}}
@media(max-width:520px){.feat-grid{grid-template-columns:1fr;}}
.fc{background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:clamp(18px,2.5vw,30px);}
.fi{width:44px;height:44px;background:#fff8ec;border:1px solid rgba(201,137,42,.2);border-radius:12px;
    display:flex;align-items:center;justify-content:center;font-size:19px;margin-bottom:13px;}
.fc h3{font-size:14.5px;font-weight:700;color:#1a1510;margin-bottom:6px;}
.fc p{font-size:13px;color:#8a7a60;line-height:1.74;}
.pg{display:grid;grid-template-columns:1fr 1fr;gap:20px;max-width:800px;margin:0 auto;}
@media(max-width:600px){.pg{grid-template-columns:1fr;}}
.pc{background:#fff;border:2px solid #dfd4bc;border-radius:24px;padding:clamp(28px,3.5vw,44px) clamp(22px,3vw,36px);text-align:center;}
.pc.pro{background:linear-gradient(158deg,#211808,#0f0d09);border-color:rgba(201,137,42,.55);}
.pl{font-size:11px;font-weight:700;color:#8a7a60;text-transform:uppercase;letter-spacing:2.5px;margin-bottom:14px;}
.pc.pro .pl{color:rgba(232,168,62,.75);}
.pp{font-family:'Fraunces',serif;font-size:clamp(46px,6vw,66px);font-weight:900;color:#1a1510;line-height:1;}
.pc.pro .pp{color:#fff;}
.per{font-size:13px;color:#8a7a60;margin-bottom:22px;margin-top:4px;}
.pc.pro .per{color:rgba(253,246,232,.4);}
.pf{font-size:13px;color:#5a5040;padding:9px 0;border-bottom:1px solid #f0e8d8;text-align:left;}
.pc.pro .pf{color:rgba(253,246,232,.8);border-bottom-color:rgba(255,255,255,.07);}
.pf.no{opacity:.45;}
.sg{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;}
@media(max-width:860px){.sg{grid-template-columns:1fr 1fr;}}
.sc{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:18px;padding:clamp(20px,2.5vw,30px);}
.sn2{font-family:'Fraunces',serif;font-size:clamp(40px,5vw,56px);font-weight:900;color:#c9892a;line-height:1;margin-bottom:13px;}
.sc h4{font-size:15px;font-weight:700;color:#fdf6e8;margin-bottom:8px;}
.sc p{font-size:13px;color:rgba(253,246,232,.5);line-height:1.72;}
.cta{background:#0f0d09;border-radius:22px;padding:clamp(44px,5.5vw,80px) clamp(22px,4.5vw,68px);
     text-align:center;margin:0 clamp(10px,3vw,48px) clamp(44px,5vw,68px);}
footer{text-align:center;padding:clamp(30px,4vw,48px);border-top:1px solid #dfd4bc;background:#faf6ef;}
.fl{font-family:'Fraunces',serif;font-size:20px;font-weight:800;color:#1a1510;margin-bottom:8px;}
</style>"""

# ─────────────────────────────────────────────────────────────────────────────
#  HOME PAGE
# ─────────────────────────────────────────────────────────────────────────────
def render_home():
    # ── NAV (real Streamlit buttons — always clickable) ──
    st.markdown("""
    <div style="background:rgba(250,246,239,0.97);border-bottom:1px solid #dfd4bc;padding:4px 0;">
    </div>""", unsafe_allow_html=True)

    c1,c2,c3,c4,c5,c6 = st.columns([2.2,0.7,0.7,0.9,1,1])
    with c1:
        st.markdown("<div style='padding:14px 0 0 24px;font-family:\"Fraunces\",serif;font-size:20px;font-weight:800;color:#1a1510;'>✦ <em style=\"color:#c9892a;font-style:normal;\">Niche</em>Flow AI</div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if st.button("Pricing", key="hn_price"): pass
    with c4:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if st.button("How It Works", key="hn_how"): pass
    with c5:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if st.button("Documentation", key="hn_docs"): go("docs")
    with c6:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if st.button("Sign In →", key="hn_login"): go("login")

    st.markdown('<hr style="margin:0;border:none;border-top:1px solid #dfd4bc;">', unsafe_allow_html=True)

    # ── HERO (display only iframe) ──
    components.html(CSS + """
<section class="hero">
  <div class="badge">✦ AI-Powered Content Platform</div>
  <h1>Write Less.<br>Publish More.<br><em>Grow on Autopilot.</em></h1>
  <p class="sub">NicheFlow AI writes full SEO blog articles, generates stunning Midjourney images, publishes to WordPress, and pins to Pinterest — completely automatically. You paste a title. We handle everything.</p>
  <div class="stats">
    <div><div class="sn">3×</div><div class="sl">Faster Publishing</div></div>
    <div><div class="sn">100%</div><div class="sl">Autopilot Content</div></div>
    <div><div class="sn">4</div><div class="sl">Images Per Article</div></div>
    <div><div class="sn">2</div><div class="sl">Platforms at Once</div></div>
  </div>
</section>""", height=500)

    # ── HERO BUTTONS ──
    c1,c2,c3 = st.columns([1.8,1,1.8])
    with c2:
        if st.button("🚀  Get Started Free →", key="hero_start", use_container_width=True): go("signup")
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    c1,c2,c3 = st.columns([1.8,1,1.8])
    with c2:
        if st.button("View Documentation", key="hero_docs2", use_container_width=True): go("docs")

    # ── FEATURES ──
    components.html(CSS + """
<section class="sec">
  <div class="center">
    <span class="eyebrow">Features</span>
    <h2 class="title">Everything Your Blog Needs</h2>
    <p class="desc">One platform handles your entire content pipeline — from idea to published post.</p>
  </div>
  <div class="feat-grid">
    <div class="fc"><div class="fi">✍️</div><h3>AI Article Writer</h3><p>Groq AI writes full SEO articles. Your prompt, your niche, your voice — zero defaults.</p></div>
    <div class="fc"><div class="fi">🎨</div><h3>Midjourney Images</h3><p>4 stunning images auto-generated per article, uploaded directly to your WordPress library.</p></div>
    <div class="fc"><div class="fi">🌐</div><h3>WordPress Publisher</h3><p>Articles publish with images and full formatting automatically. No copy-pasting ever.</p></div>
    <div class="fc"><div class="fi">📌</div><h3>Pinterest Auto-Post</h3><p>Post optimized Pins using the featured image after every publish. Pro plan only.</p></div>
    <div class="fc"><div class="fi">🃏</div><h3>Custom Niche Cards</h3><p>Styled info cards for every article — recipe, travel, health, or any niche you want.</p></div>
    <div class="fc"><div class="fi">🎨</div><h3>Design Studio</h3><p>Control article colors, fonts, and HTML structure. Every article matches your brand.</p></div>
  </div>
</section>""", height=520)

    # ── PRICING ──
    components.html(CSS + """
<section class="sec-alt">
  <div class="center">
    <span class="eyebrow">Pricing</span>
    <h2 class="title">Simple, Honest Pricing</h2>
    <p class="desc">No hidden fees. No shared quotas. Cancel anytime.</p>
  </div>
  <div class="pg">
    <div class="pc">
      <div class="pl">Basic</div>
      <div class="pp">$30</div>
      <div class="per">per month</div>
      <div class="pf">✅ AI Article Generation</div>
      <div class="pf">✅ Midjourney Images (4/article)</div>
      <div class="pf">✅ WordPress Auto-Publish</div>
      <div class="pf">✅ Custom Prompts &amp; Design</div>
      <div class="pf">✅ Draft or Live Publishing</div>
      <div class="pf no">✗ Pinterest Auto-Post</div>
    </div>
    <div class="pc pro">
      <div class="pl">Pro · Most Popular</div>
      <div class="pp">$40</div>
      <div class="per">per month</div>
      <div class="pf">✅ Everything in Basic</div>
      <div class="pf">✅ Pinterest Auto-Post</div>
      <div class="pf">✅ Pinterest Keyword Optimizer</div>
      <div class="pf">✅ Custom Pinterest Prompt</div>
      <div class="pf">✅ Pinterest Post Scheduler</div>
      <div class="pf">✅ Priority Support</div>
    </div>
  </div>
</section>""", height=560)

    c1,c2,c3 = st.columns([1.8,1,1.8])
    with c2:
        if st.button("Get Started — Basic $30/mo", key="price_cta", use_container_width=True): go("signup")
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    c1,c2,c3 = st.columns([1.8,1,1.8])
    with c2:
        if st.button("Get Pro — $40/mo", key="pro_cta", use_container_width=True): go("signup")

    # ── HOW IT WORKS ──
    components.html(CSS + """
<section class="sec-dark">
  <div class="center">
    <span class="eyebrow eyebrow-l">How It Works</span>
    <h2 class="title-l">From Zero to Published in Minutes</h2>
    <p class="desc-l" style="margin:0 auto 48px;">No technical skills needed. If you can paste a title, you can use NicheFlow AI.</p>
  </div>
  <div class="sg">
    <div class="sc"><div class="sn2">01</div><h4>Sign Up &amp; Choose Plan</h4><p>Create your account and pick Basic or Pro.</p></div>
    <div class="sc"><div class="sn2">02</div><h4>Add Your Credentials</h4><p>Enter your Groq API key, Midjourney key, and WordPress app password once.</p></div>
    <div class="sc"><div class="sn2">03</div><h4>Write Your Prompts</h4><p>Customize article and card prompts to match your niche voice and audience.</p></div>
    <div class="sc"><div class="sn2">04</div><h4>Paste Titles &amp; Go</h4><p>Drop in article titles and hit Generate. NicheFlow writes, designs, and publishes.</p></div>
  </div>
</section>""", height=360)

    # ── CTA + FOOTER ──
    components.html(CSS + """
<section class="sec">
  <div class="cta">
    <span class="eyebrow eyebrow-l">Start Today</span>
    <h2 class="title" style="color:#fdf6e8;">Ready to Automate Your Content?</h2>
    <p class="desc" style="color:rgba(253,246,232,.5);margin:0 auto 28px;">Join bloggers who publish more, stress less, and grow faster.</p>
  </div>
</section>
<footer>
  <div class="fl">✦ NicheFlow AI</div>
  <p style="font-size:13px;color:#8a7a60;">AI-powered blog &amp; Pinterest content generator</p>
  <p style="font-size:12px;color:#b0a080;margin-top:10px;">© 2026 NicheFlow AI · All rights reserved</p>
</footer>""", height=380)

    c1,c2,c3 = st.columns([1.8,1,1.8])
    with c2:
        if st.button("🚀  Start Free Today", key="cta_final", use_container_width=True): go("signup")


# ─────────────────────────────────────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────────────────────────────────────
def render_login():
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    if st.button("← Back to Home", key="lb"): go("home")

    col = st.columns([1,1.2,1])[1]
    with col:
        st.markdown("""
        <div style="background:#fff;border:1px solid #dfd4bc;border-radius:24px;padding:42px 38px 32px;
             box-shadow:0 12px 56px rgba(0,0,0,.08);margin-top:24px;">
          <div style="font-family:'Fraunces',serif;font-size:19px;font-weight:800;color:#1a1510;
               text-align:center;margin-bottom:22px;">✦ <em style='color:#c9892a;font-style:normal;'>NicheFlow</em> AI</div>
          <h2 style="font-family:'Fraunces',serif;font-size:27px;font-weight:800;color:#1a1510;
               text-align:center;margin:0 0 5px;">Welcome Back</h2>
          <p style="font-size:14px;color:#8a7a60;text-align:center;margin:0 0 24px;">Sign in to your account</p>
        </div>""", unsafe_allow_html=True)

        if st.session_state.auth_error: st.error(st.session_state.auth_error)
        if st.session_state.auth_success:
            st.success(st.session_state.auth_success)
            st.session_state.auth_success = ""

        email = st.text_input("Email Address", placeholder="your@email.com", key="le")
        password = st.text_input("Password", type="password", placeholder="Your password", key="lp")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("Sign In →", type="primary", use_container_width=True, key="ls"):
            if email and password: do_login(email, password); st.rerun()
            else: st.session_state.auth_error = "Please fill in both fields"; st.rerun()
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if st.button("Don't have an account? Sign Up Free", use_container_width=True, key="l2s"):
            go("signup")


# ─────────────────────────────────────────────────────────────────────────────
#  SIGNUP
# ─────────────────────────────────────────────────────────────────────────────
def render_signup():
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    if st.button("← Back to Home", key="sb"): go("home")

    col = st.columns([1,1.2,1])[1]
    with col:
        st.markdown("""
        <div style="background:#fff;border:1px solid #dfd4bc;border-radius:24px;padding:42px 38px 32px;
             box-shadow:0 12px 56px rgba(0,0,0,.08);margin-top:24px;">
          <div style="font-family:'Fraunces',serif;font-size:19px;font-weight:800;color:#1a1510;
               text-align:center;margin-bottom:22px;">✦ <em style='color:#c9892a;font-style:normal;'>NicheFlow</em> AI</div>
          <h2 style="font-family:'Fraunces',serif;font-size:27px;font-weight:800;color:#1a1510;
               text-align:center;margin:0 0 5px;">Create Account</h2>
          <p style="font-size:14px;color:#8a7a60;text-align:center;margin:0 0 24px;">Start automating your content today</p>
        </div>""", unsafe_allow_html=True)

        if st.session_state.auth_error: st.error(st.session_state.auth_error)

        email   = st.text_input("Email Address", placeholder="your@email.com", key="se")
        password= st.text_input("Password", type="password", placeholder="At least 6 characters", key="sp")
        confirm = st.text_input("Confirm Password", type="password", placeholder="Repeat password", key="sc")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("Create Account →", type="primary", use_container_width=True, key="ss"):
            if email and password and confirm: do_signup(email, password, confirm); st.rerun()
            else: st.session_state.auth_error = "Please fill in all fields"; st.rerun()
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if st.button("Already have an account? Sign In", use_container_width=True, key="s2l"):
            go("login")


# ─────────────────────────────────────────────────────────────────────────────
#  DOCS
# ─────────────────────────────────────────────────────────────────────────────
def render_docs():
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    if st.button("← Back to Home", key="db_back"): go("home")

    components.html(CSS + """
<style>
.dw{max-width:860px;margin:0 auto;padding:28px 20px 72px;}
.ds{background:#fff;border:1px solid #dfd4bc;border-radius:16px;padding:22px 26px;margin-bottom:12px;}
.ds h2{font-family:'Fraunces',serif;font-size:17px;font-weight:800;color:#1a1510;
       margin:0 0 12px;padding-bottom:10px;border-bottom:1px solid #f0e6d4;}
.ds h3{font-size:13px;font-weight:700;color:#1a1510;margin:13px 0 5px;}
.ds p{font-size:13px;color:#5a5040;line-height:1.78;margin-bottom:7px;}
.ds ol,.ds ul{padding-left:17px;margin:5px 0 7px;}
.ds li{font-size:13px;color:#5a5040;line-height:1.78;margin-bottom:3px;}
.dn{background:#fff8ec;border-left:3px solid #c9892a;border-radius:0 7px 7px 0;
    padding:8px 12px;margin:7px 0;font-size:12.5px;color:#7a5820;line-height:1.65;}
.de{background:#f8f3ea;border:1px solid #e4d8c4;border-radius:8px;padding:11px 14px;
    margin:7px 0;font-size:12.5px;color:#5a4a34;font-style:italic;line-height:1.68;}
.badge2{font-size:11px;font-weight:700;color:#c9892a;background:#fff8ec;padding:2px 9px;border-radius:100px;margin-left:7px;}
</style>
<div class="dw">
<span style="font-size:11px;font-weight:700;color:#c9892a;text-transform:uppercase;letter-spacing:3px;">Documentation</span>
<h1 style="font-family:'Fraunces',serif;font-size:clamp(24px,4vw,40px);font-weight:800;color:#1a1510;margin:7px 0 26px;">Setup Guide</h1>
<div class="ds"><h2>1. Get Your Groq API Key (Free)</h2>
<ol><li>Go to <strong>console.groq.com</strong> — create a free account</li>
<li>Click <strong>API Keys</strong> in the sidebar</li>
<li>Click <strong>Create API Key</strong> — name it "NicheFlow"</li>
<li>Copy the key — starts with <strong>gsk_</strong></li>
<li>Paste in <strong>Settings → Groq API Key</strong></li></ol>
<div class="dn">Free tier: 14,400 requests/day — more than enough for daily publishing.</div></div>
<div class="ds"><h2>2. Get Your Midjourney API Key</h2>
<ol><li>Go to <strong>goapi.ai</strong> — create an account</li>
<li>Choose pay-as-you-go</li>
<li>Go to <strong>Dashboard → API Keys</strong> — copy your key</li>
<li>Paste in <strong>Settings → Midjourney API Key</strong></li></ol>
<div class="dn">A few cents per image. 4 images per article.</div></div>
<div class="ds"><h2>3. Connect Your WordPress Site</h2>
<ol><li>Log in to your <strong>WordPress Dashboard</strong></li>
<li>Go to <strong>Users → Your Profile</strong></li>
<li>Scroll to <strong>Application Passwords</strong></li>
<li>Name it <strong>NicheFlow AI</strong> → click <strong>Add New</strong></li>
<li>Copy the password (format: xxxx xxxx xxxx xxxx)</li>
<li>Settings: URL = <strong>https://yoursite.com</strong></li>
<li>Password = <strong>YourUsername:xxxx xxxx xxxx xxxx</strong></li></ol>
<div class="dn">URL must include https:// — no trailing slash.</div></div>
<div class="ds"><h2>4. Set Up Pinterest <span class="badge2">Pro Plan</span></h2>
<ol><li>Go to <strong>developers.pinterest.com</strong></li>
<li>Create app — enable <strong>boards:read</strong> and <strong>pins:write</strong></li>
<li>Generate a <strong>User Access Token</strong></li>
<li>Find your <strong>Board ID</strong> from the board URL</li>
<li>Paste both into the Pinterest tab</li></ol></div>
<div class="ds"><h2>5. Write a Great Article Prompt</h2>
<p>Your prompt tells the AI exactly how to write for your niche. <strong>No defaults — your rules.</strong></p>
<h3>Travel Example</h3>
<div class="de">Write an inspiring travel guide in second person. Open with a vivid sensory scene. Cover top 5 attractions, local food, best time to visit, budget, and 5 practical tips. Target budget adventurers 25-40. 1200-1500 words.</div>
<h3>Recipe Example</h3>
<div class="de">Write a warm personal recipe article in first person. Open with a nostalgic story. Include "Why You'll Love This", 6 tips, variations, and 3 FAQs. Friendly tone for home cooks. 1200 words.</div>
<div class="dn">⚠️ Keep prompts under 2000 tokens to avoid Groq rate limits.</div></div>
<div class="ds"><h2>6. Best Practices</h2>
<ul><li><strong>Use descriptive titles</strong> — "Easy Creamy Tuscan Chicken" beats "Chicken Recipe"</li>
<li><strong>Set 5-10 second delay</strong> between articles during bulk runs</li>
<li><strong>Start with Draft</strong> to review before going live</li>
<li><strong>Test with one article first</strong> before running a batch</li>
<li><strong>Keep API keys private</strong> — never share them</li></ul></div>
</div>""", height=2600, scrolling=True)


# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def stat_card(title, value, icon):
    st.markdown(f"""<div style="background:#fff;border:1px solid #dfd4bc;border-radius:14px;padding:20px;text-align:center;">
      <div style="font-size:22px;margin-bottom:8px;">{icon}</div>
      <div style="font-family:'Fraunces',serif;font-size:32px;font-weight:800;color:#c9892a;line-height:1;">{value}</div>
      <div style="font-size:11.5px;color:#8a7a60;margin-top:4px;">{title}</div>
    </div>""", unsafe_allow_html=True)

def sec_hdr(title, sub=""):
    st.markdown(f"""<div style="padding:20px 0 16px;border-bottom:1px solid #dfd4bc;margin-bottom:22px;">
      <h1 style="font-family:'Fraunces',serif;font-size:22px;font-weight:800;color:#1a1510;margin:0;">{title}</h1>
      {f'<p style="font-size:13px;color:#8a7a60;margin:4px 0 0;">{sub}</p>' if sub else ''}
    </div>""", unsafe_allow_html=True)

def ibox(msg): st.markdown(f'<div style="background:#fff8ec;border-left:4px solid #c9892a;border-radius:0 8px 8px 0;padding:10px 14px;font-size:13px;color:#7a5820;margin-bottom:12px;">{msg}</div>', unsafe_allow_html=True)
def sbox(msg): st.markdown(f'<div style="background:#f0faf4;border:1px solid #a4d8b8;color:#1a6e38;border-radius:9px;padding:10px 14px;font-size:13px;margin-bottom:12px;">✅ {msg}</div>', unsafe_allow_html=True)
def ebox(msg): st.markdown(f'<div style="background:#fff0f0;border:1px solid #ffd0d0;color:#c03030;border-radius:9px;padding:10px 14px;font-size:13px;margin-bottom:12px;">❌ {msg}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
def render_sidebar():
    s = st.session_state
    pc = "#e8a83e" if s.user_plan=="pro" else "rgba(253,246,232,.4)"
    pl = "Pro Plan · $40/mo" if s.user_plan=="pro" else "Basic Plan · $30/mo"
    with st.sidebar:
        st.markdown(f"""
        <style>
        section[data-testid="stSidebar"]{{display:flex!important;}}
        [data-testid="stSidebarContent"]{{background:#0f0d09!important;padding:0!important;}}
        </style>
        <div style="padding:20px 20px 15px;font-family:'Fraunces',serif;font-size:18px;font-weight:800;
             color:#fdf6e8;border-bottom:1px solid rgba(255,255,255,.07);">
          ✦ <em style="color:#c9892a;font-style:normal;">Niche</em>Flow AI</div>
        <div style="padding:12px 20px;border-bottom:1px solid rgba(255,255,255,.07);">
          <div style="font-size:13px;font-weight:600;color:#fdf6e8;">{s.user_email or 'User'}</div>
          <div style="font-size:11px;color:{pc};margin-top:2px;">{pl}</div>
        </div><div style="height:8px;"></div>""", unsafe_allow_html=True)

        for key, label in [("overview","📊 Overview"),("generate","✍️ Generate"),("settings","⚙️ Settings"),
                            ("prompts","📝 Prompts"),("design","🎨 Design Studio"),("pinterest","📌 Pinterest"),
                            ("billing","💳 Billing"),("docs","📖 Documentation")]:
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                s.dash_tab = key; st.rerun()

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if st.button("🚪 Sign Out", use_container_width=True, key="nav_out"):
            do_logout(); st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD TABS
# ─────────────────────────────────────────────────────────────────────────────
def tab_overview():
    sec_hdr("Overview","Your NicheFlow AI dashboard")
    s = st.session_state.settings
    c1,c2,c3,c4 = st.columns(4)
    with c1: stat_card("Articles Generated",s.get("articles_generated",0),"✍️")
    with c2: stat_card("Images Created",s.get("images_created",0),"🎨")
    with c3: stat_card("Posts Published",s.get("posts_published",0),"🌐")
    with c4: stat_card("Pins Posted",s.get("pins_posted",0),"📌")
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("""<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:22px;">
          <h3 style="font-size:14px;font-weight:700;color:#1a1510;margin:0 0 12px;padding-bottom:10px;border-bottom:1px solid #f0e6d4;">🚀 Quick Start</h3>
          <p style="font-size:13.5px;color:#5a5040;line-height:2.1;">1. Add API keys in <strong>Settings</strong><br>2. Write prompts in <strong>Prompts</strong><br>3. Style in <strong>Design Studio</strong><br>4. Go to <strong>Generate</strong> and paste titles</p>
        </div>""", unsafe_allow_html=True)
    with c2:
        plan = st.session_state.user_plan
        st.markdown(f"""<div style="background:linear-gradient(135deg,#1c1810,#0f0d09);border:1px solid rgba(201,137,42,.3);border-radius:18px;padding:22px;">
          <h3 style="font-size:14px;font-weight:700;color:#e8a83e;margin:0 0 10px;">{'⭐ Pro Plan' if plan=='pro' else '📦 Basic Plan'}</h3>
          <p style="font-size:13px;color:rgba(253,246,232,.6);line-height:1.7;">{'All features unlocked including Pinterest Auto-Post.' if plan=='pro' else 'Upgrade to Pro ($40/mo) to unlock Pinterest, Scheduler, and priority support.'}</p>
        </div>""", unsafe_allow_html=True)

def tab_settings():
    sec_hdr("Settings","API credentials and publishing preferences")
    s = st.session_state.settings
    if st.session_state.save_ok: sbox("Settings saved!"); st.session_state.save_ok = False
    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:22px;">', unsafe_allow_html=True)
        st.markdown('<h3 style="font-size:14px;font-weight:700;color:#1a1510;margin:0 0 15px;padding-bottom:10px;border-bottom:1px solid #f0e6d4;">🔑 API Credentials</h3>', unsafe_allow_html=True)
        groq_key = st.text_input("Groq API Key", value=s.get("groq_key",""), type="password", placeholder="gsk_...")
        a1,a2 = st.columns([1,2])
        with a1:
            if st.button("Test Groq",key="tg"):
                st.session_state["groq_test"] = test_groq_key(groq_key) if (GEN_OK and groq_key) else {"success":False,"message":"Enter key first"}
        with a2:
            if "groq_test" in st.session_state:
                r=st.session_state.groq_test; st.markdown(f'<div style="font-size:12px;padding:6px 0;color:{"#1a6e38" if r["success"] else "#c03030"};">{r["message"]}</div>',unsafe_allow_html=True)
        goapi_key = st.text_input("Midjourney API Key", value=s.get("mj_key",""), type="password", placeholder="Your GoAPI key")
        b1,b2 = st.columns([1,2])
        with b1:
            if st.button("Test GoAPI",key="tga"):
                st.session_state["goapi_test"] = test_goapi_key(goapi_key) if (GEN_OK and goapi_key) else {"success":False,"message":"Enter key first"}
        with b2:
            if "goapi_test" in st.session_state:
                r=st.session_state.goapi_test; st.markdown(f'<div style="font-size:12px;padding:6px 0;color:{"#1a6e38" if r["success"] else "#c03030"};">{r["message"]}</div>',unsafe_allow_html=True)
        wp_url = st.text_input("WordPress URL", value=s.get("wp_url",""), placeholder="https://yoursite.com")
        wp_pass = st.text_input("WordPress App Password", value=s.get("wp_password",""), type="password", placeholder="Username:xxxx xxxx xxxx xxxx")
        c1a,c1b = st.columns([1,2])
        with c1a:
            if st.button("Test WP",key="twp"):
                r = test_wordpress(wp_url,wp_pass) if (GEN_OK and wp_url and wp_pass) else {"success":False,"message":"Enter credentials first"}
                st.session_state["wp_test"]=r
                if r["success"] and GEN_OK: st.session_state.wp_categories=fetch_wp_categories(wp_url,wp_pass)
        with c1b:
            if "wp_test" in st.session_state:
                r=st.session_state.wp_test; st.markdown(f'<div style="font-size:12px;padding:6px 0;color:{"#1a6e38" if r["success"] else "#c03030"};">{r["message"]}</div>',unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:22px;">', unsafe_allow_html=True)
        st.markdown('<h3 style="font-size:14px;font-weight:700;color:#1a1510;margin:0 0 15px;padding-bottom:10px;border-bottom:1px solid #f0e6d4;">⚙️ Preferences</h3>', unsafe_allow_html=True)
        pub = st.selectbox("Publish Status",["draft","publish"],index=0 if s.get("publish_status","draft")=="draft" else 1)
        ibox("💡 Start with <strong>Draft</strong> — review before going live.")
        use_img = st.toggle("Generate Images",value=bool(s.get("use_images",True)))
        show_card = st.toggle("Include Info Card",value=bool(s.get("show_card",True)))
        card_click = st.toggle("Card Clickable in WordPress",value=bool(s.get("card_clickable",False)))
        st.markdown('<p style="font-size:12.5px;font-weight:600;color:#1a1510;margin:14px 0 6px;">Midjourney Template</p>', unsafe_allow_html=True)
        mj_t = st.text_area("MJ",value=s.get("mj_template",""),height=70,placeholder="{recipe_name}, food photography --ar 2:3 --v 6.1",label_visibility="collapsed")
        use_il = st.toggle("Enable Internal Linking",value=bool(s.get("use_internal_links",False)))
        ml = int(s.get("max_links",4))
        if use_il: ml = st.slider("Max links per article",1,8,ml)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    if st.button("💾 Save Settings",type="primary"):
        st.session_state.settings.update({"groq_key":groq_key,"mj_key":goapi_key,"wp_url":wp_url,"wp_password":wp_pass,
            "publish_status":pub,"use_images":use_img,"show_card":show_card,"card_clickable":card_click,
            "mj_template":mj_t,"use_internal_links":use_il,"max_links":ml})
        save_db(); st.rerun()

def tab_prompts():
    sec_hdr("Prompts","Customize how your content is generated")
    s = st.session_state.settings
    if st.session_state.save_ok: sbox("Prompts saved!"); st.session_state.save_ok = False
    ibox("⚠️ <strong>Token Warning:</strong> Keep your article prompt under 2000 tokens to avoid Groq rate limits.")
    t1,t2,t3 = st.tabs(["✍️ Article Prompt","🃏 Card Prompt","📌 Pinterest Prompt"])
    with t1:
        ap = st.text_area("Article Prompt",value=s.get("article_prompt",""),height=200,
            placeholder="Travel: Write an inspiring guide in second person. Open with a vivid scene. Cover top 5 attractions, food, best time, budget, 5 tips. Target 25-40 adventurers. 1200-1500 words.\n\nRecipe: Write a warm personal recipe in first person. Open with a nostalgic story. Include 'Why You'll Love This', 6 tips, variations, 3 FAQs. 1200 words.")
        hs = st.text_area("HTML Structure (optional)",value=s.get("html_structure",""),height=100,
            placeholder='<h2 style="color:MAIN_COLOR;">Section</h2>')
    with t2:
        cp = st.text_area("Card Prompt",value=s.get("card_prompt",""),height=180,
            placeholder="Recipe: Create a card with prep time, cook time, servings, calories, ingredients, instructions.\n\nTravel: Create a card with best time to visit, daily budget USD, language, currency, top 3 attractions.")
    with t3:
        if st.session_state.user_plan != "pro":
            st.markdown("""<div style="background:linear-gradient(135deg,#1c1810,#0f0d09);border:1px solid rgba(201,137,42,.38);
                 border-radius:18px;padding:26px;text-align:center;">
              <div style="font-size:30px;margin-bottom:8px;">📌</div>
              <h3 style="font-family:'Fraunces',serif;font-size:19px;font-weight:800;color:#fdf6e8;margin:0 0 8px;">Pinterest Prompt</h3>
              <p style="font-size:13px;color:rgba(253,246,232,.5);">Available on <span style="color:#e8a83e;font-weight:600;">Pro plan ($40/month)</span>.</p>
            </div>""", unsafe_allow_html=True)
            pp = s.get("pinterest_prompt","")
        else:
            pp = st.text_area("Pinterest Prompt",value=s.get("pinterest_prompt",""),height=150,
                placeholder="My audience loves quick dinner recipes. Write warm pin descriptions using family food keywords. Under 200 chars with CTA.")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    if st.button("💾 Save Prompts",type="primary"):
        u = {"article_prompt":ap,"html_structure":hs,"card_prompt":cp}
        if st.session_state.user_plan=="pro": u["pinterest_prompt"]=pp
        st.session_state.settings.update(u); save_db(); st.rerun()

def tab_design():
    sec_hdr("Design Studio","Customize how your articles look")
    s = st.session_state.settings
    if st.session_state.save_ok: sbox("Design saved!"); st.session_state.save_ok = False
    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:22px;">', unsafe_allow_html=True)
        mc = st.color_picker("Main Color",value=s.get("design_main_color","#333333"))
        ac = st.color_picker("Accent Color",value=s.get("design_accent_color","#ea580c"))
        fo = ["inherit","'Georgia',serif","'Arial',sans-serif","'Verdana',sans-serif","'Times New Roman',serif"]
        fl = ["Site default","Georgia","Arial","Verdana","Times New Roman"]
        cf = s.get("design_font_family","inherit")
        fi = fo.index(cf) if cf in fo else 0
        ff = fo[st.selectbox("Font",range(len(fl)),format_func=lambda i:fl[i],index=fi)]
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:22px;">
          <h3 style="font-size:13.5px;font-weight:700;color:#1a1510;margin:0 0 14px;padding-bottom:10px;border-bottom:1px solid #f0e6d4;">👁️ Preview</h3>
          <div style="font-family:{ff};border:1px solid #eee;border-radius:10px;padding:16px;background:#fafafa;">
            <h2 style="color:{mc};font-size:16px;font-weight:800;margin:0 0 8px;">Your Article Title</h2>
            <p style="font-size:13px;color:#444;line-height:1.7;margin:0 0 11px;">This is how your article body text will look with your settings applied.</p>
            <div style="background:#f9f9f9;border-left:4px solid {ac};padding:9px 13px;border-radius:0 7px 7px 0;">
              <ul style="margin:0;padding-left:13px;line-height:2;font-size:13px;color:#444;"><li>Key insight here</li><li>Expert tip here</li></ul>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    if st.button("💾 Save Design",type="primary"):
        st.session_state.settings.update({"design_main_color":mc,"design_accent_color":ac,"design_font_family":ff})
        save_db(); st.rerun()

def tab_generate():
    sec_hdr("Generate Articles","Paste titles and publish automatically")
    s = st.session_state.settings
    miss = [k for k,v in [("Groq API key",s.get("groq_key")),("WordPress URL",s.get("wp_url")),
                           ("WordPress Password",s.get("wp_password")),("Article Prompt",s.get("article_prompt"))] if not v]
    if miss: ebox(f"Configure first: <strong>{', '.join(miss)}</strong>"); return

    st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:22px;margin-bottom:16px;">', unsafe_allow_html=True)
    ti = st.text_area("Titles (one per line)",height=150,placeholder="How to Travel Europe on a Budget\n10 Best Hiking Trails in Colorado\nMediterranean Grilled Chicken")
    c1,c2,c3,c4 = st.columns(4)
    with c1: gi = st.toggle("Images",value=bool(s.get("use_images",True)),key="g_img")
    with c2: gc = st.toggle("Card",value=bool(s.get("show_card",True)),key="g_card")
    with c3: gl = st.toggle("Int. Links",value=bool(s.get("use_internal_links",False)),key="g_links")
    with c4: ds = st.number_input("Delay(s)",0,30,5)
    sl = st.checkbox("Show logs",False)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🚀 Generate & Publish All",type="primary") and ti.strip():
        titles = [t.strip() for t in ti.strip().splitlines() if t.strip()]
        lc = st.empty()
        ps = {"groq_key":s.get("groq_key",""),"goapi_key":s.get("mj_key",""),"wp_url":s.get("wp_url",""),
              "wp_password":s.get("wp_password",""),"publish_status":s.get("publish_status","draft"),
              "mj_template":s.get("mj_template",""),"use_images":gi and bool(s.get("mj_key","")),
              "show_card":gc,"card_clickable":bool(s.get("card_clickable",False)),
              "use_internal_links":gl,"max_links":int(s.get("max_links",4)),
              "user_article_prompt":s.get("article_prompt",""),"user_html_structure":s.get("html_structure",""),
              "user_card_prompt":s.get("card_prompt",""),
              "user_design":{"main_color":s.get("design_main_color","#333333"),"accent_color":s.get("design_accent_color","#ea580c"),"font_family":s.get("design_font_family","inherit")}}
        logs = []
        for i,title in enumerate(titles):
            st.markdown(f'<div style="background:#fff8ec;border-left:4px solid #c9892a;border-radius:0 8px 8px 0;padding:9px 13px;font-size:13px;color:#7a5820;margin-bottom:7px;">⏳ <strong>{i+1}/{len(titles)}</strong>: {title}</div>',unsafe_allow_html=True)
            def lfn(m,_l=logs,_c=lc,_s=sl):
                _l.append(m)
                if _s: _c.markdown('<div style="background:#1a1510;border-radius:9px;padding:12px;font-family:monospace;font-size:12px;color:#a0c080;max-height:180px;overflow-y:auto;">'+'<br>'.join(_l[-18:])+'</div>',unsafe_allow_html=True)
            r = run_full_pipeline(title,ps,log_fn=lfn) if GEN_OK else {"success":False,"error":"Generator not available"}
            if r.get("success"):
                st.markdown(f'<div style="background:#f0faf4;border:1px solid #a4d8b8;color:#1a6e38;border-radius:9px;padding:9px 13px;font-size:13px;margin-bottom:7px;">✅ <strong>{title}</strong> → <a href="{r.get("post_url","")}" target="_blank">View Post</a></div>',unsafe_allow_html=True)
                db_inc(st.session_state.user_id,"articles_generated")
                db_inc(st.session_state.user_id,"posts_published")
                if r.get("image_count",0): db_inc(st.session_state.user_id,"images_created",r["image_count"])
            else: ebox(f"<strong>{title}</strong>: {r.get('error','Unknown error')}")
            if i < len(titles)-1 and ds > 0: time.sleep(ds)
        st.session_state.settings = db_load(st.session_state.user_id)

def tab_pinterest():
    sec_hdr("Pinterest Auto-Post","Configure Pinterest integration")
    s = st.session_state.settings
    if st.session_state.user_plan != "pro":
        st.markdown("""<div style="background:linear-gradient(135deg,#1c1810,#0f0d09);border:1px solid rgba(201,137,42,.38);
             border-radius:18px;padding:30px;text-align:center;margin-bottom:20px;">
          <div style="font-size:36px;margin-bottom:10px;">📌</div>
          <h3 style="font-family:'Fraunces',serif;font-size:21px;font-weight:800;color:#fdf6e8;margin:0 0 9px;">Pinterest Auto-Post</h3>
          <p style="font-size:13px;color:rgba(253,246,232,.5);line-height:1.7;max-width:420px;margin:0 auto 16px;">
            Available on <span style="color:#e8a83e;font-weight:700;">Pro plan ($40/month)</span>.</p>
        </div>""", unsafe_allow_html=True)
        if st.button("⬆️ Upgrade to Pro",type="primary"): st.session_state.dash_tab="billing"; st.rerun()
        return
    if st.session_state.save_ok: sbox("Pinterest saved!"); st.session_state.save_ok = False
    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:22px;">', unsafe_allow_html=True)
        pt = st.text_input("Pinterest Access Token",value=s.get("pinterest_token",""),type="password")
        pb = st.text_input("Pinterest Board ID",value=s.get("pinterest_board",""),placeholder="Your board ID")
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:22px;">', unsafe_allow_html=True)
        pp = st.text_area("Pinterest Prompt",value=s.get("pinterest_prompt",""),height=140,
            placeholder="My audience loves quick dinner recipes. Write warm pin descriptions using family food keywords.",label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:22px;margin-top:14px;">', unsafe_allow_html=True)
    st.markdown('<h3 style="font-size:14px;font-weight:700;color:#1a1510;margin:0 0 5px;padding-bottom:10px;border-bottom:1px solid #f0e6d4;">📅 Post Scheduler</h3>', unsafe_allow_html=True)
    days=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    sd=(s.get("schedule_days","") or "").split(",")
    dc=st.columns(7); sel=[]
    for i,d in enumerate(days):
        with dc[i]:
            if st.checkbox(d[:3],value=(d in sd),key=f"d_{d}"): sel.append(d)
    tc1,tc2=st.columns(2)
    with tc1: st2=st.time_input("Time",value=datetime.strptime(s.get("schedule_time","09:00"),"%H:%M").time())
    with tc2:
        tzs=["UTC","America/New_York","America/Los_Angeles","Europe/London","Europe/Paris","Asia/Dubai","Africa/Casablanca","Asia/Tokyo"]
        ctz=s.get("schedule_timezone","UTC"); tz=st.selectbox("Timezone",tzs,index=tzs.index(ctz) if ctz in tzs else 0)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    if st.button("💾 Save Pinterest",type="primary"):
        st.session_state.settings.update({"pinterest_token":pt,"pinterest_board":pb,"pinterest_prompt":pp,
            "schedule_days":",".join(sel),"schedule_time":st2.strftime("%H:%M"),"schedule_timezone":tz})
        save_db(); st.rerun()

def tab_billing():
    sec_hdr("Billing","Manage your plan")
    plan=st.session_state.user_plan
    c1,c2=st.columns(2)
    with c1:
        ab="border:2px solid #c9892a;" if plan=="basic" else "border:2px solid #dfd4bc;"
        st.markdown(f"""<div style="background:#fff;{ab}border-radius:22px;padding:36px 30px;text-align:center;">
          {'<div style="font-size:10px;font-weight:700;color:#c9892a;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px;">✦ Current</div>' if plan=='basic' else ''}
          <div style="font-size:11px;font-weight:700;color:#8a7a60;text-transform:uppercase;letter-spacing:2px;margin-bottom:13px;">Basic</div>
          <div style="font-family:'Fraunces',serif;font-size:58px;font-weight:900;color:#1a1510;line-height:1;">$30</div>
          <div style="font-size:13px;color:#8a7a60;margin-bottom:18px;">per month</div>
          <div style="text-align:left;font-size:13px;color:#5a5040;line-height:2.3;">✅ AI Articles<br>✅ Midjourney Images<br>✅ WordPress Publish<br>✅ Custom Prompts<br>❌ Pinterest</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div style="background:linear-gradient(158deg,#211808,#0f0d09);border:2px solid rgba(201,137,42,.55);border-radius:22px;padding:36px 30px;text-align:center;">
          {'<div style="font-size:10px;font-weight:700;color:#e8a83e;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px;">✦ Current</div>' if plan=='pro' else ''}
          <div style="font-size:11px;font-weight:700;color:rgba(232,168,62,.7);text-transform:uppercase;letter-spacing:2px;margin-bottom:13px;">Pro</div>
          <div style="font-family:'Fraunces',serif;font-size:58px;font-weight:900;color:#fff;line-height:1;">$40</div>
          <div style="font-size:13px;color:rgba(253,246,232,.4);margin-bottom:18px;">per month</div>
          <div style="text-align:left;font-size:13px;color:rgba(253,246,232,.8);line-height:2.3;">✅ Everything in Basic<br>✅ Pinterest Auto-Post<br>✅ Pinterest Optimizer<br>✅ Post Scheduler<br>✅ Priority Support</div>
        </div>""", unsafe_allow_html=True)
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown('<div style="background:#fff;border:1px solid #dfd4bc;border-radius:18px;padding:20px;">', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13.5px;color:#5a5040;">To upgrade contact <strong>support@nicheflow.ai</strong>. Payments via Stripe.</p>', unsafe_allow_html=True)
    if plan=="basic":
        if st.button("⬆️ Upgrade to Pro ($40/mo)",type="primary"): ibox("Contact support@nicheflow.ai to upgrade.")
    else: sbox("You are on the Pro plan.")
    st.markdown('</div>', unsafe_allow_html=True)

def tab_docs():
    sec_hdr("Documentation","Setup guide and best practices")
    render_docs()

# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
def render_dashboard():
    render_sidebar()
    st.markdown("""<style>
    section[data-testid="stSidebar"]{display:flex!important;}
    [data-testid="stSidebarContent"]{background:#0f0d09!important;}
    </style>""", unsafe_allow_html=True)
    t = st.session_state.dash_tab
    if   t=="overview":  tab_overview()
    elif t=="settings":  tab_settings()
    elif t=="prompts":   tab_prompts()
    elif t=="design":    tab_design()
    elif t=="generate":  tab_generate()
    elif t=="pinterest": tab_pinterest()
    elif t=="billing":   tab_billing()
    elif t=="docs":      tab_docs()

# ─────────────────────────────────────────────────────────────────────────────
#  ROUTER
# ─────────────────────────────────────────────────────────────────────────────
p = st.session_state.page
if   p=="home":      render_home()
elif p=="login":     render_login()
elif p=="signup":    render_signup()
elif p=="docs":      render_docs()
elif p=="dashboard":
    if not st.session_state.user_id: st.session_state.page="login"; st.rerun()
    else: render_dashboard()