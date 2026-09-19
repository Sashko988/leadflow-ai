"""Small multi-tenant web MVP for AI Lead Automation.

Run with: python web.py setup
         python web.py run
"""

from __future__ import annotations

import argparse
import secrets
import smtplib
from email.message import EmailMessage
from functools import wraps

from flask import Flask, flash, redirect, render_template_string, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

try:
    from authlib.integrations.flask_client import OAuth
except ImportError:
    OAuth = None

import app as core
import config

app = Flask(__name__)
app.secret_key = config.WEB_SECRET_KEY
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

oauth = OAuth(app) if OAuth else None
if oauth and config.GOOGLE_CLIENT_ID and config.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=config.GOOGLE_CLIENT_ID,
        client_secret=config.GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
if oauth and config.MICROSOFT_CLIENT_ID and config.MICROSOFT_CLIENT_SECRET:
    oauth.register(
        name="microsoft",
        client_id=config.MICROSOFT_CLIENT_ID,
        client_secret=config.MICROSOFT_CLIENT_SECRET,
        server_metadata_url="https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile User.Read"},
    )

BASE_TEMPLATE = """
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title or 'LeadFlow AI' }}</title><style>
:root{--ink:#101114;--muted:#787b83;--line:#dedfdc;--paper:#f5f5f1;--acid:#d7ff55;--violet:#8c7cff}*{box-sizing:border-box}html{scroll-behavior:smooth}body{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--paper);color:var(--ink);margin:0}nav{background:var(--ink);color:#fff;padding:21px 5.5%;display:flex;justify-content:space-between;align-items:center;position:relative;z-index:10}nav a{color:#d7d7d2;text-decoration:none;margin-left:24px;font-size:14px}.brand{font-weight:900;letter-spacing:-.7px;color:#fff;font-size:18px}.brand span{color:var(--acid)}main{max-width:1240px;margin:0 auto;padding:0 28px}.card{background:white;border:1px solid #e5e7eb;border-radius:16px;padding:22px;margin-bottom:20px;box-shadow:0 8px 24px #1118270b}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px}.metric{font-size:30px;font-weight:700}.muted{color:#667085}.badge{border-radius:99px;padding:5px 10px;font-size:12px;font-weight:700}.HOT{background:#fee2e2;color:#991b1b}.WARM{background:#fef3c7;color:#92400e}.COLD{background:#dbeafe;color:#1e40af}input,textarea{width:100%;box-sizing:border-box;padding:12px;border:1px solid #d0d5dd;border-radius:8px;margin:6px 0 14px}button,.button{background:#101114;color:white;border:0;border-radius:999px;padding:13px 20px;text-decoration:none;cursor:pointer;font-weight:750;display:inline-block}.button.secondary{background:#fff;color:#101114;border:1px solid #34363b}.flash{background:#ecfdf3;padding:10px;border-radius:8px;margin-bottom:16px}.error{background:#fef2f2}.table{width:100%;border-collapse:collapse}.table th,.table td{text-align:left;border-bottom:1px solid #eaecf0;padding:12px 8px}
.hero{position:relative;overflow:hidden;background:var(--ink);color:#fff;padding:86px 7%;min-height:640px;display:grid;grid-template-columns:1.05fr .95fr;gap:38px;align-items:center}.hero:before{content:"";position:absolute;width:610px;height:610px;border-radius:50%;right:-120px;top:-150px;background:radial-gradient(circle,#8c7cff 0,#5549bc 25%,#252334 60%,transparent 70%);opacity:.9}.hero:after{content:"";position:absolute;inset:0;background:linear-gradient(120deg,transparent 0 48%,#ffffff08 48.2% 48.5%,transparent 48.7%);pointer-events:none}.hero-copy,.hero-art{position:relative;z-index:1}.eyebrow{color:var(--acid);font-weight:850;letter-spacing:1.7px;text-transform:uppercase;font-size:11px}.hero h1{max-width:730px;font-size:clamp(48px,7vw,94px);line-height:.94;letter-spacing:-6px;margin:18px 0 24px}.hero h1 em{font-style:normal;color:var(--acid)}.hero p{max-width:570px;color:#c9c9c5;font-size:18px;line-height:1.6}.hero-actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:32px}.hero .button{background:var(--acid);color:#101114}.hero .button.secondary{background:transparent;color:#fff;border:1px solid #ffffff55}.hero-art{min-height:410px;display:grid;place-items:center}.orb{width:min(390px,72vw);height:min(390px,72vw);border-radius:50%;border:1px solid #ffffff44;position:relative;display:grid;place-items:center;box-shadow:0 0 90px #8277ff55}.orb:before,.orb:after{content:"";position:absolute;border-radius:50%;border:1px solid #d7ff5570;inset:12%}.orb:after{inset:25%;border-color:#ffffff70}.orb-core{width:110px;height:110px;border-radius:50%;background:radial-gradient(circle at 30% 25%,#fff,#d7ff55 20%,#8c7cff 62%,#2d286a);box-shadow:0 0 55px #d7ff55aa}.orbit-dot{position:absolute;width:13px;height:13px;border-radius:50%;background:var(--acid);box-shadow:0 0 20px var(--acid);top:4%;left:50%}.orbit-dot.two{top:68%;left:5%;background:#fff;box-shadow:0 0 20px #fff}.orbit-label{position:absolute;background:#ffffff12;border:1px solid #ffffff33;border-radius:999px;padding:8px 12px;color:#fff;font-size:11px;backdrop-filter:blur(8px)}.label-one{right:-8px;top:18%}.label-two{left:-22px;bottom:23%}.ticker{background:var(--acid);color:var(--ink);padding:13px 0;overflow:hidden;white-space:nowrap;font-size:12px;font-weight:850;letter-spacing:1.5px;text-transform:uppercase}.ticker span{margin-right:45px}.section{padding:100px 0 20px}.section h2{font-size:clamp(36px,5vw,66px);line-height:.98;letter-spacing:-4px;margin:10px 0 16px;max-width:760px}.section-intro{max-width:660px;color:var(--muted);font-size:17px;line-height:1.6}.service-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:42px}.service{min-height:245px;padding:27px;background:#fff;border:1px solid var(--line);position:relative;overflow:hidden}.service:nth-child(2){background:#e9e5ff}.service:nth-child(3){background:#dff1c7}.service:nth-child(4){background:#dce8ff}.service:nth-child(5){background:#fff1ca}.service:nth-child(6){background:#f0dff4}.service-no{font-size:12px;color:#555;font-weight:800}.service h3{font-size:22px;letter-spacing:-1px;margin:48px 0 10px}.service p{color:#5e6065;line-height:1.5;margin:0}.service-arrow{position:absolute;right:22px;top:22px;font-size:24px}.proof-row{display:grid;grid-template-columns:repeat(3,1fr);gap:25px;border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:28px 0;margin-top:45px}.proof strong{display:block;font-size:31px;letter-spacing:-2px}.proof span{display:block;color:var(--muted);font-size:13px;margin-top:5px}.steps{counter-reset:step;display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:42px}.step{border-top:1px solid #bfc0bc;padding-top:17px;position:relative}.step:before{counter-increment:step;content:"0" counter(step);font-size:13px;color:#7166db;font-weight:850}.step h3{margin:35px 0 8px;font-size:21px}.step p{color:var(--muted);line-height:1.5}.cta{background:var(--ink);color:#fff;text-align:center;padding:76px 20px;border-radius:2px;margin:110px 0 30px;position:relative;overflow:hidden}.cta:before{content:"";position:absolute;width:360px;height:360px;border-radius:50%;background:#8c7cff55;filter:blur(35px);left:-90px;top:-180px}.cta>*{position:relative}.cta h2{margin:0 auto 14px;font-size:clamp(38px,5vw,66px);letter-spacing:-4px;line-height:1}.cta p{color:#c9c9c5;margin-bottom:28px}.landing-footer{text-align:center;color:#667085;padding:0 0 28px;font-size:13px}@media(max-width:800px){main{padding:0 16px}.hero{grid-template-columns:1fr;padding:64px 28px;min-height:auto}.hero h1{letter-spacing:-3px}.hero-art{min-height:310px}.service-grid,.steps{grid-template-columns:1fr 1fr}.proof-row{grid-template-columns:1fr 1fr;gap:20px}}@media(max-width:520px){nav{padding:18px 20px}nav>div a:first-child{display:none}nav a{margin-left:12px}.hero{padding:53px 22px}.hero h1{font-size:54px}.service-grid,.steps{grid-template-columns:1fr}.section{padding-top:70px}.section h2{letter-spacing:-2px}.proof-row{grid-template-columns:1fr}.hero-art{min-height:275px}}
</style></head><body><nav><a class="brand" href="{{url_for('landing')}}">Lead<span>Flow</span> AI</a><div><a href="{{url_for('landing')}}#services">Services</a><a href="{{url_for('landing')}}#process">Process</a>{% if session.get('user_id') %}<a href="{{url_for('dashboard')}}">Dashboard</a><a href="{{url_for('logout')}}">Log out</a>{% else %}<a href="{{url_for('login')}}">Sign in</a>{% endif %}</div></nav><main>{% with messages=get_flashed_messages(with_categories=true) %}{% for category,message in messages %}<div class="flash {{category}}">{{message}}</div>{% endfor %}{% endwith %}{{content|safe}}</main></body></html>
"""

