# Enicar Product Matrix — dashboard

Live: https://enicarpharmaceuticals.github.io/-Enicar-Product-Matrix/

This repository holds **only the published dashboard and the email workflow**.
Source documents (licence PDFs, the Bill of Material PDF) and the extraction
pipeline are deliberately **not** here — the repository is public.

| Path | What it is |
|---|---|
| `index.html`, `data.js`, `bom.js`, `config.js`, `logo.png` | the dashboard |
| `scripts/send_emails.py` | sends queued notifications via Gmail SMTP |
| `.github/workflows/send-emails.yml` | runs the mailer every 30 min (dry-run by default) |

Email addresses are **not** stored here; they come from the `RECIPIENTS_JSON`
repository secret.
