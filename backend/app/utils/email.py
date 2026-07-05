"""
app/utils/email.py
------------------
Email sending utility using Gmail SMTP via STARTTLS.

Configuration (all from backend/.env):
    EMAIL_ADDRESS  — Gmail address used as sender AND SMTP login username
                     e.g.  kavyasakthivelsk@gmail.com
    EMAIL_PASSWORD — Gmail App Password (16 characters, NOT your Gmail password)
                     Generate at: https://myaccount.google.com/apppasswords
    FRONTEND_URL   — Base URL of the React app, used in the reset link
                     e.g.  http://localhost:5173

Gmail App Password setup (required — normal Gmail password won't work):
  1. Go to your Google Account → Security.
  2. Enable 2-Step Verification if not already on.
  3. Search for "App Passwords" (or go to myaccount.google.com/apppasswords).
  4. Select app "Mail", device "Other", give it a name, click Generate.
  5. Copy the 16-character password (spaces don't matter) into EMAIL_PASSWORD.

Dev fallback:
  If EMAIL_ADDRESS or EMAIL_PASSWORD are missing, the reset link is printed
  to the server terminal so the flow can be tested without an email account.
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — loaded from .env at import time
# ---------------------------------------------------------------------------
EMAIL_ADDRESS:  str = os.getenv("EMAIL_ADDRESS",  "").strip()
EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "").strip()
FRONTEND_URL:   str = os.getenv("FRONTEND_URL",   "http://localhost:5173").rstrip("/")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587   # STARTTLS


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def send_password_reset_email(to_email: str, reset_token: str) -> None:
    """
    Send a password reset email to the given address.

    Args:
        to_email:    Recipient's email address.
        reset_token: Signed JWT reset token (1-hour expiry).

    The reset link is:
        {FRONTEND_URL}/reset-password?token={reset_token}

    Dev mode (EMAIL_ADDRESS or EMAIL_PASSWORD not set):
        Prints the reset link to the terminal instead of sending an email.
        This lets you test the full reset flow without configuring Gmail.

    Raises:
        RuntimeError: On SMTP authentication or network failure when email
                      credentials ARE configured.
    """
    reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        # ── Development fallback ────────────────────────────────────
        logger.warning(
            "[Email] EMAIL_ADDRESS or EMAIL_PASSWORD not set in .env — "
            "printing reset link to terminal (dev mode only)."
        )
        print("\n" + "=" * 70)
        print("[Email] DEV MODE — password reset link (not sent via email):")
        print(f"  To:    {to_email}")
        print(f"  Link:  {reset_link}")
        print("=" * 70 + "\n")
        return

    subject   = "Reset your Shopping AI password"
    html_body = _build_reset_email_html(reset_link)
    text_body = _build_reset_email_text(reset_link)

    logger.info("[Email] Sending reset email to: %s", to_email)
    _send_via_smtp(to_email, subject, html_body, text_body)


# ---------------------------------------------------------------------------
# Private: SMTP send
# ---------------------------------------------------------------------------

def _send_via_smtp(
    to_email:  str,
    subject:   str,
    html_body: str,
    text_body: str,
) -> None:
    """Send an email via Gmail SMTP using STARTTLS."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Shopping AI <{EMAIL_ADDRESS}>"
    msg["To"]      = to_email

    # Plain text first, HTML second (RFC 2046 — clients prefer last part)
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        logger.debug("[Email] Connecting to %s:%d …", SMTP_HOST, SMTP_PORT)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())

        logger.info("[Email] Reset email sent successfully to: %s", to_email)
        print(f"[Email] Reset email sent successfully to: {to_email}")

    except smtplib.SMTPAuthenticationError as exc:
        logger.error(
            "[Email] SMTP authentication failed for %s. "
            "Verify EMAIL_ADDRESS and EMAIL_PASSWORD in backend/.env. "
            "Use a Gmail App Password — your normal Gmail password will NOT work. "
            "Error: %s",
            EMAIL_ADDRESS,
            exc,
        )
        raise RuntimeError(
            "Email authentication failed. "
            "Check EMAIL_ADDRESS and EMAIL_PASSWORD in backend/.env."
        ) from exc

    except smtplib.SMTPRecipientsRefused as exc:
        logger.error("[Email] Recipient refused: %s — %s", to_email, exc)
        raise RuntimeError(f"Recipient address rejected: {to_email}") from exc

    except smtplib.SMTPException as exc:
        logger.error("[Email] SMTP error while sending to %s: %s", to_email, exc)
        raise RuntimeError(f"SMTP error: {exc}") from exc

    except OSError as exc:
        logger.error(
            "[Email] Network error connecting to %s:%d — %s",
            SMTP_HOST, SMTP_PORT, exc,
        )
        raise RuntimeError(
            f"Could not connect to Gmail SMTP ({SMTP_HOST}:{SMTP_PORT}). "
            "Check your internet connection."
        ) from exc


# ---------------------------------------------------------------------------
# Private: email templates
# ---------------------------------------------------------------------------

def _build_reset_email_html(reset_link: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Reset your password</title>
  <style>
    body  {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
             background: #0F172A; margin: 0; padding: 0; }}
    .wrap {{ max-width: 560px; margin: 40px auto; padding: 0 16px; }}
    .card {{ background: #1E293B; border: 1px solid rgba(99,102,241,0.25);
             border-radius: 16px; padding: 40px 36px; }}
    .logo {{ font-size: 13px; font-weight: 900; letter-spacing: 0.1em;
             color: #6366F1; margin-bottom: 28px; }}
    h1   {{ font-size: 22px; font-weight: 700; color: #E2E8F0; margin: 0 0 12px; }}
    p    {{ font-size: 15px; color: #94A3B8; line-height: 1.6; margin: 0 0 24px; }}
    .btn {{ display: inline-block; padding: 14px 32px;
            background: linear-gradient(135deg,#6366F1,#8B5CF6);
            color: #fff !important; text-decoration: none; border-radius: 8px;
            font-size: 15px; font-weight: 600; letter-spacing: 0.02em; }}
    .expire    {{ font-size: 13px; color: #F87171; margin-top: 20px; }}
    .link-note {{ font-size: 13px; color: #475569; margin-top: 28px; }}
    .link-note a {{ color: #6366F1; word-break: break-all; }}
    .ignore    {{ font-size: 13px; color: #475569; margin-top: 20px; }}
    .footer    {{ font-size: 12px; color: #334155; text-align: center;
                  margin-top: 32px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <div class="logo">SHOPPING AI</div>
      <h1>Reset your password</h1>
      <p>
        We received a request to reset the password for your Shopping AI account.
        Click the button below to choose a new password.
      </p>
      <a href="{reset_link}" class="btn">Reset Password</a>
      <p class="expire">&#9200; This link expires in <strong>1 hour</strong>.</p>
      <p class="link-note">
        Button not working? Copy and paste this link into your browser:<br>
        <a href="{reset_link}">{reset_link}</a>
      </p>
      <p class="ignore">
        If you did not request a password reset, you can safely ignore this email.
        Your password will not be changed.
      </p>
    </div>
    <div class="footer">Shopping AI &copy; 2026</div>
  </div>
</body>
</html>""".strip()


def _build_reset_email_text(reset_link: str) -> str:
    return (
        "SHOPPING AI — Reset your password\n"
        "==================================\n\n"
        "We received a request to reset the password for your account.\n\n"
        f"Reset link (expires in 1 hour):\n{reset_link}\n\n"
        "If you did not request a password reset, ignore this email.\n"
        "Your password will not be changed.\n\n"
        "— Shopping AI"
    )