BASE_TEMPLATE = BASE_TEMPLATE.replace("</style>", "body:has(.hero){background:#101114;color:#fff}body:has(.hero):before{content:'';position:fixed;inset:-4vh 0;z-index:0;background:url('/static/leadflow-bg.svg') center/cover no-repeat;transform:translate3d(0,var(--parallax-y,0px),0) scale(1.04);will-change:transform}body:has(.hero) nav,body:has(.hero) main{position:relative;z-index:1}body:has(.hero) nav{background:#101114dd;backdrop-filter:blur(14px);position:sticky;top:0}.hero{background:rgba(16,17,20,.78)}.section{position:relative}</style>")

LANDING_TEMPLATE = """
<section class="hero"><div class="hero-copy"><div class="eyebrow">AI systems for ambitious teams</div><h1>Make your business feel <em>superhuman.</em></h1><p>LeadFlow AI turns repetitive lead and customer workflows into intelligent systems that respond faster, stay organized, and help your team grow without adding more busywork.</p><div class="hero-actions"><a class="button" href="{{url_for('demo')}}">Book a free demo ↗</a><a class="button secondary" href="#services">Explore services</a></div></div><div class="hero-art" aria-label="Abstract AI automation visualization"><div class="orb"><div class="orb-core"></div><div class="orbit-dot"></div><div class="orbit-dot two"></div><div class="orbit-label label-one">AI AGENTS</div><div class="orbit-label label-two">YOUR WORKFLOW</div></div></div></section>
<div class="ticker"><span>Lead qualification</span><span>Inbox automation</span><span>Custom AI workflows</span><span>Faster response times</span><span>Lead qualification</span></div>
<section class="section" id="services"><div class="eyebrow">What we build</div><h2>Practical AI that moves work forward.</h2><p class="section-intro">We combine automation, AI reasoning, and clean interfaces to remove bottlenecks from the moments that matter most to your business.</p><div class="service-grid"><div class="service"><div class="service-no">01 / SALES</div><div class="service-arrow">↗</div><h3>AI Lead Qualification</h3><p>Score, prioritize, and route every inquiry so your team knows who to contact first.</p></div><div class="service"><div class="service-no">02 / COMMUNICATION</div><div class="service-arrow">↗</div><h3>Smart Inbox Workflows</h3><p>Turn incoming emails into structured records, tasks, and next steps automatically.</p></div><div class="service"><div class="service-no">03 / FOLLOW-UP</div><div class="service-arrow">↗</div><h3>Personalized Replies</h3><p>Generate thoughtful first-draft responses that sound like your business and stay under review.</p></div><div class="service"><div class="service-no">04 / OPERATIONS</div><div class="service-arrow">↗</div><h3>Workflow Automation</h3><p>Connect the repetitive steps between forms, inboxes, CRMs, calendars, and your team.</p></div><div class="service"><div class="service-no">05 / INSIGHT</div><div class="service-arrow">↗</div><h3>AI-Powered Dashboards</h3><p>See priorities, lead quality, response status, and recommended actions in one clear view.</p></div><div class="service"><div class="service-no">06 / CUSTOM</div><div class="service-arrow">↗</div><h3>Custom AI Assistants</h3><p>Design a focused assistant for the questions, decisions, and processes unique to your company.</p></div></div><div class="proof-row"><div class="proof"><strong>24/7</strong><span>Always-on workflow coverage</span></div><div class="proof"><strong>1 place</strong><span>For leads, context, and next actions</span></div><div class="proof"><strong>Built for you</strong><span>Workflows shaped around your process</span></div></div></section>
<section class="section" id="process"><div class="eyebrow">The approach</div><h2>From messy process to clear system.</h2><div class="steps"><div class="step"><h3>Understand</h3><p>We map where leads, messages, and manual decisions enter your business.</p></div><div class="step"><h3>Design</h3><p>We shape an automation workflow around your tools, tone, and goals.</p></div><div class="step"><h3>Improve</h3><p>We launch a focused MVP, measure it, and keep making the workflow smarter.</p></div></div></section>
<section class="cta"><div class="eyebrow">Start with one workflow</div><h2>Let’s make your next process intelligent.</h2><p>Tell us what is slowing your team down. We will show you where AI automation can create the most leverage.</p><a class="button" href="{{url_for('demo')}}">Book a free strategy call ↗</a></section><div class="landing-footer">LeadFlow AI · Intelligent automation for modern businesses</div>
"""

