# Security — how the confidential data is protected

The dashboard holds Enicar's complete formulation book (every raw material and
quantity for 1,907 products) plus licence and permission numbers. It is
published on GitHub Pages, which serves files to anyone with the link. So the
data itself is encrypted before it is ever published.

## Two levels of access

| | Who | Protected how |
|---|---|---|
| **Dashboard, families, licences, compositions** | anyone with the link | not protected — open by decision (31/07/2026) |
| **BOM — raw materials & quantities** | QA, Verma Sir, Swarali, Nimish | **BOM password**, AES-256-GCM encryption |
| **Adding licences** (RA) | RA | RA password, checked server-side |
| **Adding BOMs** (QA) | QA | QA password — the same secret as the BOM password |

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
| BOM password | `config/bom_key.txt` on the Director's Mac (git-ignored, mode 600) — and as `QA_PASSWORD` in Apps Script | in the repository, or in the same message as the link |
| RA / QA passwords | Apps Script Script Properties | in the repository |
| Apps Script token | `config/local_settings.json` locally (git-ignored) + GitHub Actions secret | on the site at all |
| Gmail app password | GitHub Actions secret | anywhere else |

## Rotating the BOM password

If it leaks, or someone leaves:

```bash
python3 scripts/encrypt_bundle.py --new-key   # prints the new BOM password
python3 scripts/refresh_site.py
cd dashboard-site && git add -A && git commit -m "Rotate vault key" && git push
```

Then set the same value as `QA_PASSWORD` in Apps Script → Script Properties, and
give it to the four people. The old password stops working as soon as the new
`site-bom.enc.js` is live.

## Residual risks — be aware of these

1. **The BOM password is shared, not per-person.** It cannot be revoked for one
   individual — rotation affects all four. Send it separately from the link.
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
