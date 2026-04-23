cat > /home/claude/App.jsx << 'ENDOFFILE'
import { useState, useEffect, useRef, useCallback } from "react";

// ─── Config ────────────────────────────────────────────────────────────────
const SUPABASE_URL = "https://gfulpvqqpakcgubkilwc.supabase.co";
const SUPABASE_KEY = "sb_publishable_U9zJp_BBd-jkJCwvGimNmw_E4NyynFN";
const API_URL = "https://web-production-1f143.up.railway.app";

// ── PADDLE CHECKOUT LINKS — replace with your real Paddle links after approval
const CHECKOUT_BASIC = "https://buy.paddle.com/product/REPLACE_WITH_BASIC_ID";
const CHECKOUT_PRO   = "https://buy.paddle.com/product/REPLACE_WITH_PRO_ID";

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
  if (!createdAt) return TRIAL_DAYS;
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

.legal-page{min-height:100vh;background:var(--bg);}
.legal-container{max-width:760px;margin:0 auto;padding:60px 24px 100px;}
.legal-badge{display:inline-flex;align-items:center;gap:6px;padding:5px 14px;background:var(--accent-dim);border:1px solid rgba(99,102,241,.25);border-radius:20px;font-size:12px;font-weight:600;color:var(--accent2);letter-spacing:.5px;text-transform:uppercase;margin-bottom:20px;}
.legal-h1{font-family:var(--font-display);font-size:clamp(28px,5vw,42px);font-weight:800;letter-spacing:-1px;margin-bottom:8px;}
.legal-subtitle{color:var(--text3);font-size:14px;margin-bottom:48px;padding-bottom:32px;border-bottom:1px solid var(--border);}
.legal-h2{font-family:var(--font-display);font-size:18px;font-weight:700;color:var(--text);margin:40px 0 12px;display:flex;align-items:center;gap:10px;}
.legal-h2::before{content:'';display:inline-block;width:4px;height:18px;background:var(--accent);border-radius:2px;flex-shrink:0;}
.legal-p{color:var(--text2);font-size:15px;margin-bottom:14px;line-height:1.7;}
.legal-ul{color:var(--text2);font-size:15px;padding-left:20px;margin-bottom:14px;}
.legal-ul li{margin-bottom:8px;line-height:1.6;}
.legal-highlight{background:var(--accent-dim);border:1px solid rgba(99,102,241,.18);border-radius:12px;padding:16px 20px;margin:20px 0;color:var(--accent2);font-size:14px;line-height:1.6;}
.legal-green{background:var(--green-dim);border:1px solid rgba(16,185,129,.25);border-radius:12px;padding:20px 24px;margin:16px 0;}
.legal-red{background:var(--red-dim);border:1px solid rgba(239,68,68,.2);border-radius:12px;padding:20px 24px;margin:16px 0;}
.legal-green-title{font-family:var(--font-display);font-size:15px;font-weight:700;color:var(--green);margin-bottom:12px;}
.legal-red-title{font-family:var(--font-display);font-size:15px;font-weight:700;color:var(--red);margin-bottom:12px;}
.legal-step{display:flex;gap:16px;margin-bottom:20px;align-items:flex-start;}
.legal-step-num{width:32px;height:32px;border-radius:50%;background:var(--accent-dim);border:1px solid rgba(99,102,241,.3);color:var(--accent2);font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.legal-step-title{font-size:14px;font-weight:600;color:var(--text);margin-bottom:4px;}
.legal-step-desc{font-size:14px;color:var(--text2);line-height:1.6;}
.legal-table{width:100%;border-collapse:collapse;margin:16px 0;font-size:14px;}
.legal-table th{text-align:left;padding:10px 14px;background:var(--accent-dim);color:var(--accent2);font-weight:600;border:1px solid rgba(99,102,241,.2);}
.legal-table td{padding:10px 14px;color:var(--text2);border:1px solid var(--border);}

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

// ─── LEGAL PAGE NAV ────────────────────────────────────────────────────────
function LegalNav() {
  return (
    <nav className="nav">
      <div className="nav-brand" style={{cursor:"pointer"}} onClick={()=>window.location.href="/"}>
        <Logo size={26}/><span>NicheFlow AI</span>
      </div>
      <a href="mailto:flowengine87@gmail.com" style={{fontSize:13,color:"var(--text3)",textDecoration:"none"}}>Contact</a>
    </nav>
  );
}

function LegalFooter() {
  return (
    <footer style={{borderTop:"1px solid var(--border)",padding:"28px 24px",textAlign:"center"}}>
      <div style={{display:"flex",justifyContent:"center",gap:28,flexWrap:"wrap",marginBottom:12}}>
        <a href="/terms" style={{fontSize:13,color:"var(--text3)",textDecoration:"none"}}>Terms of Service</a>
        <a href="/privacy" style={{fontSize:13,color:"var(--text3)",textDecoration:"none"}}>Privacy Policy</a>
        <a href="/refund" style={{fontSize:13,color:"var(--text3)",textDecoration:"none"}}>Refund Policy</a>
      </div>
      <div style={{fontSize:13,color:"var(--text3)"}}>© 2026 NicheFlow AI. All rights reserved.</div>
    </footer>
  );
}

// ─── TERMS OF SERVICE PAGE ─────────────────────────────────────────────────
function TermsPage() {
  return (
    <div className="legal-page">
      <style>{css}</style>
      <LegalNav/>
      <div className="legal-container" style={{paddingTop:100}}>
        <div className="legal-badge">✦ Legal</div>
        <h1 className="legal-h1">Terms of Service</h1>
        <p className="legal-subtitle">Last updated: April 23, 2026 · Effective immediately upon account creation</p>
        <div className="legal-highlight">By creating an account or using NicheFlow AI, you agree to these Terms of Service in full. Please read them carefully before using the platform.</div>

        <h2 className="legal-h2">1. About NicheFlow AI</h2>
        <p className="legal-p">NicheFlow AI is a SaaS platform that automates content creation, image generation, and WordPress publishing for content creators. Contact: <a href="mailto:flowengine87@gmail.com" style={{color:"var(--accent2)"}}>flowengine87@gmail.com</a></p>

        <h2 className="legal-h2">2. Eligibility</h2>
        <p className="legal-p">You must be at least 18 years old to use NicheFlow AI. By using the service, you confirm that you are legally capable of entering into a binding agreement.</p>

        <h2 className="legal-h2">3. Account Registration</h2>
        <p className="legal-p">You must provide a valid email address and a secure password to create an account. You are responsible for keeping your login credentials confidential and all activity that occurs under your account.</p>

        <h2 className="legal-h2">4. Free Trial</h2>
        <p className="legal-p">New accounts receive a 2-day free trial with full access to the platform. No credit card is required during the trial. After 2 days, access is restricted until a paid plan is purchased.</p>

        <h2 className="legal-h2">5. Paid Plans & Billing</h2>
        <p className="legal-p">NicheFlow AI offers subscription plans billed monthly:</p>
        <ul className="legal-ul">
          <li><strong style={{color:"var(--text)"}}>Basic — $30/month:</strong> Unlimited articles, images, WordPress publishing, internal linking.</li>
          <li><strong style={{color:"var(--text)"}}>Pro — $40/month:</strong> Everything in Basic plus Pinterest automation, AI pin images, and scheduling.</li>
        </ul>
        <p className="legal-p">Payments are processed securely by Paddle. By subscribing, you authorize recurring monthly charges to your payment method until you cancel.</p>

        <h2 className="legal-h2">6. Cancellation & Refunds</h2>
        <p className="legal-p">You may cancel your subscription at any time. Cancellation takes effect at the end of the current billing period. See our <a href="/refund" style={{color:"var(--accent2)"}}>Refund Policy</a> for details on refunds.</p>

        <h2 className="legal-h2">7. Acceptable Use</h2>
        <p className="legal-p">You agree not to use NicheFlow AI to generate spam or deceptive content, violate any applicable law, reverse engineer or resell the platform, or abuse the service in a way that degrades performance for other users.</p>

        <h2 className="legal-h2">8. Third-Party Services</h2>
        <p className="legal-p">NicheFlow AI integrates with Groq, Google Gemini, GoAPI (Midjourney), WordPress REST API, Pinterest API, Supabase, and Paddle. Your use of these services is subject to their respective terms. We are not responsible for third-party service availability.</p>

        <h2 className="legal-h2">9. Content Ownership</h2>
        <p className="legal-p">You retain full ownership of all content you generate using NicheFlow AI. We do not claim any rights to your articles, images, or published posts.</p>

        <h2 className="legal-h2">10. Limitation of Liability</h2>
        <p className="legal-p">NicheFlow AI is provided "as is" without warranties of any kind. To the maximum extent permitted by law, NicheFlow AI shall not be liable for any indirect, incidental, or consequential damages arising from your use of the platform.</p>

        <h2 className="legal-h2">11. Termination</h2>
        <p className="legal-p">We reserve the right to suspend or terminate your account at any time for violation of these Terms or fraudulent activity.</p>

        <h2 className="legal-h2">12. Changes to Terms</h2>
        <p className="legal-p">We may update these Terms from time to time. Continued use after changes are posted constitutes acceptance. We will notify users of significant changes by email.</p>

        <h2 className="legal-h2">13. Contact</h2>
        <p className="legal-p">For questions: <a href="mailto:flowengine87@gmail.com" style={{color:"var(--accent2)"}}>flowengine87@gmail.com</a></p>
      </div>
      <LegalFooter/>
    </div>
  );
}

// ─── PRIVACY POLICY PAGE ───────────────────────────────────────────────────
function PrivacyPage() {
  return (
    <div className="legal-page">
      <style>{css}</style>
      <LegalNav/>
      <div className="legal-container" style={{paddingTop:100}}>
        <div className="legal-badge">✦ Legal</div>
        <h1 className="legal-h1">Privacy Policy</h1>
        <p className="legal-subtitle">Last updated: April 23, 2026 · We take your privacy seriously.</p>
        <div className="legal-highlight">This Privacy Policy explains what data we collect, how we use it, and your rights regarding your personal information when you use NicheFlow AI.</div>

        <h2 className="legal-h2">1. Who We Are</h2>
        <p className="legal-p">NicheFlow AI is a SaaS content automation platform. Contact: <a href="mailto:flowengine87@gmail.com" style={{color:"var(--accent2)"}}>flowengine87@gmail.com</a></p>

        <h2 className="legal-h2">2. Data We Collect</h2>
        <table className="legal-table">
          <thead><tr><th>Data Type</th><th>Purpose</th></tr></thead>
          <tbody>
            <tr><td>Email address</td><td>Account creation, login, and communication</td></tr>
            <tr><td>Password (hashed)</td><td>Authentication — never stored in plain text</td></tr>
            <tr><td>API keys you enter</td><td>Stored encrypted to connect your AI and WordPress services</td></tr>
            <tr><td>Generated article titles</td><td>Displayed in your history dashboard</td></tr>
            <tr><td>Published post URLs</td><td>Stored for your history and Pinterest automation</td></tr>
            <tr><td>Subscription plan & status</td><td>To determine your access level</td></tr>
          </tbody>
        </table>
        <p className="legal-p">We do not collect your full name, phone number, home address, or financial payment information (payments are handled by Paddle).</p>

        <h2 className="legal-h2">3. How We Use Your Data</h2>
        <ul className="legal-ul">
          <li>To provide and operate the NicheFlow AI service</li>
          <li>To authenticate your account and protect against unauthorized access</li>
          <li>To process subscription payments via Paddle</li>
          <li>To send transactional emails (account confirmation, payment receipts)</li>
          <li>To respond to your support requests</li>
        </ul>
        <p className="legal-p">We do <strong style={{color:"var(--text)"}}>not</strong> sell, rent, or share your personal data with third parties for marketing purposes.</p>

        <h2 className="legal-h2">4. Third-Party Services</h2>
        <ul className="legal-ul">
          <li><strong style={{color:"var(--text)"}}>Supabase</strong> — Database and authentication</li>
          <li><strong style={{color:"var(--text)"}}>Groq / Google Gemini</strong> — AI text generation. Your article titles are sent to these APIs.</li>
          <li><strong style={{color:"var(--text)"}}>GoAPI (Midjourney)</strong> — Image generation. Your image prompts are sent to this API.</li>
          <li><strong style={{color:"var(--text)"}}>WordPress REST API</strong> — Publishing to your own WordPress site</li>
          <li><strong style={{color:"var(--text)"}}>Pinterest API</strong> — Pin creation using your access token</li>
          <li><strong style={{color:"var(--text)"}}>Paddle</strong> — Processes subscription payments. We never see your card details.</li>
          <li><strong style={{color:"var(--text)"}}>Railway / Vercel</strong> — Hosting infrastructure</li>
        </ul>

        <h2 className="legal-h2">5. Data Storage & Security</h2>
        <p className="legal-p">Your data is stored securely on Supabase with row-level security. API keys are stored encrypted. Passwords are hashed and never stored in plain text. We use HTTPS for all data transmission.</p>

        <h2 className="legal-h2">6. Your Rights</h2>
        <ul className="legal-ul">
          <li><strong style={{color:"var(--text)"}}>Access</strong> — Request a copy of the data we hold about you</li>
          <li><strong style={{color:"var(--text)"}}>Correction</strong> — Ask us to correct inaccurate data</li>
          <li><strong style={{color:"var(--text)"}}>Deletion</strong> — Request deletion of your account and personal data</li>
          <li><strong style={{color:"var(--text)"}}>Portability</strong> — Request your data in a portable format</li>
        </ul>
        <p className="legal-p">To exercise these rights: <a href="mailto:flowengine87@gmail.com" style={{color:"var(--accent2)"}}>flowengine87@gmail.com</a></p>

        <h2 className="legal-h2">7. Cookies</h2>
        <p className="legal-p">NicheFlow AI uses minimal cookies and browser local storage for session management and saving your settings locally. We do not use tracking cookies or third-party advertising cookies.</p>

        <h2 className="legal-h2">8. Contact</h2>
        <p className="legal-p">For privacy questions: <a href="mailto:flowengine87@gmail.com" style={{color:"var(--accent2)"}}>flowengine87@gmail.com</a></p>
      </div>
      <LegalFooter/>
    </div>
  );
}

// ─── REFUND POLICY PAGE ────────────────────────────────────────────────────
function RefundPage() {
  return (
    <div className="legal-page">
      <style>{css}</style>
      <LegalNav/>
      <div className="legal-container" style={{paddingTop:100}}>
        <div className="legal-badge">✦ Legal</div>
        <h1 className="legal-h1">Refund Policy</h1>
        <p className="legal-subtitle">Last updated: April 23, 2026 · We want you to be satisfied.</p>
        <div className="legal-highlight">We offer a <strong>7-day money-back guarantee</strong> for all new paid subscriptions. If you are not satisfied within the first 7 days of your first payment, contact us for a full refund — no questions asked.</div>

        <h2 className="legal-h2">Free Trial First</h2>
        <p className="legal-p">Before any payment, every new user gets a <strong style={{color:"var(--text)"}}>2-day free trial</strong> with full access to the platform. We encourage you to use the trial to evaluate the service before subscribing. No credit card is required.</p>

        <h2 className="legal-h2">Eligible for a Refund</h2>
        <div className="legal-green">
          <div className="legal-green-title">✓ You qualify for a full refund if:</div>
          <ul className="legal-ul">
            <li>You request a refund within <strong>7 days</strong> of your first payment on a new subscription</li>
            <li>You experienced a technical issue on our end that prevented you from using the service</li>
            <li>You were charged incorrectly or more than once due to a billing error</li>
          </ul>
        </div>

        <h2 className="legal-h2">Not Eligible for a Refund</h2>
        <div className="legal-red">
          <div className="legal-red-title">✗ Refunds are not issued if:</div>
          <ul className="legal-ul">
            <li>More than 7 days have passed since your first payment on the current subscription</li>
            <li>You are requesting a refund for a renewal charge (you had access during the billing period)</li>
            <li>Your account was suspended due to a violation of our Terms of Service</li>
            <li>You forgot to cancel before the renewal date</li>
          </ul>
        </div>

        <h2 className="legal-h2">How to Request a Refund</h2>
        <div>
          {[
            {n:"1", t:"Email us within 7 days", d:<>Send an email to <a href="mailto:flowengine87@gmail.com" style={{color:"var(--accent2)"}}>flowengine87@gmail.com</a> with subject: <strong>"Refund Request — NicheFlow AI"</strong></>},
            {n:"2", t:"Include your details", d:"Provide the email address you used to sign up and the approximate date of your payment."},
            {n:"3", t:"Processed within 3–5 business days", d:"Once approved, your refund is processed through Paddle. Funds appear within 5–10 business days depending on your bank."},
          ].map(s=>(
            <div key={s.n} className="legal-step">
              <div className="legal-step-num">{s.n}</div>
              <div>
                <div className="legal-step-title">{s.t}</div>
                <div className="legal-step-desc">{s.d}</div>
              </div>
            </div>
          ))}
        </div>

        <h2 className="legal-h2">Cancellation</h2>
        <p className="legal-p">You can cancel your subscription at any time. Cancellation stops future charges but does not issue a refund for the current billing period — you keep access until the end of the period you paid for.</p>
        <p className="legal-p">To cancel, contact us at <a href="mailto:flowengine87@gmail.com" style={{color:"var(--accent2)"}}>flowengine87@gmail.com</a> or manage your subscription via Paddle's customer portal (link sent in your payment confirmation email).</p>

        <h2 className="legal-h2">Contact</h2>
        <p className="legal-p"><a href="mailto:flowengine87@gmail.com" style={{color:"var(--accent2)"}}>flowengine87@gmail.com</a> — We respond within 24 hours on business days.</p>
      </div>
      <LegalFooter/>
    </div>
  );
}

// ─── TOP BAR ───────────────────────────────────────────────────────────────
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
    const cls = daysLeft <= 3 ? "top-bar-sub-warn" : "top-bar-sub-ok";
    const expired = daysLeft === 0;
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
        <p style={{fontSize:12,color:"var(--text3)"}}>Secure checkout via Paddle · Cancel anytime</p>
      </div>
    </div>
  );
}