LANDING_TEMPLATE += """<script>let target=0,current=0;window.addEventListener('scroll',()=>{target=window.scrollY*.035},{passive:true});function drift(){current+=(target-current)*.08;document.body.style.setProperty('--parallax-y',(-current).toFixed(2)+'px');requestAnimationFrame(drift)}drift();</script>"""

BASE_TEMPLATE = BASE_TEMPLATE.replace("</style>", ".reference-shell{max-width:1240px;margin:0 auto;padding:0 28px}.reference-hero{min-height:calc(100vh - 70px);display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:80px 20px 70px}.reference-hero h1{font-size:clamp(58px,10vw,150px);line-height:.86;letter-spacing:-9px;max-width:1100px;margin:22px 0 28px}.reference-hero h1 em{font-style:normal;color:var(--acid)}.reference-hero p{color:#c8c8c4;max-width:620px;font-size:18px;line-height:1.55}.pill-row{display:flex;gap:9px;flex-wrap:wrap;justify-content:center;margin:28px auto 0;max-width:850px}.pill{border:1px solid #ffffff40;border-radius:999px;padding:10px 14px;color:#e9e9e5;font-size:12px;background:#ffffff0d}.reference-section{padding:130px 0 35px}.reference-section.dark{background:#101114;color:#fff;margin:0 -28px;padding-left:28px;padding-right:28px}.reference-kicker{font-size:11px;font-weight:850;letter-spacing:1.8px;color:var(--acid);text-transform:uppercase}.reference-section h2{font-size:clamp(42px,6vw,82px);letter-spacing:-6px;line-height:.93;max-width:850px;margin:16px 0 22px}.reference-section .lead{color:#888b91;max-width:650px;font-size:18px;line-height:1.55}.capability-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-top:54px}.capability{min-height:310px;border:1px solid #ffffff1c;border-radius:2px;padding:28px;position:relative;overflow:hidden;background:#18191d}.capability:nth-child(2){background:#222044}.capability:nth-child(3){background:#203024}.capability:nth-child(4){background:#222a42}.capability:nth-child(5){background:#39301b}.capability:nth-child(6){background:#34243b}.capability h3{font-size:30px;letter-spacing:-2px;margin:82px 0 12px}.capability p{color:#c4c5c4;max-width:380px;line-height:1.5;margin:0}.capability-no{color:var(--acid);font-size:12px;font-weight:850}.capability-mark{position:absolute;right:28px;top:22px;font-size:36px;color:#ffffffaa}.spotlight{display:grid;grid-template-columns:1fr 1fr;gap:46px;align-items:center;margin-top:55px;padding:40px 0;border-top:1px solid #ffffff24}.spotlight-visual{min-height:390px;border:1px solid #ffffff22;background:radial-gradient(circle at 50% 40%,#d7ff5540,transparent 26%),linear-gradient(135deg,#24213d,#121317);display:grid;place-items:center}.spotlight-visual .mini-orb{width:210px;height:210px;border:1px solid #d7ff5570;border-radius:50%;box-shadow:0 0 80px #8c7cff66;display:grid;place-items:center}.mini-orb:after{content:'AI';font-size:45px;font-weight:900;color:var(--acid);letter-spacing:-4px}.spotlight h3{font-size:32px;letter-spacing:-2px;margin:20px 0 12px}.spotlight p{color:#bfc0c0;line-height:1.6}.prompt{border-left:2px solid var(--acid);padding:15px 18px;color:#dadad5;font-style:italic;margin-top:28px}.steps-reference{display:grid;grid-template-columns:repeat(4,1fr);gap:22px;margin-top:58px}.step-reference{border-top:1px solid #ffffff33;padding-top:16px}.step-reference b{color:var(--acid);font-size:13px}.step-reference h3{font-size:20px;margin:34px 0 10px}.step-reference p{color:#989a9e;line-height:1.5;font-size:14px}.faq-list{max-width:900px;margin:48px auto 0}.faq-list details{border-top:1px solid #ffffff24;padding:22px 0}.faq-list details:last-child{border-bottom:1px solid #ffffff24}.faq-list summary{cursor:pointer;list-style:none;font-size:19px;display:flex;gap:20px}.faq-list summary::-webkit-details-marker{display:none}.faq-list summary:before{content:'+';color:var(--acid);font-size:24px;line-height:18px}.faq-list details[open] summary:before{content:'−'}.faq-list p{color:#999da3;line-height:1.55;margin:16px 0 0 38px;max-width:700px}.reference-final{text-align:center;padding:150px 20px}.reference-final h2{margin-left:auto;margin-right:auto}.reference-footer{border-top:1px solid #ffffff24;padding:28px 0 34px;color:#858890;display:flex;justify-content:space-between;font-size:13px}@media(max-width:800px){.reference-hero h1{letter-spacing:-5px}.capability-grid,.spotlight{grid-template-columns:1fr}.steps-reference{grid-template-columns:1fr 1fr}.reference-section h2{letter-spacing:-3px}}@media(max-width:520px){.reference-hero{min-height:calc(100vh - 64px);padding-top:45px}.reference-hero h1{font-size:62px;letter-spacing:-4px}.reference-section{padding-top:90px}.reference-section.dark{margin:0 -16px;padding-left:16px;padding-right:16px}.capability h3{font-size:26px}.steps-reference{grid-template-columns:1fr}.reference-footer{display:block}.reference-footer span{display:block;margin-top:9px}}</style>")
BASE_TEMPLATE = BASE_TEMPLATE.replace("</style>", "html{background:#101114;scrollbar-color:#8c7cff #101114}body:has(.hero) .reference-shell,body:has(.hero) .reference-section,body:has(.hero) .reference-footer{background:transparent}body:has(.hero) .reference-section.dark{background:rgba(9,10,14,.68);backdrop-filter:blur(2px)}body:has(.hero) .reference-footer{border-color:#ffffff22}body:has(.hero) .reference-hero{background:linear-gradient(180deg,#10111420,transparent)}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}body:has(.hero):before{transform:scale(1.04)!important}}</style>")
BASE_TEMPLATE = BASE_TEMPLATE.replace("</style>", ".reference-section.dark{background:rgba(8,9,12,.78)}.capability{background:linear-gradient(145deg,#191a1f,#111216)!important;border-color:#ffffff1c;box-shadow:inset 0 1px #ffffff0a}.capability:nth-child(2){background:linear-gradient(145deg,#252044,#14151c)!important}.capability:nth-child(3){background:linear-gradient(145deg,#20342c,#131719)!important}.capability:nth-child(4){background:linear-gradient(145deg,#202a43,#13151c)!important}.capability:nth-child(5){background:linear-gradient(145deg,#3b311d,#171618)!important}.capability:nth-child(6){background:linear-gradient(145deg,#38263d,#17151b)!important}.capability:hover{border-color:#d7ff5599;transform:translateY(-3px);transition:transform .35s ease,border-color .35s ease}.reference-hero .button{box-shadow:0 0 35px #d7ff5533}.reference-section{background:transparent}</style>")
BASE_TEMPLATE = BASE_TEMPLATE.replace("</style>", "body:has(.reference-hero){background:#101114!important;color:#fff;overflow-x:hidden}body:has(.reference-hero):before{content:'';position:fixed;inset:-4vh 0;z-index:0;background:url('/static/leadflow-bg.svg') center/cover no-repeat;transform:translate3d(0,var(--parallax-y,0px),0) scale(1.04);will-change:transform}body:has(.reference-hero) nav,body:has(.reference-hero) main{position:relative;z-index:1}body:has(.reference-hero) nav{background:#101114dd;backdrop-filter:blur(14px);position:sticky;top:0}</style>")

