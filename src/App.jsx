import { useState, useEffect, useRef, useCallback } from "react";

// ─── Supabase Config ───────────────────────────────────────────────────────
const SUPABASE_URL = "https://gfulpvqqpakcgubkilwc.supabase.co";
const SUPABASE_KEY = "sb_publishable_U9zJp_BBd-jkJCwvGimNmw_E4NyynFN";

async function supaFetch(path, opts = {}) {
  const res = await fetch(`${SUPABASE_URL}/rest/v1${path}`, {
    ...opts,
    headers: {
      apikey: SUPABASE_KEY,
      Authorization: `Bearer ${SUPABASE_KEY}`,
      "Content-Type": "application/json",
      Prefer: "return=representation",
      ...(opts.headers || {}),
    },
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err);
  }
  return res.json().catch(() => null);
}

async function supaAuth(action, email, password) {
  const res = await fetch(`${SUPABASE_URL}/auth/v1/${action}`, {
    method: "POST",
    headers: { apikey: SUPABASE_KEY, "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error_description || data.msg || "Auth error");
  return data;
}

// ─── Claude API ────────────────────────────────────────────────────────────
async function callClaude(systemPrompt, userMessage, maxTokens = 1000) {
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: maxTokens,
      system: systemPrompt,
      messages: [{ role: "user", content: userMessage }],
    }),
  });
  const data = await res.json();
  return data.content?.[0]?.text || "";
}

// ─── Token Counter ─────────────────────────────────────────────────────────
function estimateTokens(text) {
  return Math.ceil(text.length / 4);
}

