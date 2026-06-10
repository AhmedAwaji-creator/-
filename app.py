<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>نظام إدارة مستودعات الطوارئ — السعودية للطاقة</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;500;600;700;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>

<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#060d1e;--bg2:#0d1c3d;--bg3:#132248;
  --card:#0f1f45;--card2:#152850;--card3:#1a3060;
  --a1:#00e5ff;--a2:#1a7fff;--a3:#9b59ff;--a4:#ff5eb0;
  --g1:#1cd99a;--r1:#ff5555;--y1:#ffb820;--o1:#ff8c32;
  --t1:#f0f6ff;--t2:#b8cce8;--t3:#6b87a8;--t4:#2d4060;
  --b1:rgba(0,212,255,.15);--b2:rgba(0,212,255,.28);--b3:rgba(0,212,255,.45);
  --gs:#006C35;--gs2:#009245;
}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--t1);font-family:'Cairo',sans-serif;min-height:100vh;overflow-x:hidden}
.bg-fx{position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden}
.bg-orb{position:absolute;border-radius:50%;filter:blur(100px);opacity:.22;animation:orb 10s ease-in-out infinite}
.bg-orb:nth-child(1){width:700px;height:700px;background:rgba(0,102,255,.5);top:-200px;right:-150px}
.bg-orb:nth-child(2){width:500px;height:500px;background:rgba(0,100,53,.4);bottom:-150px;left:-100px;animation-delay:4s}
.bg-orb:nth-child(3){width:350px;height:350px;background:rgba(124,58,237,.3);top:35%;left:35%;animation-delay:7s}
@keyframes orb{0%,100%{transform:translate(0,0)}50%{transform:translate(25px,-25px)}}
.grid-bg{position:fixed;inset:0;z-index:0;pointer-events:none;background-image:linear-gradient(rgba(0,212,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(0,212,255,.025) 1px,transparent 1px);background-size:48px 48px}

/* ═══ LOGIN ═══ */
#login-screen{position:fixed;inset:0;z-index:6000;display:flex;align-items:center;justify-content:center;background:var(--bg)}
.lcard{background:rgba(9,19,42,.97);border:1px solid rgba(0,180,80,.25);border-radius:22px;padding:40px 36px;width:420px;backdrop-filter:blur(30px);box-shadow:0 30px 80px rgba(0,0,0,.7);position:relative;z-index:1}
.llogo{display:flex;flex-direction:column;align-items:center;gap:14px;margin-bottom:24px}
.ltitle{font-size:19px;font-weight:800;text-align:center;color:var(--t1);line-height:1.35}
.lsub{font-size:11px;color:var(--t2);text-align:center}
.ldiv{height:1px;background:linear-gradient(90deg,transparent,rgba(0,180,80,.4),transparent);margin:18px 0}
.lfield{margin-bottom:14px}
.llabel{font-size:12px;color:var(--t2);font-weight:600;margin-bottom:7px;display:flex;align-items:center;gap:7px}
.linput{width:100%;padding:12px 16px;background:var(--bg2);border:1px solid var(--b1);border-radius:10px;color:var(--t1);font-size:14px;font-family:'Cairo',sans-serif;outline:none;transition:all .2s;direction:ltr;text-align:right}
.linput:focus{border-color:var(--b3);box-shadow:0 0 0 3px rgba(0,212,255,.07)}
.linput.err{border-color:rgba(239,68,68,.6)!important;background:rgba(239,68,68,.05)}
.lerr{font-size:11.5px;color:var(--r1);margin-top:5px;display:none;align-items:center;gap:5px}
.lerr.show{display:flex}
.prel{position:relative}
.peye{position:absolute;left:13px;top:50%;transform:translateY(-50%);cursor:pointer;color:var(--t3);transition:color .15s}
.peye:hover{color:var(--a1)}
.lbtn{width:100%;padding:13px;background:linear-gradient(135deg,var(--gs),var(--gs2));color:#fff;border:none;border-radius:11px;font-size:15px;font-weight:700;font-family:'Cairo',sans-serif;cursor:pointer;transition:all .22s;box-shadow:0 5px 20px rgba(0,108,53,.4);margin-top:6px}
.lbtn:hover:not(:disabled){transform:translateY(-2px);box-shadow:0 10px 28px rgba(0,108,53,.5)}
.lbtn:disabled{opacity:.6;cursor:not-allowed;transform:none}
.lhints{margin-top:16px;display:flex;flex-direction:column;gap:5px}
.lhi{display:flex;align-items:center;justify-content:space-between;padding:7px 12px;background:rgba(0,212,255,.04);border:1px solid var(--b1);border-radius:8px;cursor:pointer;transition:all .15s}
.lhi:hover{background:rgba(0,212,255,.09);border-color:var(--b2)}
.lhir{font-size:9.5px;color:var(--a1);font-weight:700}
.lhin{font-size:10px;color:var(--t2);margin-top:1px}
.lhic{font-family:'JetBrains Mono',monospace;font-size:9.5px;color:var(--t3)}

/* ═══ LOADER ═══ */
#loader{position:fixed;inset:0;z-index:5000;background:var(--bg);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;transition:opacity .6s,transform .6s;display:none}
#loader.show{display:flex}
#loader.done{opacity:0;transform:scale(1.04);pointer-events:none}
.ldr-bounce{animation:lbounce 1s ease-in-out infinite}
@keyframes lbounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}
.ldr-bar{width:240px;height:2px;background:rgba(255,255,255,.08);border-radius:2px;overflow:hidden}
.ldr-fill{height:100%;background:linear-gradient(90deg,var(--gs2),var(--a1));width:0;transition:width .1s}
.ldr-pct{font-size:12px;color:var(--t3);font-family:'JetBrains Mono',monospace}

/* ═══ SHELL ═══ */
#shell{display:none;height:100vh;overflow:hidden}
#shell.show{display:flex;flex-direction:row;height:100vh;overflow:hidden}

/* ═══ SIDEBAR ═══ */
.sidebar{width:290px;background:rgba(5,10,22,.97);backdrop-filter:blur(24px);border-left:1px solid rgba(0,180,80,.15);display:flex;flex-direction:column;position:fixed;right:0;top:0;bottom:0;z-index:200;overflow:hidden}
.s-logo{padding:10px 12px;border-bottom:1px solid var(--b1)}
.logo-card{display:flex;align-items:center;gap:12px;padding:10px 12px;background:linear-gradient(135deg,rgba(0,108,53,.18),rgba(0,146,69,.1));border:1px solid rgba(0,180,80,.25);border-radius:14px;cursor:pointer;transition:all .2s}
.logo-card:hover{border-color:rgba(0,180,80,.45);background:linear-gradient(135deg,rgba(0,108,53,.25),rgba(0,146,69,.15))}
.logo-emblem{width:64px;height:64px;flex-shrink:0;border-radius:12px;overflow:hidden;background:rgba(0,212,255,.07);border:1px solid rgba(0,212,255,.2)}
.logo-org{font-size:8.5px;color:var(--gs2);font-weight:700;letter-spacing:1.5px;text-transform:uppercase}
.logo-sys{font-size:13.5px;font-weight:800;color:var(--t1);line-height:1.3;margin-top:2px}
.logo-dept{font-size:10.5px;color:var(--t2);margin-top:3px;font-weight:500}
.s-nav{flex:1;overflow-y:auto;padding:4px 0;scrollbar-width:none}
.s-sec{padding:6px 18px 2px;font-size:8.5px;color:var(--t3);font-weight:700;letter-spacing:2px;text-transform:uppercase}
.s-item{display:flex;align-items:center;gap:10px;padding:7px 12px;margin:1px 6px;border-radius:10px;cursor:pointer;font-size:13px;font-weight:600;color:var(--t2);transition:all .16s;position:relative;border:1px solid transparent;white-space:nowrap}
.s-item:hover{background:rgba(0,212,255,.06);color:var(--t1);border-color:var(--b1)}
.s-item.on{background:linear-gradient(135deg,rgba(0,102,255,.18),rgba(0,212,255,.08));color:var(--a1);border-color:var(--b2)}
.s-item.on::after{content:'';position:absolute;right:-8px;top:50%;transform:translateY(-50%);width:3px;height:16px;border-radius:2px;background:linear-gradient(180deg,var(--a2),var(--a1));box-shadow:0 0 8px var(--a1)}
.s-item i{width:18px;text-align:center;font-size:14px;flex-shrink:0}
.s-badge{position:absolute;left:8px;top:50%;transform:translateY(-50%);background:var(--r1);color:#fff;font-size:8.5px;font-weight:800;min-width:17px;height:17px;padding:0 4px;border-radius:9px;display:flex;align-items:center;justify-content:center;border:1.5px solid var(--bg);animation:badgep 2s ease-in-out infinite}
@keyframes badgep{0%,100%{box-shadow:0 0 0 0 rgba(239,68,68,.5)}50%{box-shadow:0 0 0 4px rgba(239,68,68,0)}}
.s-div{height:1px;background:linear-gradient(90deg,transparent,var(--b2),transparent);margin:2px 10px}
.s-foot{padding:0;border-top:1px solid var(--b1);flex-shrink:0}
.ucard{display:flex;align-items:center;gap:10px;padding:10px 12px;background:var(--card2);border:1px solid var(--b1);border-radius:10px;cursor:pointer;transition:all .2s}
.ucard:hover{border-color:var(--b2)}
.uav{width:36px;height:36px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:#fff;flex-shrink:0}
.uname{font-size:12px;font-weight:700;color:var(--t1)}
.urole{font-size:10px;color:var(--a1);margin-top:1px}
.ulive{width:6px;height:6px;border-radius:50%;background:var(--g1);margin-right:auto;flex-shrink:0;box-shadow:0 0 5px var(--g1);animation:ulive 2s ease infinite}
@keyframes ulive{0%,100%{opacity:1}50%{opacity:.3}}

/* ═══ MAIN ═══ */
.main{margin-right:290px;flex:1;display:flex;flex-direction:column;height:100vh;overflow:hidden}
.topbar{padding:0 24px;height:60px;display:flex;align-items:center;justify-content:space-between;background:rgba(6,13,30,.92);backdrop-filter:blur(24px);border-bottom:1px solid var(--b1);position:sticky;top:0;z-index:100}
.tb-l{display:flex;align-items:center;gap:10px}
.tb-title{font-size:14.5px;font-weight:700;color:var(--t1)}
.tb-sep{color:var(--t3);font-size:11px}
.tb-sub{font-size:12px;color:var(--t2)}
.tb-r{display:flex;align-items:center;gap:8px}
.tb-btn{width:36px;height:36px;border-radius:9px;background:var(--card);border:1px solid var(--b1);display:flex;align-items:center;justify-content:center;cursor:pointer;color:var(--t2);font-size:14px;transition:all .16s;position:relative}
.tb-btn:hover{border-color:var(--b2);color:var(--a1)}
.tb-dot{position:absolute;top:7px;left:7px;width:6px;height:6px;background:var(--r1);border-radius:50%;border:1.5px solid var(--bg)}
.tb-clock{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--a1);padding:6px 12px;background:rgba(0,212,255,.06);border:1px solid var(--b2);border-radius:8px;letter-spacing:1px}
.live-pill{display:flex;align-items:center;gap:5px;padding:5px 10px;border-radius:20px;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.2);font-size:10.5px;color:var(--g1);font-weight:600}
.ldot{width:6px;height:6px;border-radius:50%;background:var(--g1);animation:ldot 1.5s ease infinite}
@keyframes ldot{0%,100%{opacity:1}50%{opacity:.3}}

.content{padding:22px 24px;flex:1;overflow-y:auto;overflow-x:hidden}
.page-in{animation:pgin .3s ease}
@keyframes pgin{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}

/* ═══ COMMON COMPONENTS ═══ */
.card{background:var(--card);border:1px solid rgba(0,212,255,.18);border-radius:14px;padding:18px 20px}
.card-hd{display:flex;align-items:center;justify-content:space-between;margin-bottom:15px}
.card-title{font-size:13px;font-weight:700;color:var(--t1);display:flex;align-items:center;gap:8px}
.pg-hd{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;flex-wrap:wrap;gap:10px}
.pg-title{font-size:18px;font-weight:800;color:var(--t1);display:flex;align-items:center;gap:10px}
.pg-sub{font-size:11.5px;color:var(--t2);margin-top:3px}

/* Buttons */
.btn{padding:9px 18px;border-radius:9px;cursor:pointer;font-size:13px;font-family:'Cairo',sans-serif;transition:all .18s;display:inline-flex;align-items:center;gap:7px;border:none;font-weight:600}
.btn-primary{background:linear-gradient(135deg,var(--a2),var(--a1));color:#fff;box-shadow:0 4px 16px rgba(0,102,255,.35)}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,102,255,.45)}
.btn-green{background:linear-gradient(135deg,var(--gs),var(--gs2));color:#fff;box-shadow:0 4px 14px rgba(0,108,53,.35)}
.btn-green:hover{transform:translateY(-2px)}
.btn-sec{background:transparent;border:1px solid var(--b2)!important;color:var(--a1)}
.btn-sec:hover{background:var(--b1)}
.btn-warn{background:rgba(245,158,11,.12);border:1px solid rgba(245,158,11,.3)!important;color:#fbbf24}
.btn-warn:hover{background:rgba(245,158,11,.2)}
.btn-danger{background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.3)!important;color:#f87171}
.btn-danger:hover{background:rgba(239,68,68,.2)}
.btn-sm{padding:6px 12px;font-size:11.5px}
.btn-xs{padding:4px 9px;font-size:11px}

/* Forms */
.form-row{display:grid;gap:12px;margin-bottom:14px}
.form-row.c2{grid-template-columns:1fr 1fr}
.form-row.c3{grid-template-columns:1fr 1fr 1fr}
.form-row.c4{grid-template-columns:repeat(4,1fr)}
.form-group{display:flex;flex-direction:column;gap:6px}
.form-label{font-size:11.5px;color:var(--t2);font-weight:600;display:flex;align-items:center;gap:6px}
.form-input,.form-select{padding:10px 14px;background:var(--bg2);border:1px solid var(--b1);border-radius:9px;color:var(--t1);font-size:13px;font-family:'Cairo',sans-serif;outline:none;transition:border-color .18s;width:100%}
.form-input:focus,.form-select:focus{border-color:var(--b3);box-shadow:0 0 0 3px rgba(0,212,255,.06)}
.form-input.err{border-color:rgba(239,68,68,.5)!important}
textarea.form-input{resize:vertical;min-height:80px}

/* Table */
.tbl-wrap{overflow-x:auto}
.tbl{width:100%;border-collapse:collapse}
.tbl th{font-size:9.5px;color:var(--t3);font-weight:700;letter-spacing:1px;text-transform:uppercase;padding:0 12px 10px;border-bottom:1px solid var(--b1);text-align:right;white-space:nowrap}
.tbl td{padding:10px 12px;border-bottom:1px solid rgba(0,212,255,.03);font-size:12.5px;color:var(--t2)}
.tbl tr:last-child td{border:none}
.tbl tbody tr{cursor:pointer;transition:background .1s}
.tbl tbody tr:hover td{background:rgba(0,212,255,.03);color:var(--t1)}
.mono{font-family:'JetBrains Mono',monospace;font-weight:700;color:var(--a1)}

/* Tags */
.tag{display:inline-flex;align-items:center;gap:3px;padding:3px 9px;border-radius:20px;font-size:10px;font-weight:700;white-space:nowrap}
.tg-blue{background:rgba(0,102,255,.12);color:#60a5fa;border:1px solid rgba(0,102,255,.2)}
.tg-green{background:rgba(16,185,129,.12);color:#34d399;border:1px solid rgba(16,185,129,.2)}
.tg-red{background:rgba(239,68,68,.12);color:#f87171;border:1px solid rgba(239,68,68,.2)}
.tg-gold{background:rgba(245,158,11,.12);color:#fbbf24;border:1px solid rgba(245,158,11,.2)}
.tg-orange{background:rgba(249,115,22,.12);color:#fb923c;border:1px solid rgba(249,115,22,.2)}
.tg-purple{background:rgba(124,58,237,.12);color:#a78bfa;border:1px solid rgba(124,58,237,.2)}
.tg-gray{background:rgba(100,116,139,.12);color:#94a3b8;border:1px solid rgba(100,116,139,.2)}
.tg-cyan{background:rgba(0,212,255,.1);color:var(--a1);border:1px solid var(--b2)}

/* Filter bar */
.fbar{display:flex;align-items:center;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.fbar .form-input{flex:1;min-width:180px}
.search-wrap{position:relative;flex:1;min-width:180px}
.search-wrap .form-input{width:100%;box-sizing:border-box;padding-left:32px}
.search-clear{position:absolute;left:10px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;color:var(--t3);font-size:13px;padding:2px;display:none;line-height:1;z-index:1}
.search-clear:hover{color:var(--r1)}
.search-wrap .form-input:not(:placeholder-shown)~.search-clear{display:block}
.fbar .form-select{width:auto}
.fchip{padding:5px 13px;border-radius:20px;font-size:11px;font-weight:600;cursor:pointer;border:1px solid var(--b1);color:var(--t2);background:transparent;transition:all .14s;font-family:'Cairo',sans-serif}
.fchip.on{background:rgba(0,102,255,.15);border-color:rgba(0,102,255,.4);color:#60a5fa}
.fchip:hover:not(.on){border-color:var(--b2);color:var(--t1)}

/* Stats row */
.stats-row{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:18px}
.stat-card{background:var(--card);border:1px solid var(--b1);border-radius:14px;padding:16px 18px;cursor:pointer;transition:all .2s;position:relative;overflow:hidden}
.stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--c,var(--a1))}
.stat-card:hover{border-color:var(--b2);transform:translateY(-2px);box-shadow:0 8px 28px rgba(0,0,0,.4)}
.st-hd{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}
.st-lbl{font-size:10.5px;color:var(--t2);font-weight:600}
.st-ico{width:28px;height:28px;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:13px}
.st-val{font-size:26px;font-weight:800;font-family:'JetBrains Mono',monospace;line-height:1}
.st-chg{font-size:10.5px;margin-top:6px;display:flex;align-items:center;gap:4px;font-weight:500}
.up{color:var(--g1)}.dn{color:var(--r1)}.nu{color:var(--t2)}

/* Grid layouts */
.g2{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}
.g31{display:grid;grid-template-columns:2fr 1fr;gap:14px;margin-bottom:14px}
.g13{display:grid;grid-template-columns:1fr 2fr;gap:14px}
.gcol{display:flex;flex-direction:column;gap:14px}@keyframes crownbob{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}.emp-crown{font-size:26px;text-align:center;margin-bottom:6px;animation:crownbob 2.5s ease-in-out infinite}@keyframes crownbob{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}.emp-av{width:68px;height:68px;border-radius:50%;margin:0 auto 8px;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:800;color:#fff;position:relative}.emp-av::before{content:"";position:absolute;inset:-4px;border-radius:50%;border:2px solid rgba(255,200,0,.5);animation:empglow 2s ease-in-out infinite}@keyframes empglow{0%,100%{opacity:.3;transform:scale(1)}50%{opacity:.9;transform:scale(1.06)}}

/* Warehouse bars */
.wh-item{margin-bottom:11px}
.wh-item:last-child{margin-bottom:0}
.wh-hd{display:flex;justify-content:space-between;margin-bottom:4px;font-size:12px}
.wh-nm{font-weight:600;color:var(--t1)}
.wh-pct{font-family:'JetBrains Mono',monospace;color:var(--a1);font-size:11px;font-weight:700}
.wh-cnt{font-size:10px;color:var(--t3)}
.wh-track{height:5px;background:rgba(255,255,255,.05);border-radius:3px;overflow:hidden}
.wh-bar{height:100%;border-radius:3px;transition:width 1.2s cubic-bezier(.25,.46,.45,.94);position:relative;overflow:hidden}
.wh-bar::after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,transparent,rgba(255,255,255,.3),transparent);animation:shim 2.5s ease infinite}
@keyframes shim{0%{transform:translateX(-100%)}100%{transform:translateX(200%)}}

/* Alert items */
.alert-item{display:flex;align-items:flex-start;gap:10px;padding:10px 12px;border-radius:9px;margin-bottom:7px;font-size:11.5px;border:1px solid;cursor:pointer;transition:all .16s}
.alert-item:last-child{margin-bottom:0}
.alert-item:hover{transform:translateX(-2px)}
.a-err{background:rgba(239,68,68,.07);border-color:rgba(239,68,68,.25);color:var(--r1)}
.a-warn{background:rgba(245,158,11,.07);border-color:rgba(245,158,11,.25);color:var(--y1)}
.a-ok{background:rgba(16,185,129,.07);border-color:rgba(16,185,129,.25);color:var(--g1)}
.a-info{background:rgba(0,212,255,.07);border-color:rgba(0,212,255,.25);color:var(--a1)}
.a-bd strong{display:block;font-weight:700;margin-bottom:1px}
.a-bd span{opacity:.75}

/* Activity */
.act-item{display:flex;align-items:center;gap:12px;padding:9px 0;border-bottom:1px solid rgba(0,212,255,.04);cursor:pointer;transition:all .12s}
.act-item:last-child{border:none}
.act-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.act-inf{flex:1}
.act-txt{font-size:12px;font-weight:600;color:var(--t2);transition:color .12s}
.act-item:hover .act-txt{color:var(--t1)}
.act-meta{font-size:10.5px;color:var(--t3);margin-top:1px}
.act-time{font-size:10.5px;color:var(--t3);font-family:'JetBrains Mono',monospace;flex-shrink:0}

/* Quick actions */
.qa-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.qa{padding:13px 8px;border-radius:10px;background:var(--card2);border:1px solid var(--b1);cursor:pointer;text-align:center;transition:all .18s;display:flex;flex-direction:column;align-items:center;gap:6px}
.qa:hover{border-color:var(--b2);transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,.4)}
.qa:active{transform:scale(.96)}
.qa i{font-size:18px;transition:transform .18s}
.qa:hover i{transform:scale(1.2)}
.qa-lbl{font-size:10.5px;font-weight:600;color:var(--t2)}
.qa:hover .qa-lbl{color:var(--t1)}

/* Chart */
.chart-wrap{display:flex;align-items:flex-end;gap:6px;height:85px;padding:0 2px}
.b-col{flex:1;display:flex;flex-direction:column;align-items:center;gap:3px}
.b-bar{width:100%;border-radius:3px 3px 0 0;cursor:pointer;transition:all .16s;position:relative}
.b-bar:hover{filter:brightness(1.4)}
.b-bar::after{content:attr(data-v);position:absolute;bottom:calc(100% + 3px);left:50%;transform:translateX(-50%);background:var(--card3);border:1px solid var(--b2);color:var(--a1);font-size:9px;font-family:'JetBrains Mono',monospace;padding:2px 5px;border-radius:4px;opacity:0;transition:opacity .14s;white-space:nowrap;pointer-events:none}
.b-bar:hover::after{opacity:1}
.b-lbl{font-size:8.5px;color:var(--t3)}

/* CART */
.cart-layout{display:grid;grid-template-columns:1fr 340px;gap:16px}
.cart-item-row{display:flex;align-items:center;gap:12px;padding:13px 15px;background:var(--card2);border:1px solid var(--b1);border-radius:11px;margin-bottom:9px;transition:all .16s}
.cart-item-row:hover{border-color:var(--b2)}
.ci-info{flex:1}
.ci-code{font-family:'JetBrains Mono',monospace;font-size:10.5px;color:var(--a1)}
.ci-name{font-size:13px;font-weight:600;color:var(--t1);margin-top:2px}
.ci-wh{font-size:10.5px;color:var(--t3);margin-top:2px}
.ci-max{color:var(--t3)}
.qty-ctrl{display:flex;align-items:center;gap:7px}
.qbtn{width:27px;height:27px;border-radius:7px;background:var(--b1);border:1px solid var(--b2);color:var(--a1);font-size:15px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .14s;font-family:monospace}
.qbtn:hover{background:var(--b2)}
.qval{font-family:'JetBrains Mono',monospace;font-size:14px;font-weight:700;color:var(--t1);min-width:26px;text-align:center}
.ci-del{width:28px;height:28px;border-radius:8px;background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.2);color:#f87171;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .14s;flex-shrink:0}
.ci-del:hover{background:rgba(239,68,68,.2)}
.empty-state{text-align:center;padding:40px 20px}
.empty-state i{font-size:38px;opacity:.2;display:block;margin-bottom:10px}
.empty-state p{color:var(--t3);font-size:13px}
.sum-card{background:var(--card);border:1px solid var(--b1);border-radius:14px;padding:18px}
.sum-card.sticky{position:sticky;top:76px}
.sum-row{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(0,212,255,.05);font-size:12.5px}
.sum-row:last-child{border:none}

/* Inventory */
.stock-bar{height:4px;border-radius:2px;background:rgba(255,255,255,.06);overflow:hidden;margin-top:4px}
.stock-bar-fill{height:100%;border-radius:2px}
.stk-lo{color:var(--r1)} .stk-mid{color:var(--y1)} .stk-hi{color:var(--g1)}

/* FEED/TRANSFER history items */
.hist-item{display:flex;align-items:center;gap:11px;padding:10px 13px;background:var(--card2);border:1px solid var(--b1);border-radius:10px;margin-bottom:7px;transition:all .15s}
.hist-item:hover{border-color:var(--b2)}
.hist-ico{width:32px;height:32px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:13px;flex-shrink:0}
.hist-info{flex:1}
.hist-code{font-family:'JetBrains Mono',monospace;font-size:10.5px}
.hist-name{font-size:12.5px;font-weight:600;color:var(--t1)}
.hist-meta{font-size:10.5px;color:var(--t3);margin-top:1px}
.hist-qty{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:14px}

/* Request/Approve cards */
.req-card{background:var(--card2);border:1px solid var(--b1);border-radius:12px;padding:15px 17px;margin-bottom:11px;transition:all .18s}
.req-card:hover{border-color:var(--b2)}
.req-hd{display:flex;align-items:center;justify-content:space-between;margin-bottom:9px;flex-wrap:wrap;gap:8px}
.req-no{font-family:'JetBrains Mono',monospace;font-size:12.5px;font-weight:700;color:var(--a1)}
.req-actions{display:flex;gap:7px}
.req-body{font-size:12.5px;color:var(--t2);line-height:1.7;margin-bottom:9px}
.req-meta{display:flex;gap:14px;padding-top:9px;border-top:1px solid var(--b1);flex-wrap:wrap}
.req-mi{display:flex;align-items:center;gap:5px;font-size:11px;color:var(--t3)}

/* Contact cards */
.contacts-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:11px}
.cc{background:var(--card2);border:1px solid var(--b1);border-radius:12px;padding:15px 17px;transition:all .18s}
.cc:hover{border-color:var(--b2);transform:translateY(-2px)}
.cc-av{width:42px;height:42px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:#fff;margin-bottom:9px}
.cc-name{font-size:13.5px;font-weight:700;color:var(--t1)}
.cc-role{font-size:11px;color:var(--a1);margin-top:2px}
.cc-tel{font-family:'JetBrains Mono',monospace;font-size:11.5px;color:var(--t2);margin-top:7px;display:flex;align-items:center;gap:5px}
.cc-actions{display:flex;gap:6px;margin-top:9px}

/* User rows */
.user-row{display:flex;align-items:center;gap:13px;padding:12px 15px;background:var(--card2);border:1px solid var(--b1);border-radius:11px;margin-bottom:8px;transition:all .16s}
.user-row:hover{border-color:var(--b2)}
.ur-av{width:38px;height:38px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:#fff;flex-shrink:0}
.ur-info{flex:1}
.ur-name{font-size:13px;font-weight:700;color:var(--t1)}
.ur-role{font-size:10.5px;color:var(--t2);margin-top:2px;display:flex;align-items:center;gap:6px}
.ur-actions{display:flex;gap:6px}
.icon-btn{width:30px;height:30px;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:12px;cursor:pointer;transition:all .14s;border:1px solid}

/* Settings */
.settings-grid{display:grid;grid-template-columns:1fr 1fr;gap:13px}
.setting-sec{background:var(--card);border:1px solid var(--b1);border-radius:14px;padding:17px 19px}
.ss-title{font-size:13px;font-weight:700;color:var(--t1);display:flex;align-items:center;gap:8px;margin-bottom:13px;padding-bottom:10px;border-bottom:1px solid var(--b1)}
.toggle-row{display:flex;align-items:center;justify-content:space-between;padding:7px 0;font-size:12.5px;color:var(--t2);border-bottom:1px solid rgba(0,212,255,.04)}
.toggle-row:last-child{border:none}
.tog{width:38px;height:21px;border-radius:11px;background:rgba(255,255,255,.1);border:1px solid var(--b1);position:relative;cursor:pointer;transition:all .2s;flex-shrink:0}
.tog.on{background:rgba(16,185,129,.3);border-color:rgba(16,185,129,.5)}
.tog::after{content:'';position:absolute;top:3px;right:3px;width:13px;height:13px;border-radius:50%;background:#fff;transition:all .2s;opacity:.6}
.tog.on::after{right:auto;left:3px;opacity:1;background:var(--g1)}

/* BOQ */
.boq-card{background:var(--card2);border:1px solid var(--b1);border-radius:11px;padding:14px 16px;margin-bottom:9px;cursor:pointer;transition:all .16s}
.boq-card:hover{border-color:var(--b2);transform:translateX(-2px)}
.boq-no{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--a1);font-weight:700}
.boq-desc{font-size:13px;font-weight:600;color:var(--t1);margin:3px 0}
.boq-meta{display:flex;gap:13px;font-size:11px;color:var(--t3);flex-wrap:wrap}

/* Logs */
.log-item{display:flex;gap:12px;padding:10px 0;border-bottom:1px solid rgba(0,212,255,.04)}
.log-item:last-child{border:none}
.log-ico{width:30px;height:30px;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:12px;flex-shrink:0}
.log-act{font-size:12.5px;font-weight:600;color:var(--t1)}
.log-meta{font-size:10.5px;color:var(--t3);margin-top:2px}
.log-time{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--t3);flex-shrink:0;text-align:left}

/* Modal */
.overlay{position:fixed;inset:0;background:rgba(0,0,0,.75);backdrop-filter:blur(6px);z-index:800;display:flex;align-items:center;justify-content:center;opacity:0;pointer-events:none;transition:opacity .28s}
.overlay.show{opacity:1;pointer-events:all}
.modal{background:var(--card2);border:1px solid var(--b2);border-radius:18px;padding:26px;width:90%;max-width:520px;transform:scale(.9) translateY(20px);transition:all .28s;box-shadow:0 20px 60px rgba(0,0,0,.7);max-height:90vh;overflow-y:auto}
.overlay.show .modal{transform:none}
.modal-hd{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px}
.modal-title{font-size:15px;font-weight:700;display:flex;align-items:center;gap:9px;color:var(--t1)}
.modal-close{width:30px;height:30px;border-radius:7px;background:transparent;border:1px solid var(--b1);cursor:pointer;color:var(--t2);font-size:14px;display:flex;align-items:center;justify-content:center;transition:all .14s;font-family:monospace}
.modal-close:hover{background:var(--b1);color:var(--t1)}

/* diff compare */
.diff-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}
.diff-box{background:var(--bg2);border:1px solid var(--b1);border-radius:9px;padding:12px}
.diff-label{font-size:9.5px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--t3);margin-bottom:8px}
.diff-row{display:flex;justify-content:space-between;font-size:12px;padding:4px 0;border-bottom:1px solid rgba(0,212,255,.04);color:var(--t2)}
.diff-row:last-child{border:none}
.diff-changed{color:var(--y1)!important;font-weight:700}

/* toasts */
#toasts{position:fixed;bottom:20px;left:20px;z-index:9999;display:flex;flex-direction:column-reverse;gap:8px;pointer-events:none;max-width:300px}
.toast{background:rgba(8,17,42,.97);backdrop-filter:blur(20px);border:1px solid var(--b2);border-radius:11px;padding:11px 13px;display:flex;align-items:flex-start;gap:10px;pointer-events:all;cursor:pointer;animation:tin .38s cubic-bezier(.34,1.56,.64,1);box-shadow:0 8px 30px rgba(0,0,0,.6)}
@keyframes tin{from{opacity:0;transform:translateY(16px) scale(.9)}to{opacity:1;transform:none}}
.toast.out{animation:tout .22s ease forwards}
@keyframes tout{to{opacity:0;transform:translateY(6px) scale(.94)}}
.t-ic{width:30px;height:30px;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:13px;flex-shrink:0}
.t-bd strong{display:block;font-size:12px;font-weight:700;color:var(--t1);margin-bottom:1px}
.t-bd span{font-size:10.5px;color:var(--t2)}

/* My invoices stats */
.mi-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin-bottom:16px}
.mi-s{background:var(--card2);border:1px solid var(--b1);border-radius:10px;padding:13px;text-align:center}
.mi-sv{font-size:21px;font-weight:800;font-family:'JetBrains Mono',monospace;margin-bottom:3px}
.mi-sl{font-size:10.5px;color:var(--t3)}

/* copyright */
.copyright{padding:12px 24px;text-align:center;border-top:1px solid var(--b1);font-size:10.5px;color:var(--t3);display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap}

::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--t4);border-radius:2px}

/* ═══ INVOICE PRINT PREVIEW ═══ */
.inv-preview{background:#fff;color:#000;border-radius:12px;padding:32px;font-family:'Cairo',sans-serif;direction:rtl;max-width:680px;margin:0 auto}
.inv-preview-hd{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:2px solid #006C35;padding-bottom:16px;margin-bottom:18px}
.inv-preview-logo{text-align:center}
.inv-preview-title{font-size:18px;font-weight:800;color:#006C35;margin-bottom:4px}
.inv-preview-sub{font-size:11px;color:#555}
.inv-preview-no{text-align:center;background:#006C35;color:#fff;border-radius:8px;padding:10px 20px;font-size:18px;font-weight:800;font-family:'JetBrains Mono',monospace}
.inv-preview-date{font-size:11px;color:#777;margin-top:4px;text-align:center}
.inv-meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:16px;background:#f8fafc;border-radius:8px;padding:14px}
.inv-meta-item{font-size:12px;color:#555}
.inv-meta-item strong{color:#000;display:block;font-size:13px}
.inv-items-table{width:100%;border-collapse:collapse;margin-bottom:16px}
.inv-items-table th{background:#006C35;color:#fff;padding:8px 12px;font-size:11px;font-weight:700;text-align:right}
.inv-items-table td{padding:8px 12px;border-bottom:1px solid #e2e8f0;font-size:12px}
.inv-items-table tr:last-child td{border:none}
.inv-items-table tr:nth-child(even) td{background:#f8fafc}
.inv-footer{display:flex;justify-content:space-between;align-items:flex-end;margin-top:20px;padding-top:14px;border-top:1px solid #ddd}
.inv-sig{text-align:center;flex:1}
.inv-sig-line{width:120px;height:1px;background:#000;margin:30px auto 4px}
.inv-sig-lbl{font-size:10px;color:#777}
.inv-stamp{width:80px;height:80px;border:2px dashed #006C35;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#006C35;font-size:9px;font-weight:700;text-align:center;padding:8px}

/* ═══ CATEGORY METER ═══ */
.cat-meter{display:flex;flex-direction:column;gap:10px;margin-bottom:14px}
.cat-item{background:var(--card2);border:1px solid var(--b1);border-radius:11px;padding:13px 15px;transition:all .18s;cursor:pointer}
.cat-item:hover{border-color:var(--b2)}
.cat-hd{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}
.cat-nm{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:700;color:var(--t1)}
.cat-ico{width:28px;height:28px;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:12px;flex-shrink:0}
.cat-stats{display:flex;gap:12px;font-size:11px;color:var(--t3)}
.cat-track{height:8px;background:rgba(255,255,255,.06);border-radius:4px;overflow:visible;position:relative;margin-top:4px}
.cat-fill{height:100%;border-radius:4px;transition:width 1s ease;position:relative}
.cat-fill::after{content:'';position:absolute;right:0;top:50%;transform:translate(50%,-50%);width:12px;height:12px;border-radius:50%;background:inherit;border:2px solid var(--bg);box-shadow:0 0 8px currentColor}
.cat-markers{position:relative;height:16px;margin-top:3px}
.cat-marker{position:absolute;font-size:8.5px;color:var(--t3);transform:translateX(50%)}
.cat-alert-badge{padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700;white-space:nowrap}
.alert-critical{background:rgba(239,68,68,.15);color:#f87171;border:1px solid rgba(239,68,68,.3);animation:pulse-r .8s ease-in-out infinite}
.alert-warning{background:rgba(245,158,11,.12);color:#fbbf24;border:1px solid rgba(245,158,11,.3)}
.alert-safe{background:rgba(16,185,129,.1);color:#34d399;border:1px solid rgba(16,185,129,.2)}
@keyframes pulse-r{0%,100%{box-shadow:0 0 0 0 rgba(239,68,68,.4)}50%{box-shadow:0 0 0 5px rgba(239,68,68,0)}}

/* ═══ QUICK FEED BUTTON ═══ */
.quick-feed-btn{position:fixed;left:24px;bottom:24px;z-index:300;width:56px;height:56px;border-radius:16px;background:linear-gradient(135deg,var(--gs),var(--gs2));border:none;cursor:pointer;display:none;align-items:center;justify-content:center;box-shadow:0 8px 28px rgba(0,108,53,.5);transition:all .22s;flex-direction:column;gap:2px}
.quick-feed-btn:hover{transform:translateY(-3px) scale(1.05);box-shadow:0 14px 36px rgba(0,108,53,.6)}
.quick-feed-btn:active{transform:scale(.95)}
#shell.show .quick-feed-btn{display:flex}
.qfb-ico{font-size:20px;color:#fff}
.qfb-lbl{font-size:8px;color:rgba(255,255,255,.8);font-weight:600;letter-spacing:.5px}
.qfb-pulse{position:absolute;inset:-4px;border-radius:20px;border:2px solid rgba(0,146,69,.4);animation:qfp 2s ease infinite}
@keyframes qfp{0%{transform:scale(1);opacity:.8}100%{transform:scale(1.25);opacity:0}}

/* ═══ WAREHOUSE PAGE ═══ */
.wh-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
.wh-card{background:var(--card2);border:1px solid var(--b1);border-radius:14px;padding:18px;transition:all .2s;position:relative;overflow:hidden}
.wh-card:hover{border-color:var(--b2);transform:translateY(-2px)}
.wh-card-top{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:14px}
.wh-card-icon{width:44px;height:44px;border-radius:11px;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0}
.wh-card-nm{font-size:15px;font-weight:800;color:var(--t1);margin-bottom:2px}
.wh-card-loc{font-size:11px;color:var(--t3)}
.wh-prog{height:6px;background:rgba(255,255,255,.06);border-radius:3px;overflow:hidden;margin:10px 0}
.wh-prog-fill{height:100%;border-radius:3px;transition:width 1.2s ease}
.wh-card-stats{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:10px}
.wh-stat{text-align:center;background:rgba(0,0,0,.2);border-radius:7px;padding:7px 4px}
.wh-stat-v{font-size:16px;font-weight:800;font-family:'JetBrains Mono',monospace}
.wh-stat-l{font-size:9px;color:var(--t3);margin-top:1px}

/* ═══ CONTRACTOR PAGE ═══ */
.contr-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:11px}
.contr-card{background:var(--card2);border:1px solid var(--b1);border-radius:12px;padding:15px 17px;transition:all .18s}
.contr-card:hover{border-color:var(--b2)}
.contr-av{width:40px;height:40px;border-radius:10px;background:linear-gradient(135deg,var(--a2),var(--a1));display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#fff;margin-bottom:9px;flex-shrink:0}
.contr-name{font-size:13.5px;font-weight:700;color:var(--t1)}
.contr-type{font-size:11px;color:var(--a1);margin-top:2px}
.contr-tel{font-family:'JetBrains Mono',monospace;font-size:11.5px;color:var(--t2);margin-top:7px;display:flex;align-items:center;gap:5px}@media print{
  body>*{display:none!important}
  #print-overlay{display:block!important;position:static!important;background:none!important;padding:0!important;margin:0!important;overflow:visible!important;width:100vw!important}
  #print-overlay>div:first-child{display:none!important}
  #print-overlay>div:last-child{width:100%!important;max-width:100%!important;box-shadow:none!important;border-radius:0!important;padding:0!important;overflow:visible!important}
  @page{margin:0;size:A4 portrait}
  html,body{margin:0!important;padding:0!important}
}
</style>
</head>
<body>

<!-- BG -->
<div class="bg-fx"><div class="bg-orb"></div><div class="bg-orb"></div><div class="bg-orb"></div></div>
<div class="grid-bg"></div>

<!-- ═══════════════════ LOGIN ═══════════════════ -->
<div id="login-screen">
  <div class="bg-fx" style="z-index:0"><div class="bg-orb"></div><div class="bg-orb"></div></div>
  <div class="grid-bg" style="z-index:0"></div>
  <div class="lcard">
    <div class="llogo">
<img src="data:image/png;base64,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" style="width:90px;height:90px;object-fit:contain">
      <div>
        <div class="ltitle">نظام إدارة مستودعات الطوارئ</div>
        <div class="lsub">دائرة شرق منطقة جازان</div>
      </div>
    </div>
    <div class="ldiv"></div>
    <div class="lfield">
      <div class="llabel"><i class="fa fa-mobile-screen" style="color:var(--a1)"></i>رقم الجوال</div>
      <input class="linput" id="lphone" type="tel" placeholder="05XXXXXXXX" maxlength="10"
        oninput="this.value=this.value.replace(/\D/g,'')" onkeydown="if(event.key==='Enter')document.getElementById('lpass').focus()">
      <div class="lerr" id="lerr-p"><i class="fa fa-circle-xmark"></i><span id="lerr-p-msg"></span></div>
    </div>
    <div class="lfield">
      <div class="llabel"><i class="fa fa-lock" style="color:var(--a1)"></i>كلمة السر</div>
      <div class="prel">
        <input class="linput" id="lpass" type="password" placeholder="••••••••" onkeydown="if(event.key==='Enter')doLogin()" style="padding-left:40px">
        <span class="peye" onclick="togglePeye()"><i class="fa fa-eye" id="peye-ico"></i></span>
      </div>
      <div class="lerr" id="lerr-w"><i class="fa fa-circle-xmark"></i><span id="lerr-w-msg"></span></div>
    </div>
    <button class="lbtn" id="lbtn" onclick="doLogin()"><i class="fa fa-right-to-bracket"></i>  تسجيل الدخول</button>
    <div style="margin:14px 0 8px;text-align:center;padding:10px 12px;background:rgba(0,212,255,.04);border:1px solid var(--b1);border-radius:9px">
      <div style="font-size:10.5px;color:var(--t3)">تم تطويره بواسطة</div>
      <div style="font-size:12px;font-weight:700;color:var(--t2);margin-top:2px">أحمد سعيد عواجي</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--a1);margin-top:2px">0501104283</div>
    </div>
    <div style="font-size:10.5px;color:var(--t3);text-align:center;margin-bottom:7px">اضغط للدخول السريع ↓</div>
    <div class="lhints" id="lhints"></div>
  </div>
</div>

<!-- ═══════════════════ LOADER ═══════════════════ -->
<div id="loader">
  <div class="ldr-bounce">
    <img src="data:image/png;base64,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" style="width:80px;height:80px;object-fit:contain">
  </div>
  <div style="font-size:16px;font-weight:700;color:var(--t1)">جاري تحميل النظام...</div>
  <div style="font-size:10px;color:var(--a1);letter-spacing:3px;font-family:'JetBrains Mono',monospace">EMERGENCY WAREHOUSE SYSTEM</div>
  <div class="ldr-bar"><div class="ldr-fill" id="ldr-fill"></div></div>
  <div class="ldr-pct" id="ldr-pct">0%</div>
</div>

<!-- ═══════════════════ SHELL ═══════════════════ -->
<div id="shell">

<!-- SIDEBAR -->
<aside class="sidebar">
  <div class="s-logo">
    <div class="logo-card" style="width:100%;cursor:default">
      <div class="logo-emblem">
  <img src="data:image/png;base64,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" style="width:60px;height:60px;object-fit:contain;border-radius:8px;background:#fff;padding:3px">
      </div>
      <div class="logo-text-wrap">
        <div class="logo-org">السعودية للطاقة</div>
        <div class="logo-sys">نظام إدارة المستودعات</div>
        <div class="logo-dept">دائرة شرق منطقة جازان</div>
      </div>
    </div>
  </div>
  <nav class="s-nav" id="s-nav">
    <div class="s-sec" id="snav-sec-main">الرئيسية</div>
    <div class="s-item on" data-p="dashboard" data-roles="admin,ameen"><i class="fa fa-gauge-high"></i>لوحة التحكم</div>
    <div class="s-item" data-p="inventory" data-roles="all"><i class="fa fa-boxes-stacked"></i>رصيد المستودعات</div>
    <div class="s-item" data-p="zones" data-roles="all"><i class="fa fa-map-location-dot"></i>رصيد الزونات<span class="s-badge" id="badge-zones" style="display:none"></span></div>
    <div class="s-div" id="snav-div-ops"></div>
    <div class="s-sec" id="snav-sec-ops">الصرف والتغذية</div>
    <div class="s-item" data-p="cart" data-roles="all"><i class="fa fa-cart-shopping"></i>سلة الصرف</div>
    <div class="s-item" data-p="feed" data-roles="admin,ameen"><i class="fa fa-cubes"></i>تغذية المستودع</div>
    <div class="s-item" data-p="direct-return" data-roles="admin,ameen"><i class="fa fa-rotate-left" style="color:var(--g1)"></i>ارجاع مواد</div>
    <div class="s-item" data-p="transfer" data-roles="admin,ameen"><i class="fa fa-right-left"></i>نقل بين المستودعات</div>
    <div class="s-div" id="snav-div-inv"></div>
    <div class="s-sec" id="snav-sec-inv">الفواتير</div>
    <div class="s-item" data-p="myinv" data-roles="moj,wardia"><i class="fa fa-file-circle-check"></i>فواتيري</div>
    <div class="s-item" data-p="inv-edit-req" data-roles="moj,wardia"><i class="fa fa-file-pen" style="color:var(--y1)"></i>طلب تعديل فاتورة صرف</div>
    <div class="s-item" data-p="invoices" data-roles="admin,ameen"><i class="fa fa-file-invoice"></i>أرشيف الفواتير</div>
    <div class="s-item" data-p="edit" data-roles="admin,ameen"><i class="fa fa-file-pen"></i>تعديل فاتورة</div>
    <div class="s-item" data-p="cancel" data-roles="admin,ameen"><i class="fa fa-file-circle-xmark"></i>إلغاء فاتورة</div>
    <div class="s-item" data-p="boq" data-roles="admin,ameen"><i class="fa fa-clipboard-list"></i>قسم BOQ</div>
    <div class="s-div" id="snav-div-req"></div>
    <div class="s-sec" id="snav-sec-req">الطلبات</div>
    <div class="s-item" data-p="requests" data-roles="all"><i class="fa fa-rotate-left"></i>طلبات الارجاع / الالغاء / النقل<span class="s-badge" id="badge-req">3</span></div>
    <div class="s-item" data-p="approve" data-roles="admin,ameen"><i class="fa fa-signature"></i>اعتماد فواتير الصرف<span class="s-badge" id="badge-appr">2</span></div>
    <div class="s-div" id="snav-div-entities"></div>
    <div class="s-sec" id="snav-sec-entities">الكيانات</div>
    <div class="s-item" data-p="warehouses-pg" data-roles="admin,ameen"><i class="fa fa-warehouse"></i>المستودعات</div>
    <div class="s-item" data-p="contractors-pg" data-roles="admin,ameen"><i class="fa fa-hard-hat"></i>المقاولون</div>
    <div class="s-item" data-p="categories-pg" data-roles="admin,ameen"><i class="fa fa-layer-group"></i>الفئات والحدود</div>
    <div class="s-div" id="snav-div-sys"></div>
    <div class="s-sec" id="snav-sec-sys">النظام</div>
    <div class="s-item" data-p="logs" data-roles="admin,ameen"><i class="fa fa-chart-line"></i>سجل العمليات</div>
    <div class="s-item" data-p="contact" data-roles="all"><i class="fa fa-address-book"></i>أرقام التواصل</div>
    <div class="s-item" data-p="users" data-roles="admin"><i class="fa fa-users"></i>المستخدمون</div>
    <div class="s-item" data-p="settings" data-roles="admin"><i class="fa fa-sliders"></i>الإعدادات</div>
  </nav>
  <div class="s-foot">
    <!-- حقوق النظام -->
    <div style="padding:8px 14px;text-align:center;border-top:1px solid var(--b1);background:rgba(0,0,0,.15)">
      <div style="font-size:11px;color:var(--t2);font-weight:700;margin-bottom:3px">نظام إدارة مواد الطوارئ</div>
      <div style="font-size:10px;color:var(--t3);margin-bottom:2px">دائرة شرق منطقة جازان</div>
      <div style="font-size:10px;color:var(--gs2);font-weight:600">تم تطويره بواسطة أحمد سعيد عواجي</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--a1);margin-top:2px;letter-spacing:1px">0501104283</div>
    </div>
    <!-- بطاقة المستخدم + زر الخروج -->
    <div style="display:flex;align-items:center;gap:6px;padding:8px 10px">
      <!-- بطاقة المستخدم مع صورته -->
      <div class="ucard" onclick="showUserProfile()" style="flex:1;min-width:0">
        <div id="uav-wrap" style="width:32px;height:32px;border-radius:50%;overflow:hidden;flex-shrink:0;display:flex;align-items:center;justify-content:center;background:var(--card3)">
          <div class="uav" id="uav" style="font-size:11px;font-weight:800;color:#fff">أح</div>
        </div>
        <div style="flex:1;min-width:0">
          <div class="uname" id="uname">أحمد عواجي</div>
          <div class="urole" id="urole">مدير النظام</div>
        </div>
        <div class="ulive"></div>
      </div>
      <!-- زر الخروج يسار البطاقة -->
      <button onclick="doLogout()" title="تسجيل الخروج"
        style="background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.25);color:#f87171;border-radius:8px;width:34px;height:34px;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:all .2s">
        <i class="fa fa-right-from-bracket"></i>
      </button>
    </div>
  </div>
</aside>

<!-- MAIN -->
<div class="main">
  <!-- TOPBAR -->
  <div class="topbar">
    <div class="tb-l">
      <button onclick="goBack()" id="back-btn" title="رجوع" style="background:rgba(255,255,255,.06);border:1px solid var(--b1);color:var(--t2);border-radius:8px;width:30px;height:30px;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:13px;margin-left:6px;flex-shrink:0"><i class="fa fa-arrow-right"></i></button>
      <span class="tb-title" id="tb-title">لوحة التحكم</span>
      <span class="tb-sep">/</span>
      <span class="tb-sub" id="tb-sub">نظرة عامة</span>
    </div>
    <div class="tb-r">
      <button onclick="toggleViewMode()" id="view-mode-btn" title="تبديل العرض" style="background:rgba(255,255,255,.06);border:1px solid var(--b1);color:var(--t2);border-radius:8px;padding:6px 10px;cursor:pointer;font-size:13px"><i class="fa fa-desktop" id="view-mode-ico"></i></button>
      <div style="display:flex;align-items:center;gap:5px;background:rgba(255,255,255,.06);border:1px solid var(--b1);border-radius:8px;padding:4px 8px">
        <button onclick="changeBrightness(-5)" title="تخفيض السطوع" style="background:none;border:none;color:var(--t2);cursor:pointer;font-size:13px;padding:0 2px;line-height:1"><i class="fa fa-sun" style="font-size:10px"></i>−</button>
        <input type="range" id="brightness-slider" min="60" max="140" value="100" step="5"
          style="width:70px;height:4px;cursor:pointer;accent-color:var(--a1)"
          oninput="applyBrightness(this.value)">
        <button onclick="changeBrightness(5)" title="رفع السطوع" style="background:none;border:none;color:var(--t2);cursor:pointer;font-size:13px;padding:0 2px;line-height:1"><i class="fa fa-sun"></i>+</button>
      </div>
      <div class="live-pill"><div class="ldot"></div>مباشر</div>
      <div class="tb-btn" id="notif-btn" onclick="openNotifs()" title="الإشعارات">
        <i class="fa fa-bell"></i><div class="tb-dot" id="notif-dot"></div>
      </div>
      <div class="tb-btn" onclick="openSearch()" title="بحث سريع Ctrl+K"><i class="fa fa-magnifying-glass"></i></div>
      <div class="tb-btn" onclick="doSync()" title="مزامنة Supabase"><i class="fa fa-rotate" id="sync-ico"></i></div>
      <div class="tb-btn" onclick="toggleFullscreen()" title="ملء الشاشة"><i class="fa fa-expand" id="fs-ico"></i></div>
      <div class="tb-clock" id="clock">00:00:00</div>
      <!-- زر إيقاف الاشعارات مكان زر الخروج -->
      <button id="notif-toggle-btn" onclick="toggleNotifications()" title="تبديل الاشعارات"
        style="background:rgba(255,255,255,.06);border:1px solid var(--b1);color:var(--a1);border-radius:8px;width:34px;height:34px;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:all .2s">
        <i class="fa fa-bell" id="notif-toggle-ico"></i>
      </button>
    </div>
  </div>

  <!-- CONTENT -->
  <div class="content" id="content">

    <!-- ═══ DASHBOARD ═══ -->
    <div id="pg-dashboard" class="page-in">
      <div class="stats-row">
        <div class="stat-card" style="--c:var(--a1)" onclick="go('inventory')">
          <div class="st-hd"><span class="st-lbl">إجمالي الكميات</span><div class="st-ico" style="background:rgba(0,212,255,.1);color:var(--a1)"><i class="fa fa-boxes-stacked"></i></div></div>
          <div class="st-val" id="sv1">0</div>
          <div class="st-chg up"><i class="fa fa-arrow-trend-up"></i>+12% هذا الشهر</div>
        </div>
        <div class="stat-card" style="--c:var(--g1)" onclick="go('invoices')">
          <div class="st-hd"><span class="st-lbl">فواتير نشطة</span><div class="st-ico" style="background:rgba(16,185,129,.1);color:var(--g1)"><i class="fa fa-file-invoice"></i></div></div>
          <div class="st-val" id="sv2">0</div>
          <div class="st-chg up"><i class="fa fa-arrow-trend-up"></i>8 جديدة اليوم</div>
        </div>
        <div class="stat-card" style="--c:var(--r1)" onclick="go('approve')">
          <div class="st-hd"><span class="st-lbl">صرف معلق</span><div class="st-ico" style="background:rgba(239,68,68,.1);color:var(--r1)"><i class="fa fa-cart-shopping"></i></div></div>
          <div class="st-val" id="sv3">0</div>
          <div class="st-chg dn"><i class="fa fa-signature"></i>بانتظار الاعتماد</div>
        </div>
        <div class="stat-card" style="--c:var(--g1)" onclick="go('requests')">
          <div class="st-hd"><span class="st-lbl">ارجاع معلق</span><div class="st-ico" style="background:rgba(16,185,129,.1);color:var(--g1)"><i class="fa fa-rotate-left"></i></div></div>
          <div class="st-val" id="sv4">0</div>
          <div class="st-chg up"><i class="fa fa-clock"></i>بانتظار المراجعة</div>
        </div>
        <div class="stat-card" style="--c:var(--gs)" onclick="go('inventory')">
          <div class="st-hd"><span class="st-lbl">المستودعات</span><div class="st-ico" style="background:rgba(0,108,53,.15);color:#009245"><i class="fa fa-warehouse"></i></div></div>
          <div class="st-val">3</div>
          <div class="st-chg nu"><i class="fa fa-circle-check"></i>جميعها تعمل</div>
        </div>
      </div>
      <div class="g31">
        <div class="card">
          <div class="card-hd">
            <div class="card-title"><i class="fa fa-bolt" style="color:var(--a1)"></i>آخر الفواتير</div>
            <button class="btn btn-sec btn-sm" onclick="go('invoices')">عرض الكل <i class="fa fa-arrow-left"></i></button>
          </div>
          <div class="tbl-wrap">
            <table class="tbl">
              <thead><tr><th>الرقم</th><th>النوع</th><th>المستودع</th><th>المقاول</th><th>الموجه</th><th>الحالة</th><th>التاريخ</th></tr></thead>
              <tbody id="dash-inv-tbody"></tbody>
            </table>
          </div>
        </div>
        <div class="gcol">
          <div id="emp-month-wrap" style="min-height:0"></div>
          <div class="card">
            <div class="card-hd" style="margin-bottom:12px"><div class="card-title"><i class="fa fa-triangle-exclamation" style="color:var(--y1)"></i>التنبيهات</div></div>
            <div id="dash-alerts"></div>
          </div>
        </div>
      </div>
      <div class="g2" style="margin-bottom:14px">
        <div class="card">
          <div class="card-hd"><div class="card-title"><i class="fa fa-fire" style="color:var(--r1)"></i>أكثر المواد صرفاً هذا الشهر</div><button class="btn btn-sec btn-sm" onclick="showTopItemsAll()"><i class="fa fa-list"></i>عرض الكل</button></div>
          <div id="dash-top-items"></div>
        </div>
        <div class="card">
          <div class="card-hd"><div class="card-title"><i class="fa fa-battery-low" style="color:var(--o1)"></i>مواد ستنفذ خلال أسبوع</div><span id="dash-running-out-badge" style="display:none;background:rgba(239,68,68,.15);color:var(--r1);border:1px solid rgba(239,68,68,.3);border-radius:20px;padding:2px 10px;font-size:11px;font-weight:700"></span></div>
          <div id="dash-running-out"></div>
        </div>
      </div>
      <div class="card" style="margin-bottom:14px" id="dash-overdue-card">
        <div class="card-hd"><div class="card-title"><i class="fa fa-hourglass-half" style="color:var(--r1)"></i>فواتير معلقة أكثر من 48 ساعة</div><button class="btn btn-warn btn-sm" onclick="go('approve')"><i class="fa fa-signature"></i>اعتماد الفواتير</button></div>
        <div id="dash-overdue"></div>
      </div>
      <div class="g2">
        <div class="card">
          <div class="card-hd">
            <div class="card-title"><i class="fa fa-wave-square" style="color:var(--g1)"></i>آخر الأنشطة</div>
            <button class="btn btn-sec btn-sm" onclick="go('logs')">السجل الكامل</button>
          </div>
          <div id="dash-acts"></div>
        </div>
        <div class="gcol">
          <div class="card">
            <div class="card-hd" style="margin-bottom:12px"><div class="card-title"><i class="fa fa-rocket" style="color:var(--a4)"></i>إجراءات سريعة</div></div>
            <div class="qa-grid" id="quick-actions-grid"></div>
          </div>
          <div class="card">
            <div class="card-hd" style="margin-bottom:10px"><div class="card-title"><i class="fa fa-chart-column" style="color:var(--a1)"></i>الصرف هذا الأسبوع</div></div>
            <div class="chart-wrap" id="dash-chart"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ INVENTORY ═══ -->
    <div id="pg-inventory" style="display:none" class="page-in">
      <div class="pg-hd">
        <div><div class="pg-title"><i class="fa fa-boxes-stacked" style="color:var(--a1)"></i>رصيد المستودعات</div><div class="pg-sub" id="inv-sub">جميع المواد</div></div>
        <div style="display:flex;gap:8px">
          <button class="btn btn-sec" onclick="exportTable('inv-full-tbody','رصيد_المستودعات')"><i class="fa fa-file-excel"></i>تصدير Excel</button>
          <button class="btn btn-green" id="btn-add-item" onclick="addInventoryItem()" data-roles="admin,ameen"><i class="fa fa-cube"></i>تعريف مادة جديدة</button>
          <button class="btn btn-primary" onclick="go('feed')"><i class="fa fa-plus"></i>تغذية جديدة</button>
        </div>
      </div>
      <!-- تبويبات الرصيد -->
      <div style="display:flex;gap:8px;margin-bottom:12px;border-bottom:1px solid var(--b1);padding-bottom:10px">
        <button id="inv-tab-all" onclick="setInvTab('all')" style="background:transparent;border:none;cursor:pointer;font-size:13px;font-weight:800;color:var(--a1);border-bottom:2px solid var(--a1);padding:4px 12px;border-radius:0"><i class="fa fa-boxes-stacked"></i> الكل</button>
        <button id="inv-tab-reserved" onclick="setInvTab('reserved')" style="background:transparent;border:none;cursor:pointer;font-size:13px;font-weight:400;color:var(--t3);padding:4px 12px;border-radius:0;border-bottom:2px solid transparent"><i class="fa fa-lock"></i> المحجوزات <span id="inv-reserved-badge" style="background:var(--y1);color:#000;border-radius:10px;padding:1px 7px;font-size:10px;font-weight:700;margin-right:3px"></span></button>
      </div>

      <!-- تاب الكل -->
      <div id="inv-tab-all-section">
      <div class="fbar">
        <div class="search-wrap"><input class="form-input" placeholder="🔍  ابحث بالكود أو الاسم..." id="inv-q" oninput="renderInventory()"><button class="search-clear" onclick="document.getElementById('inv-q').value='';renderInventory()" title="مسح البحث"><i class="fa fa-times-circle"></i></button></div>
        <select class="form-select" id="inv-wh" onchange="renderInventory()" style="width:auto">
          <option value="">كل المستودعات</option>
          <option>اسناد</option><option>رايكو صبيا</option><option>هيف بني مالك</option>
        </select>
        <select class="form-select" id="inv-cat" onchange="renderInventory()" style="width:auto">
          <option value="">كل الفئات</option>
          <option>محولات</option><option>كابلات</option><option>قواطع</option><option>عدادات</option><option>صناديق</option><option>إنارة</option>
        </select>
        <select class="form-select" id="inv-stk" onchange="renderInventory()" style="width:auto">
          <option value="">كل المستويات</option>
          <option value="lo">نفذ / منخفض جداً</option>
          <option value="mid">منخفض</option>
          <option value="hi">كافٍ</option>
        </select>
      </div>
      <div class="card tbl-wrap">
        <table class="tbl">
          <thead><tr><th>كود المادة</th><th>اسم المادة</th><th>الفئة</th><th>اسناد</th><th>رايكو صبيا</th><th>هيف بني مالك</th><th>الإجمالي</th><th>المستوى</th><th></th></tr></thead>
          <tbody id="inv-full-tbody"></tbody>
        </table>
      </div>
      </div>

      <!-- تاب المحجوزات -->
      <div id="inv-tab-reserved-section" style="display:none">
        <div class="fbar" style="margin-bottom:12px">
          <div class="search-wrap" style="flex:1">
            <input class="form-input" id="res-q" placeholder="🔍 ابحث بكود أو اسم المادة..." oninput="renderReserved()">
            <button class="search-clear" onclick="document.getElementById('res-q').value='';renderReserved()"><i class="fa fa-times-circle"></i></button>
          </div>
          <select class="form-select" id="res-wh" onchange="renderReserved()" style="width:auto">
            <option value="">كل المستودعات</option>
          </select>
        </div>
        <div id="res-content"></div>
      </div>
    </div>

    <!-- ═══ CART ═══ -->
    <div id="pg-cart" style="display:none" class="page-in">
      <div class="pg-hd">
        <div><div class="pg-title"><i class="fa fa-cart-shopping" style="color:var(--a1)"></i>سلة الصرف</div><div class="pg-sub">إنشاء فاتورة صرف جديدة</div></div>
      </div>
      <div class="cart-layout">
        <div>
          <div class="card" style="margin-bottom:13px">
            <div class="card-hd"><div class="card-title"><i class="fa fa-plus" style="color:var(--g1)"></i>إضافة مادة</div></div>
            <div class="form-row c3" style="align-items:end;margin-bottom:0">
              <div class="form-group">
                <label class="form-label">كود المادة / الاسم</label>
                <input class="form-input" id="cart-add-q" list="inv-datalist" placeholder="908514012 أو محول..." onkeydown="if(event.key==='Enter')cartAdd()">
                <datalist id="inv-datalist"></datalist>
              </div>
              <div class="form-group">
                <label class="form-label">المستودع</label>
                <select class="form-select" id="cart-add-wh"></select>              </div>
              <div class="form-group">
                <label class="form-label">الكمية</label>
                <input class="form-input" id="cart-add-qty" type="number" min="0" value="0" style="font-family:'JetBrains Mono',monospace">
              </div>
            </div>
            <button class="btn btn-primary" style="margin-top:10px" onclick="cartAdd()"><i class="fa fa-plus"></i>إضافة للسلة</button>
          </div>
          <div id="cart-rows"></div>
        </div>
        <div>
          <div class="sum-card sticky">
            <div class="card-hd" style="margin-bottom:14px"><div class="card-title"><i class="fa fa-file-invoice" style="color:var(--y1)"></i>تفاصيل الفاتورة</div></div>
            <div class="form-group" style="margin-bottom:10px">
              <label class="form-label"><i class="fa fa-hard-hat" style="color:var(--o1)"></i>المقاول</label>
              <input class="form-input" id="cart-contractor" placeholder="اسم المقاول...">
            </div>
            <div class="form-group" style="margin-bottom:10px">
              <label class="form-label"><i class="fa fa-clipboard-list" style="color:var(--a3)"></i>رقم BOQ</label>
              <input class="form-input" id="cart-boq" placeholder="BOQ-2026-...">
            </div>
            <div class="form-group" style="margin-bottom:12px">
              <label class="form-label"><i class="fa fa-note-sticky" style="color:var(--t3)"></i>وصف البلاغ <span style="color:var(--r1)">*</span></label>
              <textarea class="form-input" id="cart-notes" rows="2" placeholder="وصف البلاغ أو سبب الصرف... (إجباري)"></textarea>
            </div>
            <div style="border-top:1px solid var(--b1);margin-bottom:10px"></div>
            <div class="sum-row"><span style="color:var(--t2)">عدد الأصناف</span><span style="font-weight:700" id="c-count">0</span></div>
            <div class="sum-row"><span style="color:var(--t2)">الكميات</span><span style="font-weight:700" id="c-total">0 وحدة</span></div>
            <div class="sum-row"><span style="color:var(--t2)">رقم الفاتورة</span><span style="font-weight:700;color:var(--a1)" id="c-no">G49</span></div>
            <div style="margin-top:13px;display:flex;flex-direction:column;gap:7px">
              <div id="cart-approval-badge"></div>
              <button class="btn btn-primary" style="width:100%;justify-content:center" onclick="cartIssue()"><i class="fa fa-paper-plane"></i>إصدار الفاتورة</button>
              <button class="btn btn-danger" style="width:100%;justify-content:center" onclick="cartClear()"><i class="fa fa-trash"></i>مسح السلة</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ FEED ═══ -->
    <div id="pg-feed" style="display:none" class="page-in">
      <div class="pg-hd">
        <div><div class="pg-title"><i class="fa fa-cubes" style="color:var(--g1)"></i>تغذية المستودع</div><div class="pg-sub">إضافة كميات للمخزون</div></div>
      </div>
      <div class="g31">
        <div class="card">
          <div class="card-hd"><div class="card-title"><i class="fa fa-plus-circle" style="color:var(--g1)"></i>عملية تغذية جديدة</div></div>
          <!-- إعدادات عامة مشتركة -->
          <div class="form-row c2" style="margin-bottom:10px">
            <div class="form-group"><label class="form-label">المستودع</label><select class="form-select" id="feed-wh"></select></div>
            <div class="form-group"><label class="form-label">المصدر</label>
              <select class="form-select" id="feed-src" onchange="toggleFeedSrcOther()">
                <option value="مستودع السعودية للطاقة">مستودع السعودية للطاقة</option>
                <option value="مواد راجعة من مشاريع">مواد راجعة من مشاريع</option>
                <option value="أخرى">أخرى</option>
              </select>
              <input class="form-input" id="feed-src-other" placeholder="اكتب المصدر..." style="display:none;margin-top:6px">
            </div>
            <div class="form-group"><label class="form-label">رقم أمر الشراء</label><input class="form-input" id="feed-po" placeholder="PO-2026-..."></div>
            <div class="form-group"><label class="form-label">ملاحظات</label><input class="form-input" id="feed-notes" placeholder="ملاحظات إضافية..."></div>
          </div>
          <!-- قائمة المواد -->
          <div style="font-size:11px;font-weight:700;color:var(--t2);letter-spacing:1px;margin-bottom:6px;border-top:1px solid var(--b1);padding-top:10px">المواد المراد تغذيتها</div>
          <div id="feed-items-list" style="margin-bottom:8px"></div>
          <!-- إضافة مادة جديدة -->
          <div style="background:var(--bg2);border:1px dashed var(--b2);border-radius:9px;padding:12px">
            <div style="font-size:11.5px;color:var(--g1);font-weight:600;margin-bottom:8px"><i class="fa fa-plus"></i> إضافة مادة</div>
            <div style="display:flex;gap:7px;align-items:flex-end;flex-wrap:wrap">
              <div class="form-group" style="flex:2;min-width:130px"><label class="form-label">كود المادة</label><input class="form-input" id="feed-code" list="inv-datalist" placeholder="908514012..." oninput="feedAutoFillName()"></div>
              <div class="form-group" style="flex:2;min-width:130px"><label class="form-label">اسم المادة</label><input class="form-input" id="feed-name" placeholder="يُعبأ تلقائياً..." readonly style="color:var(--t2)"></div>
              <div class="form-group" style="flex:1;min-width:70px"><label class="form-label">الكمية</label><input class="form-input" id="feed-qty" type="number" min="1" value="1" style="font-family:'JetBrains Mono',monospace"></div>
              <button class="btn btn-green btn-sm" onclick="feedAddItem()"><i class="fa fa-plus"></i>إضافة</button>
            </div>
          </div>
          <button class="btn btn-green" style="width:100%;justify-content:center;margin-top:10px" onclick="doFeedMulti()"><i class="fa fa-cubes"></i>تنفيذ التغذية</button>
        </div>
        <div class="card">
          <div class="card-hd" style="margin-bottom:12px"><div class="card-title"><i class="fa fa-history" style="color:var(--a1)"></i>آخر التغذيات</div></div>
          <div id="feed-hist"></div>
        </div>
      </div>
    </div>

    <!-- ═══ TRANSFER ═══ -->
    <div id="pg-transfer" style="display:none" class="page-in">
      <div class="pg-hd">
        <div><div class="pg-title"><i class="fa fa-right-left" style="color:var(--a1)"></i>نقل بين المستودعات</div><div class="pg-sub">نقل داخلي مع فاتورة تلقائية</div></div>
      </div>
      <div class="g31">
        <div class="card">
          <div class="card-hd"><div class="card-title"><i class="fa fa-truck" style="color:var(--a1)"></i>طلب نقل جديد</div></div>
          <!-- اختيار المستودعات -->
          <div class="form-row c3" style="align-items:center;margin-bottom:14px">
            <div class="form-group"><label class="form-label">من مستودع</label><select class="form-select" id="tr-from" onchange="trCheckWh()"></select></div>
            <div style="text-align:center;padding-top:20px;color:var(--a1);font-size:22px"><i class="fa fa-arrow-left"></i></div>
            <div class="form-group"><label class="form-label">إلى مستودع</label><select class="form-select" id="tr-to" onchange="trCheckWh()"></select></div>
          </div>
          <!-- سبب النقل -->
          <div class="form-row c2" style="margin-bottom:10px">
            <div class="form-group"><label class="form-label">سبب النقل</label><input class="form-input" id="tr-reason" placeholder="اكتب سبب النقل..."></div>
            <div class="form-group"><label class="form-label">ملاحظات</label><input class="form-input" id="tr-notes" placeholder="ملاحظات إضافية..."></div>
          </div>
          <!-- إضافة مادة -->
          <div style="font-size:11px;font-weight:700;color:var(--t2);letter-spacing:1px;margin:10px 0 7px;border-top:1px solid var(--b1);padding-top:10px">المواد المراد نقلها</div>
          <div id="tr-items-list"></div>
          <div style="background:var(--bg2);border:1px dashed var(--b2);border-radius:9px;padding:12px;margin-top:8px">
            <div style="font-size:11.5px;color:var(--a1);font-weight:600;margin-bottom:8px"><i class="fa fa-plus"></i> إضافة مادة للنقل</div>
            <div style="display:flex;gap:7px;align-items:flex-end;flex-wrap:wrap">
              <div class="form-group" style="flex:2;min-width:130px">
                <label class="form-label">كود المادة</label>
                <input class="form-input" id="tr-add-code" list="inv-datalist" placeholder="908514012..." oninput="trAutoFill()">
              </div>
              <div class="form-group" style="flex:2;min-width:130px">
                <label class="form-label">اسم المادة</label>
                <input class="form-input" id="tr-add-name" placeholder="يُعبأ تلقائياً..." readonly style="color:var(--t2);background:var(--bg2)">
              </div>
              <div class="form-group" style="flex:1;min-width:70px">
                <label class="form-label">الكمية</label>
                <input class="form-input" id="tr-add-qty" type="number" min="1" value="1" style="font-family:'JetBrains Mono',monospace">
              </div>
              <button class="btn btn-primary btn-sm" onclick="trAddItem()"><i class="fa fa-plus"></i>إضافة</button>
            </div>
            <div id="tr-add-stock" style="font-size:11px;color:var(--t3);margin-top:5px;min-height:16px"></div>
          </div>
          <button class="btn btn-primary" style="width:100%;justify-content:center;margin-top:12px" onclick="doTransfer()"><i class="fa fa-right-left"></i>تنفيذ النقل وإصدار الفاتورة</button>
        </div>
        <div class="card">
          <div class="card-hd" style="margin-bottom:12px"><div class="card-title"><i class="fa fa-history" style="color:var(--a1)"></i>آخر عمليات النقل</div></div>
          <div id="tr-hist"></div>
        </div>
      </div>
    </div>

    <!-- ═══ DIRECT RETURN ═══ -->
    <div id="pg-direct-return" style="display:none" class="page-in">
      <div class="pg-hd">
        <div><div class="pg-title"><i class="fa fa-rotate-left" style="color:var(--g1)"></i>ارجاع مواد</div><div class="pg-sub">إرجاع مواد للمستودع مباشرة بدون اعتماد</div></div>
      </div>
      <div class="g31">
        <div class="card">
          <div class="card-hd"><div class="card-title"><i class="fa fa-rotate-left" style="color:var(--g1)"></i>بيانات الارجاع</div></div>
          <div class="form-group" style="margin-bottom:10px">
            <label class="form-label"><i class="fa fa-file-invoice" style="color:var(--a1)"></i> رقم فاتورة الصرف الأصلية (اختياري)</label>
            <div style="display:flex;gap:6px">
              <input class="form-input" id="dr-inv-no" placeholder="G51..." style="font-family:'JetBrains Mono',monospace" oninput="drFetchInv()">
              <button class="btn btn-sec btn-sm" onclick="drFetchInv()"><i class="fa fa-search"></i>جلب</button>
            </div>
            <div id="dr-inv-info" style="display:none;margin-top:7px;padding:9px 12px;background:rgba(0,212,255,.06);border:1px solid rgba(0,212,255,.2);border-radius:8px;font-size:12px"></div>
          </div>
          <div class="form-row c2">
            <div class="form-group"><label class="form-label"><i class="fa fa-warehouse" style="color:var(--g1)"></i> المستودع المستلم <span style="color:var(--r1)">*</span></label><select class="form-select" id="dr-wh"></select></div>
            <div class="form-group"><label class="form-label"><i class="fa fa-hard-hat" style="color:var(--o1)"></i> المقاول المُسلِّم <span style="color:var(--r1)">*</span></label><input class="form-input" id="dr-cont" placeholder="اسم المقاول..."></div>
            <div class="form-group"><label class="form-label"><i class="fa fa-clipboard-list" style="color:var(--a3)"></i> رقم BOQ</label><input class="form-input" id="dr-boq" placeholder="BOQ-2026-..." style="font-family:'JetBrains Mono',monospace"></div>
            <div class="form-group"><label class="form-label"><i class="fa fa-comment" style="color:var(--t3)"></i> ملاحظات</label><input class="form-input" id="dr-notes" placeholder="سبب الارجاع..."></div>
          </div>
          <div style="font-size:11px;font-weight:700;color:var(--t2);letter-spacing:1px;margin:10px 0 7px;border-top:1px solid var(--b1);padding-top:10px">المواد المُراد إرجاعها</div>
          <div id="dr-items-list"></div>
          <div style="background:var(--bg2);border:1px dashed var(--b2);border-radius:9px;padding:12px;margin-top:8px">
            <div style="font-size:11.5px;color:var(--g1);font-weight:600;margin-bottom:8px"><i class="fa fa-plus"></i> إضافة مادة</div>
            <div style="display:flex;gap:7px;align-items:flex-end;flex-wrap:wrap">
              <div class="form-group" style="flex:2;min-width:130px"><label class="form-label">كود المادة</label><input class="form-input" id="dr-add-code" list="inv-datalist" placeholder="908514012..." oninput="drAutoFill()"></div>
              <div class="form-group" style="flex:2;min-width:130px"><label class="form-label">اسم المادة</label><input class="form-input" id="dr-add-name" placeholder="يُعبأ تلقائياً..." readonly style="color:var(--t2)"></div>
              <div class="form-group" style="flex:1;min-width:70px"><label class="form-label">الكمية</label><input class="form-input" id="dr-add-qty" type="number" min="1" value="1" style="font-family:'JetBrains Mono',monospace"></div>
              <button class="btn btn-green btn-sm" onclick="drAddItem()"><i class="fa fa-plus"></i>إضافة</button>
            </div>
          </div>
          <button class="btn btn-green" style="width:100%;justify-content:center;margin-top:12px" onclick="doDirectReturn()"><i class="fa fa-rotate-left"></i>تنفيذ الارجاع — تُضاف المواد فوراً للمستودع</button>
        </div>
        <div class="card">
          <div class="card-hd" style="margin-bottom:12px"><div class="card-title"><i class="fa fa-history" style="color:var(--a1)"></i>آخر الارجاعات</div></div>
          <div id="dr-hist"></div>
        </div>
      </div>
    </div>

    <!-- ═══ INVOICES ARCHIVE ═══ -->
    <div id="pg-zones" style="display:none" class="page-in">
      <div class="pg-hd">
        <div>
          <div class="pg-title"><i class="fa fa-map-location-dot" style="color:var(--a1)"></i>رصيد الزونات</div>
          <div class="pg-sub" id="zones-sub">اختر زوناً لعرض مستوى مواده</div>
        </div>
        <button class="btn btn-sec" id="btn-zones-export" onclick="zonesExport()" style="display:none"><i class="fa fa-file-excel"></i>تصدير Excel</button>
      </div>

      <!-- بطاقات الزونات -->
      <div id="zones-cards" style="display:flex;gap:14px;flex-wrap:wrap;margin-bottom:20px"></div>

      <!-- محتوى الزون المختار -->
      <div id="zones-content" style="display:none">
        <!-- شريط البحث + التنبيهات -->
        <div class="fbar" style="margin-bottom:14px">
          <div class="search-wrap" style="flex:1">
            <input class="form-input" id="zones-search" list="inv-datalist" placeholder="🔍 ابحث بكود أو اسم المادة..." oninput="zonesRender()">
            <button class="search-clear" onclick="document.getElementById('zones-search').value='';zonesRender()"><i class="fa fa-times-circle"></i></button>
          </div>
          <select class="form-select" id="zones-filter-wh" onchange="zonesRender()" style="width:auto">
            <option value="">كل المستودعات</option>
          </select>
          <select class="form-select" id="zones-filter-level" onchange="zonesRender()" style="width:auto">
            <option value="">كل المستويات</option>
            <option value="حرج">🔴 حرج</option>
            <option value="تحذير">🟡 تحذير</option>
            <option value="آمن">🟢 آمن</option>
          </select>
          <button class="btn btn-sec btn-sm" onclick="document.getElementById('zones-search').value='';document.getElementById('zones-filter-wh').value='';document.getElementById('zones-filter-level').value='';zonesRender()" title="مسح الفلاتر"><i class="fa fa-xmark"></i></button>
        </div>

        <!-- إحصائيات الزون -->
        <div id="zones-stats" style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px"></div>

        <!-- تنبيهات نقص المواد -->
        <div id="zones-alerts" style="margin-bottom:14px"></div>

        <!-- جدول المواد -->
        <div class="card">
          <div class="card-hd" style="margin-bottom:12px">
            <div class="card-title" id="zones-table-title"><i class="fa fa-boxes-stacked" style="color:var(--g1)"></i>مواد الزون</div>
            <div style="font-size:11px;color:var(--t3)" id="zones-wh-list"></div>
          </div>
          <div class="tbl-wrap">
            <table class="tbl">
              <thead>
                <tr>
                  <th>الكود</th>
                  <th>اسم المادة</th>
                  <th>الفئة</th>
                  <th id="zones-wh-headers"></th>
                  <th>الإجمالي</th>
                  <th>المستوى</th>
                </tr>
              </thead>
              <tbody id="zones-tbody"></tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <div id="pg-invoices" style="display:none" class="page-in">
      <div class="pg-hd">
        <div><div class="pg-title"><i class="fa fa-file-invoice" style="color:var(--a1)"></i>أرشيف الفواتير</div><div class="pg-sub" id="inv-arc-sub">جميع الفواتير</div></div>
        <button class="btn btn-sec" onclick="exportInvoicesCSV()"><i class="fa fa-file-excel"></i>تصدير Excel</button>
      </div>

      <!-- تابات الأقسام الرئيسية -->
      <div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap">
        <button class="btn" id="arc-tab-all" onclick="arcSetTab('all')" style="background:rgba(0,212,255,.12);border:1px solid var(--a1);color:var(--a1);border-radius:10px;padding:8px 16px;font-weight:700;font-size:12.5px"><i class="fa fa-layer-group"></i> جميع الفواتير</button>
        <button class="btn" id="arc-tab-active" onclick="arcSetTab('active')" style="background:rgba(255,255,255,.04);border:1px solid var(--b1);color:var(--t2);border-radius:10px;padding:8px 16px;font-weight:700;font-size:12.5px"><i class="fa fa-file-circle-check" style="color:var(--g1)"></i> الصرف والنقل</button>
        <button class="btn" id="arc-tab-cancelled" onclick="arcSetTab('cancelled')" style="background:rgba(255,255,255,.04);border:1px solid var(--b1);color:var(--t2);border-radius:10px;padding:8px 16px;font-weight:700;font-size:12.5px"><i class="fa fa-ban" style="color:var(--r1)"></i> الملغية</button>
      </div>

      <!-- فلاتر البحث -->
      <div class="fbar" style="margin-bottom:12px">
        <div class="search-wrap"><input class="form-input" placeholder="🔍  بحث برقم الفاتورة أو الموجه أو المقاول..." id="inv-arc-q" oninput="renderArc()"><button class="search-clear" onclick="document.getElementById('inv-arc-q').value='';renderArc()" title="مسح البحث"><i class="fa fa-times-circle"></i></button></div>
        <select class="form-select" id="inv-arc-wh" onchange="renderArc()" style="width:auto"><option value="">كل المستودعات</option></select>
        <select class="form-select" id="inv-arc-st" onchange="renderArc()" style="width:auto"><option value="">كل الحالات</option><option>معتمد</option><option>معلق</option><option>مرفوض</option><option>ملغي</option></select>
        <select class="form-select" id="inv-arc-emp" onchange="renderArc()" style="width:auto"><option value="">كل الموجهين</option></select>
        <input type="date" class="form-input" id="inv-arc-date" onchange="renderArc()" style="width:auto;font-family:'JetBrains Mono',monospace" title="فلتر بالتاريخ">
        <button class="btn btn-sec btn-sm" onclick="document.getElementById('inv-arc-date').value='';document.getElementById('inv-arc-emp').value='';document.getElementById('inv-arc-q').value='';renderArc()" title="مسح الفلاتر"><i class="fa fa-xmark"></i> مسح</button>
      </div>

      <!-- إحصائيات سريعة -->
      <div id="inv-arc-stats" style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px"></div>

      <!-- الجدول -->
      <div class="card tbl-wrap">
        <table class="tbl">
          <thead><tr><th>الرقم</th><th>النوع</th><th>المستودع</th><th>الموجه</th><th>المقاول</th><th>الحالة</th><th>التاريخ</th><th>إجراء</th></tr></thead>
          <tbody id="inv-arc-tbody"></tbody>
        </table>
      </div>
    </div>

    <!-- ═══ EDIT ═══ -->
    <div id="pg-edit" style="display:none" class="page-in">
      <div class="pg-hd">
        <div><div class="pg-title"><i class="fa fa-file-pen" style="color:var(--y1)"></i>تعديل فاتورة</div><div class="pg-sub">البحث عن فاتورة وتعديل بياناتها</div></div>
      </div>
      <div class="card" style="margin-bottom:13px">
        <div class="card-hd"><div class="card-title"><i class="fa fa-magnifying-glass" style="color:var(--a1)"></i>البحث</div></div>
        <div style="display:flex;gap:9px">
          <input class="form-input" id="edit-q" placeholder="رقم الفاتورة أو اسم الموجه..." style="flex:1" onkeydown="if(event.key==='Enter')editSearch()">
          <button class="btn btn-primary" onclick="editSearch()"><i class="fa fa-search"></i>بحث</button>
        </div>
        <div id="edit-results" style="margin-top:12px"></div>
      </div>
      <div id="edit-form" style="display:none">
        <div class="card">
          <div class="card-hd"><div class="card-title"><i class="fa fa-pen" style="color:var(--y1)"></i>تعديل الفاتورة <span id="edit-label" style="color:var(--a1)"></span></div></div>
          <div class="form-row c2" style="margin-bottom:12px">
            <div class="form-group"><label class="form-label">المستودع</label><select class="form-select" id="edit-wh"><option>اسناد</option><option>رايكو صبيا</option><option>هيف بني مالك</option></select></div>
            <div class="form-group"><label class="form-label">المقاول</label><input class="form-input" id="edit-cont"></div>
            <div class="form-group"><label class="form-label">رقم BOQ</label><input class="form-input" id="edit-boq" placeholder="BOQ-2026-..."></div>
            <div class="form-group"><label class="form-label">الحالة</label><select class="form-select" id="edit-st"><option>معلق</option><option>معتمد</option><option>مرفوض</option></select></div>
            <div class="form-group" style="grid-column:span 2"><label class="form-label">ملاحظات التعديل</label><input class="form-input" id="edit-notes" placeholder="سبب التعديل..."></div>
          </div>
          <!-- تعديل المواد -->
          <div style="font-size:12px;font-weight:700;color:var(--t2);letter-spacing:1px;text-transform:uppercase;margin-bottom:9px;border-top:1px solid var(--b1);padding-top:12px">المواد في الفاتورة</div>
          <div id="edit-items-list"></div>
          <!-- إضافة مادة جديدة -->
          <div style="background:var(--bg2);border:1px dashed var(--b2);border-radius:9px;padding:12px;margin-top:10px">
            <div style="font-size:12px;color:var(--a1);font-weight:600;margin-bottom:8px"><i class="fa fa-plus"></i> إضافة مادة للفاتورة</div>
            <div style="display:flex;gap:8px;align-items:flex-end;flex-wrap:wrap">
              <div class="form-group" style="flex:2;min-width:140px"><label class="form-label">كود/اسم المادة</label><input class="form-input" id="edit-add-code" list="inv-datalist" placeholder="908514012..."></div>
              <div class="form-group" style="flex:1;min-width:80px"><label class="form-label">الكمية</label><input class="form-input" id="edit-add-qty" type="number" min="1" value="1" style="font-family:'JetBrains Mono',monospace"></div>
              <button class="btn btn-primary btn-sm" onclick="editAddItem()"><i class="fa fa-plus"></i>إضافة</button>
            </div>
          </div>
          <div style="margin-top:14px;display:flex;gap:8px">
            <button class="btn btn-primary" onclick="editSave()"><i class="fa fa-save"></i>حفظ التعديلات</button>
            <button class="btn btn-sec" onclick="document.getElementById('edit-form').style.display='none'"><i class="fa fa-times"></i>إلغاء</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ CANCEL ═══ -->
    <div id="pg-cancel" style="display:none" class="page-in">
      <div class="pg-hd">
        <div><div class="pg-title"><i class="fa fa-file-circle-xmark" style="color:var(--r1)"></i>إلغاء فاتورة مباشر</div><div class="pg-sub">إلغاء وإعادة المواد فوراً — مدير النظام فقط</div></div>
      </div>
      <div class="card" style="margin-bottom:13px">
        <div class="card-hd"><div class="card-title"><i class="fa fa-magnifying-glass" style="color:var(--r1)"></i>البحث عن فاتورة</div></div>
        <div style="display:flex;gap:9px">
          <input class="form-input" id="cancel-q" placeholder="رقم الفاتورة..." style="flex:1" onkeydown="if(event.key==='Enter')cancelSearch()">
          <button class="btn btn-danger" onclick="cancelSearch()"><i class="fa fa-search"></i>بحث</button>
        </div>
        <div id="cancel-results" style="margin-top:12px"></div>
      </div>
      <div id="cancel-form" style="display:none" class="card">
        <div class="card-hd"><div class="card-title"><i class="fa fa-ban" style="color:var(--r1)"></i>تأكيد إلغاء <span id="cancel-label" style="color:var(--r1)"></span></div></div>
        <div style="background:rgba(239,68,68,.07);border:1px solid rgba(239,68,68,.25);border-radius:9px;padding:12px 14px;margin-bottom:14px;font-size:12.5px;color:var(--r1);display:flex;align-items:flex-start;gap:9px">
          <i class="fa fa-triangle-exclamation fa-lg" style="margin-top:2px"></i>
          <span>تحذير: سيتم إلغاء الفاتورة وإعادة جميع المواد للمستودع فوراً. هذا الإجراء لا يمكن التراجع عنه.</span>
        </div>
        <div class="form-row c2">
          <div class="form-group"><label class="form-label">سبب الإلغاء</label><select class="form-select" id="cancel-reason"><option>خطأ في البيانات</option><option>طلب المقاول</option><option>مادة معطوبة</option><option>تكرار الفاتورة</option><option>أخرى</option></select></div>
          <div class="form-group"><label class="form-label">ملاحظات</label><input class="form-input" id="cancel-notes" placeholder="تفاصيل إضافية..."></div>
        </div>
        <div style="display:flex;gap:8px">
          <button class="btn btn-danger" onclick="doCancel()"><i class="fa fa-ban"></i>تأكيد الإلغاء</button>
          <button class="btn btn-sec" onclick="document.getElementById('cancel-form').style.display='none'"><i class="fa fa-times"></i>تراجع</button>
        </div>
      </div>
    </div>

    <!-- ═══ REQUESTS ═══ -->
    <div id="pg-requests" style="display:none" class="page-in">
      <div class="pg-hd">
        <div><div class="pg-title"><i class="fa fa-rotate-left" style="color:var(--o1)"></i><span id="req-pg-title">طلبات الارجاع / الالغاء / النقل</span></div><div class="pg-sub" id="req-sub">بانتظار المراجعة</div></div>
        <div id="req-pg-actions"></div>
      </div>
      <!-- موجه البلاغات: نموذج إنشاء الطلب -->
      <div id="req-mojtahed-view" style="display:none">
        <div class="g2">
          <!-- نموذج طلب ارجاع -->
          <div class="card" id="req-return-form-card">
            <div class="card-hd"><div class="card-title"><i class="fa fa-rotate-left" style="color:var(--o1)"></i>طلب ارجاع مواد</div></div>
            <div class="form-group" style="margin-bottom:10px">
              <label class="form-label"><i class="fa fa-file-invoice" style="color:var(--a1)"></i> رقم الفاتورة الأصلية <span style="color:var(--r1)">*</span></label>
              <div style="display:flex;gap:6px">
                <input class="form-input" id="ret-inv-no" placeholder="G100..." style="font-family:'JetBrains Mono',monospace" oninput="fetchReturnInv()">
                <button class="btn btn-sec btn-sm" onclick="fetchReturnInv()"><i class="fa fa-search"></i></button>
              </div>
            </div>
            <div id="ret-inv-info" style="display:none;margin-bottom:10px;padding:10px;background:rgba(0,212,255,.06);border:1px solid rgba(0,212,255,.2);border-radius:9px;font-size:12px"></div>
            <div class="form-row c2">
              <div class="form-group">
                <label class="form-label"><i class="fa fa-warehouse" style="color:var(--g1)"></i> المستودع المستلم <span style="color:var(--r1)">*</span></label>
                <select class="form-select" id="ret-wh"><option value="">-- اختر --</option></select>
              </div>
              <div class="form-group">
                <label class="form-label"><i class="fa fa-hard-hat" style="color:var(--o1)"></i> المقاول المُسلِّم <span style="color:var(--r1)">*</span></label>
                <input class="form-input" id="ret-cont" placeholder="اسم المقاول..." list="contr-datalist">
                <datalist id="contr-datalist"></datalist>
              </div>
              <div class="form-group">
                <label class="form-label"><i class="fa fa-clipboard-list" style="color:var(--a3)"></i> رقم BOQ <span style="color:var(--r1)">*</span></label>
                <input class="form-input" id="ret-boq-f" placeholder="BOQ-2026-..." style="font-family:'JetBrains Mono',monospace">
              </div>
              <div class="form-group">
                <label class="form-label"><i class="fa fa-comment" style="color:var(--t3)"></i> سبب الارجاع</label>
                <input class="form-input" id="ret-reason-f" placeholder="سبب الارجاع...">
              </div>
            </div>
            <!-- مواد الارجاع -->
            <div style="font-size:11px;font-weight:700;color:var(--t2);letter-spacing:1px;margin:10px 0 7px;border-top:1px solid var(--b1);padding-top:10px">المواد المُراد إرجاعها</div>
            <div id="ret-items-list"></div>
            <div style="background:var(--bg2);border:1px dashed var(--b2);border-radius:9px;padding:11px;margin-top:8px">
              <div style="font-size:11.5px;color:var(--a1);font-weight:600;margin-bottom:7px"><i class="fa fa-plus"></i> إضافة مادة للارجاع</div>
              <div style="display:flex;gap:7px;align-items:flex-end;flex-wrap:wrap">
                <div class="form-group" style="flex:2;min-width:130px"><label class="form-label">كود المادة</label><input class="form-input" id="ret-add-code" list="inv-datalist" placeholder="908514012..."></div>
                <div class="form-group" style="flex:1;min-width:70px"><label class="form-label">الكمية</label><input class="form-input" id="ret-add-qty" type="number" min="1" value="1" style="font-family:'JetBrains Mono',monospace"></div>
                <button class="btn btn-primary btn-sm" onclick="retAddItem()"><i class="fa fa-plus"></i>إضافة</button>
              </div>
            </div>
            <button class="btn btn-warn" style="width:100%;justify-content:center;margin-top:12px" onclick="submitReturnRequest()"><i class="fa fa-paper-plane"></i>تقديم طلب الارجاع</button>
          </div>
          <!-- نموذج طلب الغاء -->
          <div class="card">
            <div class="card-hd"><div class="card-title"><i class="fa fa-ban" style="color:var(--r1)"></i>طلب الغاء فاتورة</div></div>
            <div class="form-group" style="margin-bottom:10px">
              <label class="form-label"><i class="fa fa-file-invoice" style="color:var(--a1)"></i> رقم الفاتورة <span style="color:var(--r1)">*</span></label>
              <div style="display:flex;gap:6px">
                <input class="form-input" id="can-inv-no" placeholder="G100..." style="font-family:'JetBrains Mono',monospace" oninput="fetchCancelInv()">
                <button class="btn btn-sec btn-sm" onclick="fetchCancelInv()"><i class="fa fa-search"></i></button>
              </div>
            </div>
            <div id="can-inv-info" style="display:none;margin-bottom:10px;padding:10px;background:rgba(239,68,68,.06);border:1px solid rgba(239,68,68,.2);border-radius:9px;font-size:12px"></div>
            <div class="form-row c2">
              <div class="form-group">
                <label class="form-label"><i class="fa fa-warehouse" style="color:var(--g1)"></i> المستودع المستلم للمواد <span style="color:var(--r1)">*</span></label>
                <select class="form-select" id="can-wh"><option value="">-- اختر --</option><option>اسناد</option><option>رايكو صبيا</option><option>هيف بني مالك</option></select>
              </div>
              <div class="form-group">
                <label class="form-label"><i class="fa fa-hard-hat" style="color:var(--o1)"></i> المقاول المُسلِّم <span style="color:var(--r1)">*</span></label>
                <input class="form-input" id="can-cont" placeholder="اسم المقاول..." list="contr-datalist">
              </div>
              <div class="form-group">
                <label class="form-label"><i class="fa fa-clipboard-list" style="color:var(--a3)"></i> رقم BOQ <span style="color:var(--r1)">*</span></label>
                <input class="form-input" id="can-boq-f" placeholder="BOQ-2026-..." style="font-family:'JetBrains Mono',monospace">
              </div>
              <div class="form-group">
                <label class="form-label"><i class="fa fa-comment" style="color:var(--r1)"></i> سبب الالغاء <span style="color:var(--r1)">*</span></label>
                <input class="form-input" id="can-reason-f" placeholder="سبب طلب الالغاء...">
              </div>
            </div>
            <button class="btn btn-danger" style="width:100%;justify-content:center;margin-top:12px" onclick="submitCancelRequest()"><i class="fa fa-paper-plane"></i>تقديم طلب الالغاء</button>
          </div>
        </div>
        <!-- نموذج طلب نقل - لمشرف الوردية فقط -->
        <div id="wardia-transfer-card" style="display:none;margin-top:14px">
          <div class="card">
            <div class="card-hd"><div class="card-title"><i class="fa fa-right-left" style="color:var(--a1)"></i>طلب نقل مواد بين المستودعات</div></div>
            <div class="form-row c2" style="margin-bottom:10px">
              <div class="form-group"><label class="form-label"><i class="fa fa-warehouse" style="color:var(--r1)"></i> من مستودع <span style="color:var(--r1)">*</span></label><select class="form-select" id="wtr-from"><option value="">-- اختر --</option></select></div>
              <div class="form-group"><label class="form-label"><i class="fa fa-warehouse" style="color:var(--g1)"></i> إلى مستودع <span style="color:var(--r1)">*</span></label><select class="form-select" id="wtr-to"><option value="">-- اختر --</option></select></div>
              <div class="form-group" style="grid-column:span 2"><label class="form-label"><i class="fa fa-comment" style="color:var(--t3)"></i> سبب النقل</label><input class="form-input" id="wtr-reason" placeholder="سبب طلب النقل..."></div>
            </div>
            <div style="font-size:11px;font-weight:700;color:var(--t2);letter-spacing:1px;margin-bottom:7px;border-top:1px solid var(--b1);padding-top:10px">المواد المراد نقلها</div>
            <div id="wtr-items-list"></div>
            <div style="background:var(--bg2);border:1px dashed var(--b2);border-radius:9px;padding:11px;margin-top:8px">
              <div style="font-size:11.5px;color:var(--a1);font-weight:600;margin-bottom:7px"><i class="fa fa-plus"></i> إضافة مادة للنقل</div>
              <div style="display:flex;gap:7px;align-items:flex-end;flex-wrap:wrap">
                <div class="form-group" style="flex:2;min-width:130px"><label class="form-label">كود المادة</label><input class="form-input" id="wtr-add-code" list="inv-datalist" placeholder="908514012..." oninput="wtrAutoFill()"></div>
                <div class="form-group" style="flex:2;min-width:130px"><label class="form-label">اسم المادة</label><input class="form-input" id="wtr-add-name" placeholder="يُعبأ تلقائياً..." readonly style="color:var(--t2)"></div>
                <div class="form-group" style="flex:1;min-width:70px"><label class="form-label">الكمية</label><input class="form-input" id="wtr-add-qty" type="number" min="1" value="1" style="font-family:'JetBrains Mono',monospace"></div>
                <button class="btn btn-primary btn-sm" onclick="wtrAddItem()"><i class="fa fa-plus"></i>إضافة</button>
              </div>
            </div>
            <div style="background:rgba(255,184,32,.06);border:1px solid rgba(255,184,32,.2);border-radius:8px;padding:8px 12px;margin-top:8px;font-size:11.5px;color:var(--y1)"><i class="fa fa-info-circle"></i> لن تُنقل الكميات إلا بعد اعتماد مدير النظام أو مسؤول المستودعات</div>
            <button class="btn btn-primary" style="width:100%;justify-content:center;margin-top:10px" onclick="submitWardiaTransfer()"><i class="fa fa-paper-plane"></i>إرسال طلب النقل للاعتماد</button>
          </div>
        </div>
        <!-- طلباتي السابقة -->
        <div class="card" style="margin-top:14px">
          <div class="card-hd"><div class="card-title"><i class="fa fa-clock" style="color:var(--y1)"></i>طلباتي السابقة</div></div>
          <div id="req-mylist"></div>
        </div>
      </div>
      <!-- مدير النظام / أمين المستودع: قائمة الطلبات -->
      <div id="req-admin-view" style="display:none">
        <div style="display:flex;gap:6px;margin-bottom:12px">
          <button class="btn btn-sec btn-sm" id="req-tab-pending" onclick="setReqTab('pending')" style="font-weight:700"><i class="fa fa-clock"></i>المعلقة <span id="req-pending-cnt" class="s-badge" style="position:relative;top:0;right:0;margin-right:4px"></span></button>
          <button class="btn btn-sec btn-sm" id="req-tab-history" onclick="setReqTab('history')"><i class="fa fa-history"></i>السابقة</button>
        </div>
        <!-- المعلقة -->
        <div id="req-pending-section">
          <div class="fbar" id="req-chips"></div>
          <div id="req-list"></div>
        </div>
        <!-- السابقة -->
        <div id="req-history-section" style="display:none">
          <div class="card" style="padding:12px 14px;margin-bottom:12px">
            <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end">
              <div class="search-wrap" style="flex:1">
                <input class="form-input" id="req-hist-q" placeholder="🔍 بحث برقم الطلب أو المقاول..." oninput="renderReqHistory()">
                <button class="search-clear" onclick="document.getElementById('req-hist-q').value='';renderReqHistory()"><i class="fa fa-times-circle"></i></button>
              </div>
              <select class="form-select" id="req-hist-type" onchange="renderReqHistory()" style="width:auto">
                <option value="">كل الأنواع</option>
                <option value="ارجاع">ارجاع</option>
                <option value="الغاء">الغاء</option>
                <option value="نقل">نقل</option>
                <option value="تعديل">تعديل</option>
              </select>
              <select class="form-select" id="req-hist-st" onchange="renderReqHistory()" style="width:auto">
                <option value="">كل الحالات</option>
                <option value="معتمد">✅ معتمد</option>
                <option value="مرفوض">❌ مرفوض</option>
              </select>
              <input type="date" class="form-input" id="req-hist-date" onchange="renderReqHistory()" style="width:auto;font-family:'JetBrains Mono',monospace">
              <button class="btn btn-sec btn-sm" onclick="['req-hist-q','req-hist-type','req-hist-st','req-hist-date'].forEach(function(id){var e=document.getElementById(id);if(e)e.value='';});renderReqHistory()"><i class="fa fa-xmark"></i>مسح</button>
            </div>
          </div>
          <div id="req-hist-list"></div>
        </div>
      </div>
    </div>

    <!-- ═══ APPROVE ═══ -->
    <div id="pg-approve" style="display:none" class="page-in">
      <div class="pg-hd">
        <div><div class="pg-title"><i class="fa fa-signature" style="color:var(--y1)"></i>اعتماد فواتير الصرف</div><div class="pg-sub" id="appr-sub">بانتظار الاعتماد</div></div>
        <div style="display:flex;gap:6px">
          <button class="btn btn-sec btn-sm" id="appr-tab-pending" onclick="setApprTab('pending')" style="font-weight:700"><i class="fa fa-clock"></i>معلقة <span id="appr-pending-badge" class="s-badge" style="position:relative;top:0;right:0;margin-right:4px"></span></button>
          <button class="btn btn-sec btn-sm" id="appr-tab-history" onclick="setApprTab('history')"><i class="fa fa-history"></i>السابقة</button>
        </div>
      </div>
      <!-- قسم المعلقة -->
      <div id="appr-pending-section">
      <!-- فلاتر البحث -->
      <div class="card" style="padding:12px 14px;margin-bottom:12px">
        <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end">
          <div class="form-group" style="flex:1;min-width:140px;margin-bottom:0">
            <label class="form-label"><i class="fa fa-warehouse"></i> فلتر المستودع</label>
            <select class="form-select" id="appr-filter-wh" onchange="renderApprovals()"><option value="">كل المستودعات</option></select>
          </div>
          <div class="form-group" style="flex:1;min-width:140px;margin-bottom:0">
            <label class="form-label"><i class="fa fa-calendar"></i> فلتر التاريخ</label>
            <input type="date" class="form-input" id="appr-filter-date" onchange="renderApprovals()" style="font-family:'JetBrains Mono',monospace">
          </div>
          <button class="btn btn-sec btn-sm" onclick="document.getElementById('appr-filter-wh').value='';document.getElementById('appr-filter-date').value='';renderApprovals()">
            <i class="fa fa-xmark"></i>مسح الفلاتر
          </button>
        </div>
      </div>
      <div id="appr-list"></div>
      </div>

      <!-- قسم الطلبات السابقة -->
      <div id="appr-history-section" style="display:none">
        <div class="card" style="padding:12px 14px;margin-bottom:12px">
          <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end">
            <div class="search-wrap" style="flex:1">
              <input class="form-input" id="appr-hist-q" placeholder="🔍 بحث برقم الفاتورة أو المقاول..." oninput="renderApprHistory()">
              <button class="search-clear" onclick="document.getElementById('appr-hist-q').value='';renderApprHistory()"><i class="fa fa-times-circle"></i></button>
            </div>
            <select class="form-select" id="appr-hist-st" onchange="renderApprHistory()" style="width:auto">
              <option value="">كل الحالات</option>
              <option value="معتمد">✅ معتمد</option>
              <option value="مرفوض">❌ مرفوض</option>
            </select>
            <input type="date" class="form-input" id="appr-hist-date" onchange="renderApprHistory()" style="width:auto;font-family:'JetBrains Mono',monospace">
            <button class="btn btn-sec btn-sm" onclick="document.getElementById('appr-hist-q').value='';document.getElementById('appr-hist-st').value='';document.getElementById('appr-hist-date').value='';renderApprHistory()"><i class="fa fa-xmark"></i>مسح</button>
          </div>
        </div>
        <div id="appr-hist-list"></div>
      </div>
    </div>

    <!-- ═══ INV EDIT REQUEST ═══ -->
    <div id="pg-inv-edit-req" style="display:none" class="page-in">
      <div class="pg-hd">
        <div><div class="pg-title"><i class="fa fa-file-pen" style="color:var(--y1)"></i>طلب تعديل فاتورة صرف</div><div class="pg-sub">اختر فاتورة وعدّل بياناتها — لا خصم إلا بعد الاعتماد</div></div>
      </div>
      <!-- قائمة الفواتير -->
      <div class="card" style="margin-bottom:14px" id="ier-list-card">
        <div class="card-hd"><div class="card-title"><i class="fa fa-file-invoice"></i>فواتيري</div></div>
        <div class="fbar">
          <div class="search-wrap"><input class="form-input" id="ier-search" placeholder="🔍 بحث برقم الفاتورة أو المقاول..." oninput="renderIerList()"></div>
          <select class="form-select" id="ier-filter-st" onchange="renderIerList()" style="width:auto"><option value="">كل الحالات</option><option>معتمد</option><option>معلق</option><option>مرفوض</option></select>
          <select class="form-select" id="ier-filter-type" onchange="renderIerList()" style="width:auto"><option value="">كل الأنواع</option><option>صرف</option><option>ارجاع</option><option>نقل</option></select>
        </div>
        <div id="ier-list"></div>
      </div>
      <!-- نموذج التعديل - يتغير حسب نوع الفاتورة -->
      <div id="ier-form-card" style="display:none">
        <!-- رأس + رجوع -->
        <div class="card" style="margin-bottom:12px">
          <div class="card-hd" style="margin-bottom:10px">
            <div style="display:flex;align-items:center;gap:10px">
              <div id="ier-type-badge"></div>
              <div class="card-title" style="margin:0"><i class="fa fa-pen" style="color:var(--y1)"></i> تعديل <span id="ier-inv-no" class="mono" style="color:var(--a1);font-size:15px"></span></div>
            </div>
            <button class="btn btn-sec btn-sm" onclick="ierGoBack()"><i class="fa fa-arrow-right"></i>رجوع</button>
          </div>
          <div id="ier-prev-approved" style="display:none;background:rgba(255,184,32,.08);border:1px solid rgba(255,184,32,.3);border-radius:9px;padding:8px 14px;margin-bottom:12px;font-size:12px;color:var(--y1)">
            <i class="fa fa-triangle-exclamation"></i> هذه الفاتورة كانت معتمدة سابقاً — سيُعاد إرسالها للاعتماد بعد التعديل
          </div>
          <!-- حقول تتغير حسب النوع -->
          <div id="ier-fields-dynamic"></div>
        </div>
        <!-- إدارة المواد -->
        <div class="card" style="margin-bottom:12px">
          <div class="card-hd" style="margin-bottom:10px">
            <div class="card-title"><i class="fa fa-boxes-stacked" style="color:var(--g1)"></i>المواد في الفاتورة</div>
          </div>
          <div id="ier-items-list"></div>
          <div style="background:var(--bg2);border:1px dashed var(--b2);border-radius:10px;padding:12px;margin-top:10px">
            <div style="font-size:11.5px;color:var(--a1);font-weight:700;margin-bottom:8px"><i class="fa fa-plus-circle"></i> إضافة مادة</div>
            <div style="display:flex;gap:8px;align-items:flex-end;flex-wrap:wrap">
              <div class="form-group" style="flex:2;min-width:130px;margin-bottom:0"><label class="form-label">كود المادة</label><input class="form-input" id="ier-add-code" list="inv-datalist" placeholder="908514012..." oninput="ierAutoFill()" style="font-family:'JetBrains Mono',monospace;direction:ltr"></div>
              <div class="form-group" style="flex:2;min-width:130px;margin-bottom:0"><label class="form-label">الاسم</label><input class="form-input" id="ier-add-name" placeholder="يُعبأ تلقائياً..." readonly style="color:var(--t2)"></div>
              <div class="form-group" style="flex:1;min-width:70px;margin-bottom:0"><label class="form-label">الكمية</label><input class="form-input" id="ier-add-qty" type="number" min="1" value="1" style="font-family:'JetBrains Mono',monospace"></div>
              <button class="btn btn-primary btn-sm" onclick="ierAddItem()"><i class="fa fa-plus"></i>إضافة</button>
            </div>
          </div>
        </div>
        <!-- إرسال -->
        <div class="card">
          <div style="background:rgba(255,184,32,.06);border:1px solid rgba(255,184,32,.2);border-radius:8px;padding:9px 14px;margin-bottom:12px;font-size:12px;color:var(--y1)">
            <i class="fa fa-info-circle"></i> لا خصم على المخزون إلا بعد اعتماد المدير — المواد المحذوفة تُعاد للمستودع المُسلِّم
          </div>
          <button class="btn btn-primary" style="width:100%;justify-content:center" onclick="submitIerRequest()">
            <i class="fa fa-paper-plane"></i>إرسال طلب التعديل للاعتماد
          </button>
        </div>
      </div>
    </div>

    <!-- ═══ MY INVOICES ═══ -->
    <div id="pg-myinv" style="display:none" class="page-in">
      <div class="pg-hd">
        <div><div class="pg-title"><i class="fa fa-file-circle-check" style="color:var(--a1)"></i>فواتيري</div><div class="pg-sub" id="myinv-sub">فواتيرك الشخصية</div></div>
      </div>
      <div class="mi-stats" id="myinv-stats"></div>

      <!-- ═══ القسم الأول: المعتمدة والمرفوضة ═══ -->
      <div class="card" style="margin-bottom:14px">
        <div class="card-hd" style="margin-bottom:10px">
          <div class="card-title"><i class="fa fa-file-invoice" style="color:var(--g1)"></i>الفواتير المنتهية</div>
          <span id="myinv-done-count" style="font-size:11px;color:var(--t3)"></span>
        </div>
        <div class="fbar" style="margin-bottom:10px">
          <div class="search-wrap"><input class="form-input" placeholder="🔍 بحث..." id="myinv-q" oninput="renderMyInv()"><button class="search-clear" onclick="document.getElementById('myinv-q').value='';renderMyInv()"><i class="fa fa-times-circle"></i></button></div>
          <select class="form-select" id="myinv-type" onchange="renderMyInv()" style="width:auto">
            <option value="">كل الأنواع</option>
            <option>صرف</option><option>ارجاع</option><option>نقل</option><option>الغاء</option>
          </select>
        </div>
        <div class="tbl-wrap">
          <table class="tbl">
            <thead><tr><th>الرقم</th><th>النوع</th><th>المستودع</th><th>المقاول</th><th>الحالة</th><th>التاريخ</th><th>إجراء</th></tr></thead>
            <tbody id="myinv-done-tbody"></tbody>
          </table>
        </div>
      </div>

      <!-- ═══ القسم الثاني: المعلقة (بانتظار الاعتماد) ═══ -->
      <div class="card" style="border:1px solid rgba(245,158,11,.25);background:rgba(245,158,11,.03)">
        <div class="card-hd" style="margin-bottom:10px">
          <div class="card-title"><i class="fa fa-clock" style="color:var(--y1)"></i>بانتظار الاعتماد <span id="myinv-pend-badge" style="display:none;background:var(--y1);color:#000;border-radius:20px;padding:1px 8px;font-size:11px;font-weight:700;margin-right:6px"></span></div>
          <span style="font-size:11px;color:var(--t3)">يمكنك تعديل أو سحب الفاتورة قبل الاعتماد</span>
        </div>
        <div class="tbl-wrap">
          <table class="tbl">
            <thead><tr><th>الرقم</th><th>النوع</th><th>المستودع</th><th>المقاول</th><th>التاريخ</th><th>إجراء</th></tr></thead>
            <tbody id="myinv-pend-tbody"></tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ═══ BOQ ═══ -->
    <div id="pg-boq" style="display:none" class="page-in">
      <div class="pg-hd">
        <div><div class="pg-title"><i class="fa fa-clipboard-list" style="color:var(--a3)"></i>بحث BOQ</div><div class="pg-sub" id="boq-sub">ابحث برقم BOQ لعرض الفواتير المرتبطة</div></div>
      </div>
      <div class="card" style="margin-bottom:14px">
        <div class="card-hd"><div class="card-title"><i class="fa fa-magnifying-glass" style="color:var(--a1)"></i>البحث برقم BOQ</div></div>
        <div class="search-wrap" style="margin-bottom:8px">
          <input class="form-input" placeholder="ادخل رقم BOQ للبحث عن الفواتير المرتبطة..." id="boq-search-q" oninput="boqSearchInv()" style="font-family:'JetBrains Mono',monospace">
          <button class="search-clear" onclick="document.getElementById('boq-search-q').value='';boqSearchInv()"><i class="fa fa-times-circle"></i></button>
        </div>
        <div id="boq-search-results"></div>
      </div>
    </div>

    <!-- ═══ LOGS ═══ -->
    <div id="pg-logs" style="display:none" class="page-in">
      <div class="pg-hd">
        <div><div class="pg-title"><i class="fa fa-chart-line" style="color:var(--a1)"></i>سجل العمليات</div><div class="pg-sub" id="logs-sub">جميع العمليات</div></div>
        <button class="btn btn-sec" onclick="exportLogs()"><i class="fa fa-file-excel"></i>تصدير Excel</button>
      </div>
      <div class="fbar">
        <div class="search-wrap"><input class="form-input" placeholder="🔍  بحث..." id="logs-q" oninput="renderLogs()"><button class="search-clear" onclick="document.getElementById('logs-q').value='';renderLogs()" title="مسح البحث"><i class="fa fa-times-circle"></i></button></div>
        <select class="form-select" id="logs-type" onchange="renderLogs()" style="width:auto"><option value="">كل العمليات</option><option>صرف</option><option>تغذية</option><option>نقل</option><option>ارجاع</option><option>إلغاء</option><option>تعديل</option></select>
        <select class="form-select" id="logs-emp" onchange="renderLogs()" style="width:auto"><option value="">كل الموظفين</option></select>
        <input type="date" class="form-input" id="logs-date" onchange="renderLogs()" style="width:auto;font-family:'JetBrains Mono',monospace" title="فلتر بالتاريخ">
        <button class="btn btn-sec btn-sm" onclick="document.getElementById('logs-date').value='';renderLogs()" title="مسح التاريخ"><i class="fa fa-xmark"></i></button>
      </div>
      <div class="card"><div id="logs-list"></div></div>
    </div>

    <!-- ═══ CONTACT ═══ -->
    <div id="pg-contact" style="display:none" class="page-in">
      <div class="pg-hd">
        <div><div class="pg-title"><i class="fa fa-address-book" style="color:var(--a1)"></i>أرقام التواصل</div><div class="pg-sub">دليل موظفي دائرة شرق جازان</div></div>
        <button class="btn btn-primary" onclick="contactNew()" id="btn-contact-new"><i class="fa fa-user-plus"></i>إضافة جهة</button>
      </div>
      <div class="fbar" style="margin-bottom:16px">
        <div class="search-wrap"><input class="form-input" placeholder="🔍  ابحث بالاسم أو الدور..." id="contact-q" oninput="renderContacts()"><button class="search-clear" onclick="document.getElementById('contact-q').value='';renderContacts()" title="مسح البحث"><i class="fa fa-times-circle"></i></button></div>
        <select class="form-select" id="contact-dept" onchange="renderContacts()" style="width:auto"><option value="">كل الأقسام</option><option>إدارة</option><option>موجهون</option><option>أمناء مستودعات</option><option>أخرى</option></select>
      </div>
      <div class="contacts-grid" id="contacts-grid"></div>
    </div>

    <!-- ═══ USERS ═══ -->
    <div id="pg-users" style="display:none" class="page-in">
      <div class="pg-hd">
        <div><div class="pg-title"><i class="fa fa-users" style="color:var(--a3)"></i>إدارة المستخدمين</div><div class="pg-sub" id="users-sub">المستخدمون النشطون</div></div>
        <button class="btn btn-primary" onclick="userNew()"><i class="fa fa-user-plus"></i>مستخدم جديد</button>
      </div>
      <div class="fbar">
        <div class="search-wrap"><input class="form-input" placeholder="🔍  بحث..." id="users-q" oninput="renderUsers()"><button class="search-clear" onclick="document.getElementById('users-q').value='';renderUsers()" title="مسح البحث"><i class="fa fa-times-circle"></i></button></div>
        <select class="form-select" id="users-role" onchange="renderUsers()" style="width:auto"><option value="">كل الأدوار</option><option>مدير النظام</option><option>موجه بلاغات</option><option>أمين مستودع</option></select>
      </div>
      <div id="users-list"></div>
    </div>

    <!-- ═══ SETTINGS ═══ -->
    <div id="pg-settings" style="display:none" class="page-in">
      <div class="pg-hd">
        <div><div class="pg-title"><i class="fa fa-sliders" style="color:var(--a1)"></i>إعدادات النظام</div><div class="pg-sub">ضبط النظام والمستودعات</div></div>
        <button class="btn btn-green" onclick="saveSettings()"><i class="fa fa-save"></i>حفظ الإعدادات</button>
      </div>
      <div class="settings-grid" id="settings-content"></div>

      <!-- بطاقة التنظيف التلقائي — للمدير فقط -->
      <div class="card" style="margin-top:16px;border:1px solid rgba(239,68,68,.2);background:rgba(239,68,68,.03)" id="cleanup-card">
        <div class="card-hd" style="margin-bottom:12px">
          <div class="card-title" style="color:var(--r1)"><i class="fa fa-broom"></i> التنظيف التلقائي للبيانات</div>
          <span style="font-size:11px;color:var(--g1)"><i class="fa fa-shield-halved"></i> الرصيد والمستودعات والزونات محمية دائماً</span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:14px;font-size:12px">
          <div style="background:var(--bg2);border-radius:8px;padding:10px;border:1px solid rgba(239,68,68,.15)">
            <div style="color:var(--r1);font-size:11px;margin-bottom:4px"><i class="fa fa-file-invoice"></i> الفواتير + ارتباطاتها</div>
            <div style="font-weight:700;color:var(--t1)">بعد <span style="color:var(--r1)">سنة</span> من الاعتماد</div>
            <div style="font-size:10px;color:var(--t3);margin-top:3px">طلبات + اعتمادات + BOQ مرتبطة</div>
          </div>
          <div style="background:var(--bg2);border-radius:8px;padding:10px;border:1px solid rgba(245,158,11,.15)">
            <div style="color:var(--y1);font-size:11px;margin-bottom:4px"><i class="fa fa-list-check"></i> سجل العمليات</div>
            <div style="font-weight:700;color:var(--t1)">بعد <span style="color:var(--y1)">شهرين</span></div>
            <div style="font-size:10px;color:var(--t3);margin-top:3px">يُحذف تلقائياً</div>
          </div>
          <div style="background:var(--bg2);border-radius:8px;padding:10px;border:1px solid rgba(99,102,241,.15)">
            <div style="color:#818cf8;font-size:11px;margin-bottom:4px"><i class="fa fa-bell"></i> الإشعارات</div>
            <div style="font-weight:700;color:var(--t1)">بعد <span style="color:#818cf8">شهر</span></div>
            <div style="font-size:10px;color:var(--t3);margin-top:3px">يُحذف تلقائياً</div>
          </div>
        </div>
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
          <div style="font-size:11.5px;color:var(--t3)">
            <i class="fa fa-clock"></i> يعمل تلقائياً عند كل تسجيل دخول &nbsp;·&nbsp;
            <span style="color:var(--r1)">الفواتير المعلقة لا تُحذف أبداً</span>
          </div>
          <button class="btn btn-danger" onclick="manualCleanup()"><i class="fa fa-broom"></i>تنظيف يدوي الآن</button>
        </div>
      </div>
    </div>

    <!-- ═══ WAREHOUSES PAGE ═══ -->
    <div id="pg-warehouses-pg" style="display:none" class="page-in">
      <div class="pg-hd">
        <div><div class="pg-title"><i class="fa fa-warehouse" style="color:var(--gs2)"></i>إدارة المستودعات</div><div class="pg-sub" id="whs-sub">المستودعات النشطة</div></div>
        <div style="display:flex;gap:8px">
          <button class="btn btn-sec" onclick="addZone()"><i class="fa fa-map-location-dot" style="color:var(--a1)"></i>زون جديد</button>
          <button class="btn btn-primary" onclick="addWarehouse()"><i class="fa fa-plus"></i>مستودع جديد</button>
        </div>
      </div>

      <!-- إدارة الزونات -->
      <div class="card" style="margin-bottom:16px">
        <div class="card-hd" style="margin-bottom:10px">
          <div class="card-title"><i class="fa fa-map-location-dot" style="color:var(--a1)"></i>الزونات الجغرافية</div>
          <span style="font-size:11px;color:var(--t3)">اضغط تعديل لتغيير اسم أو لون الزون</span>
        </div>
        <div id="zones-manage-list" style="display:flex;gap:10px;flex-wrap:wrap"></div>
      </div>

      <div class="fbar">
        <div class="search-wrap"><input class="form-input" placeholder="🔍  بحث عن مستودع..." id="whs-q" oninput="renderWarehouses()"><button class="search-clear" onclick="document.getElementById('whs-q').value='';renderWarehouses()" title="مسح البحث"><i class="fa fa-times-circle"></i></button></div>
      </div>
      <div class="wh-cards" id="whs-cards"></div>
    </div>

    <!-- ═══ CONTRACTORS PAGE ═══ -->
    <div id="pg-contractors-pg" style="display:none" class="page-in">
      <div class="pg-hd">
        <div><div class="pg-title"><i class="fa fa-hard-hat" style="color:var(--o1)"></i>إدارة المقاولين</div><div class="pg-sub" id="contr-sub">المقاولون النشطون</div></div>
        <button class="btn btn-primary" onclick="addContractor()"><i class="fa fa-plus"></i>مقاول جديد</button>
      </div>
      <div class="fbar">
        <div class="search-wrap"><input class="form-input" placeholder="🔍  بحث عن مقاول..." id="contr-q" oninput="renderContractors()"><button class="search-clear" onclick="document.getElementById('contr-q').value='';renderContractors()" title="مسح البحث"><i class="fa fa-times-circle"></i></button></div>

      </div>
      <div class="contr-grid" id="contr-grid"></div>
    </div>

    <!-- ═══ CATEGORIES PAGE ═══ -->
    <div id="pg-categories-pg" style="display:none" class="page-in">
      <div class="pg-hd">
        <div><div class="pg-title"><i class="fa fa-layer-group" style="color:var(--a3)"></i>الفئات وحدود الإشعار</div><div class="pg-sub">تحديد حدود التنبيه لكل فئة من المواد</div></div>
        <button class="btn btn-green" onclick="saveCategoryLimits()"><i class="fa fa-save"></i>حفظ الحدود</button>
      </div>
      <div class="g2">
        <div class="card">
          <div class="card-hd"><div class="card-title"><i class="fa fa-sliders" style="color:var(--a3)"></i>ضبط حدود الفئات</div></div>
          <div id="cat-limits-list"></div>
        </div>
        <div class="card">
          <div class="card-hd"><div class="card-title"><i class="fa fa-gauge" style="color:var(--y1)"></i>مقياس المخزون الحالي</div></div>
          <div class="cat-meter" id="cat-meter"></div>
        </div>
      </div>
    </div>

  </div><!-- /content -->

  <!-- FOOTER -->
  <div class="copyright">
    <span>© 2026 جميع الحقوق محفوظة</span>
    <span style="color:var(--t4)">|</span>
    <span>أحمد سعيد عواجي — <span style="color:var(--a1)">مدير النظام</span></span>
    <span style="color:var(--t4)">|</span>
    <span>دائرة شرق منطقة جازان</span>
  </div>
</div><!-- /main -->

<!-- QUICK FEED FLOATING BUTTON -->
<button class="quick-feed-btn" onclick="go('cart')" title="صرف سريع">
  <div class="qfb-pulse"></div>
  <i class="fa fa-cart-shopping qfb-ico"></i>
  <span class="qfb-lbl">صرف</span>
</button>

</div><!-- /shell -->

<!-- ═══ MODALS ═══ -->
<!-- Search Modal -->
<div class="overlay" id="modal-search" onclick="if(event.target===this)closeModal('modal-search')">
  <div class="modal">
    <div class="modal-hd"><div class="modal-title"><i class="fa fa-magnifying-glass"></i>بحث سريع</div><button class="modal-close" onclick="closeModal('modal-search')">✕</button></div>
    <input class="form-input" id="search-q" placeholder="ابحث عن فاتورة، مادة، موجه..." oninput="renderSearchResults(this.value)" autofocus>
    <div id="search-results" style="margin-top:12px"></div>
  </div>
</div>
<!-- Notifications Modal -->
<div class="overlay" id="modal-notifs" onclick="if(event.target===this)closeModal('modal-notifs')">
  <div class="modal">
    <div class="modal-hd"><div class="modal-title"><i class="fa fa-bell"></i>الإشعارات</div><button class="modal-close" onclick="closeModal('modal-notifs')">✕</button></div>
    <div id="notifs-list"></div>
    <div style="margin-top:12px;text-align:center"><button class="btn btn-sec btn-sm" onclick="clearNotifs()"><i class="fa fa-check-double"></i>تعيين الكل كمقروء</button></div>
  </div>
</div>
<!-- Generic Form Modal -->
<div class="overlay" id="modal-form" onclick="if(event.target===this)closeModal('modal-form')">
  <div class="modal" id="modal-form-inner">
    <div class="modal-hd"><div class="modal-title" id="modal-form-title"></div><button class="modal-close" onclick="closeModal('modal-form')">✕</button></div>
    <div id="modal-form-body"></div>
    <div id="modal-form-actions" style="display:flex;gap:8px;margin-top:16px"></div>
  </div>
</div>
<!-- Confirm Modal -->
<div class="overlay" id="modal-confirm" onclick="if(event.target===this)closeModal('modal-confirm')">
  <div class="modal" style="max-width:380px">
    <div class="modal-hd"><div class="modal-title" id="confirm-title"></div><button class="modal-close" onclick="closeModal('modal-confirm')">✕</button></div>
    <div id="confirm-body" style="font-size:13.5px;color:var(--t2);line-height:1.7;margin-bottom:16px"></div>
    <div style="display:flex;gap:8px;justify-content:flex-end">
      <button class="btn btn-sec" onclick="closeModal('modal-confirm')">إلغاء</button>
      <button class="btn" id="confirm-ok-btn" onclick="confirmOK()">تأكيد</button>
    </div>
  </div>
</div>
<!-- Invoice Detail Modal -->
<div class="overlay" id="modal-inv" onclick="if(event.target===this)closeModal('modal-inv')">
  <div class="modal" style="max-width:560px">
    <div class="modal-hd"><div class="modal-title" id="inv-detail-title"></div><button class="modal-close" onclick="closeModal('modal-inv')">✕</button></div>
    <div id="inv-detail-body"></div>
  </div>
</div>

<div id="toasts"></div>





<script>
// ══ تعبئة قوائم المستودعات ديناميكياً ══
function getWhOptions(includeEmpty){
  var opts=includeEmpty?'<option value="">-- اختر --</option>':'';
  DB.warehouses.filter(function(w){return w.active;}).forEach(function(w){
    opts+='<option value="'+w.name+'">'+w.name+'</option>';
  });
  return opts;
}
function getWhOptionsAll(selected){
  var opts='<option value="">كل المستودعات</option>';
  DB.warehouses.filter(function(w){return w.active;}).forEach(function(w){
    opts+='<option value="'+w.name+'"'+(selected===w.name?' selected':'')+'>'+w.name+'</option>';
  });
  return opts;
}
function fillWhSelects(){
  var basic=getWhOptions(false);
  var withEmpty=getWhOptions(true);
  var allOpt=getWhOptionsAll('');
  // cart
  var cw=document.getElementById('cart-add-wh');if(cw)cw.innerHTML=basic;
  // feed
  var fw=document.getElementById('feed-wh');if(fw)fw.innerHTML=basic;
  // transfer
  var tf=document.getElementById('tr-from');if(tf)tf.innerHTML=basic;
  var tt=document.getElementById('tr-to');if(tt)tt.innerHTML=basic;
  // direct return
  var dr=document.getElementById('dr-wh');if(dr)dr.innerHTML=basic;
  // request return
  var rw=document.getElementById('ret-wh');if(rw)rw.innerHTML=withEmpty;
  // wardia transfer
  var wf=document.getElementById('wtr-from');if(wf)wf.innerHTML=withEmpty;
  var wto=document.getElementById('wtr-to');if(wto)wto.innerHTML=withEmpty;
  // ier form
  var iw=document.getElementById('ier-wh');if(iw)iw.innerHTML=basic;
  var iwr=document.getElementById('ier-wh-recv');if(iwr)iwr.innerHTML='<option value="">-- اختياري --</option>'+basic;
  var af=document.getElementById('appr-filter-wh');if(af)af.innerHTML=allOpt;
  // archive filter
  var arw=document.getElementById('inv-arc-wh');if(arw)arw.innerHTML=allOpt;
}
function toggleFeedSrcOther(){
  var src=getFeedSrc()||'مستودع السعودية للطاقة';
  var other=document.getElementById('feed-src-other');
  if(other)other.style.display=src==='أخرى'?'block':'none';
}
function getFeedSrc(){
  var src=document.getElementById('feed-src')?.value||'مستودع السعودية للطاقة';
  if(src==='أخرى'){
    return (document.getElementById('feed-src-other')?.value||'أخرى').trim();
  }
  return src;
}




// ══ سلال منفصلة لكل موظف ══


// ══ نموذج نقل مشرف الوردية في الطلبات ══
var wtrItems=[];
function wtrAutoFill(){
  var code=(document.getElementById('wtr-add-code')?.value||'').trim();
  var nameEl=document.getElementById('wtr-add-name');
  if(!nameEl)return;
  var item=DB.inventory.find(function(i){return i.code===code||i.name===code;});
  nameEl.value=item?item.name:'';
}
function wtrAddItem(){
  var code=(document.getElementById('wtr-add-code')?.value||'').trim();
  var qty=parseInt(document.getElementById('wtr-add-qty')?.value)||0;
  if(!code){toast('err','حقل مطلوب','ادخل كود المادة','fa-triangle-exclamation');return;}
  if(qty<1){toast('err','كمية غير صحيحة','الكمية يجب أن تكون أكبر من صفر','fa-triangle-exclamation');return;}
  var item=validateItemExists(code);
  if(!item)return;
  var ex=wtrItems.find(function(x){return x.code===item.code;});
  if(ex)ex.qty+=qty;
  else wtrItems.push({code:item.code,name:item.name,qty:qty});
  document.getElementById('wtr-add-code').value='';
  document.getElementById('wtr-add-name').value='';
  document.getElementById('wtr-add-qty').value=1;
  wtrRenderItems();
  toast('ok','أُضيفت',item.name+' x'+qty,'fa-box');
}
function wtrRenderItems(){
  var el=document.getElementById('wtr-items-list');if(!el)return;
  if(!wtrItems.length){
    el.innerHTML='<div style="text-align:center;color:var(--t3);font-size:12px;padding:8px 0">أضف مواد أدناه لطلب النقل</div>';
    return;
  }
  el.innerHTML=wtrItems.map(function(it,i){
    return '<div class="cart-item-row" style="margin-bottom:6px">'+
      '<div class="ci-info"><div class="ci-code">'+it.code+'</div><div class="ci-name">'+it.name+'</div></div>'+
      '<div class="qty-ctrl">'+
        '<div class="qbtn" onclick="wtrQty('+i+',-1)">-</div>'+
        '<div class="qval">'+it.qty+'</div>'+
        '<div class="qbtn" onclick="wtrQty('+i+',1)">+</div>'+
      '</div>'+
      '<div class="ci-del" onclick="wtrItems.splice('+i+',1);wtrRenderItems()"><i class="fa fa-trash"></i></div>'+
    '</div>';
  }).join('');
}
function wtrQty(i,d){wtrItems[i].qty=Math.max(1,wtrItems[i].qty+d);wtrRenderItems();}
function submitWardiaTransfer(){
  var from=document.getElementById('wtr-from')?.value;
  var to=document.getElementById('wtr-to')?.value;
  var reason=(document.getElementById('wtr-reason')?.value||'').trim();
  if(!from){toast('err','حقل مطلوب','اختر المستودع المصدر','fa-warehouse');return;}
  if(!to){toast('err','حقل مطلوب','اختر المستودع الهدف','fa-warehouse');return;}
  if(from===to){toast('err','خطأ','لا يمكن النقل من والى نفس المستودع','fa-ban');return;}
  if(!wtrItems.length){toast('err','لا توجد مواد','أضف مادة واحدة على الأقل','fa-box');return;}
  var reqNo=genInvNo('نقل');
  var items=wtrItems.map(function(it){return {code:it.code,name:it.name,qty:it.qty};});
  DB.requests.unshift({
    id:Date.now(),no:reqNo,type:'نقل',emp:currentUser.name,
    from:from,to:to,items:items,st:'معلق',d:today(),t:nowTime(),
    reason:reason||'طلب نقل من مشرف وردية'
  });
  addLog('نقل','طلب نقل '+reqNo+' ('+items.length+' أصناف) — '+from+' → '+to+' — بانتظار الاعتماد',from,{no:reqNo,from:from,to:to});
  wtrItems=[];wtrRenderItems();
  document.getElementById('wtr-from').value='';
  document.getElementById('wtr-to').value='';
  document.getElementById('wtr-reason').value='';
  updateBadges();renderMyRequests();
  toast('ok','✓ طلب نقل '+reqNo,'أُرسل للاعتماد — '+from+' → '+to,'fa-right-left');
}


function dashReject(no,id){
  if(currentUser?.role==='مشرف وردية'){toast('err','غير مصرح','ليس لديك صلاحية الرفض','fa-lock');return;}
  var a=DB.approvals.find(function(x){return x.id===id;});
  if(!a)return;
  showConfirm('<i class="fa fa-times" style="color:var(--r1)"></i> رفض '+no,
    'رفض فاتورة الصرف <strong>'+no+'</strong>؟<br>سيتم حفظها كمرفوضة.',
    'رفض','btn-danger',function(){
      a.st='مرفوض';a.approvedDate=today();a.approvedBy=currentUser.name;
      syncInvoiceStatus(no,'مرفوض');
      addLog('رفض','رفض فاتورة صرف '+no+' من لوحة التحكم',a.wh,{no:no});
      addNotif('warn','رُفضت فاتورة '+no,'تم رفض فاتورة الصرف من لوحة التحكم','fa-times',a.emp);
      updateBadges();
      renderDashboard();
      toast('ok','رُفضت '+no,'تم حفظها كمرفوضة','fa-times');
    });
}


// ══ طلب تعديل فاتورة ══
// ══ متغيرات طلب تعديل الفاتورة ══
// ══ متغيرات طلب تعديل الفاتورة ══
var ierItems=[];
var ierDeleted=[];
var ierCurrentInv=null;

function ierGoBack(){
  document.getElementById('ier-form-card').style.display='none';
  document.getElementById('ier-list-card').style.display='block';
  ierCurrentInv=null;ierItems=[];ierDeleted=[];
}

function renderIerList(){
  var q=(document.getElementById('ier-search')?.value||'').toLowerCase();
  var st=document.getElementById('ier-filter-st')?.value||'';
  var tp=document.getElementById('ier-filter-type')?.value||'';
  var el=document.getElementById('ier-list');if(!el)return;
  var isWardia=currentUser?.role==='مشرف وردية';
  var mine=DB.invoices.filter(function(i){
    if(i.emp!==currentUser.name)return false;
    // لا تعرض الملغية بطلب معتمد — لا يمكن تعديلها
    if(i.st==='ملغي'){
      var hasCancelReq=DB.requests.find(function(r){
        return (r.origInv===i.no||r.no===i.no)&&r.type==='الغاء'&&r.st==='معتمد';
      });
      if(hasCancelReq) return false;
    }
    if(isWardia) return i.type==='صرف'||i.type==='ارجاع'||i.type==='نقل';
    return i.type==='صرف'||i.type==='ارجاع';
  });
  if(q)mine=mine.filter(function(i){return i.no.toLowerCase().includes(q)||(i.cont&&i.cont.toLowerCase().includes(q));});
  if(st)mine=mine.filter(function(i){return i.st===st;});
  if(tp)mine=mine.filter(function(i){return i.type===tp;});
  if(!mine.length){el.innerHTML='<div class="empty-state" style="padding:16px"><i class="fa fa-file-circle-xmark"></i><p>لا توجد فواتير</p></div>';return;}
  var typeMap={صرف:{i:'fa-file-invoice',c:'var(--g1)',b:'rgba(16,185,129,.1)'},ارجاع:{i:'fa-rotate-left',c:'var(--o1)',b:'rgba(249,115,22,.1)'},نقل:{i:'fa-right-left',c:'var(--a1)',b:'rgba(0,212,255,.1)'}};
  el.innerHTML=mine.map(function(inv){
    var ti=typeMap[inv.type]||{i:'fa-file',c:'var(--t2)',b:'rgba(255,255,255,.05)'};
    var sc=inv.st==='معتمد'?'var(--g1)':inv.st==='معلق'?'var(--y1)':'var(--r1)';
    var isMoj=currentUser?.role==='موجه بلاغات';
    var isWardiaApproved=currentUser?.role==='مشرف وردية'&&(inv.st==='معتمد'||inv.st==='مرفوض'||inv.st==='ملغي');
    var canEdit=!isMoj&&!isWardiaApproved;
    var clickFn=canEdit?'onclick="loadIerForm(\''+inv.no+'\')"':'onclick="toast(\'warn\',\'غير مسموح\',\'لا يمكنك تعديل هذه الفاتورة\',\'fa-lock\')"';
    var lockIcon=canEdit?'':'<i class="fa fa-lock" style="color:var(--t3);font-size:11px;margin-right:4px"></i>';
    return '<div style="display:flex;align-items:center;gap:12px;padding:12px 14px;border-bottom:1px solid var(--b1);cursor:'+(canEdit?'pointer':'not-allowed')+';opacity:'+(canEdit?'1':'.7')+';transition:background .15s" onmouseenter="this.style.background=\'rgba(255,200,0,.04)\'" onmouseleave="this.style.background=\'\'" '+clickFn+'>'+
      '<div style="width:40px;height:40px;border-radius:10px;background:'+ti.b+';display:flex;align-items:center;justify-content:center;flex-shrink:0"><i class="fa '+ti.i+'" style="color:'+ti.c+'"></i></div>'+
      '<div style="flex:1;min-width:0">'+
        '<div style="display:flex;align-items:center;gap:8px;margin-bottom:3px">'+
          '<span class="mono" style="font-size:13px;font-weight:800;color:var(--a1)">'+inv.no+'</span>'+
          '<span style="font-size:10px;font-weight:700;color:'+ti.c+';background:'+ti.b+';padding:2px 8px;border-radius:20px">'+inv.type+'</span>'+
          lockIcon+
        '</div>'+
        '<div style="font-size:12px;color:var(--t2)">'+(inv.cont&&inv.cont!=='—'?'<i class="fa fa-hard-hat" style="color:var(--t3);margin-left:4px"></i>'+inv.cont+' &nbsp;':'')+'<i class="fa fa-warehouse" style="color:var(--t3);margin-left:4px"></i>'+inv.wh+'</div>'+
        '<div style="font-size:10px;color:var(--t3);margin-top:2px">'+inv.d+(inv.boq?' &nbsp;·&nbsp; BOQ: '+inv.boq:'')+'</div>'+
      '</div>'+
      '<div style="text-align:center;flex-shrink:0"><div style="font-size:11px;font-weight:700;color:'+sc+'">'+inv.st+'</div><div style="font-size:10px;color:var(--t3);margin-top:2px">'+inv.items.length+' أصناف</div></div>'+
    '</div>';
  }).join('');
}

function ierTypeBadge(type){
  var m={صرف:{c:'var(--g1)',b:'rgba(16,185,129,.12)',i:'fa-file-invoice'},ارجاع:{c:'var(--o1)',b:'rgba(249,115,22,.12)',i:'fa-rotate-left'},نقل:{c:'var(--a1)',b:'rgba(0,212,255,.12)',i:'fa-right-left'}};
  var t=m[type]||{c:'var(--t2)',b:'rgba(255,255,255,.06)',i:'fa-file'};
  return '<span style="display:inline-flex;align-items:center;gap:6px;background:'+t.b+';border:1px solid '+t.c+'33;border-radius:8px;padding:4px 12px;font-size:11.5px;font-weight:700;color:'+t.c+'"><i class="fa '+t.i+'"></i>'+type+'</span>';
}

function ierBuildFields(inv){
  var whOpts=getWhOptions(false);
  var whEmptyOpts='<option value="">-- اختر --</option>'+whOpts;
  var notesField='<textarea class="form-input" id="ier-notes" rows="2" placeholder="وصف البلاغ...">'+(inv.notes||'')+'</textarea>';
  var whSend='<select class="form-select" id="ier-wh">'+whOpts+'</select>';
  var whRecv='<select class="form-select" id="ier-wh-recv">'+whEmptyOpts+'</select>';
  var contrField='<input class="form-input" id="ier-cont" list="contr-datalist" value="'+(inv.cont&&inv.cont!=='—'?inv.cont:'')+'" placeholder="اسم المقاول...">';
  var boqField='<input class="form-input" id="ier-boq" value="'+(inv.boq||'')+'" placeholder="رقم BOQ...">';
  var html='';
  if(inv.type==='صرف'){
    html='<div class="form-row c2">'+
      '<div class="form-group"><label class="form-label"><i class="fa fa-warehouse" style="color:var(--r1)"></i> المستودع المُسلِّم <span style="color:var(--r1)">*</span></label>'+whSend+'</div>'+
      '<div class="form-group"><label class="form-label"><i class="fa fa-hard-hat" style="color:var(--o1)"></i> المقاول المستلم <span style="color:var(--r1)">*</span></label>'+contrField+'</div>'+
      '<div class="form-group"><label class="form-label"><i class="fa fa-clipboard-list" style="color:var(--a3)"></i> رقم BOQ</label>'+boqField+'</div>'+
      '<div class="form-group" style="grid-column:span 2"><label class="form-label"><i class="fa fa-note-sticky" style="color:var(--t3)"></i> وصف البلاغ <span style="color:var(--r1)">*</span></label>'+notesField+'</div>'+
    '</div>';
  } else if(inv.type==='ارجاع'){
    html='<div class="form-row c2">'+
      '<div class="form-group"><label class="form-label"><i class="fa fa-warehouse" style="color:var(--g1)"></i> المستودع المستلم <span style="color:var(--r1)">*</span></label>'+whSend+'</div>'+
      '<div class="form-group"><label class="form-label"><i class="fa fa-hard-hat" style="color:var(--o1)"></i> المقاول المُسلِّم <span style="color:var(--r1)">*</span></label>'+contrField+'</div>'+
      '<div class="form-group" style="grid-column:span 2"><label class="form-label"><i class="fa fa-note-sticky" style="color:var(--t3)"></i> سبب الارجاع</label>'+notesField+'</div>'+
    '</div>';
  } else if(inv.type==='نقل'){
    html='<div class="form-row c2">'+
      '<div class="form-group"><label class="form-label"><i class="fa fa-warehouse" style="color:var(--r1)"></i> المستودع المصدر <span style="color:var(--r1)">*</span></label>'+whSend+'</div>'+
      '<div class="form-group"><label class="form-label"><i class="fa fa-warehouse" style="color:var(--g1)"></i> المستودع الهدف <span style="color:var(--r1)">*</span></label>'+whRecv+'</div>'+
      '<div class="form-group" style="grid-column:span 2"><label class="form-label"><i class="fa fa-note-sticky" style="color:var(--t3)"></i> سبب النقل</label>'+notesField+'</div>'+
    '</div>';
  }
  document.getElementById('ier-fields-dynamic').innerHTML=html;
  setTimeout(function(){
    var wEl=document.getElementById('ier-wh');if(wEl)wEl.value=inv.wh||'';
    var wrEl=document.getElementById('ier-wh-recv');if(wrEl)wrEl.value=inv.whRecv||'';
  },10);
}

function loadIerForm(no){
  var inv=DB.invoices.find(function(i){return i.no===no;});
  if(!inv){toast('err','غير موجودة','الفاتورة غير موجودة','fa-ban');return;}
  // موجه البلاغات لا يمكنه تعديل أي فاتورة
  if(currentUser?.role==='موجه بلاغات'){
    toast('warn','غير مسموح','موجه البلاغات لا يملك صلاحية تعديل الفواتير','fa-lock');return;
  }
  // مشرف الوردية لا يمكنه تعديل فاتورة نقل معتمدة أو مرفوضة أو ملغية
  if(currentUser?.role==='مشرف وردية' && inv.type==='نقل'){
    if(inv.st==='معتمد'||inv.st==='مرفوض'||inv.st==='ملغي'){
      toast('warn','غير مسموح','لا يمكن تعديل فاتورة نقل بحالة «'+inv.st+'»','fa-lock');return;
    }
  }
  fillWhSelects();
  ierCurrentInv=inv;
  ierItems=inv.items.map(function(it){return {code:it.code,name:it.name,qty:it.qty,origQty:it.qty};});
  ierDeleted=[];
  document.getElementById('ier-inv-no').textContent=no;
  document.getElementById('ier-type-badge').innerHTML=ierTypeBadge(inv.type);
  var prevDiv=document.getElementById('ier-prev-approved');
  if(prevDiv){
    if(inv.st==='معتمد') prevDiv.innerHTML='<i class="fa fa-triangle-exclamation"></i> هذه الفاتورة كانت معتمدة — سيُعاد إرسالها للاعتماد بعد التعديل',prevDiv.style.display='block';
    else if(inv.st==='ملغي') prevDiv.innerHTML='<i class="fa fa-triangle-exclamation" style="color:var(--r1)"></i> هذه الفاتورة ملغية — طلب الإلغاء لم يُعتمد بعد، يمكنك التعديل',prevDiv.style.display='block',prevDiv.style.background='rgba(239,68,68,.08)',prevDiv.style.borderColor='rgba(239,68,68,.3)',prevDiv.style.color='var(--r1)';
    else prevDiv.style.display='none';
  }
  ierBuildFields(inv);
  document.getElementById('ier-list-card').style.display='none';
  document.getElementById('ier-form-card').style.display='block';
  ierRenderItems();
  document.getElementById('ier-form-card').scrollIntoView({behavior:'smooth'});
}

function ierRenderItems(){
  var el=document.getElementById('ier-items-list');if(!el)return;
  if(!ierItems.length){
    el.innerHTML='<div style="text-align:center;color:var(--t3);font-size:12px;padding:12px">لا توجد مواد — أضف من الأسفل</div>';
    return;
  }
  el.innerHTML=ierItems.map(function(it,i){
    var changed=it.qty!==it.origQty;
    return '<div style="display:flex;align-items:center;gap:10px;padding:9px 12px;border-bottom:1px solid var(--b1);background:'+(changed?'rgba(255,184,32,.04)':'')+'" >'+
      '<div style="width:38px;height:38px;border-radius:8px;background:rgba(0,212,255,.08);display:flex;align-items:center;justify-content:center;flex-shrink:0"><i class="fa fa-box" style="color:var(--a1);font-size:13px"></i></div>'+
      '<div style="flex:1;min-width:0">'+
        '<div style="font-size:12px;font-weight:700;color:var(--t1)">'+it.name+'</div>'+
        '<div style="font-size:10px;color:var(--t3);font-family:\'JetBrains Mono\',monospace">'+it.code+(changed?'  <span style="color:var(--y1)">تعديل: '+it.origQty+' → '+it.qty+'</span>':'')+'</div>'+
      '</div>'+
      '<div style="display:flex;align-items:center;gap:6px">'+
        '<div style="display:flex;align-items:center;background:var(--bg2);border:1px solid var(--b1);border-radius:8px;overflow:hidden">'+
          '<button style="background:none;border:none;color:var(--t2);cursor:pointer;padding:5px 10px;font-size:14px" onclick="ierQty('+i+',-1)">−</button>'+
          '<span style="font-family:\'JetBrains Mono\',monospace;font-weight:700;color:var(--t1);min-width:30px;text-align:center;font-size:14px">'+it.qty+'</span>'+
          '<button style="background:none;border:none;color:var(--t2);cursor:pointer;padding:5px 10px;font-size:14px" onclick="ierQty('+i+',1)">+</button>'+
        '</div>'+
        '<button style="background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.2);color:#f87171;border-radius:7px;padding:5px 9px;cursor:pointer;font-size:12px" onclick="ierRemoveItem('+i+')" title="حذف المادة"><i class="fa fa-trash"></i></button>'+
      '</div>'+
    '</div>';
  }).join('');
}

function ierQty(i,d){
  ierItems[i].qty=Math.max(1,ierItems[i].qty+d);
  ierRenderItems();
}

function ierRemoveItem(i){
  var removed=ierItems.splice(i,1)[0];
  ierDeleted.push({code:removed.code,name:removed.name,qty:removed.origQty});
  ierRenderItems();
  toast('warn','حُذفت: '+removed.name,'ستُعاد كميتها للمستودع بعد الاعتماد','fa-trash');
}

function ierAutoFill(){
  var code=(document.getElementById('ier-add-code')?.value||'').trim();
  var nameEl=document.getElementById('ier-add-name');if(!nameEl)return;
  var item=DB.inventory.find(function(i){return i.code===code;});
  nameEl.value=item?item.name:'';
}

function ierAddItem(){
  var code=(document.getElementById('ier-add-code')?.value||'').trim();
  var qty=parseInt(document.getElementById('ier-add-qty')?.value)||0;
  if(!code){toast('err','حقل مطلوب','ادخل كود المادة','fa-barcode');return;}
  if(qty<1){toast('err','كمية غير صحيحة','الكمية يجب أن تكون 1 على الأقل','fa-triangle-exclamation');return;}
  var item=validateItemExists(code);
  if(!item)return;
  var ex=ierItems.find(function(x){return x.code===item.code;});
  if(ex){ex.qty+=qty;}
  else{ierItems.push({code:item.code,name:item.name,qty:qty,origQty:0});}
  document.getElementById('ier-add-code').value='';
  document.getElementById('ier-add-name').value='';
  document.getElementById('ier-add-qty').value=1;
  ierRenderItems();
  toast('ok','أُضيفت',item.name+' x'+qty,'fa-box');
}

function submitIerRequest(){
  var no=(document.getElementById('ier-inv-no')?.textContent||'').trim();
  if(!no||!ierCurrentInv){toast('err','خطأ','اختر فاتورة من القائمة','fa-ban');return;}
  var inv=ierCurrentInv;
  // منع تعديل الملغية المعتمدة
  if(inv.st==='ملغي'){
    var hasCancelReq=DB.requests.find(function(r){
      return (r.origInv===no||r.no===no)&&r.type==='الغاء'&&r.st==='معتمد';
    });
    if(hasCancelReq){toast('err','غير مسموح','هذه الفاتورة أُلغيت بطلب معتمد — لا يمكن تعديلها','fa-ban');return;}
  }
  if(!ierItems.length){toast('err','لا توجد مواد','أضف مادة واحدة على الأقل','fa-box');return;}
  // قراءة القيم
  var cont=(document.getElementById('ier-cont')?.value||inv.cont||'').trim();
  var boq=(document.getElementById('ier-boq')?.value||inv.boq||'').trim();
  var notes=(document.getElementById('ier-notes')?.value||inv.notes||'').trim();
  var wh=document.getElementById('ier-wh')?.value||inv.wh;
  var whRecv=document.getElementById('ier-wh-recv')?.value||inv.whRecv||'';
  // تحقق حسب النوع
  if(inv.type==='صرف'){if(!cont){toast('err','حقل مطلوب','ادخل اسم المقاول المستلم','fa-triangle-exclamation');return;}}
  if(inv.type==='ارجاع'){if(!cont){toast('err','حقل مطلوب','ادخل اسم المقاول المُسلِّم','fa-triangle-exclamation');return;}}
  if(inv.type==='نقل'){if(!whRecv||whRecv===wh){toast('err','خطأ','اختر مستودعَيْن مختلفين','fa-ban');return;}}

  var wasApproved=inv.st==='معتمد';
  // ══ حفظ القيم القديمة ══
  var oldValues={
    cont:inv.cont,boq:inv.boq,notes:inv.notes,
    wh:inv.wh,whRecv:inv.whRecv||'',
    items:JSON.parse(JSON.stringify(inv.items))
  };

  // ══ تحديث الفاتورة نفسها فوراً ══
  inv.cont  = cont;
  inv.boq   = boq;
  inv.notes = notes;
  inv.wh    = wh;
  if(whRecv) inv.whRecv = whRecv;
  inv.items = JSON.parse(JSON.stringify(ierItems));

  // ══ تحديث DB.approvals فوراً (ما يراه الموجه ومشرف الوردية والمدير) ══
  DB.approvals.forEach(function(a){
    if(a.no===no){
      a.cont     = cont;
      a.wh       = wh;
      a.boq      = boq;
      a.notes    = notes;
      a.items    = JSON.parse(JSON.stringify(ierItems));
      a.itemsStr = ierItems.map(function(i){return i.name+' ×'+i.qty;}).join(' + ');
      if(whRecv) a.whRecv = whRecv;
      // إعادة الاعتماد لمعلق إذا كان معتمداً
      if(wasApproved) a.st = 'معلق';
    }
  });

  // ══ تحديث أي طلب سابق بنفس رقم الفاتورة في DB.requests ══
  DB.requests.forEach(function(r){
    if((r.no===no||r.origInv===no)&&r.type!=='تعديل'){
      r.cont  = cont;
      r.wh    = wh;
      r.items = JSON.parse(JSON.stringify(ierItems));
    }
  });

  // ══ حذف أي طلب تعديل معلق سابق لنفس الفاتورة ══
  DB.requests = DB.requests.filter(function(r){
    return !(r.origInv===no && r.type==='تعديل' && r.st==='معلق');
  });

  // ══ إضافة طلب التعديل الجديد ══
  DB.requests.unshift({
    id:Date.now(),no:no,type:'تعديل',emp:currentUser.name,
    origInv:no,invType:inv.type,wasApproved:wasApproved,
    newItems:JSON.parse(JSON.stringify(ierItems)),
    deletedItems:JSON.parse(JSON.stringify(ierDeleted)),
    changes:{cont:cont,boq:boq,notes:notes,wh:wh,whRecv:whRecv},
    oldValues:oldValues,
    st:'معلق',d:today(),t:nowTime(),wh:wh
  });

  // ══ مزامنة الحالة في كل النظام ══
  syncInvoiceStatus(no,'معلق');

  addLog('تعديل','طلب تعديل ('+inv.type+') '+no+' — '+ierItems.length+' أصناف'+(ierDeleted.length?' — حذف '+ierDeleted.length:''),wh,{no:no,origInv:no,cont:cont,wh:wh});
  if(wasApproved) addNotif('warn','فاتورة '+no+' أُعيدت للمراجعة',currentUser.name+' طلب تعديل فاتورة '+inv.type+' معتمدة','fa-rotate-left',null);
  else addNotif('info','طلب تعديل '+no,currentUser.name+' عدّل فاتورة '+inv.type+' — '+cont,'fa-pen',null);

  ierCurrentInv=null;ierItems=[];ierDeleted=[];
  document.getElementById('ier-form-card').style.display='none';
  document.getElementById('ier-list-card').style.display='block';
  renderIerList();
  toast('ok','✓ طلب التعديل '+no,'الفاتورة والطلبات مُحدَّثة فوراً'+(wasApproved?' — أُعيدت لمعلق':''),'fa-paper-plane');
}



var _userBaskets={};

function saveUserBaskets(){
  // لا نحفظ - كل مستخدم يبدأ بسلة فارغة دائماً
}

function loadUserBaskets(){
  // دائماً سلة فارغة عند الدخول
  cart=[];trItems=[];feedItems=[];drItems=[];wtrItems=[];
}

function clearAllBaskets(){
  cart=[];trItems=[];feedItems=[];drItems=[];wtrItems=[];
}

// ══════════════════════ DATABASE ══════════════════════
const DB = {
  users: [
    {id:1,phone:'0501104283',pass:'AaSs123456+++**',name:'أحمد سعيد عواجي',role:'مدير النظام',photo:'',av:'أح',color:'linear-gradient(135deg,#3b82f6,#1d4ed8)',dept:'إدارة',active:true},
    {id:2,phone:'0507654321',pass:'mojtahed1',name:'محمد صميلي',role:'موجه بلاغات',photo:'',av:'مح',color:'linear-gradient(135deg,#10b981,#059669)',dept:'موجهون',active:true},
    {id:3,phone:'0508765432',pass:'wardia2',name:'م. علي عريبي',role:'مشرف وردية',photo:'',av:'سع',color:'linear-gradient(135deg,#f59e0b,#d97706)',dept:'مشرفون',active:true},
    {id:4,phone:'0509876543',pass:'ameen123',name:'ماجد رضوان',role:'أمين مستودع',photo:'',av:'خا',color:'linear-gradient(135deg,#8b5cf6,#7c3aed)',dept:'أمناء مستودعات',active:true},
    {id:5,phone:'0501234567',pass:'ameen456',name:'يزيد عطيف',role:'أمين مستودع',photo:'',av:'عب',color:'linear-gradient(135deg,#ec4899,#be185d)',dept:'أمناء مستودعات',active:true},
    {id:6,phone:'0502345678',pass:'ameen789',name:'سامي مجممي',role:'أمين مستودع',av:'فه',color:'linear-gradient(135deg,#14b8a6,#0d9488)',dept:'أمناء مستودعات',active:false},
  ],
  contacts: [
    {id:1,name:'أحمد سعيد عواجي',role:'مدير النظام',tel:'0506543210',av:'أح',color:'linear-gradient(135deg,#3b82f6,#1d4ed8)',dept:'إدارة'},
    {id:2,name:'محمد صميلي',role:'موجه بلاغات',tel:'0507654321',av:'مح',color:'linear-gradient(135deg,#10b981,#059669)',dept:'موجهون'},
    {id:3,name:'م. علي عريبي',role:'موجه بلاغات',tel:'0508765432',av:'سع',color:'linear-gradient(135deg,#f59e0b,#d97706)',dept:'موجهون'},
    {id:4,name:'ماجد رضوان',role:'أمين مستودع اسناد',tel:'0509876543',av:'خا',color:'linear-gradient(135deg,#8b5cf6,#7c3aed)',dept:'أمناء مستودعات'},
    {id:5,name:'يزيد عطيف',role:'أمين مستودع رايكو صبيا',tel:'0501234567',av:'عب',color:'linear-gradient(135deg,#ec4899,#be185d)',dept:'أمناء مستودعات'},
    {id:6,name:'سامي مجممي',role:'أمين مستودع هيف بني مالك',tel:'0502345678',av:'فه',color:'linear-gradient(135deg,#14b8a6,#0d9488)',dept:'أمناء مستودعات'},
    ],
  inventory: [
    {code:'908514012',name:'محول 100KVA',cat:'محولات',asnad:10,raiko:4,manatiq:2,min:3},
    {code:'908514023',name:'محول 250KVA',cat:'محولات',asnad:6,raiko:3,manatiq:1,min:2},
    {code:'908514034',name:'محول 500KVA',cat:'محولات',asnad:3,raiko:1,manatiq:0,min:1},
    {code:'912300011',name:'كابل 3x185 مم',cat:'كابلات',asnad:220,raiko:85,manatiq:30,min:50},
    {code:'912300022',name:'كابل 3x95 مم',cat:'كابلات',asnad:180,raiko:70,manatiq:25,min:40},
    {code:'912300033',name:'كابل 3x50 مم',cat:'كابلات',asnad:95,raiko:40,manatiq:12,min:20},
    {code:'915100001',name:'قاطع 630A',cat:'قواطع',asnad:8,raiko:5,manatiq:2,min:2},
    {code:'915100002',name:'قاطع 400A',cat:'قواطع',asnad:12,raiko:7,manatiq:3,min:3},
    {code:'920200001',name:'عداد احادي',cat:'عدادات',asnad:45,raiko:22,manatiq:8,min:10},
    {code:'920200002',name:'عداد ثلاثي',cat:'عدادات',asnad:30,raiko:15,manatiq:5,min:8},
    {code:'930100001',name:'صندوق توزيع 8 دائرة',cat:'صناديق',asnad:14,raiko:8,manatiq:3,min:3},
    {code:'930100002',name:'صندوق توزيع 16 دائرة',cat:'صناديق',asnad:9,raiko:4,manatiq:1,min:2},
    {code:'940500001',name:'برج انارة 9م',cat:'انارة',asnad:20,raiko:10,manatiq:4,min:4},
    {code:'940500002',name:'لمبة LED 150W',cat:'انارة',asnad:60,raiko:30,manatiq:8,min:15},
  ],
  invoices: [
    {no:'G48',type:'صرف',wh:'رايكو صبيا',emp:'أحمد سعيد عواجي',cont:'بن دلامة',st:'معتمد',d:'2026-06-04',items:[{code:'908514012',name:'محول 100KVA',qty:2}],notes:'',boq:''},
    {no:'R12',type:'ارجاع',wh:'اسناد',emp:'محمد صميلي',cont:'اعسار السعودية',st:'معلق',d:'2026-06-04',items:[{code:'908514012',name:'محول 100KVA',qty:3}],notes:'مواد زائدة',boq:''},
    {no:'G47',type:'صرف',wh:'اسناد',emp:'م. علي عريبي',cont:'قوى البيئة',st:'معتمد',d:'2026-06-03',items:[{code:'912300011',name:'كابل 3x185',qty:50}],notes:'',boq:'BOQ-2026-041'},
    {no:'T05',type:'نقل',wh:'هيف بني مالك',emp:'أحمد سعيد عواجي',cont:'—',st:'معتمد',d:'2026-06-03',items:[{code:'908514012',name:'محول 100KVA',qty:2}],notes:'نقل طارئ',boq:''},
    {no:'G46',type:'صرف',wh:'رايكو صبيا',emp:'محمد صميلي',cont:'بن دلامة',st:'مرفوض',d:'2026-06-02',items:[{code:'915100001',name:'قاطع 630A',qty:3}],notes:'رصيد غير كاف',boq:''},
    {no:'CR08',type:'الغاء',wh:'اسناد',emp:'م. علي عريبي',cont:'اعسار السعودية',st:'معلق',d:'2026-06-01',items:[{code:'920200001',name:'عداد احادي',qty:5}],notes:'خطأ في البيانات',boq:''},
    {no:'G45',type:'صرف',wh:'اسناد',emp:'أحمد سعيد عواجي',cont:'شبكات النجم',st:'معتمد',d:'2026-05-31',items:[{code:'940500001',name:'برج انارة',qty:4}],notes:'',boq:'BOQ-2026-038'},
    {no:'R11',type:'ارجاع',wh:'هيف بني مالك',emp:'محمد صميلي',cont:'بن دلامة',st:'معتمد',d:'2026-05-30',items:[{code:'912300022',name:'كابل 3x95',qty:20}],notes:'',boq:''},
    {no:'T04',type:'نقل',wh:'رايكو صبيا',emp:'أحمد سعيد عواجي',cont:'—',st:'معتمد',d:'2026-05-29',items:[{code:'930100001',name:'صندوق توزيع',qty:3}],notes:'',boq:''},
    {no:'G44',type:'صرف',wh:'اسناد',emp:'م. علي عريبي',cont:'اعسار السعودية',st:'معتمد',d:'2026-05-28',items:[{code:'920200002',name:'عداد ثلاثي',qty:8}],notes:'',boq:''},
  ],
  requests: [
    {id:1,no:'R12',type:'ارجاع',emp:'محمد صميلي',wh:'اسناد',cont:'اعسار السعودية',origInv:'R12',retItems:[{code:'908514012',name:'محول 100KVA',qty:3}],reason:'مواد زائدة عن الحاجة',d:'2026-06-04',time:'09:47',st:'معلق'},
    {id:2,no:'R11B',type:'ارجاع',emp:'م. علي عريبي',wh:'رايكو صبيا',cont:'قوى البيئة',origInv:'R11B',retItems:[{code:'908585001',name:'كابل 3x95مم',qty:20}],reason:'طلب المقاول اعادتها',d:'2026-06-03',time:'14:22',st:'معلق'},
    {id:3,no:'CR08',type:'الغاء',emp:'م. علي عريبي',wh:'اسناد',cont:'اعسار السعودية',origInv:'CR08',retItems:[],reason:'خطأ في الكميات المدخلة',d:'2026-06-01',time:'11:05',st:'معلق'},
  ],
  approvals: [
    {id:1,no:'G49',emp:'محمد صميلي',wh:'اسناد',cont:'بن دلامة',items:[{code:'915100001',name:'قاطع 630A',qty:2},{code:'930100001',name:'كابل 185مم',qty:5}],itemsStr:'قاطع 630A x2 + كابل 185مم x5',d:'2026-06-05',time:'08:30',st:'معلق'},
    {id:2,no:'G50',emp:'م. علي عريبي',wh:'رايكو صبيا',cont:'فوى البلاة',items:[{code:'920200001',name:'عداد احادي',qty:3}],itemsStr:'عداد احادي x3',d:'2026-06-03',time:'14:20',st:'معلق'},
  ],
  boq: [
    {no:'BOQ-2026-041',desc:'إصلاح خط 33KV منطقة صبيا',wh:'رايكو صبيا',inv:['G48','G47'],st:'جاري',d:'2026-06-01',tech:'أحمد سعيد عواجي'},
    {no:'BOQ-2026-038',desc:'توصيل محول جديد حي الورود',wh:'اسناد',inv:['G45','G44'],st:'مغلق',d:'2026-05-25',tech:'م. علي عريبي'},
    {no:'BOQ-2026-035',desc:'صيانة شبكة هيف بني مالك الريفية',wh:'هيف بني مالك',inv:['G43'],st:'مفتوح',d:'2026-05-20',tech:'محمد صميلي'},
    {no:'BOQ-2026-033',desc:'توسعة شبكة الضغط المنخفض',wh:'اسناد',inv:['G42','G41'],st:'جاري',d:'2026-05-15',tech:'أحمد سعيد عواجي'},
  ],
  logs: [
    {type:'صرف',act:'اصدار فاتورة G48',emp:'أحمد سعيد عواجي',wh:'رايكو صبيا',t:'11:23',d:'2026-06-04',c:'var(--g1)',i:'fa-file-invoice'},
    {type:'ارجاع',act:'طلب ارجاع R12',emp:'محمد صميلي',wh:'اسناد',t:'09:47',d:'2026-06-04',c:'var(--o1)',i:'fa-rotate-left'},
    {type:'صرف',act:'اعتماد فاتورة G47',emp:'أحمد سعيد عواجي',wh:'اسناد',t:'08:15',d:'2026-06-03',c:'var(--a1)',i:'fa-signature'},
    {type:'تغذية',act:'تغذية 100 وحدة كابل 3x185',emp:'أحمد سعيد عواجي',wh:'رايكو صبيا',t:'07:30',d:'2026-06-03',c:'#009245',i:'fa-cubes'},
    {type:'صرف',act:'رفض فاتورة G46',emp:'أحمد سعيد عواجي',wh:'رايكو صبيا',t:'06:18',d:'2026-06-02',c:'var(--r1)',i:'fa-xmark'},
    {type:'نقل',act:'نقل T05 من اسناد الى هيف بني مالك',emp:'أحمد سعيد عواجي',wh:'هيف بني مالك',t:'15:40',d:'2026-06-03',c:'var(--a3)',i:'fa-right-left'},
    {type:'صرف',act:'اصدار فاتورة G45',emp:'أحمد سعيد عواجي',wh:'اسناد',t:'11:00',d:'2026-05-31',c:'var(--g1)',i:'fa-file-invoice'},
    {type:'ارجاع',act:'اعتماد طلب ارجاع R11',emp:'أحمد سعيد عواجي',wh:'هيف بني مالك',t:'09:00',d:'2026-05-30',c:'var(--g1)',i:'fa-check'},
    {type:'نظام',act:'نسخة احتياطية تلقائية',emp:'النظام',wh:'—',t:'04:00',d:'2026-06-04',c:'var(--t3)',i:'fa-hard-drive'},
    {type:'تعديل',act:'تعديل فاتورة G44',emp:'أحمد سعيد عواجي',wh:'اسناد',t:'13:30',d:'2026-05-28',c:'var(--y1)',i:'fa-pen'},
  ],
  notifications: [
    {id:1,type:'warn',title:'طلب ارجاع جديد',msg:'محمد صميلي — اسناد — 3 محولات 100KVA',i:'fa-rotate-left',read:false,time:'09:47'},
    {id:2,type:'err',title:'تنبيه مخزون منخفض',msg:'محول 500KVA وصل للحد الادنى في هيف بني مالك',i:'fa-triangle-exclamation',read:false,time:'08:00'},
    {id:3,type:'ok',title:'مزامنة Supabase ناجحة',msg:'تمت مزامنة 24 عملية جديدة بنجاح',i:'fa-database',read:true,time:'07:30'},
    {id:4,type:'info',title:'فاتورة جديدة بانتظار الاعتماد',msg:'G49 — محمد صميلي — اسناد',i:'fa-signature',read:false,time:'08:30'},
  ],
  settings:{autoNotif:true,supabaseSync:true,autoBackup:true,logAll:true,autoApproveFeed:false,maintenance:false,twoFA:true,ipRestrict:false,sessionTimeout:true},
  warehouses: [
    {id:1,name:'اسناد',key:'asnad',location:'جازان — اسناد',manager:'ماجد رضوان',phone:'0501111111',active:true,color:'#0066ff',zone:'south'},
    {id:2,name:'رايكو صبيا',key:'raiko',location:'صبيا — رايكو',manager:'يزيد عطيف',phone:'0502222222',active:true,color:'#10b981',zone:'north'},
    {id:3,name:'هيف بني مالك',key:'manatiq',location:'مناطق متفرقة',manager:'سامي مجممي',phone:'0503333333',active:true,color:'#f59e0b',zone:'east'},
  ],
  zones: [
    {id:'south',name:'المستودعات الجنوبية',icon:'fa-arrow-down',color:'#10b981',bg:'rgba(16,185,129,.1)',border:'rgba(16,185,129,.3)'},
    {id:'north',name:'المستودعات الشمالية',icon:'fa-arrow-up',color:'#3b82f6',bg:'rgba(59,130,246,.1)',border:'rgba(59,130,246,.3)'},
    {id:'east', name:'المستودعات الشرقية',icon:'fa-arrow-right',color:'#f59e0b',bg:'rgba(245,158,11,.1)',border:'rgba(245,158,11,.3)'},
  ],
  contractors: [
    {id:1,name:'شركة بن دلامة',contact:'0501112223',active:true},
    {id:2,name:'اعسار السعودية',contact:'0502223334',active:true},
    {id:3,name:'قوى البيئة',contact:'0503334445',active:true},
    {id:4,name:'شبكات النجم',contact:'0504445556',active:true},
    {id:5,name:'الراشد للمقاولات',contact:'0505556667',active:false},
  ],
  categories: [
    {id:1,name:'محولات',icon:'fa-bolt',color:'#f59e0b',criticalLimit:3,warningLimit:8,safeLimit:15},
    {id:2,name:'كابلات',icon:'fa-cable-car',color:'#3b82f6',criticalLimit:30,warningLimit:80,safeLimit:200},
    {id:3,name:'قواطع',icon:'fa-toggle-on',color:'#8b5cf6',criticalLimit:3,warningLimit:8,safeLimit:20},
    {id:4,name:'عدادات',icon:'fa-gauge',color:'#10b981',criticalLimit:5,warningLimit:15,safeLimit:40},
    {id:5,name:'صناديق',icon:'fa-box',color:'#ec4899',criticalLimit:2,warningLimit:6,safeLimit:15},
    {id:6,name:'انارة',icon:'fa-lightbulb',color:'#f97316',criticalLimit:5,warningLimit:20,safeLimit:60},
  ],
};

let currentUser=null, cart=[], invNextNo=51, editingInv=null, confirmCB=null, arcFilter='all', reqFilter='all';

// ══ توليد رقم الفاتورة/الطلب الموحد ══
function genInvNo(type){
  var prefix={صرف:'G',ارجاع:'R',نقل:'T',الغاء:'CL',تعديل:'ED'};
  var p=prefix[type]||'INV';
  var used=DB.invoices.concat(DB.requests).map(function(x){return x.no;});
  var n=1;
  while(used.indexOf(p+n)>=0)n++;
  return p+n;
}
var currentPage=null, prevPage=null;
let feedHistory=[], trHistory=[];

// ══════════════════════ HELPERS ══════════════════════
function tag(s){
  const m={معتمد:'tg-green',معلق:'tg-gold',مرفوض:'tg-red',ملغي:'tg-gray',صرف:'tg-red',ارجاع:'tg-blue',نقل:'tg-orange',الغاء:'tg-purple',تغذية:'tg-green',تعديل:'tg-gold',مفتوح:'tg-blue',جاري:'tg-gold',مغلق:'tg-green',نظام:'tg-gray',نشط:'tg-green','غير نشط':'tg-gray'};
  const ico={معتمد:'✓ ',مرفوض:'✗ ',معلق:'⏳ ',ملغي:'⊘ '};
  return `<span class="tag ${m[s]||'tg-cyan'}">${(ico[s]||'')}${s}</span>`;
  // عرض النسخ الاحتياطية وموظف الشهر
  renderBackups();
  renderEmpMonth();
  // إضافة زر الحفظ
  document.querySelectorAll('[data-s-key]').forEach(function(el){
    el.addEventListener('change',function(){
      var key=this.dataset.sKey,val=this.type==='checkbox'?this.checked:this.value;
      if(DB.settings)DB.settings[key]=val;
    });
  });
}
function today(){return new Date().toLocaleDateString('en-CA',{timeZone:'Asia/Riyadh'});}

// ══ تحديث حالة الفاتورة في كامل النظام ══
function syncInvoiceStatus(no,newStatus,extra){
  extra=extra||{};
  // 1. DB.invoices — حدّث الفاتورة مباشرة
  var inv=DB.invoices.find(function(i){return i.no===no;});
  if(inv){
    inv.st=newStatus;
    if(extra.items&&extra.items.length)inv.items=extra.items;
    if(extra.cont)inv.cont=extra.cont;
    if(extra.wh)inv.wh=extra.wh;
    if(extra.boq!==undefined)inv.boq=extra.boq;
    if(extra.notes!==undefined)inv.notes=extra.notes;
    if(extra.whRecv)inv.whRecv=extra.whRecv;
    if(extra.editedAt)inv.editedAt=extra.editedAt;
    if(extra.editedBy)inv.editedBy=extra.editedBy;
  }
  // 2. DB.approvals — حدّث اعتمادات هذه الفاتورة
  DB.approvals.forEach(function(a){if(a.no===no)a.st=newStatus;});
  // 3. DB.requests — حدّث الطلبات التي رقمها = no أو origInv = no
  DB.requests.forEach(function(r){
    if(r.no===no||r.origInv===no) r.st=newStatus;
  });
  // 4. أعد رسم كل الواجهات المفتوحة + انتقل للتاب الصحيح
  updateBadges();
  try{if(currentPage==='dashboard')renderDashboard();}catch(e){}
  try{if(currentPage==='myinv')renderMyInv();}catch(e){}
  try{if(currentPage==='invoices')renderArc();}catch(e){}
  try{if(currentPage==='approve'){
    // إذا الحالة انتهت → اعرض السابقة تلقائياً
    if(newStatus==='معتمد'||newStatus==='مرفوض'){
      setApprTab('history');
    } else {
      renderApprovals();
    }
  }}catch(e){}
  try{if(currentPage==='requests'){
    if(newStatus==='معتمد'||newStatus==='مرفوض'||newStatus==='ملغي'){
      setReqTab('history');
    } else {
      renderAdminRequests();renderMyRequests();
    }
  }}catch(e){}
  try{if(currentPage==='inventory')renderInventory();}catch(e){}
  try{if(currentPage==='zones')zonesRender();}catch(e){}
  updateBadges();
}


// ══════════════════════════════════════════
// تبويبات السابقة — اعتماد فواتير الصرف
// ══════════════════════════════════════════
var apprTab='pending';
function setApprTab(t){
  apprTab=t;
  var ps=document.getElementById('appr-pending-section');
  var hs=document.getElementById('appr-history-section');
  var tp=document.getElementById('appr-tab-pending');
  var th=document.getElementById('appr-tab-history');
  if(ps)ps.style.display=t==='pending'?'block':'none';
  if(hs)hs.style.display=t==='history'?'block':'none';
  if(tp)tp.style.fontWeight=t==='pending'?'800':'400';
  if(th)th.style.fontWeight=t==='history'?'800':'400';
  if(t==='history')renderApprHistory();
  else renderApprovals();
}

function renderApprHistory(){
  var el=document.getElementById('appr-hist-list');if(!el)return;
  var q=(document.getElementById('appr-hist-q')?.value||'').toLowerCase().trim();
  var st=(document.getElementById('appr-hist-st')?.value||'').trim();
  var dt=(document.getElementById('appr-hist-date')?.value||'').trim();
  var items=DB.approvals.filter(function(a){return a.st!=='معلق';});
  if(q)items=items.filter(function(a){return a.no.toLowerCase().includes(q)||(a.cont||'').toLowerCase().includes(q)||(a.emp||'').toLowerCase().includes(q);});
  if(st)items=items.filter(function(a){return a.st===st;});
  if(dt)items=items.filter(function(a){return (a.approvedDate||a.d)===dt;});
  items.sort(function(a,b){return ((b.approvedDate||b.d)||'').localeCompare((a.approvedDate||a.d)||'');});
  var pend=DB.approvals.filter(function(a){return a.st==='معلق';}).length;
  var badge=document.getElementById('appr-pending-badge');
  if(badge){badge.textContent=pend;badge.style.display=pend?'inline-flex':'none';}
  if(!items.length){
    el.innerHTML='<div class="empty-state card"><i class="fa fa-history"></i><p>لا توجد طلبات سابقة</p></div>';
    return;
  }
  el.innerHTML=items.map(function(a){
    var isOk=a.st==='معتمد';
    var sc=isOk?'var(--g1)':'var(--r1)';
    var sb=isOk?'rgba(16,185,129,.1)':'rgba(239,68,68,.1)';
    var si=isOk?'fa-check-circle':'fa-times-circle';
    var dateLabel=a.approvedDate||a.d||'—';
    var byLabel=a.approvedBy||'—';
    return '<div class="req-card" style="margin-bottom:10px;opacity:.95">'+
      '<div class="req-hd">'+
        '<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">'+
          '<span class="req-no" style="color:var(--a1)">'+a.no+'</span>'+
          tag('صرف')+
          '<span style="background:'+sb+';color:'+sc+';border:1px solid '+sc+'44;border-radius:8px;padding:2px 10px;font-size:11px;font-weight:700"><i class="fa '+si+'"></i> '+a.st+'</span>'+
        '</div>'+
        '<div style="display:flex;gap:5px">'+
          '<button class="btn btn-sec btn-xs" onclick="showInvDetail(\''+a.no+'\')"><i class="fa fa-eye"></i>معاينة</button>'+
          '<button class="btn btn-primary btn-xs" onclick="printInvoice(\''+a.no+'\')"><i class="fa fa-print"></i>طباعة</button>'+
        '</div>'+
      '</div>'+
      '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px;margin-top:8px;font-size:11.5px">'+
        '<div><span style="color:var(--t3)">المقاول: </span><strong>'+a.cont+'</strong></div>'+
        '<div><span style="color:var(--t3)">المستودع: </span><strong>'+a.wh+'</strong></div>'+
        '<div><span style="color:var(--t3)">تاريخ الفاتورة: </span><span class="mono">'+a.d+'</span></div>'+
        '<div><span style="color:'+sc+'"><i class="fa '+si+'"></i> تاريخ '+a.st+': </span><span class="mono" style="color:'+sc+';font-weight:700">'+dateLabel+'</span></div>'+
        (byLabel!=='—'?'<div><span style="color:var(--t3)">بواسطة: </span><strong>'+byLabel+'</strong></div>':'')+
        (a.boq?'<div><span style="color:var(--t3)">BOQ: </span><span class="mono">'+a.boq+'</span></div>':'')+
      '</div>'+
      '<div style="margin-top:6px;font-size:11px;color:var(--t3)">'+
        (a.itemsStr||((a.items||[]).map(function(i){return i.name+' ×'+i.qty;}).join(' + ')))+
      '</div>'+
    '</div>';
  }).join('');
}

// ══════════════════════════════════════════
// تبويبات السابقة — طلبات الارجاع/الالغاء/النقل
// ══════════════════════════════════════════
var reqHistTab='pending';
function setReqTab(t){
  reqHistTab=t;
  var ps=document.getElementById('req-pending-section');
  var hs=document.getElementById('req-history-section');
  var tp=document.getElementById('req-tab-pending');
  var th=document.getElementById('req-tab-history');
  if(ps)ps.style.display=t==='pending'?'block':'none';
  if(hs)hs.style.display=t==='history'?'block':'none';
  if(tp)tp.style.fontWeight=t==='pending'?'800':'400';
  if(th)th.style.fontWeight=t==='history'?'800':'400';
  var cnt=DB.requests.filter(function(r){return r.st==='معلق';}).length;
  var badge=document.getElementById('req-pending-cnt');
  if(badge){badge.textContent=cnt;badge.style.display=cnt?'inline-flex':'none';}
  if(t==='history')renderReqHistory();
}

function renderReqHistory(){
  var el=document.getElementById('req-hist-list');if(!el)return;
  var q=(document.getElementById('req-hist-q')?.value||'').toLowerCase().trim();
  var tp=(document.getElementById('req-hist-type')?.value||'').trim();
  var st=(document.getElementById('req-hist-st')?.value||'').trim();
  var dt=(document.getElementById('req-hist-date')?.value||'').trim();
  var items=DB.requests.filter(function(r){return r.st!=='معلق';});
  if(q)items=items.filter(function(r){return r.no.toLowerCase().includes(q)||(r.cont||'').toLowerCase().includes(q)||(r.emp||'').toLowerCase().includes(q);});
  if(tp)items=items.filter(function(r){return r.type===tp;});
  if(st)items=items.filter(function(r){return r.st===st;});
  if(dt)items=items.filter(function(r){return (r.approvedDate||r.d)===dt;});
  items.sort(function(a,b){return ((b.approvedDate||b.d)||'').localeCompare((a.approvedDate||a.d)||'');});
  if(!items.length){
    el.innerHTML='<div class="empty-state card"><i class="fa fa-history"></i><p>لا توجد طلبات سابقة</p></div>';
    return;
  }
  var typeIco={ارجاع:'fa-rotate-left',الغاء:'fa-ban',نقل:'fa-right-left',تعديل:'fa-pen'};
  var typeColor={ارجاع:'var(--g1)',الغاء:'var(--r1)',نقل:'var(--a1)',تعديل:'var(--y1)'};
  el.innerHTML=items.map(function(r){
    var isOk=r.st==='معتمد';
    var sc=isOk?'var(--g1)':'var(--r1)';
    var sb=isOk?'rgba(16,185,129,.1)':'rgba(239,68,68,.1)';
    var si=isOk?'fa-check-circle':'fa-times-circle';
    var ico=typeIco[r.type]||'fa-file';
    var tc=typeColor[r.type]||'var(--t2)';
    var invNo=r.origInv||r.no;
    var dateLabel=r.approvedDate||r.d||'—';
    var byLabel=r.approvedBy||'—';
    return '<div class="req-card" style="margin-bottom:10px;opacity:.95">'+
      '<div class="req-hd">'+
        '<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">'+
          '<span class="req-no" style="color:var(--a1)">'+r.no+'</span>'+
          '<span style="background:rgba(255,255,255,.06);border:1px solid var(--b1);border-radius:6px;padding:2px 8px;font-size:10px;font-weight:700;color:'+tc+'"><i class="fa '+ico+'"></i> '+r.type+'</span>'+
          '<span style="background:'+sb+';color:'+sc+';border:1px solid '+sc+'44;border-radius:8px;padding:2px 10px;font-size:11px;font-weight:700"><i class="fa '+si+'"></i> '+r.st+'</span>'+
        '</div>'+
        '<div style="display:flex;gap:5px">'+
          '<button class="btn btn-sec btn-xs" onclick="showInvDetail(\''+invNo+'\')"><i class="fa fa-eye"></i>معاينة</button>'+
          '<button class="btn btn-primary btn-xs" onclick="printInvoice(\''+invNo+'\')"><i class="fa fa-print"></i>طباعة</button>'+
        '</div>'+
      '</div>'+
      '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px;margin-top:8px;font-size:11.5px">'+
        '<div><span style="color:var(--t3)">مقدّم الطلب: </span><strong>'+r.emp+'</strong></div>'+
        '<div><span style="color:var(--t3)">المستودع: </span><strong>'+(r.wh||'—')+'</strong></div>'+
        (r.cont?'<div><span style="color:var(--t3)">المقاول: </span><strong>'+r.cont+'</strong></div>':'')+
        (r.origInv?'<div><span style="color:var(--t3)">الفاتورة: </span><span class="mono" style="color:var(--a1)">'+r.origInv+'</span></div>':'')+
        '<div><span style="color:var(--t3)">تاريخ الطلب: </span><span class="mono">'+r.d+'</span></div>'+
        '<div><span style="color:'+sc+'"><i class="fa '+si+'"></i> تاريخ '+r.st+': </span><span class="mono" style="color:'+sc+';font-weight:700">'+dateLabel+'</span></div>'+
        (byLabel!=='—'?'<div><span style="color:var(--t3)">بواسطة: </span><strong>'+byLabel+'</strong></div>':'')+
        (r.boq?'<div><span style="color:var(--t3)">BOQ: </span><span class="mono">'+r.boq+'</span></div>':'')+
        (r.reason?'<div style="grid-column:span 2"><span style="color:var(--t3)">السبب: </span>'+r.reason+'</div>':'')+
      '</div>'+
      ((r.retItems||r.items)&&(r.retItems||r.items).length&&typeof (r.retItems||r.items)[0]==='object'?
        '<div style="margin-top:6px;font-size:11px;color:var(--t3)">'+(r.retItems||r.items).map(function(i){return i.name+' ×'+i.qty;}).join(' · ')+'</div>':'')+
    '</div>';
  }).join('');
}


// ══════════════════════════════════════════
// تبويبات رصيد المستودعات — المحجوزات
// ══════════════════════════════════════════
var invTab='all';

function setInvTab(t){
  invTab=t;
  var allS=document.getElementById('inv-tab-all-section');
  var resS=document.getElementById('inv-tab-reserved-section');
  var tabA=document.getElementById('inv-tab-all');
  var tabR=document.getElementById('inv-tab-reserved');
  if(allS) allS.style.display=t==='all'?'block':'none';
  if(resS) resS.style.display=t==='reserved'?'block':'none';
  if(tabA){tabA.style.color=t==='all'?'var(--a1)':'var(--t3)';tabA.style.borderBottomColor=t==='all'?'var(--a1)':'transparent';tabA.style.fontWeight=t==='all'?'800':'400';}
  if(tabR){tabR.style.color=t==='reserved'?'var(--y1)':'var(--t3)';tabR.style.borderBottomColor=t==='reserved'?'var(--y1)':'transparent';tabR.style.fontWeight=t==='reserved'?'800':'400';}
  if(t==='reserved') renderReserved();
  else renderInventory();
}

function getReservationsForItem(code, wh){
  var out=[];
  // فواتير صرف معلقة
  DB.approvals.filter(function(a){return a.st==='معلق'&&(!wh||a.wh===wh);}).forEach(function(a){
    var items=Array.isArray(a.items)?a.items:[];
    var it=items.find(function(x){return x.code===code;});
    if(it) out.push({no:a.no,type:'صرف',wh:a.wh,qty:it.qty,emp:a.emp,d:a.d,color:'var(--r1)',icon:'fa-cart-shopping'});
  });
  DB.invoices.filter(function(inv){return inv.st==='معلق'&&inv.type==='صرف'&&(!wh||inv.wh===wh);}).forEach(function(inv){
    var it=inv.items.find(function(x){return x.code===code;});
    if(it&&!out.find(function(o){return o.no===inv.no;}))
      out.push({no:inv.no,type:'صرف',wh:inv.wh,qty:it.qty,emp:inv.emp,d:inv.d,color:'var(--r1)',icon:'fa-cart-shopping'});
  });
  // طلبات نقل معلقة
  DB.requests.filter(function(r){return r.st==='معلق'&&r.type==='نقل'&&(!wh||r.wh===wh);}).forEach(function(r){
    var items=Array.isArray(r.items)?r.items:(r.retItems||[]);
    var it=items.find(function(x){return x.code===code;});
    if(it) out.push({no:r.no,type:'نقل',wh:r.wh,to:r.to||r.whRecv||'',qty:it.qty,emp:r.emp,d:r.d,color:'var(--a1)',icon:'fa-right-left'});
  });
  return out;
}

function updateReservedBadge(){
  var whs=DB.warehouses.filter(function(w){return w.active;});
  var count=0;
  DB.inventory.forEach(function(item){
    whs.forEach(function(w){
      if(getReservedStock(item.code,w.name)>0) count++;
    });
  });
  var badge=document.getElementById('inv-reserved-badge');
  if(badge){badge.textContent=count||'';badge.style.display=count?'inline':'none';}
}

function renderReserved(){
  var el=document.getElementById('res-content');if(!el)return;
  var q=(document.getElementById('res-q')?.value||'').toLowerCase().trim();
  var whFilter=(document.getElementById('res-wh')?.value||'').trim();

  // تعبئة فلتر المستودعات
  var whSel=document.getElementById('res-wh');
  if(whSel&&whSel.options.length<=1){
    DB.warehouses.filter(function(w){return w.active;}).forEach(function(w){
      var opt=document.createElement('option');opt.value=w.name;opt.textContent=w.name;whSel.appendChild(opt);
    });
  }

  var whs=DB.warehouses.filter(function(w){return w.active&&(!whFilter||w.name===whFilter);});

  // بناء قائمة المواد المحجوزة
  var rows=[];
  DB.inventory.forEach(function(item){
    if(q&&!item.code.toLowerCase().includes(q)&&!item.name.toLowerCase().includes(q)) return;
    whs.forEach(function(w){
      var reservations=getReservationsForItem(item.code,w.name);
      if(!reservations.length) return;
      var totalReal=getStock(item.code,w.name);
      var totalRes=reservations.reduce(function(s,r){return s+r.qty;},0);
      var avail=Math.max(0,totalReal-totalRes);
      rows.push({item:item,wh:w,real:totalReal,reserved:totalRes,avail:avail,reservations:reservations});
    });
  });

  if(!rows.length){
    el.innerHTML='<div class="empty-state card"><i class="fa fa-lock-open" style="font-size:32px;color:var(--g1)"></i><p style="color:var(--g1);font-weight:700">لا توجد مواد محجوزة حالياً</p><p style="color:var(--t3);font-size:12px">كل المخزون متاح للصرف</p></div>';
    return;
  }

  el.innerHTML=rows.map(function(row){
    var alertPct=row.avail===0?'var(--r1)':row.avail<row.real*0.3?'var(--y1)':'var(--g1)';
    var alertBg=row.avail===0?'rgba(239,68,68,.06)':row.avail<row.real*0.3?'rgba(245,158,11,.06)':'rgba(16,185,129,.06)';
    var pendRet=getPendingReturnStock(row.item.code,row.wh.name);
    return '<div class="card" style="margin-bottom:12px;border-right:4px solid '+alertPct+';background:'+alertBg+'">'+
      // ─ رأس البطاقة
      '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:12px">'+
        '<div style="display:flex;align-items:center;gap:10px">'+
          '<div style="width:42px;height:42px;background:rgba(255,255,255,.06);border:1px solid var(--b1);border-radius:10px;display:flex;align-items:center;justify-content:center">'+
            '<i class="fa fa-box" style="color:var(--a1)"></i>'+
          '</div>'+
          '<div>'+
            '<div style="font-weight:800;font-size:13px;color:var(--t1)">'+row.item.name+'</div>'+
            '<div style="font-size:11px;color:var(--t3)"><span class="mono" style="color:var(--a1)">'+row.item.code+'</span> · '+row.item.cat+' · '+row.wh.name+'</div>'+
          '</div>'+
        '</div>'+
        // ─ أرقام الرصيد
        '<div style="display:flex;gap:16px;text-align:center">'+
          '<div style="background:var(--bg2);border-radius:8px;padding:6px 14px">'+
            '<div style="font-size:11px;color:var(--t3)">الرصيد الكلي</div>'+
            '<div style="font-size:20px;font-weight:900;color:var(--t1);font-family:monospace">'+row.real+'</div>'+
          '</div>'+
          '<div style="background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.2);border-radius:8px;padding:6px 14px">'+
            '<div style="font-size:11px;color:var(--r1)"><i class="fa fa-lock"></i> محجوز</div>'+
            '<div style="font-size:20px;font-weight:900;color:var(--r1);font-family:monospace">'+row.reserved+'</div>'+
          '</div>'+
          (pendRet>0?
            '<div style="background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.2);border-radius:8px;padding:6px 14px">'+
              '<div style="font-size:11px;color:var(--g1)"><i class="fa fa-rotate-left"></i> ارجاع معلق</div>'+
              '<div style="font-size:20px;font-weight:900;color:var(--g1);font-family:monospace">+'+pendRet+'</div>'+
            '</div>':'')+ 
          '<div style="background:'+(row.avail===0?'rgba(239,68,68,.08)':row.avail<row.real*0.3?'rgba(245,158,11,.08)':'rgba(16,185,129,.08)')+';border:1px solid '+alertPct+'33;border-radius:8px;padding:6px 14px">'+
            '<div style="font-size:11px;color:'+alertPct+'"><i class="fa fa-unlock"></i> متاح</div>'+
            '<div style="font-size:20px;font-weight:900;color:'+alertPct+';font-family:monospace">'+row.avail+'</div>'+
          '</div>'+
        '</div>'+
      '</div>'+
      // ─ شريط التقدم
      '<div style="background:var(--bg2);border-radius:6px;height:8px;margin-bottom:12px;overflow:hidden">'+
        '<div style="height:100%;border-radius:6px;background:'+alertPct+';width:'+Math.min(100,row.reserved/Math.max(1,row.real)*100)+'%"></div>'+
      '</div>'+
      // ─ تفاصيل الحجوزات
      '<div style="font-size:11.5px;font-weight:700;color:var(--t3);margin-bottom:8px;text-transform:uppercase;letter-spacing:1px">تفاصيل الحجوزات</div>'+
      '<div style="display:flex;flex-direction:column;gap:6px">'+
      row.reservations.map(function(res){
        return '<div style="display:flex;align-items:center;gap:10px;background:var(--bg2);border:1px solid var(--b1);border-radius:8px;padding:8px 12px">'+
          '<div style="width:32px;height:32px;background:'+res.color+'22;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0">'+
            '<i class="fa '+res.icon+'" style="color:'+res.color+';font-size:13px"></i>'+
          '</div>'+
          '<div style="flex:1;min-width:0">'+
            '<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">'+
              '<span class="mono" style="font-weight:800;font-size:12px;color:'+res.color+'">'+res.no+'</span>'+
              '<span style="background:'+res.color+'22;color:'+res.color+';border-radius:5px;padding:1px 7px;font-size:10px;font-weight:700">'+res.type+'</span>'+
              (res.type==='نقل'&&res.to?'<span style="font-size:10px;color:var(--t3)">→ '+res.to+'</span>':'')+
            '</div>'+
            '<div style="font-size:11px;color:var(--t3);margin-top:2px">'+
              '<i class="fa fa-user" style="margin-left:4px"></i>'+res.emp+
              ' &nbsp;·&nbsp; <i class="fa fa-calendar" style="margin-left:4px"></i>'+res.d+
            '</div>'+
          '</div>'+
          '<div style="background:'+res.color+'22;border:1px solid '+res.color+'44;border-radius:8px;padding:4px 12px;text-align:center;flex-shrink:0">'+
            '<div style="font-size:10px;color:'+res.color+'">الكمية</div>'+
            '<div style="font-size:17px;font-weight:900;color:'+res.color+';font-family:monospace">'+res.qty+'</div>'+
          '</div>'+
        '</div>';
      }).join('')+
      '</div>'+
    '</div>';
  }).join('');
  updateReservedBadge();
}


function doTransferApprove(r){
  r.st='معتمد';r.approvedDate=today();r.approvedBy=currentUser.name;
  var from=r.from||r.wh;
  var to=r.to||r.whRecv||'';
  (r.items||[]).forEach(function(it){
    setStock(it.code,from,-it.qty);
    if(to) setStock(it.code,to,+it.qty);
  });
  syncInvoiceStatus(r.origInv||r.no,'معتمد');
  addLog('نقل','اعتماد نقل '+r.no+' من '+from+' → '+to,from);
  addNotif('ok','✓ نقل '+r.no,'تم اعتماد نقل المواد من '+from+' لـ'+to,'fa-right-left',r.emp);
  updateBadges();renderRequests();renderMyRequests();
  toast('ok','✓ اعتماد نقل '+r.no,'تم نقل المواد من '+from+' إلى '+to,'fa-right-left');
}

function validateItemExists(code){
  var item=DB.inventory.find(function(i){return i.code===code;});
  if(!item){
    toast('err','مادة غير معرفة',
      'الكود <strong class="mono">'+code+'</strong> غير موجود في النظام — يجب تعريف المادة أولاً من قسم رصيد المستودعات',
      'fa-ban');
    return null;
  }
  return item;
}

function nowTime(){return new Date().toLocaleTimeString('ar-SA',{timeZone:'Asia/Riyadh',hour:'2-digit',minute:'2-digit',hour12:false});}
function addLog(type,act,wh,extra){
  const cols={صرف:'var(--g1)',تغذية:'#009245',نقل:'var(--a3)',ارجاع:'var(--o1)',الغاء:'var(--r1)',تعديل:'var(--y1)',اعتماد:'var(--g1)',رفض:'var(--r1)'};
  const icos={صرف:'fa-file-invoice',تغذية:'fa-cubes',نقل:'fa-right-left',ارجاع:'fa-rotate-left',الغاء:'fa-ban',تعديل:'fa-pen',اعتماد:'fa-signature',رفض:'fa-times'};
  DB.logs.unshift({type,act,emp:currentUser?currentUser.name:'النظام',wh:wh||'—',t:nowTime(),d:today(),c:cols[type]||'var(--t3)',i:icos[type]||'fa-circle-info',...(extra||{})});
  if(DB.logs.length>200)DB.logs.pop();
}
function getWhKey(wh){var w=DB.warehouses.find(function(x){return x.name===wh;});return w?w.key:null;}
function getStock(code,wh){const i=DB.inventory.find(x=>x.code===code);if(!i)return 0;var k=getWhKey(wh);return k?(i[k]||0):0;}
function setStock(code,wh,delta){const i=DB.inventory.find(x=>x.code===code);if(!i)return;var k=getWhKey(wh);if(k)i[k]=Math.max(0,(i[k]||0)+delta);}
// ══════════════════════════════════════════════════════
// نظام التنظيف التلقائي الشامل
// الفواتير وكل ارتباطاتها: سنة من تاريخ الاعتماد/الإغلاق
// سجل العمليات: شهران
// الإشعارات: شهر
// المعلقة لا تُحذف أبداً
// المستودعات/الرصيد/الزونات/المستخدمين/الفئات/التواصل/المقاولين محمية
// ══════════════════════════════════════════════════════

function getCleanupCutoffs(){
  var now = new Date(new Date().toLocaleString('en-US',{timeZone:'Asia/Riyadh'}));
  var oneYear    = new Date(now); oneYear.setFullYear(oneYear.getFullYear()-1);
  var twoMonths  = new Date(now); twoMonths.setMonth(twoMonths.getMonth()-2);
  var oneMonth   = new Date(now); oneMonth.setMonth(oneMonth.getMonth()-1);
  return {oneYear:oneYear, twoMonths:twoMonths, oneMonth:oneMonth};
}

function isExpired(dateStr, cutoff){
  if(!dateStr) return false;
  var d = new Date(dateStr);
  return !isNaN(d.getTime()) && d < cutoff;
}

function getInvCloseDate(inv){
  return inv.approvedDate || inv.cancelDate || inv.closedDate || null;
}

function getExpiredInvoiceNos(cutoff){
  // جمع أرقام الفواتير المنتهية فقط (ليست معلقة وتجاوزت السنة)
  var nos = new Set();
  DB.invoices.forEach(function(inv){
    if(inv.st === 'معلق') return; // المعلقة لا تُحذف
    var closeDate = getInvCloseDate(inv);
    if(closeDate && isExpired(closeDate, cutoff)) nos.add(inv.no);
  });
  return nos;
}

function autoCleanup(){
  var cuts = getCleanupCutoffs();
  var stats = {invoices:0, requests:0, approvals:0, boq:0, logs:0, notifs:0};

  // ── الفواتير المنتهية وكل ارتباطاتها ──
  var expiredNos = getExpiredInvoiceNos(cuts.oneYear);

  if(expiredNos.size > 0){
    // 1. حذف الفواتير
    var invBefore = DB.invoices.length;
    DB.invoices = DB.invoices.filter(function(inv){ return !expiredNos.has(inv.no); });
    stats.invoices = invBefore - DB.invoices.length;

    // 2. حذف طلبات مرتبطة (origInv أو no)
    var reqBefore = DB.requests.length;
    DB.requests = DB.requests.filter(function(r){
      return !expiredNos.has(r.origInv) && !expiredNos.has(r.no);
    });
    stats.requests = reqBefore - DB.requests.length;

    // 3. حذف اعتمادات مرتبطة
    var apprBefore = DB.approvals.length;
    DB.approvals = DB.approvals.filter(function(a){ return !expiredNos.has(a.no); });
    stats.approvals = apprBefore - DB.approvals.length;

    // 4. حذف BOQ المرتبط
    if(DB.boqItems){
      var boqBefore = DB.boqItems.length;
      DB.boqItems = DB.boqItems.filter(function(b){
        return !expiredNos.has(b.invNo) && !expiredNos.has(b.no);
      });
      stats.boq = boqBefore - DB.boqItems.length;
    }

    // 5. حذف الإشعارات المرتبطة بالفواتير المنتهية
    if(DB.notifications){
      DB.notifications = DB.notifications.filter(function(n){
        var invRef = n.invNo || n.no || '';
        return !expiredNos.has(invRef);
      });
    }
  }

  // ── سجل العمليات: شهران ──
  if(DB.logs){
    var logsBefore = DB.logs.length;
    DB.logs = DB.logs.filter(function(l){
      return !isExpired(l.date||l.d, cuts.twoMonths);
    });
    stats.logs = logsBefore - DB.logs.length;
  }

  // ── الإشعارات: شهر (الكل القديم) ──
  if(DB.notifications){
    var notifBefore = DB.notifications.length;
    DB.notifications = DB.notifications.filter(function(n){
      return !isExpired(n.date||n.d, cuts.oneMonth);
    });
    stats.notifs = notifBefore - DB.notifications.length;
  }

  var total = stats.invoices+stats.requests+stats.approvals+stats.boq+stats.logs+stats.notifs;
  return {stats:stats, total:total, expiredCount:expiredNos.size};
}

function runAutoCleanupOnLogin(){
  var result = autoCleanup();
  if(result.total > 0){
    var parts = [];
    if(result.stats.invoices) parts.push(result.stats.invoices+' فاتورة');
    if(result.stats.requests) parts.push(result.stats.requests+' طلب');
    if(result.stats.approvals) parts.push(result.stats.approvals+' اعتماد');
    if(result.stats.boq) parts.push(result.stats.boq+' BOQ');
    if(result.stats.logs) parts.push(result.stats.logs+' سجل');
    if(result.stats.notifs) parts.push(result.stats.notifs+' إشعار');
    toast('info','🗑 تنظيف تلقائي','حُذف: '+parts.join('، '),'fa-broom');
  }
}

// ══ معاينة ما سيُحذف قبل التنفيذ ══
function previewCleanup(){
  var cuts = getCleanupCutoffs();
  var expiredNos = getExpiredInvoiceNos(cuts.oneYear);
  var preview = {
    invoices: expiredNos.size,
    requests: DB.requests.filter(function(r){return expiredNos.has(r.origInv)||expiredNos.has(r.no);}).length,
    approvals: DB.approvals.filter(function(a){return expiredNos.has(a.no);}).length,
    boq: DB.boqItems?DB.boqItems.filter(function(b){return expiredNos.has(b.invNo)||expiredNos.has(b.no);}).length:0,
    logs: (DB.logs||[]).filter(function(l){return isExpired(l.date||l.d,cuts.twoMonths);}).length,
    notifs: (DB.notifications||[]).filter(function(n){return isExpired(n.date||n.d,cuts.oneMonth);}).length,
  };
  var total = preview.invoices+preview.requests+preview.approvals+preview.boq+preview.logs+preview.notifs;
  return {preview:preview, total:total, expiredNos:expiredNos};
}

function manualCleanup(){
  if(currentUser?.role!=='مدير النظام'){toast('err','غير مصرح','هذه العملية للمدير فقط','fa-lock');return;}
  var pv = previewCleanup();
  if(!pv.total){toast('ok','النظام نظيف','لا توجد بيانات منتهية الصلاحية','fa-check-circle');return;}
  var p = pv.preview;
  var html =
    '<div style="font-size:12px">'+
    '<div style="background:rgba(239,68,68,.07);border:1px solid rgba(239,68,68,.2);border-radius:8px;padding:10px;margin-bottom:12px">'+
      '<i class="fa fa-triangle-exclamation" style="color:var(--r1)"></i> <strong style="color:var(--r1)">سيُحذف نهائياً مع كامل الارتباطات:</strong>'+
    '</div>'+
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px">'+
      (p.invoices?'<div style="background:var(--bg2);border-radius:8px;padding:10px;text-align:center;border:1px solid rgba(239,68,68,.15)"><div style="font-size:22px;font-weight:900;color:var(--r1)">'+p.invoices+'</div><div style="font-size:11px;color:var(--t3)">فاتورة (أكثر من سنة)</div></div>':'')+
      (p.requests?'<div style="background:var(--bg2);border-radius:8px;padding:10px;text-align:center;border:1px solid rgba(239,68,68,.15)"><div style="font-size:22px;font-weight:900;color:var(--r1)">'+p.requests+'</div><div style="font-size:11px;color:var(--t3)">طلب مرتبط</div></div>':'')+
      (p.approvals?'<div style="background:var(--bg2);border-radius:8px;padding:10px;text-align:center;border:1px solid rgba(239,68,68,.15)"><div style="font-size:22px;font-weight:900;color:var(--r1)">'+p.approvals+'</div><div style="font-size:11px;color:var(--t3)">اعتماد مرتبط</div></div>':'')+
      (p.boq?'<div style="background:var(--bg2);border-radius:8px;padding:10px;text-align:center;border:1px solid rgba(239,68,68,.15)"><div style="font-size:22px;font-weight:900;color:var(--r1)">'+p.boq+'</div><div style="font-size:11px;color:var(--t3)">سجل BOQ</div></div>':'')+
      (p.logs?'<div style="background:var(--bg2);border-radius:8px;padding:10px;text-align:center;border:1px solid rgba(245,158,11,.15)"><div style="font-size:22px;font-weight:900;color:var(--y1)">'+p.logs+'</div><div style="font-size:11px;color:var(--t3)">سجل عمليات (أكثر من شهرين)</div></div>':'')+
      (p.notifs?'<div style="background:var(--bg2);border-radius:8px;padding:10px;text-align:center;border:1px solid rgba(245,158,11,.15)"><div style="font-size:22px;font-weight:900;color:var(--y1)">'+p.notifs+'</div><div style="font-size:11px;color:var(--t3)">إشعار (أكثر من شهر)</div></div>':'')+
    '</div>'+
    '<div style="background:rgba(16,185,129,.06);border:1px solid rgba(16,185,129,.2);border-radius:8px;padding:8px 12px;font-size:11px;color:var(--g1)">'+
      '<i class="fa fa-shield-halved"></i> محمي: المستودعات · الرصيد · الزونات · المستخدمين · الفئات · أرقام التواصل · المقاولين'+
    '</div></div>';
  showConfirm('<i class="fa fa-broom" style="color:var(--r1)"></i> تنظيف البيانات المنتهية',
    html,'تنظيف الآن','btn-danger',function(){
      var result = autoCleanup();
      toast('ok','✓ تم التنظيف','حُذف '+result.total+' سجل منتهي الصلاحية','fa-broom');
      updateBadges();renderLogs();
    });
}



// ══ اعتماد/رفض من لوحة التحكم ══
function dashApprove(no,id){
  if(currentUser?.role==='مشرف وردية'){toast('err','غير مصرح','ليس لديك صلاحية الاعتماد','fa-lock');return;}
  var a=DB.approvals.find(function(x){return x.id===id;});
  var inv=DB.invoices.find(function(i){return i.no===no;});
  if(!a&&!inv){toast('err','غير موجودة','الفاتورة غير موجودة','fa-ban');return;}
  var wh=a?a.wh:inv?inv.wh:'';
  var rawItems=a?a.items:inv?inv.items:[];
  var items=Array.isArray(rawItems)?rawItems:[];
  showConfirm('<i class="fa fa-signature" style="color:var(--g1)"></i> اعتماد '+no,
    'اعتماد فاتورة الصرف <strong>'+no+'</strong> — '+(a?a.cont:inv?inv.cont:'')+'؟',
    'اعتماد','btn-green',function(){
      items.forEach(function(it){if(it.code&&it.qty)setStock(it.code,wh,-it.qty);});
      if(a){a.st='معتمد';a.approvedDate=today();a.approvedBy=currentUser.name;}
      if(inv){inv.st='معتمد';inv.approvedDate=today();inv.approvedBy=currentUser.name;}
      syncInvoiceStatus(no,'معتمد');
      addLog('اعتماد','اعتماد فاتورة صرف '+no+' من لوحة التحكم',wh,{no:no});
      addNotif('ok','✓ اعتماد '+no,'تم اعتماد فاتورة الصرف وخصم المواد من '+wh,'fa-signature',a?a.emp:inv?inv.emp:'');
      updateBadges();renderDashboard();
      toast('ok','✓ تم الاعتماد','فاتورة '+no+' معتمدة — المخزون مُحدَّث','fa-signature');
    });
}

function dashReject(no,id){
  if(currentUser?.role==='مشرف وردية'){toast('err','غير مصرح','ليس لديك صلاحية الرفض','fa-lock');return;}
  var a=DB.approvals.find(function(x){return x.id===id;});
  if(!a)return;
  showConfirm('<i class="fa fa-times" style="color:var(--r1)"></i> رفض '+no,
    'رفض فاتورة الصرف <strong>'+no+'</strong>؟<br>سيتم حفظها كمرفوضة.',
    'رفض','btn-danger',function(){
      a.st='مرفوض';a.approvedDate=today();a.approvedBy=currentUser.name;
      syncInvoiceStatus(no,'مرفوض');
      addLog('رفض','رفض فاتورة صرف '+no+' من لوحة التحكم',a.wh,{no:no});
      addNotif('warn','رُفضت فاتورة '+no,'تم رفض فاتورة الصرف من لوحة التحكم','fa-times',a.emp);
      updateBadges();renderDashboard();
      toast('ok','رُفضت '+no,'تم حفظها كمرفوضة','fa-times');
    });
}

// ══ موظف الشهر — دائماً الشهر السابق ══
function renderEmpMonth(){
  var now=new Date(new Date().toLocaleString('en-US',{timeZone:'Asia/Riyadh'}));
  var prev=new Date(now.getFullYear(),now.getMonth()-1,1);
  var targetMonth=prev.getMonth();
  var targetYear=prev.getFullYear();
  var months=['يناير','فبراير','مارس','أبريل','مايو','يونيو','يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر'];
  var mn=months[targetMonth];
  var tm=targetYear+'-'+String(targetMonth+1).padStart(2,'0');
  var mojtaheds=DB.users.filter(function(u){return u.active&&(u.role==='موجه بلاغات'||u.role==='مشرف وردية');});
  var stats=mojtaheds.map(function(u){
    return {u:u,approved:DB.invoices.filter(function(i){return i.emp===u.name&&i.st==='معتمد'&&(i.d||'').startsWith(tm);}).length};
  }).sort(function(a,b){return b.approved-a.approved;});
  var top=stats.length&&stats[0].approved>0?stats[0]:null;
  var el=document.getElementById('emp-month-wrap');
  if(el){
    if(!top){el.innerHTML='';el.style.display='none';}
    else{
      el.style.display='';
      var avHtml=top.u.photo?('<img src="'+top.u.photo+'" style="width:100%;height:100%;object-fit:cover;border-radius:50%">'):('<div style="font-size:22px;font-weight:800;color:#fff">'+top.u.av+'</div>');
      el.innerHTML='<div class="card" style="padding:14px 12px;text-align:center">'+
        '<div style="font-size:8.5px;color:rgba(255,200,0,.8);letter-spacing:2px;font-weight:700;margin-bottom:8px">⭐ موظف الشهر — '+mn+' ⭐</div>'+
        '<div style="font-size:20px">👑</div>'+
        '<div style="width:60px;height:60px;border-radius:50%;margin:6px auto;background:'+top.u.color+';display:flex;align-items:center;justify-content:center;overflow:hidden;box-shadow:0 0 0 3px rgba(255,200,0,.4)">'+avHtml+'</div>'+
        '<div style="font-size:13px;font-weight:800;color:var(--t1)">'+top.u.name+'</div>'+
        '<div style="font-size:10px;color:var(--t3);margin-top:1px">'+top.u.role+'</div>'+
        '<div style="display:flex;gap:8px;justify-content:center;margin-top:8px">'+
          '<div style="background:rgba(255,200,0,.08);border:1px solid rgba(255,200,0,.2);border-radius:8px;padding:5px 12px">'+
            '<div style="font-size:18px;font-weight:900;color:#f9c72c;font-family:monospace">'+top.approved+'</div>'+
            '<div style="font-size:9px;color:var(--t3)">طلب ناجح</div>'+
          '</div>'+
        '</div>'+
      '</div>';
    }
  }
  var old=document.getElementById('emp-month-content');if(old&&old.parentNode)old.parentNode.style.display='none';
  if(typeof renderEmpMini==='function')renderEmpMini(top,mn);
}

function updateBadges(){updateZonesBadge();updateReservedBadge();
  // تحديث بطاقات لوحة التحكم
  var sv3=document.getElementById('sv3');
  var sv4=document.getElementById('sv4');
  if(sv3) sv3.textContent=DB.approvals.filter(function(a){return a.st==='معلق';}).length;
  if(sv4) sv4.textContent=DB.requests.filter(function(r){return r.st==='معلق'&&r.type==='ارجاع';}).length;
  var isM=currentUser?.role==='موجه بلاغات';
  var isW=currentUser?.role==='مشرف وردية';
  // badge الطلبات: للموجه ومشرف الوردية = طلباتهم المعلقة فقط، للمدير/أمين = كل المعلقة
  var rCount = (isM||isW)
    ? DB.requests.filter(function(x){return x.st==='معلق'&&x.emp===currentUser.name;}).length
    : DB.requests.filter(function(x){return x.st==='معلق';}).length;
  var a=DB.approvals.filter(function(x){return x.st==='معلق';}).length;
  var rb=document.getElementById('badge-req');var ab=document.getElementById('badge-appr');
  if(rb){rb.textContent=rCount;rb.style.display=rCount?'flex':'none';}
  if(ab){ab.textContent=a;ab.style.display=a?'flex':'none';}
  var nd=document.getElementById('notif-dot');
  if(nd)nd.style.display=DB.notifications.filter(function(n){return !n.read;}).length?'block':'none';
}
function fillDL(){const dl=document.getElementById('inv-datalist');if(dl)dl.innerHTML=DB.inventory.map(i=>`<option value="${i.code}">${i.name}</option>`).join('');}

// حساب الكمية المحجوزة (فواتير معلقة لم تُعتمد بعد)
function getReservedStock(code,wh){
  // جمع أرقام الفواتير المحسوبة لتجنب التكرار
  var counted=new Set();
  var total=0;

  // 1. DB.approvals المعلقة (فواتير الصرف بانتظار الاعتماد) — الأولوية للاعتماد
  DB.approvals
    .filter(function(a){return a.st==='معلق'&&a.wh===wh;})
    .forEach(function(a){
      if(counted.has(a.no)) return;
      counted.add(a.no);
      var items=Array.isArray(a.items)?a.items:[];
      var item=items.find(function(it){return it.code===code;});
      if(item) total+=item.qty;
    });

  // 2. DB.invoices المعلقة من نوع صرف — فقط التي لم تُحسب من approvals
  DB.invoices
    .filter(function(inv){return inv.st==='معلق'&&inv.type==='صرف'&&inv.wh===wh;})
    .forEach(function(inv){
      if(counted.has(inv.no)) return; // تجنب التكرار مع approvals
      counted.add(inv.no);
      var item=(inv.items||[]).find(function(it){return it.code===code;});
      if(item) total+=item.qty;
    });

  // 3. طلبات النقل المعلقة من هذا المستودع (أولوية أدنى)
  DB.requests
    .filter(function(r){return r.st==='معلق'&&r.type==='نقل'&&r.wh===wh;})
    .forEach(function(r){
      if(counted.has(r.no)) return;
      counted.add(r.no);
      var items=Array.isArray(r.items)?r.items:(r.retItems||[]);
      var item=items.find(function(it){return it.code===code;});
      if(item) total+=item.qty;
    });

  return total;
}
// الكمية المتاحة الفعلية = الرصيد الحقيقي − المحجوز
function getAvailableStock(code,wh){
  return Math.max(0,getStock(code,wh)-getReservedStock(code,wh));
}
// ثغرة ٢ — الارجاع المعلق يُحسب كرصيد مؤقت إضافي
function getPendingReturnStock(code,wh){
  // فقط طلبات الارجاع المعلقة في DB.requests (لم تُعتمد بعد)
  // doDirectReturn يضيف للمخزون فوراً فلا تُحسب هنا
  return DB.requests
    .filter(function(r){return r.st==='معلق'&&r.type==='ارجاع'&&r.wh===wh;})
    .reduce(function(sum,r){
      var items=Array.isArray(r.retItems)?r.retItems:Array.isArray(r.items)?r.items:[];
      var it=items.find(function(x){return x.code===code;});
      return sum+(it?it.qty:0);
    },0);
}
// الرصيد المتوقع = المتاح الفعلي + الارجاعات المعلقة
function getExpectedStock(code,wh){
  return getAvailableStock(code,wh)+getPendingReturnStock(code,wh);
}

// ══════════════════════ TOAST ══════════════════════
const TC={info:{bg:'rgba(0,102,255,.15)',c:'#60a5fa'},ok:{bg:'rgba(16,185,129,.15)',c:'#34d399'},warn:{bg:'rgba(245,158,11,.15)',c:'#fbbf24'},err:{bg:'rgba(239,68,68,.15)',c:'#f87171'}};
function toast(type,title,msg,icon){
  // لا تظهر الاشعارات في شاشة تسجيل الدخول
  if(!currentUser)return;
  const c=TC[type]||TC.info;
  const el=document.createElement('div');el.className='toast';
  el.innerHTML='<div class="t-ic" style="background:'+c.bg+'"><i class="fa '+(icon||'fa-circle-info')+'" style="color:'+c.c+'"></i></div><div class="t-bd"><strong>'+title+'</strong><span>'+msg+'</span></div>';
  document.getElementById('toasts').prepend(el);
  el.onclick=function(){el.classList.add('out');setTimeout(function(){el.remove();},250);};
  setTimeout(function(){el.classList.add('out');setTimeout(function(){el.remove();},250);},4000);
}

// ══════════════════════ MODAL ══════════════════════
function openModal(id){document.getElementById(id).classList.add('show');}
function closeModal(id){document.getElementById(id).classList.remove('show');}
function showConfirm(title,body,okLbl,okCls,cb){
  document.getElementById('confirm-title').innerHTML=title;
  document.getElementById('confirm-body').innerHTML=body;
  const b=document.getElementById('confirm-ok-btn');b.textContent=okLbl;b.className='btn '+okCls;
  confirmCB=cb;openModal('modal-confirm');
}
function confirmOK(){closeModal('modal-confirm');if(confirmCB)confirmCB();confirmCB=null;}
function showFormModal(title,body,actions){
  document.getElementById('modal-form-title').innerHTML=title;
  document.getElementById('modal-form-body').innerHTML=body;
  const ab=document.getElementById('modal-form-actions');
  ab.innerHTML=actions.map((a,i)=>`<button class="btn ${a.cls}" id="mfa${i}">${a.lbl}</button>`).join('');
  actions.forEach((a,i)=>document.getElementById('mfa'+i).onclick=a.fn);
  openModal('modal-form');
}

// ══════════════════════ LOGIN ══════════════════════
(function(){
  document.getElementById('lhints').innerHTML=DB.users.filter(u=>u.active).map(u=>
    `<div class="lhi" onclick="fillLogin('${u.phone}','${u.pass}')">
      <div><div class="lhir">${u.role}</div><div class="lhin">${u.name}</div></div>
      <div class="lhic">${u.phone} / ${u.pass}</div>
    </div>`).join('');
})();
function fillLogin(p,w){document.getElementById('lphone').value=p;document.getElementById('lpass').value=w;clearLE();}
function togglePeye(){const i=document.getElementById('lpass'),ic=document.getElementById('peye-ico');i.type=i.type==='password'?'text':'password';ic.className='fa fa-eye'+(i.type==='text'?'-slash':'');}
function clearLE(){['lerr-p','lerr-w'].forEach(id=>document.getElementById(id).classList.remove('show'));['lphone','lpass'].forEach(id=>document.getElementById(id).classList.remove('err'));}
function doLogin(){
  clearLE();
  const phone=document.getElementById('lphone').value.trim();
  const pass=document.getElementById('lpass').value.trim();
  const btn=document.getElementById('lbtn');
  if(!phone||phone.length<10||!phone.startsWith('05')){
    document.getElementById('lphone').classList.add('err');
    document.getElementById('lerr-p-msg').textContent='ادخل رقم جوال صحيح يبدأ بـ 05';
    document.getElementById('lerr-p').classList.add('show');return;
  }
  if(!pass){document.getElementById('lpass').classList.add('err');document.getElementById('lerr-w-msg').textContent='ادخل كلمة السر';document.getElementById('lerr-w').classList.add('show');return;}
  btn.disabled=true;btn.innerHTML='<i class="fa fa-spinner fa-spin"></i>  جاري التحقق...';
  setTimeout(()=>{
    const user=DB.users.find(u=>u.phone===phone&&u.pass===pass&&u.active);
    if(!user){
      const ex=DB.users.find(u=>u.phone===phone);
      if(!ex){document.getElementById('lphone').classList.add('err');document.getElementById('lerr-p-msg').textContent='رقم الجوال غير مسجل في النظام';document.getElementById('lerr-p').classList.add('show');}
      else{document.getElementById('lpass').classList.add('err');document.getElementById('lerr-w-msg').textContent='كلمة السر غير صحيحة';document.getElementById('lerr-w').classList.add('show');}
      btn.disabled=false;btn.innerHTML='<i class="fa fa-right-to-bracket"></i>  تسجيل الدخول';return;
    }
    // حفظ سلة المستخدم السابق إن وجد
    if(currentUser)saveUserBaskets();
    currentUser=user;
    // تحميل سلة المستخدم الجديد
    loadUserBaskets();
    document.getElementById('uav').textContent=user.av;
    // تحديث صورة المستخدم في البطاقة
    var uavWrap=document.getElementById('uav-wrap');
    if(uavWrap){
      if(user.photo){
        uavWrap.innerHTML='<img src="'+user.photo+'" style="width:100%;height:100%;object-fit:cover">';
      } else {
        uavWrap.innerHTML='<div class="uav" id="uav" style="font-size:11px;font-weight:800;color:#fff">'+user.av+'</div>';
      }
    }
    document.getElementById('uav').style.background=user.color;
    document.getElementById('uname').textContent=user.name;
    document.getElementById('urole').textContent=user.role;
    const ls=document.getElementById('login-screen');
    ls.style.transition='opacity .45s';ls.style.opacity='0';
    setTimeout(()=>{ls.style.display='none';startLoader();},450);
    setTimeout(applySidebarRole,1200);
  },700);
}
function doLogout(){
  showConfirm('<i class="fa fa-right-from-bracket" style="color:var(--r1)"></i> تسجيل الخروج','هل تريد تسجيل الخروج من النظام؟','خروج','btn-danger',()=>{
    saveUserBaskets();
    clearAllBaskets();
    currentUser=null;
    document.getElementById('shell').classList.remove('show');
    document.getElementById('lphone').value='';document.getElementById('lpass').value='';
    document.getElementById('lbtn').disabled=false;document.getElementById('lbtn').innerHTML='<i class="fa fa-right-to-bracket"></i>  تسجيل الدخول';
    clearLE();
    const ls=document.getElementById('login-screen');
    ls.style.display='flex';ls.style.opacity='0';
    requestAnimationFrame(()=>{ls.style.transition='opacity .4s';ls.style.opacity='1';});
  });
}
function startLoader(){
  const loader=document.getElementById('loader'),fill=document.getElementById('ldr-fill'),pctEl=document.getElementById('ldr-pct');
  loader.classList.add('show');let pct=0;
  const t=setInterval(()=>{
    pct=Math.min(pct+Math.random()*18,100);
    fill.style.width=pct+'%';pctEl.textContent=Math.round(pct)+'%';
    if(pct>=100){clearInterval(t);setTimeout(()=>{
      loader.classList.add('done');
      setTimeout(()=>{loader.classList.remove('show','done');document.getElementById('shell').classList.add('show');loadUserBaskets();cleanOldInvoices();fillWhSelects();go(currentUser?.role==='موجه بلاغات'||currentUser?.role==='مشرف وردية'?'inventory':'dashboard');autoBackup();initNotifToggle();applySidebarRole();updateBadges();renderEmpMonth();startLiveNotifs();initBrightness();},600);
    },300);}
  },100);
}

// ══════════════════════ NAVIGATION ══════════════════════
const PAGES={dashboard:{t:'لوحة التحكم',s:'نظرة عامة'},inventory:{t:'رصيد المستودعات',s:'المخزون'},cart:{t:'سلة الصرف',s:'اصدار فواتير'},feed:{t:'تغذية المستودع',s:'اضافة مواد'},transfer:{t:'نقل بين المستودعات',s:'نقل داخلي'},zones:{t:'رصيد الزونات',s:'عرض المواد حسب الزون الجغرافي'},invoices:{t:'أرشيف الفواتير',s:'جميع الفواتير'},'direct-return':{t:'ارجاع مواد',s:'إرجاع مواد للمستودع مباشرة'},edit:{t:'تعديل فاتورة',s:'تعديل'},cancel:{t:'الغاء فاتورة',s:'الغاء مباشر'},requests:{t:'طلبات الارجاع / الالغاء / النقل',s:'الطلبات'},approve:{t:'اعتماد فواتير الصرف',s:'الاعتماد'},myinv:{t:'فواتيري',s:'فواتيرك الشخصية'},'inv-edit-req':{t:'طلب تعديل فاتورة صرف',s:'إرسال طلب تعديل فاتورة صرف'},boq:{t:'قسم BOQ',s:'البلاغات'},logs:{t:'سجل العمليات',s:'المراقبة'},contact:{t:'أرقام التواصل',s:'الدليل'},users:{t:'إدارة المستخدمين',s:'الصلاحيات'},settings:{t:'إعدادات النظام',s:'الإعدادات'},'warehouses-pg':{t:'إدارة المستودعات',s:'المستودعات'},'contractors-pg':{t:'إدارة المقاولين',s:'المقاولون'},'categories-pg':{t:'الفئات وحدود الإشعار',s:'إدارة الفئات'}};
// صفحات موجه البلاغات المسموح بها
const MOJTAHED_PAGES=['inventory','zones','cart','requests','myinv','logs','contact','direct-return','inv-edit-req'];
const WARDIA_PAGES=['inventory','zones','cart','transfer','direct-return','requests','myinv','logs','contact','inv-edit-req'];

function applySidebarRole(){
  if(!currentUser)return;
  const role=currentUser.role;
  const isMoj=role==='موجه بلاغات';
  const isW=role==='مشرف وردية';
  const isA=role==='أمين مستودع';
  const isAdmin=role==='مدير النظام';
  const roleKey=isAdmin?'admin':isA?'ameen':isMoj?'moj':isW?'wardia':'admin';

  // إظهار/إخفاء عناصر القائمة حسب data-roles
  document.querySelectorAll('.s-item[data-p]').forEach(function(el){
    const roles=(el.dataset.roles||'all');
    const show=roles==='all'||roles.split(',').indexOf(roleKey)>=0;
    el.style.display=show?'flex':'none';
  });

  // عنوان قسم الفواتير: "الادارة" للموجه
  var secInv=document.getElementById('snav-sec-inv');
  if(secInv)secInv.textContent=(isMoj||isW)?'الفواتير':'الفواتير';
  var secSys=document.getElementById('snav-sec-sys');
  if(secSys)secSys.textContent=(isMoj||isW)?'التواصل':'النظام';

  // إخفاء الأقسام (عنوان+فاصل) إذا لم يكن فيها عناصر مرئية
  ['ops','inv','req','entities'].forEach(function(k){
    var sec=document.getElementById('snav-sec-'+k);
    var div=document.getElementById('snav-div-'+k);
    if(!sec)return;
    var next=sec.nextElementSibling;
    var hasVis=false;
    while(next&&!next.classList.contains('s-sec')&&!next.classList.contains('s-div')){
      if(next.classList.contains('s-item')&&next.style.display!=='none')hasVis=true;
      next=next.nextElementSibling;
    }
    if(sec)sec.style.display=hasVis?'':'none';
    if(div)div.style.display=hasVis?'':'none';
  });

  // إخفاء تعريف مادة جديدة عن مشرف الوردية
  var btnAddItem=document.getElementById('btn-add-item');
  if(btnAddItem)btnAddItem.style.display=(isAdmin||isA)?'flex':'none';
  // زر إضافة جهة التواصل
  var btnContact=document.getElementById('btn-contact-new');
  if(btnContact)btnContact.style.display=isMoj?'none':'flex';

  // موظف الشهر في الشريط الجانبي
  if(isMoj||isW) renderEmpMonth();
}

function go(page){
  if(currentPage&&currentPage!==page)prevPage=currentPage;
  currentPage=page;
  // تحقق صلاحية الوصول للموجه
  const rolePages={"موجه بلاغات":MOJTAHED_PAGES,"مشرف وردية":WARDIA_PAGES,"أمين مستودع":['inventory','zones','cart','feed','myinv','logs']};
  const userPages=currentUser?.role?rolePages[currentUser.role]:null;
  if(userPages&&!userPages.includes(page)){
    toast('err','غير مصرح','ليس لديك صلاحية الوصول لهذه الصفحة','fa-lock');return;
  }
  document.querySelectorAll('.s-item').forEach(el=>el.classList.toggle('on',el.dataset.p===page));
  const info=PAGES[page]||PAGES.dashboard;
  document.getElementById('tb-title').textContent=info.t;
  document.getElementById('tb-sub').textContent=info.s;
  Object.keys(PAGES).forEach(p=>{const el=document.getElementById('pg-'+p);if(el)el.style.display='none';});
  const pg=document.getElementById('pg-'+page);
  if(pg){pg.style.display='block';pg.className='page-in';}
  const init={dashboard:renderDashboard,'direct-return':()=>{fillWhSelects();renderDrPage();},inventory:renderInventory,cart:()=>{fillWhSelects();renderCart();},feed:()=>{fillWhSelects();renderFeedHist();},transfer:()=>{fillWhSelects();renderTrHist();},invoices:renderArc,requests:()=>{fillWhSelects();renderRequests();},approve:()=>{fillWhSelects();renderApprovals();},myinv:renderMyInv,'inv-edit-req':()=>{fillWhSelects();var lc=document.getElementById('ier-list-card'),fc=document.getElementById('ier-form-card');if(lc)lc.style.display='block';if(fc)fc.style.display='none';renderIerList();},boq:renderBOQ,logs:renderLogs,contact:renderContacts,users:renderUsers,settings:renderSettings,zones:renderZonesPage,'warehouses-pg':function(){renderWarehouses();renderZonesManage();},'contractors-pg':renderContractors,'categories-pg':renderCategories};
  if(init[page])init[page]();
}
document.querySelectorAll('.s-item').forEach(el=>el.addEventListener('click',()=>go(el.dataset.p)));

// ══════════════════════ DASHBOARD ══════════════════════
function renderQuickActions(){
  const el=document.getElementById('quick-actions-grid');if(!el)return;
  const isM=currentUser?.role==='موجه بلاغات';
  const allActions=[
    {page:'cart',icon:'fa-cart-shopping',color:'var(--a1)',lbl:'صرف مواد',always:true},
    {page:'feed',icon:'fa-cubes',color:'var(--g1)',lbl:'تغذية',always:false},
    {page:'approve',icon:'fa-signature',color:'var(--y1)',lbl:'اعتماد',always:false},
    {page:'requests',icon:'fa-rotate-left',color:'var(--o1)',lbl:'ارجاع',always:true},
    {page:'cancel',icon:'fa-file-circle-xmark',color:'var(--r1)',lbl:'إلغاء',always:false},
    {page:'boq',icon:'fa-clipboard-list',color:'var(--a3)',lbl:'BOQ',always:true},
  ];
  const visible=allActions.filter(a=>a.always||!isM);
  el.innerHTML=visible.map(a=>`
    <div class="qa" onclick="go('${a.page}')">
      <i class="fa ${a.icon}" style="color:${a.color}"></i>
      <div class="qa-lbl">${a.lbl}</div>
    </div>`).join('');
}
function renderDashboard(){
  renderQuickActions();
  var whKeys=DB.warehouses.filter(function(w){return w.active;}).map(function(w){return w.key;});
  countUp('sv1',DB.inventory.reduce(function(s,i){return s+whKeys.reduce(function(ws,k){return ws+(i[k]||0);},0);},0));
  countUp('sv2',DB.invoices.length);
  // معلق الصرف = DB.approvals المعلقة
  countUp('sv3',DB.approvals.filter(a=>a.st==='معلق').length);
  // معلق الارجاع = طلبات الارجاع المعلقة في DB.requests
  countUp('sv4',DB.requests.filter(r=>r.st==='معلق'&&r.type==='ارجاع').length);
  document.getElementById('dash-inv-tbody').innerHTML=DB.invoices.slice(0,6).map(r=>`
    <tr onclick="showInvDetail('${r.no}')">
      <td class="mono">${r.no}</td><td>${tag(r.type)}</td><td>${r.wh}</td>
      <td style="max-width:80px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--t1)">${r.cont}</td>
      <td style="font-size:12px">${r.emp.split(' ').slice(0,2).join(' ')}</td>
      <td>${tag(r.st)}</td>
      <td style="font-size:11px;font-family:'JetBrains Mono',monospace;color:var(--t3)">${r.d}</td>
    </tr>`).join('');
  // التنبيهات
  const alerts=[];
  DB.inventory.filter(i=>i.manatiq<i.min).forEach(i=>alerts.push({t:'a-err',i:'fa-triangle-exclamation',h:i.name,b:'مستودع هيف بني مالك — '+i.manatiq+' وحدة فقط'}));
  if(DB.requests.filter(r=>r.st==='معلق').length)alerts.push({t:'a-warn',i:'fa-clock',h:DB.requests.filter(r=>r.st==='معلق').length+' طلبات ارجاع معلقة',b:'تحتاج مراجعة فورية'});
  if(DB.approvals.filter(a=>a.st==='معلق').length)alerts.push({t:'a-info',i:'fa-signature',h:DB.approvals.filter(a=>a.st==='معلق').length+' فواتير بانتظار الاعتماد',b:'راجع قسم الاعتماد'});
    var alertEl=document.getElementById('dash-alerts');
  if(alertEl){
    var aHtml='';
    alerts.slice(0,4).forEach(function(a){
      aHtml+='<div class="alert-item '+a.t+'"><i class="fa '+a.i+'"></i><div class="a-bd"><strong>'+a.h+'</strong><span>'+a.b+'</span></div></div>';
    });
    aHtml+='<button class="btn btn-sec btn-sm" style="width:100%;justify-content:center;margin-top:8px" onclick="showAllAlerts()"><i class="fa fa-list"></i>عرض مستوى جميع المواد</button>';
    alertEl.innerHTML=aHtml;
  }
    renderEmpMonth();
  document.getElementById('dash-acts').innerHTML=DB.logs.slice(0,7).map(function(l){return '<div class="act-item" onclick="go(\'logs\')"><div class="act-dot" style="background:'+l.c+'"></div><div class="act-inf"><div class="act-txt">'+(l.no?'['+l.no+'] ':'')+l.act+'</div><div class="act-meta">'+l.emp+' — '+l.wh+(l.cont?' — '+l.cont:'')+'</div></div><div class="act-time">'+l.t+'</div></div>';}).join('');
  renderEmpMonth();dashTopItems();dashRunningOut();dashOverdue();
  const chart=[{l:'احد',v:12},{l:'اثنين',v:8},{l:'ثلاثاء',v:19},{l:'اربعاء',v:7},{l:'خميس',v:15},{l:'جمعة',v:3},{l:'سبت',v:11}];
  const mx=Math.max(...chart.map(d=>d.v));
  document.getElementById('dash-chart').innerHTML=chart.map((d,i)=>`<div class="b-col"><div class="b-bar" data-v="${d.v}" style="height:${Math.round(d.v/mx*75)+5}px;background:${i===2?'linear-gradient(180deg,var(--a1),var(--a2))':'linear-gradient(180deg,rgba(0,212,255,.35),rgba(0,102,255,.2))'}"></div><div class="b-lbl">${d.l}</div></div>`).join('');
}
function countUp(id,target){let v=0;const el=document.getElementById(id);if(!el)return;const step=Math.max(1,Math.ceil(target/50));const t=setInterval(()=>{v=Math.min(v+step,target);el.textContent=v.toLocaleString('ar');if(v>=target)clearInterval(t);},18);}

// ══════════════════════ INVENTORY ══════════════════════
function renderInventory(){
  fillDL();fillWhSelects();
  const isM=currentUser?.role==='موجه بلاغات';
  const isW=currentUser?.role==='مشرف وردية';
  const addBtn=document.getElementById('btn-add-item');
  if(addBtn)addBtn.style.display=(isM||isW)?'none':'inline-flex';
  const q=(document.getElementById('inv-q')?.value||'').toLowerCase();
  const wh=document.getElementById('inv-wh')?.value||'';
  const cat=document.getElementById('inv-cat')?.value||'';
  const stk=document.getElementById('inv-stk')?.value||'';
  const whList=DB.warehouses.filter(function(w){return w.active;});
  const items=DB.inventory.filter(i=>{
    if(q&&!i.code.toLowerCase().includes(q)&&!i.name.toLowerCase().includes(q))return false;
    if(cat&&i.cat!==cat)return false;
    const tot=whList.reduce(function(s,w){return s+(i[w.key]||0);},0);
    if(stk==='lo'&&tot>5)return false;
    if(stk==='mid'&&(tot<=5||tot>15))return false;
    if(stk==='hi'&&tot<=15)return false;
    return true;
  });
  document.getElementById('inv-sub').textContent=items.length+' مادة';
  // تحديث رأس الجدول ديناميكياً
  var thead=document.querySelector('#inv-full-tbody')?.closest('table')?.querySelector('thead tr');
  if(thead){
    var whHeaders=whList.map(function(w){return '<th>'+w.name+'</th>';}).join('');
    thead.innerHTML='<th>كود المادة</th><th>اسم المادة</th><th>الفئة</th>'+whHeaders+'<th>الإجمالي</th><th>المستوى</th><th></th>';
  }
  const tbody=document.getElementById('inv-full-tbody');if(!tbody)return;
  tbody.innerHTML=items.map(i=>{
    const tot=whList.reduce(function(s,w){return s+(i[w.key]||0);},0);
    // إجمالي المحجوز والمتاح لكل المستودعات
    const totalReserved=whList.reduce(function(s,w){return s+getReservedStock(i.code,w.name);},0);
    const totalAvail=Math.max(0,tot-totalReserved);
    const pct=Math.min(Math.round(totalAvail/Math.max(tot,1)*100),100);
    const cls=tot===0?'stk-lo':totalAvail===0?'stk-lo':totalAvail<i.min?'stk-mid':'stk-hi';
    const bc=tot===0?'var(--r1)':totalAvail===0?'var(--r1)':totalAvail<i.min?'var(--y1)':'var(--g1)';
    const whCols=whList.map(function(w){
      var qty=i[w.key]||0;
      var res=getReservedStock(i.code,w.name);
      var av=Math.max(0,qty-res);
      var pendRet=getPendingReturnStock(i.code,w.name);
      var cell='';
      if(!wh||wh===w.name){
        var qColor=qty===0?'var(--r1)':av===0?'var(--r1)':qty<i.min?'var(--y1)':'var(--t1)';
        cell='<td class="mono" style="color:'+qColor+'">';
        cell+=qty;
        if(res>0) cell+='<br><span style="font-size:9px;color:var(--r1)">🔒'+res+'</span>';
        if(pendRet>0) cell+='<br><span style="font-size:9px;color:var(--g1)">↩+'+pendRet+'</span>';
        cell+='</td>';
      } else {
        cell='<td style="color:var(--t3)">—</td>';
      }
      return cell;
    }).join('');
    const totColor=tot===0?'var(--r1)':totalAvail===0?'var(--r1)':tot<i.min?'var(--y1)':'var(--a1)';
    const resCol='<td class="mono" style="font-weight:700;color:'+(totalReserved>0?'var(--r1)':'var(--t3)')+'">'+
      (totalReserved>0?'🔒'+totalReserved:'—')+'</td>';
    const availCol='<td class="mono" style="font-weight:800;color:'+(totalAvail===0?'var(--r1)':totalAvail<i.min?'var(--y1)':'var(--g1)')+'">'+
      totalAvail+'</td>';
    return '<tr onclick="invDetail(\''+i.code+'\')" style="cursor:pointer">'+
      '<td class="mono">'+i.code+'</td>'+
      '<td style="font-weight:600;color:var(--t1)">'+i.name+'</td>'+
      '<td>'+tag(i.cat)+'</td>'+
      whCols+
      '<td class="mono" style="font-weight:800;color:'+totColor+'">'+tot+'</td>'+
      resCol+availCol+
      '<td style="min-width:90px"><div style="font-size:9px;color:var(--t3);margin-bottom:2px">متاح '+pct+'%</div><div class="stock-bar"><div class="stock-bar-fill" style="width:'+pct+'%;background:'+bc+'"></div></div></td>'+
      '<td><button class="btn btn-sec btn-xs" onclick="event.stopPropagation();invDetail(\''+i.code+'\')"><i class="fa fa-info-circle"></i></button></td>'+
    '</tr>';
  }).join('');
}
// ══════════════════════════════════════════════
// INVENTORY ITEM MANAGEMENT — إدارة المواد
// ══════════════════════════════════════════════
function getCatOptions(selected=''){
  return DB.categories.map(cat=>`<option value="${cat.name}" ${cat.name===selected?'selected':''}>${cat.name}</option>`).join('');
}
function addInventoryItem(){
  showFormModal('<i class="fa fa-cube" style="color:var(--g1)"></i> تعريف مادة جديدة',`
    <div class="form-row c2">
      <div class="form-group">
        <label class="form-label"><i class="fa fa-barcode" style="color:var(--a1)"></i> كود المادة <span style="color:var(--r1)">*</span></label>
        <input class="form-input" id="ni-code" placeholder="908514012..." style="font-family:'JetBrains Mono',monospace;direction:ltr;text-align:left" oninput="this.value=this.value.replace(/[^A-Za-z0-9\-_]/g,'')">
        <div style="font-size:10px;color:var(--t3);margin-top:3px"><i class="fa fa-info-circle"></i> أحرف إنجليزية وأرقام فقط — لا مسافات</div>
      </div>
      <div class="form-group">
        <label class="form-label"><i class="fa fa-tag" style="color:var(--a1)"></i> اسم المادة <span style="color:var(--r1)">*</span></label>
        <input class="form-input" id="ni-name" placeholder="محول 100KVA...">
      </div>
      <div class="form-group" style="grid-column:span 2">
        <label class="form-label"><i class="fa fa-align-right" style="color:var(--t3)"></i> وصف المادة</label>
        <input class="form-input" id="ni-desc" placeholder="وصف تفصيلي للمادة...">
      </div>
      <div class="form-group" style="grid-column:span 2">
        <label class="form-label"><i class="fa fa-layer-group" style="color:var(--a3)"></i> الفئة <span style="color:var(--r1)">*</span></label>
        <select class="form-select" id="ni-cat">
          <option value="">-- اختر الفئة --</option>
          ${getCatOptions()}
        </select>
      </div>
    </div>
    <div style="margin-top:6px;background:rgba(0,212,255,.05);border:1px solid rgba(0,212,255,.15);border-radius:8px;padding:10px 12px;font-size:11.5px;color:var(--t2)">
      <i class="fa fa-info-circle" style="color:var(--a1)"></i>
      التنبيهات تُحدَّد حسب <strong>حدود الفئة</strong> — الكميات تُضاف عبر <strong>تغذية المستودع</strong>
    </div>`,
    [{lbl:'<i class="fa fa-save"></i> حفظ المادة',cls:'btn-primary',fn:()=>{
      const code=(document.getElementById('ni-code')?.value||'').trim();
      const name=(document.getElementById('ni-name')?.value||'').trim();
      const desc=(document.getElementById('ni-desc')?.value||'').trim();
      const cat=document.getElementById('ni-cat')?.value||'';
      if(!code){toast('err','حقل مطلوب','ادخل كود المادة','fa-barcode');return;}
      // التحقق من الكود: إنجليزي وأرقام فقط، لا مسافات، لا عربي
      if(!/^[A-Za-z0-9\-_]+$/.test(code)){
        toast('err','كود غير صحيح','كود المادة يجب أن يحتوي على أحرف إنجليزية وأرقام فقط (لا مسافات، لا عربي)','fa-ban');
        return;
      }
      if(!name){toast('err','حقل مطلوب','ادخل اسم المادة','fa-tag');return;}
      if(!cat){toast('err','حقل مطلوب','اختر فئة المادة','fa-layer-group');return;}
      if(DB.inventory.find(i=>i.code===code)){toast('err','كود مكرر','الكود <strong>'+code+'</strong> موجود مسبقاً في النظام — اختر كوداً آخر','fa-ban');return;}
      var newItem={code:code,name:name,desc:desc||'',cat:cat,min:0};
      DB.warehouses.filter(function(w){return w.key;}).forEach(function(w){newItem[w.key]=0;});
      DB.inventory.push(newItem);
      fillDL();closeModal('modal-form');renderInventory();
      toast('ok','✓ مادة جديدة','تم تعريف '+name+' ('+code+') بنجاح','fa-cube');
    }}]);
}
function editInventoryItem(code){
  if(currentUser?.role==='مشرف وردية'){toast('err','غير مصرح','ليس لديك صلاحية تعديل المواد','fa-lock');return;}
  const item=DB.inventory.find(i=>i.code===code);if(!item)return;
  showFormModal(`<i class="fa fa-pen" style="color:var(--y1)"></i> تعديل مادة`,`
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;padding:8px 12px;background:rgba(0,212,255,.05);border-radius:8px;border:1px solid var(--b1)">
      <span class="mono" style="color:var(--a1);font-size:14px;font-weight:700">${item.code}</span>
      <span style="color:var(--t3);font-size:12px">اسناد: ${item.asnad} | رايكو: ${item.raiko} | هيف بني مالك: ${item.manatiq}</span>
    </div>
    <div class="form-row c2">
      <div class="form-group">
        <label class="form-label"><i class="fa fa-barcode" style="color:var(--a1)"></i> كود المادة <span style="color:var(--r1)">*</span></label>
        <input class="form-input" id="ei-code" value="${item.code}" style="font-family:'JetBrains Mono',monospace">
      </div>
      <div class="form-group">
        <label class="form-label"><i class="fa fa-tag" style="color:var(--a1)"></i> اسم المادة <span style="color:var(--r1)">*</span></label>
        <input class="form-input" id="ei-name" value="${item.name}">
      </div>
      <div class="form-group" style="grid-column:span 2">
        <label class="form-label"><i class="fa fa-align-right" style="color:var(--t3)"></i> وصف المادة</label>
        <input class="form-input" id="ei-desc" value="${item.desc||''}">
      </div>
      <div class="form-group" style="grid-column:span 2">
        <label class="form-label"><i class="fa fa-layer-group" style="color:var(--a3)"></i> الفئة</label>
        <select class="form-select" id="ei-cat">${getCatOptions(item.cat)}</select>
      </div>
    </div>`,
    [{lbl:'<i class="fa fa-save"></i> حفظ',cls:'btn-primary',fn:()=>{
      const newCode=(document.getElementById('ei-code')?.value||'').trim();
      const name=(document.getElementById('ei-name')?.value||'').trim();
      const desc=(document.getElementById('ei-desc')?.value||'').trim();
      const cat=document.getElementById('ei-cat')?.value||item.cat;
      if(!name){toast('err','حقل مطلوب','ادخل اسم المادة','fa-tag');return;}
      if(!newCode){toast('err','حقل مطلوب','الكود لا يمكن أن يكون فارغاً','fa-barcode');return;}
      if(newCode!==item.code&&DB.inventory.find(i=>i.code===newCode)){toast('err','كود مكرر','هذا الكود مستخدم بالفعل','fa-ban');return;}
      if(newCode!==item.code) DB.invoices.forEach(inv=>inv.items.forEach(it=>{if(it.code===item.code)it.code=newCode;}));
      item.code=newCode;item.name=name;item.desc=desc;item.cat=cat;
      fillDL();closeModal('modal-form');renderInventory();
      toast('ok','✓ تم التعديل','تم تحديث '+name,'fa-save');
    }},{lbl:'<i class="fa fa-trash"></i> حذف المادة',cls:'btn-danger',fn:()=>{
      const tot=item.asnad+item.raiko+item.manatiq;
      if(tot>0){toast('err','لا يمكن الحذف','المادة لا تزال تحتوي على '+tot+' وحدة في المستودعات — أفرغها أولاً','fa-ban');return;}
      showConfirm(`<i class="fa fa-trash" style="color:var(--r1)"></i> حذف ${item.name}`,
        'هل تريد حذف <strong>'+item.name+'</strong> ('+item.code+') نهائياً من النظام؟',
        'حذف نهائي','btn-danger',()=>{
          DB.inventory=DB.inventory.filter(i=>i.code!==item.code);
          fillDL();closeModal('modal-form');renderInventory();
          toast('ok','حُذفت','تم حذف المادة '+item.name,'fa-trash');
        });
    }}]);
}

function fillCartFromInv(code,asnad,raiko,manatiq){
  // اختر المستودع الذي فيه رصيد
  const whEl=document.getElementById('cart-add-wh');
  const qEl=document.getElementById('cart-add-q');
  const qtyEl=document.getElementById('cart-add-qty');
  if(!qEl||!whEl||!qtyEl)return;
  // اختر المستودع تلقائياً حسب الرصيد الأعلى
  let bestWh='اسناد';
  const stocks=[['اسناد',parseInt(asnad)||0],['رايكو صبيا',parseInt(raiko)||0],['هيف بني مالك',parseInt(manatiq)||0]];
  stocks.sort((a,b)=>b[1]-a[1]);
  bestWh=stocks[0][1]>0?stocks[0][0]:'اسناد';
  qEl.value=code;
  whEl.value=bestWh;
  qtyEl.value=0;
  qtyEl.focus();qtyEl.select();
  go('cart');
  toast('info','اختر الكمية','تم تعبئة الكود والمستودع — أدخل الكمية يدوياً','fa-cart-plus');
}
function invDetail(code){
  var i=DB.inventory.find(function(x){return x.code===code;});if(!i)return;
  var activeWhs=DB.warehouses.filter(function(w){return w.active;});

  var whCards=activeWhs.map(function(w){
    var qty=i[w.key]||0;
    var reserved=getReservedStock(code,w.name);
    var avail=Math.max(0,qty-reserved);
    var pendRet=getPendingReturnStock(code,w.name);
    var qColor=qty<=(i.min||0)?'var(--r1)':qty<=(i.min||0)*2?'var(--y1)':'var(--a1)';
    var resDetails=buildReservationDetails(code,w.name);
    return '<div style="background:var(--bg2);border:1px solid '+(reserved>0?'rgba(239,68,68,.3)':'var(--b1)')+';border-radius:10px;padding:12px">'+
      '<div style="font-size:11px;font-weight:700;color:var(--t2);margin-bottom:8px;text-align:center">'+w.name+'</div>'+
      '<div style="display:flex;gap:6px;justify-content:center">'+
        '<div style="text-align:center;flex:1">'+
          '<div style="font-size:9px;color:var(--t3);margin-bottom:2px">الكلي</div>'+
          '<div style="font-size:22px;font-weight:900;font-family:monospace;color:'+qColor+'">'+qty+'</div>'+
        '</div>'+
        (reserved>0?
          '<div style="text-align:center;flex:1;background:rgba(239,68,68,.08);border-radius:6px;padding:4px">'+
            '<div style="font-size:9px;color:var(--r1);margin-bottom:2px">🔒 محجوز</div>'+
            '<div style="font-size:22px;font-weight:900;font-family:monospace;color:var(--r1)">'+reserved+'</div>'+
          '</div>'+
          '<div style="text-align:center;flex:1;background:rgba(16,185,129,.08);border-radius:6px;padding:4px">'+
            '<div style="font-size:9px;color:var(--g1);margin-bottom:2px">🔓 متاح</div>'+
            '<div style="font-size:22px;font-weight:900;font-family:monospace;color:var(--g1)">'+avail+'</div>'+
          '</div>'
        :'')+
      '</div>'+
      (pendRet>0?'<div style="margin-top:5px;text-align:center;font-size:10px;color:var(--g1);background:rgba(16,185,129,.06);border-radius:5px;padding:2px">↩ ارجاع معلق +'+pendRet+'</div>':'')+
      resDetails+
    '</div>';
  });

  var tot=activeWhs.reduce(function(s,w){return s+(i[w.key]||0);},0);
  var totRes=activeWhs.reduce(function(s,w){return s+getReservedStock(code,w.name);},0);
  var totAvail=Math.max(0,tot-totRes);

  document.getElementById('inv-detail-title').innerHTML='<i class="fa fa-box" style="color:var(--a1)"></i> '+i.name;
  document.getElementById('inv-detail-body').innerHTML=
    '<div style="display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap">'+
      '<div style="flex:1;min-width:70px;background:var(--bg2);border-radius:8px;padding:10px;text-align:center">'+
        '<div style="font-size:10px;color:var(--t3)">إجمالي الرصيد</div>'+
        '<div style="font-size:26px;font-weight:900;font-family:monospace;color:var(--a1)">'+tot+'</div>'+
      '</div>'+
      (totRes>0?
        '<div style="flex:1;min-width:70px;background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.2);border-radius:8px;padding:10px;text-align:center">'+
          '<div style="font-size:10px;color:var(--r1)">🔒 إجمالي محجوز</div>'+
          '<div style="font-size:26px;font-weight:900;font-family:monospace;color:var(--r1)">'+totRes+'</div>'+
        '</div>'+
        '<div style="flex:1;min-width:70px;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.2);border-radius:8px;padding:10px;text-align:center">'+
          '<div style="font-size:10px;color:var(--g1)">🔓 متاح للصرف</div>'+
          '<div style="font-size:26px;font-weight:900;font-family:monospace;color:var(--g1)">'+totAvail+'</div>'+
        '</div>':'')+
    '</div>'+
    '<div style="display:grid;grid-template-columns:repeat('+Math.min(activeWhs.length,3)+',1fr);gap:9px;margin-bottom:14px">'+
      whCards.join('')+
    '</div>'+
    '<div style="font-size:12px;color:var(--t2);display:flex;gap:12px;flex-wrap:wrap;padding:8px 0;border-top:1px solid var(--b1)">'+
      '<span>الكود: <span class="mono" style="color:var(--a1)">'+i.code+'</span></span>'+
      '<span>الفئة: '+tag(i.cat)+'</span>'+
      '<span>الحد الأدنى: <strong style="color:var(--r1)">'+i.min+'</strong></span>'+
    '</div>'+
    '<div style="margin-top:10px;display:flex;gap:7px;flex-wrap:wrap">'+
      (currentUser?.role!=='موجه بلاغات'&&currentUser?.role!=='مشرف وردية'?'<button class="btn btn-warn btn-sm" onclick="closeModal(\'modal-inv\');editInventoryItem(\''+code+'\')"><i class="fa fa-pen"></i>تعديل</button>':'')+
      '<button class="btn btn-green btn-sm" onclick="closeModal(\'modal-inv\');go(\'feed\')"><i class="fa fa-cubes"></i>تغذية</button>'+
      '<button class="btn btn-primary btn-sm" onclick="closeModal(\'modal-inv\');go(\'cart\')"><i class="fa fa-cart-shopping"></i>صرف</button>'+
      '<button class="btn btn-sec btn-sm" onclick="if(currentUser?.role===\'مشرف وردية\'){toast(\'err\',\'غير مصرح\',\'استخدم نموذج طلب النقل\',\'fa-lock\');}else{closeModal(\'modal-inv\');go(\'transfer\');}"><i class="fa fa-right-left"></i>نقل</button>'+
    '</div>';
  openModal('modal-inv');
}

function buildReservationDetails(code,wh){
  var items=getReservationsForItem(code,wh);
  if(!items.length) return '';
  return '<div style="margin-top:8px;border-top:1px solid var(--b1);padding-top:6px">'+
    '<div style="font-size:10px;color:var(--t3);margin-bottom:4px">تفاصيل الحجوزات:</div>'+
    items.map(function(r){
      return '<div style="display:flex;align-items:center;gap:6px;padding:2px 0;font-size:11px">'+
        '<i class="fa '+(r.type==='نقل'?'fa-right-left':'fa-cart-shopping')+'" style="color:'+r.color+';font-size:10px"></i>'+
        '<span class="mono" style="color:'+r.color+';font-weight:700">'+r.no+'</span>'+
        '<span style="color:var(--t3);flex:1">'+r.emp+'</span>'+
        '<span style="background:'+r.color+'22;color:'+r.color+';border-radius:4px;padding:1px 6px;font-weight:700;font-family:monospace">×'+r.qty+'</span>'+
      '</div>';
    }).join('')+
  '</div>';
}


// ══════════════════════ CART ══════════════════════
function cartAdd(){
  fillDL();
  const q=(document.getElementById('cart-add-q')?.value||'').trim();
  const wh=document.getElementById('cart-add-wh')?.value||'اسناد';
  const qty=parseInt(document.getElementById('cart-add-qty')?.value)||0;
  if(qty===0){toast('err','أدخل الكمية','الكمية يجب أن تكون أكبر من صفر','fa-triangle-exclamation');return;}
  if(!q){toast('err','حقل مطلوب','ادخل كود او اسم المادة','fa-triangle-exclamation');return;}
  const found=validateItemExists(q);
  if(!found)return;
  const realStock=getStock(found.code,wh);
  const reserved=getReservedStock(found.code,wh);
  const avail=Math.max(0,realStock-reserved);
  if(realStock===0){toast('err','لا يوجد رصيد',found.name+' غير متوفر في '+wh+' (الرصيد: 0)','fa-warehouse');return;}
  if(avail===0){toast('err','الرصيد محجوز',found.name+' — الرصيد '+realStock+' محجوز بفواتير معلقة','fa-clock');return;}
  if(qty>avail){
    var pendRet=getPendingReturnStock(found.code,wh);
    var msg='المتاح في '+wh+': '+avail;
    if(reserved>0) msg+=' (محجوز: '+reserved+')';
    if(pendRet>0) msg+=' — ارجاع معلق: +'+pendRet+' (بانتظار اعتماد)';
    toast('warn','كمية أكثر من المتاح',msg,'fa-triangle-exclamation');return;
  }
  const ex=cart.find(c=>c.code===found.code&&c.wh===wh);
  if(ex)ex.qty=Math.min(ex.qty+qty,avail);
  else cart.push({code:found.code,name:found.name,wh,qty,max:avail,realMax:realStock});
  document.getElementById('cart-add-q').value='';
  document.getElementById('cart-add-qty').value=1;
  renderCart();
  toast('ok','اضيفت',found.name+' x'+qty+' — '+wh,'fa-cart-shopping');
}
function cartQty(idx,delta){cart[idx].qty=Math.max(1,Math.min(cart[idx].max,cart[idx].qty+delta));renderCart();}
function cartRemove(idx){cart.splice(idx,1);renderCart();toast('info','حذف','تمت إزالة المادة من السلة','fa-trash');}
function cartClear(){
  if(!cart.length)return;
  showConfirm('<i class="fa fa-trash" style="color:var(--r1)"></i> مسح السلة','هل تريد مسح جميع المواد من السلة؟','مسح','btn-danger',()=>{cart=[];renderCart();toast('info','مسح','تم مسح السلة','fa-trash');});
}
function cartIssue(){
  if(!cart.length){toast('err','السلة فارغة','اضف مواد للسلة اولاً','fa-cart-shopping');return;}
  const cont=(document.getElementById('cart-contractor')?.value||'').trim();
  if(!cont){
    document.getElementById('cart-contractor').classList.add('err');
    document.getElementById('cart-contractor').focus();
    toast('err','حقل مطلوب','ادخل اسم المقاول','fa-user');return;
  }
  document.getElementById('cart-contractor').classList.remove('err');
  const boq=(document.getElementById('cart-boq')?.value||'').trim();
  if(!boq){
    document.getElementById('cart-boq').classList.add('err');
    document.getElementById('cart-boq').focus();
    toast('err','حقل مطلوب','رقم BOQ إجباري عند الصرف','fa-clipboard-list');return;
  }
  document.getElementById('cart-boq').classList.remove('err');
  const no=genInvNo('صرف');
  const notes=(document.getElementById('cart-notes')?.value||'').trim();
  if(!notes){
    document.getElementById('cart-notes').classList.add('err');
    document.getElementById('cart-notes').focus();
    toast('err','وصف العمل مطلوب','يرجى إدخال وصف العمل قبل إصدار الفاتورة','fa-triangle-exclamation');
    return;
  }
  document.getElementById('cart-notes').classList.remove('err');
  const wh=cart[0].wh;
  const items=cart.map(c=>({code:c.code,name:c.name,qty:c.qty}));

  // مدير النظام وأمين المستودع → معتمد فوراً + خصم فوري
  // موجه البلاغات ومشرف الوردية → معلق، لا خصم حتى الاعتماد
  const needsApproval = currentUser.role === 'موجه بلاغات' || currentUser.role === 'مشرف وردية';
  const invStatus = needsApproval ? 'معلق' : 'معتمد';

  // خصم الرصيد فقط للمعتمد فوراً
  if(!needsApproval){
    cart.forEach(cc=>setStock(cc.code,cc.wh,-cc.qty));
  }
  // للموجه: تحقق مرة أخيرة من الرصيد المتاح (قد يتغير بين cartAdd والإصدار)
  if(needsApproval){
    for(const cc of cart){
      const avail=getAvailableStock(cc.code,cc.wh);
      if(cc.qty>avail){
        toast('err','رصيد غير كافٍ','تغير الرصيد المتاح لـ '+cc.name+' — المتاح الآن: '+avail,'fa-triangle-exclamation');
        return;
      }
    }
  }

  DB.invoices.unshift({no,type:'صرف',wh,emp:currentUser.name,cont,st:invStatus,d:today(),items,notes,boq});
  const itemsDetail2=items.map(function(it){return it.code+' '+it.name+' x'+it.qty;}).join(' | ');
  addLog('صرف','فاتورة '+no+' — '+cont+(boq?' — BOQ:'+boq:'')+' — '+itemsDetail2,wh,{
    no:no,type:'صرف',cont:cont,boq:boq,
    items:itemsDetail2,
    receiver:cont,
    sender:currentUser?currentUser.name:'—',
    wh:wh,date:today(),st:invStatus
  });

  const summary=items.map(i=>i.name+'x'+i.qty).join('، ');

  if(needsApproval){
    DB.approvals.unshift({id:Date.now(),no,emp:currentUser.name,wh,cont,
      items:items,
      itemsStr:items.map(i=>i.name+' x'+i.qty).join(' + '),
      boq:boq,notes:notes,d:today(),time:nowTime(),st:'معلق'});
    addNotif('info','فاتورة '+no+' تنتظر الاعتماد',currentUser.name+' — '+cont,'fa-signature',null);
    updateBadges();
    toast('ok','✓ فاتورة '+no+' صادرة',summary+' — بانتظار اعتماد المدير (الكمية محجوزة)','fa-file-invoice');
  } else {
    addNotif('ok','✓ فاتورة '+no+' معتمدة تلقائياً',summary+' — '+cont,'fa-file-invoice',currentUser.name);
    updateBadges();
    toast('ok','✓ فاتورة '+no+' معتمدة',summary+' — صدرت واعتمدت فوراً','fa-circle-check');
  }

  cart=[];
  ['cart-contractor','cart-boq','cart-notes'].forEach(id=>{const e=document.getElementById(id);if(e)e.value='';});
  renderCart();
  // معاينة الفاتورة فور الإصدار للجميع
  setTimeout(()=>printInvoice(no),300);
  // موجه البلاغات: انتقل أيضاً لـ "فواتيري"
  if(needsApproval){
    setTimeout(()=>go('myinv'),350);
  }
}
function renderCart(){
  fillDL();
  const el=document.getElementById('cart-rows');if(!el)return;
  document.getElementById('c-count').textContent=cart.length;
  document.getElementById('c-total').textContent=cart.reduce((s,c)=>s+c.qty,0)+' وحدة';
  document.getElementById('c-no').textContent=genInvNo('صرف');
  // تحديث شارة الاعتماد
  const badge=document.getElementById('cart-approval-badge');
  if(badge){
    const isM=currentUser?.role==='موجه بلاغات';
    badge.innerHTML=`<div style="padding:8px 10px;border-radius:8px;font-size:11.5px;display:flex;align-items:center;gap:7px;${isM?'background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.25);color:#fbbf24':'background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.25);color:#34d399'}">
      <i class="fa ${isM?'fa-clock':'fa-circle-check'}"></i>
      ${isM?'تحتاج اعتماد المدير بعد الإصدار (الكمية محجوزة)':'تُعتمد الفاتورة فوراً عند الإصدار'}
    </div>`;
  }
  if(!cart.length){el.innerHTML=`<div class="empty-state"><i class="fa fa-cart-shopping"></i><p>السلة فارغة — ابحث عن مادة واضفها</p></div>`;return;}
  el.innerHTML=cart.map((c,i)=>`
    <div class="cart-item-row">
      <div class="ci-info">
        <div class="ci-code">${c.code}</div>
        <div class="ci-name">${c.name}</div>
        <div class="ci-wh"><i class="fa fa-warehouse" style="color:var(--t3)"></i> ${c.wh} <span class="ci-max">— متاح: ${c.max} (من إجمالي: ${c.realMax||c.max})</span></div>
      </div>
      <div class="qty-ctrl">
        <div class="qbtn" onclick="cartQty(${i},-1)">−</div>
        <div class="qval">${c.qty}</div>
        <div class="qbtn" onclick="cartQty(${i},1)">+</div>
      </div>
      <div class="ci-del" onclick="cartRemove(${i})"><i class="fa fa-trash"></i></div>
    </div>`).join('');
}

// ══════════════════════ FEED ══════════════════════
function doFeed(){
  const code=(document.getElementById('feed-code')?.value||'').trim();
  const name=(document.getElementById('feed-name')?.value||'').trim();
  const wh=document.getElementById('feed-wh')?.value||'اسناد';
  const qty=parseInt(document.getElementById('feed-qty')?.value)||0;
  const src=getFeedSrc()||'مستودع السعودية للطاقة';
  const po=(document.getElementById('feed-po')?.value||'').trim();
  if(!code){document.getElementById('feed-code').classList.add('err');toast('err','حقل مطلوب','ادخل كود المادة','fa-triangle-exclamation');return;}
  if(!qty||qty<1){document.getElementById('feed-qty').classList.add('err');toast('err','كمية غير صحيحة','ادخل كمية اكبر من صفر','fa-triangle-exclamation');return;}
  ['feed-code','feed-qty'].forEach(id=>document.getElementById(id).classList.remove('err'));
  setStock(code,wh,qty);
  feedHistory.unshift({code,name:name||code,wh,qty,src,po,d:today(),t:nowTime()});
  addLog('تغذية','تغذية '+qty+' وحدة | '+code+' | '+wh+(po?' | PO:'+po:''),wh,{code:code,qty:qty,src:src,po:po,date:today()});
  ['feed-code','feed-name','feed-qty','feed-po','feed-notes'].forEach(id=>{const e=document.getElementById(id);if(e)e.value='';});
  renderFeedHist();
  toast('ok','✓ تغذية ناجحة','تم اضافة '+qty+' وحدة من '+(name||code)+' الى '+wh,'fa-cubes');
}
function renderFeedHist(){
  const el=document.getElementById('feed-hist');if(!el)return;
  if(!feedHistory.length){el.innerHTML=`<div class="empty-state"><i class="fa fa-history"></i><p>لا توجد تغذيات حتى الان</p></div>`;return;}
  el.innerHTML=feedHistory.slice(0,8).map(f=>`
    <div class="hist-item">
      <div class="hist-ico" style="background:rgba(16,185,129,.1);color:var(--g1)"><i class="fa fa-cubes"></i></div>
      <div class="hist-info"><div class="hist-code" style="color:var(--g1)">${f.code}</div><div class="hist-name">${f.name}</div><div class="hist-meta">${f.wh} — ${f.src} — ${f.d} ${f.t}</div></div>
      <div class="hist-qty" style="color:var(--g1)">+${f.qty}</div>
    </div>`).join('');
}

// ══════════════════════ TRANSFER ══════════════════════
// ── مواد النقل ──
let trItems=[];
function trCheckWh(){
  const from=document.getElementById('tr-from')?.value;
  const to=document.getElementById('tr-to')?.value;
  if(from===to)toast('warn','تنبيه','المستودع المصدر والوجهة متطابقان','fa-triangle-exclamation');
  if(trItems.length)renderTrItems();
}
function trAutoFill(){
  const code=(document.getElementById('tr-add-code')?.value||'').trim();
  const nameEl=document.getElementById('tr-add-name');
  const stockEl=document.getElementById('tr-add-stock');
  const from=document.getElementById('tr-from')?.value||'اسناد';
  const item=DB.inventory.find(i=>i.code===code||i.name===code);
  if(item){
    if(nameEl)nameEl.value=item.name;
    const avail=getAvailableStock(item.code,from);
    const total=getStock(item.code,from);
    if(stockEl)stockEl.innerHTML=`<i class="fa fa-warehouse" style="color:var(--g1)"></i> متوفر في <strong>${from}</strong>: <span style="color:var(--a1);font-family:'JetBrains Mono',monospace;font-weight:700">${avail}</span> وحدة ${total!==avail?`<span style="color:var(--t3)">(إجمالي: ${total})</span>`:''}${item.desc?`<br><i class="fa fa-info-circle" style="color:var(--t3)"></i> <span style="color:var(--t3)">${item.desc}</span>`:''}`;
  } else {
    if(nameEl)nameEl.value='';
    if(stockEl)stockEl.innerHTML=code?'<span style="color:var(--r1)"><i class="fa fa-triangle-exclamation"></i> المادة غير موجودة</span>':'';
  }
}
function trAddItem(){
  fillDL();
  const code=(document.getElementById('tr-add-code')?.value||'').trim();
  const qty=parseInt(document.getElementById('tr-add-qty')?.value)||0;
  const from=document.getElementById('tr-from')?.value||'اسناد';
  const to=document.getElementById('tr-to')?.value||'هيف بني مالك';
  if(from===to){toast('err','خطأ','المستودع المصدر والوجهة متطابقان','fa-ban');return;}
  if(!code){toast('err','حقل مطلوب','ادخل كود المادة','fa-barcode');return;}
  if(qty<1){toast('err','كمية غير صحيحة','الكمية يجب أن تكون أكبر من صفر','fa-triangle-exclamation');return;}
  const item=validateItemExists(code);
  if(!item)return;
  const avail=getAvailableStock(item.code,from);
  if(qty>avail){toast('err','رصيد غير كافٍ','المتوفر في '+from+': '+avail+' فقط','fa-warehouse');return;}
  const ex=trItems.find(t=>t.code===item.code);
  if(ex){
    if(ex.qty+qty>avail){toast('warn','تجاوز الرصيد','الكمية الإجمالية تتجاوز المتوفر','fa-triangle-exclamation');return;}
    ex.qty+=qty;
  } else {
    trItems.push({code:item.code,name:item.name,desc:item.desc||'',qty,max:avail});
  }
  document.getElementById('tr-add-code').value='';
  document.getElementById('tr-add-name').value='';
  document.getElementById('tr-add-qty').value=1;
  document.getElementById('tr-add-stock').innerHTML='';
  renderTrItems();
  toast('ok','أُضيفت',item.name+' x'+qty,'fa-box');
}
function renderTrItems(){
  const from=document.getElementById('tr-from')?.value||'اسناد';
  const el=document.getElementById('tr-items-list');if(!el)return;
  if(!trItems.length){el.innerHTML='<div style="text-align:center;color:var(--t3);font-size:12px;padding:10px 0">أضف مواد للنقل أدناه</div>';return;}
  el.innerHTML=trItems.map((it,i)=>`
    <div class="cart-item-row" style="margin-bottom:6px">
      <div class="ci-info">
        <div class="ci-code">${it.code}</div>
        <div class="ci-name">${it.name}</div>
        ${it.desc?`<div style="font-size:10px;color:var(--t3)">${it.desc}</div>`:''}
        <div style="font-size:10px;color:var(--t3)">متوفر في ${from}: ${it.max}</div>
      </div>
      <div class="qty-ctrl">
        <div class="qbtn" onclick="trQty(${i},-1)">−</div>
        <div class="qval">${it.qty}</div>
        <div class="qbtn" onclick="trQty(${i},1)">+</div>
      </div>
      <div class="ci-del" onclick="trItems.splice(${i},1);renderTrItems()"><i class="fa fa-trash"></i></div>
    </div>`).join('');
}
function trQty(i,d){
  const it=trItems[i];
  it.qty=Math.max(1,Math.min(it.max,it.qty+d));
  renderTrItems();
}
function doTransfer(){
  // مشرف الوردية: يُحفظ كطلب اعتماد
  if(currentUser?.role==='مشرف وردية'){doTransferRequest();return;}
  const from=document.getElementById('tr-from')?.value;
  const to=document.getElementById('tr-to')?.value;
  const reason=document.getElementById('tr-reason')?.value||'—';
  const notes=(document.getElementById('tr-notes')?.value||'').trim();
  if(from===to){toast('err','خطأ','لا يمكن النقل من والى نفس المستودع','fa-triangle-exclamation');return;}
  if(!trItems.length){toast('err','لا توجد مواد','أضف مادة واحدة على الأقل للنقل','fa-box');return;}
  // تحقق نهائي من الرصيد
  for(const it of trItems){
    const avail=getAvailableStock(it.code,from);
    if(it.qty>avail){toast('err','رصيد غير كافٍ','تغير الرصيد — '+it.name+': متوفر '+avail+' فقط','fa-warehouse');return;}
  }
  const no=genInvNo('نقل');
  const items=trItems.map(it=>({code:it.code,name:it.name,qty:it.qty}));
  // تنفيذ النقل
  trItems.forEach(it=>{setStock(it.code,from,-it.qty);setStock(it.code,to,it.qty);});
  DB.invoices.unshift({no,type:'نقل',wh:to,emp:currentUser.name,cont:from,st:'معتمد',d:today(),items,notes:reason+(notes?' — '+notes:''),boq:''});
  trHistory.unshift({no,from,to,items:items.map(it=>it.name+' x'+it.qty).join(' + '),d:today(),t:nowTime()});
  addLog('نقل','نقل '+no+' ('+items.length+' أصناف): '+from+' الى '+to,to);
  const summary=items.map(it=>it.name+' x'+it.qty).join('، ');
  trItems=[];
  document.getElementById('tr-notes').value='';
  renderTrItems();renderTrHist();
  toast('ok','✓ نقل '+no+' ناجح',summary+' — '+from+' → '+to,'fa-right-left');
}
function renderTrHist(){
  const el=document.getElementById('tr-hist');if(!el)return;
  if(!trHistory.length){el.innerHTML=`<div class="empty-state"><i class="fa fa-right-left"></i><p>لا توجد نقليات حتى الان</p></div>`;return;}
  el.innerHTML=trHistory.slice(0,8).map(t=>`
    <div class="hist-item">
      <div class="hist-ico" style="background:rgba(0,212,255,.1);color:var(--a1)"><i class="fa fa-right-left"></i></div>
      <div class="hist-info"><div class="hist-code" style="color:var(--a1)">${t.no}</div><div class="hist-name">${t.items}</div><div class="hist-meta">${t.from} → ${t.to} — ${t.d} ${t.t}</div></div>
    </div>`).join('');
}

// ══════════════════════ INVOICES ARCHIVE ══════════════════════
function initArcChips(){
  var el=document.getElementById('inv-arc-chips');if(!el)return;
  var types=['الكل','صرف','ارجاع','نقل','الغاء'];
  el.innerHTML=types.map(function(t){return '<button class="fchip '+((t==='الكل'&&arcFilter==='all')||(t===arcFilter)?'on':'')+'" onclick="setArcFilter(\''+(t==='الكل'?'all':t)+'\',this)">'+t+'</button>';}).join('');
}
function setArcFilter(f,btn){arcFilter=f;document.querySelectorAll('#inv-arc-chips .fchip').forEach(b=>b.classList.remove('on'));btn.classList.add('on');renderArc();}
// ══ متغير التاب الحالي ══
var arcTab='all'; // all | active | cancelled

function arcSetTab(tab){
  arcTab=tab;
  var tabs={all:'arc-tab-all',active:'arc-tab-active',cancelled:'arc-tab-cancelled'};
  Object.keys(tabs).forEach(function(k){
    var btn=document.getElementById(tabs[k]);if(!btn)return;
    var isActive=k===tab;
    btn.style.background=isActive?'rgba(0,212,255,.12)':'rgba(255,255,255,.04)';
    btn.style.borderColor=isActive?'var(--a1)':'var(--b1)';
    btn.style.color=isActive?'var(--a1)':'var(--t2)';
  });
  renderArc();
}

function renderArc(){
  initArcChips();
  var q=(document.getElementById('inv-arc-q')?.value||'').toLowerCase();
  var wh=document.getElementById('inv-arc-wh')?.value||'';
  var st=document.getElementById('inv-arc-st')?.value||'';
  var emp=document.getElementById('inv-arc-emp')?.value||'';
  var dt=document.getElementById('inv-arc-date')?.value||'';
  // تعبئة قائمة الموجهين
  var empSel=document.getElementById('inv-arc-emp');
  if(empSel){
    var curEmp=empSel.value;
    var emps=[...new Set(DB.invoices.map(function(i){return i.emp;}))].sort();
    empSel.innerHTML='<option value="">كل الموجهين</option>'+emps.map(function(e){return '<option value="'+e+'"'+(e===curEmp?' selected':'')+'>'+e+'</option>';}).join('');
  }
  // تطبيق التاب
  var base=DB.invoices.filter(function(i){
    // الأرشيف يعرض المعتمدة والمرفوضة والملغية فقط — المعلقة لها قسمها
    if(i.st==='معلق') return false;
    if(arcTab==='active') return i.type==='صرف'||i.type==='نقل'||i.type==='ارجاع';
    if(arcTab==='cancelled') return i.st==='ملغي';
    return true;
  });
  var items=base.filter(function(i){
    if(arcFilter!=='all'&&i.type!==arcFilter)return false;
    if(q&&!i.no.toLowerCase().includes(q)&&!i.emp.toLowerCase().includes(q)&&!(i.cont||'').toLowerCase().includes(q))return false;
    if(wh&&i.wh!==wh)return false;
    if(st&&i.st!==st)return false;
    if(emp&&i.emp!==emp)return false;
    if(dt&&i.d!==dt)return false;
    return true;
  });
  document.getElementById('inv-arc-sub').textContent=items.length+' فاتورة';

  // إحصائيات
  var statsEl=document.getElementById('inv-arc-stats');
  if(statsEl){
    var counts={معتمد:0,معلق:0,مرفوض:0,ملغي:0};
    items.forEach(function(i){if(counts[i.st]!==undefined)counts[i.st]++;});
    var statsHtml=[
      {l:'معتمد',c:'var(--g1)',b:'rgba(16,185,129,.08)',n:counts.معتمد},
      {l:'معلق',c:'var(--y1)',b:'rgba(245,158,11,.08)',n:counts.معلق},
      {l:'مرفوض',c:'var(--o1)',b:'rgba(249,115,22,.08)',n:counts.مرفوض},
      {l:'ملغي',c:'var(--r1)',b:'rgba(239,68,68,.08)',n:counts.ملغي}
    ].filter(function(s){return s.n>0;}).map(function(s){
      return '<div style="background:'+s.b+';border:1px solid '+s.c+'33;border-radius:9px;padding:6px 14px;display:flex;align-items:center;gap:8px">'+
        '<span style="font-size:16px;font-weight:800;color:'+s.c+';font-family:monospace">'+s.n+'</span>'+
        '<span style="font-size:11px;color:var(--t2)">'+s.l+'</span>'+
      '</div>';
    }).join('');
    statsEl.innerHTML=statsHtml;
  }

  var tbody=document.getElementById('inv-arc-tbody');if(!tbody)return;
  if(!items.length){
    tbody.innerHTML='<tr><td colspan="8" style="text-align:center;padding:24px;color:var(--t3)"><i class="fa fa-search"></i> لا توجد نتائج</td></tr>';
    return;
  }

  var isAdmin=currentUser?.role==='مدير النظام'||currentUser?.role==='أمين مستودع';
  tbody.innerHTML=items.map(function(r){
    var stColor=r.st==='معتمد'?'var(--g1)':r.st==='معلق'?'var(--y1)':r.st==='ملغي'?'var(--r1)':'var(--o1)';
    var actionBtns=
      '<button class="btn btn-sec btn-xs" onclick="event.stopPropagation();showInvDetail(\''+r.no+'\')"><i class="fa fa-eye"></i></button>'+
      '<button class="btn btn-primary btn-xs" onclick="event.stopPropagation();printInvoice(\''+r.no+'\')"><i class="fa fa-print"></i></button>';
    if(isAdmin){
      if(r.st!=='ملغي'){
        if(r.type!=='الغاء') actionBtns+='<button class="btn btn-warn btn-xs" onclick="event.stopPropagation();arcEditInvoice(\''+r.no+'\')" title="تعديل"><i class="fa fa-pen"></i></button>';
      }
      if(r.st==='ملغي'){
        actionBtns+='<button class="btn btn-green btn-xs" onclick="event.stopPropagation();arcRestoreInvoice(\''+r.no+'\')" title="إعادة تفعيل"><i class="fa fa-rotate-left"></i> استعادة</button>';
      }
      if(r.st==='معتمد'||r.st==='معلق'){
        actionBtns+='<button class="btn btn-danger btn-xs" onclick="event.stopPropagation();arcCancelInvoice(\''+r.no+'\')" title="إلغاء"><i class="fa fa-ban"></i></button>';
      }
    }
    return '<tr style="cursor:pointer" onclick="showInvDetail(\''+r.no+'\')">'+
      '<td class="mono" style="color:var(--a1);font-weight:700">'+r.no+'</td>'+
      '<td>'+tag(r.type)+'</td>'+
      '<td style="font-size:12px">'+r.wh+'</td>'+
      '<td style="color:var(--t1);font-size:12px">'+r.emp.split(' ').slice(0,2).join(' ')+'</td>'+
      '<td style="font-size:12px">'+(r.cont||'—')+'</td>'+
      '<td><span style="font-size:11px;font-weight:700;color:'+stColor+'">'+r.st+'</span></td>'+
      '<td style="font-size:11px;font-family:\'JetBrains Mono\',monospace;color:var(--t3)">'+r.d+'</td>'+
      '<td onclick="event.stopPropagation()"><div style="display:flex;gap:4px;flex-wrap:wrap">'+actionBtns+'</div></td>'+
    '</tr>';
  }).join('');
}

// ══ إجراءات الأرشيف للمدير ══
function arcEditInvoice(no){
  closeModal('modal-inv');
  adminEditInvoice(no,'archive');
}

function arcCancelInvoice(no){
  var inv=DB.invoices.find(function(i){return i.no===no;});
  if(!inv)return;
  var wasApproved=inv.st==='معتمد';
  showConfirm(
    '<i class="fa fa-ban" style="color:var(--r1)"></i> إلغاء فاتورة '+no,
    'إلغاء الفاتورة <strong>'+no+'</strong> ('+inv.type+')?'+
    (wasApproved?'<br><span style="color:var(--y1);font-size:12px">⚠ سيتم إعادة المواد للمستودع '+inv.wh+'</span>':''),
    'تأكيد الإلغاء','btn-danger',function(){
      // إعادة المواد للمستودع فقط إذا كانت معتمدة
      if(wasApproved){
        (inv.items||[]).forEach(function(it){setStock(it.code,inv.wh,+it.qty);});
      }
      // وضع ختم الإلغاء
      inv.cancelled   = true;
      inv.cancelledBy = currentUser.name;
      inv.cancelDate  = today();
      inv.cancelNote  = 'إلغاء مباشر من الأرشيف';
      syncInvoiceStatus(no,'ملغي');
      addLog('الغاء','إلغاء مباشر للفاتورة '+no+' من الأرشيف',inv.wh,{no:no,cont:inv.cont});
      addNotif('err','تم إلغاء فاتورة '+no,currentUser.name+' — أُلغيت '+(wasApproved?'وأُعيدت المواد للمستودع':''),'fa-ban',inv.emp);
      closeModal('modal-inv');
      // الانتقال لتاب الملغية
      arcTab='cancelled';renderArc();
      toast('ok','✓ تم الإلغاء','الفاتورة '+no+' في قسم الملغية'+(wasApproved?' — أُعيدت المواد للمستودع':''),'fa-ban');
    });
}

function arcRestoreInvoice(no){
  var inv=DB.invoices.find(function(i){return i.no===no;});
  if(!inv)return;
  // لا استعادة إذا أُلغيت عبر طلب معتمد من الموجه
  var approvedCancelReq=DB.requests.find(function(r){
    return (r.origInv===no||r.no===no) && r.type==='الغاء' && r.st==='معتمد';
  });
  if(approvedCancelReq){
    toast('err','غير مسموح','هذه الفاتورة أُلغيت بطلب معتمد — لا يمكن استعادتها','fa-ban');
    return;
  }
  var typeLabel = inv.type==='صرف'?'الصرف':inv.type==='ارجاع'?'الارجاع':inv.type==='نقل'?'النقل':'الفاتورة';
  showConfirm(
    '<i class="fa fa-rotate-left" style="color:var(--g1)"></i> استعادة فاتورة '+no,
    'استعادة فاتورة <strong>'+no+'</strong> ('+inv.type+') وإلغاء ختم الإلغاء عنها؟'+
    '<br><span style="color:var(--a1);font-size:12px">ستعود الفاتورة <strong>معلقة</strong> بانتظار الاعتماد — بدون خصم من المخزون</span>',
    'استعادة','btn-green',function(){
      // إزالة ختم الإلغاء وإعادة الفاتورة معلقة
      inv.cancelled   = false;
      inv.cancelledBy = null;
      inv.cancelDate  = null;
      inv.cancelNote  = null;
      // حذف طلب الإلغاء المرتبط إن وجد (غير معتمد)
      DB.requests = DB.requests.filter(function(r){
        return !((r.origInv===no||r.no===no) && r.type==='الغاء' && r.st!=='معتمد');
      });
      // حذف من approvals إن وجد
      DB.approvals = DB.approvals.filter(function(a){
        return !(a.no===no && a.type==='الغاء');
      });
      // تزامن الحالة: معلق
      syncInvoiceStatus(no,'معلق');
      addLog('استعادة','استعادة فاتورة '+inv.type+' ملغية '+no+' — أصبحت معلقة بانتظار الاعتماد',inv.wh,{no:no,cont:inv.cont});
      addNotif('ok','✓ استعادة فاتورة '+no,'تمت الاستعادة — الفاتورة معلقة بانتظار الاعتماد','fa-rotate-left',inv.emp);
      closeModal('modal-inv');
      renderArc();
      toast('ok','✓ استُعيدت '+no,'الفاتورة معلقة الآن — يمكن اعتمادها أو تعديلها','fa-circle-check');
    });
}
function showInvDetail(no){
  // دائماً اقرأ الحالة الأحدث من DB مباشرة
  let inv=DB.invoices.find(i=>i.no===no);
  let fromApproval=false;
  if(!inv){
    const a=DB.approvals.find(x=>x.no===no);
    if(a){
      fromApproval=true;
      var parsedItems=[];
      if(Array.isArray(a.items)) parsedItems=a.items;
      else if(typeof a.items==='string'){
        parsedItems=a.items.split(' + ').map(function(s){
          var m=s.match(/(.+) x(\d+)/);
          return m?{code:'—',name:m[1],qty:parseInt(m[2])}:{code:'—',name:s,qty:0};
        });
      }
      inv={no:a.no,type:'صرف',wh:a.wh,cont:a.cont,emp:a.emp,st:a.st,d:a.d,
           items:parsedItems,boq:a.boq||'',notes:a.notes||''};
    }
  }
  if(!inv){toast('err','غير موجودة','لا توجد فاتورة بهذا الرقم في النظام','fa-ban');return;}
  // تلوين الحالة
  var stColor=inv.st==='معتمد'?'var(--g1)':inv.st==='معلق'?'var(--y1)':inv.st==='ملغي'?'var(--r1)':'var(--o1)';
  var stBg=inv.st==='معتمد'?'rgba(16,185,129,.1)':inv.st==='معلق'?'rgba(245,158,11,.1)':inv.st==='ملغي'?'rgba(239,68,68,.1)':'rgba(249,115,22,.1)';

  document.getElementById('inv-detail-title').innerHTML='<i class="fa fa-file-invoice" style="color:var(--a1)"></i> فاتورة '+no;
  var itemsHtml=inv.items.map(function(it){
    return '<div class="hist-item" style="margin-bottom:6px">'+
      '<div class="hist-ico" style="background:rgba(0,102,255,.1);color:var(--a1)"><i class="fa fa-box"></i></div>'+
      '<div class="hist-info"><div class="hist-code">'+(it.code||'—')+'</div><div class="hist-name">'+it.name+'</div></div>'+
      '<div class="hist-qty" style="color:var(--a1)">x '+it.qty+'</div>'+
    '</div>';
  }).join('');
  var btns='';
  var fromDash=(currentPage==='dashboard');
  var canEdit=(currentUser?.role==='مدير النظام'||currentUser?.role==='أمين مستودع');
  var fromMyInv=(currentPage==='myinv');
  var fromRequests=(currentPage==='requests');
  if(!fromApproval&&!fromDash&&!fromMyInv&&inv.st!=='ملغي'&&canEdit&&inv.type!=='الغاء') btns+='<button class="btn btn-warn btn-sm" onclick="closeModal(\'modal-inv\');arcEditInvoice(\''+no+'\')"><i class="fa fa-pen"></i>تعديل</button>';
  if(!fromApproval&&!fromDash&&!fromMyInv&&!fromRequests&&inv.st!=='ملغي'&&canEdit) btns+='<button class="btn btn-danger btn-sm" onclick="arcCancelInvoice(\''+no+'\')"><i class="fa fa-ban"></i>إلغاء</button>';
  var hasApprovedCancel=DB.requests.some(function(r){return (r.origInv===no||r.no===no)&&r.type==='الغاء'&&r.st==='معتمد';});
  if(!fromApproval&&!fromDash&&inv.st==='ملغي'&&!hasApprovedCancel&&(currentUser?.role==='مدير النظام'||currentUser?.role==='أمين مستودع')) btns+='<button class="btn btn-green btn-sm" onclick="arcRestoreInvoice(\''+no+'\')"><i class="fa fa-rotate-left"></i>استعادة</button>';
  btns+='<button class="btn btn-sec btn-sm" onclick="closeModal(\'modal-inv\')"><i class="fa fa-times"></i>اغلاق</button>';
  // زر الطباعة - يعمل للفواتير المعلقة وغير المعلقة
  if(fromApproval){
    // فاتورة معلقة - اطبع من بيانات الاعتماد مباشرة
    var _a=DB.approvals.find(function(x){return x.no===no;});
    if(_a)btns+='<button class="btn btn-primary btn-sm" onclick="closeModal(\'modal-inv\');printApprovalInvoice(\''+no+'\')"><i class="fa fa-print"></i>طباعة / PDF</button>';
  } else {
    btns+='<button class="btn btn-primary btn-sm" onclick="closeModal(\'modal-inv\');printInvoice(\''+no+'\')"><i class="fa fa-print"></i>طباعة / PDF</button>';
  }
  document.getElementById('inv-detail-body').innerHTML=
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:14px;font-size:12.5px">'+
      '<div><span style="color:var(--t3)">النوع: </span>'+tag(inv.type)+'</div>'+
      '<div><span style="color:var(--t3)">الحالة: </span><span style="font-weight:700;color:'+stColor+';background:'+stBg+';padding:2px 10px;border-radius:6px;font-size:12px">'+inv.st+'</span></div>'+
      (inv.st==="ملغي"?'<div style="grid-column:span 2;text-align:center;margin:8px 0">'+
        '<div style="display:inline-block;border:5px solid rgba(220,38,38,.4);border-radius:8px;padding:4px 22px;transform:rotate(-4deg);font-size:28px;font-weight:900;color:rgba(220,38,38,.5);letter-spacing:4px">ملغـي</div>'+
        (inv.cancelledBy?'<div style="margin-top:6px;font-size:11px;color:var(--r1)"><i class="fa fa-user-slash"></i> ألغاها: <strong>'+inv.cancelledBy+'</strong>'+(inv.cancelDate?' — '+inv.cancelDate:'')+'</div>':'')+
        (inv.cancelNote?'<div style="font-size:10px;color:var(--t3);margin-top:2px">'+inv.cancelNote+'</div>':'')+
      '</div>':'')+

      '<div><span style="color:var(--t3)">المستودع: </span><strong>'+inv.wh+'</strong></div>'+
      '<div><span style="color:var(--t3)">المقاول: </span><strong>'+inv.cont+'</strong></div>'+
      '<div><span style="color:var(--t3)">الموجه: </span>'+inv.emp+'</div>'+
      '<div><span style="color:var(--t3)">التاريخ: </span><span style="font-family:\'JetBrains Mono\',monospace">'+inv.d+'</span></div>'+
      (inv.boq?'<div><span style="color:var(--t3)">BOQ: </span>'+inv.boq+'</div>':'')+
      (inv.notes?'<div style="grid-column:span 2"><span style="color:var(--t3)">وصف البلاغ: </span>'+inv.notes+'</div>':'')+
    '</div>'+
    '<div style="font-size:10px;color:var(--t3);font-weight:700;letter-spacing:1.5px;margin-bottom:8px">المواد</div>'+
    itemsHtml+
    '<div style="display:flex;gap:7px;margin-top:14px;flex-wrap:wrap">'+btns+'</div>';
  openModal('modal-inv');
}

// ══════════════════════ EDIT ══════════════════════
function editSearch(){
  const q=(document.getElementById('edit-q')?.value||'').trim();
  const el=document.getElementById('edit-results');if(!el)return;
  if(!q){el.innerHTML='';return;}
  const found=DB.invoices.filter(i=>i.no.toUpperCase().includes(q.toUpperCase())||i.emp.includes(q)||i.cont.includes(q));
  if(!found.length){el.innerHTML=`<div style="color:var(--t3);font-size:13px;padding:8px 0"><i class="fa fa-search" style="margin-left:6px"></i>لم يتم العثور على فاتورة</div>`;return;}
  el.innerHTML=found.slice(0,6).map(r=>`
    <div class="hist-item" style="margin-bottom:7px;cursor:pointer" onclick="editSelect('${r.no}')">
      <div class="hist-ico" style="background:rgba(245,158,11,.1);color:var(--y1)"><i class="fa fa-file-pen"></i></div>
      <div class="hist-info"><div style="display:flex;align-items:center;gap:7px;flex-wrap:wrap"><span class="hist-code" style="color:var(--a1)">${r.no}</span>${tag(r.type)}${tag(r.st)}</div><div class="hist-name">${r.emp} — ${r.wh} — ${r.cont}</div><div class="hist-meta">${r.d}</div></div>
      <button class="btn btn-warn btn-sm">تعديل</button>
    </div>`).join('');
}
let editingItems=[];
function editSelect(no){
  const inv=DB.invoices.find(i=>i.no===no);if(!inv)return;
  editingInv={...inv};
  editingItems=inv.items.map(it=>({...it}));
  document.getElementById('edit-form').style.display='block';
  document.getElementById('edit-label').textContent=no;
  document.getElementById('edit-wh').value=inv.wh;
  document.getElementById('edit-cont').value=inv.cont;
  document.getElementById('edit-boq').value=inv.boq||'';
  document.getElementById('edit-st').value=inv.st;
  document.getElementById('edit-notes').value='';
  renderEditItems();
  document.getElementById('edit-form').scrollIntoView({behavior:'smooth'});
}
function renderEditItems(){
  const el=document.getElementById('edit-items-list');if(!el)return;
  if(!editingItems.length){el.innerHTML=`<div class="empty-state" style="padding:16px"><i class="fa fa-box-open"></i><p>لا توجد مواد</p></div>`;return;}
  el.innerHTML=editingItems.map((it,i)=>`
    <div class="cart-item-row" style="margin-bottom:7px">
      <div class="ci-info">
        <div class="ci-code">${it.code}</div>
        <div class="ci-name">${it.name}</div>
        <div style="font-size:10px;color:var(--t3)">متوفر في ${editingInv.wh}: ${getStock(it.code,editingInv.wh)}</div>
      </div>
      <div class="qty-ctrl">
        <div class="qbtn" onclick="editItemQty(${i},-1)">−</div>
        <div class="qval">${it.qty}</div>
        <div class="qbtn" onclick="editItemQty(${i},1)">+</div>
      </div>
      <div class="ci-del" onclick="editRemoveItem(${i})"><i class="fa fa-trash"></i></div>
    </div>`).join('');
}
function editItemQty(idx,delta){
  const it=editingItems[idx];
  const maxAvail=getStock(it.code,editingInv.wh);
  it.qty=Math.max(1,Math.min(maxAvail,it.qty+delta));
  renderEditItems();
}
function editRemoveItem(idx){editingItems.splice(idx,1);renderEditItems();}
function editAddItem(){
  const code=(document.getElementById('edit-add-code')?.value||'').trim();
  const qty=parseInt(document.getElementById('edit-add-qty')?.value)||1;
  if(!code){toast('err','حقل مطلوب','ادخل كود المادة','fa-triangle-exclamation');return;}
  const found=DB.inventory.find(i=>i.code===code||i.name.includes(code));
  if(!found){toast('err','مادة غير موجودة','لا توجد مادة بهذا الكود','fa-triangle-exclamation');return;}
  const wh=document.getElementById('edit-wh')?.value||editingInv.wh;
  const avail=getAvailableStock(found.code,wh);
  if(qty>avail){toast('warn','كمية تتجاوز المتاح','المتاح: '+avail,'fa-triangle-exclamation');return;}
  const ex=editingItems.find(it=>it.code===found.code);
  if(ex)ex.qty=Math.min(ex.qty+qty,avail);
  else editingItems.push({code:found.code,name:found.name,qty});
  document.getElementById('edit-add-code').value='';
  document.getElementById('edit-add-qty').value=1;
  renderEditItems();
  toast('ok','اضيفت',found.name+' x'+qty,'fa-box');
}
function editSave(){
  if(!editingInv)return;
  const wh=document.getElementById('edit-wh')?.value;
  const cont=(document.getElementById('edit-cont')?.value||'').trim();
  const boq=(document.getElementById('edit-boq')?.value||'').trim();
  const st=document.getElementById('edit-st')?.value;
  if(!cont){document.getElementById('edit-cont').classList.add('err');toast('err','حقل مطلوب','ادخل اسم المقاول','fa-user');return;}
  if(!editingItems.length){toast('err','لا توجد مواد','اضف مادة واحدة على الاقل','fa-box');return;}
  document.getElementById('edit-cont').classList.remove('err');
  const idx=DB.invoices.findIndex(i=>i.no===editingInv.no);
  if(idx>-1){
    const wasApproved=DB.invoices[idx].st==='معتمد';
    const oldDate=DB.invoices[idx].d;
    DB.invoices[idx].wh=wh;
    DB.invoices[idx].cont=cont;
    DB.invoices[idx].boq=boq;
    DB.invoices[idx].items=editingItems.map(it=>({...it}));
    // إذا كانت معتمدة → تعود للاعتماد مع حفظ تاريخ الاعتماد القديم
    if(wasApproved){
      DB.invoices[idx].st='معلق';
      DB.invoices[idx].prevApprDate=oldDate;
      // أضف للاعتماد
      const existAppr=DB.approvals.find(a=>a.no===editingInv.no);
      if(!existAppr){
        DB.approvals.unshift({id:Date.now(),no:editingInv.no,emp:currentUser.name,wh,cont,boq,items:editingItems.map(it=>it.name+' x'+it.qty).join(' + '),st:'معلق',d:today(),prevApprDate:oldDate});
      } else {
        existAppr.st='معلق';existAppr.d=today();existAppr.prevApprDate=oldDate;
      }
      toast('warn','⚠ تحتاج اعتماداً','الفاتورة '+editingInv.no+' معدّلة وبانتظار الاعتماد مجدداً','fa-signature');
    } else {
      DB.invoices[idx].st=st;
    }
  }
  addLog('تعديل','تعديل فاتورة '+editingInv.no+' (مواد+بيانات)',wh);
  toast('ok','✓ تم تعديل '+editingInv.no,'تم حفظ التعديلات بنجاح','fa-save');
  document.getElementById('edit-form').style.display='none';
  document.getElementById('edit-results').innerHTML='';
  document.getElementById('edit-q').value='';
  editingInv=null;editingItems=[];renderDashboard();
}

// ══════════════════════ CANCEL ══════════════════════
let cancelTarget=null;
function cancelSearch(){
  const q=(document.getElementById('cancel-q')?.value||'').trim().toUpperCase();
  const el=document.getElementById('cancel-results');if(!el)return;
  if(!q){el.innerHTML='';return;}
  const found=DB.invoices.filter(i=>i.no.includes(q)&&i.st!=='ملغي');
  if(!found.length){el.innerHTML=`<div style="color:var(--t3);font-size:13px;padding:8px">لا توجد فواتير قابلة للالغاء بهذا الرقم</div>`;return;}
  el.innerHTML=found.slice(0,5).map(r=>`
    <div class="hist-item" style="margin-bottom:7px">
      <div class="hist-ico" style="background:rgba(239,68,68,.1);color:var(--r1)"><i class="fa fa-file-circle-xmark"></i></div>
      <div class="hist-info"><div style="display:flex;align-items:center;gap:7px"><span class="hist-code" style="color:var(--r1)">${r.no}</span>${tag(r.type)}${tag(r.st)}</div><div class="hist-name">${r.emp} — ${r.wh} — ${r.cont}</div><div class="hist-meta">${r.d}</div></div>
      <div style="display:flex;gap:5px">
        <button class="btn btn-sec btn-sm" onclick="showInvDetail('${r.no}')"><i class="fa fa-eye"></i>معاينة</button>
        <button class="btn btn-danger btn-sm" onclick="cancelSelect('${r.no}')"><i class="fa fa-ban"></i>الغاء</button>
      </div>
    </div>`).join('');
}
function cancelSelect(no){cancelTarget=no;document.getElementById('cancel-label').textContent=no;document.getElementById('cancel-form').style.display='block';document.getElementById('cancel-form').scrollIntoView({behavior:'smooth'});}
function doCancel(){
  if(!cancelTarget)return;
  const reason=document.getElementById('cancel-reason')?.value||'—';
  showConfirm(`<i class="fa fa-ban" style="color:var(--r1)"></i> الغاء ${cancelTarget}`,
    `سيتم الغاء الفاتورة <strong>${cancelTarget}</strong> وإعادة جميع المواد للمستودع فوراً.<br><br>السبب: ${reason}<br><br>هذا الاجراء لا يمكن التراجع عنه.`,
    'تأكيد الالغاء','btn-danger',()=>{
      const inv=DB.invoices.find(i=>i.no===cancelTarget);
      if(inv){
        inv.st='ملغي';
        inv.items.forEach(it=>setStock(it.code,inv.wh,it.qty));
        addLog('الغاء','الغاء فاتورة '+cancelTarget+' — '+reason,inv.wh);
      }
      toast('ok','✓ الغاء '+cancelTarget,'تم الالغاء واعادة المواد للمستودع','fa-ban');
      document.getElementById('cancel-form').style.display='none';
      document.getElementById('cancel-results').innerHTML='';
      document.getElementById('cancel-q').value='';
      cancelTarget=null;renderDashboard();
    });
}

// ══════════════════════ REQUESTS ══════════════════════
// ══ متغيرات طلب الارجاع ══
let retItems=[];

function renderRequests(){
  const isM=currentUser?.role==='موجه بلاغات';
  const isW=currentUser?.role==='مشرف وردية';
  const isMojOrW=isM||isW;
  // إظهار الواجهة المناسبة
  const mv=document.getElementById('req-mojtahed-view');
  const av=document.getElementById('req-admin-view');
  const wc=document.getElementById('wardia-transfer-card');
  if(mv)mv.style.display=isMojOrW?'block':'none';
  if(av)av.style.display=isMojOrW?'none':'block';
  if(wc)wc.style.display=isW?'block':'none';
  document.getElementById('req-pg-title').textContent=isMojOrW?'إنشاء طلب ارجاع / الغاء / نقل':'طلبات الارجاع / الالغاء / النقل';

  if(isMojOrW){
    // تعبئة قائمة المقاولين
    const cd=document.getElementById('contr-datalist');
    if(cd)cd.innerHTML=DB.contractors.map(cc=>`<option value="${cc.name}">`).join('');
    renderRetItems();renderMyRequests();wtrRenderItems();
    document.getElementById('req-sub').textContent='إنشاء طلب جديد';
  } else {
    renderAdminRequests();
  }
}

function renderMyRequests(){
  var mine=DB.requests.filter(function(r){
    return r.emp===currentUser.name && r.st==='معلق';
  });
  var el=document.getElementById('req-mylist');if(!el)return;
  if(!mine.length){el.innerHTML='<div class="empty-state" style="padding:20px"><i class="fa fa-inbox"></i><p>لا توجد طلبات مقدمة بعد</p></div>';return;}
  var typeIco={ارجاع:'fa-rotate-left',الغاء:'fa-ban',نقل:'fa-right-left',تعديل:'fa-pen'};
  var isMoj=currentUser?.role==='موجه بلاغات';
  var isW=currentUser?.role==='مشرف وردية';

  el.innerHTML=mine.map(function(r){
    var ico=typeIco[r.type]||'fa-file';
    var invNo=r.origInv||r.no;
    var isPending=r.st==='معلق';

    // ─ ملخص التعديل
    var editSummary='';
    if(r.type==='تعديل'&&r.newItems){
      editSummary='<div style="margin-top:6px;font-size:11px;color:var(--t2)">'+
        '<span style="color:var(--t3)">التعديل: </span>'+
        (r.changes?.cont?'مقاول: <strong>'+r.changes.cont+'</strong> &nbsp;':'')+
        (r.changes?.wh?'مستودع: <strong>'+r.changes.wh+'</strong> &nbsp;':'')+
        r.newItems.length+' أصناف'+(r.deletedItems?.length?' — حذف '+r.deletedItems.length+' أصناف':'')+
      '</div>';
    }

    // ─ قائمة المواد
    var itemsHtml='';
    if(r.retItems&&r.retItems.length){
      itemsHtml='<div style="margin-top:6px">'+r.retItems.map(function(it){
        return '<div style="display:flex;align-items:center;gap:8px;padding:4px 8px;background:var(--bg2);border-radius:6px;margin-bottom:3px;font-size:11px">'+
          '<span class="mono" style="color:var(--a1)">'+it.code+'</span><span>'+it.name+'</span>'+
          '<span style="margin-right:auto;font-family:monospace;color:var(--o1)">x '+it.qty+'</span>'+
        '</div>';
      }).join('')+'</div>';
    }

    // ── ختم الإلغاء ──
    var cancelStamp='';
    if(r.type==='الغاء'){
      var stampColor=isPending?'rgba(245,158,11,.45)':'rgba(220,38,38,.45)';
      var stampText=isPending?'طلب إلغاء':'مُلغى';
      cancelStamp='<div style="display:inline-block;border:3px solid '+stampColor+';border-radius:6px;padding:2px 14px;transform:rotate(-5deg);font-size:13px;font-weight:900;color:'+stampColor+';letter-spacing:2px;margin-top:6px">'+stampText+'</div>';
    }

    // ── الأزرار حسب الدور والنوع والحالة ──
    var btns='';
    // معاينة دائماً
    btns+='<button class="btn btn-sec btn-xs" onclick="showInvDetail(\''+invNo+'\')">'+'<i class="fa fa-eye"></i>معاينة</button>';
    // طباعة دائماً
    btns+='<button class="btn btn-primary btn-xs" onclick="printInvoice(\''+invNo+'\')">'+'<i class="fa fa-print"></i>طباعة</button>';

    if(isPending){
      if(r.type==='ارجاع'){
        // موجه + مشرف: تعديل + سحب
        btns+='<button class="btn btn-warn btn-xs" onclick="editMyPendingRequest('+r.id+')"><i class="fa fa-pen"></i>تعديل</button>';
        btns+='<button class="btn btn-danger btn-xs" onclick="cancelMyRequest('+r.id+')"><i class="fa fa-xmark"></i>سحب</button>';
      } else if(r.type==='نقل'){
        // مشرف الوردية فقط: تعديل + سحب
        if(isW){
          btns+='<button class="btn btn-warn btn-xs" onclick="editMyPendingRequest('+r.id+')"><i class="fa fa-pen"></i>تعديل</button>';
          btns+='<button class="btn btn-danger btn-xs" onclick="cancelMyRequest('+r.id+')"><i class="fa fa-xmark"></i>سحب</button>';
        }
      } else if(r.type==='الغاء'){
        // الجميع: سحب فقط
        btns+='<button class="btn btn-danger btn-xs" onclick="cancelMyRequest('+r.id+')"><i class="fa fa-xmark"></i>سحب</button>';
      }
    }

    return '<div class="req-card" style="margin-bottom:10px">'+
      '<div class="req-hd">'+
        '<div style="display:flex;align-items:center;gap:7px;flex-wrap:wrap">'+
          '<span class="req-no">'+r.no+'</span>'+
          '<span style="font-size:10px;font-weight:700;background:rgba(255,255,255,.06);border:1px solid var(--b1);border-radius:6px;padding:2px 8px;color:var(--t2)"><i class="fa '+ico+'"></i> '+r.type+'</span>'+
          tag(r.st)+
        '</div>'+
        '<div style="display:flex;gap:5px;flex-wrap:wrap">'+btns+'</div>'+
      '</div>'+
      '<div style="font-size:11.5px;color:var(--t2);margin-top:5px;display:flex;gap:12px;flex-wrap:wrap">'+
        (r.wh?'<span><i class="fa fa-warehouse" style="color:var(--g1)"></i> '+r.wh+'</span>':'')+
        (r.cont?'<span><i class="fa fa-hard-hat" style="color:var(--o1)"></i> '+r.cont+'</span>':'')+
        (r.origInv?'<span><i class="fa fa-file" style="color:var(--a1)"></i> <span class="mono">'+r.origInv+'</span></span>':'')+
        '<span style="color:var(--t3)"><i class="fa fa-clock"></i> '+r.d+'</span>'+
      '</div>'+
      editSummary+itemsHtml+cancelStamp+
      (r.reason?'<div style="font-size:11px;color:var(--t3);margin-top:4px"><i class="fa fa-comment"></i> '+r.reason+'</div>':'')+
    '</div>';
  }).join('');
}

function renderAdminRequests(){
  var pendCount2=DB.requests.filter(function(r){return r.st==='معلق';}).length;
  var badge2=document.getElementById('req-pending-cnt');
  if(badge2){badge2.textContent=pendCount2;badge2.style.display=pendCount2?'inline-flex':'none';}
  const all=DB.requests;
  const pending=all.filter(r=>r.st==='معلق');
  document.getElementById('req-sub').textContent=pending.length+' طلبات بانتظار المراجعة';
  // الشرائح تعمل على المعلقة فقط
  const chips=[
    {v:'all',l:'الكل ('+pending.length+')'},
    {v:'ارجاع',l:'ارجاع ('+pending.filter(r=>r.type==='ارجاع').length+')'},
    {v:'الغاء',l:'الغاء ('+pending.filter(r=>r.type==='الغاء').length+')'},
    {v:'نقل',l:'نقل ('+pending.filter(r=>r.type==='نقل').length+')'}
  ];
  const chipsEl=document.getElementById('req-chips');
  if(chipsEl)chipsEl.innerHTML=chips.map(cc=>`<button class="fchip ${cc.v===reqFilter?'on':''}" onclick="setReqFilter('${cc.v}',this)">${cc.l}</button>`).join('');
  const items=pending.filter(r=>reqFilter==='all'||r.type===reqFilter);
  const el=document.getElementById('req-list');if(!el)return;
  if(!items.length){el.innerHTML='<div class="empty-state card"><i class="fa fa-check-double"></i><p>لا توجد طلبات</p></div>';return;}
  el.innerHTML=items.map(r=>`
    <div class="req-card">
      <div class="req-hd">
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
          <span class="req-no">${r.no}</span>${tag(r.type)}${tag(r.st)}
          <span style="font-size:11px;color:var(--t3)">من: ${r.emp}</span>
          ${r.type==='نقل'?`<span style="font-size:11px;color:var(--a1)"><i class="fa fa-right-left"></i> ${r.from||''} → ${r.to||''}</span>`:''}
        </div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center">
          <button class="btn btn-sec btn-sm" onclick="showInvDetail('${r.origInv||r.no}')"><i class="fa fa-eye"></i>معاينة</button>
          <button class="btn btn-primary btn-sm" onclick="var _n='${r.origInv||r.no}';var _i=DB.invoices.find(function(x){return x.no===_n;});if(_i)printInvoice(_n);else toast('warn','معلق','يمكن الطباعة بعد الاعتماد','fa-clock')"><i class="fa fa-print"></i></button>
          ${r.st==='معلق'&&(currentUser?.role==='مدير النظام'||currentUser?.role==='أمين مستودع')?`
            ${r.type!=='الغاء'?'<button class="btn btn-warn btn-sm" onclick="adminEditRequest('+r.id+')"><i class="fa fa-pen"></i>تعديل</button>':''}
            <button class="btn btn-green btn-sm" onclick="reqApprove(${r.id})"><i class="fa fa-check"></i>اعتماد</button>
            <button class="btn btn-danger btn-sm" onclick="reqReject(${r.id})"><i class="fa fa-times"></i>رفض</button>`
          :r.st==='معتمد'?`<span style="color:var(--g1);font-size:12px;display:flex;align-items:center;gap:5px"><i class="fa fa-check-circle"></i>معتمد</span>`
          :`<span style="color:var(--r1);font-size:12px;display:flex;align-items:center;gap:5px"><i class="fa fa-times-circle"></i>مرفوض</span>`}
        </div>
      </div>
      <!-- تفاصيل الطلب -->
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:7px;margin:10px 0;background:var(--bg2);border-radius:8px;padding:10px">
        <div style="font-size:11px"><span style="color:var(--t3)">المستودع المستلم:</span><br><strong>${r.wh}</strong></div>
        <div style="font-size:11px"><span style="color:var(--t3)">المقاول المُسلِّم:</span><br><strong>${r.cont}</strong></div>
        ${r.boq?`<div style="font-size:11px"><span style="color:var(--t3)">رقم BOQ:</span><br><strong class="mono">${r.boq}</strong></div>`:''}
        ${r.reason?`<div style="font-size:11px"><span style="color:var(--t3)">السبب:</span><br><strong>${r.reason}</strong></div>`:''}
        <div style="font-size:11px"><span style="color:var(--t3)">التاريخ:</span><br><strong class="mono">${r.d}</strong></div>
      </div>
      <!-- المواد -->
      <div style="margin-top:4px">
        ${(r.retItems||[]).map(it=>`<div style="display:flex;align-items:center;gap:8px;padding:5px 10px;background:var(--bg2);border-radius:6px;margin-bottom:3px;font-size:11.5px;border:1px solid var(--b1)">
          <span class="mono" style="color:var(--a1)">${it.code}</span><span style="color:var(--t1)">${it.name}</span>
          <span style="margin-right:auto;font-family:'JetBrains Mono',monospace;font-weight:700;color:var(--o1)">x ${it.qty} وحدة</span>
        </div>`).join('')}
      </div>
    </div>`).join('');
}

function setReqFilter(f,btn){reqFilter=f;document.querySelectorAll('#req-chips .fchip').forEach(b=>b.classList.remove('on'));btn.classList.add('on');renderRequests();}

// ── جلب بيانات فاتورة للارجاع ──
function fetchReturnInv(){
  const no=(document.getElementById('ret-inv-no')?.value||'').trim();
  const inv=DB.invoices.find(i=>i.no===no);
  const el=document.getElementById('ret-inv-info');
  if(!el)return;
  if(!inv){el.style.display='none';return;}
  el.style.display='block';
  el.innerHTML=`<div style="display:flex;flex-wrap:wrap;gap:10px">
    <span><i class="fa fa-warehouse" style="color:var(--g1)"></i> <strong>${inv.wh}</strong></span>
    <span><i class="fa fa-hard-hat" style="color:var(--o1)"></i> <strong>${inv.cont}</strong></span>
    <span>${tag(inv.type)} ${tag(inv.st)}</span>
  </div>
  <div style="margin-top:7px;font-size:11px;color:var(--t2)">${inv.items.map(it=>`<span style="margin-left:10px;font-family:monospace">${it.code} x${it.qty}</span>`).join('')}</div>`;
  // تعبئة المقاول تلقائياً
  const ce=document.getElementById('ret-cont');
  if(ce&&!ce.value)ce.value=inv.cont;
  const we=document.getElementById('ret-wh');
  if(we&&!we.value)we.value=inv.wh;
}
function fetchCancelInv(){
  const no=(document.getElementById('can-inv-no')?.value||'').trim();
  const inv=DB.invoices.find(i=>i.no===no);
  const el=document.getElementById('can-inv-info');
  if(!el)return;
  if(!inv){el.style.display='none';return;}
  el.style.display='block';
  el.innerHTML=`<div style="display:flex;flex-wrap:wrap;gap:10px">
    <span><i class="fa fa-warehouse" style="color:var(--g1)"></i> <strong>${inv.wh}</strong></span>
    <span><i class="fa fa-hard-hat" style="color:var(--o1)"></i> <strong>${inv.cont}</strong></span>
    <span>${tag(inv.type)} ${tag(inv.st)}</span>
  </div>
  <div style="margin-top:7px;font-size:11px;color:var(--t2)">${inv.items.map(it=>`<span style="margin-left:10px;font-family:monospace">${it.code} x${it.qty}</span>`).join('')}</div>`;
  const ce=document.getElementById('can-cont');
  if(ce&&!ce.value)ce.value=inv.cont;
  const we=document.getElementById('can-wh');
  if(we&&!we.value)we.value=inv.wh;
}

// ── مواد الارجاع ──
function renderRetItems(){
  const el=document.getElementById('ret-items-list');if(!el)return;
  if(!retItems.length){el.innerHTML='<div style="text-align:center;color:var(--t3);font-size:12px;padding:10px">أضف مواد للارجاع أدناه</div>';return;}
  el.innerHTML=retItems.map((it,i)=>`
    <div class="cart-item-row" style="margin-bottom:6px">
      <div class="ci-info"><div class="ci-code">${it.code}</div><div class="ci-name">${it.name}</div></div>
      <div class="qty-ctrl">
        <div class="qbtn" onclick="retQty(${i},-1)">−</div>
        <div class="qval">${it.qty}</div>
        <div class="qbtn" onclick="retQty(${i},1)">+</div>
      </div>
      <div class="ci-del" onclick="retItems.splice(${i},1);renderRetItems()"><i class="fa fa-trash"></i></div>
    </div>`).join('');
}
function retQty(i,d){const it=retItems[i];it.qty=Math.max(1,it.qty+d);renderRetItems();}
function retAddItem(){
  const code=(document.getElementById('ret-add-code')?.value||'').trim();
  const qty=parseInt(document.getElementById('ret-add-qty')?.value)||1;
  if(!code){toast('err','أدخل الكود','ادخل كود المادة المراد اعادتها','fa-triangle-exclamation');return;}
  const found=validateItemExists(code);
  if(!found)return;
  const ex=retItems.find(it=>it.code===found.code);
  if(ex)ex.qty+=qty;
  else retItems.push({code:found.code,name:found.name,qty});
  document.getElementById('ret-add-code').value='';
  document.getElementById('ret-add-qty').value=1;
  renderRetItems();
  toast('ok','أضيفت',found.name+' x'+qty,'fa-box');
}

// ── تقديم طلب الارجاع ──
function submitReturnRequest(){
  const origNo=(document.getElementById('ret-inv-no')?.value||'').trim();
  const wh=document.getElementById('ret-wh')?.value||'';
  const cont=(document.getElementById('ret-cont')?.value||'').trim();
  const boq=(document.getElementById('ret-boq-f')?.value||'').trim();
  const reason=(document.getElementById('ret-reason-f')?.value||'').trim();
  if(!origNo){toast('err','حقل مطلوب','ادخل رقم الفاتورة الأصلية','fa-file-invoice');return;}
  if(!DB.invoices.find(i=>i.no===origNo)){toast('err','فاتورة غير موجودة','لا توجد فاتورة بهذا الرقم','fa-ban');return;}
  if(!wh){toast('err','حقل مطلوب','اختر المستودع المستلم','fa-warehouse');return;}
  if(!cont){toast('err','حقل مطلوب','ادخل اسم المقاول المُسلِّم','fa-hard-hat');return;}
  if(!boq){toast('err','حقل مطلوب','رقم BOQ إجباري','fa-clipboard-list');return;}
  if(!retItems.length){toast('err','لا توجد مواد','أضف مادة واحدة على الأقل للارجاع','fa-box');return;}
  const no=origNo;  // رقم الطلب = رقم الفاتورة الأصلية
  DB.requests.push({
    id:Date.now(),no,type:'ارجاع',origInv:origNo,
    emp:currentUser.name,wh,cont,boq,reason,
    retItems:retItems.map(it=>({...it})),
    items:retItems.map(it=>it.name+' x'+it.qty).join(' + '),
    d:today(),time:nowTime(),st:'معلق'
  });
  addNotif('warn','طلب ارجاع جديد',currentUser.name+' — فاتورة '+origNo+' — '+retItems.length+' أصناف','fa-rotate-left',currentUser.name);
  addLog('ارجاع','تقديم طلب ارجاع '+no+' للفاتورة '+origNo,wh);
  retItems=[];
  ['ret-inv-no','ret-cont','ret-boq-f','ret-reason-f'].forEach(id=>{const e=document.getElementById(id);if(e)e.value='';});
  const we=document.getElementById('ret-wh');if(we)we.value='';
  const ri=document.getElementById('ret-inv-info');if(ri)ri.style.display='none';
  updateBadges();renderRequests();
  toast('ok','✓ تم تقديم طلب الارجاع','رقم الطلب: '+no+' — بانتظار اعتماد المدير','fa-rotate-left');
}

// ── تقديم طلب الالغاء ──
function submitCancelRequest(){
  const origNo=(document.getElementById('can-inv-no')?.value||'').trim();
  const wh=document.getElementById('can-wh')?.value||'';
  const cont=(document.getElementById('can-cont')?.value||'').trim();
  const boq=(document.getElementById('can-boq-f')?.value||'').trim();
  const reason=(document.getElementById('can-reason-f')?.value||'').trim();
  if(!origNo){toast('err','حقل مطلوب','ادخل رقم الفاتورة','fa-file-invoice');return;}
  const inv=DB.invoices.find(i=>i.no===origNo);
  if(!inv){toast('err','فاتورة غير موجودة','لا توجد فاتورة بهذا الرقم','fa-ban');return;}
  if(inv.st==='ملغي'){toast('err','ملغية مسبقاً','هذه الفاتورة ملغية بالفعل','fa-ban');return;}
  if(!wh){toast('err','حقل مطلوب','اختر المستودع المستلم للمواد','fa-warehouse');return;}
  if(!cont){toast('err','حقل مطلوب','ادخل اسم المقاول المُسلِّم','fa-hard-hat');return;}
  if(!boq){toast('err','حقل مطلوب','رقم BOQ إجباري','fa-clipboard-list');return;}
  if(!reason){toast('err','حقل مطلوب','ادخل سبب الالغاء','fa-comment');return;}
  const no=origNo;  // رقم الطلب = رقم الفاتورة الأصلية
  DB.requests.push({
    id:Date.now(),no,type:'الغاء',origInv:origNo,
    emp:currentUser.name,wh,cont,boq,reason,
    prevSt:inv.st,
    retItems:inv.items.map(it=>({...it})),
    items:'الغاء فاتورة '+origNo+' ('+inv.items.length+' أصناف)',
    d:today(),time:nowTime(),st:'معلق'
  });
  addNotif('err','طلب الغاء فاتورة',currentUser.name+' — فاتورة '+origNo,'fa-ban',currentUser.name);
  addLog('الغاء','تقديم طلب الغاء '+no+' للفاتورة '+origNo,wh);
  ['can-inv-no','can-cont','can-boq-f','can-reason-f'].forEach(id=>{const e=document.getElementById(id);if(e)e.value='';});
  const we=document.getElementById('can-wh');if(we)we.value='';
  const ci=document.getElementById('can-inv-info');if(ci)ci.style.display='none';
  updateBadges();renderRequests();
  toast('ok','✓ تم تقديم طلب الالغاء','رقم الطلب: '+no+' — بانتظار اعتماد المدير','fa-ban');
}

// ── تعديل الطلب (للموجه — فقط المعلقة) ──
// ══ متغيرات تعديل الطلب المعلق ══
var eprItems = [];
var eprRequestId = null;

function eprRenderItems(){
  var el = document.getElementById('epr-items-list');
  if(!el) return;
  if(!eprItems.length){
    el.innerHTML='<div style="text-align:center;color:var(--t3);font-size:12px;padding:12px">لا توجد مواد</div>';
    return;
  }
  el.innerHTML = eprItems.map(function(it,i){
    return '<div style="display:flex;align-items:center;gap:8px;padding:7px 10px;background:var(--bg2);border-radius:8px;margin-bottom:5px">'+
      '<span class="mono" style="color:var(--a1);font-size:11px;min-width:55px">'+it.code+'</span>'+
      '<span style="flex:1;font-size:12px;color:var(--t1)">'+it.name+'</span>'+
      '<button style="background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.2);color:var(--r1);border-radius:5px;padding:2px 7px;cursor:pointer;font-size:12px" onclick="eprQty('+i+',-1)">−</button>'+
      '<span class="mono" style="min-width:28px;text-align:center;font-weight:700;color:var(--t1)">'+it.qty+'</span>'+
      '<button style="background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.2);color:var(--g1);border-radius:5px;padding:2px 7px;cursor:pointer;font-size:12px" onclick="eprQty('+i+',1)">+</button>'+
      '<button style="background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.15);color:#f87171;border-radius:6px;padding:3px 8px;cursor:pointer;font-size:11px" onclick="eprRemove('+i+')"><i class="fa fa-trash"></i></button>'+
    '</div>';
  }).join('');
}

function eprQty(i,d){
  eprItems[i].qty = Math.max(1, eprItems[i].qty + d);
  eprRenderItems();
}

function eprRemove(i){
  eprItems.splice(i,1);
  eprRenderItems();
}

function eprAddItem(){
  var code = (document.getElementById('epr-add-code')?.value||'').trim();
  if(!code) return;
  var qty = parseInt(document.getElementById('epr-add-qty')?.value||1)||1;
  var item = validateItemExists(code);
  if(!item) return;
  var ex = eprItems.find(function(x){return x.code===item.code;});
  if(ex){ ex.qty+=qty; }
  else { eprItems.push({code:item.code,name:item.name,qty:qty}); }
  document.getElementById('epr-add-code').value='';
  document.getElementById('epr-add-qty').value=1;
  eprRenderItems();
  toast('ok','أُضيفت',item.name+' ×'+qty,'fa-box');
}

function editMyPendingRequest(id){
  var r = DB.requests.find(function(x){return x.id===id;});
  if(!r||r.st!=='معلق') return;
  eprRequestId = id;
  var srcItems = r.retItems||r.items||[];
  eprItems = srcItems.map(function(it){return {code:it.code,name:it.name,qty:it.qty};});

  var isReturn   = r.type==='ارجاع';
  var isTransfer = r.type==='نقل';
  var whOpts      = getWhOptions(false);
  var whEmptyOpts = '<option value="">-- اختر --</option>'+whOpts;

  var html =
    '<div style="max-width:520px">'+
    '<div class="form-row c2" style="margin-bottom:12px">'+
      '<div class="form-group">'+
        '<label class="form-label"><i class="fa fa-warehouse" style="color:var(--'+(isReturn?'g':'r')+'1)"></i> '+(isTransfer?'المستودع المصدر':isReturn?'المستودع المستلم':'المستودع')+'</label>'+
        '<select class="form-select" id="epr-wh">'+whOpts+'</select>'+
      '</div>'+
      (isTransfer
        ? '<div class="form-group"><label class="form-label"><i class="fa fa-warehouse" style="color:var(--g1)"></i> المستودع الهدف</label><select class="form-select" id="epr-wh-recv">'+whEmptyOpts+'</select></div>'
        : '<div class="form-group"><label class="form-label"><i class="fa fa-hard-hat" style="color:var(--o1)"></i> '+(isReturn?'المقاول المُسلِّم':'المقاول')+'</label><input class="form-input" id="epr-cont" value="'+(r.cont||'')+'" list="contr-datalist" placeholder="اسم المقاول..."></div>'
      )+
      (!isTransfer?'<div class="form-group">'+
        '<label class="form-label"><i class="fa fa-clipboard-list" style="color:var(--a3)"></i> رقم BOQ</label>'+
        '<input class="form-input" id="epr-boq" value="'+(r.boq||'')+'" placeholder="رقم BOQ...">'+
      '</div>':'') +
      '<div class="form-group">'+
        '<label class="form-label"><i class="fa fa-comment" style="color:var(--t3)"></i> السبب / الملاحظات</label>'+
        '<input class="form-input" id="epr-reason" value="'+(r.reason||r.notes||'')+'" placeholder="السبب...">'+
      '</div>'+
    '</div>'+
    '<div style="border:1px solid var(--b1);border-radius:10px;padding:10px;margin-bottom:10px">'+
      '<div style="font-size:12px;font-weight:700;color:var(--t2);margin-bottom:8px"><i class="fa fa-boxes-stacked" style="color:var(--a1)"></i> المواد</div>'+
      '<div id="epr-items-list"></div>'+
      '<div style="display:flex;gap:6px;align-items:center;margin-top:8px;padding-top:8px;border-top:1px solid var(--b1)">'+
        '<input class="form-input" id="epr-add-code" list="inv-datalist" placeholder="كود أو اسم المادة..." style="flex:1;font-size:12px">'+
        '<input class="form-input" id="epr-add-qty" type="number" min="1" value="1" style="width:60px;font-size:12px">'+
        '<button class="btn btn-primary btn-sm" onclick="eprAddItem()"><i class="fa fa-plus"></i>إضافة</button>'+
      '</div>'+
    '</div>'+
    '</div>';

  showFormModal(
    '<i class="fa fa-pen" style="color:var(--y1)"></i> تعديل طلب '+r.type+' — <span class="mono" style="color:var(--a1)">'+r.no+'</span>',
    html,
    [{lbl:'<i class="fa fa-save"></i> حفظ التعديل',cls:'btn-primary',fn:function(){
      if(!eprItems.length){toast('err','لا توجد مواد','أضف مادة واحدة على الأقل','fa-box');return;}
      var wh    = document.getElementById('epr-wh')?.value||r.wh;
      var whRecv= document.getElementById('epr-wh-recv')?.value||r.whRecv||'';
      var cont  = isTransfer?'':(document.getElementById('epr-cont')?.value||'').trim()||r.cont||'';
      var boq   = isTransfer?'':(document.getElementById('epr-boq')?.value||'').trim();
      var reason= (document.getElementById('epr-reason')?.value||'').trim();

      if(isTransfer && whRecv && whRecv===wh){toast('err','خطأ','اختر مستودعَيْن مختلفين','fa-ban');return;}

      r.wh     = wh;
      if(isTransfer) r.whRecv = whRecv;
      if(!isTransfer) r.cont  = cont;
      r.boq    = boq;
      r.reason = reason;
      r.retItems = JSON.parse(JSON.stringify(eprItems));
      r.items    = JSON.parse(JSON.stringify(eprItems));

      var invNo = r.origInv||r.no;
      var inv = DB.invoices.find(function(i){return i.no===invNo;});
      if(inv){
        inv.wh    = wh;
        if(isTransfer && whRecv) inv.whRecv = whRecv;
        if(!isTransfer) inv.cont = cont;
        inv.boq   = boq;
        inv.notes = reason;
        inv.items = JSON.parse(JSON.stringify(eprItems));
        syncInvoiceStatus(invNo, inv.st);
      }
      DB.approvals.forEach(function(a){
        if(a.no===invNo){
          a.wh=wh; if(!isTransfer)a.cont=cont; a.boq=boq;
          a.items=JSON.parse(JSON.stringify(eprItems));
          a.itemsStr=eprItems.map(function(i){return i.name+' \u00d7'+i.qty;}).join(' + ');
        }
      });

      addLog('تعديل','تعديل طلب '+r.type+' '+r.no+' — '+eprItems.length+' أصناف',wh,{no:r.no});
      closeModal('modal-form');
      renderRequests();
      toast('ok','✓ تم التعديل','طلب '+r.type+' '+r.no+' مُحدَّث في كامل النظام','fa-save');
    }}]
  );

  setTimeout(function(){
    var whEl=document.getElementById('epr-wh');
    if(whEl) whEl.value=r.wh||'';
    var wrEl=document.getElementById('epr-wh-recv');
    if(wrEl) wrEl.value=r.whRecv||'';
    eprRenderItems();
  },60);
}


function cancelMyRequest(id){
  var r=DB.requests.find(function(x){return x.id===id;});
  if(!r||r.st!=='معلق')return;

  var isCancelReq = r.type==='الغاء';
  var confirmMsg = isCancelReq
    ? 'سحب طلب <strong>إلغاء</strong> الفاتورة <strong>'+r.no+'</strong>؟<br>سيُحذف طلب الإلغاء كاملاً ويعود وضع الفاتورة كما كان.'
    : 'سحب طلب <strong>'+r.type+'</strong> الرقم <strong>'+r.no+'</strong>؟<br>سيُحذف الطلب من القائمة.';

  showConfirm('<i class="fa fa-xmark" style="color:var(--r1)"></i> سحب الطلب '+r.no,
    confirmMsg,'سحب الطلب','btn-danger',function(){

      var invNo = r.origInv||r.no;

      if(isCancelReq){
        // ── حذف طلب الإلغاء كاملاً من النظام ──
        DB.requests = DB.requests.filter(function(x){return x.id!==id;});

        // ── حذف من DB.approvals أيضاً ──
        DB.approvals = DB.approvals.filter(function(a){
          return !(a.no===invNo && a.type==='الغاء');
        });

        // ── استعادة حالة الفاتورة الأصلية لما قبل طلب الإلغاء ──
        var inv = DB.invoices.find(function(i){return i.no===invNo;});
        if(inv){
          // إذا كانت الفاتورة أصبحت "ملغي" بسبب هذا الطلب أعدها لـ"معتمد"
          if(inv.st==='ملغي'||inv.st==='معلق'){
            inv.st = r.prevSt||'معتمد';
          }
          syncInvoiceStatus(invNo, inv.st);
        }

        addLog('سحب','سحب طلب إلغاء الفاتورة '+invNo+' — حُذف الطلب كاملاً',r.wh||'—');
        updateBadges();renderMyInv();renderRequests();
        toast('ok','✓ سُحب طلب الإلغاء','طلب إلغاء الفاتورة '+invNo+' حُذف كاملاً من النظام','fa-trash');

      } else {
        // ── طلبات أخرى: حذف عادي ──
        DB.requests = DB.requests.filter(function(x){return x.id!==id;});
        addLog('الغاء','تم سحب طلب '+r.type+' '+r.no+' قبل الاعتماد',r.wh||'—');
        updateBadges();renderRequests();
        toast('ok','✓ سُحب الطلب','تم سحب الطلب '+r.no+' — لن يظهر في القائمة','fa-xmark');
      }
    });
}

function editMyRequest(id){
  const r=DB.requests.find(x=>x.id===id);if(!r||r.st!=='معلق')return;
  showFormModal(`<i class="fa fa-pen" style="color:var(--y1)"></i> تعديل طلب ${r.no}`,`
    <div class="form-row c2">
      <div class="form-group"><label class="form-label">المستودع المستلم</label>
        <select class="form-select" id="er-wh"><option value="">--</option><option ${r.wh==='اسناد'?'selected':''}>اسناد</option><option ${r.wh==='رايكو صبيا'?'selected':''}>رايكو صبيا</option><option ${r.wh==='هيف بني مالك'?'selected':''}>هيف بني مالك</option></select>
      </div>
      <div class="form-group"><label class="form-label">المقاول المُسلِّم</label>
        <input class="form-input" id="er-cont" value="${r.cont}">
      </div>
      <div class="form-group"><label class="form-label">رقم BOQ</label>
        <input class="form-input" id="er-boq" value="${r.boq||''}">
      </div>
      <div class="form-group"><label class="form-label">السبب</label>
        <input class="form-input" id="er-reason" value="${r.reason||''}">
      </div>
    </div>
    <div style="font-size:11px;font-weight:600;color:var(--t2);margin:10px 0 6px;border-top:1px solid var(--b1);padding-top:8px">المواد</div>
    ${(r.retItems||[]).map((it,i)=>`<div style="display:flex;align-items:center;gap:8px;padding:6px 10px;background:var(--bg2);border-radius:7px;margin-bottom:4px">
      <span class="mono" style="color:var(--a1)">${it.code}</span><span style="flex:1">${it.name}</span>
      <input type="number" min="1" value="${it.qty}" style="width:70px;font-family:'JetBrains Mono',monospace;padding:4px 8px;border:1px solid var(--b1);border-radius:6px;background:var(--bg2);color:var(--t1)" id="er-qty-${i}">
    </div>`).join('')}`,
    [{lbl:'<i class="fa fa-save"></i> حفظ',cls:'btn-primary',fn:()=>{
      r.wh=document.getElementById('er-wh')?.value||r.wh;
      r.cont=(document.getElementById('er-cont')?.value||r.cont).trim();
      r.boq=(document.getElementById('er-boq')?.value||'').trim();
      r.reason=(document.getElementById('er-reason')?.value||'').trim();
      (r.retItems||[]).forEach((it,i)=>{const v=parseInt(document.getElementById('er-qty-'+i)?.value);if(v&&v>0)it.qty=v;});
      closeModal('modal-form');renderRequests();
      toast('ok','✓ تم التعديل','تم تحديث بيانات الطلب','fa-save');
    }}]);
}

// ── تعديل الطلب (للمدير) ──
// ══════════════════════════════════════════════════════
// تعديل الفاتورة من قِبل المدير / أمين المستودع
// يعمل من: صفحة الاعتماد، طلبات الارجاع/الالغاء/النقل
// ══════════════════════════════════════════════════════
var aeItems = [];     // مواد نموذج التعديل
var aeInvNo = null;   // رقم الفاتورة الجارية

function aeRenderItems(){
  var el=document.getElementById('ae-items-list');if(!el)return;
  if(!aeItems.length){
    el.innerHTML='<div style="text-align:center;color:var(--t3);font-size:12px;padding:12px">لا توجد مواد — أضف من الحقل أدناه</div>';
    return;
  }
  el.innerHTML=aeItems.map(function(it,i){
    return '<div style="display:flex;align-items:center;gap:7px;padding:7px 10px;background:var(--bg2);border-radius:8px;margin-bottom:4px;border:1px solid var(--b1)">'+
      '<span class="mono" style="color:var(--a1);font-size:11px;min-width:60px">'+it.code+'</span>'+
      '<span style="flex:1;font-size:11.5px;color:var(--t1)">'+it.name+'</span>'+
      '<button style="background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.2);color:var(--r1);border-radius:5px;padding:2px 8px;cursor:pointer;font-size:12px;font-weight:700" onclick="aeQty('+i+',-1)">−</button>'+
      '<span class="mono" style="min-width:30px;text-align:center;font-weight:800;font-size:14px;color:var(--t1)">'+it.qty+'</span>'+
      '<button style="background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.2);color:var(--g1);border-radius:5px;padding:2px 8px;cursor:pointer;font-size:12px;font-weight:700" onclick="aeQty('+i+',1)">+</button>'+
      '<button style="background:rgba(239,68,68,.07);border:1px solid rgba(239,68,68,.15);color:#f87171;border-radius:6px;padding:3px 9px;cursor:pointer;font-size:11px" onclick="aeRemove('+i+')"><i class="fa fa-trash"></i></button>'+
    '</div>';
  }).join('');
}
function aeQty(i,d){aeItems[i].qty=Math.max(1,aeItems[i].qty+d);aeRenderItems();}
function aeRemove(i){aeItems.splice(i,1);aeRenderItems();}
function aeAddItem(){
  var code=(document.getElementById('ae-add-code')?.value||'').trim();
  if(!code)return;
  var qty=parseInt(document.getElementById('ae-add-qty')?.value||1)||1;
  var item=validateItemExists(code);if(!item)return;
  var ex=aeItems.find(function(x){return x.code===item.code;});
  if(ex){ex.qty+=qty;}else{aeItems.push({code:item.code,name:item.name,qty:qty});}
  document.getElementById('ae-add-code').value='';
  document.getElementById('ae-add-qty').value=1;
  aeRenderItems();
  toast('ok','أُضيفت',item.name+' ×'+qty,'fa-box');
}

function adminEditInvoice(no, fromPage){
  var inv=DB.invoices.find(function(i){return i.no===no;});
  if(!inv){toast('err','غير موجودة','الفاتورة غير موجودة','fa-ban');return;}
  aeInvNo=no;
  aeItems=inv.items.map(function(it){return {code:it.code,name:it.name,qty:it.qty};});

  var isIssue=inv.type==='صرف';
  var isReturn=inv.type==='ارجاع';
  var isTransfer=inv.type==='نقل';
  var whOpts=getWhOptions(false);
  var whEmptyOpts='<option value="">-- اختر --</option>'+whOpts;

  var html=
    '<div style="max-width:540px">'+
    // ─ تنبيه
    '<div style="background:rgba(245,158,11,.07);border:1px solid rgba(245,158,11,.2);border-radius:8px;padding:8px 12px;margin-bottom:12px;font-size:11.5px;color:var(--y1)">'+
      '<i class="fa fa-triangle-exclamation"></i> التعديل يُحدّث الفاتورة مباشرة — تبقى <strong>معلقة</strong> بانتظار الاعتماد'+
    '</div>'+
    // ─ معلومات الفاتورة
    '<div class="form-row c2" style="margin-bottom:12px">'+
      // المستودع المصدر
      '<div class="form-group">'+
        '<label class="form-label"><i class="fa fa-warehouse" style="color:var(--a1)"></i> '+(isTransfer?'مستودع المصدر':isReturn?'مستودع الاستلام':isIssue?'المستودع':'المستودع')+'</label>'+
        '<select class="form-select" id="ae-wh">'+whOpts+'</select>'+
      '</div>'+
      // مستودع الهدف (للنقل فقط)
      (isTransfer?
        '<div class="form-group"><label class="form-label"><i class="fa fa-warehouse" style="color:var(--g1)"></i> مستودع الهدف</label><select class="form-select" id="ae-wh-recv">'+whEmptyOpts+'</select></div>'
      :
        '<div class="form-group"><label class="form-label"><i class="fa fa-hard-hat" style="color:var(--o1)"></i> '+(isReturn?'المقاول المُسلِّم':'المقاول المستلم')+'</label>'+
        '<input class="form-input" id="ae-cont" value="'+(inv.cont||'')+'" list="contr-datalist" placeholder="اسم المقاول..."></div>'
      )+
      (!isTransfer?'<div class="form-group">'+
        '<label class="form-label"><i class="fa fa-clipboard-list" style="color:var(--a3)"></i> رقم BOQ</label>'+
        '<input class="form-input" id="ae-boq" value="'+(inv.boq||'')+'" placeholder="رقم BOQ...">'+
      '</div>':'') +
      '<div class="form-group">'+
        '<label class="form-label"><i class="fa fa-comment" style="color:var(--t3)"></i> '+(isReturn?'وصف البلاغ / الملاحظات':'وصف البلاغ / الملاحظات')+'</label>'+
        '<input class="form-input" id="ae-notes" value="'+(inv.notes||'')+'" placeholder="الوصف...">'+
      '</div>'+
      (isReturn?
        '<div class="form-group">'+
          '<label class="form-label"><i class="fa fa-rotate-left" style="color:var(--g1)"></i> سبب الارجاع</label>'+
          '<input class="form-input" id="ae-reason" value="'+(inv.reason||'')+'" placeholder="سبب ارجاع المواد...">'+
        '</div>'
      :'')+
    '</div>'+
    // ─ المواد
    '<div style="border:1px solid var(--b1);border-radius:10px;padding:10px">'+
      '<div style="font-size:12px;font-weight:700;color:var(--t2);margin-bottom:8px"><i class="fa fa-boxes-stacked" style="color:var(--a1)"></i> المواد</div>'+
      '<div id="ae-items-list"></div>'+
      '<div style="display:flex;gap:6px;align-items:center;margin-top:8px;padding-top:8px;border-top:1px solid var(--b1)">'+
        '<input class="form-input" id="ae-add-code" list="inv-datalist" placeholder="كود أو اسم المادة..." style="flex:1;font-size:12px">'+
        '<input class="form-input" id="ae-add-qty" type="number" min="1" value="1" style="width:60px;font-size:12px">'+
        '<button class="btn btn-primary btn-sm" onclick="aeAddItem()"><i class="fa fa-plus"></i>إضافة</button>'+
      '</div>'+
    '</div>'+
    '</div>';

  showFormModal(
    '<i class="fa fa-pen" style="color:var(--y1)"></i> تعديل فاتورة <span class="mono" style="color:var(--a1)">'+no+'</span> <span style="font-size:11px;background:rgba(255,255,255,.07);border-radius:5px;padding:2px 8px">'+inv.type+'</span>',
    html,
    [{lbl:'<i class="fa fa-save"></i> حفظ وإبقاء معلقة',cls:'btn-primary',fn:function(){
      if(!aeItems.length){toast('err','لا توجد مواد','أضف مادة على الأقل','fa-box');return;}
      var wh   =document.getElementById('ae-wh')?.value||inv.wh;
      var whRecv=document.getElementById('ae-wh-recv')?.value||inv.whRecv||'';
      var cont =isTransfer?inv.cont:(document.getElementById('ae-cont')?.value||'').trim()||inv.cont;
      var boq  =isTransfer?'':(document.getElementById('ae-boq')?.value||'').trim();
      var notes=(document.getElementById('ae-notes')?.value||'').trim();
      var reason=isReturn?(document.getElementById('ae-reason')?.value||'').trim():inv.reason||'';
      if(isTransfer&&whRecv&&whRecv===wh){toast('err','خطأ','المستودعان متطابقان — اختر مختلفين','fa-ban');return;}

      // ── تحديث الفاتورة ──
      inv.wh    =wh;
      inv.cont  =cont;
      inv.boq   =boq;
      inv.notes =notes;
      inv.reason=reason;
      if(isTransfer&&whRecv) inv.whRecv=whRecv;
      inv.items =JSON.parse(JSON.stringify(aeItems));

      // ── تحديث DB.approvals ──
      DB.approvals.forEach(function(a){
        if(a.no===no){
          a.wh=wh; a.cont=cont; a.boq=boq; a.notes=notes;
          a.items=JSON.parse(JSON.stringify(aeItems));
          a.itemsStr=aeItems.map(function(i){return i.name+' ×'+i.qty;}).join(' + ');
          if(isTransfer&&whRecv) a.whRecv=whRecv;
        }
      });

      // ── تحديث DB.requests المرتبطة ──
      DB.requests.forEach(function(r){
        if(r.origInv===no||r.no===no){
          r.wh=wh; if(!isTransfer)r.cont=cont; r.boq=boq;
          r.items=JSON.parse(JSON.stringify(aeItems));
          r.retItems=JSON.parse(JSON.stringify(aeItems));
        }
      });

      // ── الفاتورة تبقى معلقة ──
      syncInvoiceStatus(no,'معلق');
      addLog('تعديل','تعديل مباشر للفاتورة '+inv.type+' '+no+' من قِبل '+currentUser.name+' — '+aeItems.length+' أصناف',wh,{no:no,cont:cont});

      closeModal('modal-form');
      if(fromPage==='approve') renderApprovals();
      else if(fromPage==='archive'){renderArc();}
      else renderRequests();
      toast('ok','✓ تم التعديل','الفاتورة '+no+' مُحدَّثة — بانتظار الاعتماد','fa-save');
    }}]
  );

  setTimeout(function(){
    var whEl=document.getElementById('ae-wh');if(whEl)whEl.value=inv.wh||'';
    var wrEl=document.getElementById('ae-wh-recv');if(wrEl)wrEl.value=inv.whRecv||'';
    aeRenderItems();
  },60);
}

// adminEditRequest يستدعي adminEditInvoice بعد تحديد رقم الفاتورة
function adminEditRequest(id){
  var r=DB.requests.find(function(x){return x.id===id;});if(!r)return;
  var no=r.origInv||r.no;
  // إذا لم تكن الفاتورة موجودة في DB.invoices أنشئها مؤقتاً من بيانات الطلب
  var inv=DB.invoices.find(function(i){return i.no===no;});
  if(!inv){
    toast('warn','تنبيه','لا توجد فاتورة بهذا الرقم في الأرشيف — يمكن تعديل الطلب مباشرة','fa-circle-info');
    editMyPendingRequest(id);
    return;
  }
  adminEditInvoice(no,'requests');
}

function reqApprove(id){
  if(currentUser?.role==='مشرف وردية'){toast('err','غير مصرح','ليس لديك صلاحية الاعتماد','fa-lock');return;}
  const r=DB.requests.find(x=>x.id===id);if(!r)return;

  // ══ اعتماد طلب التعديل ══
  if(r.type==='تعديل'){
    var inv=DB.invoices.find(function(i){return i.no===r.origInv;});
    var newWh=r.changes.wh||inv?.wh||'—';
    // بناء جدول مقارنة قبل/بعد
    function fmtItems(items){
      if(!items||!items.length)return '<div style="color:var(--t3);font-size:11px">لا مواد</div>';
      return items.map(function(it){
        return '<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--b1);font-size:11.5px">'+
          '<span>'+it.name+'</span><span class="mono" style="color:var(--a1);font-weight:700">x'+it.qty+'</span></div>';
      }).join('');
    }
    var beforeHtml='<div style="background:rgba(239,68,68,.06);border:1px solid rgba(239,68,68,.2);border-radius:9px;padding:10px 12px;flex:1">'+
      '<div style="font-size:10px;font-weight:700;color:var(--r1);margin-bottom:6px">قبل التعديل</div>'+
      '<div style="font-size:11px;color:var(--t3);margin-bottom:6px">'+
        (inv?'المستودع: <strong>'+inv.wh+'</strong> &nbsp;·&nbsp; المقاول: <strong>'+inv.cont+'</strong>':'—')+
        (inv?.boq?'<br>BOQ: '+inv.boq:'')+
      '</div>'+
      fmtItems(r.oldValues?.items||inv?.items)+
    '</div>';
    var afterHtml='<div style="background:rgba(16,185,129,.06);border:1px solid rgba(16,185,129,.2);border-radius:9px;padding:10px 12px;flex:1">'+
      '<div style="font-size:10px;font-weight:700;color:var(--g1);margin-bottom:6px">بعد التعديل</div>'+
      '<div style="font-size:11px;color:var(--t3);margin-bottom:6px">'+
        'المستودع: <strong>'+newWh+'</strong> &nbsp;·&nbsp; المقاول: <strong>'+(r.changes.cont||inv?.cont||'—')+'</strong>'+
        (r.changes.boq?'<br>BOQ: '+r.changes.boq:'')+
      '</div>'+
      fmtItems(r.newItems)+
      (r.deletedItems?.length?'<div style="margin-top:6px;font-size:10.5px;color:var(--r1)"><i class="fa fa-trash"></i> محذوفة: '+r.deletedItems.map(function(d){return d.name+' x'+d.origQty;}).join('، ')+'</div>':'')+
    '</div>';
    var compareHtml='<div style="display:flex;gap:10px;margin-top:10px;flex-wrap:wrap">'+beforeHtml+afterHtml+'</div>';
    showConfirm('<i class="fa fa-pen" style="color:var(--y1)"></i> مراجعة تعديل '+r.origInv,
      '<p style="font-size:12px;margin-bottom:8px">طلب التعديل <strong style="color:var(--a1)">'+r.no+'</strong> من <strong>'+r.emp+'</strong></p>'+compareHtml,
      'اعتماد التعديل','btn-green',function(){
        r.st='معتمد';
        if(inv){
          var oldWh=inv.wh;
          (inv.items||[]).forEach(function(it){setStock(it.code,oldWh,+it.qty);});
          (r.newItems||[]).forEach(function(it){setStock(it.code,newWh,-it.qty);});
          (r.deletedItems||[]).forEach(function(it){setStock(it.code,oldWh,+it.origQty);});
          syncInvoiceStatus(r.origInv,'معتمد',{
            cont:r.changes.cont||inv.cont,
            boq:r.changes.boq||inv.boq,
            notes:r.changes.notes||inv.notes,
            wh:newWh,
            whRecv:r.changes.whRecv||inv.whRecv||'',
            items:JSON.parse(JSON.stringify(r.newItems||[])),
            editedAt:today(),editedBy:currentUser.name
          });
        }
        addLog('تعديل','اعتماد تعديل '+r.origInv+' ← '+r.no,newWh,{no:r.no,origInv:r.origInv,approvedBy:currentUser.name});
        addNotif('ok','✓ اعتمد تعديل فاتورة '+r.origInv,'تم تطبيق التعديل وتحديث الفاتورة والمخزون','fa-pen',r.emp);
        updateBadges();renderRequests();renderMyRequests();
        toast('ok','✓ فاتورة '+r.origInv+' تم تحديثها','اعتماد التعديل ونقل المخزون','fa-circle-check');
      });
    return;
  }

  // ══ اعتماد طلب النقل ══
  if(r.type==='نقل'){
    // فحص الرصيد المتاح (مطروح منه الحجوزات الأعلى أولوية = فواتير الصرف)
    var trShortages=[];
    (r.items||[]).forEach(function(it){
      var realStock=getStock(it.code,r.wh||r.from);
      var issuedReserved=DB.approvals
        .filter(function(a){return a.st==='معلق'&&a.wh===(r.wh||r.from);})
        .reduce(function(s,a){
          var items=Array.isArray(a.items)?a.items:[];
          var ai=items.find(function(x){return x.code===it.code;});
          return s+(ai?ai.qty:0);
        },0);
      var invReserved=DB.invoices
        .filter(function(inv){return inv.st==='معلق'&&inv.type==='صرف'&&inv.wh===(r.wh||r.from);})
        .reduce(function(s,inv){
          var ii=inv.items.find(function(x){return x.code===it.code;});
          return s+(ii?ii.qty:0);
        },0);
      // الصرف له أولوية — يُخصم أولاً
      var availForTransfer=realStock-issuedReserved-invReserved;
      if(it.qty>availForTransfer){
        trShortages.push({name:it.name,need:it.qty,avail:Math.max(0,availForTransfer),real:realStock,reserved:issuedReserved+invReserved});
      }
    });
    if(trShortages.length){
      var trMsg='<div style="font-size:12px">'+
        '<div style="background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.2);border-radius:8px;padding:10px;margin-bottom:10px">'+
          '<i class="fa fa-ban" style="color:var(--r1)"></i> <strong style="color:var(--r1)">رُفض اعتماد النقل</strong>'+
        '</div>'+
        '<strong>السبب: كمية النقل تتعارض مع طلبات صرف معلقة ذات أولوية أعلى</strong><br><br>'+
        trShortages.map(function(s){
          return '• <strong>'+s.name+'</strong><br>'+
            '&nbsp;&nbsp;المخزون الفعلي: <span class="mono">'+s.real+'</span>'+
            ' — محجوز للصرف: <span style="color:var(--r1);font-weight:700">'+s.reserved+'</span><br>'+
            '&nbsp;&nbsp;المتاح للنقل: <span style="color:var(--y1);font-weight:700">'+s.avail+'</span>'+
            ' — المطلوب: <span style="color:var(--r1);font-weight:700">'+s.need+'</span>';
        }).join('<br><br>')+
        '<br><br><div style="background:rgba(0,212,255,.06);border:1px solid rgba(0,212,255,.15);border-radius:6px;padding:8px;font-size:11px;color:var(--a1)">'+
          '<i class="fa fa-lightbulb"></i> لاعتماد النقل: ارفض أولاً طلبات الصرف المعلقة أو انتظر اعتمادها'+
        '</div></div>';
      toast('err','❌ رُفض اعتماد النقل','الكمية محجوزة لفاتورة صرف معلقة — راجع المحجوزات في رصيد المستودعات','fa-ban');
      showFormModal('<i class="fa fa-ban" style="color:var(--r1)"></i> تعذّر اعتماد النقل '+r.no,
        trMsg,[{lbl:'<i class="fa fa-times"></i> إغلاق',cls:'btn-sec',fn:function(){closeModal('modal-form');}}]);
      return;
    }
    showConfirm('<i class="fa fa-right-left" style="color:var(--a1)"></i> اعتماد نقل '+r.no,
      'اعتماد نقل المواد من <strong>'+(r.from||r.wh)+'</strong> إلى <strong>'+r.to+'</strong>؟',
      'اعتماد ونقل المواد','btn-green',function(){
        doTransferApprove(r);
      });
    return;
  }

  // ══ اعتماد طلب ارجاع / الغاء ══
  const isCancel=r.type==='الغاء';
  showConfirm(
    '<i class="fa fa-check" style="color:var(--g1)"></i> اعتماد '+r.no,
    'اعتماد طلب '+(isCancel?'الالغاء':'الارجاع')+' <strong>'+r.no+'</strong>؟<br><span style="color:var(--y1);font-size:12px">⚠ سيتم إعادة المواد للمستودع: '+r.wh+'</span>',
    'اعتماد واعادة المواد','btn-green',function(){
      r.st='معتمد';r.approvedDate=today();r.approvedBy=currentUser.name;
      (r.retItems||[]).forEach(function(it){
        if(DB.inventory.find(function(x){return x.code===it.code;}))setStock(it.code,r.wh,it.qty);
      });
      // وضع ختم الإلغاء على الفاتورة إذا كان طلب إلغاء
      if(isCancel){
        var invToCancel=DB.invoices.find(function(i){return i.no===(r.origInv||r.no);});
        if(invToCancel){
          invToCancel.cancelled   = true;
          invToCancel.cancelledBy = currentUser.name;
          invToCancel.cancelDate  = today();
          invToCancel.cancelNote  = 'اعتماد طلب إلغاء '+r.no;
        }
      }
      // تحديث حالة الفاتورة: إذا كان الطلب يرتبط بفاتورة أصلية (origInv)، حدّثها
      // وإذا كان رقم الطلب هو رقم الفاتورة نفسه، حدّثه أيضاً
      if(r.origInv) syncInvoiceStatus(r.origInv, isCancel?'ملغي':'معتمد');
      syncInvoiceStatus(r.no, isCancel?'ملغي':'معتمد');
      addLog(isCancel?'الغاء':'ارجاع','اعتماد طلب '+r.no+' — اعيدت المواد لـ '+r.wh,r.wh);
      addNotif('ok','✓ اعتماد '+r.no,'تم اعتماد الطلب وإعادة المواد للمستودع '+r.wh,'fa-check',r.emp);
      updateBadges();renderRequests();renderMyRequests();
      toast('ok','✓ اعتماد '+r.no,'تم اعتماد الطلب وإعادة المواد للمستودع','fa-check');
    });
}
function reqReject(id){
  const r=DB.requests.find(x=>x.id===id);if(!r)return;
  var msg=r.type==='تعديل'?
    'رفض طلب التعديل <strong>'+r.no+'</strong>؟<br><span style="color:var(--g1);font-size:12px">ستبقى الفاتورة الأصلية <strong>'+r.origInv+'</strong> كما هي بدون أي تغيير</span>':
    'رفض الطلب <strong>'+r.no+'</strong>؟ لن تُعاد أي مواد للمستودع.';
  showConfirm('<i class="fa fa-times" style="color:var(--r1)"></i> رفض '+r.no,msg,'رفض','btn-danger',function(){
    r.st='مرفوض';r.approvedDate=today();r.approvedBy=currentUser.name;
    if(r.type==='تعديل'){
      if(r.origInv) syncInvoiceStatus(r.origInv, r.wasApproved?'معتمد':'معتمد');
      addNotif('err','رُفض تعديل فاتورة '+(r.origInv||r.no),'الفاتورة الأصلية لم تتغير','fa-times',r.emp);
    } else {
      if(r.origInv) syncInvoiceStatus(r.origInv,'مرفوض');
      syncInvoiceStatus(r.no,'مرفوض');
      addNotif('err','رفض '+r.no,'تم رفض الطلب — لم تُعد المواد','fa-times',r.emp);
    }
    addLog('رفض','رفض طلب '+r.no+(r.origInv?' — الفاتورة الأصلية '+(r.origInv)+' محفوظة':''),r.wh||'—');
    updateBadges();renderRequests();renderMyRequests();
    toast('err','رفض '+r.no,r.type==='تعديل'?'الفاتورة الأصلية محفوظة كما هي':'تم الرفض','fa-times');
  });
}

// ══════════════════════ APPROVALS ══════════════════════
function renderApprovals(){
  var pendCount=DB.approvals.filter(function(a){return a.st==='معلق';}).length;
  var badge=document.getElementById('appr-pending-badge');
  if(badge){badge.textContent=pendCount;badge.style.display=pendCount?'inline-flex':'none';}
  const filterWh=(document.getElementById('appr-filter-wh')?.value||'');
  const filterDate=(document.getElementById('appr-filter-date')?.value||'');
  const pending=DB.approvals.filter(a=>a.st==='معلق');
  document.getElementById('appr-sub').textContent=pending.length+' فاتورة بانتظار الاعتماد';
  const el=document.getElementById('appr-list');if(!el)return;
  // فقط المعلقة في قسم المعلقة
  let items=pending;
  if(filterWh)items=items.filter(a=>a.wh===filterWh);
  if(filterDate)items=items.filter(a=>a.d===filterDate);
  if(!items.length){el.innerHTML=`<div class="empty-state card"><i class="fa fa-search"></i><p>لا توجد نتائج للفلاتر المحددة</p></div>`;return;}
  el.innerHTML=items.map(a=>`
    <div class="req-card">
      <div class="req-hd">
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
          <span class="req-no">${a.no}</span>${tag('صرف')}${tag(a.st)}
        </div>
        <div style="display:flex;align-items:center;gap:7px;flex-wrap:wrap">
          <button class="btn btn-sec btn-sm" onclick="showInvDetail('${a.no}')"><i class="fa fa-eye"></i>معاينة</button>
          <button class="btn btn-primary btn-sm" onclick="printInvoice('${a.no}')"><i class="fa fa-print"></i>طباعة</button>
          ${a.st==='معلق'&&(currentUser?.role==='مدير النظام'||currentUser?.role==='أمين مستودع')?`<div class="req-actions">
            <button class="btn btn-warn btn-sm" onclick="adminEditInvoice('${a.no}','approve')"><i class="fa fa-pen"></i>تعديل</button>
            <button class="btn btn-green btn-sm" onclick="apprApprove(${a.id})"><i class="fa fa-signature"></i>اعتماد</button>
            <button class="btn btn-danger btn-sm" onclick="apprReject(${a.id})"><i class="fa fa-times"></i>رفض</button>
          </div>`:a.st==='معتمد'?`<span style="color:var(--g1);font-size:12px;display:flex;align-items:center;gap:5px"><i class="fa fa-check-circle"></i>معتمد</span>`:`<span style="color:var(--r1);font-size:12px;display:flex;align-items:center;gap:5px"><i class="fa fa-times-circle"></i>مرفوض</span>`}
        </div>
      </div>
      <div class="req-meta" style="margin-bottom:8px">
        <div class="req-mi"><i class="fa fa-user"></i>${a.emp}</div>
        <div class="req-mi"><i class="fa fa-warehouse"></i>${a.wh}</div>
        <div class="req-mi"><i class="fa fa-hard-hat"></i>${a.cont}</div>
        <div class="req-mi"><i class="fa fa-clock"></i>${a.d}</div>
        ${a.boq?`<div class="req-mi"><i class="fa fa-clipboard-list" style="color:var(--a3)"></i>${a.boq}</div>`:''}
      </div>
      <div style="background:var(--bg2);border-radius:8px;padding:8px 10px;font-size:11.5px;color:var(--t2);border:1px solid var(--b1)">
        <i class="fa fa-boxes-stacked" style="color:var(--g1);margin-left:5px"></i><strong style="color:var(--t1)">${a.itemsStr||a.items}</strong>
      </div>
    </div>`).join('');
}
function apprApprove(id){
  if(currentUser?.role==='مشرف وردية'){toast('err','غير مصرح','ليس لديك صلاحية اعتماد فواتير الصرف','fa-lock');return;}
  const a=DB.approvals.find(x=>x.id===id);if(!a)return;
  const inv=DB.invoices.find(i=>i.no===a.no);
  // فحص الرصيد الفعلي (المخزون الحقيقي) قبل تأكيد الاعتماد
  var shortages=[];
  if(inv){
    inv.items.forEach(function(it){
      var realStock=getStock(it.code,inv.wh);
      // الكمية المحجوزة من طلبات أخرى (بدون هذه الفاتورة)
      var otherReserved=DB.approvals
        .filter(function(other){return other.st==='معلق'&&other.wh===inv.wh&&other.no!==a.no;})
        .reduce(function(s,other){
          var items=Array.isArray(other.items)?other.items:[];
          var oi=items.find(function(x){return x.code===it.code;});
          return s+(oi?oi.qty:0);
        },0);
      var otherTransfer=DB.requests
        .filter(function(r){return r.st==='معلق'&&r.type==='نقل'&&r.wh===inv.wh;})
        .reduce(function(s,r){
          var items=Array.isArray(r.items)?r.items:(r.retItems||[]);
          var ri=items.find(function(x){return x.code===it.code;});
          return s+(ri?ri.qty:0);
        },0);
      var available=realStock-otherReserved-otherTransfer;
      if(it.qty>available){
        shortages.push({name:it.name,code:it.code,need:it.qty,avail:Math.max(0,available),real:realStock});
      }
    });
  }
  if(shortages.length){
    var msg='<div style="font-size:12px">الكميات التالية غير متوفرة بعد احتساب الطلبات المعلقة:<br><br>'+
      shortages.map(function(s){
        return '• <strong>'+s.name+'</strong> — مطلوب: <span style="color:var(--r1);font-weight:700">'+s.need+'</span> متوفر فعلياً: <span style="color:var(--y1)">'+s.avail+'</span>';
      }).join('<br>')+
      '<br><br><span style="color:var(--y1)">⚠ الاعتماد سيتم لكن قد يكون المخزون سالباً</span></div>';
    showConfirm('<i class="fa fa-triangle-exclamation" style="color:var(--y1)"></i> تحذير — رصيد غير كافٍ',
      msg,'اعتماد رغم النقص','btn-warn',function(){doApprApprove(a,inv);});
    return;
  }
  showConfirm('<i class="fa fa-signature" style="color:var(--g1)"></i> اعتماد '+a.no,
    'اعتماد فاتورة الصرف <strong>'+a.no+'</strong> — '+a.cont+'؟','اعتماد','btn-green',
    function(){doApprApprove(a,inv);});
}

function doApprApprove(a,inv){
  var wh = inv?inv.wh:a.wh;
  var itemsToDeduct = inv?inv.items:(Array.isArray(a.items)?a.items:[]);
  // خصم المخزون
  itemsToDeduct.forEach(function(it){
    if(it.code&&it.qty) setStock(it.code,wh,-it.qty);
  });
  // تحديث الاعتماد
  a.st='معتمد';a.approvedDate=today();a.approvedBy=currentUser.name;
  // تحديث الفاتورة إذا وُجدت
  if(inv){inv.st='معتمد';inv.approvedDate=today();inv.approvedBy=currentUser.name;}
  syncInvoiceStatus(a.no,'معتمد');
  addLog('صرف','اعتماد فاتورة '+a.no,wh);
  addNotif('ok','اعتماد '+a.no,'تم اعتماد فاتورة الصرف وخصم المواد','fa-signature',a.emp);
  updateBadges();renderApprovals();renderMyRequests();
  toast('ok','✓ اعتماد '+a.no,'تم الاعتماد وخصم المواد من '+wh,'fa-signature');
}
function apprReject(id){
  const a=DB.approvals.find(x=>x.id===id);if(!a)return;
  const inv=DB.invoices.find(i=>i.no===a.no);
  const wasDeducted=inv?.st==='معتمد';
  showConfirm('<i class="fa fa-times" style="color:var(--r1)"></i> رفض '+a.no,'رفض فاتورة <strong>'+a.no+'</strong>؟'+(wasDeducted?' سيتم اعادة المواد للمستودع.':' (الكمية المحجوزة ستُحرر)'),'رفض','btn-danger',function(){
    if(inv){
      if(inv.st==='معتمد') inv.items.forEach(function(it){setStock(it.code,inv.wh,+it.qty);});
    }
    a.st='مرفوض';a.approvedDate=today();a.approvedBy=currentUser.name;
    syncInvoiceStatus(a.no,'مرفوض');
    addLog('صرف','رفض فاتورة '+a.no,a.wh);
    addNotif('err','رفض '+a.no,'تم رفض فاتورة الصرف','fa-times',a.emp);
    renderApprovals();
    toast('err','رفض '+a.no,'تم الرفض — الكمية المحجوزة حُررت','fa-times');
  });
}

// ══════════════════════ MY INVOICES ══════════════════════

// ══ تعديل فاتورة الصرف المعلقة (قبل الاعتماد) ══
// ══════════════════════════════════════════════════════════════
// ⚠️ لا تحذف هذه الدوال — أساسية لصفحة فواتيري
// myInvEdit     → تعديل الفاتورة المعلقة (صاحبها فقط)
// myInvEditSave → حفظ التعديل مع التحقق من الملكية
// myInvWithdraw → سحب الفاتورة قبل الاعتماد (صاحبها فقط)
// تنطبق على: صرف · ارجاع · الغاء · نقل
// ══════════════════════════════════════════════════════════════
function myInvEdit(no){
  var inv=DB.invoices.find(function(i){return i.no===no;});
  if(!inv){toast('err','غير موجودة','الفاتورة غير موجودة','fa-ban');return;}
  if(inv.st!=='معلق'){toast('warn','غير مسموح','يمكن التعديل فقط على الفواتير المعلقة','fa-lock');return;}
  if(inv.emp!==currentUser.name){toast('err','غير مصرح','يمكنك تعديل فواتيرك فقط','fa-lock');return;}
  window._editingInvNo=no;



  var whOpts=DB.warehouses.filter(function(w){return w.active;}).map(function(w){
    return '<option value="'+w.name+'"'+(w.name===inv.wh?' selected':'')+'>'+w.name+'</option>';
  }).join('');
  var contOpts='<option value="">-- اختر مقاول --</option>'+DB.contractors.map(function(ct){
    return '<option value="'+ct.name+'"'+(ct.name===inv.cont?' selected':'')+'>'+ct.name+'</option>';
  }).join('');
  var itemsHtml=inv.items.map(function(it,idx){
    var row='<div style="display:flex;gap:8px;align-items:center;padding:6px;background:var(--bg2);border-radius:6px;margin-bottom:4px">';
    row+='<span class="mono" style="color:var(--a1);min-width:90px">'+it.code+'</span>';
    row+='<span style="flex:1;font-size:12px">'+it.name+'</span>';
    row+='<input type="number" min="1" value="'+it.qty+'" id="eit-qty-'+idx+'" style="width:70px;padding:4px 6px;border:1px solid var(--b1);border-radius:5px;background:var(--bg1);color:var(--t1);text-align:center">';
    row+='</div>';
    return row;
  }).join('');
  var html='<div style="font-size:13px">';
  html+='<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px">';
  html+='<div><label style="font-size:11px;color:var(--t3)">المستودع</label><select id="eit-wh" style="width:100%;padding:7px;border:1px solid var(--b1);border-radius:6px;background:var(--bg1);color:var(--t1);margin-top:3px">'+whOpts+'</select></div>';
  html+='<div><label style="font-size:11px;color:var(--t3)">المقاول المستلم</label><select id="eit-cont" style="width:100%;padding:7px;border:1px solid var(--b1);border-radius:6px;background:var(--bg1);color:var(--t1);margin-top:3px">'+contOpts+'</select></div>';
  html+='<div><label style="font-size:11px;color:var(--t3)">رقم BOQ</label><input id="eit-boq" value="'+(inv.boq||'')+'" style="width:100%;padding:7px;border:1px solid var(--b1);border-radius:6px;background:var(--bg1);color:var(--t1);margin-top:3px"></div>';
  html+='<div><label style="font-size:11px;color:var(--t3)">ملاحظات</label><input id="eit-notes" value="'+(inv.notes||'')+'" style="width:100%;padding:7px;border:1px solid var(--b1);border-radius:6px;background:var(--bg1);color:var(--t1);margin-top:3px"></div>';
  html+='</div>';
  html+='<div style="font-size:11px;color:var(--t3);margin-bottom:6px">المواد ('+inv.items.length+'):</div>';
  html+='<div id="eit-items">'+itemsHtml+'</div>';
  html+='</div>';
  showFormModal('<i class="fa fa-pen" style="color:var(--y1)"></i> تعديل فاتورة '+no,
    html,[
      {lbl:'<i class="fa fa-save"></i> حفظ',cls:'btn-warn',fn:function(){myInvEditSave(no);}},
      {lbl:'<i class="fa fa-eye"></i> معاينة',cls:'btn-primary',fn:function(){closeModal('modal-form');showInvDetail(no);}},
      {lbl:'<i class="fa fa-print"></i> طباعة',cls:'btn-sec',fn:function(){closeModal('modal-form');printInvoice(no);}},
      {lbl:'إلغاء',cls:'btn-sec',fn:function(){closeModal('modal-form');}}
    ]);
}


// ══ سحب فاتورة الصرف المعلقة ══

function myInvEditSave(no){
  var inv=DB.invoices.find(function(i){return i.no===no;});
  if(!inv) return;
  // التحقق أن المستخدم هو صاحب الفاتورة
  if(inv.emp!==currentUser.name){toast('err','غير مصرح','يمكنك تعديل فواتيرك فقط','fa-lock');return;}
  if(inv.st!=='معلق'){toast('warn','غير مسموح','يمكن التعديل فقط قبل الاعتماد','fa-lock');return;}
  var newWh=document.getElementById('eit-wh')?.value||inv.wh;
  var newCont=document.getElementById('eit-cont')?.value||inv.cont;
  var newBoq=document.getElementById('eit-boq')?.value||'';
  var newNotes=document.getElementById('eit-notes')?.value||'';
  var newReason=document.getElementById('eit-reason')?.value||inv.reason||'';
  var newWhRecv=document.getElementById('eit-whrecv')?.value||inv.whRecv||'';
  if(!newCont){toast('err','حقل مطلوب','اختر اسم المقاول','fa-ban');return;}
  // تحديث الكميات
  (inv.items||[]).forEach(function(it,idx){
    var qEl=document.getElementById('eit-qty-'+idx);
    if(qEl) it.qty=Math.max(1,parseInt(qEl.value)||it.qty);
  });
  inv.wh=newWh;inv.cont=newCont;inv.boq=newBoq;inv.notes=newNotes;
  if(newReason)inv.reason=newReason;
  if(newWhRecv)inv.whRecv=newWhRecv;
  inv.editedAt=today();inv.editedBy=currentUser.name;
  // تحديث الاعتماد المرتبط
  var a=DB.approvals.find(function(x){return x.no===no;});
  if(a){a.wh=newWh;a.cont=newCont;a.boq=newBoq;a.notes=newNotes;
    a.items=(inv.items||[]).map(function(it){return Object.assign({},it);});}
  // تحديث الطلب المرتبط
  var req=DB.requests.find(function(r){return r.no===no&&r.st==='معلق';});
  if(req){req.wh=newWh;req.cont=newCont;req.boq=newBoq;req.notes=newNotes;
    if(newReason)req.reason=newReason;if(newWhRecv)req.to=newWhRecv;}
  addLog('تعديل','تعديل '+inv.type+' معلق '+no+' بواسطة '+currentUser.name,newWh,{no:no});
  closeModal('modal-form');renderMyInv();
  toast('ok','✓ تم التعديل','تم تحديث '+inv.type+' '+no,'fa-pen');
}

function myInvWithdraw(no){
  var inv=DB.invoices.find(function(i){return i.no===no;});
  if(!inv){toast('err','غير موجودة','الفاتورة غير موجودة','fa-ban');return;}
  // التحقق أن المستخدم هو صاحب الفاتورة فقط
  if(inv.emp!==currentUser.name){toast('err','غير مصرح','يمكنك سحب فواتيرك فقط','fa-lock');return;}
  if(inv.st!=='معلق'){toast('warn','غير مسموح','يمكن السحب فقط قبل الاعتماد — اطلب إلغاءً من الأرشيف','fa-lock');return;}
  showConfirm('<i class="fa fa-xmark" style="color:var(--r1)"></i> سحب '+inv.type+' '+no,
    'سحب <strong>'+no+'</strong> ('+inv.type+') قبل الاعتماد؟<br>'+
    '<div style="margin-top:6px;font-size:11px;color:var(--t3)">لن يتم أي تأثير على المخزون</div>',
    'سحب','btn-danger',function(){
      inv.st='ملغي';inv.cancelDate=today();inv.cancelBy=currentUser.name;
      var a=DB.approvals.find(function(x){return x.no===no;});
      if(a){a.st='ملغي';a.cancelDate=today();a.cancelBy=currentUser.name;}
      var req=DB.requests.find(function(r){return r.no===no&&r.st==='معلق';});
      if(req){req.st='ملغي';req.cancelDate=today();req.cancelBy=currentUser.name;}
      addLog('إلغاء','سحب '+inv.type+' معلق '+no+' بواسطة '+currentUser.name,inv.wh,{no:no});
      addNotif('warn','سُحب '+no,currentUser.name+' سحب '+inv.type+' قبل الاعتماد','fa-xmark',null);
      updateBadges();syncInvoiceStatus(no,'ملغي');renderMyInv();
      toast('ok','✓ تم السحب',no+' ('+inv.type+') سُحب وأُلغي','fa-xmark');
    });
}


function renderMyInv(){
  var q=(document.getElementById('myinv-q')?.value||'').toLowerCase();
  var typeF=document.getElementById('myinv-type')?.value||'';
  var mine=DB.invoices.filter(function(i){return i.emp===currentUser?.name;});

  // إحصائيات
  var stats=[
    {l:'الإجمالي',v:mine.length,c:'var(--a1)'},
    {l:'معتمدة',v:mine.filter(function(i){return i.st==='معتمد';}).length,c:'var(--g1)'},
    {l:'معلقة',v:mine.filter(function(i){return i.st==='معلق';}).length,c:'var(--y1)'},
    {l:'مرفوضة/ملغاة',v:mine.filter(function(i){return i.st==='مرفوض'||i.st==='ملغي';}).length,c:'var(--r1)'}
  ];
  document.getElementById('myinv-stats').innerHTML=stats.map(function(s){
    return '<div class="mi-s"><div class="mi-sv" style="color:'+s.c+'">'+s.v+'</div><div class="mi-sl">'+s.l+'</div></div>';
  }).join('');
  document.getElementById('myinv-sub').textContent=mine.length+' فاتورة';

  // ═══ القسم الأول: المنتهية (معتمدة + مرفوضة + ملغية) ═══
  var done=mine.filter(function(i){return i.st!=='معلق';});
  if(q) done=done.filter(function(i){return i.no.toLowerCase().includes(q)||(i.cont||'').toLowerCase().includes(q);});
  if(typeF) done=done.filter(function(i){return i.type===typeF;});
  var doneCount=document.getElementById('myinv-done-count');
  if(doneCount) doneCount.textContent=done.length+' فاتورة';
  var doneTbody=document.getElementById('myinv-done-tbody');
  if(doneTbody){
    if(!done.length){
      doneTbody.innerHTML='<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--t3)"><i class="fa fa-inbox" style="font-size:24px;display:block;margin-bottom:8px"></i>لا توجد فواتير منتهية</td></tr>';
    } else {
      doneTbody.innerHTML=done.map(function(r){
        var btns='<button class="btn btn-sec btn-xs" onclick="event.stopPropagation();showInvDetail(\''+r.no+'\')"><i class="fa fa-eye"></i>معاينة</button>';
        btns+='<button class="btn btn-primary btn-xs" onclick="event.stopPropagation();printInvoice(\''+r.no+'\')"><i class="fa fa-print"></i>طباعة</button>';
        if(r.st==='معتمد'&&r.type==='صرف'){
          btns+='<button class="btn btn-warn btn-xs" onclick="event.stopPropagation();go(\'requests\')"><i class="fa fa-rotate-left"></i>طلب ارجاع</button>';
        }
        var stColor=r.st==='معتمد'?'var(--g1)':r.st==='مرفوض'?'var(--r1)':'var(--t3)';
        return '<tr onclick="showInvDetail(\''+r.no+'\')">'+
          '<td class="mono">'+r.no+'</td>'+
          '<td>'+tag(r.type)+'</td>'+
          '<td>'+r.wh+'</td>'+
          '<td>'+r.cont+'</td>'+
          '<td><span style="color:'+stColor+';font-weight:700">'+r.st+'</span></td>'+
          '<td style="font-size:11px;color:var(--t3)">'+r.d+'</td>'+
          '<td><div style="display:flex;gap:4px;flex-wrap:wrap">'+btns+'</div></td>'+
        '</tr>';
      }).join('');
    }
  }

  // ═══ القسم الثاني: المعلقة ═══
  var pend=mine.filter(function(i){return i.st==='معلق';});
  var pendBadge=document.getElementById('myinv-pend-badge');
  if(pendBadge){pendBadge.textContent=pend.length;pendBadge.style.display=pend.length?'inline-block':'none';}
  var pendTbody=document.getElementById('myinv-pend-tbody');
  if(pendTbody){
    if(!pend.length){
      pendTbody.innerHTML='<tr><td colspan="6" style="text-align:center;padding:20px;color:var(--t3)"><i class="fa fa-check-circle" style="font-size:24px;display:block;margin-bottom:8px;color:var(--g1)"></i>لا توجد فواتير معلقة</td></tr>';
    } else {
      pendTbody.innerHTML=pend.map(function(r){
        var btns='<button class="btn btn-sec btn-xs" onclick="event.stopPropagation();showInvDetail(\''+r.no+'\')"><i class="fa fa-eye"></i>معاينة</button>';
        btns+='<button class="btn btn-primary btn-xs" onclick="event.stopPropagation();printInvoice(\''+r.no+'\')"><i class="fa fa-print"></i>طباعة</button>';
        // تعديل وسحب متاح لكل أنواع الفواتير المعلقة
        btns+='<button class="btn btn-warn btn-xs" onclick="event.stopPropagation();myInvEdit(\''+r.no+'\')"><i class="fa fa-pen"></i>تعديل</button>';
        btns+='<button class="btn btn-danger btn-xs" onclick="event.stopPropagation();myInvWithdraw(\''+r.no+'\')"><i class="fa fa-xmark"></i>سحب</button>';
        return '<tr onclick="showInvDetail(\''+r.no+'\')">'+
          '<td class="mono">'+r.no+'</td>'+
          '<td>'+tag(r.type)+'</td>'+
          '<td>'+r.wh+'</td>'+
          '<td>'+r.cont+'</td>'+
          '<td style="font-size:11px;color:var(--t3)">'+r.d+'</td>'+
          '<td><div style="display:flex;gap:4px;flex-wrap:wrap">'+btns+'</div></td>'+
        '</tr>';
      }).join('');
    }
  }
}


// reqReturn replaced by submitReturnRequest

// ══════════════════════ BOQ ══════════════════════
function searchInvByBOQ(){
  const q=(document.getElementById('boq-inv-q')?.value||'').trim().toLowerCase();
  const el=document.getElementById('boq-inv-results');if(!el)return;
  if(!q){el.innerHTML='';return;}
  // البحث الجزئي في رقم BOQ لجميع الفواتير
  const results=DB.invoices.filter(i=>i.boq&&i.boq.toLowerCase().includes(q));
  if(!results.length){
    el.innerHTML=`<div style="color:var(--t3);font-size:12px;text-align:center;padding:14px"><i class="fa fa-search" style="color:var(--t4)"></i> لا توجد فواتير تحتوي على "<strong style="color:var(--a1)">${q}</strong>" في رقم BOQ</div>`;
    return;
  }
  el.innerHTML=`
    <div style="font-size:11px;color:var(--t3);margin-bottom:8px"><i class="fa fa-check-circle" style="color:var(--g1)"></i> وُجدت <strong style="color:var(--a1)">${results.length}</strong> فاتورة تحتوي على "<strong style="color:var(--a1)">${q}</strong>"</div>
    <div class="card tbl-wrap" style="margin:0">
      <table class="tbl">
        <thead><tr><th>رقم الفاتورة</th><th>رقم BOQ</th><th>النوع</th><th>المستودع</th><th>المقاول</th><th>الموجه</th><th>التاريخ</th><th>الحالة</th><th></th></tr></thead>
        <tbody>
          ${results.map(r=>`<tr>
            <td class="mono" style="color:var(--a1);font-weight:700">${r.no}</td>
            <td><span style="font-family:'JetBrains Mono',monospace;font-size:11px;background:rgba(0,212,255,.08);padding:2px 8px;border-radius:5px;color:var(--a1)">${r.boq.replace(new RegExp('('+q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+')','gi'),'<mark style="background:rgba(255,200,0,.35);color:var(--t1);border-radius:2px">$1</mark>')}</span></td>
            <td>${tag(r.type)}</td>
            <td style="font-size:12px">${r.wh}</td>
            <td style="font-size:12px">${r.cont}</td>
            <td style="font-size:12px">${r.emp}</td>
            <td style="font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--t3)">${r.d}</td>
            <td>${tag(r.st)}</td>
            <td style="display:flex;gap:4px">
              <button class="btn btn-sec btn-xs" onclick="showInvDetail('${r.no}')"><i class="fa fa-eye"></i></button>
              <button class="btn btn-primary btn-xs" onclick="printInvoice('${r.no}')"><i class="fa fa-print"></i></button>
            </td>
          </tr>`).join('')}
        </tbody>
      </table>
    </div>`;
  // عرض النسخ الاحتياطية وموظف الشهر
  renderBackups();
  renderEmpMonth();
  // إضافة زر الحفظ
  document.querySelectorAll('[data-s-key]').forEach(function(el){
    el.addEventListener('change',function(){
      var key=this.dataset.sKey,val=this.type==='checkbox'?this.checked:this.value;
      if(DB.settings)DB.settings[key]=val;
    });
  });
}
function renderBOQ(){
  // عند فتح الصفحة - لا تعرض شيئاً
  var el=document.getElementById('boq-search-results');
  if(el)el.innerHTML='<div class="empty-state"><i class="fa fa-search" style="color:var(--a3)"></i><p>ادخل رقم BOQ للبحث عن الفواتير المرتبطة</p></div>';
  var sub=document.getElementById('boq-sub');
  if(sub)sub.textContent='ابحث برقم BOQ لعرض الفواتير المرتبطة';
}
function boqSearchInv(){
  var q=(document.getElementById('boq-search-q')?.value||'').trim().toLowerCase();
  var el=document.getElementById('boq-search-results');
  var sub=document.getElementById('boq-sub');
  if(!el)return;
  if(!q){
    el.innerHTML='<div class="empty-state"><i class="fa fa-search" style="color:var(--a3)"></i><p>ادخل رقم BOQ للبحث عن الفواتير المرتبطة</p></div>';
    if(sub)sub.textContent='ابحث برقم BOQ لعرض الفواتير المرتبطة';
    return;
  }
  var results=DB.invoices.filter(function(i){return i.boq&&i.boq.toLowerCase().includes(q);});
  if(sub)sub.textContent='نتائج البحث: '+results.length+' فاتورة';
  if(!results.length){
    el.innerHTML='<div class="empty-state"><i class="fa fa-search"></i><p>لا توجد فواتير برقم BOQ يحتوي على "'+q+'"</p></div>';
    return;
  }
  el.innerHTML='<div class="card tbl-wrap" style="margin:0"><table class="tbl"><thead><tr><th>رقم الفاتورة</th><th>رقم BOQ</th><th>النوع</th><th>المستودع</th><th>المقاول</th><th>الموجه</th><th>التاريخ</th><th>الحالة</th><th></th></tr></thead><tbody>'+
  results.map(function(r){
    var boqHl=r.boq.replace(new RegExp('('+q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+')','gi'),'<mark style="background:rgba(255,200,0,.3);border-radius:2px">$1</mark>');
    return '<tr onclick="showInvDetail(\'' +r.no+ '\')" style="cursor:pointer">'+
      '<td class="mono" style="color:var(--a1);font-weight:700">'+r.no+'</td>'+
      '<td style="font-family:monospace;font-size:11px">'+boqHl+'</td>'+
      '<td>'+tag(r.type)+'</td>'+
      '<td style="font-size:12px">'+r.wh+'</td>'+
      '<td style="font-size:12px">'+r.cont+'</td>'+
      '<td style="font-size:12px">'+r.emp+'</td>'+
      '<td style="font-size:11px;color:var(--t3)">'+r.d+'</td>'+
      '<td>'+tag(r.st)+'</td>'+
      '<td style="display:flex;gap:4px">'+
        '<button class="btn btn-sec btn-xs" onclick="event.stopPropagation();showInvDetail(\'' +r.no+ '\')" ><i class="fa fa-eye"></i></button>'+
        '<button class="btn btn-primary btn-xs" onclick="event.stopPropagation();printInvoice(\'' +r.no+ '\')" ><i class="fa fa-print"></i></button>'+
      '</td>'+
    '</tr>';
  }).join('');
}


function boqDetail(no){
  const b=DB.boq.find(x=>x.no===no);if(!b)return;
  showFormModal(`<i class="fa fa-clipboard-list" style="color:var(--a3)"></i> ${no}`,`
    <div style="font-size:13px;color:var(--t2);line-height:2.2">
      <div style="font-size:14px;font-weight:700;color:var(--t1);margin-bottom:6px">${b.desc}</div>
      <div>الحالة: ${tag(b.st)}</div>
      <div>المستودع: <strong style="color:var(--t1)">${b.wh}</strong></div>
      <div>المسؤول: ${b.tech}</div>
      <div>الفواتير المرتبطة: ${b.inv.length?b.inv.map(n=>`<span class="mono" style="font-size:12px">${n}</span>`).join('، '):'لا توجد'}</div>
      <div>التاريخ: <span style="font-family:'JetBrains Mono',monospace">${b.d}</span></div>
    </div>`,
    b.st!=='مغلق'?[{lbl:'<i class="fa fa-check"></i> اغلاق البلاغ',cls:'btn-green',fn:()=>boqClose(no)},{lbl:'<i class="fa fa-cart-shopping"></i> صرف مواد',cls:'btn-primary',fn:()=>{closeModal('modal-form');go('cart');}}]
    :[{lbl:'<i class="fa fa-cart-shopping"></i> صرف مواد',cls:'btn-primary',fn:()=>{closeModal('modal-form');go('cart');}}]);
}
function boqNew(){
  showFormModal('<i class="fa fa-plus" style="color:var(--a3)"></i> BOQ جديد',`
    <div class="form-row c2">
      <div class="form-group"><label class="form-label">رقم BOQ</label><input class="form-input" id="boq-new-no" placeholder="BOQ-2026-..."></div>
      <div class="form-group"><label class="form-label">المستودع</label><select class="form-select" id="boq-new-wh"><option>اسناد</option><option>رايكو صبيا</option><option>هيف بني مالك</option></select></div>
      <div class="form-group" style="grid-column:span 2"><label class="form-label">وصف البلاغ</label><input class="form-input" id="boq-new-desc" placeholder="وصف تفصيلي للبلاغ..."></div>
    </div>`,
    [{lbl:'<i class="fa fa-save"></i> حفظ',cls:'btn-primary',fn:()=>{
      const no=(document.getElementById('boq-new-no')?.value||'').trim();
      const desc=(document.getElementById('boq-new-desc')?.value||'').trim();
      const wh=document.getElementById('boq-new-wh')?.value||'اسناد';
      if(!no||!desc){toast('err','حقول مطلوبة','ادخل رقم BOQ والوصف','fa-triangle-exclamation');return;}
      DB.boq.unshift({no,desc,wh,inv:[],st:'مفتوح',d:today(),tech:currentUser.name});
      closeModal('modal-form');renderBOQ();
      toast('ok','✓ BOQ جديد','تم انشاء '+no+' بنجاح','fa-clipboard-list');
    }}]);
}
function boqClose(no){
  const b=DB.boq.find(x=>x.no===no);if(!b)return;
  showConfirm(`<i class="fa fa-check" style="color:var(--g1)"></i> اغلاق ${no}`,`هل تريد اغلاق البلاغ <strong>${no}</strong>؟`,'اغلاق','btn-green',()=>{
    b.st='مغلق';closeModal('modal-form');renderBOQ();
    toast('ok','✓ اغلاق '+no,'تم اغلاق البلاغ','fa-check');
  });
}

// ══════════════════════ LOGS ══════════════════════
function renderLogs(){
  const q=(document.getElementById('logs-q')?.value||'').toLowerCase();
  const type=document.getElementById('logs-type')?.value||'';
  const dt=document.getElementById('logs-date')?.value||'';
  const empSel=document.getElementById('logs-emp');
  if(empSel&&empSel.options.length===1){
    [...new Set(DB.logs.map(l=>l.emp))].forEach(e=>{const o=document.createElement('option');o.value=e;o.textContent=e;empSel.appendChild(o);});
  }
  const emp=empSel?.value||'';
  // موجه البلاغات يرى سجله فقط
  const logsSource = currentUser?.role==='موجه بلاغات'
    ? DB.logs.filter(l=>l.emp===currentUser.name)
    : DB.logs;
  const items=logsSource.filter(l=>
    (!type||l.type===type)&&
    (!emp||l.emp===emp)&&
    (!dt||l.d===dt)&&
    (!q||l.act.toLowerCase().includes(q)||l.emp.toLowerCase().includes(q))
  );
  document.getElementById('logs-sub').textContent=items.length+' عملية';
  const el=document.getElementById('logs-list');if(!el)return;
  if(!items.length){el.innerHTML=`<div class="empty-state"><i class="fa fa-search"></i><p>لا توجد نتائج</p></div>`;return;}
  el.innerHTML=items.map(function(l){
    // بناء تفاصيل إضافية
    var details='';
    if(l.no) details+='<span class="log-badge mono">'+l.no+'</span>';
    if(l.boq) details+='<span class="log-badge" style="color:var(--a3)">BOQ: '+l.boq+'</span>';
    if(l.cont) details+='<span class="log-badge"><i class="fa fa-hard-hat"></i> '+l.cont+'</span>';
    if(l.receiver) details+='<span class="log-badge" style="color:var(--g1)"><i class="fa fa-arrow-left"></i> المستلم: '+l.receiver+'</span>';
    if(l.approvedBy) details+='<span class="log-badge" style="color:var(--y1)"><i class="fa fa-signature"></i> اعتمد: '+l.approvedBy+'</span>';
    if(l.items) details+='<div class="log-items-detail">'+l.items+'</div>';
    return '<div class="log-item" style="flex-direction:column;align-items:stretch;gap:6px;padding:10px 14px">'+
      '<div style="display:flex;align-items:center;gap:10px">'+
        '<div class="log-ico" style="background:rgba(0,0,0,.2);color:'+l.c+';flex-shrink:0"><i class="fa '+l.i+'"></i></div>'+
        '<div style="flex:1;min-width:0">'+
          '<div class="log-act" style="font-size:13px;font-weight:700;color:var(--t1)">'+l.act+'</div>'+
          '<div class="log-meta" style="margin-top:2px">'+
            '<span style="color:var(--a1)"><i class="fa fa-user"></i> '+l.emp+'</span>'+
            ' &nbsp;·&nbsp; <span><i class="fa fa-warehouse"></i> '+l.wh+'</span>'+
            ' &nbsp;·&nbsp; '+tag(l.type)+
          '</div>'+
        '</div>'+
        '<div class="log-time" style="text-align:left;flex-shrink:0">'+l.d+'<br><span style="color:var(--a1)">'+l.t+'</span></div>'+
      '</div>'+
      (details?'<div style="display:flex;flex-wrap:wrap;gap:5px;padding-right:44px">'+details+'</div>':'')+
    '</div>';
  }).join('');
}

// ══════════════════════ CONTACTS ══════════════════════
function renderContacts(){
  const q=(document.getElementById('contact-q')?.value||'').toLowerCase();
  const dept=document.getElementById('contact-dept')?.value||'';
  const items=DB.contacts.filter(c=>(!q||(c.name.includes(q)||c.role.includes(q)||c.tel.includes(q)))&&(!dept||c.dept===dept));
  const el=document.getElementById('contacts-grid');if(!el)return;
  el.innerHTML=items.map(c=>`
    <div class="cc">
      <div class="cc-av" style="background:${c.color}">${c.av}</div>
      <div class="cc-name">${c.name}</div>
      <div class="cc-role">${c.role}</div>
      <div class="cc-tel"><i class="fa fa-phone" style="color:var(--g1)"></i>${c.tel}</div>
      <div class="cc-actions">
        <button class="btn btn-green btn-xs" onclick="callContact('${c.tel}','${c.name}')"><i class="fa fa-phone"></i>اتصال</button>
        <button class="btn btn-sec btn-xs" onclick="whatsappContact('${c.tel}','${c.name}')"><i class="fa-brands fa-whatsapp"></i>واتساب</button>
        ${currentUser?.role==='مدير النظام'?`<button class="btn btn-warn btn-xs" onclick="contactEdit(${c.id})"><i class="fa fa-pen"></i></button>`:''}
      </div>
    </div>`).join('');
}
function callContact(tel,name){toast('info','اتصال بـ '+name,tel,'fa-phone');}
function whatsappContact(tel,name){window.open('https://wa.me/966'+tel.slice(1),'_blank');toast('ok','واتساب','فتح محادثة مع '+name,'fa-comment');}
function contactNew(){
  if(currentUser?.role==='موجه بلاغات'){toast('err','غير مصرح','ليس لديك صلاحية إضافة أرقام التواصل','fa-lock');return;}
  showFormModal('<i class="fa fa-user-plus" style="color:var(--a1)"></i> اضافة جهة اتصال',`
    <div class="form-row c2">
      <div class="form-group"><label class="form-label">الاسم</label><input class="form-input" id="cn-name" placeholder="الاسم الكامل..."></div>
      <div class="form-group"><label class="form-label">رقم الجوال</label><input class="form-input" id="cn-tel" placeholder="05XXXXXXXX" type="tel"></div>
      <div class="form-group"><label class="form-label">الدور / الوظيفة</label><input class="form-input" id="cn-role" placeholder="مسمى وظيفي..."></div>
      <div class="form-group"><label class="form-label">القسم</label><select class="form-select" id="cn-dept"><option>إدارة</option><option>موجهون</option><option>أمناء مستودعات</option><option>أخرى</option></select></div>
    </div>`,
    [{lbl:'<i class="fa fa-save"></i> حفظ',cls:'btn-primary',fn:()=>{
      const name=(document.getElementById('cn-name')?.value||'').trim();
      const tel=(document.getElementById('cn-tel')?.value||'').trim();
      const role=(document.getElementById('cn-role')?.value||'').trim();
      const dept=document.getElementById('cn-dept')?.value||'أخرى';
      if(!name||!tel){toast('err','حقول مطلوبة','ادخل الاسم ورقم الجوال','fa-triangle-exclamation');return;}
      const cs=['linear-gradient(135deg,#3b82f6,#1d4ed8)','linear-gradient(135deg,#10b981,#059669)','linear-gradient(135deg,#f59e0b,#d97706)','linear-gradient(135deg,#8b5cf6,#7c3aed)'];
      DB.contacts.push({id:Date.now(),name,tel,role:role||'—',dept,av:name.slice(0,2),color:cs[Math.floor(Math.random()*cs.length)]});
      closeModal('modal-form');renderContacts();
      toast('ok','✓ اضيفت','تم اضافة '+name,'fa-user-plus');
    }}]);
}
function contactEdit(id){
  const c=DB.contacts.find(x=>x.id===id);if(!c)return;
  showFormModal(`<i class="fa fa-pen" style="color:var(--y1)"></i> تعديل ${c.name}`,`
    <div class="form-row c2">
      <div class="form-group"><label class="form-label">الاسم</label><input class="form-input" id="ce-name" value="${c.name}"></div>
      <div class="form-group"><label class="form-label">رقم الجوال</label><input class="form-input" id="ce-tel" value="${c.tel}"></div>
      <div class="form-group" style="grid-column:span 2"><label class="form-label">الدور</label><input class="form-input" id="ce-role" value="${c.role}"></div>
    </div>`,
    [{lbl:'<i class="fa fa-save"></i> حفظ',cls:'btn-primary',fn:()=>{
      c.name=(document.getElementById('ce-name')?.value||c.name).trim();
      c.tel=(document.getElementById('ce-tel')?.value||c.tel).trim();
      c.role=(document.getElementById('ce-role')?.value||c.role).trim();
      c.av=c.name.slice(0,2);
      closeModal('modal-form');renderContacts();
      toast('ok','✓ تم التعديل','تم تحديث بيانات '+c.name,'fa-save');
    }},{lbl:'<i class="fa fa-trash"></i> حذف',cls:'btn-danger',fn:()=>{
      showConfirm('حذف '+c.name,'هل تريد حذف جهة اتصال <strong>'+c.name+'</strong>؟','حذف','btn-danger',()=>{
        DB.contacts=DB.contacts.filter(x=>x.id!==id);closeModal('modal-form');renderContacts();
        toast('ok','حُذف','تم حذف '+c.name,'fa-trash');
      });
    }}]);
}

// ══════════════════════ USERS ══════════════════════
function renderUsers(){
  const q=(document.getElementById('users-q')?.value||'').toLowerCase();
  const role=document.getElementById('users-role')?.value||'';
  const items=DB.users.filter(u=>(!q||(u.name.includes(q)||u.role.includes(q)))&&(!role||u.role===role));
  document.getElementById('users-sub').textContent=DB.users.filter(u=>u.active).length+' مستخدمين نشطين';
  const el=document.getElementById('users-list');if(!el)return;
  el.innerHTML=items.map(u=>`
    <div class="user-row">
      <div class="ur-av" style="background:${u.color}">${u.av}</div>
      <div class="ur-info">
        <div class="ur-name">${u.name}</div>
        <div class="ur-role">${tag(u.role)} ${tag(u.active?'نشط':'غير نشط')}</div>
      </div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--t3);flex:1">${u.phone}</div>
      <div class="ur-actions">
        <div class="icon-btn" style="color:var(--a1);border-color:var(--b1);background:rgba(0,212,255,.06)" onclick="userEdit(${u.id})" title="تعديل"><i class="fa fa-pen"></i></div>
        <div class="icon-btn" style="color:${u.active?'var(--r1)':'var(--g1)'};border-color:${u.active?'rgba(239,68,68,.25)':'rgba(16,185,129,.25)'};background:${u.active?'rgba(239,68,68,.07)':'rgba(16,185,129,.07)'}" onclick="userToggle(${u.id})" title="${u.active?'تعطيل':'تفعيل'}">
          <i class="fa ${u.active?'fa-ban':'fa-circle-check'}"></i>
        </div>
        <div class="icon-btn" style="color:var(--y1);border-color:rgba(245,158,11,.25);background:rgba(245,158,11,.07)" onclick="userResetPass(${u.id})" title="تغيير كلمة السر"><i class="fa fa-key"></i></div>
      </div>
    </div>`).join('');
}
function userNew(){
  showFormModal('<i class="fa fa-user-plus" style="color:var(--a3)"></i> مستخدم جديد',`
    <div class="form-row c2">
      <div class="form-group"><label class="form-label">الاسم الكامل</label><input class="form-input" id="un-name" placeholder="احمد محمد..."></div>
      <div class="form-group"><label class="form-label">رقم الجوال</label><input class="form-input" id="un-phone" placeholder="05XXXXXXXX" type="tel"></div>
      <div class="form-group"><label class="form-label">كلمة السر</label><input class="form-input" id="un-pass" placeholder="password123..."></div>
      <div class="form-group"><label class="form-label">الدور</label><select class="form-select" id="un-role"><option>موجه بلاغات</option><option>أمين مستودع</option><option>مدير النظام</option></select></div>
    </div>`,
    [{lbl:'<i class="fa fa-save"></i> اضافة',cls:'btn-primary',fn:()=>{
      const name=(document.getElementById('un-name')?.value||'').trim();
      const phone=(document.getElementById('un-phone')?.value||'').trim();
      const pass=(document.getElementById('un-pass')?.value||'').trim();
      const role=document.getElementById('un-role')?.value||'موجه بلاغات';
      if(!name||!phone||!pass){toast('err','حقول مطلوبة','ادخل جميع البيانات','fa-triangle-exclamation');return;}
      if(DB.users.find(u=>u.phone===phone)){toast('err','جوال مكرر','رقم الجوال مستخدم مسبقاً','fa-triangle-exclamation');return;}
      const cs=['linear-gradient(135deg,#3b82f6,#1d4ed8)','linear-gradient(135deg,#10b981,#059669)','linear-gradient(135deg,#f59e0b,#d97706)','linear-gradient(135deg,#8b5cf6,#7c3aed)','linear-gradient(135deg,#f97316,#ea580c)'];
      const nu={id:Date.now(),phone,pass,name,role,av:name.slice(0,2),color:cs[Math.floor(Math.random()*cs.length)],dept:'أخرى',active:true};
      DB.users.push(nu);
      DB.contacts.push({id:Date.now()+1,name,tel:phone,role,dept:'أخرى',av:nu.av,color:nu.color});
      closeModal('modal-form');renderUsers();
      toast('ok','✓ مستخدم جديد','تم اضافة '+name+' بنجاح','fa-user-plus');
    }}]);
}
function userEdit(id){
  const u=DB.users.find(x=>x.id===id);if(!u)return;
  showFormModal(`<i class="fa fa-pen" style="color:var(--y1)"></i> تعديل ${u.name}`,`
    <div class="form-row c2">
      <div class="form-group"><label class="form-label">الاسم</label><input class="form-input" id="ue-name" value="${u.name}"></div>
      <div class="form-group"><label class="form-label">رقم الجوال</label><input class="form-input" id="ue-phone" value="${u.phone}"></div>
      <div class="form-group"><label class="form-label">الدور</label><select class="form-select" id="ue-role">
        <option ${u.role==='موجه بلاغات'?'selected':''}>موجه بلاغات</option>
        <option ${u.role==='أمين مستودع'?'selected':''}>أمين مستودع</option>
        <option ${u.role==='مدير النظام'?'selected':''}>مدير النظام</option>
        <option ${u.role==='مشرف وردية'?'selected':''}>مشرف وردية</option>
      </select></div>
      <div class="form-group"><label class="form-label">كلمة السر الجديدة</label><input class="form-input" id="ue-pass" placeholder="اتركه فارغاً لعدم التغيير"></div>
    </div>
    <div class="form-group" style="margin-top:6px">
      <label class="form-label"><i class="fa fa-camera" style="color:var(--a3)"></i> صورة الموظف</label>
      <div style="display:flex;align-items:center;gap:12px;margin-top:4px">
        <div id="ue-photo-circle" style="width:52px;height:52px;border-radius:50%;overflow:hidden;background:'+u.color+';display:flex;align-items:center;justify-content:center;flex-shrink:0;border:2px solid var(--b2)">
        </div>
        <div style="flex:1;display:flex;gap:6px;flex-wrap:wrap">
          <input type="file" id="photo-file-input" accept="image/*" style="display:none">
          <button class="btn btn-sec btn-sm" id="ue-photo-pick-btn"><i class="fa fa-upload"></i>رفع صورة</button>
          <span id="ue-photo-del-wrap"></span>
        </div>
      </div>
    </div>`,
    [{lbl:'<i class="fa fa-save"></i> حفظ',cls:'btn-primary',fn:()=>{
      u.name=(document.getElementById('ue-name')?.value||u.name).trim();
      u.phone=(document.getElementById('ue-phone')?.value||u.phone).trim();
      u.role=document.getElementById('ue-role')?.value||u.role;
      const np=(document.getElementById('ue-pass')?.value||'').trim();
      if(np)u.pass=np;
      u.av=u.name.slice(0,2);
      // حفظ الصورة
      if(currentPhotoData==='__delete__'){u.photo='';currentPhotoData=null;}
      else if(currentPhotoData){u.photo=currentPhotoData;currentPhotoData=null;}
      if(u.id===currentUser.id){
        document.getElementById('uname').textContent=u.name;
        document.getElementById('urole').textContent=u.role;
        var uavWrap=document.getElementById('uav-wrap');
        if(uavWrap){
          if(u.photo) uavWrap.innerHTML='<img src="'+u.photo+'" style="width:100%;height:100%;object-fit:cover">';
          else uavWrap.innerHTML='<div class="uav" id="uav" style="font-size:11px;font-weight:800;color:#fff">'+u.av+'</div>';
        }
      }
      closeModal('modal-form');renderUsers();renderEmpMonth();
      toast('ok','✓ تم التعديل','تم تحديث بيانات '+u.name,'fa-save');
    }},{lbl:'<i class="fa fa-trash"></i> حذف الحساب',cls:'btn-danger',fn:()=>{
      if(u.id===currentUser.id){toast('err','لا يمكن','لا يمكنك حذف حسابك الحالي','fa-ban');return;}
      showConfirm('<i class="fa fa-trash" style="color:var(--r1)"></i> حذف '+u.name,
        'هل أنت متأكد من حذف حساب <strong>'+u.name+'</strong> نهائياً؟<br><br><span style="color:var(--r1);font-size:12px">⚠ هذا الإجراء لا يمكن التراجع عنه</span>',
        'حذف نهائياً','btn-danger',()=>{
          DB.users=DB.users.filter(x=>x.id!==u.id);
          closeModal('modal-form');renderUsers();
          toast('ok','حُذف','تم حذف حساب '+u.name+' نهائياً','fa-trash');
        });
    }}]);
  // تهيئة دائرة الصورة بعد فتح النموذج
  setTimeout(function(){
    var circle=document.getElementById('ue-photo-circle');
    if(circle){
      circle.innerHTML=u.photo?
        '<img src="'+u.photo+'" style="width:100%;height:100%;object-fit:cover;border-radius:50%">':
        '<div style="font-size:18px;font-weight:800;color:#fff">'+u.av+'</div>';
    }
    var delWrap=document.getElementById('ue-photo-del-wrap');
    if(delWrap&&u.photo){
      delWrap.innerHTML='<button class="btn btn-danger btn-sm" id="del-photo-btn"><i class="fa fa-trash"></i>حذف</button>';
      var delBtn=document.getElementById('del-photo-btn');
      if(delBtn)delBtn.onclick=function(){
        var c=document.getElementById('ue-photo-circle');
        if(c)c.innerHTML='<div style="font-size:18px;font-weight:800;color:#fff">'+u.av+'</div>';
        currentPhotoData='__delete__';
        delWrap.innerHTML='';
      };
    }
    var pickBtn=document.getElementById('ue-photo-pick-btn');
    if(pickBtn)pickBtn.onclick=function(){document.getElementById('photo-file-input').click();};
    var fileInp=document.getElementById('photo-file-input');
    if(fileInp)fileInp.onchange=function(){
      var file=this.files[0];if(!file)return;
      var reader=new FileReader();
      reader.onload=function(e){
        currentPhotoData=e.target.result;
        var c=document.getElementById('ue-photo-circle');
        if(c)c.innerHTML='<img src="'+e.target.result+'" style="width:100%;height:100%;object-fit:cover;border-radius:50%">';
      };
      reader.readAsDataURL(file);
    };
  },150);
}
function userToggle(id){
  const u=DB.users.find(x=>x.id===id);if(!u)return;
  if(u.id===currentUser.id){toast('err','لا يمكن','لا يمكنك تعطيل حسابك الحالي','fa-ban');return;}
  showConfirm((u.active?'تعطيل':'تفعيل')+' '+u.name,'هل تريد '+(u.active?'تعطيل':'تفعيل')+' حساب <strong>'+u.name+'</strong>؟',u.active?'تعطيل':'تفعيل',u.active?'btn-danger':'btn-green',()=>{
    u.active=!u.active;renderUsers();
    toast(u.active?'ok':'warn',u.active?'تفعيل':'تعطيل',u.name+' — '+(u.active?'نشط الان':'معطّل الان'),u.active?'fa-circle-check':'fa-ban');
  });
}
function userResetPass(id){
  const u=DB.users.find(x=>x.id===id);if(!u)return;
  showFormModal(`<i class="fa fa-key" style="color:var(--y1)"></i> تغيير كلمة سر ${u.name}`,`
    <div class="form-group"><label class="form-label">كلمة السر الجديدة</label><input class="form-input" id="urp-pass" type="password" placeholder="كلمة السر الجديدة..."></div>
    <div class="form-group"><label class="form-label">تأكيد كلمة السر</label><input class="form-input" id="urp-conf" type="password" placeholder="اعد الكتابة..."></div>`,
    [{lbl:'<i class="fa fa-key"></i> تغيير',cls:'btn-warn',fn:()=>{
      const np=(document.getElementById('urp-pass')?.value||'').trim();
      const cf=(document.getElementById('urp-conf')?.value||'').trim();
      if(!np){toast('err','حقل مطلوب','ادخل كلمة السر الجديدة','fa-lock');return;}
      if(np!==cf){toast('err','خطأ','كلمتا السر غير متطابقتين','fa-lock');return;}
      u.pass=np;closeModal('modal-form');
      toast('ok','✓ تم التغيير','تم تغيير كلمة سر '+u.name,'fa-key');
    }}]);
}

// ══════════════════════ SETTINGS ══════════════════════
function renderSettings(){
  const s=DB.settings;

  document.getElementById('settings-content').innerHTML=`
    <div class="setting-sec">
      <div class="ss-title"><i class="fa fa-toggle-on" style="color:var(--a1)"></i>اعدادات عامة</div>
      ${[['autoNotif','الاشعارات التلقائية'],['supabaseSync','مزامنة Supabase'],['autoBackup','نسخ احتياطي تلقائي'],['logAll','تسجيل جميع العمليات'],['autoApproveFeed','اعتماد تلقائي للتغذية'],['maintenance','وضع الصيانة']].map(([k,l])=>`
        <div class="toggle-row"><span>${l}</span><div class="tog ${s[k]?'on':''}" onclick="toggleSetting('${k}',this)"></div></div>`).join('')}
    </div>
    <div class="setting-sec">
      <div class="ss-title"><i class="fa fa-hard-drive" style="color:var(--y1)"></i>النسخ الاحتياطية</div>
      <div class="toggle-row"><span>آخر نسخة</span><span style="color:var(--t1);font-family:'JetBrains Mono',monospace;font-size:11px">اليوم 04:00</span></div>
      <div class="toggle-row"><span>حجم قاعدة البيانات</span><span style="color:var(--t1)">2.4 MB</span></div>
      <div class="toggle-row"><span>النسخ المحفوظة</span><span style="color:var(--t1)">30 نسخة</span></div>
      <div class="toggle-row"><span>Supabase</span><span class="tag tg-green">متصل</span></div>
      <button class="btn btn-green" style="width:100%;justify-content:center;margin-top:10px" onclick="doBackup()"><i class="fa fa-hard-drive"></i>نسخة احتياطية الان</button>
    </div>
    <div class="setting-sec">
      <div class="ss-title"><i class="fa fa-shield-halved" style="color:var(--g1)"></i>الأمان</div>
      ${[['twoFA','المصادقة الثنائية'],['ipRestrict','تقييد IP'],['sessionTimeout','انتهاء الجلسة (30 دقيقة)']].map(([k,l])=>`
        <div class="toggle-row"><span>${l}</span><div class="tog ${s[k]?'on':''}" onclick="toggleSetting('${k}',this)"></div></div>`).join('')}
      <div style="margin-top:12px;display:flex;flex-direction:column;gap:7px">
        <button class="btn btn-warn" style="width:100%;justify-content:center" onclick="changeMyPass()"><i class="fa fa-key"></i>تغيير كلمة المرور</button>
        <button class="btn btn-danger" style="width:100%;justify-content:center" onclick="clearLogs()"><i class="fa fa-trash"></i>مسح سجل العمليات القديم</button>
      </div>
    </div>`;
  // عرض النسخ الاحتياطية وموظف الشهر
  renderBackups();
  renderEmpMonth();
  // إضافة زر الحفظ
  document.querySelectorAll('[data-s-key]').forEach(function(el){
    el.addEventListener('change',function(){
      var key=this.dataset.sKey,val=this.type==='checkbox'?this.checked:this.value;
      if(DB.settings)DB.settings[key]=val;
    });
  });
}
function toggleSetting(k,el){DB.settings[k]=!DB.settings[k];el.classList.toggle('on',DB.settings[k]);toast('ok','تم','تم تحديث الاعداد','fa-toggle-on');}
function saveSettings(){toast('ok','✓ حفظ الاعدادات','تم حفظ جميع الاعدادات بنجاح','fa-save');}
function doBackup(){toast('ok','✓ نسخة احتياطية','تم انشاء نسخة احتياطية يدوية بنجاح','fa-hard-drive');}
function clearLogs(){
  var cutoff=new Date();
  cutoff.setDate(cutoff.getDate()-30);
  var cutoffStr=cutoff.toISOString().slice(0,10);
  var toDelete=DB.logs.filter(function(l){return l.d<cutoffStr;}).length;
  if(!toDelete){toast('info','لا يوجد ما يُحذف','لا توجد سجلات أقدم من 30 يوماً','fa-info-circle');return;}
  showConfirm('<i class="fa fa-trash" style="color:var(--r1)"></i> مسح السجل القديم',
    'سيتم حذف <strong>'+toDelete+'</strong> سجل أقدم من 30 يوماً.<br>هذا الإجراء لا يمكن التراجع عنه.',
    'مسح','btn-danger',function(){
      DB.logs=DB.logs.filter(function(l){return l.d>=cutoffStr;});
      renderLogs();
      toast('ok','✓ تم المسح','تم حذف '+toDelete+' سجل قديم','fa-trash');
    });
}
function changeMyPass(){
  showFormModal('<i class="fa fa-key" style="color:var(--y1)"></i> تغيير كلمة المرور',`
    <div class="form-group"><label class="form-label">كلمة المرور الحالية</label><input class="form-input" id="cp-old" type="password"></div>
    <div class="form-group"><label class="form-label">كلمة المرور الجديدة</label><input class="form-input" id="cp-new" type="password"></div>
    <div class="form-group"><label class="form-label">تأكيد كلمة المرور</label><input class="form-input" id="cp-conf" type="password"></div>`,
    [{lbl:'<i class="fa fa-key"></i> تغيير',cls:'btn-warn',fn:()=>{
      const old=document.getElementById('cp-old')?.value;
      const nw=document.getElementById('cp-new')?.value;
      const cf=document.getElementById('cp-conf')?.value;
      if(old!==currentUser.pass){toast('err','خطأ','كلمة المرور الحالية غير صحيحة','fa-lock');return;}
      if(!nw||nw.length<6){toast('err','خطأ','كلمة المرور الجديدة قصيرة جداً (6 احرف على الاقل)','fa-lock');return;}
      if(nw!==cf){toast('err','خطأ','كلمتا المرور غير متطابقتين','fa-lock');return;}
      currentUser.pass=nw;
      const u=DB.users.find(x=>x.id===currentUser.id);if(u)u.pass=nw;
      closeModal('modal-form');
      toast('ok','✓ تم التغيير','تم تغيير كلمة المرور بنجاح','fa-key');
    }}]);
}

// ══════════════════════ SEARCH ══════════════════════
function openSearch(){openModal('modal-search');setTimeout(()=>document.getElementById('search-q')?.focus(),200);}
function renderSearchResults(q){
  const el=document.getElementById('search-results');if(!el||!q)return el&&(el.innerHTML='');
  q=q.toLowerCase();
  const invR=DB.invoices.filter(i=>i.no.toLowerCase().includes(q)||i.cont.toLowerCase().includes(q)||i.emp.toLowerCase().includes(q)).slice(0,4);
  const invI=DB.inventory.filter(i=>i.code.toLowerCase().includes(q)||i.name.toLowerCase().includes(q)).slice(0,3);
  const cts=DB.contacts.filter(c=>c.name.includes(q)||c.tel.includes(q)).slice(0,3);
  let html='';
  if(invR.length){html+=`<div style="font-size:9.5px;color:var(--t3);font-weight:700;letter-spacing:1.5px;margin:6px 0 5px">الفواتير</div>`;
    html+=invR.map(r=>`<div class="hist-item" style="margin-bottom:5px;cursor:pointer" onclick="closeModal('modal-search');showInvDetail('${r.no}')">
      <div class="hist-ico" style="background:rgba(0,102,255,.1);color:var(--a1)"><i class="fa fa-file-invoice"></i></div>
      <div class="hist-info"><div style="display:flex;gap:6px;flex-wrap:wrap">${tag(r.no)} ${tag(r.type)} ${tag(r.st)}</div><div class="hist-meta">${r.emp} — ${r.cont}</div></div>
    </div>`).join('');}
  if(invI.length){html+=`<div style="font-size:9.5px;color:var(--t3);font-weight:700;letter-spacing:1.5px;margin:8px 0 5px">المواد</div>`;
    html+=invI.map(i=>`<div class="hist-item" style="margin-bottom:5px;cursor:pointer" onclick="closeModal('modal-search');go('inventory')">
      <div class="hist-ico" style="background:rgba(0,212,255,.1);color:var(--a1)"><i class="fa fa-box"></i></div>
      <div class="hist-info"><div class="hist-code">${i.code}</div><div class="hist-name">${i.name} — اجمالي: ${i.asnad+i.raiko+i.manatiq}</div></div>
    </div>`).join('');}
  if(cts.length){html+=`<div style="font-size:9.5px;color:var(--t3);font-weight:700;letter-spacing:1.5px;margin:8px 0 5px">جهات الاتصال</div>`;
    html+=cts.map(c=>`<div class="hist-item" style="margin-bottom:5px;cursor:pointer" onclick="closeModal('modal-search');go('contact')">
      <div class="hist-ico" style="background:${c.color}"><span style="color:#fff;font-weight:700;font-size:11px">${c.av}</span></div>
      <div class="hist-info"><div class="hist-name">${c.name}</div><div class="hist-meta">${c.role} — ${c.tel}</div></div>
    </div>`).join('');}
  if(!html)html=`<div style="color:var(--t3);font-size:13px;padding:18px 0;text-align:center"><i class="fa fa-search" style="display:block;font-size:24px;opacity:.2;margin-bottom:8px"></i>لا توجد نتائج لـ "${q}"</div>`;
  el.innerHTML=html;
}

// ══════════════════════ NOTIFICATIONS ══════════════════════
function openNotifs(){
  DB.notifications.forEach(n=>n.read=true);updateBadges();
  document.getElementById('notifs-list').innerHTML=DB.notifications.slice(0,10).map(n=>{
    const c=TC[n.type]||TC.info;
    return `<div class="hist-item" style="margin-bottom:7px">
      <div class="hist-ico" style="background:${c.bg};color:${c.c}"><i class="fa ${n.i}"></i></div>
      <div class="hist-info"><div class="hist-name">${n.title}</div><div class="hist-meta">${n.msg}</div></div>
      <div class="hist-meta" style="flex-shrink:0;text-align:left">${n.time}</div>
    </div>`;
  }).join('')||`<div style="color:var(--t3);text-align:center;padding:20px">لا توجد اشعارات</div>`;
  openModal('modal-notifs');
}
function clearNotifs(){DB.notifications=[];updateBadges();openNotifs();toast('ok','مقروء','تم تعيين جميع الاشعارات كمقروءة','fa-check-double');}

// ══════════════════════ USER PROFILE ══════════════════════
function showUserProfile(){
  showFormModal(`<span style="display:flex;align-items:center;gap:10px"><div style="width:30px;height:30px;border-radius:7px;background:${currentUser.color};display:flex;align-items:center;justify-content:center;font-weight:700;font-size:11px">${currentUser.av}</div>${currentUser.name}</span>`,`
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:13px">
      <div><span style="color:var(--t3)">الدور: </span>${tag(currentUser.role)}</div>
      <div><span style="color:var(--t3)">الحالة: </span>${tag('نشط')}</div>
      <div><span style="color:var(--t3)">الجوال: </span><span style="font-family:'JetBrains Mono',monospace">${currentUser.phone}</span></div>
      <div><span style="color:var(--t3)">فواتيري: </span><strong>${DB.invoices.filter(i=>i.emp===currentUser.name).length}</strong></div>
    </div>`,
    [{lbl:'<i class="fa fa-file-invoice"></i> فواتيري',cls:'btn-sec',fn:()=>{closeModal('modal-form');go('myinv');}},
     {lbl:'<i class="fa fa-key"></i> تغيير كلمة المرور',cls:'btn-warn',fn:()=>{closeModal('modal-form');go('settings');setTimeout(changeMyPass,200);}},
     {lbl:'<i class="fa fa-right-from-bracket"></i> خروج',cls:'btn-danger',fn:()=>{closeModal('modal-form');doLogout();}}]);
}
function showSysInfo(){toast('info','السعودية للكهرباء','نظام ادارة مواد الطوارئ — دائرة شرق جازان','fa-building');}

// ══════════════════════ TOPBAR ══════════════════════
document.addEventListener('DOMContentLoaded',()=>{});
const _st=document.createElement('style');
_st.textContent='@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}';
document.head.appendChild(_st);
function doSync(){
  const ico=document.getElementById('sync-ico');
  ico.style.animation='spin 1.2s linear infinite';
  setTimeout(()=>{ico.style.animation='';toast('ok','✓ مزامنة Supabase','تمت المزامنة بنجاح — قاعدة البيانات محدّثة','fa-database');},1600);
}
function toggleFullscreen(){
  const ico=document.getElementById('fs-ico');
  if(!document.fullscreenElement){document.documentElement.requestFullscreen().catch(()=>{});ico.className='fa fa-compress';}
  else{document.exitFullscreen();ico.className='fa fa-expand';}
}
function exportToExcel(rows,filename,sheetName){
  sheetName=sheetName||'البيانات';
  filename=filename+'_'+today()+'.xlsx';
  try{
    if(typeof XLSX==='undefined'){
      toast('err','خطأ','مكتبة Excel غير محملة، تحقق من الاتصال بالإنترنت','fa-triangle-exclamation');
      return;
    }
    var wb=XLSX.utils.book_new();
    var ws=XLSX.utils.aoa_to_sheet(rows);
    // ضبط اتجاه الورقة لليمين (RTL)
    if(!ws['!cols'])ws['!cols']=[];
    // ضبط عرض الأعمدة تلقائياً
    var colWidths=[];
    rows.forEach(function(row){
      row.forEach(function(cell,ci){
        var len=String(cell||'').length;
        if(!colWidths[ci]||len>colWidths[ci])colWidths[ci]=len;
      });
    });
    ws['!cols']=colWidths.map(function(w){return {wch:Math.min(Math.max(w+2,10),50)};});
    XLSX.utils.book_append_sheet(wb,ws,sheetName);
    XLSX.writeFile(wb,filename);
    toast('ok','✓ تم التصدير','تم تصدير '+filename+' بنجاح','fa-file-excel');
  }catch(err){
    console.error(err);
    toast('err','خطأ في التصدير',String(err),'fa-triangle-exclamation');
  }
}
// احتفظ باسم قديم للتوافق
function exportToCSV(rows,filename){exportToExcel(rows,filename);}

function exportTable(id,name){
  var rows=[['كود المادة','اسم المادة','الفئة','اسناد','رايكو صبيا','هيف بني مالك','الإجمالي','المستوى']];
  DB.inventory.forEach(function(i){
    var tot=i.asnad+i.raiko+i.manatiq;
    var cat=DB.categories.find(function(cc){return cc.name===i.cat;});
    var crit=cat?cat.criticalLimit:i.min;
    var warn=cat?cat.warningLimit:i.min*2;
    var level=tot<=crit?'حرج':tot<=warn?'تحذير':'آمن';
    rows.push([i.code,i.name,i.cat,i.asnad,i.raiko,i.manatiq,tot,level]);
  });
  exportToExcel(rows,'رصيد_المستودعات','رصيد المستودعات');
}

function exportInvoicesCSV(){
  var rows=[['رقم الفاتورة','النوع','الحالة','المستودع','المقاول','الموجه','رقم BOQ','التاريخ','المواد','وصف البلاغ']];
  DB.invoices.forEach(function(inv){
    var itemsSummary=inv.items.map(function(it){return it.code+' '+it.name+' x'+it.qty;}).join(' | ');
    rows.push([inv.no,inv.type,inv.st,inv.wh,inv.cont,inv.emp,inv.boq||'',inv.d,itemsSummary,inv.notes||'']);
  });
  exportToExcel(rows,'أرشيف_الفواتير','أرشيف الفواتير');
}

function exportLogs(){
  var rows=[['التاريخ','الوقت','النوع','العملية','الموظف','المستودع','رقم الفاتورة','المقاول','رقم BOQ','المواد']];
  DB.logs.forEach(function(l){
    rows.push([l.d,l.t,l.type,l.act,l.emp,l.wh,l.no||'',l.cont||'',l.boq||'',l.items||'']);
  });
  exportToExcel(rows,'سجل_العمليات','سجل العمليات');
}

// ══════════════════════ CLOCK ══════════════════════
function tick(){const n=new Date();const p=x=>String(x).padStart(2,'0');const el=document.getElementById('clock');if(el)el.textContent=p(n.getHours())+':'+p(n.getMinutes())+':'+p(n.getSeconds());}
setInterval(tick,1000);tick();

// ══════════════════════ KEYBOARD ══════════════════════
document.addEventListener('keydown',e=>{
  if((e.ctrlKey||e.metaKey)&&e.key==='k'){e.preventDefault();if(document.getElementById('shell').classList.contains('show'))openSearch();}
  if(e.key==='Escape'){['modal-search','modal-notifs','modal-form','modal-confirm','modal-inv'].forEach(closeModal);}
});

// ══════════════════════ LIVE NOTIFICATIONS ══════════════════════
const LIVE=[
  ['warn','طلب ارجاع جديد','محمد صميلي — اسناد — 3 محولات 100KVA','fa-rotate-left'],
  ['ok','اعتماد فاتورة','تم اعتماد فاتورة G47 بنجاح','fa-signature'],
  ['err','تنبيه مخزون','محول 500KVA وصل للحد الادنى','fa-triangle-exclamation'],
  ['info','مزامنة Supabase','تمت مزامنة 24 عملية جديدة','fa-database'],
  ['ok','نسخة احتياطية','تم انشاء نسخة احتياطية تلقائية','fa-hard-drive'],
];
let _lni=0;
function startLiveNotifs(){
  runStartupChecks();
  // لا interval - الاشعارات تُضاف فقط عند الأحداث الحقيقية
}
// ══════════════════════════════════════════════════════
// INVOICE PRINT PREVIEW
// ══════════════════════════════════════════════════════
function printInvoice(no){
  const inv=DB.invoices.find(i=>i.no===no);
  // إذا لم توجد في الأرشيف جرب الاعتمادات
  if(!inv){
    printApprovalInvoice(no);
    return;
  }

  // ختم الملغي للطباعة
  const cancelledStamp=inv.st==='ملغي'?'<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-35deg);pointer-events:none;z-index:99;opacity:.15"><div style="border:12px solid #cc0000;border-radius:14px;padding:10px 30px"><div style="color:#cc0000;font-size:80px;font-weight:900;font-family:Cairo,sans-serif;letter-spacing:6px">ملغـي</div></div></div>':'';
  const typeLabel={صرف:'فاتورة صرف مواد طوارئ',ارجاع:'فاتورة إرجاع مواد طوارئ',نقل:'فاتورة نقل مواد طوارئ بين المستودعات',الغاء:'فاتورة إلغاء صرف مواد'}[inv.type]||'فاتورة '+inv.type;
  const C='#0055aa';
  const logoEl=document.querySelector('.logo-emblem img');
  const logoSrc=logoEl?logoEl.src:'';

  const sigs=inv.type==='صرف'
    ?[{lbl:'توقيع أمين المستودع المسلّم',name:inv.wh},{lbl:'توقيع المقاول المستلم',name:inv.cont}]
    :inv.type==='ارجاع'
    ?[{lbl:'توقيع المقاول المُسلِّم للمواد',name:inv.cont},{lbl:'توقيع أمين المستودع المستلم',name:inv.wh}]
    :inv.type==='نقل'
    ?[{lbl:'توقيع أمين المستودع الناقل',name:inv.cont||'المستودع المُصدِّر'},{lbl:'توقيع أمين المستودع المستلم',name:inv.wh}]
    :[{lbl:'توقيع أمين المستودع',name:inv.wh}];

  const metaLeft=[['المستودع',inv.wh],['المقاول / الجهة',inv.cont],['موجه البلاغ',inv.emp]];
  const metaRight=[['التاريخ',inv.d]];
  if(inv.boq)metaRight.push(['رقم BOQ',inv.boq]);
  if(inv.notes)metaRight.push(['وصف البلاغ',inv.notes]);

  const html=`
<div style="font-family:'Cairo',Tahoma,Arial,sans-serif;direction:rtl;background:#fff;color:#1a1a2e;width:100%;box-sizing:border-box;position:relative">
${cancelledStamp}

  <!-- ══ HEADER ══ -->
  <div style="background:${C};padding:18px 28px 14px;display:flex;align-items:center;justify-content:space-between">
    <div style="text-align:center">
      ${logoSrc?`<img src="${logoSrc}" style="width:90px;height:90px;object-fit:contain;background:#fff;border-radius:10px;padding:6px">`:
      `<div style="width:90px;height:90px;background:rgba(255,255,255,.2);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:28px;color:#fff;font-weight:900">SE</div>`}
    </div>
    <div style="text-align:center;flex:1;padding:0 20px">
      <div style="color:rgba(255,255,255,.7);font-size:10px;letter-spacing:2px;text-transform:uppercase;margin-bottom:5px">السعودية للطاقة</div>
      <div style="color:#fff;font-size:20px;font-weight:900;line-height:1.2">${typeLabel}</div>
      <div style="color:rgba(255,255,255,.6);font-size:9px;margin-top:4px">دائرة شرق منطقة جازان — نظام إدارة مواد الطوارئ</div>
    </div>
    <div style="text-align:center;background:rgba(255,255,255,.12);border:2px solid rgba(255,255,255,.3);border-radius:10px;padding:12px 20px;min-width:100px">
      <div style="color:rgba(255,255,255,.6);font-size:9px;letter-spacing:1px;margin-bottom:4px">رقم الفاتورة</div>
      <div style="color:#fff;font-size:22px;font-weight:900;font-family:monospace;letter-spacing:3px">${inv.no}</div>
      <div style="color:rgba(255,255,255,.6);font-size:9px;margin-top:4px">${inv.d}</div>
    </div>
  </div>

  <!-- ══ META STRIP ══ -->
  <div style="background:#f0f6ff;border-bottom:2px solid ${C}20;padding:12px 28px;display:flex;gap:0">
    <div style="flex:1;padding-left:24px;border-left:1px solid ${C}20">
      ${metaLeft.map(([l,v])=>`<div style="display:flex;align-items:baseline;gap:8px;margin-bottom:5px"><span style="font-size:9px;font-weight:700;color:${C};min-width:90px;flex-shrink:0">${l}</span><span style="font-size:12px;color:#222;font-weight:600;border-bottom:1px dashed #cce;flex:1;padding-bottom:1px">${v}</span></div>`).join('')}
    </div>
    <div style="flex:1;padding-right:24px">
      ${metaRight.map(([l,v])=>`<div style="display:flex;align-items:baseline;gap:8px;margin-bottom:5px"><span style="font-size:9px;font-weight:700;color:${C};min-width:70px;flex-shrink:0">${l}</span><span style="font-size:12px;color:#222;font-weight:600;border-bottom:1px dashed #cce;flex:1;padding-bottom:1px">${v}</span></div>`).join('')}
    </div>
  </div>

  <!-- ══ ITEMS TABLE ══ -->
  <div style="padding:16px 28px">
    <div style="font-size:10px;font-weight:700;color:${C};letter-spacing:2px;margin-bottom:8px;text-transform:uppercase">المواد المشمولة في الفاتورة</div>
    <table style="width:100%;border-collapse:collapse;border:1.5px solid ${C}30;border-radius:8px;overflow:hidden">
      <thead>
        <tr style="background:${C}">
          <th style="padding:9px 14px;color:#fff;font-size:10.5px;font-weight:700;text-align:center;width:36px">م</th>
          <th style="padding:9px 14px;color:#fff;font-size:10.5px;font-weight:700;text-align:right">كود المادة</th>
          <th style="padding:9px 14px;color:#fff;font-size:10.5px;font-weight:700;text-align:right">اسم المادة</th>
          <th style="padding:9px 14px;color:#fff;font-size:10.5px;font-weight:700;text-align:center;width:80px">الكمية</th>
        </tr>
      </thead>
      <tbody>
        ${inv.items.map((it,i)=>`
        <tr style="background:${i%2===0?'#fff':'#f7faff'};border-bottom:1px solid ${C}12">
          <td style="padding:9px 14px;text-align:center;font-size:11px;color:#888">${i+1}</td>
          <td style="padding:9px 14px;font-family:monospace;font-size:11.5px;color:${C};font-weight:700">${it.code}</td>
          <td style="padding:9px 14px;font-size:12.5px;color:#1a1a2e;font-weight:500">${it.name}</td>
          <td style="padding:9px 14px;text-align:center;font-size:16px;font-weight:900;color:${C};font-family:monospace">${it.qty}</td>
        </tr>`).join('')}
      </tbody>
    </table>
  </div>

  <!-- ══ SIGNATURES ══ -->
  <div style="padding:4px 28px 20px">
    <div style="font-size:10px;font-weight:700;color:${C};letter-spacing:2px;margin-bottom:10px;text-transform:uppercase">خانات التوقيع</div>
    <div style="display:grid;grid-template-columns:repeat(${sigs.length},1fr);gap:14px">
      ${sigs.map(s=>`
      <div style="border:1.5px solid ${C}30;border-radius:10px;overflow:hidden;text-align:center">
        <div style="background:${C}0d;padding:8px 14px;border-bottom:1px solid ${C}20;text-align:center">
          <div style="font-size:9.5px;font-weight:700;color:${C};text-align:center">${s.lbl}</div>
          <div style="font-size:11px;color:#333;margin-top:2px;font-weight:600;text-align:center">${s.name}</div>
        </div>
        <div style="padding:28px 14px 10px;text-align:center">
          <div style="border-bottom:1.5px solid #222;margin:0 10px 6px"></div>
          <div style="font-size:9px;color:#aaa;text-align:center">التوقيع</div>
        </div>
      </div>`).join('')}
    </div>
  </div>

  <!-- ══ FOOTER ══ -->
  <div style="background:#f0f6ff;border-top:2px solid ${C}20;padding:8px 28px;display:flex;justify-content:space-between;align-items:center">
    <span style="font-size:9px;color:#888">طُبع بواسطة: <strong style="color:${C}">${inv.emp}</strong></span>
    <span style="font-size:9px;color:#bbb">${new Date().toLocaleString('ar-SA')}</span>
    <span style="font-size:9px;color:#888">نظام إدارة مواد الطوارئ — السعودية للطاقة</span>
  </div>

</div>`;

  let ov=document.getElementById('print-overlay');
  if(ov)ov.remove();
  ov=document.createElement('div');
  ov.id='print-overlay';
  ov.style.cssText='position:fixed;inset:0;background:rgba(0,5,20,.92);z-index:9000;display:flex;flex-direction:column;align-items:center;overflow-y:auto;padding:16px';
  const bar=document.createElement('div');
  bar.style.cssText=`display:flex;gap:8px;margin-bottom:14px;position:sticky;top:0;z-index:1;background:rgba(0,5,20,.96);padding:10px 16px;border-radius:10px;border:1px solid ${C}50;width:720px;max-width:96vw;box-sizing:border-box;align-items:center`;
  bar.innerHTML=`
    <button onclick="window.print()" style="padding:9px 20px;background:${C};color:#fff;border:none;border-radius:8px;cursor:pointer;font-family:'Cairo',sans-serif;font-size:13px;font-weight:700;display:flex;align-items:center;gap:7px;flex-shrink:0">
      <i class="fa fa-print"></i>طباعة / PDF
    </button>
    <button onclick="document.getElementById('print-overlay').remove()" style="padding:9px 16px;background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.3);color:#f87171;border-radius:8px;cursor:pointer;font-family:'Cairo',sans-serif;font-size:13px;flex-shrink:0">
      <i class="fa fa-times"></i> اغلاق
    </button>
    <span style="color:rgba(255,255,255,.4);font-size:11px;margin-right:6px;flex:1;text-align:center">${typeLabel} — <span style="color:rgba(255,255,255,.7);font-family:monospace">${inv.no}</span></span>`;
  const wrap=document.createElement('div');
  wrap.style.cssText='width:720px;max-width:96vw;box-shadow:0 20px 60px rgba(0,0,0,.7);border-radius:12px;overflow:hidden';
  wrap.innerHTML=html;
  ov.appendChild(bar);ov.appendChild(wrap);
  document.body.appendChild(ov);
  ov.addEventListener('click',e=>{if(e.target===ov)ov.remove();});
}

// ══════════════════════════════════════════════════════
// WAREHOUSES MANAGEMENT
// ══════════════════════════════════════════════════════
function printApprovalInvoice(no){
  var a=DB.approvals.find(function(x){return x.no===no;});
  if(!a){toast('err','غير موجودة','لا توجد فاتورة بهذا الرقم','fa-ban');return;}
  // بناء كائن الفاتورة من بيانات الاعتماد
  var parsedItems=[];
  if(Array.isArray(a.items)){parsedItems=a.items;}
  else if(typeof a.items==='string'){
    parsedItems=a.items.split(' + ').map(function(s){
      var m=s.match(/(.+) x(\d+)/);
      return m?{code:'—',name:m[1],qty:parseInt(m[2])}:{code:'—',name:s,qty:0};
    });
  }
  var inv={no:a.no,type:'صرف',wh:a.wh,cont:a.cont,emp:a.emp,st:'معلق',d:a.d,items:parsedItems,boq:a.boq||'',notes:a.notes||''};
  // أضفها مؤقتاً لـ DB.invoices لاستخدام printInvoice
  var tmpAdded=false;
  if(!DB.invoices.find(function(i){return i.no===inv.no;})){
    DB.invoices.unshift(inv);
    tmpAdded=true;
  }
  printInvoice(no);
  // احذفها بعد الطباعة إذا كانت مؤقتة
  if(tmpAdded){
    setTimeout(function(){
      DB.invoices=DB.invoices.filter(function(i){return i.no!==no||i.st!=='معلق';});
    },500);
  }
}

// ══════════════════════════════════════════════
// رصيد الزونات الجغرافية
// ══════════════════════════════════════════════
var currentZone = null;


// ══ renderZonesPage — تهيئة صفحة الزونات ══
function renderZonesPage(){
  currentZone=null;
  var content=document.getElementById('zones-content');
  var btn=document.getElementById('btn-zones-export');
  var sub=document.getElementById('zones-sub');
  if(content) content.style.display='none';
  if(btn) btn.style.display='none';
  if(sub) sub.textContent='اختر زوناً لعرض مستوى مواده';
  renderZones();
  updateZonesBadge();
}

// ══ renderZonesManage — إدارة الزونات في الإعدادات ══
function renderZonesManage(){
  var el=document.getElementById('zones-manage-list');if(!el)return;
  el.innerHTML=DB.zones.map(function(z){
    var whCount=DB.warehouses.filter(function(w){return w.active&&w.zone===z.id;}).length;
    return '<div style="display:flex;align-items:center;gap:10px;background:'+(z.bg||'var(--bg2)')+';border:1px solid '+(z.border||'var(--b1)')+';border-radius:10px;padding:8px 14px">'+
      '<i class="fa '+(z.icon||'fa-map')+'" style="color:'+(z.color||'var(--a1)')+'"></i>'+
      '<div><div style="font-size:12px;font-weight:700;color:var(--t1)">'+z.name+'</div>'+
      '<div style="font-size:10.5px;color:var(--t3)">'+whCount+' مستودع</div></div>'+
      '<button class="btn btn-warn btn-xs" onclick="editZone(\''+z.id+'\')" ><i class="fa fa-pen"></i>تعديل</button>'+
      (whCount===0?'<button class="btn btn-danger btn-xs" onclick="deleteZone(\''+z.id+'\')" ><i class="fa fa-trash"></i>حذف</button>':'')+
    '</div>';
  }).join('')+(DB.zones.length===0?'<div style="color:var(--t3);font-size:12px;padding:8px">لا توجد زونات</div>':'');
}

function renderZones(){
  // بطاقات الزونات
  var cardsEl = document.getElementById('zones-cards');
  if(!cardsEl) return;
  
  cardsEl.innerHTML = DB.zones.map(function(z){
    var whs = DB.warehouses.filter(function(w){return w.active && w.zone===z.id;});
    // حساب عدد المواد الحرجة في الزون
    var critCount = 0, warnCount = 0;
    DB.inventory.forEach(function(item){
      var total = whs.reduce(function(s,w){return s+(item[w.key]||0);},0);
      var cat = DB.categories.find(function(cc){return cc.name===item.cat;});
      var crit = cat?cat.criticalLimit:item.min;
      var warn = cat?cat.warningLimit:(item.min*2);
      if(total<=crit) critCount++;
      else if(total<=warn) warnCount++;
    });
    var isActive = currentZone===z.id;
    var alertBadge = critCount>0 ?
      '<span style="background:var(--r1);color:#fff;border-radius:20px;padding:2px 8px;font-size:10px;font-weight:700">'+critCount+' حرج</span>' :
      warnCount>0 ?
      '<span style="background:var(--y1);color:#000;border-radius:20px;padding:2px 8px;font-size:10px;font-weight:700">'+warnCount+' تحذير</span>' :
      '<span style="background:var(--g1);color:#fff;border-radius:20px;padding:2px 8px;font-size:10px;font-weight:700">آمن</span>';
    
    return '<div onclick="selectZone(\''+z.id+'\')" style="flex:1;min-width:200px;max-width:280px;background:'+(isActive?z.bg:'var(--bg2)')+';border:2px solid '+(isActive?z.border:'var(--b1)')+';border-radius:14px;padding:18px;cursor:pointer;transition:all .2s;position:relative">'+
      '<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">'+
        '<div style="width:42px;height:42px;border-radius:10px;background:'+z.bg+';border:1px solid '+z.border+';display:flex;align-items:center;justify-content:center">'+
          '<i class="fa '+z.icon+'" style="color:'+z.color+';font-size:18px"></i>'+
        '</div>'+
        '<div>'+
          '<div style="font-size:13px;font-weight:800;color:var(--t1)">'+z.name+'</div>'+
          '<div style="font-size:11px;color:var(--t3)">'+whs.length+' مستودع · '+DB.inventory.length+' صنف</div>'+
        '</div>'+
      '</div>'+
      '<div style="display:flex;gap:6px;flex-wrap:wrap">'+
        whs.map(function(w){return '<span style="background:rgba(255,255,255,.06);border:1px solid var(--b1);border-radius:6px;padding:2px 8px;font-size:10.5px;color:var(--t2)">'+w.name+'</span>';}).join('')+
      '</div>'+
      '<div style="margin-top:10px">'+alertBadge+'</div>'+
      (isActive?'<div style="position:absolute;top:10px;left:10px;width:10px;height:10px;border-radius:50%;background:'+z.color+'"></div>':'')+
    '</div>';
  }).join('');
}

function selectZone(zid){
  currentZone = zid;
  document.getElementById('zones-content').style.display='block';
  document.getElementById('btn-zones-export').style.display='flex';
  document.getElementById('zones-search').value='';
  document.getElementById('zones-filter-level').value='';
  // تعبئة فلتر المستودعات حسب الزون المختار
  var whs = DB.warehouses.filter(function(w){return w.active && w.zone===zid;});
  var whSel = document.getElementById('zones-filter-wh');
  if(whSel){
    whSel.innerHTML = '<option value="">كل المستودعات ('+whs.length+')</option>'+
      whs.map(function(w){return '<option value="'+w.key+'">'+w.name+'</option>';}).join('');
  }
  renderZones();
  zonesRender();
  document.getElementById('zones-content').scrollIntoView({behavior:'smooth'});
}

function zonesGetData(){
  if(!currentZone) return {rows:[],whs:[]};
  var zone = DB.zones.find(function(z){return z.id===currentZone;});
  if(!zone) return {rows:[],whs:[]};
  var allWhs = DB.warehouses.filter(function(w){return w.active && w.zone===currentZone;});
  var whFilter = (document.getElementById('zones-filter-wh')?.value||'').trim();
  // المستودعات المعروضة في الجدول: كل أو واحد فقط
  var whs = whFilter ? allWhs.filter(function(w){return w.key===whFilter;}) : allWhs;
  var q = (document.getElementById('zones-search')?.value||'').toLowerCase().trim();
  var lvFilter = (document.getElementById('zones-filter-level')?.value||'').trim();

  var rows = DB.inventory.map(function(item){
    // الكميات دائماً من كل مستودعات الزون (للإجمالي الحقيقي)
    var allQtys = allWhs.map(function(w){return {wh:w,qty:(item[w.key]||0)};});
    var totalAll = allQtys.reduce(function(s,x){return s+x.qty;},0);
    // الكميات المعروضة في الجدول (حسب فلتر المستودع)
    var whQtys = whs.map(function(w){
      var qty=item[w.key]||0;
      var reserved=getReservedStock(item.code,w.name);
      var avail=Math.max(0,qty-reserved);
      return {wh:w,qty:qty,reserved:reserved,avail:avail};
    });
    var total = whQtys.reduce(function(s,x){return s+x.qty;},0);
    var totalReserved = whQtys.reduce(function(s,x){return s+x.reserved;},0);
    var totalAvail = Math.max(0,total-totalReserved);
    var cat = DB.categories.find(function(cc){return cc.name===item.cat;});
    var crit = cat?cat.criticalLimit:(item.min||0);
    var warn = cat?cat.warningLimit:((item.min||0)*2);
    // المستوى يُحسب على إجمالي الزون كله دائماً
    var level = totalAll<=crit?'حرج':totalAll<=warn?'تحذير':'آمن';
    return {item:item,whQtys:whQtys,total:total,totalAll:totalAll,totalReserved:totalReserved,totalAvail:totalAvail,level:level,crit:crit,warn:warn};
  });

  if(q) rows = rows.filter(function(r){
    return r.item.code.toLowerCase().includes(q) || r.item.name.toLowerCase().includes(q);
  });
  if(lvFilter) rows = rows.filter(function(r){return r.level===lvFilter;});

  rows.sort(function(a,b){
    var o={حرج:0,تحذير:1,آمن:2};
    return (o[a.level]||2)-(o[b.level]||2)||a.totalAll-b.totalAll;
  });
  return {rows:rows,whs:whs,allWhs:allWhs};
}

function zonesRender(){
  var zone=DB.zones.find(function(z){return z.id===currentZone;});
  if(!zone) return;
  var data=zonesGetData();
  var whs=data.whs;
  var rows=data.rows;

  // عنوان الجدول
  var titleEl=document.getElementById('zones-table-title');
  if(titleEl) titleEl.innerHTML='<i class="fa fa-boxes-stacked" style="color:var(--g1)"></i>مواد '+zone.name;
  var subEl=document.getElementById('zones-sub');
  if(subEl) subEl.textContent=zone.name+' — '+rows.length+' صنف';

  // إحصائيات المستويات
  var counts={حرج:0,تحذير:0,آمن:0};
  rows.forEach(function(r){counts[r.level]=(counts[r.level]||0)+1;});
  var statsEl=document.getElementById('zones-stats');
  if(statsEl){
    statsEl.innerHTML=[
      {l:'حرج',c:'var(--r1)',b:'rgba(239,68,68,.08)',n:counts.حرج,i:'fa-circle-exclamation'},
      {l:'تحذير',c:'var(--y1)',b:'rgba(245,158,11,.08)',n:counts.تحذير,i:'fa-triangle-exclamation'},
      {l:'آمن',c:'var(--g1)',b:'rgba(16,185,129,.08)',n:counts.آمن,i:'fa-circle-check'}
    ].map(function(s){
      var active=(document.getElementById('zones-filter-level')?.value||'')===s.l;
      return '<div onclick="var el=document.getElementById(\'zones-filter-level\');if(el){el.value=el.value===\''+s.l+'\'?\'\':\''+s.l+'\';zonesRender();}" style="cursor:pointer;background:'+s.b+';border:1px solid '+(active?s.c:'transparent')+';border-radius:10px;padding:8px 16px;display:flex;align-items:center;gap:8px;flex:1;min-width:100px">'+
        '<i class="fa '+s.i+'" style="color:'+s.c+'"></i>'+
        '<div><div style="font-size:18px;font-weight:900;color:'+s.c+'">'+s.n+'</div><div style="font-size:10px;color:var(--t3)">'+s.l+'</div></div>'+
      '</div>';
    }).join('');
  }

  // تنبيهات المواد الحرجة
  var alertsEl=document.getElementById('zones-alerts');
  if(alertsEl){
    var critItems=rows.filter(function(r){return r.level==='حرج';});
    var warnItems=rows.filter(function(r){return r.level==='تحذير';});
    var alertsHtml='';
    if(critItems.length){
      alertsHtml+='<div style="background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.25);border-radius:10px;padding:12px;margin-bottom:8px">'+
        '<div style="font-size:12px;font-weight:700;color:var(--r1);margin-bottom:6px"><i class="fa fa-circle-exclamation"></i> مواد حرجة ('+critItems.length+')</div>'+
        '<div style="display:flex;flex-wrap:wrap;gap:6px">'+
        critItems.slice(0,8).map(function(r){return '<span style="background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.3);border-radius:6px;padding:3px 10px;font-size:11px;cursor:pointer" onclick="invDetail(\''+r.item.code+'\')" ><strong>'+r.item.code+'</strong> '+r.item.name+' <span style="color:var(--r1)">×'+r.total+'</span></span>';}).join('')+
        (critItems.length>8?'<span style="font-size:11px;color:var(--t3);align-self:center">و '+(critItems.length-8)+' أخرى...</span>':'')+
        '</div></div>';
    }
    if(warnItems.length){
      alertsHtml+='<div style="background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.25);border-radius:10px;padding:12px">'+
        '<div style="font-size:12px;font-weight:700;color:var(--y1);margin-bottom:6px"><i class="fa fa-triangle-exclamation"></i> مواد في مستوى تحذير ('+warnItems.length+')</div>'+
        '<div style="display:flex;flex-wrap:wrap;gap:6px">'+
        warnItems.slice(0,8).map(function(r){return '<span style="background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.3);border-radius:6px;padding:3px 10px;font-size:11px;cursor:pointer" onclick="invDetail(\''+r.item.code+'\')" ><strong>'+r.item.code+'</strong> '+r.item.name+' <span style="color:var(--y1)">×'+r.total+'</span></span>';}).join('')+
        (warnItems.length>8?'<span style="font-size:11px;color:var(--t3);align-self:center">و '+(warnItems.length-8)+' أخرى...</span>':'')+
        '</div></div>';
    }
    alertsEl.innerHTML=alertsHtml;
  }

  // رأس الجدول
  var thead=document.querySelector('#pg-zones thead tr');
  if(thead){
    thead.innerHTML='<th>الكود</th><th>اسم المادة</th>'+
      whs.map(function(w){return '<th style="color:'+w.color+';font-size:11px;text-align:center"><i class="fa fa-warehouse" style="margin-left:3px"></i>'+w.name+'<div style="font-size:9px;color:var(--t3);font-weight:400">كلي/🔒/✓</div></th>';}).join('')+
      '<th style="text-align:center">الكلي</th><th style="text-align:center">🔒 محجوز</th><th style="text-align:center">✓ متاح</th><th>المستوى</th>';
  }

  // جسم الجدول
  var tbody=document.getElementById('zones-tbody');
  if(!tbody) return;
  if(!rows.length){
    tbody.innerHTML='<tr><td colspan="'+(4+whs.length)+'" style="text-align:center;padding:24px;color:var(--t3)"><i class="fa fa-search" style="font-size:20px;display:block;margin-bottom:8px"></i>لا توجد نتائج</td></tr>';
    return;
  }

  var levelColor={حرج:'var(--r1)',تحذير:'var(--y1)',آمن:'var(--g1)'};
  var levelBg={حرج:'rgba(239,68,68,.1)',تحذير:'rgba(245,158,11,.1)',آمن:'rgba(16,185,129,.1)'};
  var levelIcon={حرج:'fa-circle-exclamation',تحذير:'fa-triangle-exclamation',آمن:'fa-circle-check'};

  tbody.innerHTML=rows.map(function(r){
    var levColor=levelColor[r.level]||'var(--t1)';
    var availColor=r.totalAvail<=0?'var(--r1)':r.totalAvail<=3?'var(--y1)':'var(--g1)';
    var pct=r.total>0?Math.round((r.totalReserved/r.total)*100):0;

    // تفاصيل كل مستودع
    var whCells=r.whQtys.map(function(x){
      var qc=x.qty<=0?'var(--r1)':x.qty<=3?'var(--y1)':'var(--t1)';
      var ac=x.avail<=0&&x.qty>0?'var(--r1)':x.avail<=2?'var(--y1)':'var(--g1)';
      var cell='<td style="text-align:center;padding:6px 4px">';
      cell+='<div class="mono" style="font-size:14px;font-weight:700;color:'+qc+'">'+x.qty+'</div>';
      if(x.reserved>0){
        cell+='<div style="font-size:9px;color:var(--r1)">🔒'+x.reserved+'</div>';
        cell+='<div style="font-size:10px;font-weight:700;color:'+ac+'">✓'+x.avail+'</div>';
      }
      cell+='</td>';
      return cell;
    }).join('');

    return '<tr data-code="'+r.item.code+'" class="zones-item-row" style="cursor:pointer">'+
      '<td class="mono" style="color:var(--a1);font-weight:700;font-size:11px">'+r.item.code+'</td>'+
      '<td style="min-width:120px">'+
        '<div style="font-weight:600;color:var(--t1);font-size:12px">'+r.item.name+'</div>'+
        '<span style="font-size:10px;background:rgba(255,255,255,.06);border-radius:4px;padding:1px 6px;color:var(--t3)">'+r.item.cat+'</span>'+
      '</td>'+
      whCells+
      '<td style="text-align:center"><div class="mono" style="font-size:16px;font-weight:900;color:var(--a1)">'+r.total+'</div></td>'+
      '<td style="text-align:center">'+(r.totalReserved>0?'<div class="mono" style="font-size:15px;font-weight:700;color:var(--r1)">🔒'+r.totalReserved+'</div>':'<div style="color:var(--t3);font-size:11px">—</div>')+'</td>'+
      '<td style="text-align:center"><div class="mono" style="font-size:16px;font-weight:900;color:'+availColor+'">'+r.totalAvail+'</div></td>'+
      '<td><span style="display:inline-flex;align-items:center;gap:4px;background:'+levelBg[r.level]+';border:1px solid '+levColor+'33;border-radius:8px;padding:4px 10px;font-size:11px;font-weight:700;color:'+levColor+'">'+
        '<i class="fa '+(levelIcon[r.level]||'fa-circle')+'"></i>'+r.level+
      '</span></td>'+
    '</tr>';
  }).join('');
  // Event delegation for row clicks
  tbody.querySelectorAll('tr.zones-item-row').forEach(function(tr){tr.addEventListener('click',function(){invDetail(this.dataset.code);});});
}

// ══ صفحة المستودعات ══
function renderWarehouses(){
  var q=(document.getElementById('whs-q')?.value||'').toLowerCase();
  var el=document.getElementById('whs-cards');if(!el)return;
  var whs=DB.warehouses.filter(function(w){return !q||w.name.toLowerCase().includes(q)||w.location.toLowerCase().includes(q);});
  el.innerHTML=whs.map(function(w){
    return '<div class="wh-card" style="background:var(--bg2);border:1px solid var(--b1);border-radius:12px;padding:14px;margin-bottom:10px">'+
      '<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">'+
        '<div style="width:36px;height:36px;border-radius:8px;background:'+w.color+'22;display:flex;align-items:center;justify-content:center">'+
          '<i class="fa fa-warehouse" style="color:'+w.color+'"></i>'+
        '</div>'+
        '<div>'+
          '<div style="font-weight:700;color:var(--t1)">'+w.name+'</div>'+
          '<div style="font-size:11px;color:var(--t3)">'+w.location+'</div>'+
        '</div>'+
        '<div style="margin-right:auto;display:flex;gap:6px">'+
          '<button class="btn btn-warn btn-xs" onclick="editWarehouse(this.dataset.id)" data-id="'+w.id+'"><i class="fa fa-pen"></i>تعديل</button>'+
          '<button class="btn btn-'+(w.active?'danger':'green')+' btn-xs" onclick="toggleWarehouse(this.dataset.id)" data-id="'+w.id+'">'+
            '<i class="fa fa-'+(w.active?'eye-slash':'eye')+'"></i>'+(w.active?'تعطيل':'تفعيل')+
          '</button>'+
        '</div>'+
      '</div>'+
      '<div style="display:flex;gap:8px;font-size:11px;color:var(--t3)">'+
        '<span><i class="fa fa-user"></i> '+w.manager+'</span>'+
        '<span><i class="fa fa-phone"></i> '+w.phone+'</span>'+
        '<span><i class="fa fa-map-marker-alt"></i> '+
          (DB.zones.find(function(z){return z.id===w.zone;})||{name:'-'}).name+
        '</span>'+
      '</div>'+
    '</div>';
  }).join('')+(whs.length===0?'<div style="text-align:center;padding:20px;color:var(--t3)">لا توجد نتائج</div>':'');
}

// ══ صفحة المقاولين ══
function renderContractors(){
  var q=(document.getElementById('contr-q')?.value||'').toLowerCase();
  var el=document.getElementById('contr-list');if(!el)return;
  var contractors=DB.contractors.filter(function(ct){return !q||ct.name.toLowerCase().includes(q);});
  el.innerHTML=contractors.map(function(ct){
    return '<div style="display:flex;align-items:center;gap:10px;padding:10px;background:var(--bg2);border:1px solid var(--b1);border-radius:10px;margin-bottom:8px">'+
      '<div style="width:36px;height:36px;border-radius:50%;background:var(--bg3);display:flex;align-items:center;justify-content:center;font-weight:700;color:var(--a1)">'+ct.name.charAt(0)+'</div>'+
      '<div style="flex:1">'+
        '<div style="font-weight:600;color:var(--t1)">'+ct.name+'</div>'+
        (ct.phone?'<div style="font-size:11px;color:var(--t3)"><i class="fa fa-phone"></i> '+ct.phone+'</div>':'')+
      '</div>'+
      '<button class="btn btn-warn btn-xs" onclick="editContractor(this.dataset.id)" data-id="'+ct.id+'"><i class="fa fa-pen"></i></button>'+
      '<button class="btn btn-danger btn-xs" onclick="deleteContractor(this.dataset.id)" data-id="'+ct.id+'"><i class="fa fa-trash"></i></button>'+
    '</div>';
  }).join('')+(contractors.length===0?'<div style="text-align:center;padding:20px;color:var(--t3)">لا توجد مقاولين</div>':'');
}

// ══ صفحة الفئات والحدود ══
function renderCategories(){
  var el=document.getElementById('cat-limits-list');if(!el)return;
  el.innerHTML=DB.categories.map(function(cat){
    var itemCount=DB.inventory.filter(function(i){return i.cat===cat.name;}).length;
    return '<div style="background:var(--bg2);border:1px solid var(--b1);border-radius:10px;padding:12px;margin-bottom:10px">'+
      '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">'+
        '<div style="width:32px;height:32px;border-radius:8px;background:rgba(0,212,255,.1);display:flex;align-items:center;justify-content:center">'+
          '<i class="fa fa-tag" style="color:var(--a1)"></i>'+
        '</div>'+
        '<div style="flex:1">'+
          '<div style="font-weight:700;color:var(--t1)">'+cat.name+'</div>'+
          '<div style="font-size:11px;color:var(--t3)">'+itemCount+' مادة</div>'+
        '</div>'+
        '<button class="btn btn-danger btn-xs" onclick="deleteCategoryItem(this.dataset.n)" data-n="'+cat.name+'"><i class="fa fa-trash"></i></button>'+
      '</div>'+
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">'+
        '<div>'+
          '<label style="font-size:10px;color:var(--t3)">🔴 الحد الحرج</label>'+
          '<input type="number" min="0" id="cat-crit-'+cat.name.replace(/\s/g,'_')+'" value="'+cat.criticalLimit+'" style="width:100%;padding:6px;border:1px solid rgba(239,68,68,.3);border-radius:6px;background:var(--bg1);color:var(--r1);font-weight:700;text-align:center;margin-top:3px">'+
        '</div>'+
        '<div>'+
          '<label style="font-size:10px;color:var(--t3)">🟡 حد التحذير</label>'+
          '<input type="number" min="0" id="cat-warn-'+cat.name.replace(/\s/g,'_')+'" value="'+cat.warningLimit+'" style="width:100%;padding:6px;border:1px solid rgba(245,158,11,.3);border-radius:6px;background:var(--bg1);color:var(--y1);font-weight:700;text-align:center;margin-top:3px">'+
        '</div>'+
      '</div>'+
    '</div>';
  }).join('')+(DB.categories.length===0?
    '<div style="text-align:center;padding:20px;color:var(--t3)"><i class="fa fa-inbox" style="font-size:24px;display:block;margin-bottom:8px"></i>لا توجد فئات</div>':'');
  renderCatMeter();
}

function saveCategoryLimits(){
  DB.categories.forEach(function(cat){
    var key=cat.name.replace(/\s/g,'_');
    var critEl=document.getElementById('cat-crit-'+key);
    var warnEl=document.getElementById('cat-warn-'+key);
    if(critEl) cat.criticalLimit=Math.max(0,parseInt(critEl.value)||0);
    if(warnEl) cat.warningLimit=Math.max(0,parseInt(warnEl.value)||0);
  });
  renderCatMeter();
  updateZonesBadge();
  toast('ok','✓ تم الحفظ','تم تحديث حدود الإشعار لجميع الفئات','fa-save');
}

function renderCatMeter(){
  var el=document.getElementById('cat-meter');if(!el)return;
  el.innerHTML=DB.categories.map(function(cat){
    var items=DB.inventory.filter(function(i){return i.cat===cat.name;});
    var totalQty=items.reduce(function(s,i){
      return s+DB.warehouses.filter(function(w){return w.active;}).reduce(function(ws,w){return ws+(i[w.key]||0);},0);
    },0);
    var avgQty=items.length?Math.round(totalQty/items.length):0;
    var level=avgQty<=cat.criticalLimit?'حرج':avgQty<=cat.warningLimit?'تحذير':'آمن';
    var color=level==='حرج'?'var(--r1)':level==='تحذير'?'var(--y1)':'var(--g1)';
    var pct=cat.warningLimit>0?Math.min(100,Math.round((avgQty/cat.warningLimit)*100)):0;
    return '<div style="margin-bottom:14px">'+
      '<div style="display:flex;justify-content:space-between;margin-bottom:4px">'+
        '<span style="font-size:12px;font-weight:600;color:var(--t1)">'+cat.name+'</span>'+
        '<span style="font-size:11px;color:'+color+';font-weight:700">'+level+'</span>'+
      '</div>'+
      '<div style="background:var(--bg2);border-radius:8px;height:10px;overflow:hidden">'+
        '<div style="height:100%;width:'+pct+'%;background:'+color+';border-radius:8px;transition:.3s"></div>'+
      '</div>'+
      '<div style="display:flex;justify-content:space-between;font-size:10px;color:var(--t3);margin-top:3px">'+
        '<span>متوسط: '+avgQty+'</span>'+
        '<span>'+items.length+' مادة</span>'+
      '</div>'+
    '</div>';
  }).join('')+(DB.categories.length===0?'<div style="color:var(--t3);text-align:center;padding:20px">لا توجد فئات</div>':'');
}

function deleteCategoryItem(name){
  if(!name) return;
  var inUse=DB.inventory.some(function(i){return i.cat===name;});
  if(inUse){toast('warn','لا يمكن الحذف','هذه الفئة مستخدمة في '+DB.inventory.filter(function(i){return i.cat===name;}).length+' مادة','fa-ban');return;}
  showConfirm('<i class="fa fa-trash" style="color:var(--r1)"></i> حذف فئة',
    'حذف فئة <strong>'+name+'</strong>؟',
    'حذف','btn-danger',function(){
      DB.categories=DB.categories.filter(function(c){return c.name!==name;});
      renderCategories();
      toast('ok','✓ تم الحذف','تم حذف الفئة '+name,'fa-trash');
    });
}

// ══ صفحة الارجاع المباشر ══
function renderDrPage(){
  var wh=document.getElementById('dr-wh')?.value||DB.warehouses.filter(function(w){return w.active;})[0]?.name||'';
  renderDrHist();
}

function renderDrHist(){
  var el=document.getElementById('dr-hist-list');if(!el)return;
  var emp=currentUser?.name;
  var returns=DB.invoices.filter(function(i){return i.type==='ارجاع'&&(!emp||i.emp===emp);}).slice(0,20);
  el.innerHTML=returns.map(function(r){
    return '<div style="background:var(--bg2);border:1px solid var(--b1);border-radius:8px;padding:10px;margin-bottom:8px;display:flex;align-items:center;gap:10px">'+
      '<span class="mono" style="color:var(--a1);font-weight:700">'+r.no+'</span>'+
      '<span>'+r.wh+'</span>'+
      '<span style="color:var(--t3);font-size:11px">'+r.cont+'</span>'+
      '<span style="margin-right:auto">'+tag(r.st)+'</span>'+
      '<button class="btn btn-sec btn-xs" onclick="showInvDetail(this.dataset.no)" data-no="'+r.no+'"><i class="fa fa-eye"></i></button>'+
      '<button class="btn btn-primary btn-xs" onclick="printInvoice(this.dataset.no)" data-no="'+r.no+'"><i class="fa fa-print"></i></button>'+
    '</div>';
  }).join('')+(returns.length===0?'<div style="text-align:center;padding:20px;color:var(--t3)"><i class="fa fa-inbox" style="font-size:24px;display:block;margin-bottom:8px"></i>لا توجد فواتير ارجاع</div>':'');
}

</script>
</body>
</html>