LANDING_TEMPLATE_V2 = """
<div class="reference-shell">
<section class="reference-hero"><div class="reference-kicker">AI automation for growing businesses</div><h1>Your business,<br><em>in flow.</em></h1><p>LeadFlow AI turns incoming leads, customer questions, and repetitive operations into intelligent workflows your team can trust.</p><div class="hero-actions"><a class="button" href="{{url_for('demo')}}">Book a free demo ↗</a></div><div class="pill-row"><span class="pill">Lead qualification</span><span class="pill">Inbox automation</span><span class="pill">Personalized follow-up</span><span class="pill">AI dashboards</span><span class="pill">Custom assistants</span></div></section>
<section class="reference-section dark" id="services"><div class="reference-kicker">What LeadFlow actually does</div><h2>AI systems that create momentum.</h2><p class="lead">Not another chatbot. Practical automation that captures context, makes decisions, and helps your team move from inquiry to action.</p><div class="capability-grid"><div class="capability"><div class="capability-no">01 / SALES</div><div class="capability-mark">↗</div><h3>Lead qualification</h3><p>Every inquiry gets a priority, a quality score, and a recommended next action.</p></div><div class="capability"><div class="capability-no">02 / INBOX</div><div class="capability-mark">↗</div><h3>Smart inbox workflows</h3><p>Turn email conversations into organized leads, tasks, and follow-up opportunities.</p></div><div class="capability"><div class="capability-no">03 / FOLLOW-UP</div><div class="capability-mark">↗</div><h3>Personalized replies</h3><p>Draft helpful responses in your tone while keeping your team in control before anything is sent.</p></div><div class="capability"><div class="capability-no">04 / OPERATIONS</div><div class="capability-mark">↗</div><h3>Workflow automation</h3><p>Connect forms, inboxes, calendars, CRMs, and internal handoffs into one reliable system.</p></div><div class="capability"><div class="capability-no">05 / INSIGHT</div><div class="capability-mark">↗</div><h3>AI dashboards</h3><p>See what needs attention now, what is slipping, and where your next opportunity is.</p></div><div class="capability"><div class="capability-no">06 / CUSTOM</div><div class="capability-mark">↗</div><h3>Custom AI assistants</h3><p>Build a focused assistant for the questions, decisions, and processes unique to your company.</p></div></div></section>
<section class="reference-section dark"><div class="reference-kicker">Use case spotlight</div><h2>From first message to next meeting.</h2><div class="spotlight"><div class="spotlight-visual"><div class="mini-orb"></div></div><div><div class="reference-kicker">Lead response system</div><h3>Never lose the thread with a promising lead.</h3><p>LeadFlow reads the inquiry, understands urgency and intent, gives your team the context they need, and prepares a response that moves the conversation forward.</p><div class="prompt">“A lead just came in. What should we do next?”</div></div></div></section>
<section class="reference-section dark" id="process"><div class="reference-kicker">How it works</div><h2>From messy process to intelligent system.</h2><p class="lead">We start with one workflow, launch an MVP, and improve it around the way your team actually works.</p><div class="steps-reference"><div class="step-reference"><b>01</b><h3>Understand</h3><p>We map your tools, inputs, bottlenecks, and handoffs.</p></div><div class="step-reference"><b>02</b><h3>Design</h3><p>We shape the AI workflow around your goals and tone.</p></div><div class="step-reference"><b>03</b><h3>Launch</h3><p>We get a focused system live without a long implementation cycle.</p></div><div class="step-reference"><b>04</b><h3>Improve</h3><p>We measure what matters and keep making the workflow smarter.</p></div></div></section>
<section class="reference-section dark"><div class="reference-kicker">FAQ</div><h2>Common questions.</h2><div class="faq-list"><details open><summary>What kind of businesses is LeadFlow for?</summary><p>LeadFlow is designed for service businesses and sales teams that receive inquiries and want faster, more consistent follow-up.</p></details><details><summary>Will AI send messages automatically?</summary><p>The MVP prepares personalized drafts for review. Automated sending can be added later with the right approval rules.</p></details><details><summary>Can it work with our existing tools?</summary><p>Yes. We can shape the workflow around your inbox, forms, CRM, calendar, and the tools your team already uses.</p></details><details><summary>How do we get started?</summary><p>Book a short demo. We will identify one high-value workflow and show you what an initial automation could look like.</p></details></div></section>
<section class="reference-final reference-section dark"><div class="reference-kicker">Ready?</div><h2>Give your team<br><em>flow.</em></h2><p class="lead" style="margin:0 auto 30px">Tell us what is slowing your business down. We will show you where AI can create the most leverage.</p><a class="button" href="{{url_for('demo')}}">Book a free strategy call ↗</a></section>
<footer class="reference-footer"><span>LeadFlow AI · Intelligent automation for modern businesses</span><span>Built for teams that want to move faster.</span></footer>
</div>
"""
LANDING_TEMPLATE_V2 += """<script>let target=0,current=0;window.addEventListener('scroll',()=>{target=window.scrollY*.05},{passive:true});function drift(){current+=(target-current)*.07;document.body.style.setProperty('--parallax-y',(-current).toFixed(2)+'px');requestAnimationFrame(drift)}drift();</script>"""

