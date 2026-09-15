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

import app as core
import config

app = Flask(__name__)
app.secret_key = config.WEB_SECRET_KEY

BASE_TEMPLATE = """
<!doctype html><html lang="mk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title or 'LeadFlow AI' }}</title><style>
*{box-sizing:border-box}body{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f7f9fc;color:#172033;margin:0}nav{background:#0b1220;color:white;padding:18px 6%;display:flex;justify-content:space-between;align-items:center}nav a{color:#dbeafe;text-decoration:none;margin-left:20px}.brand{font-weight:800;letter-spacing:-.4px}.brand span{color:#60a5fa}main{max-width:1100px;margin:32px auto;padding:0 20px}.card{background:white;border:1px solid #e5e7eb;border-radius:16px;padding:22px;margin-bottom:20px;box-shadow:0 8px 24px #1118270b}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px}.metric{font-size:30px;font-weight:700}.muted{color:#667085}.badge{border-radius:99px;padding:5px 10px;font-size:12px;font-weight:700}.HOT{background:#fee2e2;color:#991b1b}.WARM{background:#fef3c7;color:#92400e}.COLD{background:#dbeafe;color:#1e40af}input,textarea{width:100%;box-sizing:border-box;padding:10px;border:1px solid #d0d5dd;border-radius:8px;margin:6px 0 14px}button,.button{background:#2563eb;color:white;border:0;border-radius:9px;padding:11px 16px;text-decoration:none;cursor:pointer;font-weight:650;display:inline-block}.button.secondary{background:#475467}.flash{background:#ecfdf3;padding:10px;border-radius:8px;margin-bottom:16px}.error{background:#fef2f2}.table{width:100%;border-collapse:collapse}.table th,.table td{text-align:left;border-bottom:1px solid #eaecf0;padding:12px 8px}
.hero{position:relative;overflow:hidden;background:linear-gradient(135deg,#0b1220 0%,#172554 55%,#1d4ed8 100%);color:white;padding:82px 8%;border-radius:24px;margin-top:28px;box-shadow:0 18px 45px #1d4ed833}.hero:after{content:"";position:absolute;width:320px;height:320px;border-radius:50%;background:#60a5fa33;right:-80px;top:-110px;filter:blur(2px)}.eyebrow{color:#93c5fd;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;font-size:12px}.hero h1{max-width:700px;font-size:clamp(38px,6vw,70px);line-height:1.02;letter-spacing:-3px;margin:16px 0}.hero p{max-width:610px;color:#dbeafe;font-size:19px;line-height:1.6}.hero-actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:28px}.hero .button{background:#60a5fa;color:#07111f}.hero .button.secondary{background:#ffffff1a;color:white;border:1px solid #ffffff33}.section{padding:70px 0 20px}.section h2{font-size:36px;letter-spacing:-1.5px;margin:8px 0 12px}.section-intro{max-width:650px;color:#667085;font-size:17px;line-height:1.6}.feature{height:100%;padding:24px}.icon{width:42px;height:42px;border-radius:12px;background:#dbeafe;color:#1d4ed8;display:grid;place-items:center;font-size:22px;font-weight:800;margin-bottom:18px}.feature h3{margin:0 0 9px;font-size:19px}.feature p{color:#667085;line-height:1.55;margin:0}.steps{counter-reset:step;display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:16px}.step{position:relative}.step:before{counter-increment:step;content:"0" counter(step);font-size:13px;color:#2563eb;font-weight:800}.step h3{margin:12px 0 8px}.step p{color:#667085;line-height:1.5}.cta{background:#eaf2ff;border:1px solid #bfdbfe;text-align:center;padding:44px 20px;border-radius:20px;margin:70px 0 30px}.cta h2{margin:0 0 10px;font-size:32px}.cta p{color:#536178;margin-bottom:24px}.landing-footer{text-align:center;color:#667085;padding:0 0 28px;font-size:13px}@media(max-width:640px){.hero{padding:52px 26px}.hero h1{letter-spacing:-2px}.hero p{font-size:17px}.section{padding-top:45px}}
</style></head><body><nav><a class="brand" href="{{url_for('landing')}}">Lead<span>Flow</span> AI</a><div><a href="#features">Features</a>{% if session.get('user_id') %}<a href="{{url_for('dashboard')}}">Dashboard</a><a href="{{url_for('logout')}}">Log out</a>{% else %}<a href="{{url_for('login')}}">Sign in</a>{% endif %}</div></nav><main>{% with messages=get_flashed_messages(with_categories=true) %}{% for category,message in messages %}<div class="flash {{category}}">{{message}}</div>{% endfor %}{% endwith %}{{content|safe}}</main></body></html>
"""

LANDING_TEMPLATE = """
<section class="hero"><div class="eyebrow">AI-powered lead response system</div><h1>Stop letting valuable leads go cold.</h1><p>LeadFlow AI analyzes new inquiries, identifies your highest-potential prospects, and prepares personalized replies — so your team can respond faster and close more business.</p><div class="hero-actions"><a class="button" href="{{url_for('demo')}}">Book a free demo →</a><a class="button secondary" href="#features">See how it works</a></div></section>
<section class="section" id="features"><div class="eyebrow">What you get</div><h2>From inbox to next step.</h2><p class="section-intro">A simple workflow that helps sales teams respond on time, with better context and less manual sorting.</p><div class="grid" style="margin-top:26px"><div class="card feature"><div class="icon">✦</div><h3>AI lead qualification</h3><p>Every lead receives a score and HOT, WARM, or COLD category based on need, budget, and urgency.</p></div><div class="card feature"><div class="icon">↗</div><h3>Personalized replies</h3><p>Generate a professional draft based on the real inquiry — without inventing prices or promises.</p></div><div class="card feature"><div class="icon">◉</div><h3>Clear dashboard</h3><p>Keep prospects organized in one place with priorities, details, and a recommended next action.</p></div></div></section>
<section class="section"><div class="eyebrow">How it works</div><h2>Three steps to better follow-up.</h2><div class="steps" style="margin-top:28px"><div class="step"><h3>1. A lead arrives</h3><p>A message from a web form or inbox enters the workflow.</p></div><div class="step"><h3>2. AI understands the context</h3><p>The system extracts needs, budget, timeline, and buying intent.</p></div><div class="step"><h3>3. Your team moves faster</h3><p>Get a clear priority and a ready-to-review draft reply.</p></div></div></section>
<section class="cta"><h2>Ready to lose fewer leads?</h2><p>Book a short demo and see how this workflow can fit your business.</p><a class="button" href="{{url_for('demo')}}">Book a demo</a></section><div class="landing-footer">LeadFlow AI · AI automation for service businesses</div>
"""

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
    <div class="card" style="max-width:420px;margin:60px auto"><h1>Sign in</h1><form method="post">
    <label>Email</label><input name="email" type="email" required><label>Password</label><input name="password" type="password" required><button>Sign in</button></form></div>
    """)


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/")
def landing():
    return page(LANDING_TEMPLATE, contact_email=config.CONTACT_EMAIL, title="LeadFlow AI")


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
            except Exception as exc:
                flash(f"Analysis failed: {exc}", "error")
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
