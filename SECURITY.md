# Security — how the confidential data is protected

The dashboard holds Enicar's complete formulation book (every raw material and
quantity for 1,907 products) plus licence and permission numbers. It is
published on GitHub Pages, which serves files to anyone with the link. So the
data itself is encrypted before it is ever published.

## Two levels of access

| | Who | Protected how |
|---|---|---|
| **Dashboard, families, licences, compositions** | anyone with the link | not protected — open by decision (31/07/2026) |
| **View the BOM** | Verma Sir, Nimish, Swarali | **view-only BOM password** |
| **View + add BOMs** | QA | **QA password** — opens the BOM *and* authorises QA writes |
| **Add licences** | RA | **RA password** — no BOM access |

Three separate secrets. The view-only password decrypts the BOM and nothing
else: it grants no write access at all, because writes are checked server-side
against the RA and QA passwords, which it does not match. RA can add licences but
cannot open the BOM unless separately given one of the BOM passwords.

**How two passwords open one file.** The BOM is encrypted once under a random
data key; that data key is then wrapped separately under each password
(envelope encryption). Adding, changing or revoking one password re-wraps only
that key — the data is never re-encrypted and the other password is unaffected.
The wraps are stored unlabelled, so the published file does not reveal which is
which.

Compositions (label claims) are open deliberately: they are printed on the pack
and leaflet, so they are not manufacturing secrets. The BOM is the formulation
and is the thing being protected.

## What is published, and what it contains

| File | Contents | Readable by a stranger? |
|---|---|---|
| `site-data.js` | matrix, families, licence references, compositions | Yes — by design |
| `site-bom.enc.js` | every raw material and quantity, packing materials | **No** — AES-256-GCM ciphertext |
| `index.html` | application code | Yes — contains no data, no key |
| `config.js` | the Apps Script URL only | Yes — harmless |

`data.js` and `bom.js` (the plaintext working files) are **never** published;
`scripts/refresh_site.py` copies only the files above.

Verified after each build: no material code, material name or BOM quantity
appears anywhere in `site-data.js`. The nearest-family explanation, which names
the raw materials that differ, is also held inside the encrypted bundle.

## How the encryption works

- **Cipher:** AES-256-GCM (authenticated — tampering is detected).
- **Key derivation:** PBKDF2-HMAC-SHA256, **600,000 iterations**, 16-byte random
  salt (OWASP 2023 guidance).
- **Password:** 20 characters, ~116 bits of entropy, from a CSPRNG.
- **Where decryption happens:** in the browser (Web Crypto API). The password is
  never transmitted and never stored on the site; within a session it is held in
  `sessionStorage` and cleared when the tab closes.

## Keys, and where they live

| Secret | Where it is kept | Never |
|---|---|---|
| QA / BOM password | `config/bom_key.txt` (git-ignored, mode 600) — and as `QA_PASSWORD` in Apps Script | in the repository, or in the same message as the link |
| View-only BOM password | `config/bom_viewer_key.txt` (git-ignored, mode 600) | anywhere else |
| RA / QA passwords | Apps Script Script Properties | in the repository |
| Apps Script token | `config/local_settings.json` locally (git-ignored) + GitHub Actions secret | on the site at all |
| Gmail app password | GitHub Actions secret | anywhere else |

## Rotating the BOM password

If it leaks, or someone leaves:

```bash
python3 scripts/encrypt_bundle.py --new-viewer-key   # rotate the view-only one
python3 scripts/encrypt_bundle.py --new-qa-key       # rotate QA's
python3 scripts/refresh_site.py
cd dashboard-site && git add -A && git commit -m "Rotate BOM password" && git push
```

Each can be rotated on its own; the other keeps working. If you rotate QA's, set
the same new value as `QA_PASSWORD` in Apps Script → Script Properties, or QA
will be able to view but not add. The old password stops working as soon as the
new `site-bom.enc.js` is live.

## Residual risks — be aware of these

1. **Each BOM password is shared by its group, not per-person.** Revoking one
   person means rotating that group's password for everyone in it. The two
   groups are independent, so rotating the view-only password does not disturb
   QA. Send passwords separately from the link.
2. **Anyone who unlocks the BOM can copy what they see.** Encryption controls
   who gets in; it cannot stop an authorised viewer from taking data.
3. **The rest of the dashboard is open to anyone with the link** — product names,
   families, licence and permission numbers, and label claims. That is the
   current decision; say the word and the whole site can be put behind a
   passphrase as well.
4. **The data was published in plaintext before 31/07/2026.** `data.js` and
   `bom.js` were readable for roughly one day, and the history has since been
   rewritten. GitHub can retain unreferenced objects for a period, so for a
   guaranteed purge the repository should be deleted and recreated (see below).
5. **Access is not logged.** GitHub Pages does not record who downloaded the
   site. Writes *are* logged, in the AuditLog tab.

## Recommended: delete and recreate the repository

To eliminate risk 4 entirely:

1. Repository **Settings → Danger Zone → Delete this repository**.
2. Create it again with the same name, **Private** if you prefer (note: GitHub
   Pages needs a public repository on the free plan).
3. Tell me, and I will push the encrypted site again and re-enable Pages.

Everything published from that point contains no readable data.