DEMO_TEMPLATE = """
<div class="card" style="max-width:680px;margin:40px auto"><div class="eyebrow">Let's talk</div><h1>Book a free demo</h1><p class="section-intro">Tell us a little about your business and we will get back to you with next steps.</p>{% if success %}<div class="flash">Thanks — your demo request has been sent. We will be in touch shortly.</div>{% else %}<form method="post"><label for="name">Full name</label><input id="name" name="name" autocomplete="name" required><label for="email">Work email</label><input id="email" name="email" type="email" autocomplete="email" required><label for="company">Company</label><input id="company" name="company" autocomplete="organization"><label for="message">What would you like to automate?</label><textarea id="message" name="message" rows="6" placeholder="Tell us about your lead flow, inbox, or sales process..."></textarea><input name="website" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px" aria-hidden="true"><button type="submit">Send demo request</button></form>{% endif %}<p style="margin-top:22px"><a href="{{url_for('landing')}}">← Back to home</a></p></div>
"""


def page(content: str, **context):
    return render_template_string(BASE_TEMPLATE, content=render_template_string(content, **context), title=context.get("title"))


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def current_tenant_id() -> int:
    return int(session["tenant_id"])


def ensure_admin_account() -> None:
    """Initialize schema and the configured admin account for cloud startup."""
    core.init_db()
    if not config.ADMIN_PASSWORD:
        return
    with core.db() as conn:
        tenant = conn.execute("SELECT id FROM tenants WHERE name=?", (config.BUSINESS_NAME,)).fetchone()
        if not tenant:
            tenant_id = conn.execute("INSERT INTO tenants(name,created_at) VALUES(?,?)", (config.BUSINESS_NAME, core.now())).lastrowid
        else:
            tenant_id = tenant["id"]
        existing = conn.execute("SELECT id FROM users WHERE email=?", (config.ADMIN_EMAIL,)).fetchone()
        if not existing:
            conn.execute("INSERT INTO users(tenant_id,email,password_hash,created_at) VALUES(?,?,?,?)", (tenant_id, config.ADMIN_EMAIL, generate_password_hash(config.ADMIN_PASSWORD), core.now()))