// ─── CHECKOUT MODAL — PADDLE ───────────────────────────────────────────────
function CheckoutModal({ plan, onClose, userEmail }) {
  const url = plan === "pro" ? CHECKOUT_PRO : CHECKOUT_BASIC;
  const fullUrl = `${url}?prefilled_email=${encodeURIComponent(userEmail || "")}`;
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
            style={{ width:"100%",marginBottom:12 }}>
            Continue to Payment →
          </a>
          <p style={{ fontSize:12,color:"var(--text3)" }}>Secure checkout via Paddle · Cancel anytime</p>
        </div>
      </div>
    </div>
  );
}

// ─── LANDING ───────────────────────────────────────────────────────────────
function LandingPage({ onLogin, onSignup, onCheckout }) {
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
      {/* ── FOOTER WITH LEGAL LINKS ── */}
      <footer style={{ borderTop:"1px solid var(--border)",padding:"32px 48px",maxWidth:1100,margin:"0 auto" }}>
        <div style={{ display:"flex",justifyContent:"space-between",alignItems:"center",flexWrap:"wrap",gap:16 }}>
          <div className="nav-brand"><Logo size={20}/><span>NicheFlow AI</span></div>
          <div style={{ display:"flex",gap:24,flexWrap:"wrap" }}>
            <a href="/terms" style={{ fontSize:13,color:"var(--text3)",textDecoration:"none" }}>Terms of Service</a>
            <a href="/privacy" style={{ fontSize:13,color:"var(--text3)",textDecoration:"none" }}>Privacy Policy</a>
            <a href="/refund" style={{ fontSize:13,color:"var(--text3)",textDecoration:"none" }}>Refund Policy</a>
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
        if (data.session || data.access_token) {
          onSuccess(data.session || data);
        } else {
          setStep("confirm");
        }
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
            <button className="btn btn-primary" style={{ width:"100%",marginBottom:10 }}
              onClick={() => { setStep("form"); onSwitch("login"); }}>
              Go to Login →
            </button>
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
    if (msg.includes("✅") || msg.includes("🎉") || msg.includes("Published")) return "ok";
    if (msg.includes("❌") || msg.includes("Failed") || msg.includes("failed")) return "err";
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
          title,
          gemini_key:config.gemini_key||"",
          goapi_key:config.goapi_key||"",
          wp_url:config.wp_url||"",
          wp_password:config.wp_password||"",
          custom_prompt:config.custom_prompt||"",
          card_prompt:config.card_prompt||"",
          mj_template:config.mj_template||"",
          publish_status:draft?"draft":(config.publish_status||"publish"),
          use_images:useImages,
          use_pollinations:config.use_pollinations||false,
          pollinations_prompt:config.pollinations_prompt||"",
          show_card:config.show_card!==false,
          use_internal_links:config.use_internal_links!==false,
          max_links:config.max_links||4
        };
        const token=getStoredToken();
        const res=await fetch(`${API_URL}/pipeline`,{
          method:"POST",
          headers:{"Content-Type":"application/json",...(token?{"Authorization":`Bearer ${token}`}:{})},
          body:JSON.stringify(payload)
        });
        let data;
        try{data=await res.json();}catch{data={success:false,error:`Server ${res.status}`};}
        if(data.logs && Array.isArray(data.logs)){
          for(const logMsg of data.logs){ addLog(logMsg, detectLogType(logMsg)); }
        }
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
      if(i<titleList.length-1&&delay>0){
        addLog(`⏱ Waiting ${delay}s...`,"info");
        await new Promise(r=>setTimeout(r,delay*1000));
      }
    }
    setProgress(1);
    addLog(`Batch complete.`,"ok");
    setRunning(false);
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
            <div><label className="form-label">Default delay between articles (seconds)</label><input className="input" type="number" value={cfg.delay_sec||10} min={0} max={120} onChange={e=>update("delay_sec",+e.target.value)} style={{width:100}}/></div>
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

