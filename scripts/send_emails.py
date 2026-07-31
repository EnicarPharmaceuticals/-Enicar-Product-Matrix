"""Mailer for the Product Matrixing workflow (runs in GitHub Actions).

Fetches PENDING rows from the Apps Script endpoint, resolves recipients from
config/recipients.json, sends via Gmail SMTP, then marks the rows sent.

DRY_RUN defaults to true: emails are printed to the job log and the sheet rows
are marked DRY_RUN_LOGGED instead of SENT. Set the workflow's DRY_RUN variable
to "false" only after reviewing a dry run.

Environment:
    APPS_SCRIPT_URL     web-app /exec URL          (repo variable or secret)
    SCRIPT_TOKEN        matches Script Properties  (repo secret)
    MAIL_USERNAME       Gmail address              (repo secret)
    MAIL_APP_PASSWORD   Gmail app password         (repo secret)
    DRY_RUN             "true" (default) | "false"
    RECIPIENTS_JSON     role->addresses JSON (repo secret; keeps real addresses
                        out of a public repo). Falls back to config/recipients.json
"""

import json
import os
import smtplib
import ssl
import sys
import urllib.parse
import urllib.request
from email.message import EmailMessage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fetch_pending(url, token):
    q = urllib.parse.urlencode({"action": "pendingEmails", "token": token})
    with urllib.request.urlopen(f"{url}?{q}", timeout=60) as resp:
        data = json.load(resp)
    if not data.get("ok"):
        raise SystemExit(f"Apps Script error: {data.get('error')}")
    return data.get("emails", [])


def mark_sent(url, token, ids, dry_run):
    body = json.dumps({"action": "markSent", "token": token,
                       "email_ids": ids, "dry_run": dry_run}).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.load(resp)
    if not data.get("ok"):
        raise SystemExit(f"markSent failed: {data.get('error')}")


def main():
    url = os.environ.get("APPS_SCRIPT_URL", "")
    token = os.environ.get("SCRIPT_TOKEN", "")
    dry_run = os.environ.get("DRY_RUN", "true").strip().lower() != "false"
    if not url or not token:
        raise SystemExit("APPS_SCRIPT_URL and SCRIPT_TOKEN must be set")

    # Recipients come from the RECIPIENTS_JSON secret when set, so real addresses
    # never sit in a public repo. config/recipients.json is the local fallback.
    raw = os.environ.get("RECIPIENTS_JSON", "").strip()
    if raw:
        recipients = json.loads(raw)
        print("recipients: loaded from RECIPIENTS_JSON secret")
    else:
        path = os.path.join(ROOT, "config", "recipients.json")
        if not os.path.exists(path):
            raise SystemExit("No recipients: set the RECIPIENTS_JSON secret "
                             "or provide config/recipients.json")
        with open(path, encoding="utf-8") as fh:
            recipients = json.load(fh)
        print(f"recipients: loaded from {path}")

    pending = fetch_pending(url, token)
    print(f"pending emails: {len(pending)}  (DRY_RUN={dry_run})")
    if not pending:
        return

    sender = os.environ.get("MAIL_USERNAME", "")
    password = os.environ.get("MAIL_APP_PASSWORD", "")
    if not dry_run and (not sender or not password):
        raise SystemExit("MAIL_USERNAME / MAIL_APP_PASSWORD required when DRY_RUN=false")

    done = []
    smtp = None
    unresolved = 0
    try:
        for em in pending:
            # to_role may name several roles: "qa,director". Resolve each and
            # de-duplicate, preserving order so the primary role is first.
            roles = [r.strip().lower() for r in str(em.get("to_role", "")).split(",")
                     if r.strip()]
            to, missing = [], []
            for role in roles:
                addrs = recipients.get(role, [])
                if not addrs or any("PLACEHOLDER" in a.upper() for a in addrs):
                    missing.append(role)
                    continue
                for a in addrs:
                    if a not in to:
                        to.append(a)
            if missing:
                print(f"!! {em['email_id']}: no real address for role(s) "
                      f"{', '.join(missing)} - fill config/recipients.json.")
            if not to:
                print(f"   {em['email_id']}: skipped, no resolvable recipient.")
                unresolved += 1
                continue
            if missing:
                print(f"   {em['email_id']}: sending to the roles that ARE "
                      f"configured ({', '.join(to)}); {', '.join(missing)} omitted.")
            if dry_run:
                print("-" * 70)
                print(f"WOULD SEND {em['email_id']}  to: {', '.join(to)}")
                print(f"Subject: {em['subject']}")
                print(em["body"])
            else:
                if smtp is None:
                    smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465,
                                            context=ssl.create_default_context())
                    smtp.login(sender, password)
                msg = EmailMessage()
                msg["From"] = sender
                msg["To"] = ", ".join(to)
                msg["Subject"] = em["subject"]
                msg.set_content(em["body"])
                smtp.send_message(msg)
                print(f"sent {em['email_id']} to {', '.join(to)}")
            done.append(em["email_id"])
    finally:
        if smtp is not None:
            smtp.quit()

    if done:
        mark_sent(url, token, done, dry_run)
        print(f"marked {len(done)} email(s) as "
              f"{'DRY_RUN_LOGGED' if dry_run else 'SENT'}")
    if unresolved:
        print(f"{unresolved} email(s) left PENDING - recipients not configured")
        sys.exit(1)


if __name__ == "__main__":
    main()