@app.get("/health")
def health():
    return {"status": "ok"}


ensure_admin_account()


def oauth_client(provider: str):
    if not oauth:
        return None
    return oauth.create_client(provider)


def finish_oauth_login(profile: dict, provider: str):
    email = (profile.get("email") or profile.get("preferred_username") or "").strip().lower()
    if not email or "@" not in email:
        raise RuntimeError(f"{provider.title()} did not provide a usable email address.")
    display_name = (profile.get("name") or profile.get("given_name") or email.split("@", 1)[0]).strip()
    with core.db() as conn:
        existing = conn.execute("SELECT id,tenant_id FROM users WHERE email=?", (email,)).fetchone()
        if existing:
            user_id, tenant_id = existing["id"], existing["tenant_id"]
        else:
            workspace_name = f"{display_name}'s Workspace"
            tenant_id = conn.execute(
                "INSERT INTO tenants(name,created_at) VALUES(?,?)", (workspace_name, core.now())
            ).lastrowid
            user_id = conn.execute(
                "INSERT INTO users(tenant_id,email,password_hash,created_at) VALUES(?,?,?,?)",
                (tenant_id, email, generate_password_hash(secrets.token_urlsafe(32)), core.now()),
            ).lastrowid
    session.update(user_id=user_id, tenant_id=tenant_id, email=email)
    return redirect(url_for("dashboard"))