// ─── PINTEREST PAGE ────────────────────────────────────────────────────────
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
    if(config.pinterest_token && boards.length === 0){ loadBoards(); }
  // eslint-disable-next-line
  },[config.pinterest_token]);

  const publishedArticles = history.filter(h=>h.status==="published"&&h.post_url);

  async function loadBoards(){
    setLoadingBoards(true);setBoardError("");
    try{
      const res=await apiCall("/pinterest/boards");
      const data=await res.json();
      if(res.ok){ setBoards(data.boards||[]); if(!data.boards?.length) setBoardError("No boards found. Check your Pinterest token in Settings."); }
      else setBoardError(data.detail||"Failed to load boards");
    }catch(e){setBoardError(e.message);}
    finally{setLoadingBoards(false);}
  }

  async function runPinterest(){
    if(!publishedArticles.length){addLog("No published articles to pin.","warn");return;}
    if(!selectedBoards.length){addLog("Select at least one board.","warn");return;}
    let scheduled_at = null;
    if(scheduleEnabled && scheduleDate){
      scheduled_at = `${scheduleDate}T${scheduleTime || "09:00"}:00`;
      addLog(`📅 Scheduling pins for: ${scheduled_at}`, "info");
    }
    setRunning(true);
    addLog(`Starting Pinterest bot: ${publishedArticles.length} articles → ${selectedBoards.length} board(s)`,"ok");
    try{
      const res=await apiCall("/pinterest/run",{method:"POST",body:JSON.stringify({board_ids:selectedBoards,pin_image_prompt:config.pin_image_prompt||"",scheduled_at})});
      const data=await res.json();
      if(res.ok){
        const results=data.results||[];
        setPinPreviews(results);
        results.forEach(r=>{ addLog(`📌 ${r.title}`,"info"); r.boards?.forEach(b=>{addLog(b.success?`  ✅ Board ${b.board_id} → Pin ${b.pin_id}`:`  ❌ ${b.error}`,b.success?"ok":"err");}); });
        addLog(`Done! ${results.filter(r=>r.status==="sent").length}/${results.length} pinned.`,"ok");
      } else addLog(`❌ ${data.detail||"Pinterest run failed"}`,"err");
    }catch(e){addLog(`❌ ${e.message}`,"err");}
    finally{setRunning(false);}
  }

  function toggleBoard(id){setSelectedBoards(prev=>prev.includes(id)?prev.filter(b=>b!==id):[...prev,id]);}
  const logCls={ok:"log-ok",err:"log-err",info:"log-info",warn:"log-warn"};
  const tomorrow = new Date(); tomorrow.setDate(tomorrow.getDate()+1);
  const tomorrowStr = tomorrow.toISOString().split("T")[0];

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
                :<div className="pin-img" style={{height:240,display:"flex",alignItems:"center",justifyContent:"center",color:"var(--text3)"}}>No pin image</div>}
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
          <button className="btn btn-pro" style={{width:"100%",padding:"13px"}} onClick={runPinterest} disabled={running||!publishedArticles.length||!selectedBoards.length||(scheduleEnabled&&!scheduleDate)}>
            {running?<><span className="spinner"/>Pinning...</>: scheduleEnabled&&scheduleDate ? `📅 Schedule ${publishedArticles.length} Pin${publishedArticles.length!==1?"s":""}` : `📌 Pin ${publishedArticles.length} Article${publishedArticles.length!==1?"s":""}`}
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
            :logs.map((l,i)=><div key={i} className="log-line"><span className="log-time">[{l.time}]</span><span className={logCls[l.type]||""}>{l.msg}</span></div>)}
        </div>
      </div>
    </div>
  );
}