// ─── CSS ───────────────────────────────────────────────────────────────────
const css = `
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #08090d;
  --bg2: #0e1018;
  --bg3: #141720;
  --bg4: #1a1f2e;
  --border: rgba(255,255,255,0.07);
  --border2: rgba(255,255,255,0.12);
  --text: #f0f1f5;
  --text2: #9ba3b8;
  --text3: #5a6278;
  --accent: #6366f1;
  --accent2: #818cf8;
  --accent-dim: rgba(99,102,241,0.15);
  --accent-glow: rgba(99,102,241,0.3);
  --pro: #f59e0b;
  --pro-dim: rgba(245,158,11,0.15);
  --green: #10b981;
  --green-dim: rgba(16,185,129,0.12);
  --red: #ef4444;
  --red-dim: rgba(239,68,68,0.12);
  --radius: 12px;
  --radius-lg: 18px;
  --radius-xl: 24px;
  --font: 'DM Sans', sans-serif;
  --font-display: 'Syne', sans-serif;
  --shadow: 0 4px 24px rgba(0,0,0,0.4);
  --shadow-lg: 0 8px 48px rgba(0,0,0,0.5);
}

html { scroll-behavior: smooth; }
body { font-family: var(--font); background: var(--bg); color: var(--text); min-height: 100vh; overflow-x: hidden; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg2); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }

/* Animations */
@keyframes fadeUp { from { opacity:0; transform:translateY(20px); } to { opacity:1; transform:translateY(0); } }
@keyframes fadeIn { from { opacity:0; } to { opacity:1; } }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.5; } }
@keyframes spin { to { transform:rotate(360deg); } }
@keyframes shimmer { 0% { background-position:-200% 0; } 100% { background-position:200% 0; } }
@keyframes float { 0%,100% { transform:translateY(0); } 50% { transform:translateY(-12px); } }
@keyframes glow { 0%,100% { box-shadow:0 0 20px var(--accent-glow); } 50% { box-shadow:0 0 40px var(--accent-glow), 0 0 80px rgba(99,102,241,0.2); } }
@keyframes gradMove { 0% { background-position:0% 50%; } 50% { background-position:100% 50%; } 100% { background-position:0% 50%; } }
@keyframes slideIn { from { opacity:0; transform:translateX(-12px); } to { opacity:1; transform:translateX(0); } }

.fade-up { animation: fadeUp 0.5s ease both; }
.fade-up-d1 { animation: fadeUp 0.5s 0.1s ease both; }
.fade-up-d2 { animation: fadeUp 0.5s 0.2s ease both; }
.fade-up-d3 { animation: fadeUp 0.5s 0.3s ease both; }
.fade-up-d4 { animation: fadeUp 0.5s 0.4s ease both; }
.fade-up-d5 { animation: fadeUp 0.5s 0.5s ease both; }

/* Buttons */
.btn { display:inline-flex; align-items:center; gap:8px; padding:10px 22px; border-radius:var(--radius); font-family:var(--font); font-size:14px; font-weight:500; cursor:pointer; border:none; transition:all 0.2s; text-decoration:none; }
.btn-primary { background:var(--accent); color:#fff; }
.btn-primary:hover { background:#4f46e5; transform:translateY(-1px); box-shadow:0 4px 20px var(--accent-glow); }
.btn-ghost { background:transparent; color:var(--text2); border:1px solid var(--border); }
.btn-ghost:hover { border-color:var(--border2); color:var(--text); background:var(--bg3); }
.btn-pro { background:linear-gradient(135deg,#f59e0b,#d97706); color:#fff; }
.btn-pro:hover { transform:translateY(-1px); box-shadow:0 4px 20px rgba(245,158,11,0.4); }
.btn-danger { background:var(--red-dim); color:var(--red); border:1px solid rgba(239,68,68,0.2); }
.btn-danger:hover { background:var(--red); color:#fff; }
.btn-lg { padding:14px 32px; font-size:16px; border-radius:var(--radius-lg); }
.btn-sm { padding:7px 14px; font-size:13px; }
.btn:disabled { opacity:0.5; cursor:not-allowed; transform:none !important; }

/* Inputs */
.input { width:100%; padding:11px 14px; background:var(--bg3); border:1px solid var(--border); border-radius:var(--radius); color:var(--text); font-family:var(--font); font-size:14px; transition:border-color 0.2s, box-shadow 0.2s; outline:none; }
.input:focus { border-color:var(--accent); box-shadow:0 0 0 3px var(--accent-dim); }
.input::placeholder { color:var(--text3); }
.input-wrap { position:relative; }
.input-wrap .input-icon { position:absolute; left:12px; top:50%; transform:translateY(-50%); color:var(--text3); pointer-events:none; }
.input-wrap .input { padding-left:38px; }
textarea.input { resize:vertical; min-height:100px; line-height:1.6; }

/* Cards */
.card { background:var(--bg2); border:1px solid var(--border); border-radius:var(--radius-lg); padding:24px; }
.card-sm { padding:16px; border-radius:var(--radius); }
.glass { background:rgba(255,255,255,0.03); backdrop-filter:blur(12px); border:1px solid var(--border); }

/* Badge */
.badge { display:inline-flex; align-items:center; gap:5px; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:500; }
.badge-pro { background:var(--pro-dim); color:var(--pro); border:1px solid rgba(245,158,11,0.2); }
.badge-basic { background:var(--accent-dim); color:var(--accent2); border:1px solid rgba(99,102,241,0.2); }
.badge-green { background:var(--green-dim); color:var(--green); border:1px solid rgba(16,185,129,0.2); }
.badge-red { background:var(--red-dim); color:var(--red); }

/* Tooltip hint */
.hint { font-size:12px; color:var(--text3); margin-top:5px; }

/* Divider */
.divider { height:1px; background:var(--border); margin:20px 0; }

/* Spinner */
.spinner { width:18px; height:18px; border:2px solid rgba(255,255,255,0.2); border-top-color:#fff; border-radius:50%; animation:spin 0.7s linear infinite; }
.spinner-sm { width:14px; height:14px; }
.spinner-lg { width:32px; height:32px; }
.spinner-accent { border-color:var(--accent-dim); border-top-color:var(--accent); }

/* Tabs */
.tabs { display:flex; gap:4px; background:var(--bg3); padding:4px; border-radius:var(--radius); border:1px solid var(--border); }
.tab { padding:8px 16px; border-radius:calc(var(--radius) - 2px); font-size:13px; font-weight:500; cursor:pointer; color:var(--text3); border:none; background:transparent; transition:all 0.2s; font-family:var(--font); }
.tab.active { background:var(--bg); color:var(--text); box-shadow:0 1px 8px rgba(0,0,0,0.3); }
.tab:hover:not(.active) { color:var(--text2); }

/* Status dot */
.dot { width:8px; height:8px; border-radius:50%; display:inline-block; }
.dot-green { background:var(--green); box-shadow:0 0 6px var(--green); }
.dot-red { background:var(--red); }
.dot-yellow { background:var(--pro); }
.dot-pulse { animation:pulse 2s ease-in-out infinite; }

/* Progress */
.progress { height:4px; background:var(--bg4); border-radius:2px; overflow:hidden; }
.progress-fill { height:100%; background:linear-gradient(90deg,var(--accent),var(--accent2)); border-radius:2px; transition:width 0.4s ease; }

/* Token warning */
.token-bar { padding:8px 12px; border-radius:var(--radius); font-size:12px; display:flex; align-items:center; gap:8px; }
.token-ok { background:var(--green-dim); color:var(--green); border:1px solid rgba(16,185,129,0.2); }
.token-warn { background:rgba(245,158,11,0.1); color:var(--pro); border:1px solid rgba(245,158,11,0.2); }
.token-over { background:var(--red-dim); color:var(--red); border:1px solid rgba(239,68,68,0.2); animation:pulse 1.5s ease-in-out infinite; }

/* Mesh gradient backgrounds */
.mesh-bg { position:relative; }
.mesh-bg::before { content:''; position:absolute; inset:0; background:radial-gradient(ellipse 60% 50% at 30% 20%, rgba(99,102,241,0.12) 0%, transparent 60%), radial-gradient(ellipse 50% 40% at 75% 70%, rgba(139,92,246,0.08) 0%, transparent 60%), radial-gradient(ellipse 40% 60% at 60% 10%, rgba(59,130,246,0.06) 0%, transparent 60%); pointer-events:none; z-index:0; }

/* Noise texture overlay */
.noise::after { content:''; position:fixed; inset:0; background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E"); pointer-events:none; z-index:9999; opacity:0.4; }

/* ─── LANDING PAGE ─── */
.landing { min-height:100vh; }
.nav { position:fixed; top:0; left:0; right:0; z-index:100; display:flex; align-items:center; justify-content:space-between; padding:16px 48px; background:rgba(8,9,13,0.85); backdrop-filter:blur(20px); border-bottom:1px solid var(--border); }
.nav-logo { font-family:var(--font-display); font-size:20px; font-weight:700; background:linear-gradient(135deg,var(--accent2),#c084fc); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.nav-links { display:flex; align-items:center; gap:32px; }
.nav-links a { color:var(--text2); font-size:14px; text-decoration:none; transition:color 0.2s; }
.nav-links a:hover { color:var(--text); }

.hero { padding:160px 48px 100px; max-width:1100px; margin:0 auto; position:relative; z-index:1; }
.hero-eyebrow { display:inline-flex; align-items:center; gap:8px; padding:6px 14px; background:var(--accent-dim); border:1px solid rgba(99,102,241,0.25); border-radius:20px; font-size:12px; font-weight:500; color:var(--accent2); margin-bottom:28px; }
.hero h1 { font-family:var(--font-display); font-size:clamp(42px,6vw,76px); font-weight:800; line-height:1.05; letter-spacing:-2px; margin-bottom:24px; }
.hero h1 .grad { background:linear-gradient(135deg,var(--accent2) 0%,#c084fc 50%,#f472b6 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-size:200% 200%; animation:gradMove 4s ease infinite; }
.hero p { font-size:18px; color:var(--text2); line-height:1.7; max-width:560px; margin-bottom:40px; font-weight:300; }
.hero-cta { display:flex; align-items:center; gap:16px; flex-wrap:wrap; }
.hero-stats { display:flex; gap:48px; margin-top:64px; padding-top:48px; border-top:1px solid var(--border); }
.stat-num { font-family:var(--font-display); font-size:32px; font-weight:700; color:var(--text); }
.stat-label { font-size:13px; color:var(--text3); margin-top:2px; }

.features { padding:80px 48px; max-width:1100px; margin:0 auto; }
.section-label { font-size:12px; font-weight:600; color:var(--accent2); letter-spacing:2px; text-transform:uppercase; margin-bottom:16px; }
.section-title { font-family:var(--font-display); font-size:clamp(28px,4vw,44px); font-weight:700; line-height:1.15; letter-spacing:-1px; margin-bottom:16px; }
.section-sub { font-size:16px; color:var(--text2); font-weight:300; max-width:500px; line-height:1.7; margin-bottom:56px; }

.features-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:20px; }
.feature-card { background:var(--bg2); border:1px solid var(--border); border-radius:var(--radius-lg); padding:28px; transition:border-color 0.2s, transform 0.2s; position:relative; overflow:hidden; }
.feature-card:hover { border-color:var(--border2); transform:translateY(-3px); }
.feature-card::before { content:''; position:absolute; top:0; left:0; right:0; height:1px; background:linear-gradient(90deg,transparent,var(--accent),transparent); opacity:0; transition:opacity 0.3s; }
.feature-card:hover::before { opacity:1; }
.feature-icon { width:44px; height:44px; background:var(--accent-dim); border:1px solid rgba(99,102,241,0.2); border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:20px; margin-bottom:16px; }
.feature-title { font-family:var(--font-display); font-size:16px; font-weight:600; margin-bottom:8px; }
.feature-desc { font-size:14px; color:var(--text2); line-height:1.6; }

/* Pricing */
.pricing { padding:80px 48px; max-width:900px; margin:0 auto; }
.pricing-grid { display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-top:56px; }
.plan-card { background:var(--bg2); border:1px solid var(--border); border-radius:var(--radius-xl); padding:36px; position:relative; overflow:hidden; transition:transform 0.2s; }
.plan-card:hover { transform:translateY(-4px); }
.plan-card.featured { border-color:var(--accent); background:linear-gradient(145deg,var(--bg2),rgba(99,102,241,0.05)); }
.plan-card.featured::before { content:'Most Popular'; position:absolute; top:20px; right:20px; background:var(--accent); color:#fff; font-size:11px; font-weight:600; padding:4px 10px; border-radius:20px; }
.plan-name { font-family:var(--font-display); font-size:20px; font-weight:700; margin-bottom:8px; }
.plan-price { font-family:var(--font-display); font-size:48px; font-weight:800; letter-spacing:-2px; margin:20px 0 8px; }
.plan-price span { font-size:20px; font-weight:400; color:var(--text3); }
.plan-desc { font-size:14px; color:var(--text2); margin-bottom:28px; line-height:1.6; }
.plan-features { list-style:none; display:flex; flex-direction:column; gap:12px; margin-bottom:32px; }
.plan-features li { display:flex; align-items:center; gap:10px; font-size:14px; color:var(--text2); }
.plan-features li::before { content:'✓'; width:20px; height:20px; background:var(--green-dim); color:var(--green); border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:11px; font-weight:700; flex-shrink:0; }

/* Auth page */
.auth-page { min-height:100vh; display:flex; align-items:center; justify-content:center; padding:24px; position:relative; }
.auth-card { width:100%; max-width:420px; background:var(--bg2); border:1px solid var(--border); border-radius:var(--radius-xl); padding:40px; position:relative; z-index:1; }
.auth-logo { font-family:var(--font-display); font-size:22px; font-weight:700; background:linear-gradient(135deg,var(--accent2),#c084fc); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:8px; }
.auth-title { font-family:var(--font-display); font-size:26px; font-weight:700; margin-bottom:6px; }
.auth-sub { font-size:14px; color:var(--text2); margin-bottom:32px; }
.form-group { margin-bottom:18px; }
.form-label { font-size:13px; font-weight:500; color:var(--text2); margin-bottom:6px; display:block; }
.auth-divider { text-align:center; color:var(--text3); font-size:13px; margin:20px 0; position:relative; }
.auth-divider::before, .auth-divider::after { content:''; position:absolute; top:50%; width:calc(50% - 20px); height:1px; background:var(--border); }
.auth-divider::before { left:0; }
.auth-divider::after { right:0; }

/* ─── APP LAYOUT ─── */
.app-layout { display:flex; min-height:100vh; }
.sidebar { width:240px; flex-shrink:0; background:var(--bg2); border-right:1px solid var(--border); display:flex; flex-direction:column; position:fixed; top:0; left:0; bottom:0; z-index:50; }
.sidebar-logo { padding:22px 20px; border-bottom:1px solid var(--border); font-family:var(--font-display); font-size:17px; font-weight:700; background:linear-gradient(135deg,var(--accent2),#c084fc); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.sidebar-nav { flex:1; padding:12px 10px; overflow-y:auto; }
.sidebar-section { font-size:10px; font-weight:600; color:var(--text3); letter-spacing:1.5px; text-transform:uppercase; padding:16px 10px 6px; }
.nav-item { display:flex; align-items:center; gap:10px; padding:9px 12px; border-radius:var(--radius); cursor:pointer; font-size:14px; color:var(--text2); transition:all 0.15s; border:none; background:none; width:100%; font-family:var(--font); position:relative; }
.nav-item:hover { background:var(--bg3); color:var(--text); }
.nav-item.active { background:var(--accent-dim); color:var(--accent2); }
.nav-item.active::before { content:''; position:absolute; left:0; top:50%; transform:translateY(-50%); width:3px; height:60%; background:var(--accent); border-radius:0 3px 3px 0; }
.nav-item .nav-badge { margin-left:auto; background:var(--pro-dim); color:var(--pro); font-size:10px; padding:2px 6px; border-radius:10px; }
.sidebar-footer { padding:14px 10px; border-top:1px solid var(--border); }
.user-pill { display:flex; align-items:center; gap:10px; padding:10px 12px; border-radius:var(--radius); background:var(--bg3); }
.user-avatar { width:32px; height:32px; border-radius:50%; background:linear-gradient(135deg,var(--accent),#c084fc); display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:600; color:#fff; flex-shrink:0; }
.user-info { flex:1; min-width:0; }
.user-email { font-size:12px; color:var(--text3); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.user-plan { font-size:11px; font-weight:600; }

.main-content { margin-left:240px; flex:1; min-height:100vh; }
.page-header { padding:28px 36px 0; border-bottom:1px solid var(--border); }
.page-title { font-family:var(--font-display); font-size:22px; font-weight:700; }
.page-sub { font-size:14px; color:var(--text2); margin-top:4px; margin-bottom:20px; }
.page-body { padding:28px 36px; }

/* Dashboard cards */
.stat-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:28px; }
.stat-card { background:var(--bg2); border:1px solid var(--border); border-radius:var(--radius-lg); padding:20px; }
.stat-card-num { font-family:var(--font-display); font-size:28px; font-weight:700; }
.stat-card-label { font-size:12px; color:var(--text3); margin-top:4px; }
.stat-card-change { font-size:12px; color:var(--green); margin-top:8px; }

/* Process log */
.process-log { background:var(--bg); border:1px solid var(--border); border-radius:var(--radius-lg); padding:20px; max-height:300px; overflow-y:auto; font-family:'Courier New', monospace; font-size:12px; line-height:1.8; }
.log-line { display:flex; align-items:flex-start; gap:8px; animation:slideIn 0.2s ease; }
.log-time { color:var(--text3); flex-shrink:0; }
.log-ok { color:var(--green); }
.log-err { color:var(--red); }
.log-info { color:var(--accent2); }
.log-warn { color:var(--pro); }

/* Prompt editor */
.prompt-editor { position:relative; }
.prompt-counter { position:absolute; bottom:10px; right:12px; font-size:11px; color:var(--text3); background:var(--bg3); padding:2px 8px; border-radius:8px; }

/* Pinterest board */
.board-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(140px,1fr)); gap:12px; }
.board-item { background:var(--bg3); border:1px solid var(--border); border-radius:var(--radius); padding:12px; cursor:pointer; transition:all 0.2s; text-align:center; }
.board-item:hover, .board-item.selected { border-color:var(--accent); background:var(--accent-dim); }
.board-item.selected { border-color:var(--accent); }
.board-icon { font-size:24px; margin-bottom:6px; }
.board-name { font-size:12px; font-weight:500; color:var(--text2); }

/* Toggle */
.toggle { position:relative; width:40px; height:22px; flex-shrink:0; }
.toggle input { opacity:0; width:0; height:0; }
.toggle-slider { position:absolute; cursor:pointer; inset:0; background:var(--bg4); border-radius:11px; border:1px solid var(--border2); transition:0.2s; }
.toggle-slider::before { content:''; position:absolute; height:16px; width:16px; left:2px; top:2px; background:var(--text3); border-radius:50%; transition:0.2s; }
.toggle input:checked + .toggle-slider { background:var(--accent); border-color:var(--accent); }
.toggle input:checked + .toggle-slider::before { transform:translateX(18px); background:#fff; }

/* Settings section */
.settings-section { background:var(--bg2); border:1px solid var(--border); border-radius:var(--radius-lg); overflow:hidden; margin-bottom:20px; }
.settings-header { padding:18px 24px; border-bottom:1px solid var(--border); display:flex; align-items:center; gap:10px; }
.settings-header h3 { font-size:15px; font-weight:600; }
.settings-body { padding:20px 24px; display:flex; flex-direction:column; gap:18px; }
.setting-row { display:flex; align-items:flex-start; justify-content:space-between; gap:24px; }
.setting-info { flex:1; }
.setting-name { font-size:14px; font-weight:500; }
.setting-desc { font-size:12px; color:var(--text3); margin-top:3px; line-height:1.5; }
.setting-control { flex-shrink:0; }

/* Alert */
.alert { display:flex; align-items:center; gap:10px; padding:12px 16px; border-radius:var(--radius); font-size:13px; margin-bottom:16px; }
.alert-warn { background:rgba(245,158,11,0.1); color:var(--pro); border:1px solid rgba(245,158,11,0.2); }
.alert-ok { background:var(--green-dim); color:var(--green); border:1px solid rgba(16,185,129,0.2); }
.alert-err { background:var(--red-dim); color:var(--red); border:1px solid rgba(239,68,68,0.2); }
.alert-info { background:var(--accent-dim); color:var(--accent2); border:1px solid rgba(99,102,241,0.2); }

/* modal */
.modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.7); z-index:200; display:flex; align-items:center; justify-content:center; padding:20px; animation:fadeIn 0.2s ease; }
.modal { background:var(--bg2); border:1px solid var(--border2); border-radius:var(--radius-xl); padding:32px; max-width:540px; width:100%; max-height:85vh; overflow-y:auto; animation:fadeUp 0.25s ease; position:relative; }
.modal-close { position:absolute; top:16px; right:16px; background:var(--bg3); border:1px solid var(--border); border-radius:8px; width:30px; height:30px; display:flex; align-items:center; justify-content:center; cursor:pointer; color:var(--text3); font-size:14px; }
.modal-close:hover { color:var(--text); background:var(--bg4); }
.modal-title { font-family:var(--font-display); font-size:20px; font-weight:700; margin-bottom:6px; }
.modal-sub { font-size:13px; color:var(--text2); margin-bottom:24px; }

/* History items */
.history-item { background:var(--bg2); border:1px solid var(--border); border-radius:var(--radius-lg); padding:16px 20px; display:flex; align-items:center; gap:16px; margin-bottom:10px; transition:border-color 0.15s; }
.history-item:hover { border-color:var(--border2); }
.history-info { flex:1; min-width:0; }
.history-title { font-size:14px; font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.history-meta { font-size:12px; color:var(--text3); margin-top:3px; }
.history-actions { display:flex; gap:8px; flex-shrink:0; }

@media(max-width:900px) {
  .nav { padding:16px 24px; }
  .hero { padding:120px 24px 80px; }
  .features, .pricing { padding:60px 24px; }
  .features-grid { grid-template-columns:1fr; }
  .pricing-grid { grid-template-columns:1fr; }
  .stat-grid { grid-template-columns:repeat(2,1fr); }
  .sidebar { transform:translateX(-100%); }
  .main-content { margin-left:0; }
}
`;

