# -*- coding: utf-8 -*-
"""
NicheFlow AI — app.py
Streamlit frontend. Connects to FastAPI backend at API_URL.
Run locally: streamlit run app.py
"""

import streamlit as st
import requests
import json
import os
import time
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────────────────────────────

API_URL = os.getenv("API_URL", "http://localhost:8000")   # Change to Railway URL after deploy

st.set_page_config(
    page_title="NicheFlow AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
#  GLOBAL STYLES
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

* { font-family: 'DM Sans', sans-serif !important; }
h1,h2,h3 { font-family: 'Syne', sans-serif !important; }

/* App background */
.stApp { background: #08090d !important; color: #f0f1f5 !important; }
.main { background: #08090d !important; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0e1018 !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
section[data-testid="stSidebar"] * { color: #c8ccd8 !important; }
section[data-testid="stSidebar"] .stMarkdown h2 {
    color: #818cf8 !important;
    font-size: 14px !important;
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* Inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox select,
.stNumberInput input {
    background: #141720 !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    color: #f0f1f5 !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label,
.stNumberInput label, .stCheckbox label {
    color: #9ba3b8 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}

/* Buttons */
.stButton > button {
    background: #6366f1 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: all 0.2s !important;
    padding: 10px 20px !important;
}
.stButton > button:hover {
    background: #4f46e5 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(99,102,241,0.35) !important;
}
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #9ba3b8 !important;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(255,255,255,0.08) !important;
    color: #f0f1f5 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #0e1018 !important;
    border-radius: 12px !important;
    padding: 4px !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
    color: #5a6278 !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: #1a1f2e !important;
    color: #818cf8 !important;
    box-shadow: 0 1px 8px rgba(0,0,0,0.3) !important;
}

/* Progress */
.stProgress > div > div { background: #6366f1 !important; }

/* Expander */
.streamlit-expanderHeader {
    background: #0e1018 !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 10px !important;
    color: #9ba3b8 !important;
}

/* Success/Error/Warning/Info */
.stSuccess { background: rgba(16,185,129,0.1) !important; border: 1px solid rgba(16,185,129,0.2) !important; color: #10b981 !important; border-radius: 10px !important; }
.stError   { background: rgba(239,68,68,0.1) !important;  border: 1px solid rgba(239,68,68,0.2) !important;  color: #ef4444 !important; border-radius: 10px !important; }
.stWarning { background: rgba(245,158,11,0.1) !important; border: 1px solid rgba(245,158,11,0.2) !important; color: #f59e0b !important; border-radius: 10px !important; }
.stInfo    { background: rgba(99,102,241,0.1) !important; border: 1px solid rgba(99,102,241,0.2) !important; color: #818cf8 !important; border-radius: 10px !important; }

/* Code blocks */
.stCodeBlock { border-radius: 10px !important; border: 1px solid rgba(255,255,255,0.06) !important; }

/* Metrics */
[data-testid="metric-container"] {
    background: #0e1018 !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 14px !important;
    padding: 16px !important;
}
[data-testid="metric-container"] label { color: #5a6278 !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #f0f1f5 !important; font-family: 'Syne', sans-serif !important; }

/* Divider */
hr { border-color: rgba(255,255,255,0.06) !important; }

/* Checkbox */
.stCheckbox [data-baseweb="checkbox"] { background: transparent !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #08090d; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────

def init_state():
    defaults = {
        "token": None,
        "user": None,
        "plan": "basic",
        "settings": {},
        "history": [],
        "history_loaded": False,
        "settings_loaded": False,
        "page": "login",
        "log_lines": [],
        "wp_categories": [],
        "categories_loaded": False,
        "wp_posts": [],
        "posts_loaded": False,
        "pinterest_boards": [],
        "boards_loaded": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─────────────────────────────────────────────────────────────────────────────
#  API HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def api(method: str, path: str, **kwargs):
    headers = kwargs.pop("headers", {})
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        resp = getattr(requests, method)(f"{API_URL}{path}", headers=headers, timeout=600, **kwargs)
        return resp
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to the backend. Make sure the FastAPI server is running.")
        return None


def load_settings():
    if st.session_state.settings_loaded:
        return
    resp = api("get", "/settings")
    if resp and resp.status_code == 200:
        data = resp.json()
        st.session_state.settings = data.get("settings", {})
        st.session_state.plan = data.get("plan", "basic")
        st.session_state.settings_loaded = True


def load_history():
    if st.session_state.history_loaded:
        return
    resp = api("get", "/history")
    if resp and resp.status_code == 200:
        st.session_state.history = resp.json().get("articles", [])
        st.session_state.history_loaded = True


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def token_badge(text: str, limit: int = 2000) -> str:
    n = estimate_tokens(text)
    pct = n / limit
    if pct > 1:
        return f"🔴 **{n:,} / {limit:,} tokens — OVER LIMIT!** Shorten your prompt."
    elif pct > 0.8:
        return f"🟡 **{n:,} / {limit:,} tokens** — approaching limit"
    return f"🟢 **{n:,} / {limit:,} estimated tokens** — good"


# ─────────────────────────────────────────────────────────────────────────────
#  CARD COMPONENTS
# ─────────────────────────────────────────────────────────────────────────────

def card(content_fn, title: str = "", icon: str = ""):
    with st.container():
        st.markdown(f"""
        <div style="background:#0e1018;border:1px solid rgba(255,255,255,0.06);
             border-radius:16px;padding:22px 24px;margin-bottom:16px;">
        {"<div style='font-family:Syne,sans-serif;font-size:15px;font-weight:600;color:#f0f1f5;margin-bottom:16px;'>" + icon + " " + title + "</div>" if title else ""}
        </div>
        """, unsafe_allow_html=True)
    content_fn()


def stat_row(stats: list):
    cols = st.columns(len(stats))
    for col, (label, value, delta) in zip(cols, stats):
        with col:
            st.metric(label, value, delta)


def section_header(title: str, subtitle: str = ""):
    st.markdown(f"""
    <div style="margin-bottom:24px;">
        <h1 style="font-family:'Syne',sans-serif;font-size:24px;font-weight:700;
                   color:#f0f1f5;margin:0 0 4px 0;">{title}</h1>
        {"<p style='color:#5a6278;font-size:14px;margin:0;'>" + subtitle + "</p>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)


def badge(text: str, color: str = "#6366f1", bg: str = "rgba(99,102,241,0.12)"):
    st.markdown(f"""
    <span style="background:{bg};color:{color};border:1px solid {color}40;
                 border-radius:20px;padding:3px 10px;font-size:12px;font-weight:600;">
        {text}
    </span>
    """, unsafe_allow_html=True)


def hint(text: str):
    st.markdown(f"<p style='color:#5a6278;font-size:12px;margin-top:4px;line-height:1.5;'>ℹ {text}</p>", unsafe_allow_html=True)


def pro_gate(feature_name: str):
    st.markdown(f"""
    <div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.2);
                border-radius:14px;padding:32px;text-align:center;">
        <div style="font-size:40px;margin-bottom:12px;">📌</div>
        <div style="font-family:'Syne',sans-serif;font-size:20px;font-weight:700;
                    color:#f0f1f5;margin-bottom:8px;">{feature_name}</div>
        <div style="color:#9ba3b8;font-size:14px;margin-bottom:20px;">
            This feature is available on the Pro plan ($40/mo).
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.link_button("Upgrade to Pro →", "https://nicheflow.ai/upgrade")


# ─────────────────────────────────────────────────────────────────────────────
#  AUTH PAGES
# ─────────────────────────────────────────────────────────────────────────────

def page_login():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center;margin-bottom:32px;padding-top:60px;">
            <div style="font-family:'Syne',sans-serif;font-size:26px;font-weight:800;
                        background:linear-gradient(135deg,#818cf8,#c084fc);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                        margin-bottom:8px;">✦ NicheFlow AI</div>
            <div style="color:#5a6278;font-size:14px;">Sign in to your dashboard</div>
        </div>
        """, unsafe_allow_html=True)

        with st.container():
            st.markdown('<div style="background:#0e1018;border:1px solid rgba(255,255,255,0.08);border-radius:20px;padding:32px;">', unsafe_allow_html=True)

            email = st.text_input("Email address", placeholder="you@example.com", key="login_email")
            password = st.text_input("Password", type="password", placeholder="Your password", key="login_pass")

            if st.button("Sign in →", use_container_width=True, key="login_btn"):
                if email and password:
                    with st.spinner("Signing in..."):
                        resp = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": password}, timeout=15)
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.token = data["access_token"]
                        st.session_state.user = data["user"]
                        st.session_state.page = "dashboard"
                        st.session_state.settings_loaded = False
                        st.session_state.history_loaded = False
                        st.rerun()
                    else:
                        err = resp.json().get("detail", "Login failed")
                        st.error(f"❌ {err}")
                else:
                    st.warning("Enter your email and password")

            st.markdown("<div style='text-align:center;margin-top:16px;color:#5a6278;font-size:13px;'>No account? <a href='#' style='color:#818cf8;'>Sign up below</a></div>", unsafe_allow_html=True)
            if st.button("Create account instead", use_container_width=True, key="goto_signup"):
                st.session_state.page = "signup"
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)


def page_signup():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center;margin-bottom:32px;padding-top:60px;">
            <div style="font-family:'Syne',sans-serif;font-size:26px;font-weight:800;
                        background:linear-gradient(135deg,#818cf8,#c084fc);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                        margin-bottom:8px;">✦ NicheFlow AI</div>
            <div style="color:#5a6278;font-size:14px;">Create your free account</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="background:#0e1018;border:1px solid rgba(255,255,255,0.08);border-radius:20px;padding:32px;">', unsafe_allow_html=True)

        email = st.text_input("Email address", placeholder="you@example.com", key="su_email")
        password = st.text_input("Password", type="password", placeholder="At least 8 characters", key="su_pass")

        if st.button("Create account →", use_container_width=True, key="signup_btn"):
            if email and len(password) >= 8:
                with st.spinner("Creating account..."):
                    resp = requests.post(f"{API_URL}/auth/signup", json={"email": email, "password": password}, timeout=15)
                if resp.status_code == 200:
                    st.success("✅ Account created! Check your email to confirm, then sign in.")
                    time.sleep(2)
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    err = resp.json().get("detail", "Signup failed")
                    st.error(f"❌ {err}")
            elif len(password) < 8:
                st.warning("Password must be at least 8 characters")
            else:
                st.warning("Enter email and password")

        if st.button("Already have an account? Sign in", use_container_width=True, key="goto_login"):
            st.session_state.page = "login"
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR (after login)
# ─────────────────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="font-family:'Syne',sans-serif;font-size:18px;font-weight:800;
                    background:linear-gradient(135deg,#818cf8,#c084fc);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                    padding:4px 0 16px;">✦ NicheFlow AI</div>
        """, unsafe_allow_html=True)

        # User pill
        user_email = st.session_state.user.get("email", "") if st.session_state.user else ""
        plan = st.session_state.plan
        plan_color = "#f59e0b" if plan == "pro" else "#818cf8"
        plan_label = "★ Pro" if plan == "pro" else "Basic"

        st.markdown(f"""
        <div style="background:#141720;border:1px solid rgba(255,255,255,0.07);
                    border-radius:12px;padding:12px;margin-bottom:16px;">
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:32px;height:32px;border-radius:50%;
                            background:linear-gradient(135deg,#6366f1,#c084fc);
                            display:flex;align-items:center;justify-content:center;
                            font-weight:700;color:#fff;font-size:13px;flex-shrink:0;">
                    {user_email[0].upper() if user_email else 'U'}
                </div>
                <div>
                    <div style="font-size:12px;color:#5a6278;white-space:nowrap;
                                overflow:hidden;text-overflow:ellipsis;max-width:140px;">
                        {user_email}
                    </div>
                    <div style="font-size:11px;font-weight:600;color:{plan_color};">{plan_label}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("## Navigation")

        pages = [
            ("dashboard", "◉  Dashboard"),
            ("generate", "⚡  Generate"),
            ("preview", "◎  Preview"),
            ("history", "📋  History"),
            ("pinterest", "📌  Pinterest" + (" ★" if plan == "pro" else " (Pro)")),
            ("settings", "⚙️  Settings"),
        ]

        for page_id, label in pages:
            is_active = st.session_state.page == page_id
            if st.button(
                label,
                key=f"nav_{page_id}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.page = page_id
                st.rerun()

        st.markdown("---")
        if st.button("Sign out →", key="logout", use_container_width=True, type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            init_state()
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD PAGE
# ─────────────────────────────────────────────────────────────────────────────

def page_dashboard():
    section_header("Dashboard", "Welcome back! Here's your overview.")
    load_history()

    history = st.session_state.history
    published = [h for h in history if h.get("status") == "published"]
    failed = [h for h in history if h.get("status") == "failed"]
    success_rate = f"{round(len(published)/max(len(history),1)*100)}%" if history else "—"

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Total Articles", len(history))
    with col2: st.metric("Published", len(published))
    with col3: st.metric("Failed", len(failed))
    with col4: st.metric("Success Rate", success_rate)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""<div style="font-family:'Syne',sans-serif;font-size:15px;font-weight:600;
                color:#f0f1f5;margin-bottom:12px;">Recent Activity</div>""", unsafe_allow_html=True)

    if not history:
        st.info("ℹ️ No articles yet. Go to **Generate** to publish your first batch.")
    else:
        for art in history[:8]:
            status_icon = "🟢" if art.get("status") == "published" else "🔴"
            ts = art.get("created_at", "")[:16].replace("T", " ") if art.get("created_at") else "—"
            col_a, col_b, col_c = st.columns([3, 1, 1])
            with col_a:
                st.markdown(f"<span style='font-size:14px;'>{status_icon} {art.get('title','')}</span>", unsafe_allow_html=True)
            with col_b:
                st.markdown(f"<span style='color:#5a6278;font-size:12px;'>{ts}</span>", unsafe_allow_html=True)
            with col_c:
                if art.get("post_url"):
                    st.markdown(f"<a href='{art['post_url']}' target='_blank' style='color:#818cf8;font-size:12px;'>View →</a>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("✦ **Tip:** Go to **Settings → Prompts** to customize your article voice before running a batch.")


# ─────────────────────────────────────────────────────────────────────────────
#  GENERATE PAGE
# ─────────────────────────────────────────────────────────────────────────────

def page_generate():
    section_header("Generate Articles", "Paste titles below — the AI handles everything else.")
    load_settings()
    cfg = st.session_state.settings

    if not cfg.get("gemini_key"):
        st.warning("⚠️ No AI key configured. Go to **Settings → API Keys** first.")
    if not cfg.get("wp_url"):
        st.warning("⚠️ No WordPress URL configured. Go to **Settings → WordPress** first.")

    col_left, col_right = st.columns([1.6, 1])

    with col_left:
        st.markdown("**Article Titles**")
        hint("One title per line. Each line becomes a full published article.")
        titles_text = st.text_area(
            "Titles",
            height=220,
            placeholder="10 Best Postpartum Recovery Tips\nHow to Build a Capsule Wardrobe on a Budget\nBest Baby Monitors 2025: Complete Guide",
            label_visibility="collapsed",
        )
        titles = [t.strip() for t in titles_text.split("\n") if t.strip()]
        st.caption(f"{len(titles)} title{'s' if len(titles) != 1 else ''} entered")

    with col_right:
        st.markdown("**Options**")

        draft = st.checkbox("Save as Draft", value=False, help="Publish to WordPress as draft instead of live")
        use_images = st.checkbox("Generate Images", value=False, help="Requires GoAPI key configured in Settings")

        delay = st.number_input(
            "Delay between articles (seconds)",
            min_value=0, max_value=120, value=cfg.get("delay_sec", 10),
            help="5–10 sec recommended for free AI tier limits"
        )

        # Categories
        if st.button("Load WP Categories", use_container_width=True, type="secondary"):
            resp = api("get", "/wp/categories")
            if resp and resp.status_code == 200:
                st.session_state.wp_categories = resp.json().get("categories", [])
                st.session_state.categories_loaded = True

        selected_cat_ids = []
        if st.session_state.categories_loaded and st.session_state.wp_categories:
            cat_options = {c["name"]: c["id"] for c in st.session_state.wp_categories}
            selected_cats = st.multiselect("WordPress Categories", list(cat_options.keys()))
            selected_cat_ids = [cat_options[c] for c in selected_cats]

    st.markdown("---")

    can_run = bool(titles and cfg.get("gemini_key") and cfg.get("wp_url"))

    if st.button(
        f"▶  Generate & Publish {len(titles)} Article{'s' if len(titles) != 1 else ''}",
        disabled=not can_run,
        use_container_width=True,
    ):
        progress = st.progress(0)
        status_placeholder = st.empty()
        log_placeholder = st.empty()
        log_lines = []

        all_done = 0
        for idx, title in enumerate(titles):
            progress.progress(idx / len(titles))
            status_placeholder.info(f"⏳ Processing **{title}** ({idx + 1}/{len(titles)})...")
            log_lines.append(f"**[{idx+1}/{len(titles)}]** {title}")
            log_placeholder.markdown("\n\n".join(log_lines[-20:]))

            resp = api("post", "/generate", json={
                "titles": [title],
                "draft": draft,
                "use_images": use_images,
                "delay_sec": 0,  # we handle delay in the loop
                "category_ids": selected_cat_ids if selected_cat_ids else None,
            })

            if resp and resp.status_code == 200:
                results = resp.json().get("results", [])
                for r in results:
                    if r.get("success"):
                        log_lines.append(f"  ✅ Published → {r.get('post_url','')}")
                        all_done += 1
                        st.session_state.history_loaded = False  # refresh
                    else:
                        log_lines.append(f"  ❌ Failed: {r.get('error','')}")
            else:
                err = resp.json().get("detail", "Unknown error") if resp else "No connection"
                log_lines.append(f"  ❌ API error: {err}")

            log_placeholder.markdown("\n\n".join(log_lines[-20:]))

            if idx < len(titles) - 1 and delay > 0:
                log_lines.append(f"  ⏱ Waiting {delay}s...")
                log_placeholder.markdown("\n\n".join(log_lines[-20:]))
                time.sleep(delay)

        progress.progress(1.0)
        status_placeholder.success(f"✅ Done! {all_done}/{len(titles)} articles published.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""<div style="background:#0e1018;border:1px solid rgba(255,255,255,0.06);
                border-radius:14px;padding:16px 20px;">
        <div style="font-size:13px;color:#5a6278;margin-bottom:8px;">💡 How it works</div>
        <div style="font-size:13px;color:#9ba3b8;line-height:1.7;">
            <strong style="color:#818cf8;">Model 1</strong> writes the full article body using your custom prompt.<br>
            <strong style="color:#818cf8;">Model 2</strong> generates the summary card with structured data.<br>
            Both run in parallel — the total time equals the slower of the two.
        </div>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  PREVIEW PAGE
# ─────────────────────────────────────────────────────────────────────────────

def page_preview():
    section_header("Preview Article", "Test your prompt style on a single title before a full batch.")
    load_settings()

    if not st.session_state.settings.get("gemini_key"):
        st.warning("⚠️ Configure an AI key in **Settings → API Keys** first.")
        return

    preview_title = st.text_input("Article title to preview", placeholder="The Best Fudgy Brookies Recipe")
    hint("This uses your configured article prompt from Settings. No WordPress publishing — just a preview.")

    if st.button("👁 Generate Preview", disabled=not preview_title):
        with st.spinner("Generating preview article... (~30–60 seconds)"):
            resp = api("post", "/preview", json={"title": preview_title})

        if resp and resp.status_code == 200:
            data = resp.json()
            st.success(f"✅ Preview ready — SEO title: **{data.get('seo_title', preview_title)}**")
            st.markdown("---")
            st.markdown(
                f"<div style='background:#0e1018;border:1px solid rgba(255,255,255,0.06);"
                f"border-radius:14px;padding:28px;color:#e0e0e8;line-height:1.8;'>"
                f"{data.get('content','')}</div>",
                unsafe_allow_html=True,
            )
        elif resp:
            st.error(f"❌ {resp.json().get('detail','Generation failed')}")


# ─────────────────────────────────────────────────────────────────────────────
#  HISTORY PAGE
# ─────────────────────────────────────────────────────────────────────────────

def page_history():
    section_header("History", "All articles you have generated and published.")

    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("↺ Refresh", use_container_width=True, type="secondary"):
            st.session_state.history_loaded = False
        if st.button("🗑 Clear All", use_container_width=True, type="secondary"):
            resp = api("delete", "/history")
            if resp and resp.status_code == 200:
                st.session_state.history = []
                st.session_state.history_loaded = False
                st.rerun()

    load_history()
    history = st.session_state.history

    if not history:
        st.info("No articles yet. Generate your first batch to see history here.")
        return

    published = sum(1 for h in history if h.get("status") == "published")
    failed = sum(1 for h in history if h.get("status") == "failed")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total", len(history))
    with col2: st.metric("Published", published)
    with col3: st.metric("Failed", failed)

    st.markdown("<br>", unsafe_allow_html=True)

    for art in history:
        status = art.get("status", "")
        icon = "🟢" if status == "published" else "🔴"
        ts = art.get("created_at", "")[:16].replace("T", " ") if art.get("created_at") else "—"

        with st.expander(f"{icon} {art.get('title','')} — {ts}"):
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.markdown(f"**Status:** {status}")
                if art.get("wp_status"):
                    st.markdown(f"**WP status:** {art.get('wp_status')}")
                if art.get("post_url"):
                    st.markdown(f"**URL:** [{art['post_url']}]({art['post_url']})")
                if art.get("error"):
                    st.error(f"Error: {art['error']}")
            with col_b:
                if art.get("post_url"):
                    st.link_button("View Article →", art["post_url"])
                if st.button("Delete", key=f"del_{art.get('id','')}", type="secondary"):
                    resp = api("delete", f"/history/{art.get('id','')}")
                    if resp and resp.status_code == 200:
                        st.session_state.history_loaded = False
                        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
#  SETTINGS PAGE
# ─────────────────────────────────────────────────────────────────────────────

def page_settings():
    section_header("Settings", "Configure your API keys, prompts, and integrations.")
    load_settings()
    cfg = st.session_state.settings.copy()
    plan = st.session_state.plan

    tab_labels = ["🔑 API Keys", "🌐 WordPress", "💬 Prompts", "🖼️ Images"]
    if plan == "pro":
        tab_labels.append("📌 Pinterest")

    tabs = st.tabs(tab_labels)

    # ── Tab: API Keys ─────────────────────────────────────────────────────────
    with tabs[0]:
        st.markdown("#### AI API Key")
        hint("Groq keys start with gsk_ (free at console.groq.com). Gemini keys start with AIza (free at aistudio.google.com). Add both comma-separated for automatic fallback and zero downtime.")

        gemini_key = st.text_input(
            "Groq / Gemini API Key(s)",
            value=cfg.get("gemini_key", ""),
            type="password",
            placeholder="gsk_... or AIza... or both comma-separated",
        )
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Test Key", key="test_ai"):
                if gemini_key:
                    with st.spinner("Testing..."):
                        resp = api("post", "/test", json={"key_type": "ai", "value": gemini_key})
                    if resp:
                        data = resp.json()
                        st.success(data["message"]) if data.get("success") else st.error(data["message"])
                else:
                    st.warning("Enter a key first")

        # Key detection info
        keys = [k.strip() for k in gemini_key.split(",") if k.strip()]
        has_groq = any(k.startswith("gsk_") for k in keys)
        has_gemini = any(k.startswith("AIza") for k in keys)
        if has_groq and has_gemini:
            st.success("✅ **Dual mode** — Groq + Gemini fallback. Zero downtime! 🚀")
        elif has_groq:
            st.info("✅ Using Groq (14,400 req/day free). Add a Gemini key after a comma for fallback.")
        elif has_gemini:
            st.info("✅ Using Gemini. Add a Groq key after a comma for fallback.")

        st.markdown("---")
        st.markdown("#### GoAPI Key (Midjourney Images)")
        hint("Only needed if you want AI-generated images via Midjourney. Get a key at goapi.ai.")

        goapi_key = st.text_input("GoAPI Key", value=cfg.get("goapi_key", ""), type="password", placeholder="Your GoAPI key...")
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Test GoAPI", key="test_goapi"):
                if goapi_key:
                    with st.spinner("Testing..."):
                        resp = api("post", "/test", json={"key_type": "goapi", "value": goapi_key})
                    if resp:
                        data = resp.json()
                        st.success(data["message"]) if data.get("success") else st.error(data["message"])

        cfg["gemini_key"] = gemini_key
        cfg["goapi_key"] = goapi_key

    # ── Tab: WordPress ────────────────────────────────────────────────────────
    with tabs[1]:
        st.markdown("#### WordPress Connection")

        wp_url = st.text_input("WordPress Site URL", value=cfg.get("wp_url", ""), placeholder="https://yoursite.com")
        hint("Include https:// and no trailing slash.")

        wp_password = st.text_input(
            "WordPress App Password",
            value=cfg.get("wp_password", ""),
            type="password",
            placeholder="username:xxxx xxxx xxxx xxxx",
        )
        hint("In WordPress: Users → Profile → Application Passwords → Add New. Format: yourusername:generated-password")

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Test Connection", key="test_wp"):
                if wp_url and wp_password:
                    with st.spinner("Testing..."):
                        resp = api("post", "/test", json={"key_type": "wp", "value": wp_url, "wp_password": wp_password})
                    if resp:
                        data = resp.json()
                        st.success(data["message"]) if data.get("success") else st.error(data["message"])
                else:
                    st.warning("Enter URL and password first")

        st.markdown("---")
        publish_status = st.selectbox(
            "Default Publish Status",
            ["draft", "publish"],
            index=1 if cfg.get("publish_status", "draft") == "publish" else 0,
        )
        hint("'draft' = review before going live. 'publish' = go live immediately.")

        use_internal_links = st.checkbox("Auto-inject internal links", value=cfg.get("use_internal_links", True))
        hint("Automatically link to your existing WordPress posts inside each new article for SEO.")

        if use_internal_links:
            max_links = st.number_input("Max links per article", min_value=1, max_value=10, value=cfg.get("max_links", 4))
            cfg["max_links"] = max_links

        delay_sec = st.number_input("Default delay between articles (seconds)", min_value=0, max_value=120, value=cfg.get("delay_sec", 10))
        hint("5–10 seconds recommended to stay within free AI tier rate limits.")

        cfg["wp_url"] = wp_url
        cfg["wp_password"] = wp_password
        cfg["publish_status"] = publish_status
        cfg["use_internal_links"] = use_internal_links
        cfg["delay_sec"] = delay_sec

    # ── Tab: Prompts ──────────────────────────────────────────────────────────
    with tabs[2]:
        st.markdown("#### Article Prompt")
        st.info("✦ Write your own prompt from scratch. Use `{title}` as a placeholder for the article title. **Leave empty to use the default general-purpose prompt.**")

        custom_prompt = st.text_area(
            "Article Prompt",
            value=cfg.get("custom_prompt", ""),
            height=260,
            placeholder="Write your own article prompt here. Example:\n\nYou are Emma, a warm mama blogger writing about pregnancy and motherhood.\nWrite a complete HTML article about: {title}\n\nInclude:\n- Relatable opening with personal story\n- 5 practical tips with real detail (2+ sentences each)\n- FAQ with 5 questions and thorough answers\n\nReturn ONLY a valid JSON: {\"seo_title\":\"\",\"excerpt\":\"\",\"html_content\":\"\",\"MAIN\":\"\",\"MAIN_DARK\":\"\",\"LIGHT_BG\":\"\",\"BORDER\":\"\"}",
            label_visibility="collapsed",
        )
        if custom_prompt:
            st.markdown(token_badge(custom_prompt, 2000))

        st.markdown("---")
        st.markdown("#### Card / Info Box Prompt")
        st.info("✦ A **separate AI model** generates your summary card. Customize it to match your niche — recipe card, gear comparison table, checklist, etc. **Leave empty to use the default.**")

        card_prompt = st.text_area(
            "Card Prompt",
            value=cfg.get("card_prompt", ""),
            height=180,
            placeholder="Example for recipe niche:\n\nExtract recipe data for: {title}\nReturn JSON with: prep_time, cook_time, servings, calories, ingredients (array), steps (array).\n\nExample for gear niche:\n\nCreate a comparison card for: {title}\nReturn JSON with: product_name, price, pros (array), cons (array), verdict.",
            label_visibility="collapsed",
        )
        if card_prompt:
            st.markdown(token_badge(card_prompt, 1500))

        show_card = st.checkbox("Show summary card in every article", value=cfg.get("show_card", True))
        hint("The card is appended at the end of each article as a styled HTML block.")

        cfg["custom_prompt"] = custom_prompt
        cfg["card_prompt"] = card_prompt
        cfg["show_card"] = show_card

    # ── Tab: Images ───────────────────────────────────────────────────────────
    with tabs[3]:
        st.markdown("#### Midjourney Image Template")
        hint("Use `{recipe_name}` or `{title}` as a placeholder. Add Midjourney parameters like --ar 2:3.")

        mj_template = st.text_area(
            "Midjourney Template",
            value=cfg.get("mj_template", ""),
            height=100,
            placeholder="Close up {recipe_name}, food photography, natural light, shot on iPhone --ar 2:3 --p h13jzed",
            label_visibility="collapsed",
        )

        st.markdown("---")
        use_pollinations = st.checkbox("Use Pollinations (free, no key needed)", value=cfg.get("use_pollinations", False))
        hint("Pollinations generates images for free but at lower quality than Midjourney. Good for testing.")

        pollinations_prompt = st.text_area(
            "Pollinations Prompt Template",
            value=cfg.get("pollinations_prompt", ""),
            height=80,
            placeholder="Professional photography of {title}, editorial style, natural light, 4K",
            label_visibility="collapsed",
        )
        hint("Use `{title}` as a placeholder.")

        cfg["mj_template"] = mj_template
        cfg["use_pollinations"] = use_pollinations
        cfg["pollinations_prompt"] = pollinations_prompt

    # ── Tab: Pinterest (Pro only) ─────────────────────────────────────────────
    if plan == "pro" and len(tabs) > 4:
        with tabs[4]:
            st.markdown("#### Pinterest API")
            hint("Get your Pinterest API access token at developers.pinterest.com → My Apps → Create App.")

            pinterest_token = st.text_input("Pinterest Access Token", value=cfg.get("pinterest_token", ""), type="password", placeholder="Your Pinterest access token...")
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("Test Pinterest", key="test_pint"):
                    if pinterest_token:
                        with st.spinner("Testing..."):
                            resp = api("post", "/test", json={"key_type": "pinterest", "value": pinterest_token})
                        if resp:
                            data = resp.json()
                            st.success(data["message"]) if data.get("success") else st.error(data["message"])

            st.markdown("---")
            auto_pin = st.checkbox("Auto-pin after publish", value=cfg.get("auto_pin", False))
            hint("Automatically create a Pinterest pin every time an article is published.")

            pin_delay_min = st.number_input("Pin delay (minutes after publish)", min_value=0, max_value=1440, value=cfg.get("pin_delay_min", 0))
            hint("Set 0 to pin immediately. Up to 1440 minutes (24 hours).")

            st.markdown("---")
            st.markdown("#### Pinterest Pin Prompt")
            st.info("✦ A separate AI model generates your pin title, description, and alt text. Use `{title}` and `{url}` as placeholders. **Leave empty to use the default.**")

            pinterest_prompt = st.text_area(
                "Pinterest Prompt",
                value=cfg.get("pinterest_prompt", ""),
                height=160,
                placeholder="For the article \"{title}\" at {url}:\nReturn JSON with:\n- pin_title (max 60 chars, keyword-rich)\n- pin_description (max 150 chars, ends with CTA like 'Save this!')\n- alt_text (1 descriptive sentence)\n- hashtags (array of 5)",
                label_visibility="collapsed",
            )
            if pinterest_prompt:
                st.markdown(token_badge(pinterest_prompt, 1000))

            st.markdown("---")
            st.markdown("#### Default Boards")
            hint("Enter board IDs comma-separated. Find them in the Pinterest URL when viewing a board.")
            pinterest_boards = st.text_input("Board IDs", value=cfg.get("pinterest_boards", ""), placeholder="board-id-1, board-id-2")

            if st.button("Load My Boards", type="secondary"):
                if pinterest_token:
                    with st.spinner("Fetching boards..."):
                        resp = api("get", "/pinterest/boards")
                    if resp and resp.status_code == 200:
                        st.session_state.pinterest_boards = resp.json().get("boards", [])
                        st.session_state.boards_loaded = True
                    else:
                        st.error("Could not load boards — check your Pinterest token.")
                else:
                    st.warning("Enter your Pinterest token first.")

            if st.session_state.boards_loaded and st.session_state.pinterest_boards:
                for b in st.session_state.pinterest_boards:
                    st.markdown(f"  — **{b['name']}** `{b['id']}`")

            cfg["pinterest_token"] = pinterest_token
            cfg["auto_pin"] = auto_pin
            cfg["pin_delay_min"] = pin_delay_min
            cfg["pinterest_prompt"] = pinterest_prompt
            cfg["pinterest_boards"] = pinterest_boards

    # ── Save button ───────────────────────────────────────────────────────────
    st.markdown("---")
    if st.button("💾  Save All Settings", use_container_width=True):
        with st.spinner("Saving..."):
            resp = api("post", "/settings", json=cfg)
        if resp and resp.status_code == 200:
            st.session_state.settings = cfg
            st.success("✅ Settings saved!")
        else:
            err = resp.json().get("detail", "Save failed") if resp else "No connection"
            st.error(f"❌ {err}")


# ─────────────────────────────────────────────────────────────────────────────
#  PINTEREST PAGE
# ─────────────────────────────────────────────────────────────────────────────

def page_pinterest():
    section_header("Pinterest Bot", "Auto-pin your articles with AI-optimized pin content.")

    if st.session_state.plan != "pro":
        pro_gate("Pinterest Bot")
        return

    load_history()
    load_settings()

    published_articles = [h for h in st.session_state.history if h.get("status") == "published" and h.get("post_url")]

    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown("**Select Boards**")
        hint("Load your boards from Pinterest, or enter board IDs manually in Settings → Pinterest.")

        if st.button("↺ Load Boards from Pinterest", type="secondary"):
            with st.spinner("Fetching boards..."):
                resp = api("get", "/pinterest/boards")
            if resp and resp.status_code == 200:
                st.session_state.pinterest_boards = resp.json().get("boards", [])
                st.session_state.boards_loaded = True
            else:
                st.error("Could not load boards — check Pinterest token in Settings.")

        boards = st.session_state.pinterest_boards
        selected_board_ids = []

        if boards:
            selected_board_names = st.multiselect(
                "Choose boards to post to",
                [b["name"] for b in boards],
                label_visibility="collapsed",
            )
            board_name_map = {b["name"]: b["id"] for b in boards}
            selected_board_ids = [board_name_map[n] for n in selected_board_names]
        else:
            manual_boards = st.session_state.settings.get("pinterest_boards", "")
            if manual_boards:
                selected_board_ids = [b.strip() for b in manual_boards.split(",") if b.strip()]
                st.info(f"Using {len(selected_board_ids)} board(s) from Settings.")
            else:
                st.warning("No boards configured. Load from Pinterest above or add board IDs in Settings → Pinterest.")

    with col_right:
        st.markdown("**Queue**")

        if not published_articles:
            st.warning("No published articles found. Generate and publish articles first.")
        else:
            st.metric("Articles ready to pin", len(published_articles))

        st.markdown("---")
        st.markdown("""
        <div style="background:#0e1018;border:1px solid rgba(255,255,255,0.06);
                    border-radius:12px;padding:16px;font-size:13px;color:#9ba3b8;line-height:1.7;">
            <strong style="color:#818cf8;">How it works:</strong><br>
            ✦ AI generates optimized pin title, description, and alt text for each article<br>
            ✦ The article's featured image is used as the pin image<br>
            ✦ Pins are created on all selected boards<br>
            ✦ Results saved to your history
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    can_pin = bool(published_articles and selected_board_ids)

    if st.button(
        f"📌  Pin {len(published_articles)} Articles to {len(selected_board_ids)} Board(s)",
        disabled=not can_pin,
        use_container_width=True,
    ):
        with st.spinner("Running Pinterest bot... this may take a few minutes."):
            resp = api("post", "/pinterest/run", json={"board_ids": selected_board_ids})

        if resp and resp.status_code == 200:
            results = resp.json().get("results", [])
            sent = sum(1 for r in results if r.get("status") == "sent")
            st.success(f"✅ Done! {sent}/{len(results)} articles pinned successfully.")
            for r in results:
                icon = "🟢" if r.get("status") == "sent" else "🔴"
                with st.expander(f"{icon} {r.get('title', '')}"):
                    st.markdown(f"**Pin title:** {r.get('pin_title', '')}")
                    st.markdown(f"**Description:** {r.get('pin_description', '')}")
                    st.markdown(f"**Alt text:** {r.get('alt_text', '')}")
                    for board_r in r.get("boards", []):
                        b_icon = "✅" if board_r.get("success") else "❌"
                        st.markdown(f"  {b_icon} Board `{board_r.get('board_id','')}` — {board_r.get('pin_id') or board_r.get('error','')}")
        elif resp:
            st.error(f"❌ {resp.json().get('detail', 'Pinterest run failed')}")
        else:
            st.error("❌ Could not connect to backend")


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN ROUTER
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if not st.session_state.token:
        if st.session_state.page == "signup":
            page_signup()
        else:
            page_login()
        return

    render_sidebar()
    load_settings()

    page = st.session_state.page
    if page == "dashboard":   page_dashboard()
    elif page == "generate":  page_generate()
    elif page == "preview":   page_preview()
    elif page == "history":   page_history()
    elif page == "settings":  page_settings()
    elif page == "pinterest": page_pinterest()
    else:                     page_dashboard()


if __name__ == "__main__":
    main()