// ─── DOCS PAGE ─────────────────────────────────────────────────────────────
function DocsPage({ plan, onUpgrade }) {
  const [section, setSection] = useState("start");
  const sections = [
    { id: "start", label: "🚀 Quick Start" },{ id: "api", label: "🔑 API Keys" },
    { id: "wordpress", label: "🌐 WordPress" },{ id: "prompts", label: "💬 Prompts & Cards" },
    { id: "images", label: "🖼️ Images & WebP" },{ id: "links", label: "🔗 Internal Links" },
    { id: "pinterest", label: "📌 Pinterest (Pro)" },{ id: "billing", label: "💳 Billing & Plans" },
  ];
  return (
    <div className="fade-up" style={{ display: "flex", gap: 24 }}>
      <div style={{ width: 190, flexShrink: 0 }}>
        <div style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", padding: 8, position: "sticky", top: 20 }}>
          {sections.map(s => (
            <button key={s.id} onClick={() => setSection(s.id)}
              style={{ display: "block", width: "100%", padding: "8px 12px", borderRadius: 8, border: "none",
                background: section === s.id ? "var(--accent-dim)" : "transparent",
                color: section === s.id ? "var(--accent2)" : "var(--text2)",
                fontSize: 13, textAlign: "left", cursor: "pointer", fontFamily: "var(--font)", marginBottom: 2 }}>
              {s.label}
            </button>
          ))}
        </div>
      </div>
      <div style={{ flex: 1 }}>
        {section === "start" && (<div className="doc-section"><h3>🚀 Quick Start</h3><p style={{ fontSize: 14, color: "var(--text2)", marginBottom: 20, lineHeight: 1.7 }}>Get your first article published in under 5 minutes.</p>{[{n:"1",t:"Get a free AI key",d:<>Go to <a href="https://console.groq.com" target="_blank" rel="noreferrer" style={{color:"var(--accent2)"}}>console.groq.com</a> — free key starting with <code>gsk_</code>. Or use Gemini at <a href="https://aistudio.google.com" target="_blank" rel="noreferrer" style={{color:"var(--accent2)"}}>aistudio.google.com</a> (starts with <code>AIza</code>). Both are free.</>},{n:"2",t:"Configure API Keys",d:<>Go to <strong>Settings → API Keys</strong>, paste your key, hit <strong>Test</strong>, then <strong>Save Settings</strong>.</>},{n:"3",t:"Connect WordPress",d:<>Go to <strong>Settings → WordPress</strong>. Enter your site URL and an App Password in format <code>username:xxxx xxxx xxxx xxxx</code>.</>},{n:"4",t:"Write your Prompts",d:<>Go to <strong>Settings → Prompts</strong>. Write your Article Prompt (use <code>{"{title}"}</code> as placeholder).</>},{n:"5",t:"Set up Images (optional)",d:<>Go to <strong>Settings → Images</strong>. Paste a Midjourney template or turn on Pollinations for free images.</>},{n:"6",t:"Generate your first article",d:<>Go to <strong>Generate</strong>, paste titles (one per line), and click Generate.</>}].map(s=>(<div key={s.n} className="doc-step"><div className="doc-step-num">{s.n}</div><div className="doc-step-text"><div className="doc-step-title">{s.t}</div><div className="doc-step-desc">{s.d}</div></div></div>))}</div>)}
        {section === "api" && (<div style={{display:"flex",flexDirection:"column",gap:16}}><div className="doc-section"><h3>🔑 AI Keys — Groq & Gemini</h3><div className="alert alert-info" style={{marginBottom:16}}>Use Groq, Gemini, or both comma-separated for automatic fallback.</div>{[{t:"Groq (recommended, free)",d:<>Sign up at <a href="https://console.groq.com" target="_blank" rel="noreferrer" style={{color:"var(--accent2)"}}>console.groq.com</a>. Key starts with <code>gsk_</code>.</>},{t:"Gemini (backup, free)",d:<>Sign up at <a href="https://aistudio.google.com" target="_blank" rel="noreferrer" style={{color:"var(--accent2)"}}>aistudio.google.com</a>. Key starts with <code>AIza</code>.</>},{t:"Using both keys",d:<>Enter both comma-separated: <code>gsk_abc123, AIzaSyXxx</code>. Groq is tried first, Gemini used on failure.</>},{t:"Testing your key",d:"Click the Test button. It makes a live API call and confirms if the key is valid."}].map((s,i)=>(<div key={i} className="doc-step"><div className="doc-step-num">{i+1}</div><div className="doc-step-text"><div className="doc-step-title">{s.t}</div><div className="doc-step-desc">{s.d}</div></div></div>))}</div><div className="doc-section"><h3>🔑 GoAPI Key (Midjourney)</h3><div className="alert alert-warn" style={{marginBottom:14}}>Only needed for Midjourney images. Skip if using Pollinations (free).</div>{[{t:"Get your GoAPI key",d:<>Sign up at <a href="https://goapi.ai" target="_blank" rel="noreferrer" style={{color:"var(--accent2)"}}>goapi.ai</a>. Go to Dashboard → API Keys.</>},{t:"How it works",d:"GoAPI submits ONE prompt to Midjourney → NicheFlow downloads the 2×2 grid → crops 4 WebP images → uploads all 4 to WordPress."},{t:"Cost",d:"GoAPI charges per MJ generation. Each article = 1 request = 4 images. Check their dashboard for pricing."}].map((s,i)=>(<div key={i} className="doc-step"><div className="doc-step-num">{i+1}</div><div className="doc-step-text"><div className="doc-step-title">{s.t}</div><div className="doc-step-desc">{s.d}</div></div></div>))}</div></div>)}
        {section === "wordpress" && (<div style={{display:"flex",flexDirection:"column",gap:16}}><div className="doc-section"><h3>🌐 Connecting WordPress</h3>{[{t:"Site URL",d:<>Enter your full URL including <code>https://</code>, no trailing slash.</>},{t:"Create an Application Password",d:<>In WordPress: <strong>Users → Profile → Application Passwords → Add New</strong>. Copy the password immediately.</>},{t:"Format the credentials",d:<>Enter as: <code>yourusername:xxxx xxxx xxxx xxxx</code></>},{t:"Test the connection",d:"Click Test Connection — it shows your WordPress display name if successful."},{t:"Required WordPress settings",d:<>Permalinks must not be set to Plain (WordPress → Settings → Permalinks → choose any other option).</>}].map((s,i)=>(<div key={i} className="doc-step"><div className="doc-step-num">{i+1}</div><div className="doc-step-text"><div className="doc-step-title">{s.t}</div><div className="doc-step-desc">{s.d}</div></div></div>))}</div></div>)}
        {section === "prompts" && (<div style={{display:"flex",flexDirection:"column",gap:16}}><div className="doc-section"><h3>💬 Article Prompt</h3><div className="alert alert-info" style={{marginBottom:14}}>Write your prompt as if briefing a writer. Be specific about tone, structure, length, and audience.</div>{[{t:"Required placeholder",d:<>Always include <code>{"{title}"}</code> in your prompt.</>},{t:"Required JSON output",d:<>The AI must return: <code>html_content</code>, <code>seo_title</code>, <code>excerpt</code>, and color hex fields: <code>MAIN</code>, <code>MAIN_DARK</code>, <code>LIGHT_BG</code>, <code>BORDER</code>.</>},{t:"Image placeholders",d:<>Include <code>##IMAGE1##</code>, <code>##IMAGE2##</code>, <code>##IMAGE3##</code> in html_content where you want images.</>},{t:"Example prompt",d:null}].map((s,i)=>(<div key={i} className="doc-step"><div className="doc-step-num">{i+1}</div><div className="doc-step-text"><div className="doc-step-title">{s.t}</div>{s.d&&<div className="doc-step-desc">{s.d}</div>}{i===3&&<pre>{`You are Emma, a warm mama blogger.\nWrite a detailed article about: {title}\nReturn ONLY valid JSON:\n{\n  "seo_title": "...",\n  "excerpt": "...",\n  "html_content": "...",\n  "MAIN": "#hex", "MAIN_DARK": "#hex",\n  "LIGHT_BG": "#hex", "BORDER": "#hex"\n}`}</pre>}</div></div>))}</div><div className="doc-section"><h3>🃏 Card Prompt</h3><div className="alert alert-info" style={{marginBottom:14}}>The card is a summary widget appended at the end of each article.</div>{[{t:"What the card outputs",d:<>Return: <code>card_title</code>, <code>summary</code>, <code>key_points</code> array, <code>quick_facts</code> array, <code>cta_text</code>.</>},{t:"CTA button",d:"Triggers browser share on mobile or copies URL on desktop."},{t:"Example",d:null}].map((s,i)=>(<div key={i} className="doc-step"><div className="doc-step-num">{i+1}</div><div className="doc-step-text"><div className="doc-step-title">{s.t}</div>{s.d&&<div className="doc-step-desc">{s.d}</div>}{i===2&&<pre>{`For "{title}", return ONLY valid JSON:\n{\n  "card_title": "Quick Summary",\n  "summary": "2-sentence overview.",\n  "key_points": ["Point 1","Point 2","Point 3"],\n  "quick_facts": [{"label":"Time","value":"10 mins"}],\n  "cta_text": "Save this! 📌"\n}`}</pre>}</div></div>))}</div></div>)}
        {section === "images" && (<div style={{display:"flex",flexDirection:"column",gap:16}}><div className="doc-section"><h3>🖼️ How Images Work</h3><div className="alert alert-info" style={{marginBottom:14}}>NicheFlow makes ONE Midjourney request per article → gets 2×2 grid → crops 4 WebP images → uploads all to WordPress.</div>{[{t:"1 MJ request → 4 images",d:"One prompt generates a 2×2 grid. NicheFlow downloads it immediately (before CDN expiry), crops into 4 pieces, converts to WebP."},{t:"Featured image = image 1",d:"The first cropped image is set as WP featured image. Images 2–4 go into ##IMAGE1## ##IMAGE2## ##IMAGE3##."},{t:"Aspect ratio from your template",d:<>The <code>--ar</code> flag controls crop ratio. E.g. <code>--ar 1:1</code> = square, <code>--ar 2:3</code> = portrait (Pinterest). Default: 1:1.</>},{t:"WebP conversion",d:"All images converted to WebP — smaller and faster than JPEG/PNG."},{t:"Pollinations (free)",d:"Enable in Settings → Images. Free AI images, no API key needed. Lower quality than Midjourney."},{t:"MJ template tips",d:<>Use <code>{"{title}"}</code> or <code>{"{recipe_name}"}</code>. Example: <code>Close up {"{title}"}, food photography --ar 1:1</code></>}].map((s,i)=>(<div key={i} className="doc-step"><div className="doc-step-num">{i+1}</div><div className="doc-step-text"><div className="doc-step-title">{s.t}</div><div className="doc-step-desc">{s.d}</div></div></div>))}</div></div>)}
        {section === "links" && (<div className="doc-section"><h3>🔗 Internal Links</h3><div className="alert alert-info" style={{marginBottom:14}}>Fetches your existing WordPress posts and injects relevant links into new articles automatically.</div>{[{t:"How it works",d:"Before publishing, NicheFlow fetches your published posts. For each post title (3+ words) found in the new article's body text, it wraps the phrase in an anchor tag."},{t:"Only paragraph text",d:"Links are only injected inside <p> tags — never in headings, FAQ questions, or existing links."},{t:"Max links per article",d:"Set the max in Settings → WordPress. Default is 4. Recommended: 3–5."},{t:"Enable / Disable",d:"Toggle in Settings → WordPress → Auto-inject internal links."}].map((s,i)=>(<div key={i} className="doc-step"><div className="doc-step-num">{i+1}</div><div className="doc-step-text"><div className="doc-step-title">{s.t}</div><div className="doc-step-desc">{s.d}</div></div></div>))}</div>)}
        {section === "pinterest" && (<div style={{display:"flex",flexDirection:"column",gap:16}}>{plan!=="pro"&&<div className="alert alert-warn">📌 Pinterest is a <strong>Pro feature</strong>. <button className="btn btn-pro btn-sm" onClick={()=>onUpgrade("pro")} style={{marginLeft:10}}>Upgrade to Pro ★</button></div>}<div className="doc-section"><h3>📌 Pinterest Setup</h3>{[{t:"Create a Pinterest Developer App",d:<>Go to <a href="https://developers.pinterest.com" target="_blank" rel="noreferrer" style={{color:"var(--accent2)"}}>developers.pinterest.com</a> → My Apps → Create App → Generate Access Token with scopes: <code>boards:read</code>, <code>pins:write</code>.</>},{t:"Paste the token",d:"Settings → Pinterest → Pinterest Access Token. Save settings."},{t:"Boards auto-load",d:"Opening the Pinterest page loads your boards automatically. Use Refresh to reload after adding/deleting boards."},{t:"Select boards and pin",d:"Select boards, then click Pin. NicheFlow creates a pin for each published article on every selected board."},{t:"Scheduling",d:"Enable the Schedule toggle to choose a future date and time. The Pinterest API schedules your pins exactly."}].map((s,i)=>(<div key={i} className="doc-step"><div className="doc-step-num">{i+1}</div><div className="doc-step-text"><div className="doc-step-title">{s.t}</div><div className="doc-step-desc">{s.d}</div></div></div>))}</div></div>)}
        {section === "billing" && (<div className="doc-section"><h3>💳 Billing & Plans</h3><div className="alert alert-info" style={{marginBottom:14}}>New users get a <strong>2-day free trial</strong> — no credit card. After 2 days, choose a plan to continue.</div>{[{t:"Free Trial — 2 days",d:"From account creation, 2 full days of access. Top bar shows countdown. After 2 days, paywall appears."},{t:"Basic — $30/month",d:"Unlimited articles, prompts, 4 images per article (featured + 3 body), WordPress publishing, internal links."},{t:"Pro — $40/month",d:"Everything in Basic plus Pinterest automation: AI pin images, hook titles, board selection, scheduling, auto-pin."},{t:"Subscription countdown",d:"After payment, top bar shows days left. Warning at 3 days. Prompt to renew at 0."},{t:"Payments via Paddle",d:"Paddle handles all payments securely. To cancel or manage your subscription, use Paddle's customer portal (link in your payment email)."},{t:"Plan not updating?",d:"Click Refresh Plan in the sidebar. Plan syncs via webhook — usually instant but can take up to a minute."}].map((s,i)=>(<div key={i} className="doc-step"><div className="doc-step-num">{i+1}</div><div className="doc-step-text"><div className="doc-step-title">{s.t}</div><div className="doc-step-desc">{s.d}</div></div></div>))}{plan!=="pro"&&<div style={{marginTop:20}}><button className="btn btn-pro" style={{width:"100%"}} onClick={()=>onUpgrade("pro")}>Upgrade to Pro — $40/mo ★</button></div>}</div>)}
      </div>
    </div>
  );
}

// ─── APP SHELL ─────────────────────────────────────────────────────────────
function AppShell({ user, onLogout }) {
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
  useEffect(() => { const i = setInterval(refreshPlan, 30000); return () => clearInterval(i); }, [refreshPlan]);

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
  const pageInfo={dashboard:["Dashboard","Welcome back."],generate:["Generate Articles","Paste titles, let AI handle everything."],preview:["Preview","Test article style before a full batch."],history:["History","All generated and published articles."],pinterest:["Pinterest Bot","Auto-pin with AI-generated hook title images."],docs:["Documentation","Everything you need to use NicheFlow AI."],settings:["Settings","API keys, prompts, and integrations."]};
  const [pageTitle,pageSub]=pageInfo[page]||["",""];

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
          <button className="nav-item" onClick={onLogout} style={{marginTop:2,color:"var(--text3)"}}><span>→</span>Sign out</button>
        </div>
      </aside>
      <main className="main-content">
        <TopBar createdAt={createdAt} plan={effectivePlan} planExpires={planExpires} onUpgrade={handleUpgrade} isAdmin={isAdmin}/>
        <div className="page-header"><h1 className="page-title">{pageTitle}</h1><p className="page-sub">{pageSub}</p></div>
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

// ─── ROOT — with path-based routing for legal pages ────────────────────────
export default function NicheFlowAI() {
  const [view, setView] = useState("landing");
  const [user, setUser] = useState(null);

  useEffect(()=>{
    // Check URL path first for legal pages
    const path = window.location.pathname;
    if (path === "/terms") { setView("terms"); return; }
    if (path === "/privacy") { setView("privacy"); return; }
    if (path === "/refund") { setView("refund"); return; }

    // Otherwise check if user is logged in
    const stored = localStorage.getItem("nicheflow_user");
    if (stored) {
      try { const u=JSON.parse(stored); setUser(u); setView("app"); } catch {}
    }
  },[]);

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
  function handleCheckoutFromLanding(planType) {
    const url = planType === "pro" ? CHECKOUT_PRO : CHECKOUT_BASIC;
    window.open(url, "_blank");
  }

  // Legal pages — no login required
  if (view==="terms") return <TermsPage/>;
  if (view==="privacy") return <PrivacyPage/>;
  if (view==="refund") return <RefundPage/>;

  if (view==="app"&&user) return <AppShell user={user} onLogout={handleLogout}/>;
  if (view==="login"||view==="signup") return (
    <AuthPage mode={view} onSuccess={handleAuthSuccess} onSwitch={setView} onBack={()=>setView("landing")}/>
  );
  return (
    <LandingPage onLogin={()=>setView("login")} onSignup={()=>setView("signup")} onCheckout={handleCheckoutFromLanding}/>
  );
}
ENDOFFILE
echo "Done. Lines: $(wc -l < /home/claude/App.jsx)"
Sortie

Command argument is 131_315 bytes, exceeding the 100_000-byte per-argument limit. For large content, pipe via stdin or use a file-write API instead of embedding the content inline in the command. Argument preview: 'cat > /home/claude/App.jsx << \'ENDOFFILE\'\nimport { useState, useEffect, useRef, useCallback } from "react";\n\n// ─── Config ────────────────────────────────────────────────────────────────\nconst SUPABA'
Terminé