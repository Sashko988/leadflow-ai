"""Central environment-based configuration for the product."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

BUSINESS_NAME = os.getenv("BUSINESS_NAME", "Your Business Name")
SENDER_NAME = os.getenv("SENDER_NAME", "Your Name")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
_database_path = Path(os.getenv("DATABASE_PATH", "data/leads.db"))
DATABASE_PATH = _database_path if _database_path.is_absolute() else BASE_DIR / _database_path
GMAIL_QUERY = os.getenv("GMAIL_QUERY", 'in:inbox subject:"New Website Lead" -from:me')
MAX_EMAILS_PER_RUN = max(1, int(os.getenv("MAX_EMAILS_PER_RUN", "20")))
DRY_RUN = os.getenv("DRY_RUN", "true").strip().lower() in {"1", "true", "yes", "on"}
TEST_EMAIL = os.getenv("TEST_EMAIL", "").strip()
WEB_SECRET_KEY = os.getenv("WEB_SECRET_KEY", "change-this-in-production")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com").strip().lower()
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", ADMIN_EMAIL).strip().lower()
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "").strip()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID", "").strip()
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET", "").strip()
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))


def ensure_directories() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
