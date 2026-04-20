import { useState, useEffect, useRef, useCallback } from "react";

// ─── Config ────────────────────────────────────────────────────────────────
const SUPABASE_URL = "https://gfulpvqqpakcgubkilwc.supabase.co";
const SUPABASE_KEY = "sb_publishable_U9zJp_BBd-jkJCwvGimNmw_E4NyynFN";
const API_URL = "https://web-production-1f143.up.railway.app";

// LemonSqueezy checkout URLs — set after approval
const CHECKOUT_BASIC = "https://nicheflowai.lemonsqueezy.com/buy/basic"; // replace after approval
const CHECKOUT_PRO   = "https://nicheflowai.lemonsqueezy.com/buy/pro";   // replace after approval

// ─── Auth helpers ──────────────────────────────────────────────────────────
async function supaSignup(email, password) {
  const res = await fetch(`${SUPABASE_URL}/auth/v1/signup`, {
    method: "POST",
    headers: { apikey: SUPABASE_KEY, "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, options: { emailRedirectTo: null } }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error_description || data.msg || "Signup failed");
  if (data.session) return data;
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

// ─── LOGO SVG ─────────────────────────────────────────────────────────────
function Logo({ size = 28 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="lg1" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#818cf8" />
          <stop offset="100%" stopColor="#c084fc" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="8" fill="url(#lg1)" />
      <path d="M8 22 L12 10 L16 18 L20 10 L24 22" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
      <circle cx="24" cy="10" r="2" fill="white" opacity="0.9"/>
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
.board-icon{font-size:22px;margin-bottom:6px;}
.board-name{font-size:12px;font-weight:500;color:var(--text2);}

.stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px;}
.stat-card{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius-lg);padding:18px;}
.stat-card-num{font-family:var(--font-display);font-size:26px;font-weight:700;}
.stat-card-label{font-size:12px;color:var(--text3);margin-top:4px;}

.history-item{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius-lg);padding:14px 18px;display:flex;align-items:center;gap:14px;margin-bottom:8px;transition:border-color .15s;}
.history-item:hover{border-color:var(--border2);}
.history-title{font-size:14px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.history-meta{font-size:12px;color:var(--text3);margin-top:2px;}

/* Modal overlay */
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:300;display:flex;align-items:center;justify-content:center;padding:20px;animation:fadeIn .2s ease;}
.modal{background:var(--bg2);border:1px solid var(--border2);border-radius:var(--radius-xl);padding:32px;max-width:600px;width:100%;max-height:85vh;overflow-y:auto;animation:fadeUp .25s ease;position:relative;}
.modal-close{position:absolute;top:16px;right:16px;background:var(--bg3);border:1px solid var(--border);border-radius:8px;width:30px;height:30px;display:flex;align-items:center;justify-content:center;cursor:pointer;color:var(--text3);font-size:14px;font-family:var(--font);}
.modal-close:hover{color:var(--text);background:var(--bg4);}

/* Pin preview card */
.pin-preview{background:var(--bg3);border:1px solid var(--border);border-radius:var(--radius-lg);overflow:hidden;margin-bottom:16px;}
.pin-img{width:100%;height:180px;object-fit:cover;display:block;background:var(--bg4);}
.pin-body{padding:14px;}
.pin-title{font-size:14px;font-weight:600;margin-bottom:6px;line-height:1.4;}
.pin-desc{font-size:12px;color:var(--text2);line-height:1.5;margin-bottom:8px;}
.pin-tags{display:flex;flex-wrap:wrap;gap:5px;}
.pin-tag{background:var(--accent-dim);color:var(--accent2);padding:2px 8px;border-radius:10px;font-size:11px;}

/* Doc sections */
.doc-section{background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius-lg);padding:24px;margin-bottom:16px;}
.doc-section h3{font-family:var(--font-display);font-size:16px;font-weight:600;margin-bottom:12px;display:flex;align-items:center;gap:8px;}
.doc-step{display:flex;gap:14px;margin-bottom:14px;align-items:flex-start;}
.doc-step-num{width:28px;height:28px;border-radius:50%;background:var(--accent-dim);color:var(--accent2);font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;border:1px solid rgba(99,102,241,.2);}
.doc-step-text{flex:1;}
.doc-step-title{font-size:14px;font-weight:600;margin-bottom:3px;}
.doc-step-desc{font-size:13px;color:var(--text2);line-height:1.6;}
code{background:var(--bg3);border:1px solid var(--border);padding:1px 6px;border-radius:5px;font-size:12px;font-family:'Courier New',monospace;color:var(--accent2);}
pre{background:var(--bg);border:1px solid var(--border);border-radius:var(--radius);padding:14px;font-size:12px;line-height:1.7;overflow-x:auto;color:var(--text2);font-family:'Courier New',monospace;margin:10px 0;}

/* Landing */
.landing{min-height:100vh;background:var(--bg);}
.nav{position:fixed;top:0;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:14px 48px;background:rgba(8,9,13,.9);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);}
.nav-brand{display:flex;align-items:center;gap:10px;font-family:var(--font-display);font-size:17px;font-weight:700;background:linear-gradient(135deg,var(--accent2),#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.nav-logo{font-family:var(--font-display);font-size:17px;font-weight:700;background:linear-gradient(135deg,var(--accent2),#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
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

/* App layout */
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

/* Auth */
.auth-page{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px;background:var(--bg);position:relative;}
.auth-page::before{content:'';position:fixed;inset:0;background:radial-gradient(ellipse 60% 50% at 30% 20%,rgba(99,102,241,.1) 0%,transparent 60%),radial-gradient(ellipse 50% 40% at 75% 70%,rgba(139,92,246,.07) 0%,transparent 60%);pointer-events:none;}
.auth-card{width:100%;max-width:400px;background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius-xl);padding:36px;position:relative;z-index:1;}
.auth-brand{display:flex;align-items:center;gap:10px;margin-bottom:22px;}
.auth-brand span{font-family:var(--font-display);font-size:18px;font-weight:700;background:linear-gradient(135deg,var(--accent2),#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}

/* mesh */
.mesh-bg::before{content:'';position:fixed;inset:0;background:radial-gradient(ellipse 60% 50% at 30% 20%,rgba(99,102,241,.1) 0%,transparent 60%),radial-gradient(ellipse 50% 40% at 75% 70%,rgba(139,92,246,.07) 0%,transparent 60%);pointer-events:none;z-index:0;}

/* Upgrade banner */
.upgrade-banner{background:linear-gradient(135deg,rgba(245,158,11,.15),rgba(245,158,11,.05));border:1px solid rgba(245,158,11,.25);border-radius:var(--radius-lg);padding:16px 20px;display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:20px;}
.upgrade-banner-text{font-size:14px;color:var(--text2);}.upgrade-banner-text strong{color:var(--pro);}

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
      <div>{pct > 1 ? `⚠️ Over limit! ${n.toLocaleString()} / ${limit.toLocaleString()} tokens — shorten your prompt` : pct > 0.8 ? `⚠️ ${n.toLocaleString()} / ${limit.toLocaleString()} tokens — approaching limit` : `✓ ${n.toLocaleString()} / ${limit.toLocaleString()} estimated tokens`}</div>
      <div className="progress"><div className="progress-fill" style={{ width: `${Math.min(pct*100,100)}%`, background: pct > 1 ? "var(--red)" : pct > 0.8 ? "var(--pro)" : undefined }} /></div>
    </div>
  );
}
function Hint({ children }) {
  return <p className="hint"><span style={{ flexShrink: 0 }}>ℹ</span><span>{children}</span></p>;
}

// ─── LANDING ───────────────────────────────────────────────────────────────
function LandingPage({ onLogin, onSignup }) {
  const features = [
    { icon: "✦", title: "AI Article Engine", desc: "Two separate AI models — one crafts your article, another builds the summary card. Fully independent." },
    { icon: "🎨", title: "Prompt Studio", desc: "Write your own prompts from scratch. Real-time token counter warns you before hitting limits." },
    { icon: "🖼️", title: "Image Automation", desc: "Midjourney or Pollinations images, auto-converted to WebP and set as featured image in WordPress." },
    { icon: "📌", title: "Pinterest Bot (Pro)", desc: "Auto-pin after publishing with AI-optimized title, description, and alt text to your boards." },
    { icon: "🔗", title: "Internal Linking", desc: "Fetches your existing WordPress posts and injects relevant long-tail phrase links automatically." },
    { icon: "📅", title: "Smart Scheduling", desc: "Delay between articles, draft or publish instantly, auto-pin with custom delay. Full control." },
  ];
  return (
    <div className="landing mesh-bg">
      <style>{css}</style>
      <nav className="nav">
        <div className="nav-brand"><Logo size={26} /><span>NicheFlow AI</span></div>
        <div style={{ display: "flex", gap: 32 }}>
          <a href="#features" style={{ color: "var(--text2)", fontSize: 14, textDecoration: "none" }}>Features</a>
          <a href="#pricing" style={{ color: "var(--text2)", fontSize: 14, textDecoration: "none" }}>Pricing</a>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="btn btn-ghost btn-sm" onClick={onLogin}>Log in</button>
          <button className="btn btn-primary btn-sm" onClick={onSignup}>Get started</button>
        </div>
      </nav>
      <section className="hero">
        <div className="fade-up" style={{ display:"inline-flex",alignItems:"center",gap:8,padding:"5px 14px",background:"var(--accent-dim)",border:"1px solid rgba(99,102,241,.25)",borderRadius:20,fontSize:12,fontWeight:500,color:"var(--accent2)",marginBottom:24 }}>✦ Content automation, reimagined</div>
        <h1 className="fade-up-d1">Publish <span className="grad">10x faster</span><br />across every niche.</h1>
        <p className="fade-up-d2">NicheFlow AI writes long-form articles, builds info cards, generates images, and pins to Pinterest — all from one dashboard.</p>
        <div className="fade-up-d3" style={{ display:"flex",gap:14,flexWrap:"wrap" }}>
          <button className="btn btn-primary btn-lg" onClick={onSignup} style={{ animation:"glow 3s ease-in-out infinite" }}>Start for free →</button>
          <button className="btn btn-ghost btn-lg" onClick={onLogin}>Sign in</button>
        </div>
        <div className="fade-up-d4" style={{ display:"flex",gap:40,marginTop:56,paddingTop:40,borderTop:"1px solid var(--border)",flexWrap:"wrap" }}>
          {[["2 AI Models","Article + Card, independent"],["Custom Prompts","Your voice, your niche"],["Pinterest Ready","Auto-pin with Pro"],["Any Niche","Mommy blog to finance"]].map(([n,l])=>(
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
        <p style={{ color:"var(--text2)",fontSize:15,marginTop:8 }}>No per-article fees. Cancel anytime.</p>
        <div className="pricing-grid">
          {[
            { name:"Basic",price:"$30",desc:"Everything you need to run a content business on autopilot.",
              features:["Unlimited article generation","Custom article prompt","Custom card prompt","Midjourney & Pollinations images","WordPress auto-publish","Featured image auto-set","Internal link injection","History & analytics"],
              btn:"Get Basic →", cls:"", action: () => { onSignup(); } },
            { name:"Pro",price:"$40",desc:"Everything in Basic plus full Pinterest automation.",
              features:["Everything in Basic","Pinterest auto-pinning","AI-optimized pin content","Alt text generation","Board selection & scheduling","Pin delay scheduling","Featured image as pin image","Auto-pin after publish"],
              btn:"Get Pro ★", cls:"featured", action: () => { onSignup(); } },
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
      </section>
      <footer style={{ borderTop:"1px solid var(--border)",padding:"32px 48px",display:"flex",justifyContent:"space-between",alignItems:"center",maxWidth:1100,margin:"0 auto" }}>
        <div className="nav-brand"><Logo size={20}/><span>NicheFlow AI</span></div>
        <div style={{ fontSize:13,color:"var(--text3)" }}>© 2026 NicheFlow AI. All rights reserved.</div>
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
            <div className="alert alert-ok" style={{ marginBottom:16 }}>
              ✓ Account created! Check your email to confirm, then log in.
            </div>
            <p style={{ fontSize:13,color:"var(--text2)",marginBottom:20,lineHeight:1.6 }}>
              Once confirmed, come back and sign in with your email and password.
            </p>
            <button
              className="btn btn-primary"
              style={{ width:"100%",marginBottom:10 }}
              onClick={() => { setStep("form"); onSwitch("login"); }}
            >
              Go to Login →
            </button>
          </div>
        ) : (
          <>
            <h2 style={{ fontFamily:"var(--font-display)",fontSize:22,fontWeight:700,margin:"6px 0 4px" }}>{mode==="login"?"Welcome back":"Create account"}</h2>
            <p style={{ fontSize:13,color:"var(--text2)",marginBottom:24 }}>{mode==="login"?"Sign in to your NicheFlow dashboard":"Start publishing smarter content today"}</p>
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
                {loading ? <><span className="spinner"/>Working...</> : mode==="login"?"Sign in →":"Create account →"}
              </button>
            </form>
            <p style={{ textAlign:"center",fontSize:13,color:"var(--text2)",marginTop:16 }}>
              {mode==="login"?"No account? ":"Already have one? "}
              <button style={{ background:"none",border:"none",color:"var(--accent2)",cursor:"pointer",fontFamily:"var(--font)",fontSize:13 }} onClick={()=>onSwitch(mode==="login"?"signup":"login")}>
                {mode==="login"?"Sign up free":"Sign in"}
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
        <strong>Upgrade to Pro</strong> — Unlock Pinterest automation, AI pin content, board scheduling, and more.
      </div>
      <button className="btn btn-pro btn-sm" onClick={onUpgrade}>Upgrade — $40/mo ★</button>
    </div>
  );
}

// ─── DASHBOARD ─────────────────────────────────────────────────────────────
function Dashboard({ history, plan, onUpgrade }) {
  const published = history.filter(h=>h.status==="published").length;
  const failed = history.filter(h=>h.status==="failed").length;
  return (
    <div className="fade-up">
      {plan !== "pro" && <UpgradeBanner onUpgrade={onUpgrade} />}
      <div className="stat-grid">
        {[{num:history.length,label:"Total articles"},{num:published,label:"Published",sub:published>0?`${Math.round(published/Math.max(history.length,1)*100)}% success`:""},{num:failed,label:"Failed"},{num:0,label:"Pinterest pins",sub:plan==="pro"?"Ready":"Pro feature"}].map((s,i)=>(
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
function GeneratePage({ config, onHistoryUpdate, plan }) {
  const [titles, setTitles] = useState("");
  const [delay, setDelay] = useState(config.delay_sec||10);
  const [draft, setDraft] = useState(false);
  const [useImages, setUseImages] = useState(false);
  const [running, setRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [progress, setProgress] = useState(0);
  const logRef = useRef(null);

  const addLog = useCallback((msg, type="info") => {
    const time = new Date().toLocaleTimeString("en",{hour:"2-digit",minute:"2-digit",second:"2-digit"});
    setLogs(prev=>[...prev.slice(-120),{msg,type,time}]);
    setTimeout(()=>{ if(logRef.current) logRef.current.scrollTop=logRef.current.scrollHeight; },50);
  },[]);

  const titleList = titles.split("\n").map(t=>t.trim()).filter(Boolean);
  const missingKeys = !config.gemini_key||!config.wp_url||!config.wp_password;

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
      addLog("✦ Calling AI pipeline...","info");
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
          max_links:config.max_links||4,
        };
        const token=getStoredToken();
        const res=await fetch(`${API_URL}/pipeline`,{
          method:"POST",
          headers:{"Content-Type":"application/json",...(token?{"Authorization":`Bearer ${token}`}:{})},
          body:JSON.stringify(payload),
        });
        let data;
        try{data=await res.json();}catch{data={success:false,error:`Server ${res.status}`};}
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
    addLog(`Batch complete. ${titleList.length} article(s) processed.`,"ok");
    setRunning(false);
  }

  const logCls={ok:"log-ok",err:"log-err",info:"log-info",warn:"log-warn"};
  return (
    <div className="fade-up">
      {missingKeys&&<div className="alert alert-warn" style={{marginBottom:18}}>⚠️ Missing config: {!config.gemini_key&&"AI key "}{!config.wp_url&&"WordPress URL "}{!config.wp_password&&"WordPress password"} — go to <strong>Settings</strong> first.</div>}
      <div style={{display:"grid",gridTemplateColumns:"1.4fr 1fr",gap:18,marginBottom:18}}>
        <div className="card">
          <div style={{fontFamily:"var(--font-display)",fontSize:14,fontWeight:600,marginBottom:6}}>Article Titles</div>
          <Hint>One title per line. Each becomes a full published article with card, images, and internal links.</Hint>
          <textarea className="input" style={{minHeight:200,marginTop:10,fontFamily:"monospace",fontSize:13}} value={titles} onChange={e=>setTitles(e.target.value)} placeholder={"10 Best Postpartum Recovery Tips\nBoursin Cheese Pasta with Broccoli\nBest Baby Monitors 2025: Complete Guide"} disabled={running}/>
          <div style={{marginTop:6,fontSize:12,color:"var(--text3)"}}>{titleList.length} title{titleList.length!==1?"s":""} entered</div>
        </div>
        <div style={{display:"flex",flexDirection:"column",gap:14}}>
          <div className="card">
            <div style={{fontFamily:"var(--font-display)",fontSize:14,fontWeight:600,marginBottom:14}}>Options</div>
            <div style={{display:"flex",flexDirection:"column",gap:14}}>
              <div className="setting-row">
                <div className="setting-info"><div className="setting-name">Save as Draft</div><div className="setting-desc">Publish to WordPress as draft instead of live</div></div>
                <label className="toggle"><input type="checkbox" checked={draft} onChange={e=>setDraft(e.target.checked)}/><span className="toggle-slider"/></label>
              </div>
              <div className="setting-row">
                <div className="setting-info"><div className="setting-name">Generate Images</div><div className="setting-desc">Midjourney (GoAPI key) or Pollinations (free). Images are converted to WebP and set as featured image.</div></div>
                <label className="toggle"><input type="checkbox" checked={useImages} onChange={e=>setUseImages(e.target.checked)}/><span className="toggle-slider"/></label>
              </div>
              <div>
                <div className="setting-name" style={{marginBottom:6}}>Delay between articles</div>
                <div style={{display:"flex",alignItems:"center",gap:10}}>
                  <input className="input" type="number" value={delay} min={0} max={120} onChange={e=>setDelay(+e.target.value)} style={{width:80}}/>
                  <span style={{fontSize:13,color:"var(--text2)"}}>seconds</span>
                </div>
                <Hint>5–10s recommended for free AI tier limits</Hint>
              </div>
            </div>
          </div>
          <button className="btn btn-primary" style={{width:"100%",padding:"13px",fontSize:15}} onClick={run} disabled={running||!titleList.length||missingKeys}>
            {running?<><span className="spinner"/>Running batch...</>:`▶ Generate ${titleList.length||""}  Article${titleList.length!==1?"s":""}`}
          </button>
          {running&&<div><div style={{display:"flex",justifyContent:"space-between",fontSize:12,color:"var(--text3)",marginBottom:6}}><span>Progress</span><span>{Math.round(progress*100)}%</span></div><div className="progress"><div className="progress-fill" style={{width:`${progress*100}%`}}/></div></div>}
          <div style={{background:"var(--bg3)",borderRadius:"var(--radius)",padding:"12px 16px",fontSize:13,color:"var(--text3)",lineHeight:1.7}}>
            <strong style={{color:"var(--accent2)"}}>Model 1</strong> — article body<br/>
            <strong style={{color:"var(--accent2)"}}>Model 2</strong> — summary card<br/>
            Images → WebP → uploaded → set as featured image
          </div>
        </div>
      </div>
      <div className="card">
        <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:12}}>
          <div style={{fontFamily:"var(--font-display)",fontSize:14,fontWeight:600,display:"flex",alignItems:"center",gap:8}}>
            <span className={`dot ${running?"dot-green dot-pulse":"dot-yellow"}`}/>Process Log
          </div>
          <button className="btn btn-ghost btn-sm" onClick={()=>setLogs([])}>Clear</button>
        </div>
        <div className="process-log" ref={logRef}>
          {logs.length===0?<div style={{color:"var(--text3)",fontFamily:"var(--font)"}}>Logs appear here when you run a batch...</div>
            :logs.map((l,i)=>(
              <div key={i} className="log-line"><span className="log-time">[{l.time}]</span><span className={logCls[l.type]||""}>{l.msg}</span></div>
            ))
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
        if(key.startsWith("gsk_")){
          const r=await fetch("https://api.groq.com/openai/v1/chat/completions",{method:"POST",headers:{Authorization:`Bearer ${key}`,"Content-Type":"application/json"},body:JSON.stringify({model:"llama-3.1-8b-instant",messages:[{role:"user",content:"Say OK"}],max_tokens:5})});
          result=r.ok?{ok:true,msg:"✅ Groq key valid!"}:{ok:false,msg:`❌ Groq error ${r.status}`};
        } else if(key.startsWith("AIza")){
          const r=await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${key}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({contents:[{parts:[{text:"Say OK"}]}],generationConfig:{maxOutputTokens:5}})});
          result=r.ok?{ok:true,msg:"✅ Gemini key valid!"}:{ok:false,msg:`❌ Gemini error ${r.status}`};
        } else{result={ok:false,msg:"❌ Use gsk_ (Groq) or AIza (Gemini)"};}
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
      {plan!=="pro"&&<UpgradeBanner onUpgrade={onUpgrade}/>}
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
              {cfg.gemini_key&&(()=>{const keys=cfg.gemini_key.split(",").map(k=>k.trim()).filter(Boolean);const hg=keys.some(k=>k.startsWith("gsk_"));const hm=keys.some(k=>k.startsWith("AIza"));if(hg&&hm)return<div className="alert alert-ok" style={{marginTop:8}}>✅ Dual mode — Groq + Gemini fallback. Zero downtime! 🚀</div>;if(hg)return<div className="alert alert-info" style={{marginTop:8}}>Using Groq. Add a Gemini key after a comma for automatic fallback.</div>;if(hm)return<div className="alert alert-info" style={{marginTop:8}}>Using Gemini. Add a Groq key after a comma for fallback.</div>;return null;})()}
              <Hint>Groq (free): console.groq.com — starts with gsk_. Gemini (free): aistudio.google.com — starts with AIza. Add both comma-separated for zero-downtime fallback.</Hint>
            </div>
            <div>
              <label className="form-label">GoAPI Key (Midjourney images)</label>
              <input className="input" type="password" value={cfg.goapi_key||""} onChange={e=>update("goapi_key",e.target.value)} placeholder="Your GoAPI key..."/>
              <Hint>Only for Midjourney images. Skip if using Pollinations (free) in the Images tab.</Hint>
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
            <div className="setting-row"><div className="setting-info"><div className="setting-name">Auto-inject internal links</div><div className="setting-desc">Match full long-tail article titles (3+ word phrases) from your existing posts</div></div><label className="toggle"><input type="checkbox" checked={cfg.use_internal_links!==false} onChange={e=>update("use_internal_links",e.target.checked)}/><span className="toggle-slider"/></label></div>
            {cfg.use_internal_links!==false&&<div><label className="form-label">Max internal links per article</label><input className="input" type="number" value={cfg.max_links||4} min={1} max={10} onChange={e=>update("max_links",+e.target.value)} style={{width:100}}/></div>}
            <div><label className="form-label">Default delay between articles (seconds)</label><input className="input" type="number" value={cfg.delay_sec||10} min={0} max={120} onChange={e=>update("delay_sec",+e.target.value)} style={{width:100}}/><Hint>5–10s recommended for free AI rate limits</Hint></div>
          </div>
        </div>
      )}

      {tab==="prompts"&&(
        <div style={{display:"flex",flexDirection:"column",gap:18}} className="fade-up">
          <div className="settings-section">
            <div className="settings-header"><span>💬</span><h3>Article Prompt</h3></div>
            <div className="settings-body">
              <div className="alert alert-info">✦ Write your own prompt. Use <code>{"{title}"}</code> as placeholder. Leave empty for the built-in default. Return a JSON with <code>html_content</code>, <code>seo_title</code>, <code>excerpt</code>, <code>MAIN</code>, <code>MAIN_DARK</code>, <code>LIGHT_BG</code>, <code>BORDER</code> hex color keys.</div>
              <div className="prompt-editor">
                <textarea className="input" style={{minHeight:220,fontFamily:"monospace",fontSize:13}} value={cfg.custom_prompt||""} onChange={e=>update("custom_prompt",e.target.value)} placeholder={"You are Emma, a warm mama blogger.\nWrite about: {title}\n\nReturn JSON:\n{\"seo_title\":\"\",\"excerpt\":\"\",\"html_content\":\"\",\"MAIN\":\"#hex\",\"MAIN_DARK\":\"#hex\",\"LIGHT_BG\":\"#hex\",\"BORDER\":\"#hex\"}"}/>
                {cfg.custom_prompt&&<div className="prompt-counter">{estimateTokens(cfg.custom_prompt).toLocaleString()} tokens</div>}
              </div>
              {cfg.custom_prompt&&<TokenCounter text={cfg.custom_prompt} limit={2000}/>}
              <Hint>Keep under 2,000 tokens. Include ##IMAGE1## ##IMAGE2## ##IMAGE3## in html_content where you want images inserted.</Hint>
            </div>
          </div>
          <div className="settings-section">
            <div className="settings-header"><span>🃏</span><h3>Card Prompt</h3></div>
            <div className="settings-body">
              <div className="alert alert-info">✦ Separate AI model generates the summary card. Return JSON with <code>card_title</code>, <code>summary</code>, <code>key_points</code> array, <code>quick_facts</code> array (label/value), <code>cta_text</code>. Leave empty for default. The "Save this!" button in the card is clickable and triggers the browser share/bookmark dialog.</div>
              <div className="prompt-editor">
                <textarea className="input" style={{minHeight:160,fontFamily:"monospace",fontSize:13}} value={cfg.card_prompt||""} onChange={e=>update("card_prompt",e.target.value)} placeholder={"For \"{title}\" return JSON:\n{\"card_title\":\"[short title]\",\"summary\":\"[2 sentences]\",\"key_points\":[\"point 1\",\"point 2\"],\"quick_facts\":[{\"label\":\"Time\",\"value\":\"30 mins\"}],\"cta_text\":\"Save this! 📌\"}"}/>
                {cfg.card_prompt&&<div className="prompt-counter">{estimateTokens(cfg.card_prompt).toLocaleString()} tokens</div>}
              </div>
              {cfg.card_prompt&&<TokenCounter text={cfg.card_prompt} limit={1500}/>}
              <div className="setting-row">
                <div className="setting-info"><div className="setting-name">Show card in every article</div><div className="setting-desc">Append the summary card HTML at the end of each article</div></div>
                <label className="toggle"><input type="checkbox" checked={cfg.show_card!==false} onChange={e=>update("show_card",e.target.checked)}/><span className="toggle-slider"/></label>
              </div>
            </div>
          </div>
        </div>
      )}

      {tab==="images"&&(
        <div className="settings-section fade-up">
          <div className="settings-header"><span>🖼️</span><h3>Image Settings</h3></div>
          <div className="settings-body">
            <div className="alert alert-info">✦ Images are automatically downloaded, converted to WebP (quality 80, optimized), uploaded to your WordPress media library, and set as the article's featured image.</div>
            <div><label className="form-label">Midjourney Image Template</label><textarea className="input" style={{minHeight:90}} value={cfg.mj_template||""} onChange={e=>update("mj_template",e.target.value)} placeholder="Close up {recipe_name}, food photography, natural light --ar 2:3"/><Hint>Use {"{recipe_name}"} or {"{title}"} as placeholder. Add --ar 2:3 for portrait. Requires GoAPI key.</Hint></div>
            <div className="divider"/>
            <div className="setting-row"><div className="setting-info"><div className="setting-name">Use Pollinations (free)</div><div className="setting-desc">Free AI images — no API key needed, lower quality than Midjourney</div></div><label className="toggle"><input type="checkbox" checked={cfg.use_pollinations||false} onChange={e=>update("use_pollinations",e.target.checked)}/><span className="toggle-slider"/></label></div>
            {cfg.use_pollinations&&<div><label className="form-label">Pollinations Prompt Template</label><textarea className="input" style={{minHeight:80}} value={cfg.pollinations_prompt||""} onChange={e=>update("pollinations_prompt",e.target.value)} placeholder="Professional editorial photography of {title}, natural light, 4K"/><Hint>Use {"{title}"} as placeholder.</Hint></div>}
          </div>
        </div>
      )}

      {tab==="pinterest"&&plan==="pro"&&(
        <div style={{display:"flex",flexDirection:"column",gap:18}} className="fade-up">
          <div className="settings-section">
            <div className="settings-header"><span>📌</span><h3>Pinterest Integration</h3><span className="badge badge-pro" style={{marginLeft:"auto"}}>PRO</span></div>
            <div className="settings-body">
              <div><label className="form-label">Pinterest Access Token</label><input className="input" type="password" value={cfg.pinterest_token||""} onChange={e=>update("pinterest_token",e.target.value)} placeholder="Your Pinterest API access token..."/><Hint>developers.pinterest.com → My Apps → Create App → Generate Token.</Hint></div>
              <div className="setting-row"><div className="setting-info"><div className="setting-name">Auto-pin after publish</div><div className="setting-desc">Automatically create a Pinterest pin every time an article is published</div></div><label className="toggle"><input type="checkbox" checked={cfg.auto_pin||false} onChange={e=>update("auto_pin",e.target.checked)}/><span className="toggle-slider"/></label></div>
              <div><label className="form-label">Pin delay (minutes after publish)</label><input className="input" type="number" value={cfg.pin_delay_min||0} min={0} max={1440} onChange={e=>update("pin_delay_min",+e.target.value)} style={{width:120}}/><Hint>0 = pin immediately. Max 1440 (24 hours).</Hint></div>
              <div><label className="form-label">Default Board IDs (comma-separated)</label><input className="input" value={cfg.pinterest_boards||""} onChange={e=>update("pinterest_boards",e.target.value)} placeholder="board-id-1, board-id-2"/><Hint>Find board IDs in the Pinterest URL. Or use the Pinterest page to load boards automatically.</Hint></div>
            </div>
          </div>
          <div className="settings-section">
            <div className="settings-header"><span>💬</span><h3>Pinterest Pin Prompt</h3></div>
            <div className="settings-body">
              <div className="alert alert-info">✦ A separate AI model generates your pin content. Returns JSON with <code>pin_title</code> (60 chars max), <code>pin_description</code> (150 chars max with CTA), <code>alt_text</code>, <code>hashtags</code> array. Leave empty for default.</div>
              <div className="prompt-editor">
                <textarea className="input" style={{minHeight:140,fontFamily:"monospace",fontSize:13}} value={cfg.pinterest_prompt||""} onChange={e=>update("pinterest_prompt",e.target.value)} placeholder={"For article \"{title}\" at {url}:\nReturn JSON:\n{\"pin_title\":\"[max 60 chars]\",\"pin_description\":\"[max 150 chars + Save this!]\",\"alt_text\":\"[1 sentence]\",\"hashtags\":[\"tag1\",\"tag2\"]}"}/>
                {cfg.pinterest_prompt&&<div className="prompt-counter">{estimateTokens(cfg.pinterest_prompt).toLocaleString()} tokens</div>}
              </div>
              {cfg.pinterest_prompt&&<TokenCounter text={cfg.pinterest_prompt} limit={1000}/>}
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
        ?<div className="card" style={{textAlign:"center",padding:"44px 24px"}}><div style={{fontSize:36,marginBottom:10}}>📋</div><div style={{fontSize:14,fontWeight:500,marginBottom:6}}>No articles yet</div><div style={{fontSize:13,color:"var(--text3)"}}>Generate your first batch to see history here</div></div>
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
  const logRef = useRef(null);

  if(plan!=="pro"){
    return (
      <div className="fade-up" style={{display:"flex",alignItems:"center",justifyContent:"center",minHeight:400}}>
        <div style={{textAlign:"center",maxWidth:400}}>
          <div style={{fontSize:52,marginBottom:14}}>📌</div>
          <div style={{fontFamily:"var(--font-display)",fontSize:22,fontWeight:700,marginBottom:8}}>Pinterest Bot</div>
          <div style={{fontSize:14,color:"var(--text2)",lineHeight:1.7,marginBottom:24}}>Auto-pin every published article with AI-optimized titles, descriptions, and alt text. Schedule across your boards. Connect your featured image as the pin image.</div>
          <button className="btn btn-pro btn-lg" style={{width:"100%",marginBottom:12}} onClick={onUpgrade}>Upgrade to Pro — $40/mo ★</button>
          <p style={{fontSize:12,color:"var(--text3)"}}>Includes everything in Basic plus full Pinterest automation</p>
        </div>
      </div>
    );
  }

  const addLog = useCallback((msg,type="info")=>{
    const time=new Date().toLocaleTimeString("en",{hour12:false});
    setLogs(prev=>[...prev.slice(-100),{msg,type,time}]);
    setTimeout(()=>{if(logRef.current)logRef.current.scrollTop=logRef.current.scrollHeight;},50);
  },[]);

  const publishedArticles = history.filter(h=>h.status==="published"&&h.post_url);

  async function loadBoards(){
    setLoadingBoards(true);setBoardError("");
    try{
      const res=await apiCall("/pinterest/boards");
      const data=await res.json();
      if(res.ok){setBoards(data.boards||[]);if(!data.boards?.length)setBoardError("No boards found. Check your Pinterest token in Settings → Pinterest.");}
      else setBoardError(data.detail||"Failed to load boards");
    }catch(e){setBoardError(e.message);}
    finally{setLoadingBoards(false);}
  }

  async function runPinterest(){
    if(!publishedArticles.length){addLog("No published articles to pin.","warn");return;}
    if(!selectedBoards.length){addLog("Select at least one board.","warn");return;}
    setRunning(true);
    addLog(`Starting Pinterest bot: ${publishedArticles.length} articles → ${selectedBoards.length} board(s)`,"ok");
    try{
      const res=await apiCall("/pinterest/run",{method:"POST",body:JSON.stringify({board_ids:selectedBoards})});
      const data=await res.json();
      if(res.ok){
        const results=data.results||[];
        setPinPreviews(results);
        results.forEach(r=>{
          addLog(`📌 ${r.title}`,"info");
          addLog(`  Title: "${r.pin_title}"`,"info");
          addLog(`  Desc: "${r.pin_description?.slice(0,60)}..."`,"info");
          r.boards?.forEach(b=>{
            addLog(b.success?`  ✅ Board ${b.board_id} → Pin ${b.pin_id}`:`  ❌ Board ${b.board_id}: ${b.error}`,b.success?"ok":"err");
          });
        });
        const sent=results.filter(r=>r.status==="sent").length;
        addLog(`Done! ${sent}/${results.length} articles pinned.`,"ok");
      } else addLog(`❌ ${data.detail||"Pinterest run failed"}`,"err");
    }catch(e){addLog(`❌ ${e.message}`,"err");}
    finally{setRunning(false);}
  }

  function toggleBoard(id){setSelectedBoards(prev=>prev.includes(id)?prev.filter(b=>b!==id):[...prev,id]);}
  const logCls={ok:"log-ok",err:"log-err",info:"log-info",warn:"log-warn"};

  return (
    <div className="fade-up">
      {previewModal&&(
        <div className="modal-overlay" onClick={()=>setPreviewModal(null)}>
          <div className="modal" onClick={e=>e.stopPropagation()}>
            <button className="modal-close" onClick={()=>setPreviewModal(null)}>✕</button>
            <div style={{fontFamily:"var(--font-display)",fontSize:18,fontWeight:700,marginBottom:4}}>Pin Preview</div>
            <div style={{fontSize:13,color:"var(--text2)",marginBottom:20}}>What your Pinterest pin will look like</div>
            <div className="pin-preview">
              {previewModal.featured_image_url
                ?<img src={previewModal.featured_image_url} alt={previewModal.pin_title} className="pin-img"/>
                :<div className="pin-img" style={{display:"flex",alignItems:"center",justifyContent:"center",color:"var(--text3)",fontSize:13}}>No featured image</div>
              }
              <div className="pin-body">
                <div className="pin-title">{previewModal.pin_title}</div>
                <div className="pin-desc">{previewModal.pin_description}</div>
                {previewModal.alt_text&&<div style={{fontSize:11,color:"var(--text3)",marginBottom:8}}>Alt: {previewModal.alt_text}</div>}
                {previewModal.hashtags?.length>0&&<div className="pin-tags">{previewModal.hashtags.map(h=><span key={h} className="pin-tag">#{h}</span>)}</div>}
                {previewModal.post_url&&<a href={previewModal.post_url} target="_blank" rel="noreferrer" style={{display:"block",marginTop:10,fontSize:12,color:"var(--accent2)",textDecoration:"none",overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>🔗 {previewModal.post_url}</a>}
              </div>
            </div>
            <div style={{fontSize:12,color:"var(--text3)",padding:"0 2px"}}>
              Boards: {previewModal.boards?.map(b=>b.board_id).join(", ")}<br/>
              Status: {previewModal.status}
            </div>
          </div>
        </div>
      )}

      <div style={{display:"grid",gridTemplateColumns:"1.3fr 1fr",gap:18,marginBottom:18}}>
        <div className="card">
          <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:8}}>
            <div style={{fontFamily:"var(--font-display)",fontSize:14,fontWeight:600}}>Pinterest Boards</div>
            <button className="btn btn-ghost btn-sm" onClick={loadBoards} disabled={loadingBoards}>{loadingBoards?<><span className="spinner spinner-accent"/>Loading...</>:"↺ Load Boards"}</button>
          </div>
          <Hint>Click "Load Boards" to automatically fetch your Pinterest boards from the API.</Hint>
          {boardError&&<div className="alert alert-err" style={{marginTop:10}}>{boardError}</div>}
          {!config.pinterest_token&&<div className="alert alert-warn" style={{marginTop:10}}>⚠️ No Pinterest token. Go to Settings → Pinterest first.</div>}
          {boards.length>0?(
            <div className="board-grid">
              {boards.map(b=>(
                <div key={b.id} className={`board-item ${selectedBoards.includes(b.id)?"selected":""}`} onClick={()=>toggleBoard(b.id)}>
                  <div className="board-icon">📋</div>
                  <div className="board-name">{b.name}</div>
                  {selectedBoards.includes(b.id)&&<div style={{fontSize:11,color:"var(--accent2)",marginTop:4}}>✓ Selected</div>}
                </div>
              ))}
            </div>
          ):(
            <div style={{marginTop:14,color:"var(--text3)",fontSize:13,textAlign:"center",padding:"20px 0"}}>
              {loadingBoards?"Fetching boards...":"Click \"Load Boards\" to see your Pinterest boards"}
            </div>
          )}
          {boards.length===0&&!loadingBoards&&config.pinterest_boards&&(
            <div style={{marginTop:12}}>
              <div style={{fontSize:12,color:"var(--text3)",marginBottom:8}}>Using board IDs from Settings:</div>
              <div className="board-grid">
                {config.pinterest_boards.split(",").map(id=>id.trim()).filter(Boolean).map(id=>(
                  <div key={id} className={`board-item ${selectedBoards.includes(id)?"selected":""}`} onClick={()=>toggleBoard(id)}>
                    <div className="board-icon">📋</div>
                    <div className="board-name" style={{wordBreak:"break-all"}}>{id}</div>
                    {selectedBoards.includes(id)&&<div style={{fontSize:11,color:"var(--accent2)",marginTop:4}}>✓</div>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div style={{display:"flex",flexDirection:"column",gap:14}}>
          <div className="card">
            <div style={{fontFamily:"var(--font-display)",fontSize:14,fontWeight:600,marginBottom:12}}>Queue Status</div>
            <div style={{fontSize:28,fontWeight:700,fontFamily:"var(--font-display)",marginBottom:4}}>{publishedArticles.length}</div>
            <div style={{fontSize:13,color:"var(--text3)"}}>published articles ready to pin</div>
            <div className="divider"/>
            <div style={{fontSize:13,color:"var(--text2)"}}>{selectedBoards.length} board{selectedBoards.length!==1?"s":""} selected</div>
            {config.pin_delay_min>0&&<div style={{marginTop:8,fontSize:12,color:"var(--text3)"}}>⏱ {config.pin_delay_min}min delay after publish</div>}
          </div>
          <div className="alert alert-info" style={{fontSize:13}}>
            ✦ AI generates pin title (60 chars), description (150 chars + CTA), and alt text for each article.<br/>
            ✦ The article's featured image is used as the pin image.<br/>
            ✦ Article URL is added as the pin link.
          </div>
          <button className="btn btn-pro" style={{width:"100%",padding:"13px"}} onClick={runPinterest} disabled={running||!publishedArticles.length||!selectedBoards.length}>
            {running?<><span className="spinner"/>Pinning...</>:`📌 Pin ${publishedArticles.length} Article${publishedArticles.length!==1?"s":""}`}
          </button>
        </div>
      </div>

      {pinPreviews.length>0&&(
        <div className="card" style={{marginBottom:18}}>
          <div style={{fontFamily:"var(--font-display)",fontSize:14,fontWeight:600,marginBottom:14}}>Pin Results — Click to Preview</div>
          {pinPreviews.map((p,i)=>(
            <div key={i} style={{display:"flex",alignItems:"center",gap:12,padding:"10px 0",borderBottom:i<pinPreviews.length-1?"1px solid var(--border)":"none",cursor:"pointer"}} onClick={()=>setPreviewModal(p)}>
              <span className={`dot ${p.status==="sent"?"dot-green":"dot-red"}`}/>
              <div style={{flex:1}}><div style={{fontSize:13,fontWeight:500}}>{p.title}</div><div style={{fontSize:12,color:"var(--text3)",marginTop:2}}>📌 {p.pin_title}</div></div>
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
          {logs.length===0?<div style={{color:"var(--text3)",fontFamily:"var(--font)"}}>Load boards, select them, and click Pin to start...</div>
            :logs.map((l,i)=>(
              <div key={i} className="log-line"><span className="log-time">[{l.time}]</span><span className={logCls[l.type]||""}>{l.msg}</span></div>
            ))
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
    {id:"start",label:"Quick Start"},
    {id:"api",label:"API Keys"},
    {id:"wordpress",label:"WordPress"},
    {id:"prompts",label:"Prompts & Cards"},
    {id:"images",label:"Images & WebP"},
    {id:"links",label:"Internal Links"},
    {id:"pinterest",label:"Pinterest (Pro)"},
    {id:"billing",label:"Billing & Plans"},
  ];
  return (
    <div className="fade-up" style={{display:"flex",gap:24}}>
      <div style={{width:180,flexShrink:0}}>
        <div style={{background:"var(--bg2)",border:"1px solid var(--border)",borderRadius:"var(--radius-lg)",padding:8,position:"sticky",top:20}}>
          {sections.map(s=>(
            <button key={s.id} onClick={()=>setSection(s.id)} style={{display:"block",width:"100%",padding:"8px 12px",borderRadius:8,border:"none",background:section===s.id?"var(--accent-dim)":"transparent",color:section===s.id?"var(--accent2)":"var(--text2)",fontSize:13,textAlign:"left",cursor:"pointer",fontFamily:"var(--font)",marginBottom:2}}>
              {s.label}
            </button>
          ))}
        </div>
      </div>
      <div style={{flex:1}}>
        {section==="start"&&(
          <>
            <div className="doc-section">
              <h3>🚀 Quick Start — Up in 5 minutes</h3>
              {[
                {n:"1",t:"Get a free AI key",d:<>Go to <a href="https://console.groq.com" target="_blank" rel="noreferrer" style={{color:"var(--accent2)"}}>console.groq.com</a> and create a free API key. It starts with <code>gsk_</code>. Groq gives you 14,400 requests/day free.</>},
                {n:"2",t:"Configure Settings",d:"Go to Settings → API Keys → paste your key → click Test → click Save Settings."},
                {n:"3",t:"Connect WordPress",d:<>Settings → WordPress → enter your site URL and App Password. Format: <code>username:xxxx xxxx xxxx xxxx</code>. Click Test Connection to verify.</>},
                {n:"4",t:"Write your Prompt",d:<>Settings → Prompts → write your article prompt. Use <code>{"{title}"}</code> as placeholder. Leave empty to use the built-in general-purpose prompt.</>},
                {n:"5",t:"Generate your first article",d:"Go to Generate → paste one title → click Generate. Watch the process log. Article appears in your WordPress as draft or published based on your settings."},
              ].map(s=>(
                <div key={s.n} className="doc-step">
                  <div className="doc-step-num">{s.n}</div>
                  <div className="doc-step-text"><div className="doc-step-title">{s.t}</div><div className="doc-step-desc">{s.d}</div></div>
                </div>
              ))}
            </div>
            <div className="doc-section">
              <h3>⚡ How the pipeline works</h3>
              <pre>{`User clicks Generate\n    ↓\nModel 1: Writes article body (HTML, 1000+ words)\nModel 2: Generates summary card (runs in parallel)\nModel 3: Generates images (parallel, if enabled)\n    ↓\nImages → downloaded → converted to WebP (quality 80)\n       → uploaded to WordPress media library\n       → set as article's featured image\n    ↓\nInternal links fetched from WordPress (if enabled)\nLong-tail phrases (3+ words) matched and hyperlinked\n    ↓\nArticle + card + images published to WordPress\nArticle URL and featured image saved to history`}</pre>
            </div>
          </>
        )}
        {section==="api"&&(
          <div className="doc-section">
            <h3>🔑 API Keys Explained</h3>
            <div className="doc-step"><div className="doc-step-num">G</div><div className="doc-step-text"><div className="doc-step-title">Groq API Key (recommended — free)</div><div className="doc-step-desc">Get at <a href="https://console.groq.com" target="_blank" rel="noreferrer" style={{color:"var(--accent2)"}}>console.groq.com</a>. Starts with <code>gsk_</code>. 14,400 requests/day free. Uses Llama 3.3 70B for articles (best quality) and Llama 3.1 8B for cards (fastest). Automatic model fallback on rate limit.</div></div></div>
            <div className="doc-step"><div className="doc-step-num">A</div><div className="doc-step-text"><div className="doc-step-title">Gemini API Key (fallback)</div><div className="doc-step-desc">Get at <a href="https://aistudio.google.com" target="_blank" rel="noreferrer" style={{color:"var(--accent2)"}}>aistudio.google.com</a>. Starts with <code>AIza</code>. 1,500 requests/day free. Add after comma: <code>gsk_xxx,AIzayyy</code> for zero-downtime fallback.</div></div></div>
            <div className="doc-step"><div className="doc-step-num">M</div><div className="doc-step-text"><div className="doc-step-title">GoAPI Key (Midjourney images)</div><div className="doc-step-desc">Get at <a href="https://goapi.ai" target="_blank" rel="noreferrer" style={{color:"var(--accent2)"}}>goapi.ai</a>. Paid service. Only needed if you want Midjourney-quality images. Skip if using Pollinations (free).</div></div></div>
            <div style={{marginTop:16}} className="alert alert-info">💡 <strong>Best setup:</strong> Add both Groq + Gemini keys comma-separated. Groq runs first (faster), Gemini is automatic fallback. Zero downtime even when one hits rate limits.</div>
          </div>
        )}
        {section==="wordpress"&&(
          <div className="doc-section">
            <h3>🌐 WordPress Connection</h3>
            {[
              {t:"Create an Application Password",d:<>In WordPress: <strong>Users → Your Profile → Application Passwords</strong> → enter any name (e.g. "NicheFlow AI") → click Add → copy the password shown.</>},
              {t:"Format the credentials",d:<>Enter as: <code>yourusername:xxxx xxxx xxxx xxxx</code>. The username is your WordPress login name (not email). The password is the generated one with spaces (keep the spaces).</>},
              {t:"Site URL format",d:<>Enter your full site URL: <code>https://yoursite.com</code> — no trailing slash, with https://.</>},
              {t:"Featured image",d:"When images are enabled, the first generated image is automatically uploaded to WordPress media and set as the post's featured image. It's also converted to WebP before upload."},
              {t:"Categories",d:"In the Generate page, click 'Load WP Categories' to see your categories and assign articles to them automatically."},
              {t:"Internal links",d:<>NicheFlow fetches all your published posts and looks for <strong>full article titles</strong> (3+ word phrases) appearing in the new article's body. When found, it wraps them in a styled hyperlink.</>},
            ].map((s,i)=>(
              <div key={i} className="doc-step">
                <div className="doc-step-num">{i+1}</div>
                <div className="doc-step-text"><div className="doc-step-title">{s.t}</div><div className="doc-step-desc">{s.d}</div></div>
              </div>
            ))}
          </div>
        )}
        {section==="prompts"&&(
          <>
            <div className="doc-section">
              <h3>💬 Article Prompt</h3>
              <p style={{fontSize:13,color:"var(--text2)",marginBottom:16,lineHeight:1.7}}>Write your own article prompt from scratch. The AI expects you to return a JSON object with these exact keys:</p>
              <pre>{`{\n  "seo_title": "Under 60 characters",\n  "excerpt": "2-sentence summary for meta description",\n  "html_content": "Full article HTML as a single-line string",\n  "MAIN": "#hexcolor",\n  "MAIN_DARK": "#hexcolor",\n  "LIGHT_BG": "#hexcolor",\n  "BORDER": "#hexcolor"\n}`}</pre>
              <p style={{fontSize:13,color:"var(--text2)",margin:"12px 0",lineHeight:1.7}}>Include <code>##IMAGE1##</code>, <code>##IMAGE2##</code>, <code>##IMAGE3##</code> in the html_content where you want images inserted.</p>
              <div className="alert alert-warn">⚠️ Keep your prompt under 2,000 tokens (the counter shows live). Longer prompts leave less room for the AI to write the actual article.</div>
            </div>
            <div className="doc-section">
              <h3>🃏 Card Prompt</h3>
              <p style={{fontSize:13,color:"var(--text2)",marginBottom:16,lineHeight:1.7}}>A separate, faster AI model generates the summary card. It should return JSON like this:</p>
              <pre>{`{\n  "card_title": "Short display title under 40 chars",\n  "card_type": "recipe|tips|checklist|comparison|guide",\n  "summary": "2-sentence summary of the topic",\n  "key_points": ["Point 1", "Point 2", "Point 3"],\n  "quick_facts": [\n    {"label": "Time", "value": "30 mins"}\n  ],\n  "cta_text": "Save this recipe! 📌"\n}`}</pre>
              <p style={{fontSize:13,color:"var(--text2)",margin:"12px 0",lineHeight:1.7}}>The CTA button in the published card is clickable — it triggers the browser's native Share dialog so readers can save/share the article.</p>
            </div>
          </>
        )}
        {section==="images"&&(
          <div className="doc-section">
            <h3>🖼️ Images & WebP Conversion</h3>
            {[
              {t:"WebP conversion",d:"All images are automatically downloaded and converted to WebP format at quality 80. Images wider than 1920px are resized down. WebP is 25-35% smaller than JPEG at the same quality."},
              {t:"WordPress upload",d:"The converted WebP is uploaded to your WordPress media library via the REST API. It gets a proper filename based on the article title."},
              {t:"Featured image",d:"Image 1 (featured) is set as the WordPress post's featured image using the media ID. Images 2, 3, 4 are injected into the article body at the ##IMAGE2## ##IMAGE3## ##IMAGE4## placeholders."},
              {t:"Midjourney (GoAPI)",d:<>Your template is used for all 4 images in parallel. The <code>--ar 2:3</code> aspect ratio creates portrait images (ideal for Pinterest). Fast mode is tried first, relax mode is automatic fallback.</>},
              {t:"Pollinations (free)",d:"Free alternative with no API key needed. Lower quality than Midjourney. Good for testing or low-budget niches. Enable in Settings → Images."},
            ].map((s,i)=>(
              <div key={i} className="doc-step">
                <div className="doc-step-num">{i+1}</div>
                <div className="doc-step-text"><div className="doc-step-title">{s.t}</div><div className="doc-step-desc">{s.d}</div></div>
              </div>
            ))}
          </div>
        )}
        {section==="links"&&(
          <div className="doc-section">
            <h3>🔗 Internal Links</h3>
            <p style={{fontSize:13,color:"var(--text2)",marginBottom:16,lineHeight:1.7}}>NicheFlow automatically injects internal links by matching your existing WordPress articles inside new article text.</p>
            {[
              {t:"Fetches all published posts",d:"When enabled, NicheFlow fetches up to 200 published posts from your WordPress site before publishing."},
              {t:"Long-tail phrase matching only",d:"Only article titles with 3 or more words are used as anchor text. Single or 2-word titles are ignored."},
              {t:"Exact title match first",d:"Looks for the exact article title text inside the new article's HTML. Case-insensitive."},
              {t:"Fallback: last 3 words",d:"If the full title isn't found, tries matching just the last 3 words of the title."},
              {t:"Relevance filtering",d:"Skips articles where more than 50% of words overlap with the current article's title."},
              {t:"Max links setting",d:"Set the max number of internal links per article in Settings → WordPress. Default is 4."},
            ].map((s,i)=>(
              <div key={i} className="doc-step">
                <div className="doc-step-num">{i+1}</div>
                <div className="doc-step-text"><div className="doc-step-title">{s.t}</div><div className="doc-step-desc">{s.d}</div></div>
              </div>
            ))}
          </div>
        )}
        {section==="pinterest"&&(
          <>
            {plan!=="pro"&&<div className="upgrade-banner" style={{marginBottom:20}}><div className="upgrade-banner-text"><strong>Pinterest is a Pro feature</strong> — upgrade to access this section.</div><button className="btn btn-pro btn-sm" onClick={onUpgrade}>Upgrade →</button></div>}
            <div className="doc-section" style={{opacity:plan!=="pro"?0.5:1}}>
              <h3>📌 Pinterest Bot</h3>
              {[
                {t:"Get a Pinterest Access Token",d:<>Go to <a href="https://developers.pinterest.com" target="_blank" rel="noreferrer" style={{color:"var(--accent2)"}}>developers.pinterest.com</a> → My Apps → Create App → Generate Access Token. You need the <code>boards:read</code> and <code>pins:write</code> scopes.</>},
                {t:"Add token in Settings",d:"Settings → Pinterest tab → paste your token → Save Settings."},
                {t:"Load your boards",d:"Go to the Pinterest page → click 'Load Boards' → select which boards to pin to."},
                {t:"How pins are created",d:"For each published article, a separate AI model generates: pin_title (max 60 chars), pin_description (max 150 chars + CTA), alt_text, and 5 hashtags. The article's featured image is used as the pin image."},
                {t:"Schedule delay",d:"Set a delay in Settings → Pinterest → 'Pin delay (minutes)'. Pinterest recommends not pinning immediately."},
                {t:"Auto-pin",d:"Enable 'Auto-pin after publish' in Settings → Pinterest to automatically pin every new article right after it's published."},
              ].map((s,i)=>(
                <div key={i} className="doc-step">
                  <div className="doc-step-num">{i+1}</div>
                  <div className="doc-step-text"><div className="doc-step-title">{s.t}</div><div className="doc-step-desc">{s.d}</div></div>
                </div>
              ))}
            </div>
          </>
        )}
        {section==="billing"&&(
          <div className="doc-section">
            <h3>💳 Billing & Plans</h3>
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16,marginBottom:20}}>
              {[
                {name:"Basic",price:"$30/mo",features:["Unlimited articles","Custom article prompt","Custom card prompt","Midjourney & Pollinations images","WordPress auto-publish","Featured image auto-set","Internal link injection","History"],color:"var(--accent2)"},
                {name:"Pro",price:"$40/mo",features:["Everything in Basic","Pinterest auto-pinning","AI pin title/description","Alt text generation","Board selection","Pin scheduling delay","Auto-pin after publish","Featured image as pin"],color:"var(--pro)"},
              ].map(p=>(
                <div key={p.name} style={{background:"var(--bg3)",border:`1px solid ${p.color}40`,borderRadius:"var(--radius-lg)",padding:20}}>
                  <div style={{fontFamily:"var(--font-display)",fontWeight:700,fontSize:16,color:p.color,marginBottom:4}}>{p.name}</div>
                  <div style={{fontFamily:"var(--font-display)",fontSize:28,fontWeight:800,marginBottom:12}}>{p.price}</div>
                  <ul style={{listStyle:"none",padding:0}}>{p.features.map(f=><li key={f} style={{fontSize:13,color:"var(--text2)",padding:"4px 0",borderBottom:"1px solid var(--border)",display:"flex",gap:8}}><span style={{color:"var(--green)"}}>✓</span>{f}</li>)}</ul>
                </div>
              ))}
            </div>
            <div className="alert alert-info">ℹ️ Payments are processed securely via LemonSqueezy. Your plan is updated automatically after payment. Cancel anytime from your LemonSqueezy account.</div>
            {plan==="basic"&&<button className="btn btn-pro" style={{width:"100%",marginTop:12}} onClick={onUpgrade}>Upgrade to Pro — $40/mo ★</button>}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── TRIAL BAR ─────────────────────────────────────────────────────────────
function TrialBar({ createdAt, plan, onUpgrade }) {
  if (plan === "pro") return null;
  const diff = (Date.now() - new Date(createdAt).getTime()) / (1000*60*60*24);
  const TRIAL_DAYS = 2;
  const daysLeft = Math.max(0, TRIAL_DAYS - Math.floor(diff));
  const msg = daysLeft===0?"⚠️ Free trial expired — upgrade to keep publishing"
    :daysLeft===1?"⏰ 1 day left in your free trial"
    :`🎉 ${daysLeft} days left in your free trial`;
  return (
    <div style={{padding:"8px 24px",display:"flex",alignItems:"center",justifyContent:"space-between",gap:14,fontSize:13,
      background:daysLeft===0?"rgba(239,68,68,0.15)":daysLeft===1?"rgba(245,158,11,0.12)":"rgba(16,185,129,0.08)",
      borderBottom:`1px solid ${daysLeft===0?"rgba(239,68,68,0.25)":daysLeft===1?"rgba(245,158,11,0.2)":"rgba(16,185,129,0.15)"}`,
      color:daysLeft===0?"var(--red)":daysLeft===1?"var(--pro)":"var(--green)"}}>
      <span><strong>{msg}</strong></span>
      <div style={{display:"flex",gap:8}}>
        <button className="btn btn-ghost btn-sm" onClick={()=>onUpgrade("basic")} style={{padding:"4px 10px",fontSize:11}}>Basic $30/mo</button>
        <button className="btn btn-pro btn-sm" onClick={()=>onUpgrade("pro")} style={{padding:"4px 10px",fontSize:11}}>Pro $40/mo ★</button>
      </div>
    </div>
  );
}

// ─── CHECKOUT MODAL ────────────────────────────────────────────────────────
function CheckoutModal({ plan, onClose, userEmail }) {
  const CHECKOUT_BASIC = "https://nicheflowai.lemonsqueezy.com/buy/basic";
  const CHECKOUT_PRO   = "https://nicheflowai.lemonsqueezy.com/buy/pro";
  const url = (plan==="pro"?CHECKOUT_PRO:CHECKOUT_BASIC)+`?checkout[email]=${encodeURIComponent(userEmail||"")}`;
  return (
    <div style={{position:"fixed",inset:0,background:"rgba(0,0,0,.78)",zIndex:300,display:"flex",alignItems:"center",justifyContent:"center",padding:20}} onClick={onClose}>
      <div style={{background:"var(--bg2)",border:"1px solid var(--border2)",borderRadius:"var(--radius-xl)",padding:36,maxWidth:440,width:"100%",position:"relative"}} onClick={e=>e.stopPropagation()}>
        <button onClick={onClose} style={{position:"absolute",top:14,right:14,background:"var(--bg3)",border:"1px solid var(--border)",borderRadius:8,width:28,height:28,cursor:"pointer",color:"var(--text3)",fontFamily:"var(--font)",fontSize:13}}>✕</button>
        <div style={{textAlign:"center",paddingTop:8}}>
          <div style={{fontSize:52,marginBottom:10}}>{plan==="pro"?"★":"⚡"}</div>
          <div style={{fontFamily:"var(--font-display)",fontSize:22,fontWeight:700,marginBottom:6}}>NicheFlow {plan==="pro"?"Pro":"Basic"}</div>
          <div style={{fontSize:38,fontWeight:800,fontFamily:"var(--font-display)",marginBottom:4,color:plan==="pro"?"var(--pro)":"var(--accent2)"}}>
            {plan==="pro"?"$40":"$30"}<span style={{fontSize:14,fontWeight:400,color:"var(--text3)"}}>/month</span>
          </div>
          <p style={{fontSize:13,color:"var(--text2)",marginBottom:22,lineHeight:1.6}}>
            {plan==="pro"?"Full Pinterest automation + everything in Basic.":"Unlimited articles, custom prompts, images, and WordPress publishing."}
          </p>
          <a href={url} target="_blank" rel="noreferrer"
            className={`btn ${plan==="pro"?"btn-pro":"btn-primary"} btn-lg`}
            style={{width:"100%",marginBottom:10,fontSize:15}}>
            Continue to Secure Checkout →
          </a>
          <p style={{fontSize:12,color:"var(--text3)"}}>Secured by LemonSqueezy · Cancel anytime · Plan activates instantly after payment</p>
        </div>
      </div>
    </div>
  );
}

// ─── APP SHELL ─────────────────────────────────────────────────────────────
function AppShell({ user, onLogout }) {
  const [page, setPage] = useState("dashboard");
  const [config, setConfig] = useState(getStoredConfig);
  const [plan, setPlan] = useState("basic");
  const [createdAt, setCreatedAt] = useState(new Date().toISOString());
  const [history, setHistory] = useState(()=>{try{return JSON.parse(localStorage.getItem("nicheflow_history")||"[]");}catch{return [];}});
  const [settingsLoaded, setSettingsLoaded] = useState(false);
  const [checkoutModal, setCheckoutModal] = useState(null);

  const email = user?.user?.email || user?.email || "user@example.com";
  const userId = user?.user?.id || user?.id || "";
  const token = user?.access_token || getStoredToken();
  const avatarLetter = email[0]?.toUpperCase() || "U";

  useEffect(() => {
    if (!userId || !token) return;
    fetch(`${SUPABASE_URL}/rest/v1/profiles?id=eq.${userId}&select=plan,created_at`, {
      headers: { apikey: SUPABASE_KEY, Authorization: `Bearer ${token}` }
    }).then(async r => {
      if (r.ok) {
        const rows = await r.json();
        if (rows && rows[0]) {
          setPlan(rows[0].plan || "basic");
          setCreatedAt(rows[0].created_at || new Date().toISOString());
        }
      }
    }).catch(() => {});
  }, [userId, token]);

  useEffect(() => {
    if (!token || settingsLoaded) return;
    fetch(`${API_URL}/settings`, { headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` } })
      .then(async res => {
        if (res.ok) {
          const data = await res.json();
          const dbSettings = data.settings || {};
          const merged = { ...config };
          Object.keys(dbSettings).forEach(k => {
            if (dbSettings[k] !== null && dbSettings[k] !== undefined && dbSettings[k] !== "") merged[k] = dbSettings[k];
          });
          setConfig(merged);
          localStorage.setItem("nicheflow_config", JSON.stringify(merged));
        }
        setSettingsLoaded(true);
      }).catch(() => setSettingsLoaded(true));
  }, [token]);

  function saveConfig(cfg) {
    setConfig(cfg);
    localStorage.setItem("nicheflow_config", JSON.stringify(cfg));
    fetch(`${API_URL}/settings`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify(cfg) }).catch(() => {});
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
  const pageInfo={dashboard:["Dashboard","Welcome back."],generate:["Generate Articles","Paste titles, let AI handle everything."],preview:["Preview","Test article style before a full batch."],history:["History","All generated and published articles."],pinterest:["Pinterest Bot","Auto-pin with AI-optimized content."],docs:["Documentation","Everything you need to use NicheFlow AI."],settings:["Settings","API keys, prompts, and integrations."]};
  const [pageTitle, pageSub]=pageInfo[page]||["",""];

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
          {plan!=="pro"&&(
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
              <div className="user-plan" style={{color:plan==="pro"?"var(--pro)":"var(--accent2)"}}>{plan==="pro"?"★ Pro":"Basic"}</div>
            </div>
          </div>
          <button className="nav-item" onClick={onLogout} style={{marginTop:6,color:"var(--text3)"}}><span>→</span>Sign out</button>
        </div>
      </aside>
      <main className="main-content">
        <TrialBar createdAt={createdAt} plan={plan} onUpgrade={handleUpgrade}/>
        <div className="page-header">
          <h1 className="page-title">{pageTitle}</h1>
          <p className="page-sub">{pageSub}</p>
        </div>
        <div className="page-body">
          {page==="dashboard"&&<Dashboard history={history} plan={plan} onUpgrade={handleUpgrade}/>}
          {page==="generate"&&<GeneratePage config={config} onHistoryUpdate={addHistory} plan={plan}/>}
          {page==="preview"&&<PreviewPage config={config}/>}
          {page==="history"&&<HistoryPage history={history} onClear={clearHistory}/>}
          {page==="pinterest"&&<PinterestPage config={config} history={history} plan={plan} onUpgrade={handleUpgrade}/>}
          {page==="docs"&&<DocsPage plan={plan} onUpgrade={handleUpgrade}/>}
          {page==="settings"&&<SettingsPage config={config} onSave={saveConfig} plan={plan} onUpgrade={handleUpgrade}/>}
        </div>
      </main>
    </div>
  );
}

// ─── ROOT ──────────────────────────────────────────────────────────────────
export default function NicheFlowAI() {
  const [view, setView] = useState("landing");
  const [user, setUser] = useState(null);

  useEffect(()=>{
    const stored = localStorage.getItem("nicheflow_user");
    if (stored) { try { const u=JSON.parse(stored); setUser(u); setView("app"); } catch {} }
  },[]);

  function handleAuthSuccess(userData) {
    localStorage.setItem("nicheflow_user", JSON.stringify(userData));
    setUser(userData);
    setView("app");
  }
  function handleLogout() {
    localStorage.removeItem("nicheflow_user");
    setUser(null); setView("landing");
  }

  if (view==="app"&&user) return <AppShell user={user} onLogout={handleLogout}/>;
  if (view==="login"||view==="signup") return <AuthPage mode={view} onSuccess={handleAuthSuccess} onSwitch={setView} onBack={()=>setView("landing")}/>;
  return <LandingPage onLogin={()=>setView("login")} onSignup={()=>setView("signup")}/>;
}