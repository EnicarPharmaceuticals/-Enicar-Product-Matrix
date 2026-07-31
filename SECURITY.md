# Security — how the confidential data is protected

The dashboard holds Enicar's complete formulation book (every raw material and
quantity for 1,907 products) plus licence and permission numbers. It is
published on GitHub Pages, which serves files to anyone with the link. So the
data itself is encrypted before it is ever published.

## What is published, and what it contains

| File | Contents | Readable by a stranger? |
|---|---|---|
| `vault.js` | all matrix data, all BOM data, the Apps Script write token | **No** — AES-256-GCM ciphertext |
| `index.html` | the application code | Yes — contains no data and no key |
| `config.js` | the Apps Script URL only | Yes — harmless without the token |
| `logo.png` | the company logo | Yes |

`data.js` and `bom.js` — the plaintext bundles — are **never published**.
`scripts/refresh_site.py` copies only the files above.

## How the encryption works

- **Cipher:** AES-256-GCM. GCM is authenticated, so tampering is detected too.
- **Key derivation:** PBKDF2-HMAC-SHA256, **600,000 iterations**, 16-byte random
  salt (OWASP 2023 guidance). This makes brute-forcing the passphrase expensive.
- **Passphrase:** 25 characters, ~145 bits of entropy, generated with a CSPRNG.
- **Where decryption happens:** in the browser, via the Web Crypto API. The
  passphrase is never transmitted anywhere and never stored on the site. Within
  one browser session it is held in `sessionStorage` and cleared when the tab
  closes.

Verified after publishing: the ciphertext has a byte entropy of 8.000/8.000
bits — statistically indistinguishable from random noise — and no product name,
material code or licence number appears in it.

## Who can do what

| | Requirement |
|---|---|
| **View the matrix** | the access passphrase |
| **RA writes** (add permission, confirm licence link, submit documents) | the RA password |
| **QA writes** (add BOM, submit BOM PDFs) | the QA password |

RA and QA passwords are held in Apps Script **Script Properties** and checked on
Google's server, so they cannot be bypassed by editing the page. The write token
lives inside the encrypted vault, so it cannot be obtained without the
passphrase either.

## Keys, and where they live

| Secret | Where it is kept | Never |
|---|---|---|
| Access passphrase | `config/vault_key.txt` on the Director's Mac (git-ignored, mode 600) | in the repository, or in the same message as the link |
| RA / QA passwords | Apps Script Script Properties | in the repository |
| Apps Script token | inside `vault.js` (encrypted) + `config/local_settings.json` locally (git-ignored) | in plaintext on the site |
| Gmail app password | GitHub Actions secret | anywhere else |

## Rotating the access passphrase

If it leaks, or someone leaves:

```bash
python3 scripts/encrypt_bundle.py --new-key   # prints the new passphrase
python3 scripts/refresh_site.py
cd dashboard-site && git add -A && git commit -m "Rotate vault key" && git push
```

Everyone must be given the new passphrase; the old one stops working as soon as
the new `vault.js` is live.

## Residual risks — be aware of these

1. **The passphrase is shared, not per-person.** Anyone who has it can read
   everything, and it cannot be revoked for one individual — rotation affects
   everyone. Send it separately from the link, ideally by a different channel.
2. **A person who unlocks the dashboard can copy what they see.** Encryption
   controls who gets in; it cannot stop an authorised viewer from taking data.
3. **The data was published in plaintext before 31/07/2026.** `data.js` and
   `bom.js` were readable for roughly one day, and the history has since been
   rewritten. GitHub can retain unreferenced objects for a period, so for a
   guaranteed purge the repository should be deleted and recreated (see below).
4. **Access is not logged.** GitHub Pages does not record who downloaded the
   site. Writes *are* logged, in the AuditLog tab.

## Recommended: delete and recreate the repository

To eliminate risk 3 entirely:

1. Repository **Settings → Danger Zone → Delete this repository**.
2. Create it again with the same name, **Private** if you prefer (note: GitHub
   Pages needs a public repository on the free plan).
3. Tell me, and I will push the encrypted site again and re-enable Pages.

Everything published from that point contains no readable data.