@app.get("/auth/google")
def google_login():
    client = oauth_client("google")
    if not client:
        flash("Google sign-in is not configured yet. Please use email and password.", "error")
        return redirect(url_for("login"))
    return client.authorize_redirect(url_for("google_callback", _external=True))


@app.get("/auth/google/callback")
def google_callback():
    try:
        client = oauth_client("google")
        if not client:
            raise RuntimeError("Google sign-in is not configured.")
        token = client.authorize_access_token()
        profile = token.get("userinfo") or client.userinfo()
        return finish_oauth_login(dict(profile), "Google")
    except Exception:
        app.logger.exception("Google OAuth sign-in failed")
        flash("Google sign-in could not be completed. Please try again.", "error")
        return redirect(url_for("login"))


@app.get("/auth/microsoft")
def microsoft_login():
    client = oauth_client("microsoft")
    if not client:
        flash("Microsoft sign-in is not configured yet. Please use email and password.", "error")
        return redirect(url_for("login"))
    return client.authorize_redirect(url_for("microsoft_callback", _external=True))


@app.get("/auth/microsoft/callback")
def microsoft_callback():
    try:
        client = oauth_client("microsoft")
        if not client:
            raise RuntimeError("Microsoft sign-in is not configured.")
        token = client.authorize_access_token()
        profile = token.get("userinfo") or client.userinfo()
        return finish_oauth_login(dict(profile), "Microsoft")
    except Exception:
        app.logger.exception("Microsoft OAuth sign-in failed")
        flash("Microsoft sign-in could not be completed. Please try again.", "error")
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        with core.db() as conn:
            user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], request.form.get("password", "")):
            session.update(user_id=user["id"], tenant_id=user["tenant_id"], email=user["email"])
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return page("""
    <div class="card" style="max-width:420px;margin:60px auto"><h1>Sign in</h1><p class="muted">Use your work account to access your LeadFlow workspace.</p>
    <div style="display:grid;gap:10px;margin:20px 0"><a class="button secondary" href="{{url_for('google_login')}}" style="text-align:center">Continue with Google</a><a class="button secondary" href="{{url_for('microsoft_login')}}" style="text-align:center">Continue with Microsoft</a></div>
    <div class="muted" style="text-align:center;margin:16px 0">or use email</div><form method="post">
    <label>Email</label><input name="email" type="email" required><label>Password</label><input name="password" type="password" required><button>Sign in</button></form></div>
    """)


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/")
def landing():
    return page(LANDING_TEMPLATE_V2, contact_email=config.CONTACT_EMAIL, title="LeadFlow AI")


@app.route("/demo", methods=["GET", "POST"])
def demo():
    success = False
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        company = request.form.get("company", "").strip()
        message_text = request.form.get("message", "").strip()
        honeypot = request.form.get("website", "").strip()
        if honeypot:
            success = True
        elif not name or "@" not in email:
            flash("Please enter your name and a valid work email.", "error")
        elif not config.SMTP_USER or not config.SMTP_PASSWORD:
            flash("Demo requests are not configured yet. Please try again later.", "error")
        else:
            try:
                msg = EmailMessage()
                msg["Subject"] = f"New LeadFlow AI demo request from {name}"
                msg["From"] = config.SMTP_USER
                msg["To"] = config.CONTACT_EMAIL
                msg["Reply-To"] = email
                msg.set_content(f"Name: {name}\nEmail: {email}\nCompany: {company or '-'}\n\nWhat they want to automate:\n{message_text or '-'}")
                with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=20) as smtp:
                    smtp.starttls()
                    smtp.login(config.SMTP_USER, config.SMTP_PASSWORD)
                    smtp.send_message(msg)
                success = True
            except Exception:
                app.logger.exception("Demo request SMTP delivery failed")
                flash("We could not send your request right now. Please try again shortly.", "error")
    return page(DEMO_TEMPLATE, success=success, title="Book a demo")


