# AI Lead Automation

A small, client-deployable lead workflow: read new Gmail enquiries, qualify them with an AI model, save a searchable local CRM record, and draft a professional reply.

## MVP web application

The first SaaS MVP is available as a small web app with a separate workspace for each account, login, dashboard, HOT/WARM/COLD filters, manual lead intake, AI qualification, and reply drafts. Drafts are never sent from the web UI yet.

```text
python -m pip install -r requirements.txt
python web.py setup
python web.py run
```

Open `http://127.0.0.1:8000`. Set `ADMIN_PASSWORD` in `.env` before running setup. For a hosted deployment, use a real `WEB_SECRET_KEY`, HTTPS, a managed database, and a proper user-invite flow.

## Deploy on Render

The repository includes `render.yaml`. Push this folder to a GitHub repository, then create a new Render Blueprint from that repository. Render will use `pip install -r requirements.txt` and `gunicorn web:app --bind 0.0.0.0:$PORT --workers 2` to build and run the service. Add the secret environment variables requested by the Blueprint (`OPENAI_API_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and `CONTACT_EMAIL`). The `/health` endpoint can be used as a basic health check.

The included SQLite database is suitable for an MVP demo only. A public client deployment should use a managed Postgres database or a persistent disk before storing important customer data.

The public landing page uses `/demo` for demo requests. Configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, and `CONTACT_EMAIL` in Render. For Gmail, use an App Password rather than your normal account password.

## What changed for client readiness

- Documented CLI entrypoint: `app.py`, plus web MVP entrypoint: `web.py`.
- Environment-based configuration; no secrets or client-specific email addresses in code.
- `DRY_RUN=true` by default. Sending requires both `DRY_RUN=false` and `--send`.
- Idempotency by Gmail message ID, so a message is not processed twice.
- SQLite schema is created automatically under `data/`.
- AI JSON is validated and scores/status values are normalized.
- Legacy scripts are retained for reference only; do not use them for production runs.

## Setup

1. Use Python 3.11+ and create a virtual environment.
2. Install dependencies: `python -m pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and fill in `OPENAI_API_KEY`, `BUSINESS_NAME`, and `SENDER_NAME`.
4. Run `python app.py init-db`.
5. For Gmail, create a Google OAuth Desktop App credential, save it locally as `credentials.json`, and run `python app.py process-gmail` once to authorize.

## Commands

```text
python app.py init-db
python app.py analyze --text "Customer enquiry text"
python app.py list
python app.py hot
python app.py process-gmail                 # preview/dry-run workflow
python app.py process-gmail --send          # only after DRY_RUN=false
```

The first Gmail run only reads messages. To send replies, configure a test address in `TEST_EMAIL`, validate the preview, then explicitly set `DRY_RUN=false` and use `--send`. Review Google OAuth scopes and client consent requirements before deployment.

## Security and deployment checklist

- Never commit `.env`, `credentials.json`, `token.json`, or `*.db`.
- Use a separate OpenAI key and Google OAuth project per client; set usage limits/billing alerts.
- Rotate any credentials that were previously stored in this folder before using the product with a client.
- Back up the database and define a retention/deletion policy for personal data.
- Keep human approval in the loop until reply quality, filtering, and legal/privacy requirements are verified.
- The MVP is not yet a public SaaS: it still needs hosted deployment, billing, password reset, email verification, rate limiting, audit logs, and a managed production database.
- Run the process as a scheduled job with a dedicated service account/user and restricted filesystem permissions.
