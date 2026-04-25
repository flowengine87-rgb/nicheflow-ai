import { useState, useEffect, useRef, useCallback } from "react";

// ─── Config ────────────────────────────────────────────────────────────────
const SUPABASE_URL = "https://gfulpvqqpakcgubkilwc.supabase.co";
const SUPABASE_KEY = "sb_publishable_U9zJp_BBd-jkJCwvGimNmw_E4NyynFN";
const API_URL = "https://web-production-1f143.up.railway.app";

// ── GUMROAD checkout links ──
const CHECKOUT_BASIC = "https://nicheflowai.gumroad.com/l/nicheflow-ai";
const CHECKOUT_PRO   = "https://nicheflowai.gumroad.com/l/ysrzyv";

// ── ADMIN: your email — bypasses trial gate, always has full Pro access locally
const ADMIN_EMAIL = "flowengine87@gmail.com";

const TRIAL_DAYS = 2;

// ─── Auth helpers ──────────────────────────────────────────────────────────
async function supaSignup(email, password) {
  const res = await fetch(`${SUPABASE_URL}/auth/v1/signup`, {
    method: "POST",
    headers: { apikey: SUPABASE_KEY, "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, options: { emailRedirectTo: null } }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error_description || data.msg || "Signup failed");
  return data;
}

async function supaLogin(email, password) {
  const res = await fetch(`${SUPABASE_URL}/auth/v1/token?grant_type=password`, {
    method: "POST",
    headers: { apikey: SUPABASE_KEY, "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error_description || data.msg || "Login failed");
  return data;
}

async function apiCall(path, opts = {}) {
  const token = getStoredToken();
  const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_URL}${path}`, { ...opts, headers });
  return res;
}

function getStoredToken() {
  try { return JSON.parse(localStorage.getItem("nicheflow_user") || "{}").access_token || ""; } catch { return ""; }
}
function getStoredConfig() {
  try { return JSON.parse(localStorage.getItem("nicheflow_config") || "{}"); } catch { return {}; }
}
function estimateTokens(text) { return Math.ceil(text.length / 4); }

function getDaysLeft(createdAt) {
  if (!createdAt) return 0;
  const diff = (Date.now() - new Date(createdAt).getTime()) / (1000 * 60 * 60 * 24);
  return Math.max(0, TRIAL_DAYS - Math.floor(diff));
}
function isTrialExpired(createdAt) { return getDaysLeft(createdAt) === 0; }

function getSubDaysLeft(planExpires) {
  if (!planExpires) return null;
  const diff = (new Date(planExpires).getTime() - Date.now()) / (1000 * 60 * 60 * 24);
  return Math.max(0, Math.ceil(diff));
}

// ─── LOGO SVG ─────────────────────────────────────────────────────────────
function Logo({ size = 28 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg" style={{flexShrink:0,display:"block"}}>
      <defs>
        <linearGradient id="nfGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#6366f1"/>
          <stop offset="100%" stopColor="#a855f7"/>
        </linearGradient>
      </defs>
      <rect width="44" height="44" rx="11" fill="url(#nfGrad)"/>
      <rect x="9" y="17" width="15" height="2.8" rx="1.4" fill="white" opacity="0.95"/>
      <rect x="9" y="22" width="11" height="2.8" rx="1.4" fill="white" opacity="0.7"/>
      <rect x="9" y="27" width="13" height="2.8" rx="1.4" fill="white" opacity="0.5"/>
      <path d="M31 33V21" stroke="white" strokeWidth="2.8" strokeLinecap="round"/>
      <path d="M27 25L31 20L35 25" stroke="white" strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round"/>
      <circle cx="31" cy="13" r="4" fill="#fbbf24"/>
      <text x="31" y="17" textAnchor="middle" fontSize="8" fill="white" fontWeight="bold">✦</text>
    </svg>
  );
}

// ─── CSS ───────────────────────────────────────────────────────────────────
const css = `
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
:root{
  --bg:#08090d;--bg2:#0e1018;--bg3:#141720;--bg4:#1a1f2e;
  --border:rgba(255,255,255,0.07);--border2:rgba(255,255,255,0.12);
  --text:#f0f1f5;--text2:#9ba3b8;--text3:#5a6278;
  --accent:#6366f1;--accent2:#818cf8;--accent-dim:rgba(99,102,241,0.15);--accent-glow:rgba(99,102,241,0.3);
  --pro:#f59e0b;--pro-dim:rgba(245,158,11,0.15);
  --green:#10b981;--green-dim:rgba(16,185,129,0.12);
  --red:#ef4444;--red-dim:rgba(239,68,68,0.12);
  --radius:12px;--radius-lg:18px;--radius-xl:24px;
  --font:'DM Sans',sans-serif;--font-display:'Syne',sans-serif;
}
html{scroll-behavior:smooth;}
body{font-family:var(--font);background:var(--bg);color:var(--text);min-height:100vh;overflow-x:hidden;}
::-webkit-scrollbar{width:5px;}::-webkit-scrollbar-track{background:var(--bg2);}::-webkit-scrollbar-thumb{background:var(--border2);border-radius:3px;}
@keyframes fadeUp{from{opacity:0;transform:translateY(18px);}to{opacity:1;transform:translateY(0);}}
@keyframes spin{to{transform:rotate(360deg);}}
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:.5;}}
@keyframes glow{0%,100%{box-shadow:0 0 20px var(--accent-glow);}50%{box-shadow:0 0 40px var(--accent-glow),0 0 80px rgba(99,102,241,.2);}}
@keyframes gradMove{0%{background-position:0% 50%;}50%{background-position:100% 50%;}100%{background-position:0% 50%;}}
@keyframes slideIn{from{opacity:0;transform:translateX(-10px);}to{opacity:1;transform:translateX(0);}}
@keyframes fadeIn{from{opacity:0;}to{opacity:1;}}
.fade-up{animation:fadeUp .45s ease both;}
.fade-up-d1{animation:fadeUp .45s .08s ease both;}
.fade-up-d2{animation:fadeUp .45s .16s ease both;}
.fade-up-d3{animation:fadeUp .45s .24s ease both;}
.fade-up-d4{animation:fadeUp .45s .32s ease both;}

.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:10px 22px;border-radius:var(--radius);font-family:var(--font);font-size:14px;font-weight:500;cursor:pointer;border:none;transition:all .2s;text-decoration:none;white-space:nowrap;}
.btn-primary{background:var(--accent);color:#fff;}.btn-primary:hover{background:#4f46e5;transform:translateY(-1px);box-shadow:0 4px 20px var(--accent-glow);}
.btn-ghost{background:transparent;color:var(--text2);border:1px solid var(--border);}.btn-ghost:hover{border-color:var(--border2);color:var(--text);background:var(--bg3);}
.btn-pro{background:linear-gradient(135deg,#f59e0b,#d97706);color:#fff;}.btn-pro:hover{transform:translateY(-1px);box-shadow:0 4px 20px rgba(245,158,11,.4);}
.btn-danger{background:var(--red-dim);color:var(--red);border:1px solid rgba(239,68,68,.2);}.btn-danger:hover{background:var(--red);color:#fff;}
.btn-lg{padding:14px 32px;font-size:16px;border-radius:var(--radius-lg);}
.btn-sm{padding:7px 14px;font-size:13px;}
.btn:disabled{opacity:.45;cursor:not-allowed;transform:none!important;box-shadow:none!important;}

.input{width:100%;padding:11px 14px;background:var(--bg3);border:1px solid var(--border);border-radius:var(--radius);color:var(--text);font-family:var(--font);font-size:14px;transition:border-color .2s,box-shadow .2s;outline:none;}
.input:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-dim);}
.input::placeholder{color:var(--text3);}
textarea.input{resize:vertical;min-height:100px;line-height:1.6;}
select.input{cursor:pointer;}

.card{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius-lg);padding:24px;}
.hint{font-size:12px;color:var(--text3);margin-top:5px;display:flex;align-items:flex-start;gap:5px;line-height:1.5;}
.divider{height:1px;background:var(--border);margin:20px 0;}

.spinner{width:16px;height:16px;border:2px solid rgba(255,255,255,.2);border-top-color:#fff;border-radius:50%;animation:spin .7s linear infinite;flex-shrink:0;}
.spinner-accent{border-color:var(--accent-dim);border-top-color:var(--accent);}
.spinner-lg{width:32px;height:32px;border-width:3px;}

.badge{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:500;}
.badge-pro{background:var(--pro-dim);color:var(--pro);border:1px solid rgba(245,158,11,.2);}
.badge-basic{background:var(--accent-dim);color:var(--accent2);border:1px solid rgba(99,102,241,.2);}
.badge-admin{background:rgba(239,68,68,.15);color:#ef4444;border:1px solid rgba(239,68,68,.25);}

.alert{display:flex;align-items:flex-start;gap:10px;padding:12px 16px;border-radius:var(--radius);font-size:13px;margin-bottom:12px;line-height:1.5;}
.alert-warn{background:rgba(245,158,11,.1);color:var(--pro);border:1px solid rgba(245,158,11,.2);}
.alert-ok{background:var(--green-dim);color:var(--green);border:1px solid rgba(16,185,129,.2);}
.alert-err{background:var(--red-dim);color:var(--red);border:1px solid rgba(239,68,68,.2);}
.alert-info{background:var(--accent-dim);color:var(--accent2);border:1px solid rgba(99,102,241,.2);}

.token-bar{padding:8px 12px;border-radius:var(--radius);font-size:12px;margin-top:6px;}
.token-ok{background:var(--green-dim);color:var(--green);border:1px solid rgba(16,185,129,.2);}
.token-warn{background:rgba(245,158,11,.1);color:var(--pro);border:1px solid rgba(245,158,11,.2);}
.token-over{background:var(--red-dim);color:var(--red);border:1px solid rgba(239,68,68,.2);animation:pulse 1.5s ease-in-out infinite;}
.progress{height:4px;background:var(--bg4);border-radius:2px;overflow:hidden;margin-top:6px;}
.progress-fill{height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2));border-radius:2px;transition:width .4s ease;}

.toggle{position:relative;width:40px;height:22px;flex-shrink:0;}
.toggle input{opacity:0;width:0;height:0;}
.toggle-slider{position:absolute;cursor:pointer;inset:0;background:var(--bg4);border-radius:11px;border:1px solid var(--border2);transition:.2s;}
.toggle-slider::before{content:'';position:absolute;height:16px;width:16px;left:2px;top:2px;background:var(--text3);border-radius:50%;transition:.2s;}
.toggle input:checked+.toggle-slider{background:var(--accent);border-color:var(--accent);}
.toggle input:checked+.toggle-slider::before{transform:translateX(18px);background:#fff;}

.tabs{display:flex;gap:4px;background:var(--bg3);padding:4px;border-radius:var(--radius);border:1px solid var(--border);width:fit-content;margin-bottom:20px;flex-wrap:wrap;}
.tab{padding:8px 16px;border-radius:calc(var(--radius) - 2px);font-size:13px;font-weight:500;cursor:pointer;color:var(--text3);border:none;background:transparent;transition:all .2s;font-family:var(--font);}
.tab.active{background:var(--bg);color:var(--text);box-shadow:0 1px 8px rgba(0,0,0,.3);}
.tab:hover:not(.active){color:var(--text2);}

.dot{width:8px;height:8px;border-radius:50%;display:inline-block;flex-shrink:0;}
.dot-green{background:var(--green);box-shadow:0 0 6px var(--green);}
.dot-red{background:var(--red);}
.dot-yellow{background:var(--pro);}
.dot-pulse{animation:pulse 2s ease-in-out infinite;}

.process-log{background:var(--bg);border:1px solid var(--border);border-radius:var(--radius-lg);padding:16px 20px;max-height:280px;overflow-y:auto;font-family:'Courier New',monospace;font-size:12px;line-height:1.9;}
.log-line{display:flex;align-items:flex-start;gap:8px;animation:slideIn .2s ease;}
.log-time{color:var(--text3);flex-shrink:0;}
.log-ok{color:var(--green);}
.log-err{color:var(--red);}
.log-info{color:var(--accent2);}
.log-warn{color:var(--pro);}

.settings-section{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius-lg);overflow:hidden;margin-bottom:18px;}
.settings-header{padding:16px 22px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:10px;}
.settings-header h3{font-size:14px;font-weight:600;}
.settings-body{padding:20px 22px;display:flex;flex-direction:column;gap:18px;}
.setting-row{display:flex;align-items:flex-start;justify-content:space-between;gap:24px;}
.setting-info{flex:1;}
.setting-name{font-size:14px;font-weight:500;}
.setting-desc{font-size:12px;color:var(--text3);margin-top:3px;line-height:1.5;}
.form-label{font-size:13px;font-weight:500;color:var(--text2);margin-bottom:6px;display:block;}
.prompt-editor{position:relative;}
.prompt-counter{position:absolute;bottom:10px;right:12px;font-size:11px;color:var(--text3);background:var(--bg3);padding:2px 8px;border-radius:8px;}

.board-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px;margin-top:14px;}
.board-item{background:var(--bg3);border:1px solid var(--border);border-radius:var(--radius);padding:12px;cursor:pointer;transition:all .2s;text-align:center;}
.board-item:hover,.board-item.selected{border-color:var(--accent);background:var(--accent-dim);}

.stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px;}
.stat-card{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius-lg);padding:18px;}
.stat-card-num{font-family:var(--font-display);font-size:26px;font-weight:700;}
.stat-card-label{font-size:12px;color:var(--text3);margin-top:4px;}

.history-item{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius-lg);padding:14px 18px;display:flex;align-items:center;gap:14px;margin-bottom:8px;transition:border-color .15s;}
.history-item:hover{border-color:var(--border2);}
.history-title{font-size:14px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.history-meta{font-size:12px;color:var(--text3);margin-top:2px;}

.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:300;display:flex;align-items:center;justify-content:center;padding:20px;animation:fadeIn .2s ease;}
.modal{background:var(--bg2);border:1px solid var(--border2);border-radius:var(--radius-xl);padding:32px;max-width:600px;width:100%;max-height:85vh;overflow-y:auto;animation:fadeUp .25s ease;position:relative;}
.modal-close{position:absolute;top:16px;right:16px;background:var(--bg3);border:1px solid var(--border);border-radius:8px;width:30px;height:30px;display:flex;align-items:center;justify-content:center;cursor:pointer;color:var(--text3);font-size:14px;font-family:var(--font);}
.modal-close:hover{color:var(--text);background:var(--bg4);}

.pin-preview{background:var(--bg3);border:1px solid var(--border);border-radius:var(--radius-lg);overflow:hidden;margin-bottom:16px;}
.pin-img{width:100%;height:180px;object-fit:cover;display:block;background:var(--bg4);}
.pin-body{padding:14px;}
.pin-title{font-size:14px;font-weight:600;margin-bottom:6px;line-height:1.4;}
.pin-desc{font-size:12px;color:var(--text2);line-height:1.5;margin-bottom:8px;}
.pin-tags{display:flex;flex-wrap:wrap;gap:5px;}
.pin-tag{background:var(--accent-dim);color:var(--accent2);padding:2px 8px;border-radius:10px;font-size:11px;}

.doc-section{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius-lg);padding:24px;margin-bottom:16px;}
.doc-section h3{font-family:var(--font-display);font-size:16px;font-weight:600;margin-bottom:12px;display:flex;align-items:center;gap:8px;}
.doc-step{display:flex;gap:14px;margin-bottom:14px;align-items:flex-start;}
.doc-step-num{width:28px;height:28px;border-radius:50%;background:var(--accent-dim);color:var(--accent2);font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;border:1px solid rgba(99,102,241,.2);}
.doc-step-text{flex:1;}
.doc-step-title{font-size:14px;font-weight:600;margin-bottom:3px;}
.doc-step-desc{font-size:13px;color:var(--text2);line-height:1.6;}
code{background:var(--bg3);border:1px solid var(--border);padding:1px 6px;border-radius:5px;font-size:12px;font-family:'Courier New',monospace;color:var(--accent2);}
pre{background:var(--bg);border:1px solid var(--border);border-radius:var(--radius);padding:14px;font-size:12px;line-height:1.7;overflow-x:auto;color:var(--text2);font-family:'Courier New',monospace;margin:10px 0;}