@app.get("/dashboard")
@login_required
def dashboard():
    status = request.args.get("status", "").upper()
    with core.db() as conn:
        where = "WHERE tenant_id=?"
        params = [current_tenant_id()]
        if status in {"HOT", "WARM", "COLD"}:
            where += " AND status=?"; params.append(status)
        rows = conn.execute(f"SELECT * FROM leads {where} ORDER BY lead_score DESC,id DESC", params).fetchall()
        counts = {s: conn.execute("SELECT COUNT(*) FROM leads WHERE tenant_id=? AND status=?", (current_tenant_id(), s)).fetchone()[0] for s in ("HOT", "WARM", "COLD")}
    return page("""
    <h1>Lead dashboard</h1><div class="grid"><div class="card"><div class="muted">HOT</div><div class="metric">{{counts.HOT}}</div></div><div class="card"><div class="muted">WARM</div><div class="metric">{{counts.WARM}}</div></div><div class="card"><div class="muted">COLD</div><div class="metric">{{counts.COLD}}</div></div></div>
    <div class="card"><a class="button" href="{{url_for('new_lead')}}">+ Add lead</a> <a class="button secondary" href="{{url_for('dashboard')}}">All</a> <a class="button secondary" href="{{url_for('dashboard',status='HOT')}}">HOT only</a></div>
    <div class="card"><table class="table"><tr><th>Lead</th><th>Company</th><th>Score</th><th>Status</th><th>Created</th></tr>{% for lead in rows %}<tr><td><a href="{{url_for('lead_detail',lead_id=lead.id)}}">{{lead.name or 'Unknown'}}</a><br><span class="muted">{{lead.email or ''}}</span></td><td>{{lead.company or '-'}}</td><td>{{lead.lead_score}}/100</td><td><span class="badge {{lead.status}}">{{lead.status}}</span></td><td>{{lead.created_at}}</td></tr>{% else %}<tr><td colspan="5">No leads yet.</td></tr>{% endfor %}</table></div>
    """, rows=rows, counts=counts)


@app.route("/leads/new", methods=["GET", "POST"])
@login_required
def new_lead():
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        if not text:
            flash("Paste the lead message first.", "error")
        else:
            try:
                lead = core.analyze(text)
                reply = core.generate_reply(lead, text)
                with core.db() as conn:
                    values = [lead.get(k) for k in core.FIELDS[:7]]
                    values += [lead["lead_score"], lead["status"], lead.get("reason"), lead.get("recommended_action"), reply, core.now()]
                    cur = conn.execute("""INSERT INTO leads (tenant_id,name,company,email,phone,service,budget,timeline,lead_score,status,reason,recommended_action,ai_email,created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", [current_tenant_id(), *values])
                return redirect(url_for("lead_detail", lead_id=cur.lastrowid))
            except Exception:
                app.logger.exception("Lead analysis failed")
                flash("We could not analyze this lead right now. Please check your AI configuration and try again.", "error")
    return page("""<h1>Add lead</h1><div class="card"><form method="post"><label>Paste incoming lead email/message</label><textarea name="text" rows="12" required></textarea><button>Analyze and save</button></form></div>""")


@app.get("/leads/<int:lead_id>")
@login_required
def lead_detail(lead_id: int):
    with core.db() as conn:
        lead = conn.execute("SELECT * FROM leads WHERE id=? AND tenant_id=?", (lead_id, current_tenant_id())).fetchone()
    if not lead:
        return "Not found", 404
    return page("""<a href="{{url_for('dashboard')}}">← Dashboard</a><h1>{{lead.name or 'Unknown lead'}}</h1><div class="card"><p><b>Company:</b> {{lead.company or '-'}}</p><p><b>Email:</b> {{lead.email or '-'}}</p><p><b>Service:</b> {{lead.service or '-'}}</p><p><b>Score:</b> {{lead.lead_score}}/100 <span class="badge {{lead.status}}">{{lead.status}}</span></p><p><b>Reason:</b> {{lead.reason or '-'}}</p><p><b>Recommended action:</b> {{lead.recommended_action or '-'}}</p></div><div class="card"><h2>Draft reply</h2><pre style="white-space:pre-wrap">{{lead.ai_email or '-'}}</pre><p class="muted">MVP safety: saving a draft does not send an email.</p></div>""", lead=lead)


def setup():
    core.init_db()
    if not config.ADMIN_PASSWORD:
        raise SystemExit("Set ADMIN_EMAIL and ADMIN_PASSWORD in .env before setup.")
    with core.db() as conn:
        tenant = conn.execute("SELECT id FROM tenants WHERE name=?", (config.BUSINESS_NAME,)).fetchone()
        if not tenant:
            tenant = conn.execute("INSERT INTO tenants(name,created_at) VALUES(?,?)", (config.BUSINESS_NAME, core.now()))
            tenant_id = tenant.lastrowid
        else:
            tenant_id = tenant["id"]
        conn.execute("INSERT OR REPLACE INTO users(tenant_id,email,password_hash,created_at) VALUES(?,?,?,?)", (tenant_id, config.ADMIN_EMAIL, generate_password_hash(config.ADMIN_PASSWORD), core.now()))
    print(f"MVP ready. Login: {config.ADMIN_EMAIL}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["setup", "run"])
    args = parser.parse_args()
    if args.command == "setup": setup()
    else: app.run(host=config.HOST, port=config.PORT, debug=False)
