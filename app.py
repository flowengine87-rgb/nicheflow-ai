import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="NicheFlow AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="collapsedControl"],
section[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
.stApp { background: #faf6ef !important; overflow: hidden; }
iframe { border: none !important; display: block; }
</style>
""", unsafe_allow_html=True)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>NicheFlow AI</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700;9..144,800;9..144,900&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --cream:#faf6ef; --cream2:#f2e8d4; --gold:#c9892a; --gold2:#e8a83e;
  --dark:#0f0d09; --dark2:#1c1810; --text:#1a1510; --text2:#5a5040;
  --text3:#8a7a60; --border:#dfd4bc; --white:#ffffff;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html{scroll-behavior:smooth;}
body{font-family:'Outfit',sans-serif;background:var(--cream);color:var(--text);overflow-x:hidden;}
.page{display:none;min-height:100vh;}
.page.active{display:block;}

/* PAGE TRANSITION FLASH */
.page-flash {
  position:fixed;top:0;left:0;width:100%;height:100%;
  background:var(--cream);z-index:9999;
  opacity:0;pointer-events:none;
  transition:opacity 0.15s ease;
}
.page-flash.show{opacity:1;pointer-events:all;}

/* BACK BUTTON */
.back-nav {
  display:inline-flex;align-items:center;gap:7px;
  font-size:13px;font-weight:600;color:var(--text3);
  cursor:pointer;padding:8px 14px;border-radius:100px;
  border:1px solid var(--border);background:rgba(255,255,255,0.8);
  transition:all .2s;margin:16px 0 0 16px;
  text-decoration:none;
}
.back-nav:hover{color:var(--gold);border-color:var(--gold);background:#fff;}
.back-nav svg{width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round;}

/* NAV */
nav{position:sticky;top:0;z-index:999;display:flex;align-items:center;justify-content:space-between;padding:0 5vw;height:66px;background:rgba(250,246,239,0.94);backdrop-filter:blur(14px);border-bottom:1px solid var(--border);}
.nav-logo{font-family:'Fraunces',serif;font-size:21px;font-weight:800;color:var(--text);cursor:pointer;display:flex;align-items:center;gap:6px;}
.nav-logo em{color:var(--gold);font-style:normal;}
.nav-links{display:flex;align-items:center;gap:32px;}
.nav-links a{font-size:14px;font-weight:500;color:var(--text2);text-decoration:none;cursor:pointer;transition:color .2s;}
.nav-links a:hover{color:var(--gold);}
.nav-cta{background:var(--dark)!important;color:#fff!important;padding:9px 22px;border-radius:100px;font-weight:600!important;font-size:13px!important;transition:all .2s!important;}
.nav-cta:hover{background:var(--dark2)!important;transform:translateY(-1px);}

/* HERO */
.hero{background:linear-gradient(160deg,#fdfaf4 0%,#f5e8cc 55%,#ecdbb8 100%);padding:96px 5vw 80px;text-align:center;border-bottom:1px solid var(--border);position:relative;overflow:hidden;}
.hero::before{content:'';position:absolute;top:-220px;left:-180px;width:560px;height:560px;background:radial-gradient(circle,rgba(201,137,42,.15) 0%,transparent 65%);border-radius:50%;}
.hero::after{content:'';position:absolute;bottom:-150px;right:-150px;width:480px;height:480px;background:radial-gradient(circle,rgba(201,137,42,.1) 0%,transparent 65%);border-radius:50%;}
.hero-badge{display:inline-flex;align-items:center;gap:7px;background:rgba(255,255,255,.7);border:1px solid rgba(201,137,42,.35);color:#8a6020;padding:7px 18px;border-radius:100px;font-size:12.5px;font-weight:600;letter-spacing:.4px;margin-bottom:28px;position:relative;z-index:1;}
.hero h1{font-family:'Fraunces',serif;font-size:clamp(46px,8vw,90px);font-weight:900;line-height:1.03;color:var(--text);margin-bottom:24px;position:relative;z-index:1;}
.hero h1 em{font-style:normal;color:var(--gold);}
.hero p{font-size:clamp(15px,1.7vw,19px);color:var(--text2);max-width:580px;margin:0 auto 44px;line-height:1.78;position:relative;z-index:1;}
.hero-btns{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;position:relative;z-index:1;}
.btn-primary{background:var(--dark);color:#fff;padding:14px 30px;border-radius:100px;font-size:15px;font-weight:600;border:none;cursor:pointer;transition:all .2s;font-family:'Outfit',sans-serif;}
.btn-primary:hover{background:var(--dark2);transform:translateY(-2px);box-shadow:0 8px 28px rgba(0,0,0,.18);}
.btn-outline{background:transparent;color:var(--text);padding:14px 30px;border-radius:100px;font-size:15px;font-weight:600;border:1.5px solid var(--border);cursor:pointer;transition:all .2s;font-family:'Outfit',sans-serif;}
.btn-outline:hover{border-color:var(--gold);color:var(--gold);transform:translateY(-2px);}
.hero-stats{display:flex;flex-wrap:wrap;justify-content:center;gap:clamp(24px,5vw,68px);margin-top:60px;padding-top:48px;border-top:1px solid rgba(0,0,0,.09);position:relative;z-index:1;}
.stat-num{font-family:'Fraunces',serif;font-size:clamp(32px,4.5vw,48px);font-weight:800;color:var(--gold);}
.stat-lbl{font-size:13px;color:var(--text3);margin-top:5px;font-weight:500;}

/* SECTIONS */
.section{padding:clamp(60px,8vw,108px) clamp(24px,6vw,96px);background:var(--cream);}
.section-dark{background:var(--dark);padding:clamp(60px,8vw,108px) clamp(24px,6vw,96px);}
.section-alt{background:var(--cream2);padding:clamp(60px,8vw,108px) clamp(24px,6vw,96px);}
.section-center{text-align:center;}
.eyebrow{font-size:11px;font-weight:700;color:var(--gold);text-transform:uppercase;letter-spacing:3.5px;margin-bottom:14px;display:block;}
.eyebrow-light{color:rgba(201,137,42,.9)!important;}
.section-title{font-family:'Fraunces',serif;font-size:clamp(30px,4.5vw,52px);font-weight:800;line-height:1.12;color:var(--text);margin-bottom:14px;}
.section-title-light{font-family:'Fraunces',serif;font-size:clamp(30px,4.5vw,52px);font-weight:800;line-height:1.12;color:#fdf6e8;margin-bottom:14px;}
.section-sub{font-size:clamp(14px,1.4vw,17px);color:var(--text2);line-height:1.72;margin-bottom:clamp(36px,6vw,68px);max-width:560px;}
.section-sub-light{font-size:clamp(14px,1.4vw,17px);color:rgba(253,246,232,.5);line-height:1.72;margin-bottom:clamp(36px,6vw,68px);max-width:560px;}
.section-center .section-sub,.section-center .section-sub-light{margin-left:auto;margin-right:auto;}

/* FEATURES */
.feat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;}
@media(max-width:900px){.feat-grid{grid-template-columns:1fr 1fr;}}
@media(max-width:560px){.feat-grid{grid-template-columns:1fr;}}
.feat-card{background:#fff;border:1px solid var(--border);border-radius:20px;padding:clamp(22px,3vw,36px);transition:transform .25s,box-shadow .25s,border-color .25s;}
.feat-card:hover{transform:translateY(-4px);box-shadow:0 14px 44px rgba(0,0,0,.07);border-color:rgba(201,137,42,.45);}
.feat-icon{width:50px;height:50px;background:#fff8ec;border:1px solid rgba(201,137,42,.2);border-radius:13px;display:flex;align-items:center;justify-content:center;font-size:22px;margin-bottom:16px;}
.feat-card h3{font-size:15.5px;font-weight:700;color:var(--text);margin-bottom:8px;}
.feat-card p{font-size:13.5px;color:var(--text3);line-height:1.76;}

/* PRICING */
.pricing-grid{display:grid;grid-template-columns:1fr 1fr;gap:22px;max-width:840px;margin:0 auto;}
@media(max-width:640px){.pricing-grid{grid-template-columns:1fr;}}
.plan-card{background:#fff;border:2px solid var(--border);border-radius:26px;padding:clamp(30px,4vw,50px) clamp(26px,3.5vw,42px);text-align:center;transition:transform .25s,box-shadow .25s;}
.plan-card:hover{transform:translateY(-3px);box-shadow:0 14px 44px rgba(0,0,0,.07);}
.plan-card.pro{background:linear-gradient(158deg,#211808,#0f0d09);border-color:rgba(201,137,42,.55);box-shadow:0 8px 44px rgba(201,137,42,.2);}
.plan-label{font-size:11px;font-weight:700;color:var(--text3);text-transform:uppercase;letter-spacing:2.5px;margin-bottom:16px;}
.plan-card.pro .plan-label{color:rgba(232,168,62,.75);}
.plan-price{font-family:'Fraunces',serif;font-size:clamp(50px,7vw,70px);font-weight:900;color:var(--text);line-height:1;}
.plan-card.pro .plan-price{color:#fff;}
.plan-period{font-size:14px;color:var(--text3);margin-bottom:28px;margin-top:4px;}
.plan-card.pro .plan-period{color:rgba(253,246,232,.4);}
.plan-feats{text-align:left;}
.plan-feat{font-size:13.5px;color:var(--text2);padding:10px 0;border-bottom:1px solid #f0e8d8;}
.plan-card.pro .plan-feat{color:rgba(253,246,232,.8);border-bottom-color:rgba(255,255,255,.07);}
.plan-feat.no{color:#b8a888;opacity:.6;}
.plan-card.pro .plan-feat.no{color:rgba(253,246,232,.25);}
.plan-btn{width:100%;margin-top:26px;padding:13px;border-radius:100px;font-size:14px;font-weight:700;cursor:pointer;transition:all .2s;border:2px solid var(--dark);background:transparent;color:var(--dark);font-family:'Outfit',sans-serif;}
.plan-btn:hover{background:var(--dark);color:#fff;}
.plan-card.pro .plan-btn{background:var(--gold);border-color:var(--gold);color:#fff;}
.plan-card.pro .plan-btn:hover{background:var(--gold2);border-color:var(--gold2);}

/* HOW IT WORKS */
.steps-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;}
@media(max-width:900px){.steps-grid{grid-template-columns:1fr 1fr;}}
@media(max-width:520px){.steps-grid{grid-template-columns:1fr;}}
.step-card{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.11);border-radius:20px;padding:clamp(24px,3vw,36px);}
.step-num{font-family:'Fraunces',serif;font-size:clamp(44px,5.5vw,60px);font-weight:900;color:var(--gold);line-height:1;margin-bottom:16px;}
.step-card h4{font-size:16px;font-weight:700;color:#fdf6e8;margin-bottom:9px;}
.step-card p{font-size:13.5px;color:rgba(253,246,232,.5);line-height:1.76;}

/* CTA */
.cta-banner{background:var(--dark);border-radius:26px;padding:clamp(52px,7vw,92px) clamp(28px,6vw,80px);text-align:center;margin:0 clamp(14px,4vw,60px) clamp(52px,6vw,80px);position:relative;overflow:hidden;}
.cta-banner::before{content:'';position:absolute;top:-80px;left:50%;transform:translateX(-50%);width:500px;height:280px;background:radial-gradient(circle,rgba(201,137,42,.2) 0%,transparent 65%);pointer-events:none;}
.cta-banner .btn-primary{background:var(--gold);position:relative;z-index:1;}
.cta-banner .btn-primary:hover{background:var(--gold2);}

/* FOOTER */
footer{text-align:center;padding:clamp(36px,5vw,56px);border-top:1px solid var(--border);background:var(--cream);}
footer .f-logo{font-family:'Fraunces',serif;font-size:21px;font-weight:800;color:var(--text);margin-bottom:9px;}
footer p{font-size:13px;color:var(--text3);margin-bottom:3px;}

/* LOGIN */
.login-page{min-height:100vh;background:linear-gradient(160deg,#fdfaf4 0%,#f0e3c8 100%);display:flex;align-items:center;justify-content:center;padding:40px 20px;}
.login-card{background:#fff;border:1px solid var(--border);border-radius:26px;padding:clamp(36px,5vw,56px) clamp(30px,4.5vw,52px);width:100%;max-width:450px;box-shadow:0 12px 56px rgba(0,0,0,.08);}
.login-logo{font-family:'Fraunces',serif;font-size:20px;font-weight:800;color:var(--text);margin-bottom:28px;text-align:center;}
.login-logo em{color:var(--gold);font-style:normal;}
.login-card h2{font-family:'Fraunces',serif;font-size:30px;font-weight:800;color:var(--text);margin-bottom:5px;text-align:center;}
.login-card .sub{font-size:14.5px;color:var(--text3);text-align:center;margin-bottom:28px;}
.field{margin-bottom:16px;}
.field label{display:block;font-size:13px;font-weight:600;color:var(--text2);margin-bottom:6px;}
.field input{width:100%;padding:12px 15px;border:1.5px solid var(--border);border-radius:11px;font-size:14.5px;font-family:'Outfit',sans-serif;background:#fdfaf5;color:var(--text);outline:none;transition:border-color .2s,box-shadow .2s;}
.field input:focus{border-color:var(--gold);box-shadow:0 0 0 3px rgba(201,137,42,.12);}
.login-btn{width:100%;padding:13px;background:var(--dark);color:#fff;border:none;border-radius:11px;font-size:15px;font-weight:700;font-family:'Outfit',sans-serif;cursor:pointer;transition:all .2s;margin-top:6px;}
.login-btn:hover{background:var(--dark2);transform:translateY(-1px);box-shadow:0 6px 24px rgba(0,0,0,.14);}
.login-foot{text-align:center;margin-top:18px;font-size:13.5px;color:var(--text3);}
.login-foot a{color:var(--gold);font-weight:600;cursor:pointer;}
.back-link{display:block;text-align:center;margin-top:16px;font-size:13px;color:var(--text3);cursor:pointer;transition:color .2s;}
.back-link:hover{color:var(--gold);}
.err{background:#fff0f0;border:1px solid #ffd0d0;color:#c03030;border-radius:9px;padding:10px 14px;font-size:13.5px;margin-bottom:14px;display:none;}

/* DASHBOARD */
.dash-layout{display:flex;min-height:100vh;}
.sidebar{width:232px;min-width:232px;background:var(--dark);display:flex;flex-direction:column;position:sticky;top:0;height:100vh;overflow-y:auto;}
.sb-logo{padding:22px 22px 18px;font-family:'Fraunces',serif;font-size:19px;font-weight:800;color:#fdf6e8;border-bottom:1px solid rgba(255,255,255,.07);}
.sb-logo em{color:var(--gold);font-style:normal;}
.sb-user{padding:15px 22px;border-bottom:1px solid rgba(255,255,255,.07);}
.sb-name{font-size:13.5px;font-weight:600;color:#fdf6e8;}
.sb-plan{font-size:11.5px;color:rgba(253,246,232,.4);margin-top:3px;}
.sb-nav{padding:14px 10px;flex:1;}
.sb-nav a{display:flex;align-items:center;gap:9px;padding:10px 13px;border-radius:9px;font-size:13.5px;font-weight:500;color:rgba(253,246,232,.5);cursor:pointer;text-decoration:none;transition:all .2s;margin-bottom:2px;}
.sb-nav a:hover,.sb-nav a.active{background:rgba(255,255,255,.07);color:#fdf6e8;}
.sb-nav a.active{color:var(--gold2);}
.sb-bottom{padding:14px 10px;border-top:1px solid rgba(255,255,255,.07);}
.sb-out{display:flex;align-items:center;gap:9px;padding:10px 13px;border-radius:9px;font-size:13.5px;font-weight:500;color:rgba(253,246,232,.35);cursor:pointer;transition:all .2s;}
.sb-out:hover{background:rgba(255,255,255,.06);color:rgba(253,246,232,.65);}
.dash-main{flex:1;overflow-y:auto;background:#f5f0e6;}
.dash-top{background:rgba(245,240,230,.96);backdrop-filter:blur(10px);border-bottom:1px solid var(--border);padding:20px 30px;position:sticky;top:0;z-index:10;}
.dash-top h1{font-family:'Fraunces',serif;font-size:21px;font-weight:800;color:var(--text);}
.dash-top p{font-size:12.5px;color:var(--text3);margin-top:2px;}
.dash-body{padding:26px 30px;}

/* STATS */
.stats-row{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:26px;}
@media(max-width:860px){.stats-row{grid-template-columns:1fr 1fr;}}
.stat-box{background:#fff;border:1px solid var(--border);border-radius:14px;padding:20px;text-align:center;}
.stat-box .ico{font-size:22px;margin-bottom:9px;}
.stat-box .v{font-family:'Fraunces',serif;font-size:34px;font-weight:800;color:var(--gold);line-height:1;}
.stat-box .l{font-size:11.5px;color:var(--text3);margin-top:4px;}

/* FORM */
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
@media(max-width:680px){.form-grid{grid-template-columns:1fr;}}
.form-card{background:#fff;border:1px solid var(--border);border-radius:18px;padding:26px;}
.form-card h3{font-size:14.5px;font-weight:700;color:var(--text);margin-bottom:18px;padding-bottom:13px;border-bottom:1px solid #f0e6d4;}
.ff{margin-bottom:15px;}
.ff label{display:block;font-size:12.5px;font-weight:600;color:var(--text2);margin-bottom:5px;}
.ff input,.ff textarea,.ff select{width:100%;padding:10px 13px;border:1.5px solid var(--border);border-radius:9px;font-size:13.5px;font-family:'Outfit',sans-serif;background:#fdfaf5;color:var(--text);outline:none;resize:vertical;transition:border-color .2s,box-shadow .2s;}
.ff input:focus,.ff textarea:focus,.ff select:focus{border-color:var(--gold);box-shadow:0 0 0 3px rgba(201,137,42,.1);}
.ff .hint{font-size:11.5px;color:var(--text3);margin-top:4px;}
.tog-row{display:flex;align-items:center;gap:11px;margin-bottom:14px;}
.tog{position:relative;width:42px;height:23px;background:#ccc5b0;border-radius:100px;cursor:pointer;transition:background .25s;flex-shrink:0;}
.tog.on{background:var(--gold);}
.tog::after{content:'';position:absolute;top:3px;left:3px;width:17px;height:17px;background:#fff;border-radius:50%;transition:left .25s;box-shadow:0 1px 4px rgba(0,0,0,.15);}
.tog.on::after{left:22px;}
.tog-lbl{font-size:13.5px;font-weight:500;color:var(--text2);}
.save-btn{background:var(--dark);color:#fff;padding:12px 30px;border-radius:9px;font-size:14px;font-weight:700;border:none;cursor:pointer;font-family:'Outfit',sans-serif;transition:all .2s;margin-top:6px;}
.save-btn:hover{background:var(--dark2);transform:translateY(-1px);}
.ok-msg{background:#f0faf4;border:1px solid #a4d8b8;color:#1a6e38;border-radius:9px;padding:10px 14px;font-size:13px;margin-top:10px;}

/* GENERATE */
.gen-card{background:#fff;border:1px solid var(--border);border-radius:18px;padding:26px;margin-bottom:18px;}
.gen-card h3{font-size:14.5px;font-weight:700;color:var(--text);margin-bottom:5px;}
.gen-card .gsub{font-size:13px;color:var(--text3);margin-bottom:18px;}
.gen-btn{background:var(--dark);color:#fff;padding:13px 30px;border-radius:9px;font-size:14px;font-weight:700;border:none;cursor:pointer;font-family:'Outfit',sans-serif;transition:all .2s;}
.gen-btn:hover{background:var(--dark2);transform:translateY(-1px);}
.gen-opts{display:flex;gap:20px;flex-wrap:wrap;margin:14px 0;}

/* PINTEREST */
.pro-box{background:linear-gradient(135deg,var(--dark),#2a2418);border:1px solid rgba(201,137,42,.38);border-radius:18px;padding:28px;text-align:center;margin-bottom:22px;color:#fdf6e8;}
.pro-box h3{font-family:'Fraunces',serif;font-size:22px;font-weight:800;color:#fdf6e8;margin:10px 0 7px;}
.pro-box p{font-size:13.5px;color:rgba(253,246,232,.5);line-height:1.7;}
.pro-box .gold{color:var(--gold2);font-weight:600;}

/* SCHEDULE */
.schedule-card{background:#fff;border:1px solid var(--border);border-radius:18px;padding:26px;margin-top:18px;}
.schedule-card h3{font-size:14.5px;font-weight:700;color:var(--text);margin-bottom:6px;padding-bottom:13px;border-bottom:1px solid #f0e6d4;}
.schedule-card .sdesc{font-size:13px;color:var(--text3);margin-bottom:18px;}
.schedule-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;}
@media(max-width:600px){.schedule-grid{grid-template-columns:1fr;}}
.day-toggle{border:1.5px solid var(--border);border-radius:10px;padding:10px 12px;display:flex;align-items:center;justify-content:space-between;cursor:pointer;transition:all .2s;background:#fdfaf5;}
.day-toggle:hover{border-color:var(--gold);}
.day-toggle.sel{border-color:var(--gold);background:#fff8ec;}
.day-toggle .day-name{font-size:13px;font-weight:600;color:var(--text2);}
.day-toggle.sel .day-name{color:var(--gold);}
.day-dot{width:9px;height:9px;border-radius:50%;background:#ddd;transition:background .2s;}
.day-toggle.sel .day-dot{background:var(--gold);}
.time-row{display:flex;gap:14px;margin-top:14px;flex-wrap:wrap;}
.time-row .ff{flex:1;min-width:160px;}
.tz-note{font-size:11.5px;color:var(--text3);margin-top:6px;}

/* DOCS */
.docs-layout{display:grid;grid-template-columns:210px 1fr;gap:24px;align-items:start;}
@media(max-width:740px){.docs-layout{grid-template-columns:1fr;}}
.docs-toc{background:#fff;border:1px solid var(--border);border-radius:14px;padding:18px;position:sticky;top:76px;}
.docs-toc h4{font-size:10.5px;font-weight:700;color:var(--text3);text-transform:uppercase;letter-spacing:2px;margin-bottom:12px;}
.docs-toc a{display:block;font-size:13px;color:var(--text2);padding:7px 9px;border-radius:7px;cursor:pointer;text-decoration:none;transition:all .2s;margin-bottom:1px;}
.docs-toc a:hover,.docs-toc a.active{background:#fff8ec;color:var(--gold);font-weight:600;}
.docs-sec{background:#fff;border:1px solid var(--border);border-radius:18px;padding:26px 30px;margin-bottom:16px;}
.docs-sec h2{font-family:'Fraunces',serif;font-size:19px;font-weight:800;color:var(--text);margin-bottom:14px;padding-bottom:12px;border-bottom:1px solid #f0e6d4;display:flex;align-items:center;gap:10px;}
.docs-sec h3{font-size:14px;font-weight:700;color:var(--text);margin:16px 0 7px;}
.docs-sec p{font-size:13.5px;color:var(--text2);line-height:1.8;margin-bottom:10px;}
.docs-sec ol,.docs-sec ul{padding-left:20px;margin:7px 0 10px;}
.docs-sec li{font-size:13.5px;color:var(--text2);line-height:1.8;margin-bottom:4px;}
.docs-sec strong{color:var(--text);}
.doc-note{background:#fff8ec;border-left:3px solid var(--gold);border-radius:0 9px 9px 0;padding:10px 14px;margin:10px 0;font-size:13px;color:#7a5820;line-height:1.7;}
.doc-eg{background:#f8f3ea;border:1px solid #e4d8c4;border-radius:10px;padding:13px 16px;margin:9px 0;font-size:13px;color:#5a4a34;line-height:1.75;font-style:italic;}
.step-num-badge{display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;min-width:26px;background:var(--dark);color:var(--cream);border-radius:50%;font-size:12px;font-weight:700;}

@media(max-width:768px){.nav-links{display:none;}.sidebar{display:none;}}
</style>
</head>
<body>

<!-- PAGE TRANSITION OVERLAY -->
<div id="flash" class="page-flash"></div>

<!-- HOME -->
<div id="page-home" class="page active">
  <nav>
    <div class="nav-logo" onclick="go('home')">✦ <em>Niche</em>Flow AI</div>
    <div class="nav-links">
      <a onclick="scrollSec('features')">Features</a>
      <a onclick="scrollSec('pricing')">Pricing</a>
      <a onclick="scrollSec('how')">How It Works</a>
      <a onclick="go('docs')">Documentation</a>
      <a class="nav-cta" onclick="go('login')">Sign In →</a>
    </div>
  </nav>

  <section class="hero">
    <div class="hero-badge">✦ AI-Powered Content Platform</div>
    <h1>Write Less.<br>Publish More.<br><em>Grow on Autopilot.</em></h1>
    <p>NicheFlow AI writes full SEO blog articles, generates stunning Midjourney images, publishes to WordPress, and pins to Pinterest — completely automatically. You paste a title. We handle everything.</p>
    <div class="hero-btns">
      <button class="btn-primary" onclick="go('login')">Get Started Free →</button>
      <button class="btn-outline" onclick="go('docs')">View Documentation</button>
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
      <div class="feat-card"><div class="feat-icon">✍️</div><h3>AI Article Writer</h3><p>Groq AI writes full long-form SEO articles in seconds. Unique, deeply structured, and formatted for your niche audience.</p></div>
      <div class="feat-card"><div class="feat-icon">🎨</div><h3>Midjourney Images</h3><p>4 stunning images auto-generated per article. Converted to WebP and uploaded directly to your WordPress media library.</p></div>
      <div class="feat-card"><div class="feat-icon">🌐</div><h3>WordPress Publisher</h3><p>Articles publish directly to your site with images and full formatting. No copy-pasting or manual uploads — ever.</p></div>
      <div class="feat-card"><div class="feat-icon">📌</div><h3>Pinterest Auto-Post</h3><p>After every WordPress publish, automatically create and post optimized Pins using the article's featured image. Pro plan.</p></div>
      <div class="feat-card"><div class="feat-icon">🃏</div><h3>Custom Niche Cards</h3><p>Add beautifully styled cards to every article — recipe, info, or destination cards. Fully customizable per user.</p></div>
      <div class="feat-card"><div class="feat-icon">🔑</div><h3>Your Own API Keys</h3><p>You control your Groq, Midjourney, and WordPress credentials. No shared limits. Your content stays completely yours.</p></div>
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
          <div class="plan-feat">✅&nbsp; Custom Article Prompt</div>
          <div class="plan-feat">✅&nbsp; Custom Niche Card</div>
          <div class="plan-feat">✅&nbsp; Draft or Live Publishing</div>
          <div class="plan-feat no">✗&nbsp; Pinterest Auto-Post</div>
        </div>
        <button class="plan-btn" onclick="go('login')">Get Started →</button>
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
        <button class="plan-btn" onclick="go('login')">Get Pro →</button>
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
      <div class="step-card"><div class="step-num">01</div><h4>Sign Up & Choose Plan</h4><p>Create your account and pick Basic or Pro — depending on whether you need Pinterest auto-posting.</p></div>
      <div class="step-card"><div class="step-num">02</div><h4>Add Your Credentials</h4><p>Enter your Groq API key, Midjourney key, and WordPress app password once in Settings.</p></div>
      <div class="step-card"><div class="step-num">03</div><h4>Write Your Prompts</h4><p>Customize your article and card prompts to match your niche voice, style, and target audience.</p></div>
      <div class="step-card"><div class="step-num">04</div><h4>Paste Titles & Go</h4><p>Drop in your article titles and hit Generate. NicheFlow writes, designs, and publishes everything.</p></div>
    </div>
  </section>

  <section class="section">
    <div class="cta-banner">
      <span class="eyebrow eyebrow-light">Start Today</span>
      <h2 class="section-title" style="color:#fdf6e8;position:relative;z-index:1;">Ready to Automate Your Content?</h2>
      <p class="section-sub" style="color:rgba(253,246,232,.5);margin:0 auto 36px;position:relative;z-index:1;">Join bloggers who publish more, stress less, and grow faster with NicheFlow AI.</p>
      <button class="btn-primary" style="background:var(--gold);" onclick="go('login')">Get Started Free →</button>
    </div>
  </section>

  <footer>
    <div class="f-logo">✦ NicheFlow AI</div>
    <p>AI-powered blog &amp; Pinterest content generator</p>
    <p style="color:#b0a080;margin-top:14px;">© 2026 NicheFlow AI · All rights reserved</p>
  </footer>
</div>


<!-- LOGIN -->
<div id="page-login" class="page">
  <a class="back-nav" onclick="go('home')">
    <svg viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>
    Back to Home
  </a>
  <div class="login-page" style="min-height:calc(100vh - 60px);">
    <div class="login-card">
      <div class="login-logo">✦ <em>NicheFlow</em> AI</div>
      <h2>Welcome Back</h2>
      <p class="sub">Sign in to your NicheFlow AI account</p>
      <div id="login-err" class="err">Please fill in both fields.</div>
      <div class="field"><label>Email Address</label><input type="email" id="l-email" placeholder="your@email.com"></div>
      <div class="field"><label>Password</label><input type="password" id="l-pass" placeholder="Your password" onkeydown="if(event.key==='Enter')doLogin()"></div>
      <button class="login-btn" onclick="doLogin()">Sign In →</button>
      <p class="login-foot">Don't have an account? <a onclick="go('home')">Contact us to get access</a></p>
    </div>
  </div>
</div>


<!-- DOCS -->
<div id="page-docs" class="page">
  <nav>
    <div class="nav-logo" onclick="go('home')">✦ <em>Niche</em>Flow AI</div>
    <div class="nav-links">
      <a onclick="go('home')">← Home</a>
      <a class="nav-cta" onclick="go('login')">Sign In →</a>
    </div>
  </nav>
  <a class="back-nav" onclick="go('home')">
    <svg viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg>
    Back to Home
  </a>
  <section class="section" style="padding-top:32px;">
    <span class="eyebrow">Documentation</span>
    <h2 class="section-title" style="margin-bottom:8px;">Setup Guide</h2>
    <p style="font-size:16px;color:var(--text2);margin-bottom:36px;">Everything you need to get fully set up and publishing in under 10 minutes.</p>
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
          <h2><span class="step-num-badge">1</span>Get Your Groq API Key (Free)</h2>
          <p>Groq is the AI engine that writes your articles. The free tier provides more than enough requests for daily publishing.</p>
          <ol>
            <li>Go to <strong>console.groq.com</strong> and create a free account</li>
            <li>In the left sidebar, click <strong>API Keys</strong></li>
            <li>Click <strong>Create API Key</strong> and name it "NicheFlow"</li>
            <li>Copy the key — it begins with <strong>gsk_</strong></li>
            <li>Paste it in your dashboard under Settings → Groq API Key</li>
          </ol>
          <div class="doc-note">Groq's free tier provides 14,400 requests per day — more than enough for regular daily publishing.</div>
        </div>
        <div class="docs-sec" id="d-mj">
          <h2><span class="step-num-badge">2</span>Get Your Midjourney API Key</h2>
          <p>GoAPI connects NicheFlow to Midjourney so 4 images are generated and uploaded automatically for every article.</p>
          <ol>
            <li>Go to <strong>goapi.ai</strong> and create an account</li>
            <li>Choose a plan — pay-as-you-go works well for most users</li>
            <li>Navigate to <strong>Dashboard → API Keys</strong></li>
            <li>Copy your key and paste it in Settings → Midjourney API Key</li>
          </ol>
          <div class="doc-note">Images cost a few cents each on GoAPI's pay-as-you-go plan. Each article generates 4 images.</div>
        </div>
        <div class="docs-sec" id="d-wp">
          <h2><span class="step-num-badge">3</span>Connect Your WordPress Site</h2>
          <p>This allows NicheFlow to publish articles directly to your WordPress site, including images and formatting.</p>
          <ol>
            <li>Log in to your <strong>WordPress Dashboard</strong></li>
            <li>Go to <strong>Users → Your Profile</strong></li>
            <li>Scroll down to <strong>Application Passwords</strong></li>
            <li>Enter a name: <strong>NicheFlow AI</strong> — then click <strong>Add New Application Password</strong></li>
            <li>Copy the generated password (format: xxxx xxxx xxxx xxxx)</li>
            <li>In Settings enter your URL as <strong>https://yoursite.com</strong></li>
            <li>Enter the password as <strong>yourusername:xxxx xxxx xxxx xxxx</strong></li>
          </ol>
          <div class="doc-note">Make sure your URL includes https:// and does not have a trailing slash at the end.</div>
        </div>
        <div class="docs-sec" id="d-pin">
          <h2><span class="step-num-badge">4</span>Set Up Pinterest Auto-Post &nbsp;<span style="font-size:12px;font-weight:700;color:var(--gold);background:#fff8ec;padding:3px 10px;border-radius:100px;">Pro Plan</span></h2>
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
          <h2><span class="step-num-badge">5</span>Write a Great Article Prompt</h2>
          <p>Your article prompt is the single most impactful setting. It tells the AI how to write for your specific niche and audience.</p>
          <h3>Food Blog Example</h3>
          <div class="doc-eg">Write a warm, personal recipe article in first person. Open with a nostalgic story. Include a "Why You'll Love This" section, 8 expert tips, variations, storage instructions, and 3 FAQs. Friendly tone for home cooks. Target 1200–1500 words.</div>
          <h3>Travel Blog Example</h3>
          <div class="doc-eg">Write an inspiring travel guide in second person. Open with a vivid sensory scene. Cover top 5 attractions, local food, best time to visit, budget breakdown, and 5 practical tips. Target budget adventurers aged 25–40.</div>
          <div class="doc-note">Leave the prompt empty to use NicheFlow's built-in default prompt, which works well for general content.</div>
        </div>
        <div class="docs-sec" id="d-card">
          <h2><span class="step-num-badge">6</span>Customize Your Niche Card</h2>
          <p>The niche card is a styled visual block added inside every article — recipe card, destination summary, or any format that fits your niche.</p>
          <h3>Recipe Card Example</h3>
          <div class="doc-eg">Create a recipe card with: prep time, cook time, total time, servings, difficulty, cuisine type, and 6–8 key ingredients with amounts. Use a warm color scheme.</div>
          <h3>Travel Card Example</h3>
          <div class="doc-eg">Create a destination card with: best time to visit, average daily budget (USD), language, currency, visa required (yes/no), and top 3 attractions.</div>
          <div class="doc-note">You can toggle the niche card on or off per session from the Generate tab.</div>
        </div>
        <div class="docs-sec" id="d-pprompt">
          <h2><span class="step-num-badge">7</span>Write Your Pinterest Prompt &nbsp;<span style="font-size:12px;font-weight:700;color:var(--gold);background:#fff8ec;padding:3px 10px;border-radius:100px;">Pro Plan</span></h2>
          <p>Your Pinterest prompt tells the AI about your niche and audience so it generates optimized Pin titles, descriptions, and keywords for every article.</p>
          <h3>Example</h3>
          <div class="doc-eg">My audience is busy moms who love quick weeknight dinner recipes. Write Pinterest pin descriptions that are warm, conversational, using keywords like family dinner, easy recipes, weeknight meals. Keep under 200 characters with a call to action.</div>
        </div>
        <div class="docs-sec" id="d-tips">
          <h2><span class="step-num-badge">8</span>Best Practices</h2>
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
  </section>
  <footer>
    <div class="f-logo">✦ NicheFlow AI</div>
    <p>AI-powered blog &amp; Pinterest content generator</p>
    <p style="color:#b0a080;margin-top:14px;">© 2026 NicheFlow AI · All rights reserved</p>
  </footer>
</div>


<!-- DASHBOARD -->
<div id="page-dashboard" class="page">
  <div class="dash-layout">
    <aside class="sidebar">
      <div class="sb-logo">✦ <em>Niche</em>Flow AI</div>
      <div class="sb-user">
        <div class="sb-name" id="sb-user">User</div>
        <div class="sb-plan">Basic Plan · $30/mo</div>
      </div>
      <nav class="sb-nav">
        <a class="active" onclick="tab('settings',this)">⚙️&nbsp; Settings</a>
        <a onclick="tab('generate',this)">✍️&nbsp; Generate</a>
        <a onclick="tab('pinterest',this)">📌&nbsp; Pinterest</a>
        <a onclick="tab('docsd',this)">📖&nbsp; Documentation</a>
      </nav>
      <div class="sb-bottom">
        <div class="sb-out" onclick="doLogout()">🚪&nbsp; Sign Out</div>
      </div>
    </aside>
    <main class="dash-main">
      <div class="dash-top">
        <h1 id="d-title">Settings</h1>
        <p id="d-sub">Manage your API keys and preferences</p>
      </div>
      <div class="dash-body">
        <div class="stats-row">
          <div class="stat-box"><div class="ico">✍️</div><div class="v">0</div><div class="l">Articles Generated</div></div>
          <div class="stat-box"><div class="ico">🎨</div><div class="v">0</div><div class="l">Images Created</div></div>
          <div class="stat-box"><div class="ico">🌐</div><div class="v">0</div><div class="l">Posts Published</div></div>
          <div class="stat-box"><div class="ico">📌</div><div class="v">0</div><div class="l">Pins Posted</div></div>
        </div>

        <!-- SETTINGS -->
        <div id="tp-settings" class="tab-pane active">
          <div class="form-grid">
            <div class="form-card">
              <h3>API Credentials</h3>
              <div class="ff"><label>Groq API Key</label><input type="password" placeholder="gsk_..."><div class="hint">Free at console.groq.com</div></div>
              <div class="ff"><label>WordPress Site URL</label><input type="text" placeholder="https://yoursite.com"></div>
              <div class="ff"><label>WordPress App Password</label><input type="password" placeholder="username:xxxx xxxx xxxx xxxx"><div class="hint">WP Dashboard → Users → Profile → Application Passwords</div></div>
              <div class="ff"><label>Midjourney API Key (GoAPI)</label><input type="password" placeholder="Your GoAPI key"><div class="hint">Get at goapi.ai</div></div>
            </div>
            <div class="form-card">
              <h3>Content Preferences</h3>
              <div class="ff"><label>Custom Article Prompt (optional)</label><textarea rows="5" placeholder="Leave empty to use NicheFlow's built-in prompt..."></textarea></div>
              <div class="ff"><label>Custom Card Prompt (optional)</label><textarea rows="4" placeholder="Leave empty to use default card prompt..."></textarea></div>
              <div class="ff"><label>Publish Status</label><select><option>draft</option><option>publish</option></select></div>
              <div class="tog-row"><div class="tog on" onclick="this.classList.toggle('on')"></div><span class="tog-lbl">Show Niche Card in Articles</span></div>
            </div>
          </div>
          <button class="save-btn" onclick="showOk('ok-s')">Save Settings</button>
          <div id="ok-s" class="ok-msg" style="display:none;">Settings saved successfully.</div>
        </div>

        <!-- GENERATE -->
        <div id="tp-generate" class="tab-pane" style="display:none;">
          <div class="gen-card">
            <h3>Generate & Publish Articles</h3>
            <p class="gsub">Paste your article titles below — one per line. NicheFlow writes, designs, and publishes each one automatically.</p>
            <div class="ff"><textarea rows="7" placeholder="Classic Chocolate Chip Cookies&#10;Easy Banana Bread&#10;Lemon Tart Recipe&#10;Creamy Tuscan Chicken Pasta"></textarea></div>
            <div class="gen-opts">
              <div class="tog-row" style="margin:0;"><div class="tog on" onclick="this.classList.toggle('on')"></div><span class="tog-lbl" style="font-size:13px;">Generate Images</span></div>
              <div class="tog-row" style="margin:0;"><div class="tog on" onclick="this.classList.toggle('on')"></div><span class="tog-lbl" style="font-size:13px;">Include Niche Card</span></div>
            </div>
            <button class="gen-btn">Generate & Publish All →</button>
          </div>
        </div>

        <!-- PINTEREST -->
        <div id="tp-pinterest" class="tab-pane" style="display:none;">
          <div class="pro-box">
            <div style="font-size:34px;">📌</div>
            <h3>Pinterest Auto-Post</h3>
            <p>Available on the <span class="gold">Pro plan ($40/month)</span>.<br>Automatically post to Pinterest after every WordPress publish — using your featured image and AI-optimized descriptions.</p>
          </div>
          <div class="form-grid">
            <div class="form-card">
              <h3>Pinterest Credentials</h3>
              <div class="ff"><label>Pinterest Access Token</label><input type="password" placeholder="Your Pinterest access token"></div>
              <div class="ff"><label>Pinterest Board ID</label><input type="text" placeholder="Your board ID"></div>
            </div>
            <div class="form-card">
              <h3>Pinterest Prompt</h3>
              <div class="ff"><textarea rows="8" placeholder="Describe your Pinterest niche and audience.&#10;&#10;Example: My audience is busy moms who love quick dinner recipes. Create warm, inviting pins using family food keywords."></textarea></div>
            </div>
          </div>

          <!-- SCHEDULE SECTION -->
          <div class="schedule-card">
            <h3>📅 Pinterest Post Scheduler</h3>
            <p class="sdesc">Choose which days and time your Pins are automatically posted to Pinterest after each article is published.</p>
            <p style="font-size:12.5px;font-weight:600;color:var(--text2);margin-bottom:10px;">Post on these days:</p>
            <div class="schedule-grid">
              <div class="day-toggle sel" onclick="this.classList.toggle('sel')"><span class="day-name">Monday</span><div class="day-dot"></div></div>
              <div class="day-toggle sel" onclick="this.classList.toggle('sel')"><span class="day-name">Tuesday</span><div class="day-dot"></div></div>
              <div class="day-toggle" onclick="this.classList.toggle('sel')"><span class="day-name">Wednesday</span><div class="day-dot"></div></div>
              <div class="day-toggle sel" onclick="this.classList.toggle('sel')"><span class="day-name">Thursday</span><div class="day-dot"></div></div>
              <div class="day-toggle" onclick="this.classList.toggle('sel')"><span class="day-name">Friday</span><div class="day-dot"></div></div>
              <div class="day-toggle" onclick="this.classList.toggle('sel')"><span class="day-name">Saturday</span><div class="day-dot"></div></div>
              <div class="day-toggle" onclick="this.classList.toggle('sel')"><span class="day-name">Sunday</span><div class="day-dot"></div></div>
            </div>
            <div class="time-row">
              <div class="ff"><label>Posting Time</label><input type="time" value="09:00"></div>
              <div class="ff"><label>Timezone</label>
                <select>
                  <option>UTC</option>
                  <option>America/New_York</option>
                  <option>America/Los_Angeles</option>
                  <option>Europe/London</option>
                  <option>Europe/Paris</option>
                  <option>Asia/Dubai</option>
                  <option>Asia/Casablanca</option>
                  <option>Africa/Casablanca</option>
                </select>
                <div class="tz-note">Pins will be scheduled at this local time on selected days.</div>
              </div>
            </div>
          </div>

          <button class="save-btn" style="margin-top:18px;" onclick="showOk('ok-p')">Save Pinterest Settings</button>
          <div id="ok-p" class="ok-msg" style="display:none;">Pinterest settings saved.</div>
        </div>

        <!-- DOCS IN DASH -->
        <div id="tp-docsd" class="tab-pane" style="display:none;">
          <div class="form-card" style="max-width:560px;">
            <h3>Documentation</h3>
            <p style="font-size:14px;color:var(--text2);line-height:1.7;margin-bottom:18px;">Open the full setup guide and documentation in a dedicated page with step-by-step instructions for all integrations.</p>
            <button class="gen-btn" onclick="go('docs')">Open Full Documentation →</button>
          </div>
        </div>

      </div>
    </main>
  </div>
</div>

<script>
const tabMeta = {
  settings:['Settings','Manage your API keys and preferences'],
  generate:['Generate Articles','Paste titles and publish automatically'],
  pinterest:['Pinterest Auto-Post','Configure your Pinterest integration'],
  docsd:['Documentation','Setup guide and best practices'],
};

// Page history stack for back navigation
const history = ['home'];

function go(p) {
  const flash = document.getElementById('flash');
  // Flash in
  flash.classList.add('show');
  setTimeout(() => {
    document.querySelectorAll('.page').forEach(x => x.classList.remove('active'));
    document.getElementById('page-' + p).classList.add('active');
    window.scrollTo(0, 0);
    // Flash out
    setTimeout(() => flash.classList.remove('show'), 80);
  }, 150);
  // Track history
  if (history[history.length - 1] !== p) history.push(p);
}

function goBack() {
  if (history.length > 1) {
    history.pop();
    go(history[history.length - 1]);
  } else {
    go('home');
  }
}

function scrollSec(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function doLogin() {
  const e = document.getElementById('l-email').value.trim();
  const p = document.getElementById('l-pass').value.trim();
  const err = document.getElementById('login-err');
  if (!e || !p) { err.style.display = 'block'; return; }
  err.style.display = 'none';
  document.getElementById('sb-user').textContent = e;
  go('dashboard');
  tab('settings', null);
}

function doLogout() { go('home'); }

function tab(name, el) {
  document.querySelectorAll('[id^="tp-"]').forEach(x => x.style.display = 'none');
  document.getElementById('tp-' + name).style.display = 'block';
  document.querySelectorAll('.sb-nav a').forEach(x => x.classList.remove('active'));
  if (el) el.classList.add('active');
  const m = tabMeta[name] || ['Dashboard', ''];
  document.getElementById('d-title').textContent = m[0];
  document.getElementById('d-sub').textContent = m[1];
}

function showOk(id) {
  const el = document.getElementById(id);
  el.style.display = 'block';
  setTimeout(() => el.style.display = 'none', 3000);
}

function sDoc(id, el) {
  document.getElementById(id).scrollIntoView({ behavior: 'smooth', block: 'start' });
  document.querySelectorAll('.docs-toc a').forEach(x => x.classList.remove('active'));
  el.classList.add('active');
}
</script>
</body>
</html>"""

components.html(HTML, height=900, scrolling=True)