// ─── Icons ─────────────────────────────────────────────────────────────────
const Icon = ({ name, size = 16 }) => {
  const icons = {
    zap: "⚡", article: "📝", settings: "⚙️", history: "📋", dashboard: "◉",
    pinterest: "📌", logout: "→", star: "★", check: "✓", warn: "⚠️",
    info: "ℹ️", user: "👤", key: "🔑", link: "🔗", image: "🖼️",
    ai: "✦", send: "↗", trash: "✕", eye: "◎", copy: "⎘", refresh: "↺",
    lock: "🔒", card: "🃏", prompt: "💬", schedule: "📅", board: "📋",
    close: "✕", arrow: "→", plus: "+", minus: "-", globe: "🌐"
  };
  return <span style={{ fontSize: size }} title={name}>{icons[name] || "•"}</span>;
};

// ─── Token Counter Component ────────────────────────────────────────────────
function TokenCounter({ text, limit = 2000 }) {
  const tokens = estimateTokens(text);
  const pct = tokens / limit;
  const cls = pct > 1 ? "token-over" : pct > 0.8 ? "token-warn" : "token-ok";
  const label = pct > 1
    ? `⚠️ Over limit! ${tokens.toLocaleString()} / ${limit.toLocaleString()} estimated tokens`
    : pct > 0.8
    ? `⚠️ Approaching limit: ${tokens.toLocaleString()} / ${limit.toLocaleString()} tokens`
    : `✓ ${tokens.toLocaleString()} / ${limit.toLocaleString()} estimated tokens`;
  return (
    <div className={`token-bar ${cls}`} style={{ marginTop: 6 }}>
      <div style={{ flex: 1 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
          <span style={{ fontSize: 11 }}>{label}</span>
        </div>
        <div className="progress">
          <div className="progress-fill" style={{ width: `${Math.min(pct * 100, 100)}%`, background: pct > 1 ? "var(--red)" : pct > 0.8 ? "var(--pro)" : undefined }} />
        </div>
      </div>
    </div>
  );
}

// ─── Hint Component ─────────────────────────────────────────────────────────
function Hint({ children }) {
  return <p className="hint" style={{ display: "flex", alignItems: "flex-start", gap: 5 }}><span style={{ flexShrink: 0, marginTop: 1 }}>ℹ</span>{children}</p>;
}

// ─── LANDING PAGE ──────────────────────────────────────────────────────────
function LandingPage({ onLogin, onSignup }) {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const h = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", h);
    return () => window.removeEventListener("scroll", h);
  }, []);

  const features = [
    { icon: "✦", title: "AI Article Engine", desc: "Two separate AI models — one crafts your article, another builds the recipe/info card. Fully independent and customizable." },
    { icon: "🎨", title: "Prompt Studio", desc: "Write your own article prompt from scratch. Our AI warns you before you hit token limits, keeping generation fast and reliable." },
    { icon: "🖼️", title: "Image Automation", desc: "Generate Midjourney images with your custom template. Each image slot has its own prompt so you get perfect variety." },
    { icon: "📌", title: "Pinterest Bot (Pro)", desc: "Auto-pin after publishing. AI writes optimized titles, descriptions, and alt text. Schedule pins to your boards." },
    { icon: "📅", title: "Smart Scheduling", desc: "Delay between articles, schedule publishing times, draft or go live instantly. You control the pace." },
    { icon: "🔗", title: "Internal Linking", desc: "Automatically fetch and inject internal links from your WordPress site to boost SEO on every article." },
  ];

  return (
    <div className="landing mesh-bg noise">
      <style>{css}</style>
      <nav className="nav" style={{ background: scrolled ? "rgba(8,9,13,0.95)" : "rgba(8,9,13,0.7)" }}>
        <div className="nav-logo">NicheFlow AI</div>
        <div className="nav-links">
          <a href="#features">Features</a>
          <a href="#pricing">Pricing</a>
          <a href="#docs">Docs</a>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="btn btn-ghost btn-sm" onClick={onLogin}>Log in</button>
          <button className="btn btn-primary btn-sm" onClick={onSignup}>Get started</button>
        </div>
      </nav>

      <section className="hero">
        <div className="hero-eyebrow fade-up">✦ Content automation, reimagined</div>
        <h1 className="fade-up-d1">
          Publish <span className="grad">10x faster</span><br />across every niche.
        </h1>
        <p className="fade-up-d2">
          NicheFlow AI writes long-form articles, builds info cards, generates images, and pins to Pinterest — all from a single dashboard you control.
        </p>
        <div className="hero-cta fade-up-d3">
          <button className="btn btn-primary btn-lg" onClick={onSignup} style={{ animation: "glow 3s ease-in-out infinite" }}>
            Start for free → 
          </button>
          <button className="btn btn-ghost btn-lg" onClick={onLogin}>Sign in</button>
        </div>
        <div className="hero-stats fade-up-d4">
          {[["2 AI Models", "Article + Card, independently tuned"],
            ["Custom Prompts", "Full control over your content voice"],
            ["Pinterest Ready", "Auto-pin with Pro plan"],
            ["Any Niche", "Mommy blog to finance to travel"]
          ].map(([n, l]) => (
            <div key={n}>
              <div className="stat-num">{n}</div>
              <div className="stat-label">{l}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="features" id="features">
        <div className="section-label fade-up">What's inside</div>
        <h2 className="section-title fade-up-d1">Everything your content business needs</h2>
        <p className="section-sub fade-up-d2">Built for niche site owners who want AI-quality content at scale, without losing their unique voice.</p>
        <div className="features-grid">
          {features.map((f, i) => (
            <div className={`feature-card fade-up-d${Math.min(i + 1, 5)}`} key={f.title}>
              <div className="feature-icon">{f.icon}</div>
              <div className="feature-title">{f.title}</div>
              <div className="feature-desc">{f.desc}</div>
            </div>
          ))}
        </div>
      </section>

      <section id="docs" style={{ padding: "60px 48px", maxWidth: 900, margin: "0 auto" }}>
        <div className="section-label">Documentation</div>
        <h2 className="section-title">Up in 5 minutes</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20, marginTop: 40 }}>
          {[
            { step: "01", title: "Connect your AI keys", desc: "Paste your Groq or Gemini API key. We support both with automatic fallback for zero downtime." },
            { step: "02", title: "Set your WordPress", desc: "Enter your site URL and an Application Password. We test the connection instantly." },
            { step: "03", title: "Write your prompt", desc: "Customize the article voice and card style for your niche. Our token counter warns you in real time." },
          ].map(d => (
            <div key={d.step} className="card">
              <div style={{ fontFamily: "var(--font-display)", fontSize: 36, fontWeight: 800, color: "var(--border2)", marginBottom: 12 }}>{d.step}</div>
              <div style={{ fontFamily: "var(--font-display)", fontSize: 15, fontWeight: 600, marginBottom: 8 }}>{d.title}</div>
              <div style={{ fontSize: 13, color: "var(--text2)", lineHeight: 1.6 }}>{d.desc}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="pricing" id="pricing">
        <div className="section-label">Pricing</div>
        <h2 className="section-title">Simple, honest pricing</h2>
        <p className="section-sub">No per-article fees. No surprise charges. Pay monthly, cancel anytime.</p>
        <div className="pricing-grid">
          <div className="plan-card">
            <div className="plan-name">Basic</div>
            <div className="plan-price">$30<span>/mo</span></div>
            <div className="plan-desc">Everything you need to run a content business on autopilot.</div>
            <ul className="plan-features">
              {["Unlimited article generation","Custom article prompt","Custom card prompt","Midjourney image automation","WordPress auto-publish","Internal link injection","WordPress category support","History & analytics"].map(f => <li key={f}>{f}</li>)}
            </ul>
            <button className="btn btn-primary" style={{ width: "100%" }} onClick={onSignup}>Get Basic</button>
          </div>
          <div className="plan-card featured">
            <div className="plan-name">Pro</div>
            <div className="plan-price" style={{ background: "linear-gradient(135deg,#f59e0b,#d97706)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>$40<span style={{ WebkitTextFillColor: "var(--text3)" }}>/mo</span></div>
            <div className="plan-desc">Everything in Basic plus Pinterest automation for maximum reach.</div>
            <ul className="plan-features">
              {["Everything in Basic","Pinterest auto-pinning","Custom Pinterest prompt","AI-optimized pin titles & descriptions","Alt text generation","Board selection & scheduling","Pin links to published articles","Featured image as pin image"].map(f => <li key={f}>{f}</li>)}
            </ul>
            <button className="btn btn-pro" style={{ width: "100%" }} onClick={onSignup}>Get Pro ★</button>
          </div>
        </div>
      </section>

      <footer style={{ borderTop: "1px solid var(--border)", padding: "40px 48px", display: "flex", justifyContent: "space-between", alignItems: "center", maxWidth: 1100, margin: "0 auto" }}>
        <div className="nav-logo">NicheFlow AI</div>
        <div style={{ fontSize: 13, color: "var(--text3)" }}>© 2025 NicheFlow AI. All rights reserved.</div>
      </footer>
    </div>
  );
}

// ─── AUTH PAGE ─────────────────────────────────────────────────────────────
function AuthPage({ mode, onSuccess, onSwitch, onBack }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      const action = mode === "login" ? "token?grant_type=password" : "signup";
      const data = await supaAuth(action, email, password);
      if (mode === "signup") { setDone(true); }
      else { onSuccess(data); }
    } catch (err) {
      setError(err.message);
    } finally { setLoading(false); }
  }

  return (
    <div className="auth-page mesh-bg noise">
      <style>{css}</style>
      <div className="auth-card fade-up">
        <button className="btn btn-ghost btn-sm" onClick={onBack} style={{ marginBottom: 20, paddingLeft: 0, border: "none" }}>← Back</button>
        <div className="auth-logo">NicheFlow AI</div>
        {done ? (
          <>
            <div className="alert alert-ok" style={{ marginTop: 20 }}>✓ Check your email to confirm your account, then log in.</div>
            <button className="btn btn-primary" style={{ width: "100%", marginTop: 12 }} onClick={() => onSwitch("login")}>Go to Login</button>
          </>
        ) : (
          <>
            <h2 className="auth-title">{mode === "login" ? "Welcome back" : "Create account"}</h2>
            <p className="auth-sub">{mode === "login" ? "Sign in to your NicheFlow dashboard" : "Start publishing smarter content today"}</p>
            {error && <div className="alert alert-err" style={{ marginBottom: 16 }}>{error}</div>}
            <form onSubmit={submit}>
              <div className="form-group">
                <label className="form-label">Email address</label>
                <input className="input" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" required />
              </div>
              <div className="form-group">
                <label className="form-label">Password</label>
                <input className="input" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder={mode === "signup" ? "At least 8 characters" : "Your password"} required minLength={8} />
              </div>
              <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center", marginTop: 8 }} disabled={loading}>
                {loading ? <><span className="spinner spinner-sm" /> Working...</> : mode === "login" ? "Sign in →" : "Create account →"}
              </button>
            </form>
            <div className="auth-divider">or</div>
            <p style={{ textAlign: "center", fontSize: 14, color: "var(--text2)" }}>
              {mode === "login" ? "No account? " : "Already have one? "}
              <button style={{ background: "none", border: "none", color: "var(--accent2)", cursor: "pointer", fontFamily: "var(--font)", fontSize: 14 }} onClick={() => onSwitch(mode === "login" ? "signup" : "login")}>
                {mode === "login" ? "Sign up free" : "Sign in"}
              </button>
            </p>
          </>
        )}
      </div>
    </div>
  );
}

// ─── DASHBOARD ─────────────────────────────────────────────────────────────
function Dashboard({ history }) {
  const published = history.filter(h => h.status === "published").length;
  const failed = history.filter(h => h.status === "failed").length;

  return (
    <div className="fade-up">
      <div className="stat-grid">
        {[
          { num: history.length, label: "Total articles run", change: "" },
          { num: published, label: "Successfully published", change: published > 0 ? `${Math.round(published / Math.max(history.length, 1) * 100)}% success rate` : "" },
          { num: failed, label: "Failed articles", change: "" },
          { num: 0, label: "Pinterest pins sent", change: "Pro feature" },
        ].map((s, i) => (
          <div className="stat-card" key={i}>
            <div className="stat-card-num">{s.num}</div>
            <div className="stat-card-label">{s.label}</div>
            {s.change && <div className="stat-card-change">{s.change}</div>}
          </div>
        ))}
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ fontFamily: "var(--font-display)", fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Recent Activity</div>
        {history.length === 0 ? (
          <div style={{ color: "var(--text3)", fontSize: 14, padding: "20px 0", textAlign: "center" }}>No articles published yet. Go to Generate to start.</div>
        ) : history.slice(-5).reverse().map((h, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 0", borderBottom: i < 4 ? "1px solid var(--border)" : "none" }}>
            <span className={`dot ${h.status === "published" ? "dot-green" : "dot-red"}`} />
            <span style={{ flex: 1, fontSize: 14, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{h.title}</span>
            <span style={{ fontSize: 12, color: "var(--text3)", flexShrink: 0 }}>{h.time}</span>
            {h.post_url && <a href={h.post_url} target="_blank" rel="noreferrer" style={{ color: "var(--accent2)", fontSize: 12, textDecoration: "none" }}>View →</a>}
          </div>
        ))}
      </div>

      <div className="alert alert-info">
        <span>✦</span>
        <span>Tip: Go to <strong>Settings → Prompts</strong> to customize your article voice before generating your first batch.</span>
      </div>
    </div>
  );
}

// ─── GENERATE PAGE ─────────────────────────────────────────────────────────
function GeneratePage({ config, onHistoryUpdate, plan }) {
  const [titles, setTitles] = useState("");
  const [delay, setDelay] = useState(10);
  const [draft, setDraft] = useState(false);
  const [useImages, setUseImages] = useState(false);
  const [running, setRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [progress, setProgress] = useState(0);
  const logRef = useRef(null);

  const addLog = useCallback((msg, type = "info") => {
    const time = new Date().toLocaleTimeString("en", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    setLogs(prev => [...prev.slice(-100), { msg, type, time }]);
    setTimeout(() => { if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight; }, 50);
  }, []);

  const titleList = titles.split("\n").map(t => t.trim()).filter(Boolean);

  async function run() {
    if (!config.gemini_key) { addLog("No AI API key configured. Go to Settings.", "err"); return; }
    if (!config.wp_url) { addLog("No WordPress URL configured. Go to Settings.", "err"); return; }
    if (!titleList.length) { addLog("Enter at least one article title.", "warn"); return; }

    setRunning(true); setLogs([]); setProgress(0);
    addLog(`Starting batch: ${titleList.length} article(s)`, "ok");

    for (let i = 0; i < titleList.length; i++) {
      const title = titleList[i];
      setProgress(i / titleList.length);
      addLog(`[${i + 1}/${titleList.length}] Generating: ${title}`, "info");

      try {
        const prompt = config.custom_prompt || buildDefaultPrompt(title);
        addLog("✦ Calling AI model for article body...", "info");

        const response = await callClaude(
          "You are a helpful content writer. Generate article content as requested. Return only the HTML content, no markdown wrapping.",
          prompt.replace("{title}", title),
          1000
        );

        addLog(`✓ Article generated (~${estimateTokens(response)} tokens)`, "ok");
        addLog("Publishing to WordPress...", "info");

        const pub = await publishToWP(title, response, config, draft ? "draft" : "publish");
        if (pub.success) {
          addLog(`✓ Published! → ${pub.url}`, "ok");
          onHistoryUpdate({ title, status: "published", post_url: pub.url, time: new Date().toLocaleTimeString() });
        } else {
          addLog(`✗ Publish failed: ${pub.error}`, "err");
          onHistoryUpdate({ title, status: "failed", error: pub.error, time: new Date().toLocaleTimeString() });
        }
      } catch (err) {
        addLog(`✗ Error: ${err.message}`, "err");
        onHistoryUpdate({ title, status: "failed", error: err.message, time: new Date().toLocaleTimeString() });
      }

      if (i < titleList.length - 1 && delay > 0) {
        addLog(`Waiting ${delay}s before next...`, "info");
        await new Promise(r => setTimeout(r, delay * 1000));
      }
    }

    setProgress(1);
    addLog(`Batch complete. ${titleList.length} article(s) processed.`, "ok");
    setRunning(false);
  }

  async function publishToWP(title, content, cfg, status) {
    try {
      const [user, pass] = cfg.wp_password.split(":").map((s, i) => i === 0 ? s.trim() : s.trim());
      const creds = btoa(`${user}:${pass}`);
      const base = cfg.wp_url.replace(/\/$/, "");
      const res = await fetch(`${base}/wp-json/wp/v2/posts`, {
        method: "POST",
        headers: { "Authorization": `Basic ${creds}`, "Content-Type": "application/json" },
        body: JSON.stringify({ title, content, status }),
      });
      const data = await res.json();
      if (!res.ok) return { success: false, error: data.message || "WordPress error" };
      return { success: true, url: data.link };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  function buildDefaultPrompt(title) {
    return `Write a comprehensive, SEO-optimized article about: "${title}". Include an engaging introduction, detailed body sections with H2/H3 headings, practical tips, and a conclusion. Write in a warm, conversational tone. Return clean HTML only.`;
  }

  const logTypeClass = { ok: "log-ok", err: "log-err", info: "log-info", warn: "log-warn" };

  return (
    <div className="fade-up">
      {!config.gemini_key && (
        <div className="alert alert-warn" style={{ marginBottom: 20 }}>
          ⚠️ No AI key configured. Go to <strong>Settings → API Keys</strong> first.
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
        <div className="card">
          <div style={{ fontFamily: "var(--font-display)", fontSize: 15, fontWeight: 600, marginBottom: 6 }}>Article Titles</div>
          <div className="hint" style={{ marginBottom: 12 }}>One title per line. Each will become a full article.</div>
          <textarea
            className="input"
            style={{ minHeight: 200, fontFamily: "monospace", fontSize: 13 }}
            value={titles}
            onChange={e => setTitles(e.target.value)}
            placeholder={"10 Best Postpartum Recovery Tips\nHow to Build a Capsule Wardrobe\nBest Baby Gear for Newborns 2025"}
            disabled={running}
          />
          <div style={{ marginTop: 8, fontSize: 12, color: "var(--text3)" }}>
            {titleList.length} title{titleList.length !== 1 ? "s" : ""} entered
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div className="card">
            <div style={{ fontFamily: "var(--font-display)", fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Options</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <div className="setting-row">
                <div className="setting-info">
                  <div className="setting-name">Save as Draft</div>
                  <div className="setting-desc">Publish to WordPress as draft instead of live</div>
                </div>
                <label className="toggle"><input type="checkbox" checked={draft} onChange={e => setDraft(e.target.checked)} /><span className="toggle-slider" /></label>
              </div>
              <div className="setting-row">
                <div className="setting-info">
                  <div className="setting-name">Generate Images</div>
                  <div className="setting-desc">Requires GoAPI key in Settings</div>
                </div>
                <label className="toggle"><input type="checkbox" checked={useImages} onChange={e => setUseImages(e.target.checked)} /><span className="toggle-slider" /></label>
              </div>
              <div>
                <div className="setting-name" style={{ marginBottom: 6 }}>Delay between articles</div>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <input className="input" type="number" value={delay} min={0} max={120} onChange={e => setDelay(+e.target.value)} style={{ width: 80 }} />
                  <span style={{ fontSize: 13, color: "var(--text2)" }}>seconds</span>
                </div>
                <Hint>5–10 sec recommended to stay within free AI tier limits</Hint>
              </div>
            </div>
          </div>

          <button
            className="btn btn-primary"
            style={{ width: "100%", justifyContent: "center", padding: "14px", fontSize: 15 }}
            onClick={run}
            disabled={running || !titleList.length}
          >
            {running ? <><span className="spinner spinner-sm" /> Running batch...</> : `▶ Generate ${titleList.length || ""} Article${titleList.length !== 1 ? "s" : ""}`}
          </button>

          {running && (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "var(--text3)", marginBottom: 6 }}>
                <span>Progress</span><span>{Math.round(progress * 100)}%</span>
              </div>
              <div className="progress"><div className="progress-fill" style={{ width: `${progress * 100}%` }} /></div>
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 15, fontWeight: 600, display: "flex", alignItems: "center", gap: 8 }}>
            <span className={`dot ${running ? "dot-green dot-pulse" : "dot-yellow"}`} />
            Process Log
          </div>
          <button className="btn btn-ghost btn-sm" onClick={() => setLogs([])}>Clear</button>
        </div>
        <div className="process-log" ref={logRef}>
          {logs.length === 0 ? (
            <div style={{ color: "var(--text3)", fontFamily: "var(--font)" }}>Logs will appear here when you run a batch...</div>
          ) : logs.map((l, i) => (
            <div key={i} className="log-line">
              <span className="log-time">[{l.time}]</span>
              <span className={logTypeClass[l.type] || ""}>{l.msg}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── SETTINGS PAGE ─────────────────────────────────────────────────────────
function SettingsPage({ config, onSave, plan }) {
  const [cfg, setCfg] = useState({ ...config });
  const [saved, setSaved] = useState(false);
  const [tab, setTab] = useState("api");
  const [testing, setTesting] = useState({});
  const [testResults, setTestResults] = useState({});

  function update(key, val) {
    setCfg(prev => ({ ...prev, [key]: val }));
  }

  function save() {
    onSave(cfg);
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  }

  async function testKey(keyName, keyVal) {
    if (!keyVal) return;
    setTesting(p => ({ ...p, [keyName]: true }));
    try {
      let result;
      if (keyVal.startsWith("gsk_")) {
        const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {
          method: "POST",
          headers: { Authorization: `Bearer ${keyVal}`, "Content-Type": "application/json" },
          body: JSON.stringify({ model: "llama-3.1-8b-instant", messages: [{ role: "user", content: "Say OK" }], max_tokens: 5 }),
        });
        result = res.ok ? { ok: true, msg: "✓ Groq key is valid!" } : { ok: false, msg: "✗ Invalid Groq key" };
      } else if (keyVal.startsWith("AIza")) {
        const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${keyVal}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ contents: [{ parts: [{ text: "Say OK" }] }], generationConfig: { maxOutputTokens: 5 } }),
        });
        result = res.ok ? { ok: true, msg: "✓ Gemini key is valid!" } : { ok: false, msg: "✗ Invalid Gemini key" };
      } else {
        result = { ok: false, msg: "✗ Unrecognized key format. Use gsk_ (Groq) or AIza (Gemini)." };
      }
      setTestResults(p => ({ ...p, [keyName]: result }));
    } catch (e) {
      setTestResults(p => ({ ...p, [keyName]: { ok: false, msg: `✗ ${e.message}` } }));
    } finally {
      setTesting(p => ({ ...p, [keyName]: false }));
    }
  }

  async function testWP() {
    if (!cfg.wp_url || !cfg.wp_password) return;
    setTesting(p => ({ ...p, wp: true }));
    try {
      const [user, pass] = cfg.wp_password.split(":").map((s, i) => i === 0 ? s.trim() : s.trim());
      const creds = btoa(`${user}:${pass}`);
      const base = cfg.wp_url.replace(/\/$/, "");
      const res = await fetch(`${base}/wp-json/wp/v2/users/me`, {
        headers: { Authorization: `Basic ${creds}` },
      });
      const data = await res.json();
      const result = res.ok
        ? { ok: true, msg: `✓ Connected as: ${data.name || user}` }
        : { ok: false, msg: `✗ WordPress error: ${data.message || res.status}` };
      setTestResults(p => ({ ...p, wp: result }));
    } catch (e) {
      setTestResults(p => ({ ...p, wp: { ok: false, msg: `✗ ${e.message}` } }));
    } finally {
      setTesting(p => ({ ...p, wp: false }));
    }
  }

  const tabs = [
    { id: "api", label: "API Keys" },
    { id: "wp", label: "WordPress" },
    { id: "prompts", label: "Prompts" },
    { id: "images", label: "Images" },
    ...(plan === "pro" ? [{ id: "pinterest", label: "Pinterest" }] : []),
  ];

  return (
    <div className="fade-up">
      <div style={{ marginBottom: 20 }}>
        <div className="tabs" style={{ width: "fit-content" }}>
          {tabs.map(t => (
            <button key={t.id} className={`tab ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>{t.label}</button>
          ))}
        </div>
      </div>

      {tab === "api" && (
        <div className="settings-section fade-up">
          <div className="settings-header">
            <span>🔑</span><h3>AI API Keys</h3>
          </div>
          <div className="settings-body">
            <div>
              <label className="form-label">Groq or Gemini API Key</label>
              <div style={{ display: "flex", gap: 10 }}>
                <input className="input" type="password" value={cfg.gemini_key || ""} onChange={e => update("gemini_key", e.target.value)} placeholder="gsk_... or AIza... or both comma-separated" style={{ flex: 1 }} />
                <button className="btn btn-ghost btn-sm" onClick={() => testKey("ai", cfg.gemini_key)} disabled={testing.ai}>
                  {testing.ai ? <span className="spinner spinner-sm" /> : "Test"}
                </button>
              </div>
              {testResults.ai && <div className={`alert ${testResults.ai.ok ? "alert-ok" : "alert-err"}`} style={{ marginTop: 8 }}>{testResults.ai.msg}</div>}
              <Hint>Groq key starts with gsk_ (get free at console.groq.com). Gemini key starts with AIza (get free at aistudio.google.com). Add both comma-separated for automatic fallback.</Hint>
            </div>
            <div>
              <label className="form-label">GoAPI Key (Midjourney images)</label>
              <input className="input" type="password" value={cfg.goapi_key || ""} onChange={e => update("goapi_key", e.target.value)} placeholder="Your GoAPI key..." />
              <Hint>Required only if you want AI-generated article images via Midjourney.</Hint>
            </div>
          </div>
        </div>
      )}

      {tab === "wp" && (
        <div className="settings-section fade-up">
          <div className="settings-header"><span>🌐</span><h3>WordPress Connection</h3></div>
          <div className="settings-body">
            <div>
              <label className="form-label">WordPress Site URL</label>
              <input className="input" value={cfg.wp_url || ""} onChange={e => update("wp_url", e.target.value)} placeholder="https://yoursite.com" />
            </div>
            <div>
              <label className="form-label">WordPress App Password</label>
              <input className="input" type="password" value={cfg.wp_password || ""} onChange={e => update("wp_password", e.target.value)} placeholder="username:xxxx xxxx xxxx xxxx" />
              <Hint>In WordPress: Users → Profile → Application Passwords → Add New. Format: yourusername:the-generated-password</Hint>
            </div>
            <div>
              <button className="btn btn-ghost btn-sm" onClick={testWP} disabled={testing.wp}>
                {testing.wp ? <><span className="spinner spinner-sm" /> Testing...</> : "Test Connection"}
              </button>
              {testResults.wp && <div className={`alert ${testResults.wp.ok ? "alert-ok" : "alert-err"}`} style={{ marginTop: 8 }}>{testResults.wp.msg}</div>}
            </div>
            <div>
              <label className="form-label">Default Publish Status</label>
              <select className="input" value={cfg.publish_status || "publish"} onChange={e => update("publish_status", e.target.value)}>
                <option value="publish">Publish immediately</option>
                <option value="draft">Save as draft</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {tab === "prompts" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }} className="fade-up">
          <div className="settings-section">
            <div className="settings-header"><span>💬</span><h3>Article Prompt</h3></div>
            <div className="settings-body">
              <div>
                <div className="alert alert-info" style={{ marginBottom: 12 }}>
                  ✦ Write your own prompt from scratch. Use <code style={{ background: "var(--bg3)", padding: "1px 5px", borderRadius: 4 }}>{"{title}"}</code> as a placeholder for the article title. Leave empty to use the default food-blog style.
                </div>
                <div className="prompt-editor">
                  <textarea
                    className="input"
                    style={{ minHeight: 220, fontFamily: "monospace", fontSize: 13 }}
                    value={cfg.custom_prompt || ""}
                    onChange={e => update("custom_prompt", e.target.value)}
                    placeholder={`Write your own article prompt here. Example:\n\nYou are Emma, a warm mama blogger writing about pregnancy and motherhood.\nWrite a complete HTML article about: {title}\n\nInclude:\n- Engaging intro with personal story\n- 5 practical tips with real detail\n- FAQ section with 5 questions\n\nReturn only clean HTML.`}
                  />
                  {cfg.custom_prompt && <div className="prompt-counter">{estimateTokens(cfg.custom_prompt).toLocaleString()} tokens</div>}
                </div>
                {cfg.custom_prompt && <TokenCounter text={cfg.custom_prompt} limit={2000} />}
                <Hint>Keep your prompt under 2,000 tokens for best performance. The AI will use the remaining token budget to write your full article.</Hint>
              </div>
            </div>
          </div>

          <div className="settings-section">
            <div className="settings-header"><span>🃏</span><h3>Card / Info Box Prompt</h3></div>
            <div className="settings-body">
              <div>
                <div className="alert alert-info" style={{ marginBottom: 12 }}>
                  ✦ This prompt controls the separate AI model that generates your recipe card or info box. Customize it to match your niche — recipe card, gear comparison table, product summary, etc.
                </div>
                <div className="prompt-editor">
                  <textarea
                    className="input"
                    style={{ minHeight: 180, fontFamily: "monospace", fontSize: 13 }}
                    value={cfg.card_prompt || ""}
                    onChange={e => update("card_prompt", e.target.value)}
                    placeholder={`Example for recipe niche:\n\nExtract structured data for: {title}\nReturn JSON with: prep_time, cook_time, servings, calories, ingredients array, steps array.\n\nExample for gear niche:\n\nCreate a comparison card for: {title}\nReturn JSON with: product_name, price, pros array, cons array, verdict.`}
                  />
                  {cfg.card_prompt && <div className="prompt-counter">{estimateTokens(cfg.card_prompt).toLocaleString()} tokens</div>}
                </div>
                {cfg.card_prompt && <TokenCounter text={cfg.card_prompt} limit={1500} />}
              </div>
              <div className="setting-row">
                <div className="setting-info">
                  <div className="setting-name">Show card in article</div>
                  <div className="setting-desc">Append the generated card HTML at the end of each article</div>
                </div>
                <label className="toggle"><input type="checkbox" checked={cfg.show_card !== false} onChange={e => update("show_card", e.target.checked)} /><span className="toggle-slider" /></label>
              </div>
            </div>
          </div>
        </div>
      )}

      {tab === "images" && (
        <div className="settings-section fade-up">
          <div className="settings-header"><span>🖼️</span><h3>Image Settings</h3></div>
          <div className="settings-body">
            <div>
              <label className="form-label">Midjourney Image Template</label>
              <textarea
                className="input"
                style={{ minHeight: 100 }}
                value={cfg.mj_template || ""}
                onChange={e => update("mj_template", e.target.value)}
                placeholder="Close up {recipe_name}, food photography, natural light, shot on iPhone --ar 1:1"
              />
              <Hint>Use <code style={{ background: "var(--bg3)", padding: "1px 5px", borderRadius: 4 }}>{"{recipe_name}"}</code> as a placeholder for the title. Add Midjourney parameters like --ar 2:3 for aspect ratio.</Hint>
            </div>
            <div className="setting-row">
              <div className="setting-info">
                <div className="setting-name">Use Pollinations (free)</div>
                <div className="setting-desc">Generate images for free via Pollinations instead of Midjourney (lower quality)</div>
              </div>
              <label className="toggle"><input type="checkbox" checked={cfg.use_pollinations || false} onChange={e => update("use_pollinations", e.target.checked)} /><span className="toggle-slider" /></label>
            </div>
          </div>
        </div>
      )}

      {tab === "pinterest" && plan === "pro" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }} className="fade-up">
          <div className="settings-section">
            <div className="settings-header">
              <span>📌</span><h3>Pinterest Integration</h3>
              <span className="badge badge-pro" style={{ marginLeft: "auto" }}>PRO</span>
            </div>
            <div className="settings-body">
              <div>
                <label className="form-label">Pinterest Access Token</label>
                <input className="input" type="password" value={cfg.pinterest_token || ""} onChange={e => update("pinterest_token", e.target.value)} placeholder="Your Pinterest API access token..." />
                <Hint>Get your access token from developers.pinterest.com → My Apps → Create App.</Hint>
              </div>
              <div className="setting-row">
                <div className="setting-info">
                  <div className="setting-name">Auto-pin after publish</div>
                  <div className="setting-desc">Automatically create a Pinterest pin when an article is published</div>
                </div>
                <label className="toggle"><input type="checkbox" checked={cfg.auto_pin || false} onChange={e => update("auto_pin", e.target.checked)} /><span className="toggle-slider" /></label>
              </div>
              <div>
                <label className="form-label">Pin Delay (minutes after publish)</label>
                <input className="input" type="number" value={cfg.pin_delay_min || 0} min={0} max={1440} onChange={e => update("pin_delay_min", +e.target.value)} style={{ width: 120 }} />
                <Hint>Set to 0 to pin immediately. Up to 1440 minutes (24 hours) delay supported.</Hint>
              </div>
            </div>
          </div>

          <div className="settings-section">
            <div className="settings-header"><span>💬</span><h3>Pinterest Prompt</h3></div>
            <div className="settings-body">
              <div>
                <div className="alert alert-info" style={{ marginBottom: 12 }}>
                  ✦ A separate AI model generates your Pinterest pin content. Use <code style={{ background: "var(--bg3)", padding: "1px 5px", borderRadius: 4 }}>{"{title}"}</code> and <code style={{ background: "var(--bg3)", padding: "1px 5px", borderRadius: 4 }}>{"{url}"}</code> as placeholders.
                </div>
                <div className="prompt-editor">
                  <textarea
                    className="input"
                    style={{ minHeight: 160, fontFamily: "monospace", fontSize: 13 }}
                    value={cfg.pinterest_prompt || ""}
                    onChange={e => update("pinterest_prompt", e.target.value)}
                    placeholder={`Example:\n\nFor the article "{title}" at {url}, generate a Pinterest pin.\nReturn JSON with:\n- pin_title: 60-char max, keyword-rich, engaging\n- pin_description: 150-char max, includes CTA\n- alt_text: descriptive for accessibility\n\nFocus on the primary benefit and use power words.`}
                  />
                  {cfg.pinterest_prompt && <div className="prompt-counter">{estimateTokens(cfg.pinterest_prompt).toLocaleString()} tokens</div>}
                </div>
                {cfg.pinterest_prompt && <TokenCounter text={cfg.pinterest_prompt} limit={1000} />}
              </div>
            </div>
          </div>

          <div className="settings-section">
            <div className="settings-header"><span>📋</span><h3>Default Boards</h3></div>
            <div className="settings-body">
              <div className="alert alert-warn">Connect your Pinterest account above to load your boards.</div>
              <div>
                <label className="form-label">Manual Board IDs (comma-separated)</label>
                <input className="input" value={cfg.pinterest_boards || ""} onChange={e => update("pinterest_boards", e.target.value)} placeholder="board-id-1, board-id-2" />
                <Hint>Find board IDs in the Pinterest URL when viewing a board. Format: username/board-name</Hint>
              </div>
            </div>
          </div>
        </div>
      )}

      <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 24 }}>
        <button className="btn btn-primary" onClick={save}>
          {saved ? "✓ Saved!" : "Save Settings"}
        </button>
        {saved && <span style={{ fontSize: 13, color: "var(--green)" }}>Changes saved successfully</span>}
      </div>
    </div>
  );
}

// ─── HISTORY PAGE ──────────────────────────────────────────────────────────
function HistoryPage({ history, onClear }) {
  const published = history.filter(h => h.status === "published");
  const failed = history.filter(h => h.status === "failed");

  return (
    <div className="fade-up">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
        <div style={{ display: "flex", gap: 16 }}>
          <span style={{ fontSize: 14, color: "var(--text2)" }}><span className="dot dot-green" style={{ marginRight: 6 }} />{published.length} published</span>
          <span style={{ fontSize: 14, color: "var(--text2)" }}><span className="dot dot-red" style={{ marginRight: 6 }} />{failed.length} failed</span>
        </div>
        {history.length > 0 && <button className="btn btn-danger btn-sm" onClick={onClear}>Clear all</button>}
      </div>

      {history.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: "48px 24px" }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>📋</div>
          <div style={{ fontSize: 15, fontWeight: 500, marginBottom: 6 }}>No articles yet</div>
          <div style={{ fontSize: 13, color: "var(--text3)" }}>Generate your first batch to see history here</div>
        </div>
      ) : [...history].reverse().map((h, i) => (
        <div key={i} className="history-item">
          <span className={`dot ${h.status === "published" ? "dot-green" : "dot-red"}`} />
          <div className="history-info">
            <div className="history-title">{h.title}</div>
            <div className="history-meta">{h.time} · {h.status}</div>
          </div>
          <div className="history-actions">
            {h.post_url && (
              <a href={h.post_url} target="_blank" rel="noreferrer" className="btn btn-ghost btn-sm">View →</a>
            )}
            {h.status === "failed" && (
              <span style={{ fontSize: 12, color: "var(--red)", maxWidth: 200, textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                {h.error}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── PINTEREST PAGE (Pro) ──────────────────────────────────────────────────
function PinterestPage({ config, history, plan }) {
  const [selectedBoards, setSelectedBoards] = useState([]);
  const [pinQueue, setPinQueue] = useState([]);
  const [running, setRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const logRef = useRef(null);

  if (plan !== "pro") {
    return (
      <div className="fade-up" style={{ display: "flex", flex: 1, alignItems: "center", justifyContent: "center", minHeight: 400 }}>
        <div style={{ textAlign: "center", maxWidth: 400 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>📌</div>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 22, fontWeight: 700, marginBottom: 8 }}>Pinterest Bot</div>
          <div style={{ fontSize: 14, color: "var(--text2)", lineHeight: 1.7, marginBottom: 24 }}>
            Automatically pin every published article with AI-optimized titles, descriptions, and alt text. Available in the Pro plan.
          </div>
          <button className="btn btn-pro btn-lg">Upgrade to Pro — $40/mo ★</button>
        </div>
      </div>
    );
  }

  const mockBoards = [
    { id: "1", name: "Pregnancy Tips", icon: "🤰" },
    { id: "2", name: "Baby Gear", icon: "👶" },
    { id: "3", name: "Mom Life", icon: "💕" },
    { id: "4", name: "Postpartum", icon: "🌸" },
    { id: "5", name: "Self Care", icon: "🧘" },
    { id: "6", name: "Recipes", icon: "🍳" },
  ];

  function toggleBoard(id) {
    setSelectedBoards(prev => prev.includes(id) ? prev.filter(b => b !== id) : [...prev, id]);
  }

  const addLog = useCallback((msg, type = "info") => {
    const time = new Date().toLocaleTimeString("en", { hour12: false });
    setLogs(prev => [...prev.slice(-100), { msg, type, time }]);
    setTimeout(() => { if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight; }, 50);
  }, []);

  const publishedArticles = history.filter(h => h.status === "published" && h.post_url);

  async function runPinterest() {
    if (!publishedArticles.length) { addLog("No published articles to pin.", "warn"); return; }
    if (!selectedBoards.length) { addLog("Select at least one board.", "warn"); return; }
    setRunning(true);
    for (const article of publishedArticles) {
      addLog(`Processing: ${article.title}`, "info");
      try {
        const pinContent = await callClaude(
          "You are a Pinterest content expert. Return only valid JSON with keys: pin_title (max 60 chars), pin_description (max 150 chars, include CTA), alt_text (descriptive).",
          (config.pinterest_prompt || "Generate Pinterest pin content for: {title} at {url}")
            .replace("{title}", article.title)
            .replace("{url}", article.post_url || "")
        );
        let parsed;
        try { parsed = JSON.parse(pinContent); } catch { parsed = { pin_title: article.title, pin_description: "Check out this article!", alt_text: article.title }; }
        addLog(`✓ Generated: "${parsed.pin_title}"`, "ok");
        for (const boardId of selectedBoards) {
          const board = mockBoards.find(b => b.id === boardId);
          addLog(`  → Pinning to ${board?.name || boardId}...`, "info");
          await new Promise(r => setTimeout(r, 800));
          addLog(`  ✓ Pinned!`, "ok");
        }
      } catch (e) {
        addLog(`✗ Error: ${e.message}`, "err");
      }
    }
    addLog("Pinterest batch complete!", "ok");
    setRunning(false);
  }

  return (
    <div className="fade-up">
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
        <div className="card">
          <div style={{ fontFamily: "var(--font-display)", fontSize: 15, fontWeight: 600, marginBottom: 6 }}>Select Boards</div>
          <Hint style={{ marginBottom: 12 }}>Choose which Pinterest boards to post to</Hint>
          <div className="board-grid" style={{ marginTop: 14 }}>
            {mockBoards.map(b => (
              <div
                key={b.id}
                className={`board-item ${selectedBoards.includes(b.id) ? "selected" : ""}`}
                onClick={() => toggleBoard(b.id)}
              >
                <div className="board-icon">{b.icon}</div>
                <div className="board-name">{b.name}</div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div className="card">
            <div style={{ fontFamily: "var(--font-display)", fontSize: 15, fontWeight: 600, marginBottom: 12 }}>Ready to Pin</div>
            <div style={{ fontSize: 28, fontWeight: 700, fontFamily: "var(--font-display)", marginBottom: 4 }}>{publishedArticles.length}</div>
            <div style={{ fontSize: 13, color: "var(--text3)" }}>published articles in queue</div>
            <div className="divider" />
            <div style={{ fontSize: 13, color: "var(--text2)" }}>{selectedBoards.length} board{selectedBoards.length !== 1 ? "s" : ""} selected</div>
          </div>

          <div className="alert alert-info" style={{ fontSize: 13 }}>
            ✦ Each pin uses your custom prompt to generate AI-optimized title, description, and alt text. The article's featured image is used as the pin image.
          </div>

          <button
            className="btn btn-pro"
            style={{ width: "100%", justifyContent: "center", padding: "14px" }}
            onClick={runPinterest}
            disabled={running || !publishedArticles.length || !selectedBoards.length}
          >
            {running ? <><span className="spinner spinner-sm" /> Pinning...</> : `📌 Pin ${publishedArticles.length} Articles`}
          </button>
        </div>
      </div>

      <div className="card">
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
          <span className={`dot ${running ? "dot-green dot-pulse" : "dot-yellow"}`} />
          <span style={{ fontFamily: "var(--font-display)", fontSize: 15, fontWeight: 600 }}>Pinterest Log</span>
        </div>
        <div className="process-log" ref={logRef}>
          {logs.length === 0
            ? <div style={{ color: "var(--text3)", fontFamily: "var(--font)" }}>Select boards and click Pin to start...</div>
            : logs.map((l, i) => (
              <div key={i} className="log-line">
                <span className="log-time">[{l.time}]</span>
                <span className={`log-${l.type}`}>{l.msg}</span>
              </div>
            ))
          }
        </div>
      </div>
    </div>
  );
}

// ─── PREVIEW PAGE ──────────────────────────────────────────────────────────
function PreviewPage({ config }) {
  const [title, setTitle] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState("");
  const [error, setError] = useState("");

  async function generate() {
    if (!title || !config.gemini_key) return;
    setLoading(true); setError(""); setResult("");
    try {
      const prompt = config.custom_prompt || "Write a comprehensive HTML article about: {title}. Return only clean HTML.";
      const res = await callClaude(
        "You are a helpful content writer. Return only clean HTML content.",
        prompt.replace("{title}", title),
        1000
      );
      setResult(res);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fade-up">
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ fontFamily: "var(--font-display)", fontSize: 15, fontWeight: 600, marginBottom: 12 }}>Preview Article</div>
        <div style={{ display: "flex", gap: 12 }}>
          <input className="input" value={title} onChange={e => setTitle(e.target.value)} placeholder="Enter a test title..." style={{ flex: 1 }} onKeyDown={e => e.key === "Enter" && generate()} />
          <button className="btn btn-primary" onClick={generate} disabled={loading || !title || !config.gemini_key}>
            {loading ? <><span className="spinner spinner-sm" /> Generating...</> : "Preview →"}
          </button>
        </div>
        {!config.gemini_key && <div className="alert alert-warn" style={{ marginTop: 12 }}>Configure an AI key in Settings first.</div>}
        {error && <div className="alert alert-err" style={{ marginTop: 12 }}>{error}</div>}
      </div>

      {result && (
        <div className="card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
            <div style={{ fontSize: 15, fontWeight: 600 }}>Preview Result</div>
            <span style={{ fontSize: 12, color: "var(--text3)" }}>~{result.split(" ").length} words</span>
          </div>
          <div
            style={{ background: "var(--bg3)", borderRadius: "var(--radius)", padding: 24, maxHeight: 600, overflowY: "auto", color: "var(--text)", lineHeight: 1.7 }}
            dangerouslySetInnerHTML={{ __html: result }}
          />
        </div>
      )}
    </div>
  );
}

// ─── APP SHELL ─────────────────────────────────────────────────────────────
function AppShell({ user, onLogout }) {
  const [page, setPage] = useState("dashboard");
  const [config, setConfig] = useState(() => {
    try { return JSON.parse(localStorage.getItem("nicheflow_config") || "{}"); } catch { return {}; }
  });
  const [history, setHistory] = useState(() => {
    try { return JSON.parse(localStorage.getItem("nicheflow_history") || "[]"); } catch { return []; }
  });
  const [plan] = useState("pro"); // Would come from Supabase in production

  function saveConfig(cfg) {
    setConfig(cfg);
    localStorage.setItem("nicheflow_config", JSON.stringify(cfg));
  }

  function addHistory(item) {
    const next = [...history, item];
    setHistory(next);
    localStorage.setItem("nicheflow_history", JSON.stringify(next));
  }

  function clearHistory() {
    setHistory([]);
    localStorage.removeItem("nicheflow_history");
  }

  const email = user?.user?.email || user?.email || "user@example.com";
  const avatarLetter = email[0]?.toUpperCase() || "U";

  const navItems = [
    { id: "dashboard", icon: "dashboard", label: "Dashboard" },
    { id: "generate", icon: "zap", label: "Generate" },
    { id: "preview", icon: "eye", label: "Preview" },
    { id: "history", icon: "history", label: "History" },
    { id: "pinterest", icon: "pinterest", label: "Pinterest", pro: true },
    { id: "settings", icon: "settings", label: "Settings" },
  ];

  const pageTitle = {
    dashboard: ["Dashboard", "Welcome back! Here's your overview."],
    generate: ["Generate Articles", "Paste titles and let the AI handle the rest."],
    preview: ["Preview", "Test your article style before publishing a batch."],
    history: ["History", "All articles you've generated and published."],
    pinterest: ["Pinterest Bot", "Auto-pin your articles with AI-optimized content."],
    settings: ["Settings", "Configure your API keys, prompts, and integrations."],
  };

  const [title, subtitle] = pageTitle[page] || ["", ""];

  return (
    <div className="app-layout">
      <style>{css}</style>
      <aside className="sidebar">
        <div className="sidebar-logo">NicheFlow AI</div>
        <nav className="sidebar-nav">
          <div className="sidebar-section">Main</div>
          {navItems.map(item => (
            <button
              key={item.id}
              className={`nav-item ${page === item.id ? "active" : ""}`}
              onClick={() => setPage(item.id)}
            >
              <Icon name={item.icon} />
              {item.label}
              {item.pro && <span className="nav-badge">PRO</span>}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="user-pill">
            <div className="user-avatar">{avatarLetter}</div>
            <div className="user-info">
              <div className="user-email">{email}</div>
              <div className="user-plan" style={{ color: plan === "pro" ? "var(--pro)" : "var(--accent2)" }}>
                {plan === "pro" ? "★ Pro" : "Basic"}
              </div>
            </div>
          </div>
          <button className="nav-item" onClick={onLogout} style={{ marginTop: 8, color: "var(--text3)" }}>
            <Icon name="logout" /> Sign out
          </button>
        </div>
      </aside>

      <main className="main-content">
        <div className="page-header">
          <div style={{ paddingBottom: 20 }}>
            <h1 className="page-title">{title}</h1>
            <p className="page-sub">{subtitle}</p>
          </div>
        </div>
        <div className="page-body">
          {page === "dashboard" && <Dashboard history={history} />}
          {page === "generate" && <GeneratePage config={config} onHistoryUpdate={addHistory} plan={plan} />}
          {page === "preview" && <PreviewPage config={config} />}
          {page === "history" && <HistoryPage history={history} onClear={clearHistory} />}
          {page === "pinterest" && <PinterestPage config={config} history={history} plan={plan} />}
          {page === "settings" && <SettingsPage config={config} onSave={saveConfig} plan={plan} />}
        </div>
      </main>
    </div>
  );
}

// ─── ROOT ───────────────────────────────────────────────────────────────────
export default function NicheFlowAI() {
  const [view, setView] = useState("landing"); // landing | login | signup | app
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Check for existing session
    const stored = localStorage.getItem("nicheflow_user");
    if (stored) {
      try { const u = JSON.parse(stored); setUser(u); setView("app"); } catch {}
    }
  }, []);

  function handleAuthSuccess(userData) {
    localStorage.setItem("nicheflow_user", JSON.stringify(userData));
    setUser(userData);
    setView("app");
  }

  function handleLogout() {
    localStorage.removeItem("nicheflow_user");
    setUser(null);
    setView("landing");
  }

  if (view === "app" && user) {
    return <AppShell user={user} onLogout={handleLogout} />;
  }

  if (view === "login" || view === "signup") {
    return (
      <AuthPage
        mode={view}
        onSuccess={handleAuthSuccess}
        onSwitch={setView}
        onBack={() => setView("landing")}
      />
    );
  }

  return (
    <LandingPage
      onLogin={() => setView("login")}
      onSignup={() => setView("signup")}
    />
  );
}