/* ── Policy pages ─────────────────────────────── */
.policy-wrap{min-height:100vh;background:var(--bg);padding:40px 24px 80px;}
.policy-inner{max-width:780px;margin:0 auto;}
.policy-inner h1{font-family:var(--font-display);font-size:32px;font-weight:800;letter-spacing:-1px;margin-bottom:6px;}
.policy-date{font-size:13px;color:var(--text3);margin-bottom:36px;display:block;}
.policy-inner h2{font-family:var(--font-display);font-size:17px;font-weight:700;margin:30px 0 10px;color:var(--text);padding-top:8px;border-top:1px solid var(--border);}
.policy-inner p{font-size:14px;color:var(--text2);line-height:1.85;margin-bottom:12px;}
.policy-inner ul{padding-left:22px;margin-bottom:14px;}
.policy-inner ul li{font-size:14px;color:var(--text2);line-height:1.85;margin-bottom:5px;}
.policy-inner a{color:var(--accent2);text-decoration:underline;}
.policy-inner a:hover{color:var(--text);}
.policy-back-row{display:flex;align-items:center;gap:12px;margin-bottom:32px;}

.landing{min-height:100vh;background:var(--bg);}
.nav{position:fixed;top:0;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:14px 48px;background:rgba(8,9,13,.9);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);}
.nav-brand{display:flex;align-items:center;gap:10px;font-family:var(--font-display);font-size:17px;font-weight:700;background:linear-gradient(135deg,var(--accent2),#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.hero{padding:140px 48px 100px;max-width:1100px;margin:0 auto;position:relative;z-index:1;}
.hero h1{font-family:var(--font-display);font-size:clamp(42px,6vw,72px);font-weight:800;line-height:1.05;letter-spacing:-2px;margin-bottom:22px;}
.hero h1 .grad{background:linear-gradient(135deg,var(--accent2) 0%,#c084fc 50%,#f472b6 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-size:200% 200%;animation:gradMove 4s ease infinite;}
.hero p{font-size:17px;color:var(--text2);line-height:1.7;max-width:520px;margin-bottom:36px;font-weight:300;}
.features-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;}
.feature-card{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius-lg);padding:26px;transition:border-color .2s,transform .2s;position:relative;overflow:hidden;}
.feature-card:hover{border-color:var(--border2);transform:translateY(-3px);}
.pricing-grid{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:50px;}
.plan-card{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius-xl);padding:34px;position:relative;overflow:hidden;transition:transform .2s;}
.plan-card:hover{transform:translateY(-4px);}
.plan-card.featured{border-color:var(--accent);background:linear-gradient(145deg,var(--bg2),rgba(99,102,241,.05));}
.plan-card.featured::before{content:'Most Popular';position:absolute;top:18px;right:18px;background:var(--accent);color:#fff;font-size:11px;font-weight:600;padding:4px 10px;border-radius:20px;}
.plan-features{list-style:none;display:flex;flex-direction:column;gap:10px;margin-bottom:28px;}
.plan-features li{display:flex;align-items:center;gap:10px;font-size:14px;color:var(--text2);}
.plan-features li::before{content:'✓';width:18px;height:18px;background:var(--green-dim);color:var(--green);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;flex-shrink:0;}

.app-layout{display:flex;min-height:100vh;}
.sidebar{width:236px;flex-shrink:0;background:var(--bg2);border-right:1px solid var(--border);display:flex;flex-direction:column;position:fixed;top:0;left:0;bottom:0;z-index:50;}
.sidebar-logo{padding:16px 18px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:10px;}
.sidebar-logo span{font-family:var(--font-display);font-size:15px;font-weight:700;background:linear-gradient(135deg,var(--accent2),#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.sidebar-nav{flex:1;padding:10px 8px;overflow-y:auto;}
.sidebar-section{font-size:10px;font-weight:600;color:var(--text3);letter-spacing:1.5px;text-transform:uppercase;padding:14px 10px 5px;}
.nav-item{display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:var(--radius);cursor:pointer;font-size:14px;color:var(--text2);transition:all .15s;border:none;background:none;width:100%;font-family:var(--font);position:relative;text-align:left;}
.nav-item:hover{background:var(--bg3);color:var(--text);}
.nav-item.active{background:var(--accent-dim);color:var(--accent2);}
.nav-item.active::before{content:'';position:absolute;left:0;top:50%;transform:translateY(-50%);width:3px;height:60%;background:var(--accent);border-radius:0 3px 3px 0;}
.nav-item .nav-badge{margin-left:auto;background:var(--pro-dim);color:var(--pro);font-size:10px;padding:2px 6px;border-radius:10px;}
.sidebar-footer{padding:12px 8px;border-top:1px solid var(--border);}
.user-pill{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:var(--radius);background:var(--bg3);}
.user-avatar{width:30px;height:30px;border-radius:50%;background:linear-gradient(135deg,var(--accent),#c084fc);display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:600;color:#fff;flex-shrink:0;}
.user-email{font-size:12px;color:var(--text3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.user-plan{font-size:11px;font-weight:600;}
.main-content{margin-left:236px;flex:1;min-height:100vh;}
.page-header{padding:24px 32px 0;border-bottom:1px solid var(--border);}
.page-title{font-family:var(--font-display);font-size:22px;font-weight:700;}
.page-sub{font-size:14px;color:var(--text2);margin-top:4px;margin-bottom:18px;}
.page-body{padding:24px 32px;}

.auth-page{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px;background:var(--bg);position:relative;}
.auth-page::before{content:'';position:fixed;inset:0;background:radial-gradient(ellipse 60% 50% at 30% 20%,rgba(99,102,241,.1) 0%,transparent 60%),radial-gradient(ellipse 50% 40% at 75% 70%,rgba(139,92,246,.07) 0%,transparent 60%);pointer-events:none;}
.auth-card{width:100%;max-width:400px;background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius-xl);padding:36px;position:relative;z-index:1;}
.auth-brand{display:flex;align-items:center;gap:10px;margin-bottom:22px;}
.auth-brand span{font-family:var(--font-display);font-size:18px;font-weight:700;background:linear-gradient(135deg,var(--accent2),#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.mesh-bg::before{content:'';position:fixed;inset:0;background:radial-gradient(ellipse 60% 50% at 30% 20%,rgba(99,102,241,.1) 0%,transparent 60%),radial-gradient(ellipse 50% 40% at 75% 70%,rgba(139,92,246,.07) 0%,transparent 60%);pointer-events:none;z-index:0;}

.upgrade-banner{background:linear-gradient(135deg,rgba(245,158,11,.15),rgba(245,158,11,.05));border:1px solid rgba(245,158,11,.25);border-radius:var(--radius-lg);padding:16px 20px;display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:20px;}
.upgrade-banner-text{font-size:14px;color:var(--text2);}.upgrade-banner-text strong{color:var(--pro);}

.top-bar{padding:10px 28px;display:flex;align-items:center;justify-content:space-between;gap:14px;font-size:13px;}
.top-bar-trial-expired{background:rgba(239,68,68,0.18);border-bottom:1px solid rgba(239,68,68,0.3);color:var(--red);}
.top-bar-trial-warn{background:rgba(245,158,11,0.13);border-bottom:1px solid rgba(245,158,11,0.22);color:var(--pro);}
.top-bar-trial-ok{background:rgba(16,185,129,0.08);border-bottom:1px solid rgba(16,185,129,0.15);color:var(--green);}
.top-bar-sub-ok{background:rgba(16,185,129,0.08);border-bottom:1px solid rgba(16,185,129,0.15);color:var(--green);}
.top-bar-sub-warn{background:rgba(245,158,11,0.13);border-bottom:1px solid rgba(245,158,11,0.22);color:var(--pro);}
.top-bar-sub-expired{background:rgba(239,68,68,0.18);border-bottom:1px solid rgba(239,68,68,0.3);color:var(--red);}
.top-bar-admin{background:rgba(239,68,68,0.1);border-bottom:1px solid rgba(239,68,68,0.2);color:#ef4444;}

.footer-link-btn{background:none;border:none;color:var(--text3);cursor:pointer;font-family:var(--font);font-size:13px;padding:0;transition:color .15s;text-decoration:none;}
.footer-link-btn:hover{color:var(--text2);}

@media(max-width:900px){
  .nav{padding:14px 20px;}
  .features-grid,.pricing-grid,.stat-grid{grid-template-columns:1fr;}
  .sidebar{transform:translateX(-100%);}
  .main-content{margin-left:0;}
}
`;

// ─── Token Counter ─────────────────────────────────────────────────────────
function TokenCounter({ text, limit = 2000 }) {
  const n = estimateTokens(text);
  const pct = n / limit;
  const cls = pct > 1 ? "token-over" : pct > 0.8 ? "token-warn" : "token-ok";
  return (
    <div className={`token-bar ${cls}`}>
      <div>{pct > 1 ? `⚠️ Over limit! ${n.toLocaleString()} / ${limit.toLocaleString()} tokens` : pct > 0.8 ? `⚠️ ${n.toLocaleString()} / ${limit.toLocaleString()} tokens` : `✓ ${n.toLocaleString()} / ${limit.toLocaleString()} tokens`}</div>
      <div className="progress"><div className="progress-fill" style={{ width: `${Math.min(pct*100,100)}%`, background: pct > 1 ? "var(--red)" : pct > 0.8 ? "var(--pro)" : undefined }} /></div>
    </div>
  );
}

function Hint({ children }) {
  return <p className="hint"><span style={{ flexShrink: 0 }}>ℹ</span><span>{children}</span></p>;
}

// ─── TOP BAR ──────────────────────────────────────────────────────────────
function TopBar({ createdAt, plan, planExpires, onUpgrade, isAdmin }) {
  if (isAdmin) {
    return (
      <div className="top-bar top-bar-admin">
        <span>🔧 <strong>Admin mode</strong> — trial and plan restrictions bypassed</span>
      </div>
    );
  }
  if (plan === "pro" && planExpires) {
    const daysLeft = getSubDaysLeft(planExpires);
    if (daysLeft === null) return null;
    const expired = daysLeft === 0;
    const cls = daysLeft <= 3 ? "top-bar-sub-warn" : "top-bar-sub-ok";
    return (
      <div className={`top-bar ${expired ? "top-bar-sub-expired" : cls}`}>
        <span>
          {expired
            ? "⚠️ Your Pro subscription has expired — renew to keep Pinterest access"
            : daysLeft <= 3
            ? `⏰ Pro renews in ${daysLeft} day${daysLeft !== 1 ? "s" : ""} — make sure your payment is up to date`
            : `★ Pro plan active — ${daysLeft} day${daysLeft !== 1 ? "s" : ""} until renewal`}
        </span>
        {expired && (
          <button className="btn btn-pro btn-sm" onClick={() => onUpgrade("pro")} style={{padding:"5px 12px",fontSize:12}}>Renew Pro →</button>
        )}
      </div>
    );
  }
  if (plan !== "pro") {
    const daysLeft = getDaysLeft(createdAt);
    const expired = daysLeft === 0;
    const cls = expired ? "top-bar-trial-expired" : daysLeft === 1 ? "top-bar-trial-warn" : "top-bar-trial-ok";
    const msg = expired
      ? "⚠️ Your 2-day free trial has expired — upgrade to keep publishing"
      : daysLeft === 1
      ? "⏰ Last day of your free trial — upgrade before it expires"
      : `🎉 ${daysLeft} days left in your free trial`;
    return (
      <div className={`top-bar ${cls}`}>
        <span><strong>{msg}</strong></span>
        <div style={{display:"flex",gap:8,flexShrink:0}}>
          <button className="btn btn-ghost btn-sm" onClick={() => onUpgrade("basic")} style={{padding:"5px 12px",fontSize:12,borderColor:"currentColor"}}>Basic $30/mo</button>
          <button className="btn btn-pro btn-sm" onClick={() => onUpgrade("pro")} style={{padding:"5px 12px",fontSize:12}}>Pro $40/mo ★</button>
        </div>
      </div>
    );
  }
  return null;
}

// ─── TRIAL EXPIRED GATE ────────────────────────────────────────────────────
function TrialExpiredGate({ onUpgrade }) {
  return (
    <div style={{display:"flex",alignItems:"center",justifyContent:"center",minHeight:400,padding:24}}>
      <div style={{textAlign:"center",maxWidth:460}}>
        <div style={{fontSize:52,marginBottom:16}}>⏰</div>
        <div style={{fontFamily:"var(--font-display)",fontSize:24,fontWeight:700,marginBottom:8}}>Your free trial has ended</div>
        <p style={{color:"var(--text2)",fontSize:15,lineHeight:1.7,marginBottom:28}}>You had 2 days to try NicheFlow AI for free. Choose a plan below to keep publishing articles and automating your content.</p>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16,marginBottom:12}}>
          <div style={{background:"var(--bg2)",border:"1px solid var(--border)",borderRadius:"var(--radius-lg)",padding:20,textAlign:"left"}}>
            <div style={{fontFamily:"var(--font-display)",fontSize:18,fontWeight:700,marginBottom:4}}>Basic</div>
            <div style={{fontSize:32,fontWeight:800,fontFamily:"var(--font-display)",color:"var(--accent2)",marginBottom:12}}>$30<span style={{fontSize:14,fontWeight:400,color:"var(--text3)"}}>/mo</span></div>
            <ul style={{listStyle:"none",padding:0,marginBottom:16,fontSize:13,color:"var(--text2)"}}>
              {["Unlimited articles","Custom prompts","Images + WebP","WordPress publish","Internal links"].map(f=><li key={f} style={{padding:"3px 0",display:"flex",gap:8,alignItems:"center"}}><span style={{color:"var(--green)"}}>✓</span>{f}</li>)}
            </ul>
            <button className="btn btn-primary" style={{width:"100%"}} onClick={()=>onUpgrade("basic")}>Get Basic →</button>
          </div>
          <div style={{background:"linear-gradient(145deg,var(--bg2),rgba(99,102,241,.08))",border:"1px solid var(--accent)",borderRadius:"var(--radius-lg)",padding:20,textAlign:"left",position:"relative"}}>
            <div style={{position:"absolute",top:12,right:12,background:"var(--accent)",color:"#fff",fontSize:10,fontWeight:700,padding:"3px 8px",borderRadius:20}}>Most Popular</div>
            <div style={{fontFamily:"var(--font-display)",fontSize:18,fontWeight:700,marginBottom:4}}>Pro</div>
            <div style={{fontSize:32,fontWeight:800,fontFamily:"var(--font-display)",background:"linear-gradient(135deg,#f59e0b,#d97706)",WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent",marginBottom:12}}>$40<span style={{fontSize:14,fontWeight:400,WebkitTextFillColor:"var(--text3)",color:"var(--text3)"}}>/mo</span></div>
            <ul style={{listStyle:"none",padding:0,marginBottom:16,fontSize:13,color:"var(--text2)"}}>
              {["Everything in Basic","Pinterest auto-pin","AI pin images","Board scheduling","Auto-pin after publish"].map(f=><li key={f} style={{padding:"3px 0",display:"flex",gap:8,alignItems:"center"}}><span style={{color:"var(--green)"}}>✓</span>{f}</li>)}
            </ul>
            <button className="btn btn-pro" style={{width:"100%"}} onClick={()=>onUpgrade("pro")}>Get Pro ★</button>
          </div>
        </div>
        <p style={{fontSize:12,color:"var(--text3)"}}>Secure checkout via Gumroad · Cancel anytime</p>
      </div>
    </div>
  );
}

// ─── CHECKOUT MODAL (Gumroad) ──────────────────────────────────────────────
function CheckoutModal({ plan, onClose, userEmail }) {
  const url = plan === "pro" ? CHECKOUT_PRO : CHECKOUT_BASIC;
  const fullUrl = `${url}?wanted=true&email=${encodeURIComponent(userEmail || "")}`;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e=>e.stopPropagation()} style={{ maxWidth:480 }}>
        <button className="modal-close" onClick={onClose}>✕</button>
        <div style={{ textAlign:"center",padding:"8px 0 24px" }}>
          <div style={{ fontSize:48,marginBottom:12 }}>{plan==="pro"?"★":"⚡"}</div>
          <div style={{ fontFamily:"var(--font-display)",fontSize:22,fontWeight:700,marginBottom:6 }}>
            {plan==="pro"?"NicheFlow Pro":"NicheFlow Basic"}
          </div>
          <div style={{ fontSize:36,fontWeight:800,fontFamily:"var(--font-display)",marginBottom:4,color:plan==="pro"?"var(--pro)":"var(--accent2)" }}>
            {plan==="pro"?"$40":"$30"}<span style={{ fontSize:16,fontWeight:400,color:"var(--text3)" }}>/month</span>
          </div>
          <p style={{ fontSize:13,color:"var(--text2)",marginBottom:24,lineHeight:1.6 }}>
            {plan==="pro"
              ?"Everything in Basic plus Pinterest auto-pinning with AI-generated pin images and 4-word hook titles."
              :"Unlimited articles, custom prompts, images, and WordPress publishing."}
          </p>
          <a href={fullUrl} target="_blank" rel="noreferrer"
            className={`btn ${plan==="pro"?"btn-pro":"btn-primary"} btn-lg`}
            style={{ width:"100%",marginBottom:12,display:"flex" }}>
            Continue to Gumroad →
          </a>
          <p style={{ fontSize:12,color:"var(--text3)" }}>Secure checkout via Gumroad · Cancel anytime</p>
        </div>
      </div>
    </div>
  );
}

// ─── POLICY PAGES ──────────────────────────────────────────────────────────
function PolicyShell({ onBack, title, date, children }) {
  return (
    <div className="policy-wrap">
      <style>{css}</style>
      <div className="policy-inner">
        <div className="policy-back-row">
          <button className="btn btn-ghost btn-sm" onClick={onBack} style={{border:"none",color:"var(--text3)",paddingLeft:0}}>← Back</button>
          <div style={{display:"flex",alignItems:"center",gap:8}}>
            <Logo size={22}/>
            <span style={{fontFamily:"var(--font-display)",fontSize:14,fontWeight:700,background:"linear-gradient(135deg,var(--accent2),#c084fc)",WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent"}}>NicheFlow AI</span>
          </div>
        </div>
        <h1>{title}</h1>
        <span className="policy-date">Last updated: April 2026</span>
        {children}
      </div>
    </div>
  );
}

function PrivacyPolicyPage({ onBack }) {
  return (
    <PolicyShell onBack={onBack} title="Privacy Policy">
      <h2>1. Information We Collect</h2>
      <p>We collect information you provide when you create an account or use the service — including your email address, encrypted password, API keys, WordPress credentials, and any custom prompts you configure in Settings.</p>
      <p>We also collect usage data automatically: articles generated, publish history, and interaction logs to help us improve the service. We do not sell this data to any third party.</p>

      <h2>2. How We Use Your Information</h2>
      <ul>
        <li>To provide, operate, and maintain NicheFlow AI</li>
        <li>To authenticate your account and process payments via Gumroad</li>
        <li>To securely store your settings (API keys, prompts, WordPress credentials)</li>
        <li>To send transactional emails such as account confirmation and payment receipts from Gumroad</li>
        <li>To debug issues and improve the service</li>
      </ul>

      <h2>3. Data Storage & Security</h2>
      <p>Your account data is stored in Supabase, a cloud database with encryption at rest. API keys you enter are stored encrypted and never logged in plain text in our server logs. All data in transit is protected with TLS/HTTPS.</p>

      <h2>4. Third-Party Services</h2>
      <p>NicheFlow AI connects to the following third-party services to deliver its functionality. By using our service, you also agree to their respective terms:</p>
      <ul>
        <li><strong>Supabase</strong> — database and authentication</li>
        <li><strong>Gumroad</strong> — payment processing and subscription management</li>
        <li><strong>Groq / Google Gemini</strong> — AI article and card generation (your prompts are sent to these APIs)</li>
        <li><strong>GoAPI / Pollinations</strong> — AI image generation</li>
        <li><strong>Pinterest API</strong> — pin creation (Pro plan only)</li>
        <li><strong>WordPress REST API</strong> — article publishing to your own website</li>
      </ul>

      <h2>5. Cookies & Local Storage</h2>
      <p>We use browser localStorage to store your session token and app configuration so you stay logged in between visits. We do not use third-party tracking cookies or advertising cookies of any kind.</p>

      <h2>6. Your Rights & Data Deletion</h2>
      <p>You may request deletion of your account and all associated data at any time by emailing <a href="mailto:support@nicheflowai.com">support@nicheflowai.com</a>. Upon deletion, your settings, history, and credentials will be permanently removed from our database within 30 days.</p>

      <h2>7. Children's Privacy</h2>
      <p>NicheFlow AI is not directed at children under 13. We do not knowingly collect personal information from anyone under 13 years of age.</p>

      <h2>8. Changes to This Policy</h2>
      <p>We may update this policy from time to time. We will notify users of significant changes by posting the new version on this page with an updated date. Continued use of the service constitutes acceptance.</p>

      <h2>9. Contact</h2>
      <p>Questions? Email us at <a href="mailto:support@nicheflowai.com">support@nicheflowai.com</a>.</p>
    </PolicyShell>
  );
}

function RefundPolicyPage({ onBack }) {
  return (
    <PolicyShell onBack={onBack} title="Refund Policy">
      <h2>Our Commitment</h2>
      <p>We want you to be completely satisfied with NicheFlow AI. This policy explains when and how you can request a refund.</p>

      <h2>Free Trial First</h2>
      <p>Every new account receives a <strong>2-day free trial</strong> with no credit card required. We strongly encourage you to test every feature during this period — article generation, image automation, WordPress publishing, and Pinterest integration (Pro) — before subscribing.</p>

      <h2>7-Day Money-Back Guarantee</h2>
      <p>If you subscribe and are not satisfied within the first <strong>7 days</strong> of your paid plan, contact us and we will issue a full refund — no questions asked. This applies to both Basic ($30/mo) and Pro ($40/mo) plans.</p>

      <h2>After the 7-Day Window</h2>
      <p>After the first 7 days, refunds are considered on a case-by-case basis. We generally will not issue refunds for:</p>
      <ul>
        <li>Unused time remaining in a billing period after the 7-day period</li>
        <li>Failure to cancel before a renewal date (please cancel at least 24 hours before your renewal)</li>
        <li>Issues caused by third-party API providers (Groq, Gemini, GoAPI, Pinterest, WordPress) outside our control</li>
        <li>Accounts that have violated our Terms of Service</li>
        <li>Requests made after the account has published a significant volume of content</li>
      </ul>

      <h2>How to Request a Refund</h2>
      <p>Email <a href="mailto:support@nicheflowai.com">support@nicheflowai.com</a> with the subject line <strong>"Refund Request"</strong>, including the email address on your account and your Gumroad order number (found in your purchase receipt email). We will process eligible refunds within 5–10 business days through Gumroad.</p>

      <h2>Cancellations</h2>
      <p>You can cancel your subscription at any time through your Gumroad account or via the link in your purchase receipt email. Cancellation stops future charges but does not automatically trigger a refund. Your access continues until the end of the current billing period.</p>

      <h2>Exceptional Circumstances</h2>
      <p>In exceptional cases — such as a critical service outage lasting more than 48 continuous hours preventing use of core features — we may offer pro-rated credits or refunds at our discretion. Contact us to discuss your situation.</p>

      <h2>Contact</h2>
      <p>Refund requests: <a href="mailto:support@nicheflowai.com">support@nicheflowai.com</a></p>
    </PolicyShell>
  );
}

function TermsOfServicePage({ onBack }) {
  return (
    <PolicyShell onBack={onBack} title="Terms of Service">
      <h2>1. Acceptance of Terms</h2>
      <p>By creating an account or using NicheFlow AI ("the Service"), you agree to be bound by these Terms of Service and our Privacy Policy. If you do not agree, do not create an account or use the Service.</p>

      <h2>2. Description of Service</h2>
      <p>NicheFlow AI is a SaaS platform that uses AI to generate long-form blog articles, automate image generation, and publish content to WordPress. Pro subscribers also have access to Pinterest automation. The Service connects to third-party APIs on your behalf using credentials you provide.</p>

      <h2>3. Account Registration</h2>
      <p>You must provide a valid email address to create an account. You are responsible for maintaining the confidentiality of your password and for all activity under your account. Notify us immediately at <a href="mailto:support@nicheflowai.com">support@nicheflowai.com</a> if you suspect unauthorized access.</p>

      <h2>4. Free Trial</h2>
      <p>New accounts receive a 2-day free trial beginning at the moment of account creation. After the trial ends, continued access requires an active paid subscription. We reserve the right to modify or discontinue the free trial for new signups at any time.</p>

      <h2>5. Acceptable Use</h2>
      <p>You agree not to use the Service to:</p>
      <ul>
        <li>Generate spam, misleading content, or content violating any third-party platform's terms (WordPress, Pinterest, your web host)</li>
        <li>Reverse engineer, copy, resell, or sublicense the Service or its underlying technology</li>
        <li>Circumvent API rate limits or abuse shared infrastructure in ways that degrade service for other users</li>
        <li>Publish or generate illegal content, hate speech, or content infringing intellectual property rights</li>
        <li>Use the Service in any way that violates applicable local, national, or international laws</li>
        <li>Attempt to gain unauthorized access to any part of the Service, its servers, or connected databases</li>
      </ul>
      <p>We reserve the right to suspend or terminate accounts violating these terms without notice and without refund.</p>

      <h2>6. API Keys & Credentials</h2>
      <p>You are solely responsible for all API keys, WordPress credentials, Pinterest tokens, and other access tokens you provide to NicheFlow AI. We store them securely but take no responsibility for charges incurred through your third-party API accounts (Groq, GoAPI, Pinterest, etc.) as a result of using this Service.</p>

      <h2>7. Subscription & Billing</h2>
      <p>Paid subscriptions are processed through <strong>Gumroad</strong>. By subscribing, you authorize Gumroad to charge your payment method on a recurring monthly basis. You may cancel at any time through your Gumroad account. Refunds are governed by our Refund Policy. We reserve the right to change pricing with 30 days' notice to existing subscribers.</p>

      <h2>8. Content Ownership</h2>
      <p>You retain full ownership of all content generated through NicheFlow AI and published to your websites. We claim no intellectual property rights over your content. You are solely responsible for ensuring generated content — including AI-produced text and images — complies with applicable laws and does not infringe third-party rights.</p>

      <h2>9. AI-Generated Content Disclaimer</h2>
      <p>AI-generated content may contain inaccuracies, errors, or outdated information. You are solely responsible for reviewing all generated content before publishing. We make no warranty that AI-generated content is accurate, original, or free from errors.</p>

      <h2>10. Service Availability</h2>
      <p>We strive for high availability but do not guarantee uninterrupted service. We are not liable for downtime caused by third-party providers (AI model APIs, image generation APIs, Pinterest, WordPress). Planned maintenance will be communicated in advance where possible.</p>

      <h2>11. Limitation of Liability</h2>
      <p>To the maximum extent permitted by law, NicheFlow AI and its operators shall not be liable for any indirect, incidental, special, consequential, or punitive damages arising from your use of the Service — including loss of data, revenue, or business. Our total aggregate liability shall not exceed the amount you paid us in the 30 days prior to the claim.</p>

      <h2>12. Disclaimer of Warranties</h2>
      <p>The Service is provided "as is" and "as available" without warranties of any kind, express or implied, including merchantability, fitness for a particular purpose, or non-infringement. Your use of the Service is at your sole risk.</p>

      <h2>13. Termination</h2>
      <p>We may suspend or terminate your account at any time for violation of these Terms, with or without prior notice. You may terminate your account at any time by cancelling your subscription and requesting data deletion by email.</p>

      <h2>14. Changes to Terms</h2>
      <p>We reserve the right to modify these Terms at any time. We will notify users of material changes via email or in-app notice at least 14 days before they take effect. Continued use constitutes acceptance.</p>

      <h2>15. Governing Law</h2>
      <p>These Terms shall be governed by applicable law. Any disputes shall be subject to the exclusive jurisdiction of the courts in the jurisdiction where NicheFlow AI is operated.</p>

      <h2>16. Contact</h2>
      <p>Questions about these Terms? Email <a href="mailto:support@nicheflowai.com">support@nicheflowai.com</a>.</p>
    </PolicyShell>
  );
}

// ─── LANDING ───────────────────────────────────────────────────────────────
function LandingPage({ onLogin, onSignup, onCheckout, onPolicy }) {
  const features = [
    { icon: "✦", title: "AI Article Engine", desc: "Two separate AI models — one crafts your article, another builds the summary card. Fully independent." },
    { icon: "🎨", title: "Prompt Studio", desc: "Write your own prompts from scratch. Real-time token counter warns you before hitting limits." },
    { icon: "🖼️", title: "Image Automation", desc: "Midjourney or Pollinations images, auto-converted to WebP and set as featured image in WordPress." },
    { icon: "📌", title: "Pinterest Bot (Pro)", desc: "Auto-pin after publishing with AI-generated 4-word hook title overlaid on custom pin images." },
    { icon: "🔗", title: "Internal Linking", desc: "Fetches your existing WordPress posts and injects relevant long-tail phrase links automatically." },
    { icon: "📅", title: "Smart Scheduling", desc: "Delay between articles, draft or publish instantly, auto-pin with custom delay. Full control." },
  ];
  return (
    <div className="landing mesh-bg">
      <style>{css}</style>
      <nav className="nav">
        <div className="nav-brand"><Logo size={26} /><span>NicheFlow AI</span></div>
        <div style={{ display:"flex",gap:32 }}>
          <a href="#features" style={{ color:"var(--text2)",fontSize:14,textDecoration:"none" }}>Features</a>
          <a href="#pricing" style={{ color:"var(--text2)",fontSize:14,textDecoration:"none" }}>Pricing</a>
        </div>
        <div style={{ display:"flex",gap:10 }}>
          <button className="btn btn-ghost btn-sm" onClick={onLogin}>Log in</button>
          <button className="btn btn-primary btn-sm" onClick={onSignup}>Try free 2 days</button>
        </div>
      </nav>

      <section className="hero">
        <div className="fade-up" style={{ display:"inline-flex",alignItems:"center",gap:8,padding:"5px 14px",background:"var(--accent-dim)",border:"1px solid rgba(99,102,241,.25)",borderRadius:20,fontSize:12,fontWeight:500,color:"var(--accent2)",marginBottom:24 }}>✦ Content automation, reimagined</div>
        <h1 className="fade-up-d1">Publish <span className="grad">10x faster</span><br />across every niche.</h1>
        <p className="fade-up-d2">NicheFlow AI writes long-form articles, builds info cards, generates images, and pins to Pinterest — all from one dashboard.</p>
        <div className="fade-up-d3" style={{ display:"flex",gap:14,flexWrap:"wrap" }}>
          <button className="btn btn-primary btn-lg" onClick={onSignup} style={{ animation:"glow 3s ease-in-out infinite" }}>Try free for 2 days →</button>
          <button className="btn btn-ghost btn-lg" onClick={onLogin}>Sign in</button>
        </div>
        <div className="fade-up-d4" style={{ display:"flex",gap:40,marginTop:56,paddingTop:40,borderTop:"1px solid var(--border)",flexWrap:"wrap" }}>
          {[["2 AI Models","Article + Card, independent"],["2 Day Free Trial","No credit card needed"],["Pinterest Ready","Auto-pin with Pro"],["Any Niche","Mommy blog to finance"]].map(([n,l])=>(
            <div key={n}><div style={{fontFamily:"var(--font-display)",fontSize:26,fontWeight:700}}>{n}</div><div style={{fontSize:12,color:"var(--text3)",marginTop:2}}>{l}</div></div>
          ))}
        </div>
      </section>

      <section id="features" style={{ padding:"72px 48px",maxWidth:1100,margin:"0 auto" }}>
        <div style={{ fontSize:12,fontWeight:600,color:"var(--accent2)",letterSpacing:2,textTransform:"uppercase",marginBottom:12 }}>What's inside</div>
        <div style={{ fontFamily:"var(--font-display)",fontSize:"clamp(24px,4vw,38px)",fontWeight:700,marginBottom:44,letterSpacing:-1 }}>Everything your content business needs</div>
        <div className="features-grid">
          {features.map(f=>(
            <div className="feature-card" key={f.title}>
              <div style={{ width:38,height:38,background:"var(--accent-dim)",border:"1px solid rgba(99,102,241,.2)",borderRadius:10,display:"flex",alignItems:"center",justifyContent:"center",fontSize:17,marginBottom:12 }}>{f.icon}</div>
              <div style={{ fontFamily:"var(--font-display)",fontSize:15,fontWeight:600,marginBottom:6 }}>{f.title}</div>
              <div style={{ fontSize:13,color:"var(--text2)",lineHeight:1.6 }}>{f.desc}</div>
            </div>
          ))}
        </div>
      </section>

      <section id="pricing" style={{ padding:"72px 48px",maxWidth:860,margin:"0 auto" }}>
        <div style={{ fontSize:12,fontWeight:600,color:"var(--accent2)",letterSpacing:2,textTransform:"uppercase",marginBottom:12 }}>Pricing</div>
        <div style={{ fontFamily:"var(--font-display)",fontSize:"clamp(24px,4vw,38px)",fontWeight:700,letterSpacing:-1 }}>Simple, honest pricing</div>
        <p style={{ color:"var(--text2)",fontSize:15,marginTop:8 }}>Start free for 2 days. No credit card required. Cancel anytime.</p>
        <div className="pricing-grid">
          {[
            { name:"Basic", price:"$30", desc:"Everything you need to run a content business on autopilot.",
              features:["Unlimited article generation","Custom article prompt","Custom card prompt","4 images per article (1 featured + 3 body)","WordPress auto-publish","Featured image auto-set","Internal link injection","History & analytics"],
              btn:"Get Basic →", cls:"", action: () => onCheckout("basic") },
            { name:"Pro", price:"$40", desc:"Everything in Basic plus full Pinterest automation with AI-designed pin images.",
              features:["Everything in Basic","Pinterest auto-pinning","AI-generated pin images","4-word hook title overlay","Board selection & scheduling","Pin delay scheduling","Auto-pin after publish","Custom pin image design"],
              btn:"Get Pro ★", cls:"featured", action: () => onCheckout("pro") },
          ].map(p=>(
            <div key={p.name} className={`plan-card ${p.cls}`}>
              <div style={{ fontFamily:"var(--font-display)",fontSize:20,fontWeight:700,marginBottom:6 }}>{p.name}</div>
              <div style={{ fontFamily:"var(--font-display)",fontSize:44,fontWeight:800,letterSpacing:-2,margin:"14px 0 4px",...(p.name==="Pro"?{background:"linear-gradient(135deg,#f59e0b,#d97706)",WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent"}:{}) }}>{p.price}<span style={{ fontSize:16,fontWeight:400,WebkitTextFillColor:"var(--text3)",color:"var(--text3)" }}>/mo</span></div>
              <div style={{ fontSize:13,color:"var(--text2)",marginBottom:20,lineHeight:1.6 }}>{p.desc}</div>
              <ul className="plan-features">{p.features.map(f=><li key={f}>{f}</li>)}</ul>
              <button className={`btn ${p.name==="Pro"?"btn-pro":"btn-primary"}`} style={{ width:"100%" }} onClick={p.action}>{p.btn}</button>
            </div>
          ))}
        </div>
        <div style={{marginTop:32,textAlign:"center"}}>
          <button className="btn btn-ghost" onClick={onSignup} style={{fontSize:13,color:"var(--text3)"}}>Or try free for 2 days — no credit card needed →</button>
        </div>
      </section>

      <footer style={{ borderTop:"1px solid var(--border)",padding:"28px 48px" }}>
        <div style={{ maxWidth:1100,margin:"0 auto",display:"flex",justifyContent:"space-between",alignItems:"center",flexWrap:"wrap",gap:16 }}>
          <div className="nav-brand"><Logo size={20}/><span>NicheFlow AI</span></div>
          <div style={{ display:"flex",gap:24,flexWrap:"wrap",alignItems:"center" }}>
            <button className="footer-link-btn" onClick={()=>onPolicy("terms")}>Terms of Service</button>
            <button className="footer-link-btn" onClick={()=>onPolicy("privacy")}>Privacy Policy</button>
            <button className="footer-link-btn" onClick={()=>onPolicy("refund")}>Refund Policy</button>
          </div>
          <div style={{ fontSize:13,color:"var(--text3)" }}>© 2026 NicheFlow AI. All rights reserved.</div>
        </div>
      </footer>
    </div>
  );
}

// ─── AUTH ──────────────────────────────────────────────────────────────────
function AuthPage({ mode, onSuccess, onSwitch, onBack }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [step, setStep] = useState("form");

  async function submit(e) {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      if (mode === "login") {
        const data = await supaLogin(email, password);
        onSuccess(data);
      } else {
        const data = await supaSignup(email, password);
        if (data.session || data.access_token) { onSuccess(data.session || data); }
        else { setStep("confirm"); }
      }
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="auth-page">
      <style>{css}</style>
      <div className="auth-card fade-up">
        <button className="btn btn-ghost btn-sm" onClick={onBack} style={{ marginBottom:16,paddingLeft:0,border:"none",color:"var(--text3)" }}>← Back</button>
        <div className="auth-brand"><Logo size={28}/><span>NicheFlow AI</span></div>
        {step === "confirm" ? (
          <div>
            <div className="alert alert-ok" style={{ marginBottom:16 }}>✓ Account created! Check your email to confirm, then log in.</div>
            <p style={{ fontSize:13,color:"var(--text2)",marginBottom:20,lineHeight:1.6 }}>Once confirmed, come back and sign in with your email and password.</p>
            <button className="btn btn-primary" style={{ width:"100%",marginBottom:10 }} onClick={() => { setStep("form"); onSwitch("login"); }}>Go to Login →</button>
          </div>
        ) : (
          <>
            <h2 style={{ fontFamily:"var(--font-display)",fontSize:22,fontWeight:700,margin:"6px 0 4px" }}>
              {mode==="login"?"Welcome back":"Start your free trial"}
            </h2>
            <p style={{ fontSize:13,color:"var(--text2)",marginBottom:24 }}>
              {mode==="login"?"Sign in to your NicheFlow dashboard":"2 days free — no credit card required"}
            </p>
            {error && <div className="alert alert-err">{error}</div>}
            <form onSubmit={submit}>
              <div style={{ marginBottom:14 }}>
                <label className="form-label">Email</label>
                <input className="input" type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@example.com" required autoComplete="email" />
              </div>
              <div style={{ marginBottom:6 }}>
                <label className="form-label">Password</label>
                <input className="input" type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder={mode==="signup"?"At least 8 characters":"Your password"} required minLength={8} autoComplete={mode==="signup"?"new-password":"current-password"} />
              </div>
              <button className="btn btn-primary" style={{ width:"100%",marginTop:14 }} disabled={loading}>
                {loading ? <><span className="spinner"/>Working...</> : mode==="login"?"Sign in →":"Start free trial →"}
              </button>
            </form>
            <p style={{ textAlign:"center",fontSize:13,color:"var(--text2)",marginTop:16 }}>
              {mode==="login"?"No account? ":"Already have one? "}
              <button style={{ background:"none",border:"none",color:"var(--accent2)",cursor:"pointer",fontFamily:"var(--font)",fontSize:13 }} onClick={()=>onSwitch(mode==="login"?"signup":"login")}>
                {mode==="login"?"Try free 2 days":"Sign in"}
              </button>
            </p>
          </>
        )}
      </div>
    </div>
  );
}

// ─── UPGRADE BANNER ────────────────────────────────────────────────────────
function UpgradeBanner({ onUpgrade }) {
  return (
    <div className="upgrade-banner">
      <div className="upgrade-banner-text">
        <strong>Upgrade to Pro</strong> — Unlock Pinterest automation, AI pin images with hook titles, board scheduling, and more.
      </div>
      <button className="btn btn-pro btn-sm" onClick={onUpgrade}>Upgrade — $40/mo ★</button>
    </div>
  );
}

// ─── DASHBOARD ─────────────────────────────────────────────────────────────
function Dashboard({ history, plan, onUpgrade, createdAt, planExpires, isAdmin }) {
  const published = history.filter(h=>h.status==="published").length;
  const failed = history.filter(h=>h.status==="failed").length;
  const daysLeft = isAdmin ? "∞" : plan === "pro" ? (getSubDaysLeft(planExpires) || "∞") : getDaysLeft(createdAt);
  return (
    <div className="fade-up">
      {plan !== "pro" && !isAdmin && <UpgradeBanner onUpgrade={()=>onUpgrade("pro")} />}
      <div className="stat-grid">
        {[
          {num:history.length,label:"Total articles"},
          {num:published,label:"Published",sub:published>0?`${Math.round(published/Math.max(history.length,1)*100)}% success`:""},
          {num:failed,label:"Failed"},
          {num:daysLeft,label:isAdmin?"Admin (∞)":plan==="pro"?"Sub days left":"Trial days left",sub:isAdmin?"Full access":plan==="pro"?"Pro active":"basic trial"},
        ].map((s,i)=>(
          <div className="stat-card" key={i}>
            <div className="stat-card-num">{s.num}</div>
            <div className="stat-card-label">{s.label}</div>
            {s.sub&&<div style={{fontSize:12,color:"var(--green)",marginTop:6}}>{s.sub}</div>}
          </div>
        ))}
      </div>
      <div className="card" style={{ marginBottom:18 }}>
        <div style={{ fontFamily:"var(--font-display)",fontSize:14,fontWeight:600,marginBottom:14 }}>Recent Activity</div>
        {history.length===0
          ?<div style={{color:"var(--text3)",fontSize:14,textAlign:"center",padding:"18px 0"}}>No articles yet. Go to Generate to start.</div>
          :history.slice(-6).reverse().map((h,i)=>(
            <div key={i} style={{display:"flex",alignItems:"center",gap:12,padding:"9px 0",borderBottom:i<5?"1px solid var(--border)":"none"}}>
              <span className={`dot ${h.status==="published"?"dot-green":"dot-red"}`}/>
              <span style={{flex:1,fontSize:13,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{h.title}</span>
              <span style={{fontSize:11,color:"var(--text3)",flexShrink:0}}>{h.time}</span>
              {h.post_url&&<a href={h.post_url} target="_blank" rel="noreferrer" style={{color:"var(--accent2)",fontSize:12,textDecoration:"none",flexShrink:0}}>View →</a>}
            </div>
          ))
        }
      </div>
      <div className="alert alert-info">✦ Go to <strong>Settings → Prompts</strong> to write your custom article and card prompts before your first batch.</div>
    </div>
  );
}

// ─── GENERATE ──────────────────────────────────────────────────────────────
function GeneratePage({ config, onHistoryUpdate, plan, createdAt, onUpgrade, isAdmin }) {
  const [titles, setTitles] = useState("");
  const [delay, setDelay] = useState(config.delay_sec||10);
  const [draft, setDraft] = useState(false);
  const [useImages, setUseImages] = useState(true);
  const [running, setRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [progress, setProgress] = useState(0);
  const logRef = useRef(null);

  const expired = isTrialExpired(createdAt) && plan !== "pro" && !isAdmin;
  const addLog = useCallback((msg, type="info") => {
    const time = new Date().toLocaleTimeString("en",{hour:"2-digit",minute:"2-digit",second:"2-digit"});
    setLogs(prev=>[...prev.slice(-120),{msg,type,time}]);
    setTimeout(()=>{ if(logRef.current) logRef.current.scrollTop=logRef.current.scrollHeight; },50);
  },[]);

  const titleList = titles.split("\n").map(t=>t.trim()).filter(Boolean);
  const missingKeys = !config.gemini_key||!config.wp_url||!config.wp_password;

  if (expired) return <TrialExpiredGate onUpgrade={onUpgrade} />;

  function detectLogType(msg) {
    if (msg.includes("✅")||msg.includes("🎉")||msg.includes("Published")) return "ok";
    if (msg.includes("❌")||msg.includes("Failed")||msg.includes("failed")) return "err";
    if (msg.includes("⚠️")) return "warn";
    return "info";
  }

  async function run() {
    if(!config.gemini_key){addLog("❌ No AI key. Go to Settings → API Keys.","err");return;}
    if(!config.wp_url){addLog("❌ No WordPress URL. Go to Settings → WordPress.","err");return;}
    if(!config.wp_password){addLog("❌ No WordPress password. Go to Settings → WordPress.","err");return;}
    if(!titleList.length){addLog("Enter at least one article title.","warn");return;}
    setRunning(true);setLogs([]);setProgress(0);
    addLog(`Starting batch: ${titleList.length} article(s)`,"ok");
    for(let i=0;i<titleList.length;i++){
      const title=titleList[i];
      setProgress(i/titleList.length);
      addLog(`[${i+1}/${titleList.length}] ${title}`,"info");
      try{
        const payload={
          title,gemini_key:config.gemini_key||"",goapi_key:config.goapi_key||"",
          wp_url:config.wp_url||"",wp_password:config.wp_password||"",
          custom_prompt:config.custom_prompt||"",card_prompt:config.card_prompt||"",
          mj_template:config.mj_template||"",publish_status:draft?"draft":(config.publish_status||"publish"),
          use_images:useImages,use_pollinations:config.use_pollinations||false,
          pollinations_prompt:config.pollinations_prompt||"",show_card:config.show_card!==false,
          use_internal_links:config.use_internal_links!==false,max_links:config.max_links||4,
full_width_images:config.full_width_images!==false,clickable_card:config.clickable_card||false
        };
        const token=getStoredToken();
        const res=await fetch(`${API_URL}/pipeline`,{method:"POST",headers:{"Content-Type":"application/json",...(token?{"Authorization":`Bearer ${token}`}:{})},body:JSON.stringify(payload)});
        let data;
        try{data=await res.json();}catch{data={success:false,error:`Server ${res.status}`};}
        if(data.logs&&Array.isArray(data.logs)){for(const logMsg of data.logs){addLog(logMsg,detectLogType(logMsg));}}
        if(data.success){
          addLog(`✅ Published → ${data.post_url}`,"ok");
          if(data.featured_image_url) addLog(`🖼️ Featured image set`,"ok");
          onHistoryUpdate({title,status:"published",post_url:data.post_url,time:new Date().toLocaleTimeString()});
        } else {
          const errMsg=data.detail||data.error||"Unknown error";
          addLog(`❌ Failed: ${errMsg}`,"err");
          onHistoryUpdate({title,status:"failed",error:errMsg,time:new Date().toLocaleTimeString()});
        }
      }catch(err){
        addLog(`❌ Network: ${err.message}`,"err");
        onHistoryUpdate({title,status:"failed",error:err.message,time:new Date().toLocaleTimeString()});
      }
      if(i<titleList.length-1&&delay>0){addLog(`⏱ Waiting ${delay}s...`,"info");await new Promise(r=>setTimeout(r,delay*1000));}
    }
    setProgress(1);addLog(`Batch complete.`,"ok");setRunning(false);
  }

  const logCls={ok:"log-ok",err:"log-err",info:"log-info",warn:"log-warn"};
  return (
    <div className="fade-up">
      {missingKeys&&<div className="alert alert-warn" style={{marginBottom:18}}>⚠️ Missing config — go to <strong>Settings</strong> first.</div>}
      <div style={{display:"grid",gridTemplateColumns:"1.4fr 1fr",gap:18,marginBottom:18}}>
        <div className="card">
          <div style={{fontFamily:"var(--font-display)",fontSize:14,fontWeight:600,marginBottom:6}}>Article Titles</div>
          <Hint>One title per line. Each becomes a full published article.</Hint>
          <textarea className="input" style={{minHeight:200,marginTop:10,fontFamily:"monospace",fontSize:13}} value={titles} onChange={e=>setTitles(e.target.value)} placeholder={"10 Best Postpartum Recovery Tips\nBoursin Cheese Pasta with Broccoli\nBest Baby Monitors 2025"} disabled={running}/>
          <div style={{marginTop:6,fontSize:12,color:"var(--text3)"}}>{titleList.length} title{titleList.length!==1?"s":""} entered</div>
        </div>
        <div style={{display:"flex",flexDirection:"column",gap:14}}>
          <div className="card">
            <div style={{fontFamily:"var(--font-display)",fontSize:14,fontWeight:600,marginBottom:14}}>Options</div>
            <div style={{display:"flex",flexDirection:"column",gap:14}}>
              <div className="setting-row"><div className="setting-info"><div className="setting-name">Save as Draft</div><div className="setting-desc">Publish as draft instead of live</div></div><label className="toggle"><input type="checkbox" checked={draft} onChange={e=>setDraft(e.target.checked)}/><span className="toggle-slider"/></label></div>
              <div className="setting-row"><div className="setting-info"><div className="setting-name">Generate Images</div><div className="setting-desc">1 featured + 3 body images. All WebP, uploaded to WordPress.</div></div><label className="toggle"><input type="checkbox" checked={useImages} onChange={e=>setUseImages(e.target.checked)}/><span className="toggle-slider"/></label></div>
              <div><div className="setting-name" style={{marginBottom:6}}>Delay between articles</div><div style={{display:"flex",alignItems:"center",gap:10}}><input className="input" type="number" value={delay} min={0} max={120} onChange={e=>setDelay(+e.target.value)} style={{width:80}}/><span style={{fontSize:13,color:"var(--text2)"}}>seconds</span></div></div>
            </div>
          </div>
          <button className="btn btn-primary" style={{width:"100%",padding:"13px",fontSize:15}} onClick={run} disabled={running||!titleList.length||missingKeys}>
            {running?<><span className="spinner"/>Running...</>:`▶ Generate ${titleList.length||""} Article${titleList.length!==1?"s":""}`}
          </button>
          {running&&<div><div style={{display:"flex",justifyContent:"space-between",fontSize:12,color:"var(--text3)",marginBottom:6}}><span>Progress</span><span>{Math.round(progress*100)}%</span></div><div className="progress"><div className="progress-fill" style={{width:`${progress*100}%`}}/></div></div>}
        </div>
      </div>
      <div className="card">
        <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:12}}>
          <div style={{fontFamily:"var(--font-display)",fontSize:14,fontWeight:600,display:"flex",alignItems:"center",gap:8}}><span className={`dot ${running?"dot-green dot-pulse":"dot-yellow"}`}/>Process Log</div>
          <button className="btn btn-ghost btn-sm" onClick={()=>setLogs([])}>Clear</button>
        </div>
        <div className="process-log" ref={logRef}>
          {logs.length===0?<div style={{color:"var(--text3)",fontFamily:"var(--font)"}}>Logs appear here when you run a batch...</div>
            :logs.map((l,i)=><div key={i} className="log-line"><span className="log-time">[{l.time}]</span><span className={logCls[l.type]||""}>{l.msg}</span></div>)
          }
        </div>
      </div>
    </div>
  );
}

// ─── SETTINGS ──────────────────────────────────────────────────────────────
function SettingsPage({ config, onSave, plan, onUpgrade }) {
  const [cfg, setCfg] = useState({...config});
  const [tab, setTab] = useState("api");
  const [saved, setSaved] = useState(false);
  const [testing, setTesting] = useState({});
  const [testResults, setTestResults] = useState({});
  useEffect(()=>{setCfg({...config});},[config]);
  const update=(k,v)=>setCfg(p=>({...p,[k]:v}));
  function save(){onSave(cfg);setSaved(true);setTimeout(()=>setSaved(false),2500);}

  async function testKey(val){
    if(!val)return;setTesting(p=>({...p,ai:true}));
    try{
      const keys=val.split(",").map(k=>k.trim()).filter(Boolean);
      let result={ok:false,msg:"❌ No valid key format"};
      for(const key of keys){
        if(key.startsWith("gsk_")){const r=await fetch("https://api.groq.com/openai/v1/chat/completions",{method:"POST",headers:{Authorization:`Bearer ${key}`,"Content-Type":"application/json"},body:JSON.stringify({model:"llama-3.1-8b-instant",messages:[{role:"user",content:"Say OK"}],max_tokens:5})});result=r.ok?{ok:true,msg:"✅ Groq key valid!"}:{ok:false,msg:`❌ Groq error ${r.status}`};}
        else if(key.startsWith("AIza")){const r=await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${key}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({contents:[{parts:[{text:"Say OK"}]}],generationConfig:{maxOutputTokens:5}})});result=r.ok?{ok:true,msg:"✅ Gemini key valid!"}:{ok:false,msg:`❌ Gemini error ${r.status}`};}
        else{result={ok:false,msg:"❌ Use gsk_ (Groq) or AIza (Gemini)"};}
        if(result.ok)break;
      }
      setTestResults(p=>({...p,ai:result}));
    }catch(e){setTestResults(p=>({...p,ai:{ok:false,msg:`❌ ${e.message}`}}));}
    finally{setTesting(p=>({...p,ai:false}));}
  }

  async function testWP(){
    if(!cfg.wp_url||!cfg.wp_password)return;setTesting(p=>({...p,wp:true}));
    try{
      const[user,...rest]=cfg.wp_password.split(":");const pass=rest.join(":").trim();
      const creds=btoa(`${user.trim()}:${pass}`);const base=cfg.wp_url.replace(/\/$/,"");
      const r=await fetch(`${base}/wp-json/wp/v2/users/me`,{headers:{Authorization:`Basic ${creds}`}});
      const data=await r.json();
      setTestResults(p=>({...p,wp:r.ok?{ok:true,msg:`✅ Connected as: ${data.name||user.trim()}`}:{ok:false,msg:`❌ ${data.message||r.status}`}}));
    }catch(e){setTestResults(p=>({...p,wp:{ok:false,msg:`❌ ${e.message}`}}));}
    finally{setTesting(p=>({...p,wp:false}));}
  }

  const tabs=[{id:"api",label:"API Keys"},{id:"wp",label:"WordPress"},{id:"prompts",label:"Prompts"},{id:"images",label:"Images"},...(plan==="pro"?[{id:"pinterest",label:"Pinterest"}]:[])]

  return (
    <div className="fade-up">
      {plan!=="pro"&&<UpgradeBanner onUpgrade={()=>onUpgrade("pro")}/>}
      <div className="tabs">{tabs.map(t=><button key={t.id} className={`tab ${tab===t.id?"active":""}`} onClick={()=>setTab(t.id)}>{t.label}</button>)}</div>

      {tab==="api"&&(
        <div className="settings-section fade-up">
          <div className="settings-header"><span>🔑</span><h3>AI API Keys</h3></div>
          <div className="settings-body">
            <div>
              <label className="form-label">Groq or Gemini API Key(s)</label>
              <div style={{display:"flex",gap:10}}>
                <input className="input" type="password" value={cfg.gemini_key||""} onChange={e=>update("gemini_key",e.target.value)} placeholder="gsk_... or AIza... or both comma-separated" style={{flex:1}}/>
                <button className="btn btn-ghost btn-sm" onClick={()=>testKey(cfg.gemini_key)} disabled={testing.ai}>{testing.ai?<span className="spinner spinner-accent"/>:"Test"}</button>
              </div>
              {testResults.ai&&<div className={`alert ${testResults.ai.ok?"alert-ok":"alert-err"}`} style={{marginTop:8}}>{testResults.ai.msg}</div>}
              <Hint>Groq (free): console.groq.com — starts with gsk_. Gemini (free): aistudio.google.com — starts with AIza. Add both comma-separated for zero-downtime fallback.</Hint>
            </div>
            <div>
              <label className="form-label">GoAPI Key (Midjourney images)</label>
              <input className="input" type="password" value={cfg.goapi_key||""} onChange={e=>update("goapi_key",e.target.value)} placeholder="Your GoAPI key..."/>
              <Hint>Only for Midjourney images. Skip if using Pollinations (free) in Images tab.</Hint>
            </div>
          </div>
        </div>
      )}

      {tab==="wp"&&(
        <div className="settings-section fade-up">
          <div className="settings-header"><span>🌐</span><h3>WordPress Connection</h3></div>
          <div className="settings-body">
            <div><label className="form-label">WordPress Site URL</label><input className="input" value={cfg.wp_url||""} onChange={e=>update("wp_url",e.target.value)} placeholder="https://yoursite.com"/><Hint>Include https:// — no trailing slash</Hint></div>
            <div><label className="form-label">WordPress App Password</label><input className="input" type="password" value={cfg.wp_password||""} onChange={e=>update("wp_password",e.target.value)} placeholder="username:xxxx xxxx xxxx xxxx"/><Hint>WordPress → Users → Profile → Application Passwords → Add New. Format: yourusername:generated-password</Hint></div>
            <div style={{display:"flex",gap:10,alignItems:"center"}}>
              <button className="btn btn-ghost btn-sm" onClick={testWP} disabled={testing.wp}>{testing.wp?<><span className="spinner spinner-accent"/>Testing...</>:"Test Connection"}</button>
              {testResults.wp&&<div className={`alert ${testResults.wp.ok?"alert-ok":"alert-err"}`} style={{margin:0,flex:1}}>{testResults.wp.msg}</div>}
            </div>
            <div className="divider"/>
            <div><label className="form-label">Default Publish Status</label><select className="input" value={cfg.publish_status||"publish"} onChange={e=>update("publish_status",e.target.value)}><option value="publish">Publish immediately</option><option value="draft">Save as draft</option></select></div>
            <div className="setting-row"><div className="setting-info"><div className="setting-name">Auto-inject internal links</div><div className="setting-desc">Match full long-tail article titles (3+ word phrases)</div></div><label className="toggle"><input type="checkbox" checked={cfg.use_internal_links!==false} onChange={e=>update("use_internal_links",e.target.checked)}/><span className="toggle-slider"/></label></div>
            {cfg.use_internal_links!==false&&<div><label className="form-label">Max internal links per article</label><input className="input" type="number" value={cfg.max_links||4} min={1} max={10} onChange={e=>update("max_links",+e.target.value)} style={{width:100}}/></div>}
            <div className="setting-row"><div className="setting-info"><div className="setting-name">Full width images</div><div className="setting-desc">Images stretch to full width in articles</div></div><label className="toggle"><input type="checkbox" checked={cfg.full_width_images!==false} onChange={e=>update("full_width_images",e.target.checked)}/><span className="toggle-slider"/></label></div>
<div className="setting-row"><div className="setting-info"><div className="setting-name">Clickable card</div><div className="setting-desc">Wrap summary card in a share link</div></div><label className="toggle"><input type="checkbox" checked={cfg.clickable_card||false} onChange={e=>update("clickable_card",e.target.checked)}/><span className="toggle-slider"/></label></div>
          </div>
        </div>
      )}

      {tab==="prompts"&&(
        <div style={{display:"flex",flexDirection:"column",gap:18}} className="fade-up">
          <div className="settings-section">
            <div className="settings-header"><span>💬</span><h3>Article Prompt</h3></div>
            <div className="settings-body">
              <div className="alert alert-info">✦ Use <code>{"{title}"}</code> as placeholder. Return JSON with <code>html_content</code>, <code>seo_title</code>, <code>excerpt</code>, color hex keys. Include <code>##IMAGE1##</code> <code>##IMAGE2##</code> <code>##IMAGE3##</code> where images go.</div>
              <div className="prompt-editor">
                <textarea className="input" style={{minHeight:220,fontFamily:"monospace",fontSize:13}} value={cfg.custom_prompt||""} onChange={e=>update("custom_prompt",e.target.value)} placeholder={"You are Emma, a warm mama blogger.\nWrite about: {title}\nReturn JSON: {\"seo_title\":\"\",\"excerpt\":\"\",\"html_content\":\"\",\"MAIN\":\"#hex\",\"MAIN_DARK\":\"#hex\",\"LIGHT_BG\":\"#hex\",\"BORDER\":\"#hex\"}"}/>
                {cfg.custom_prompt&&<div className="prompt-counter">{estimateTokens(cfg.custom_prompt).toLocaleString()} tokens</div>}
              </div>
              {cfg.custom_prompt&&<TokenCounter text={cfg.custom_prompt} limit={2000}/>}
            </div>
          </div>
          <div className="settings-section">
            <div className="settings-header"><span>🃏</span><h3>Card Prompt</h3></div>
            <div className="settings-body">
              <div className="alert alert-info">✦ Return JSON with <code>card_title</code>, <code>summary</code>, <code>key_points</code> array, <code>quick_facts</code> array, <code>cta_text</code>. The CTA button triggers browser share/bookmark.</div>
              <div className="prompt-editor">
                <textarea className="input" style={{minHeight:160,fontFamily:"monospace",fontSize:13}} value={cfg.card_prompt||""} onChange={e=>update("card_prompt",e.target.value)} placeholder={"For \"{title}\" return JSON:\n{\"card_title\":\"[short title]\",\"summary\":\"[2 sentences]\",\"key_points\":[\"point 1\"],\"quick_facts\":[{\"label\":\"Time\",\"value\":\"30 mins\"}],\"cta_text\":\"Save this! 📌\"}"}/>
                {cfg.card_prompt&&<div className="prompt-counter">{estimateTokens(cfg.card_prompt).toLocaleString()} tokens</div>}
              </div>
              {cfg.card_prompt&&<TokenCounter text={cfg.card_prompt} limit={1500}/>}
              <div className="setting-row"><div className="setting-info"><div className="setting-name">Show card in every article</div><div className="setting-desc">Append summary card at end of each article</div></div><label className="toggle"><input type="checkbox" checked={cfg.show_card!==false} onChange={e=>update("show_card",e.target.checked)}/><span className="toggle-slider"/></label></div>
            </div>
          </div>
        </div>
      )}

      {tab==="images"&&(
        <div className="settings-section fade-up">
          <div className="settings-header"><span>🖼️</span><h3>Image Settings</h3></div>
          <div className="settings-body">
            <div className="alert alert-info">✦ 4 images per article: 1 featured (set on WP post) + 3 body (at ##IMAGE1## ##IMAGE2## ##IMAGE3##). All cropped to your --ar ratio, WebP, uploaded to WordPress.</div>
            <div><label className="form-label">Midjourney Image Template</label><textarea className="input" style={{minHeight:90}} value={cfg.mj_template||""} onChange={e=>update("mj_template",e.target.value)} placeholder="Close up {recipe_name}, food photography, natural light --ar 1:1"/><Hint>Use {"{recipe_name}"} or {"{title}"}. The --ar flag controls crop ratio for ALL images including featured. Requires GoAPI key.</Hint></div>
            <div className="divider"/>
            <div className="setting-row"><div className="setting-info"><div className="setting-name">Use Pollinations (free)</div><div className="setting-desc">Free AI images — no API key needed</div></div><label className="toggle"><input type="checkbox" checked={cfg.use_pollinations||false} onChange={e=>update("use_pollinations",e.target.checked)}/><span className="toggle-slider"/></label></div>
            {cfg.use_pollinations&&<div><label className="form-label">Pollinations Prompt Template</label><textarea className="input" style={{minHeight:80}} value={cfg.pollinations_prompt||""} onChange={e=>update("pollinations_prompt",e.target.value)} placeholder="Professional editorial photography of {title}, natural light, 4K"/></div>}
          </div>
        </div>
      )}

      {tab==="pinterest"&&plan==="pro"&&(
        <div style={{display:"flex",flexDirection:"column",gap:18}} className="fade-up">
          <div className="settings-section">
            <div className="settings-header"><span>📌</span><h3>Pinterest Integration</h3><span className="badge badge-pro" style={{marginLeft:"auto"}}>PRO</span></div>
            <div className="settings-body">
              <div><label className="form-label">Pinterest Access Token</label><input className="input" type="password" value={cfg.pinterest_token||""} onChange={e=>update("pinterest_token",e.target.value)} placeholder="Your Pinterest API access token..."/><Hint>developers.pinterest.com → My Apps → Create App → Generate Token.</Hint></div>
              <div className="setting-row"><div className="setting-info"><div className="setting-name">Auto-pin after publish</div><div className="setting-desc">Automatically create a pin every time an article is published</div></div><label className="toggle"><input type="checkbox" checked={cfg.auto_pin||false} onChange={e=>update("auto_pin",e.target.checked)}/><span className="toggle-slider"/></label></div>
              <div><label className="form-label">Pin delay (minutes after publish)</label><input className="input" type="number" value={cfg.pin_delay_min||0} min={0} max={1440} onChange={e=>update("pin_delay_min",+e.target.value)} style={{width:120}}/></div>
              <div><label className="form-label">Default Board IDs (comma-separated)</label><input className="input" value={cfg.pinterest_boards||""} onChange={e=>update("pinterest_boards",e.target.value)} placeholder="board-id-1, board-id-2"/></div>
            </div>
          </div>
          <div className="settings-section">
            <div className="settings-header"><span>💬</span><h3>Pinterest Pin Prompt</h3></div>
            <div className="settings-body">
              <div className="alert alert-info">✦ AI generates pin content. Return JSON with <code>pin_title</code> (60 chars), <code>pin_description</code> (150 chars + CTA), <code>alt_text</code>, <code>hashtags</code> array, and <code>hook_title</code> (EXACTLY 4 words).</div>
              <div className="prompt-editor">
                <textarea className="input" style={{minHeight:140,fontFamily:"monospace",fontSize:13}} value={cfg.pinterest_prompt||""} onChange={e=>update("pinterest_prompt",e.target.value)} placeholder={"For article \"{title}\" at {url}:\nReturn JSON:\n{\"pin_title\":\"[max 60 chars]\",\"pin_description\":\"[max 150 chars + Save this!]\",\"alt_text\":\"[1 sentence]\",\"hashtags\":[\"tag1\",\"tag2\"],\"hook_title\":\"[EXACTLY 4 words]\"}"}/>
              </div>
              {cfg.pinterest_prompt&&<TokenCounter text={cfg.pinterest_prompt} limit={1000}/>}
            </div>
          </div>
          <div className="settings-section">
            <div className="settings-header"><span>🎨</span><h3>Pin Image Design</h3><span className="badge badge-pro" style={{marginLeft:"auto"}}>PRO</span></div>
            <div className="settings-body">
              <div className="alert alert-info">✦ Generates a custom Pinterest pin image: article body image as background + 4-word hook title overlaid. Uploaded to WordPress and used as pin image — NOT the featured image.</div>
              <div>
                <label className="form-label">Pin Image Design Prompt</label>
                <textarea className="input" style={{minHeight:90,fontFamily:"monospace",fontSize:13}} value={cfg.pin_image_prompt||""} onChange={e=>update("pin_image_prompt",e.target.value)} placeholder={"background_color:#1a1a2e overlay_opacity:0.55 title_color:#ffffff title_size:72 subtitle_color:#f0f0f0 subtitle_size:32 canvas_width:1000 canvas_height:1500 title_position:bottom logo_text:yoursite.com gradient:true gradient_color:#6366f1"}/>
                <Hint>Each setting is key:value separated by spaces. All optional — defaults used if omitted.</Hint>
              </div>
              <div style={{background:"var(--bg3)",border:"1px solid var(--border)",borderRadius:"var(--radius)",padding:"14px 16px",fontSize:12,color:"var(--text2)",lineHeight:2}}>
                <strong style={{color:"var(--accent2)",display:"block",marginBottom:6}}>Available settings:</strong>
                <code>background_color:#1a1a2e</code> · <code>overlay_opacity:0.55</code> · <code>title_color:#ffffff</code> · <code>title_size:72</code><br/>
                <code>subtitle_color:#f0f0f0</code> · <code>subtitle_size:32</code> · <code>canvas_width:1000</code> · <code>canvas_height:1500</code><br/>
                <code>title_position:bottom</code> (top/center/bottom) · <code>logo_text:yoursite.com</code><br/>
                <code>gradient:true</code> · <code>gradient_color:#6366f1</code>
              </div>
            </div>
          </div>
        </div>
      )}

      <div style={{display:"flex",alignItems:"center",gap:14,marginTop:22}}>
        <button className="btn btn-primary" onClick={save}>{saved?"✓ Saved!":"Save Settings"}</button>
        {saved&&<span style={{fontSize:13,color:"var(--green)"}}>All settings saved</span>}
      </div>
    </div>
  );
}

// ─── HISTORY ───────────────────────────────────────────────────────────────
function HistoryPage({ history, onClear }) {
  const published = history.filter(h=>h.status==="published");
  const failed = history.filter(h=>h.status==="failed");
  return (
    <div className="fade-up">
      <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:18}}>
        <div style={{display:"flex",gap:18}}>
          <span style={{fontSize:14,color:"var(--text2)",display:"flex",alignItems:"center",gap:7}}><span className="dot dot-green"/>{published.length} published</span>
          <span style={{fontSize:14,color:"var(--text2)",display:"flex",alignItems:"center",gap:7}}><span className="dot dot-red"/>{failed.length} failed</span>
        </div>
        {history.length>0&&<button className="btn btn-danger btn-sm" onClick={onClear}>Clear all</button>}
      </div>
      {history.length===0
        ?<div className="card" style={{textAlign:"center",padding:"44px 24px"}}><div style={{fontSize:36,marginBottom:10}}>📋</div><div style={{fontSize:14,fontWeight:500,marginBottom:6}}>No articles yet</div></div>
        :[...history].reverse().map((h,i)=>(
          <div key={i} className="history-item">
            <span className={`dot ${h.status==="published"?"dot-green":"dot-red"}`}/>
            <div style={{flex:1,minWidth:0}}><div className="history-title">{h.title}</div><div className="history-meta">{h.time} · {h.status}</div></div>
            <div style={{display:"flex",gap:8,flexShrink:0}}>
              {h.post_url&&<a href={h.post_url} target="_blank" rel="noreferrer" className="btn btn-ghost btn-sm">View →</a>}
              {h.status==="failed"&&<span style={{fontSize:12,color:"var(--red)",maxWidth:200,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{h.error}</span>}
            </div>
          </div>
        ))
      }
    </div>
  );
}

// ─── PREVIEW ───────────────────────────────────────────────────────────────
function PreviewPage({ config }) {
  const [title, setTitle] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState("");
  const [error, setError] = useState("");
  async function generate(){
    if(!title||!config.gemini_key)return;
    setLoading(true);setError("");setResult("");
    try{
      const res=await apiCall("/preview",{method:"POST",body:JSON.stringify({title})});
      const data=await res.json();
      if(data.success)setResult(data.content);
      else setError(data.detail||data.error||"Generation failed");
    }catch(e){setError(e.message);}
    finally{setLoading(false);}
  }
  return (
    <div className="fade-up">
      <div className="card" style={{marginBottom:18}}>
        <div style={{fontFamily:"var(--font-display)",fontSize:14,fontWeight:600,marginBottom:12}}>Preview Article</div>
        <div style={{display:"flex",gap:12}}>
          <input className="input" value={title} onChange={e=>setTitle(e.target.value)} placeholder="Enter a test title..." style={{flex:1}} onKeyDown={e=>e.key==="Enter"&&generate()}/>
          <button className="btn btn-primary" onClick={generate} disabled={loading||!title||!config.gemini_key}>{loading?<><span className="spinner"/>Generating...</>:"Preview →"}</button>
        </div>
        {!config.gemini_key&&<div className="alert alert-warn" style={{marginTop:10}}>Configure an AI key in Settings → API Keys first.</div>}
        {error&&<div className="alert alert-err" style={{marginTop:10}}>{error}</div>}
      </div>
      {result&&<div className="card"><div style={{display:"flex",justifyContent:"space-between",marginBottom:14}}><div style={{fontWeight:600}}>Preview Result</div><span style={{fontSize:12,color:"var(--text3)"}}>~{result.split(" ").length} words</span></div><div style={{background:"var(--bg3)",borderRadius:"var(--radius)",padding:22,maxHeight:600,overflowY:"auto",color:"var(--text)",lineHeight:1.8}} dangerouslySetInnerHTML={{__html:result}}/></div>}
    </div>
  );
}

// ─── PINTEREST PAGE ─────────────────────────────────────────────────────────
function PinterestPage({ config, history, plan, onUpgrade }) {
  const [boards, setBoards] = useState([]);
  const [selectedBoards, setSelectedBoards] = useState([]);
  const [loadingBoards, setLoadingBoards] = useState(false);
  const [boardError, setBoardError] = useState("");
  const [running, setRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [pinPreviews, setPinPreviews] = useState([]);
  const [previewModal, setPreviewModal] = useState(null);
  const [scheduleEnabled, setScheduleEnabled] = useState(false);
  const [scheduleDate, setScheduleDate] = useState("");
  const [scheduleTime, setScheduleTime] = useState("09:00");
  const logRef = useRef(null);

  if(plan!=="pro"){
    return (
      <div className="fade-up" style={{display:"flex",alignItems:"center",justifyContent:"center",minHeight:400}}>
        <div style={{textAlign:"center",maxWidth:400}}>
          <div style={{fontSize:52,marginBottom:14}}>📌</div>
          <div style={{fontFamily:"var(--font-display)",fontSize:22,fontWeight:700,marginBottom:8}}>Pinterest Bot</div>
          <div style={{fontSize:14,color:"var(--text2)",lineHeight:1.7,marginBottom:24}}>Auto-pin every published article with AI-generated pin images.</div>
          <button className="btn btn-pro btn-lg" style={{width:"100%",marginBottom:12}} onClick={()=>onUpgrade("pro")}>Upgrade to Pro — $40/mo ★</button>
        </div>
      </div>
    );
  }

  const addLog = useCallback((msg,type="info")=>{
    const time=new Date().toLocaleTimeString("en",{hour12:false});
    setLogs(prev=>[...prev.slice(-100),{msg,type,time}]);
    setTimeout(()=>{if(logRef.current)logRef.current.scrollTop=logRef.current.scrollHeight;},50);
  },[]);

  useEffect(()=>{
    if(config.pinterest_token && boards.length === 0){loadBoards();}
  // eslint-disable-next-line
  },[config.pinterest_token]);

  const publishedArticles = history.filter(h=>h.status==="published"&&h.post_url);

  async function loadBoards(){
    setLoadingBoards(true);setBoardError("");
    try{
      const res=await apiCall("/pinterest/boards");const data=await res.json();
      if(res.ok){setBoards(data.boards||[]);if(!data.boards?.length)setBoardError("No boards found. Check your Pinterest token in Settings.");}
      else setBoardError(data.detail||"Failed to load boards");
    }catch(e){setBoardError(e.message);}
    finally{setLoadingBoards(false);}
  }

  async function runPinterest(){
    if(!publishedArticles.length){addLog("No published articles to pin.","warn");return;}
    if(!selectedBoards.length){addLog("Select at least one board.","warn");return;}
    let scheduled_at = null;
    if(scheduleEnabled&&scheduleDate){scheduled_at=`${scheduleDate}T${scheduleTime||"09:00"}:00`;addLog(`📅 Scheduling pins for: ${scheduled_at}`,"info");}
    setRunning(true);
    addLog(`Starting Pinterest bot: ${publishedArticles.length} articles → ${selectedBoards.length} board(s)`,"ok");
    try{
      const res=await apiCall("/pinterest/run",{method:"POST",body:JSON.stringify({board_ids:selectedBoards,pin_image_prompt:config.pin_image_prompt||"",scheduled_at})});
      const data=await res.json();
      if(res.ok){
        const results=data.results||[];setPinPreviews(results);
        results.forEach(r=>{addLog(`📌 ${r.title}`,"info");r.boards?.forEach(b=>{addLog(b.success?`  ✅ Board ${b.board_id} → Pin ${b.pin_id}`:`  ❌ ${b.error}`,b.success?"ok":"err");});});
        addLog(`Done! ${results.filter(r=>r.status==="sent").length}/${results.length} pinned.`,"ok");
      } else addLog(`❌ ${data.detail||"Pinterest run failed"}`,"err");
    }catch(e){addLog(`❌ ${e.message}`,"err");}
    finally{setRunning(false);}
  }

  function toggleBoard(id){setSelectedBoards(prev=>prev.includes(id)?prev.filter(b=>b!==id):[...prev,id]);}
  const logCls={ok:"log-ok",err:"log-err",info:"log-info",warn:"log-warn"};
  const tomorrow=new Date();tomorrow.setDate(tomorrow.getDate()+1);
  const tomorrowStr=tomorrow.toISOString().split("T")[0];

  return (
    <div className="fade-up">
      {previewModal&&(
        <div className="modal-overlay" onClick={()=>setPreviewModal(null)}>
          <div className="modal" onClick={e=>e.stopPropagation()}>
            <button className="modal-close" onClick={()=>setPreviewModal(null)}>✕</button>
            <div style={{fontFamily:"var(--font-display)",fontSize:18,fontWeight:700,marginBottom:16}}>Pin Preview</div>
            <div className="pin-preview">
              {(previewModal.pin_image_url||previewModal.featured_image_url)
                ?<img src={previewModal.pin_image_url||previewModal.featured_image_url} alt={previewModal.pin_title} className="pin-img" style={{height:240}}/>
                :<div className="pin-img" style={{height:240,display:"flex",alignItems:"center",justifyContent:"center",color:"var(--text3)"}}>No pin image</div>
              }
              <div className="pin-body">
                <div className="pin-title">{previewModal.pin_title}</div>
                <div className="pin-desc">{previewModal.pin_description}</div>
                {previewModal.hashtags?.length>0&&<div className="pin-tags">{previewModal.hashtags.map(h=><span key={h} className="pin-tag">#{h}</span>)}</div>}
              </div>
            </div>
          </div>
        </div>
      )}
      <div style={{display:"grid",gridTemplateColumns:"1.3fr 1fr",gap:18,marginBottom:18}}>
        <div className="card">
          <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:8}}>
            <div style={{fontFamily:"var(--font-display)",fontSize:14,fontWeight:600}}>Pinterest Boards</div>
            <button className="btn btn-ghost btn-sm" onClick={loadBoards} disabled={loadingBoards}>{loadingBoards?<><span className="spinner spinner-accent"/>Loading...</>:"↺ Refresh Boards"}</button>
          </div>
          {!config.pinterest_token&&<div className="alert alert-warn" style={{marginTop:10}}>⚠️ No Pinterest token. Go to Settings → Pinterest first.</div>}
          {boardError&&<div className="alert alert-err" style={{marginTop:10}}>{boardError}</div>}
          {loadingBoards&&<div style={{textAlign:"center",padding:"20px 0",color:"var(--text3)",fontSize:13}}>Loading your boards...</div>}
          {boards.length>0?(
            <div className="board-grid">
              {boards.map(b=>(
                <div key={b.id} className={`board-item ${selectedBoards.includes(b.id)?"selected":""}`} onClick={()=>toggleBoard(b.id)}>
                  <div style={{fontSize:22,marginBottom:6}}>📋</div>
                  <div style={{fontSize:12,fontWeight:500,color:"var(--text2)"}}>{b.name}</div>
                  {selectedBoards.includes(b.id)&&<div style={{fontSize:11,color:"var(--accent2)",marginTop:4}}>✓ Selected</div>}
                </div>
              ))}
            </div>
          ):(!loadingBoards&&config.pinterest_token&&<div style={{marginTop:14,color:"var(--text3)",fontSize:13,textAlign:"center",padding:"20px 0"}}>No boards loaded yet. Click Refresh Boards.</div>)}
        </div>
        <div style={{display:"flex",flexDirection:"column",gap:14}}>
          <div className="card">
            <div style={{fontFamily:"var(--font-display)",fontSize:14,fontWeight:600,marginBottom:12}}>Queue Status</div>
            <div style={{fontSize:28,fontWeight:700,fontFamily:"var(--font-display)",marginBottom:4}}>{publishedArticles.length}</div>
            <div style={{fontSize:13,color:"var(--text3)"}}>articles ready to pin</div>
            <div className="divider"/>
            <div style={{fontSize:13,color:"var(--text2)",marginBottom:8}}>{selectedBoards.length} board{selectedBoards.length!==1?"s":""} selected</div>
          </div>
          <div className="card">
            <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:scheduleEnabled?14:0}}>
              <div><div style={{fontSize:14,fontWeight:500}}>📅 Schedule pins</div><div style={{fontSize:12,color:"var(--text3)",marginTop:2}}>Pin at a specific date & time</div></div>
              <label className="toggle"><input type="checkbox" checked={scheduleEnabled} onChange={e=>setScheduleEnabled(e.target.checked)}/><span className="toggle-slider"/></label>
            </div>
            {scheduleEnabled&&(
              <div style={{display:"flex",flexDirection:"column",gap:10}}>
                <div><label className="form-label">Date</label><input className="input" type="date" value={scheduleDate} min={tomorrowStr} onChange={e=>setScheduleDate(e.target.value)}/></div>
                <div><label className="form-label">Time</label><input className="input" type="time" value={scheduleTime} onChange={e=>setScheduleTime(e.target.value)}/></div>
                {scheduleDate&&<div className="alert alert-info" style={{fontSize:12}}>📅 Pins will be scheduled for {scheduleDate} at {scheduleTime}</div>}
              </div>
            )}
          </div>
          <button className="btn btn-pro" style={{width:"100%",padding:"13px"}} onClick={runPinterest}
            disabled={running||!publishedArticles.length||!selectedBoards.length||(scheduleEnabled&&!scheduleDate)}>
            {running?<><span className="spinner"/>Pinning...</>:scheduleEnabled&&scheduleDate
              ?`📅 Schedule ${publishedArticles.length} Pin${publishedArticles.length!==1?"s":""}`
              :`📌 Pin ${publishedArticles.length} Article${publishedArticles.length!==1?"s":""}`}
          </button>
        </div>
      </div>
      {pinPreviews.length>0&&(
        <div className="card" style={{marginBottom:18}}>
          <div style={{fontFamily:"var(--font-display)",fontSize:14,fontWeight:600,marginBottom:14}}>Pin Results</div>
          {pinPreviews.map((p,i)=>(
            <div key={i} style={{display:"flex",alignItems:"center",gap:12,padding:"10px 0",borderBottom:i<pinPreviews.length-1?"1px solid var(--border)":"none",cursor:"pointer"}} onClick={()=>setPreviewModal(p)}>
              <span className={`dot ${p.status==="sent"?"dot-green":"dot-red"}`}/>
              <div style={{flex:1}}><div style={{fontSize:13,fontWeight:500}}>{p.title}</div><div style={{fontSize:12,color:"var(--text3)",marginTop:2}}>📌 {p.pin_title} · Hook: "{p.hook_title}"</div></div>
              <button className="btn btn-ghost btn-sm" onClick={e=>{e.stopPropagation();setPreviewModal(p);}}>Preview →</button>
            </div>
          ))}
        </div>
      )}
      <div className="card">
        <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:12}}>
          <span className={`dot ${running?"dot-green dot-pulse":"dot-yellow"}`}/>
          <span style={{fontFamily:"var(--font-display)",fontSize:14,fontWeight:600}}>Pinterest Log</span>
          <button className="btn btn-ghost btn-sm" style={{marginLeft:"auto"}} onClick={()=>setLogs([])}>Clear</button>
        </div>
        <div className="process-log" ref={logRef}>
          {logs.length===0?<div style={{color:"var(--text3)",fontFamily:"var(--font)"}}>Select boards and click Pin to start...</div>
            :logs.map((l,i)=><div key={i} className="log-line"><span className="log-time">[{l.time}]</span><span className={logCls[l.type]||""}>{l.msg}</span></div>)
          }
        </div>
      </div>
    </div>
  );
}

// ─── DOCUMENTATION PAGE ─────────────────────────────────────────────────────
function DocsPage({ plan, onUpgrade }) {
  const [section, setSection] = useState("start");
  const sections = [
    {id:"start",label:"🚀 Quick Start"},{id:"api",label:"🔑 API Keys"},
    {id:"wordpress",label:"🌐 WordPress"},{id:"prompts",label:"💬 Prompts & Cards"},
    {id:"images",label:"🖼️ Images & WebP"},{id:"links",label:"🔗 Internal Links"},
    {id:"pinterest",label:"📌 Pinterest (Pro)"},{id:"billing",label:"💳 Billing & Plans"},
  ];
  return (
    <div className="fade-up" style={{display:"flex",gap:24}}>
      <div style={{width:190,flexShrink:0}}>
        <div style={{background:"var(--bg2)",border:"1px solid var(--border)",borderRadius:"var(--radius-lg)",padding:8,position:"sticky",top:20}}>
          {sections.map(s=>(
            <button key={s.id} onClick={()=>setSection(s.id)} style={{display:"block",width:"100%",padding:"8px 12px",borderRadius:8,border:"none",background:section===s.id?"var(--accent-dim)":"transparent",color:section===s.id?"var(--accent2)":"var(--text2)",fontSize:13,textAlign:"left",cursor:"pointer",fontFamily:"var(--font)",marginBottom:2}}>{s.label}</button>
          ))}
        </div>
      </div>
      <div style={{flex:1}}>
        {section==="start"&&(
          <div className="doc-section">
            <h3>🚀 Quick Start</h3>
            <p style={{fontSize:14,color:"var(--text2)",marginBottom:20,lineHeight:1.7}}>Get your first article published in under 5 minutes.</p>
            {[
              {n:"1",t:"Get a free AI key",d:<>Go to <a href="https://console.groq.com" target="_blank" rel="noreferrer" style={{color:"var(--accent2)"}}>console.groq.com</a> — free key starting with <code>gsk_</code>. Or Gemini at <a href="https://aistudio.google.com" target="_blank" rel="noreferrer" style={{color:"var(--accent2)"}}>aistudio.google.com</a> (starts with <code>AIza</code>). Both are free.</>},
              {n:"2",t:"Configure API Keys",d:<>Go to <strong>Settings → API Keys</strong>, paste your key, hit <strong>Test</strong>, then <strong>Save Settings</strong>.</>},
              {n:"3",t:"Connect WordPress",d:<>Go to <strong>Settings → WordPress</strong>. Enter your site URL and App Password in format <code>username:xxxx xxxx xxxx xxxx</code>.</>},
              {n:"4",t:"Write your Prompts",d:<>Go to <strong>Settings → Prompts</strong>. Use <code>{"{title}"}</code> as placeholder. Return JSON with <code>html_content</code>, <code>seo_title</code>, <code>excerpt</code>, and color hex keys.</>},
              {n:"5",t:"Set up Images (optional)",d:<>Go to <strong>Settings → Images</strong>. Paste a Midjourney template or turn on Pollinations for free images.</>},
              {n:"6",t:"Generate your first article",d:<>Go to <strong>Generate</strong>, paste titles (one per line), and click Generate. Watch the Process Log.</>},
            ].map(s=>(
              <div key={s.n} className="doc-step">
                <div className="doc-step-num">{s.n}</div>
                <div className="doc-step-text"><div className="doc-step-title">{s.t}</div><div className="doc-step-desc">{s.d}</div></div>
              </div>
            ))}
          </div>
        )}
        {section==="billing"&&(
          <div className="doc-section">
            <h3>💳 Billing & Plans</h3>
            <div className="alert alert-info" style={{marginBottom:14}}>New users get a <strong>2-day free trial</strong> — no credit card required. After 2 days, the app blocks until you choose a plan.</div>
            {[
              {t:"Free Trial — 2 days",d:"From the moment you create your account, you have 2 full days to use the app free. No credit card needed. The top bar shows a countdown."},
              {t:"Basic plan — $30/month",d:"Unlimited articles, custom article and card prompts, 4 images per article (featured + 3 body), WordPress auto-publish, internal link injection, history."},
              {t:"Pro plan — $40/month",d:"Everything in Basic plus Pinterest automation: AI-generated pin images with 4-word hook titles, board selection, pin scheduling, and auto-pin after publish."},
              {t:"Payments via Gumroad",d:"Payments are handled securely by Gumroad. You'll receive a receipt and can manage or cancel your subscription through your Gumroad account."},
              
              {t:"Subscription countdown",d:"After payment, the top bar shows days left in your billing period. At 3 days or fewer you'll see a warning to renew."},
            ].map((s,i)=>(
              <div key={i} className="doc-step">
                <div className="doc-step-num">{i+1}</div>
                <div className="doc-step-text"><div className="doc-step-title">{s.t}</div><div className="doc-step-desc">{s.d}</div></div>
              </div>
            ))}
            {plan!=="pro"&&<div style={{marginTop:20}}><button className="btn btn-pro" style={{width:"100%"}} onClick={()=>onUpgrade("pro")}>Upgrade to Pro — $40/mo ★</button></div>}
          </div>
        )}
        {section==="api"&&(
          <div className="doc-section">
            <h3>🔑 API Keys</h3>
            <p style={{fontSize:14,color:"var(--text2)",marginBottom:20,lineHeight:1.7}}>NicheFlow uses Groq or Gemini to generate articles. Both are free.</p>
            {[
              {n:"1",t:"Get a Groq key (recommended)",d:<>Go to <a href="https://console.groq.com" target="_blank" rel="noreferrer" style={{color:"var(--accent2)"}}>console.groq.com</a> → Sign up free → API Keys → Create key. Starts with <code>gsk_</code>. Free with generous limits.</>},
              {n:"2",t:"Get a Gemini key (backup)",d:<>Go to <a href="https://aistudio.google.com" target="_blank" rel="noreferrer" style={{color:"var(--accent2)"}}>aistudio.google.com</a> → Get API key. Starts with <code>AIza</code>. Free tier available.</>},
              {n:"3",t:"Add both for zero downtime",d:<>In Settings → API Keys, paste both keys comma-separated: <code>gsk_yourgroqkey, AIzayourgeminikey</code>. If Groq hits rate limits, Gemini takes over automatically.</>},
              {n:"4",t:"GoAPI key (Midjourney images only)",d:<>Only needed if you want Midjourney images. Get it at <a href="https://goapi.ai" target="_blank" rel="noreferrer" style={{color:"var(--accent2)"}}>goapi.ai</a>. Skip this if you use Pollinations (free) in the Images tab.</>},
              {n:"5",t:"Test your keys",d:<>Always click the <strong>Test</strong> button after pasting a key. It makes a live call and confirms the key works before you run a batch.</>},
            ].map(s=>(
              <div key={s.n} className="doc-step">
                <div className="doc-step-num">{s.n}</div>
                <div className="doc-step-text"><div className="doc-step-title">{s.t}</div><div className="doc-step-desc">{s.d}</div></div>
              </div>
            ))}
          </div>
        )}
        {section==="wordpress"&&(
          <div className="doc-section">
            <h3>🌐 WordPress</h3>
            <p style={{fontSize:14,color:"var(--text2)",marginBottom:20,lineHeight:1.7}}>NicheFlow publishes directly to your WordPress site using the REST API and Application Passwords.</p>
            {[
              {n:"1",t:"Site URL",d:<>Enter your full site URL including <code>https://</code>, no trailing slash. Example: <code>https://myblog.com</code>. Works with any WordPress host — Hostinger, WP Engine, Bluehost, self-hosted, etc.</>},
              {n:"2",t:"Create an Application Password",d:<>In WordPress: go to <strong>Users → Profile</strong> → scroll to <strong>Application Passwords</strong> → enter a name like "NicheFlow" → click <strong>Add New Application Password</strong>. Copy the generated password immediately (it won't show again).</>},
              {n:"3",t:"Format the credentials",d:<>In NicheFlow, enter it as: <code>yourusername:xxxx xxxx xxxx xxxx</code>. Replace <code>yourusername</code> with your WordPress admin username (not email). The password is the one WordPress just generated with spaces included.</>},
              {n:"4",t:"Test the connection",d:<>Click <strong>Test Connection</strong> — it makes a live call to your WordPress REST API. If it succeeds, it shows your WordPress display name. If it fails, double-check the username and that the App Password was copied correctly.</>},
              {n:"5",t:"Required WordPress settings",d:<>Make sure <strong>Permalinks</strong> are not set to Plain (WordPress → Settings → Permalinks → choose any option except Plain). Plain permalinks break the REST API.</>},
            ].map(s=>(
              <div key={s.n} className="doc-step">
                <div className="doc-step-num">{s.n}</div>
                <div className="doc-step-text"><div className="doc-step-title">{s.t}</div><div className="doc-step-desc">{s.d}</div></div>
              </div>
            ))}
            <div className="doc-section" style={{marginTop:16,marginBottom:0}}>
              <h3 style={{fontSize:14}}>📋 Publish Settings</h3>
              {[
                {n:"1",t:"Publish immediately vs Draft",d:"Set the default publish status in Settings → WordPress. You can also override this per batch in the Generate page using the 'Save as Draft' toggle."},
                {n:"2",t:"Internal links",d:<>When enabled, NicheFlow fetches your existing WordPress posts and automatically injects relevant internal links using long-tail phrase matching. Set max links per article (default: 4).</>},
                {n:"3",t:"Delay between articles",d:"Set a delay in seconds between each article in a batch. Recommended: 10–30 seconds to avoid hitting API rate limits."},
              ].map(s=>(
                <div key={s.n} className="doc-step">
                  <div className="doc-step-num">{s.n}</div>
                  <div className="doc-step-text"><div className="doc-step-title">{s.t}</div><div className="doc-step-desc">{s.d}</div></div>
                </div>
              ))}
            </div>
          </div>
        )}
        {section==="prompts"&&(
          <div className="doc-section">
            <h3>💬 Prompts & Cards</h3>
            <p style={{fontSize:14,color:"var(--text2)",marginBottom:20,lineHeight:1.7}}>NicheFlow uses two separate AI calls — one for the article, one for the summary card. You control both prompts completely.</p>
            {[
              {n:"1",t:"Article Prompt basics",d:<>Your prompt must include <code>{"{title}"}</code> as a placeholder — NicheFlow replaces it with the actual article title. The AI must return a JSON object.</>},
              {n:"2",t:"Required JSON keys for articles",d:<>Your prompt must tell the AI to return: <code>seo_title</code> (SEO-optimized title), <code>excerpt</code> (meta description), <code>html_content</code> (full article HTML), and color hex keys: <code>MAIN</code>, <code>MAIN_DARK</code>, <code>LIGHT_BG</code>, <code>BORDER</code>.</>},
              {n:"3",t:"Image placeholders in articles",d:<>Put <code>##IMAGE1##</code> <code>##IMAGE2##</code> <code>##IMAGE3##</code> inside your <code>html_content</code> where you want body images injected. NicheFlow replaces these with real uploaded WordPress image tags.</>},
              {n:"4",t:"Example article prompt",d:<><pre>{"You are Emma, a warm mama blogger.\nWrite a detailed article about: {title}\nReturn only JSON:\n{\"seo_title\":\"\",\"excerpt\":\"\",\"html_content\":\"<h2>...</h2>##IMAGE1##...\",\n\"MAIN\":\"#e91e8c\",\"MAIN_DARK\":\"#c4186e\",\"LIGHT_BG\":\"#fdf0f7\",\"BORDER\":\"#f8c8e8\"}"}</pre></>},
              {n:"5",t:"Card Prompt",d:<>Separate AI call for the summary card appended at the end of each article. Must return JSON with: <code>card_title</code>, <code>summary</code> (2 sentences), <code>key_points</code> (array), <code>quick_facts</code> (array of label/value objects), <code>cta_text</code>.</>},
              {n:"6",t:"Token counter",d:"The real-time token counter below each prompt warns you if your prompt is too long. Keep article prompts under 2000 tokens and card prompts under 1500 tokens for best results."},
            ].map(s=>(
              <div key={s.n} className="doc-step">
                <div className="doc-step-num">{s.n}</div>
                <div className="doc-step-text"><div className="doc-step-title">{s.t}</div><div className="doc-step-desc">{s.d}</div></div>
              </div>
            ))}
          </div>
        )}
        {section==="images"&&(
          <div className="doc-section">
            <h3>🖼️ Images & WebP</h3>
            <p style={{fontSize:14,color:"var(--text2)",marginBottom:20,lineHeight:1.7}}>NicheFlow generates 4 images per article: 1 featured image + 3 body images. All are auto-converted to WebP and uploaded to WordPress.</p>
            {[
              {n:"1",t:"How images work",d:<>NicheFlow generates all 4 images in parallel, converts them to WebP, uploads them to your WordPress media library, and injects them at <code>##IMAGE1##</code> <code>##IMAGE2##</code> <code>##IMAGE3##</code> in the article. The featured image is set automatically on the post.</>},
              {n:"2",t:"Option A — Midjourney (GoAPI)",d:<>Requires a GoAPI key from <a href="https://goapi.ai" target="_blank" rel="noreferrer" style={{color:"var(--accent2)"}}>goapi.ai</a>. In Settings → Images, write a Midjourney template using <code>{"{title}"}</code> or <code>{"{recipe_name}"}</code>. Example: <code>Close up {"{title}"}, food photography, natural light --ar 1:1</code>. The <code>--ar</code> flag controls crop ratio for all images.</>},
              {n:"3",t:"Option B — Pollinations (free)",d:<>Turn on "Use Pollinations" in Settings → Images. No API key needed — completely free. Write a prompt template like: <code>Professional editorial photography of {"{title}"}, natural light, 4K</code>. Quality is good for most niches.</>},
              {n:"4",t:"WebP conversion",d:"All images are automatically converted to WebP format before uploading. WebP is smaller and faster than JPEG/PNG — better for SEO and page speed."},
              {n:"5",t:"Toggle images per batch",d:"In the Generate page, use the 'Generate Images' toggle to enable or disable images for a specific batch. Disabling images makes generation much faster if you just need text."},
            ].map(s=>(
              <div key={s.n} className="doc-step">
                <div className="doc-step-num">{s.n}</div>
                <div className="doc-step-text"><div className="doc-step-title">{s.t}</div><div className="doc-step-desc">{s.d}</div></div>
              </div>
            ))}
          </div>
        )}
        {section==="links"&&(
          <div className="doc-section">
            <h3>🔗 Internal Links</h3>
            <p style={{fontSize:14,color:"var(--text2)",marginBottom:20,lineHeight:1.7}}>NicheFlow automatically injects internal links into every article by matching your existing WordPress posts.</p>
            {[
              {n:"1",t:"How it works",d:"Before publishing, NicheFlow fetches up to 200 of your existing WordPress posts. It then scans your new article for phrases that match existing post titles (3+ word long-tail phrases) and wraps them in anchor tags pointing to those posts."},
              {n:"2",t:"Enable internal links",d:<>Go to <strong>Settings → WordPress</strong> and make sure "Auto-inject internal links" is turned on. Set "Max internal links per article" — default is 4. We recommend 3–6 links per article.</>},
              {n:"3",t:"Matching logic",d:"NicheFlow matches full long-tail phrases (3+ words) from your article text against your existing post titles. It only links phrases that appear naturally in your content — it never forces links where the text doesn't match."},
              {n:"4",t:"Why internal links matter",d:"Internal links improve SEO by distributing page authority across your site. They also keep readers on your site longer by connecting related content. NicheFlow automates what would otherwise take hours of manual work per article."},
              {n:"5",t:"Disable for a specific batch",d:"In Settings → WordPress, toggle off 'Auto-inject internal links' if you want to publish a batch without links. You can re-enable it after."},
            ].map(s=>(
              <div key={s.n} className="doc-step">
                <div className="doc-step-num">{s.n}</div>
                <div className="doc-step-text"><div className="doc-step-title">{s.t}</div><div className="doc-step-desc">{s.d}</div></div>
              </div>
            ))}
          </div>
        )}
        {section==="pinterest"&&(
          <div className="doc-section">
            <h3>📌 Pinterest (Pro)</h3>
            <div className="alert alert-info" style={{marginBottom:16}}>Pinterest automation is a <strong>Pro plan</strong> feature only.</div>
            {[
              {n:"1",t:"Get a Pinterest Access Token",d:<>Go to <a href="https://developers.pinterest.com" target="_blank" rel="noreferrer" style={{color:"var(--accent2)"}}>developers.pinterest.com</a> → My Apps → Create App → fill in your app name and redirect URI → Generate Access Token. Paste it in Settings → Pinterest.</>},
              {n:"2",t:"Load your boards",d:<>Go to the <strong>Pinterest</strong> page in NicheFlow → click <strong>Refresh Boards</strong>. Your Pinterest boards will appear as clickable cards. Select one or more boards to pin to.</>},
              {n:"3",t:"Pin image design",d:<>NicheFlow generates a custom pin image: it takes one of your article body images as background, overlays a dark gradient, and adds your AI-generated 4-word hook title in large text. This is separate from the featured image — it's uploaded to WordPress and used only as the pin image.</>},
              {n:"4",t:"4-word hook title",d:<>The Pinterest prompt must return a <code>hook_title</code> field with EXACTLY 4 words. This gets overlaid on the pin image in large text. Example: "Best Tips For Mamas", "Easy Recipes For Beginners". Short, bold, scroll-stopping.</>},
              {n:"5",t:"Auto-pin after publish",d:<>In Settings → Pinterest, enable "Auto-pin after publish". Every time an article is published via Generate, NicheFlow will automatically create a pin. Set a delay (minutes) if you want to wait before pinning.</>},
              {n:"6",t:"Manual pin from Pinterest page",d:<>Go to the <strong>Pinterest</strong> page, select your boards, and click <strong>Pin Articles</strong>. This pins all your published articles at once. You can also schedule pins for a specific date and time.</>},
              {n:"7",t:"Pin Image Design settings",d:<>In Settings → Pinterest → Pin Image Design, customize the overlay: <code>background_color</code>, <code>overlay_opacity</code>, <code>title_color</code>, <code>title_size</code>, <code>canvas_width</code>, <code>canvas_height</code>, <code>title_position</code> (top/center/bottom), <code>logo_text</code>, <code>gradient</code>.</>},
            ].map(s=>(
              <div key={s.n} className="doc-step">
                <div className="doc-step-num">{s.n}</div>
                <div className="doc-step-text"><div className="doc-step-title">{s.t}</div><div className="doc-step-desc">{s.d}</div></div>
              </div>
            ))}
            {plan!=="pro"&&<div style={{marginTop:20}}><button className="btn btn-pro" style={{width:"100%"}} onClick={()=>onUpgrade("pro")}>Upgrade to Pro — $40/mo ★</button></div>}
          </div>
        )}
        {!["start","api","wordpress","prompts","images","links","pinterest","billing"].includes(section)&&(
          <div className="doc-section">
            <h3>{sections.find(s=>s.id===section)?.label}</h3>
            <p style={{fontSize:14,color:"var(--text2)",lineHeight:1.7}}>Documentation coming soon.</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── APP SHELL ─────────────────────────────────────────────────────────────
function AppShell({ user, onLogout, onPolicy }) {
  const [page, setPage] = useState("dashboard");
  const [config, setConfig] = useState(getStoredConfig);
  const [plan, setPlan] = useState("basic");
  const [planExpires, setPlanExpires] = useState(null);
  const [createdAt, setCreatedAt] = useState(new Date().toISOString());
  const [history, setHistory] = useState(()=>{try{return JSON.parse(localStorage.getItem("nicheflow_history")||"[]");}catch{return [];}});
  const [settingsLoaded, setSettingsLoaded] = useState(false);
  const [checkoutModal, setCheckoutModal] = useState(null);

  const email = user?.user?.email || user?.email || "user@example.com";
  const userId = user?.user?.id || user?.id || "";
  const token = user?.access_token || getStoredToken();
  const avatarLetter = email[0]?.toUpperCase() || "U";
  const isAdmin = email === ADMIN_EMAIL;
  const effectivePlan = isAdmin ? "pro" : plan;

  const refreshPlan = useCallback(() => {
    if (!userId || !token) return;
    fetch(`${SUPABASE_URL}/rest/v1/profiles?id=eq.${userId}&select=plan,plan_expires,created_at`, {
      headers: { apikey: SUPABASE_KEY, Authorization: `Bearer ${token}` }
    }).then(async r => {
      if (r.ok) {
        const rows = await r.json();
        if (rows && rows[0]) {
          setPlan(rows[0].plan || "basic");
          setPlanExpires(rows[0].plan_expires || null);
          setCreatedAt(rows[0].created_at || new Date().toISOString());
        }
      }
    }).catch(() => {});
  }, [userId, token]);

  useEffect(() => { refreshPlan(); }, [refreshPlan]);
  useEffect(() => { const iv = setInterval(refreshPlan, 30000); return () => clearInterval(iv); }, [refreshPlan]);

  useEffect(() => {
    if (!token || settingsLoaded) return;
    fetch(`${API_URL}/settings`, { headers: { "Content-Type":"application/json", Authorization:`Bearer ${token}` } })
      .then(async res => {
        if (res.ok) {
          const data = await res.json();
          const dbSettings = data.settings || {};
          if (data.plan) setPlan(data.plan);
          if (data.plan_expires) setPlanExpires(data.plan_expires);
          const merged = { ...config };
          Object.keys(dbSettings).forEach(k => { if (dbSettings[k] !== null && dbSettings[k] !== undefined && dbSettings[k] !== "") merged[k] = dbSettings[k]; });
          setConfig(merged);
          localStorage.setItem("nicheflow_config", JSON.stringify(merged));
        }
        setSettingsLoaded(true);
      }).catch(() => setSettingsLoaded(true));
  }, [token]);

  function saveConfig(cfg) {
    setConfig(cfg);
    localStorage.setItem("nicheflow_config", JSON.stringify(cfg));
    fetch(`${API_URL}/settings`, { method:"POST", headers:{"Content-Type":"application/json", Authorization:`Bearer ${token}`}, body:JSON.stringify(cfg) }).catch(()=>{});
  }

  function addHistory(item) { const next=[...history,item]; setHistory(next); localStorage.setItem("nicheflow_history",JSON.stringify(next)); }
  function clearHistory() { setHistory([]); localStorage.removeItem("nicheflow_history"); }
  function handleUpgrade(targetPlan="pro") { setCheckoutModal(targetPlan); }

  const navItems=[
    {id:"dashboard",icon:"◉",label:"Dashboard"},
    {id:"generate",icon:"⚡",label:"Generate"},
    {id:"preview",icon:"◎",label:"Preview"},
    {id:"history",icon:"📋",label:"History"},
    {id:"pinterest",icon:"📌",label:"Pinterest",pro:true},
    {id:"docs",icon:"📖",label:"Docs"},
    {id:"settings",icon:"⚙️",label:"Settings"},
  ];

  const pageInfo={
    dashboard:["Dashboard","Welcome back."],
    generate:["Generate Articles","Paste titles, let AI handle everything."],
    preview:["Preview","Test article style before a full batch."],
    history:["History","All generated and published articles."],
    pinterest:["Pinterest Bot","Auto-pin with AI-generated hook title images."],
    docs:["Documentation","Everything you need to use NicheFlow AI."],
    settings:["Settings","API keys, prompts, and integrations."],
  };
  const [pageTitle, pageSub] = pageInfo[page] || ["",""];

  return (
    <div className="app-layout">
      <style>{css}</style>
      {checkoutModal&&<CheckoutModal plan={checkoutModal} onClose={()=>setCheckoutModal(null)} userEmail={email}/>}
      <aside className="sidebar">
        <div className="sidebar-logo"><Logo size={24}/><span>NicheFlow AI</span></div>
        <nav className="sidebar-nav">
          <div className="sidebar-section">Main</div>
          {navItems.map(item=>(
            <button key={item.id} className={`nav-item ${page===item.id?"active":""}`} onClick={()=>setPage(item.id)}>
              <span style={{fontSize:15}}>{item.icon}</span>{item.label}
              {item.pro&&<span className="nav-badge">PRO</span>}
            </button>
          ))}
          {effectivePlan!=="pro"&&(
            <button className="nav-item" onClick={()=>handleUpgrade("pro")} style={{marginTop:8,color:"var(--pro)",background:"var(--pro-dim)",border:"1px solid rgba(245,158,11,.2)"}}>
              <span>★</span>Upgrade to Pro
            </button>
          )}
        </nav>
        <div className="sidebar-footer">
          <div className="user-pill">
            <div className="user-avatar">{avatarLetter}</div>
            <div style={{flex:1,minWidth:0}}>
              <div className="user-email">{email}</div>
              <div className="user-plan" style={{color:isAdmin?"#ef4444":effectivePlan==="pro"?"var(--pro)":"var(--accent2)"}}>
                {isAdmin?"🔧 Admin":effectivePlan==="pro"?"★ Pro":"Basic"}
              </div>
            </div>
          </div>
          <button className="nav-item" onClick={refreshPlan} style={{marginTop:4,color:"var(--text3)",fontSize:12,padding:"6px 12px"}}><span>↺</span>Refresh Plan</button>
          <div style={{height:1,background:"var(--border)",margin:"6px 4px"}}/>
          <button className="nav-item" onClick={()=>onPolicy("terms")}   style={{color:"var(--text3)",fontSize:12,padding:"7px 12px"}}><span>📋</span>Terms of Service</button>
          <button className="nav-item" onClick={()=>onPolicy("privacy")} style={{color:"var(--text3)",fontSize:12,padding:"7px 12px"}}><span>📄</span>Privacy Policy</button>
          <button className="nav-item" onClick={()=>onPolicy("refund")}  style={{color:"var(--text3)",fontSize:12,padding:"7px 12px"}}><span>💳</span>Refund Policy</button>
          <div style={{height:1,background:"var(--border)",margin:"6px 4px"}}/>
          <button className="nav-item" onClick={onLogout} style={{color:"var(--text3)"}}><span>→</span>Sign out</button>
        </div>
      </aside>
      <main className="main-content">
        <TopBar createdAt={createdAt} plan={effectivePlan} planExpires={planExpires} onUpgrade={handleUpgrade} isAdmin={isAdmin}/>
        <div className="page-header">
          <h1 className="page-title">{pageTitle}</h1>
          <p className="page-sub">{pageSub}</p>
        </div>
        <div className="page-body">
          {page==="dashboard"&&<Dashboard history={history} plan={effectivePlan} onUpgrade={handleUpgrade} createdAt={createdAt} planExpires={planExpires} isAdmin={isAdmin}/>}
          {page==="generate"&&<GeneratePage config={config} onHistoryUpdate={addHistory} plan={effectivePlan} createdAt={createdAt} onUpgrade={handleUpgrade} isAdmin={isAdmin}/>}
          {page==="preview"&&<PreviewPage config={config}/>}
          {page==="history"&&<HistoryPage history={history} onClear={clearHistory}/>}
          {page==="pinterest"&&<PinterestPage config={config} history={history} plan={effectivePlan} onUpgrade={handleUpgrade}/>}
          {page==="docs"&&<DocsPage plan={effectivePlan} onUpgrade={handleUpgrade}/>}
          {page==="settings"&&<SettingsPage config={config} onSave={saveConfig} plan={effectivePlan} onUpgrade={handleUpgrade}/>}
        </div>
      </main>
    </div>
  );
}

// ─── ROOT ──────────────────────────────────────────────────────────────────
export default function NicheFlowAI() {
  const [view, setView] = useState("landing");
  const [user, setUser] = useState(null);
  const [policyPage, setPolicyPage] = useState(null); // "privacy" | "refund" | "terms"

  useEffect(()=>{
    const stored = localStorage.getItem("nicheflow_user");
    if (stored) { try { const u=JSON.parse(stored); setUser(u); setView("app"); } catch {} }
  },[]);

  function handleAuthSuccess(userData) {
    localStorage.setItem("nicheflow_user", JSON.stringify(userData));
    setUser(userData); setView("app");
  }
  function handleLogout() {
    localStorage.removeItem("nicheflow_user");
    setUser(null); setView("landing");
  }
  function handleCheckoutFromLanding(planType) {
    const url = planType === "pro" ? CHECKOUT_PRO : CHECKOUT_BASIC;
    const email = user?.user?.email || user?.email || "";
    window.open(`${url}?wanted=true${email ? `&email=${encodeURIComponent(email)}` : ""}`, "_blank");
  }
  function handlePolicy(page) { setPolicyPage(page); }
  function handleBackFromPolicy() { setPolicyPage(null); }

  // ── Policy pages — accessible from anywhere ──
  if (policyPage === "privacy") return <PrivacyPolicyPage onBack={handleBackFromPolicy} />;
  if (policyPage === "refund")  return <RefundPolicyPage  onBack={handleBackFromPolicy} />;
  if (policyPage === "terms")   return <TermsOfServicePage onBack={handleBackFromPolicy} />;

  if (view==="app"&&user) return <AppShell user={user} onLogout={handleLogout} onPolicy={handlePolicy}/>;
  if (view==="login"||view==="signup") return (
    <AuthPage mode={view} onSuccess={handleAuthSuccess} onSwitch={setView} onBack={()=>setView("landing")}/>
  );
  return (
    <LandingPage
      onLogin={()=>setView("login")}
      onSignup={()=>setView("signup")}
      onCheckout={handleCheckoutFromLanding}
      onPolicy={handlePolicy}
    />
  );
}