## Key Differences

### 1. **NICECURL SHA256 Hashes**
- **docling.md**: Lists **6 SHA256 hashes** for NICECURL
- **naive.md**: Lists only **1 SHA256 hash** for NICECURL (`e0ba0cedd8a8624c75af29965e5fa7ab754fc0fcddbb330bb548dab4f2be333f`)

**Missing from naive.md:**
- `3c74109005111688341f4e5fcba42be9c21baa4465f5f84a5a342708732ac0ff`
- `0e51029ba28243b0a6a071713c17357a8eb024aa4298d1ccc9e2c4ac8916df4d`
- `3226b3e7d7fdaebfe7d7f06bdaf0cad08ea9792cd32843d01e6023f67cd0c889`
- `dbdb14e37fc4412711a1e5e37e609e33410de31de13911aee99ab473753baa4a`
- `07384ab4488ea795affc923851e00ebc2ead3f01b57be6bf8358d7659e9ee407`

### 2. **TAMECAT SHA256 Hashes**
- **docling.md**: Lists **4 SHA256 hashes** for TAMECAT
- **naive.md**: Lists only **3 SHA256 hashes** for TAMECAT

**Missing from naive.md:**
- `5404e39f2f175a0fc993513ee52be3679a64c69c79e32caa656fbb7645965422`

### 3. **Domain IOCs**
**docling.md** contains significantly more domains (~41+ domains) while **naive.md** has a truncated/shorter list:

**Notable domains in docling.md but missing from naive.md:**
- `eocnomist.com`, `foreiqnaffairs.com`, `forieqnaffairs.com`
- `khaleejtimes.org`, `maariv.net`, `themedealine.org`, `timesfisrael.com`, `vanityfaire.org`
- `washinqtonpost.press`, `ynetnews.press`
- Most "Generic Login Services" domains (e.g., `activity-permission.online`, `advission.online`, etc.)
- Most "Miscellaneous Services" domains (e.g., `book-download.shop`, `drive-access.site`, etc.)
- URL shortening domains: `s59.site`, `s20.site`, `d75.site`, `litby.us`, `daemo-mailer.co`
- `g-online.org`, `youtransfer.live`

**Unique to naive.md:**
- `foreiqnaffairs.org` (not in docling.md)
- `account-signin.com` (not in docling.md)
- `check-pabnel-status.live`, `panel-view.live` (not in docling.md)

### 4. **Additional Content in naive.md**
- **MITRE ATT&CK mapping table** (10 techniques) - completely absent from docling.md
- More structured operational context section

### 5. **Formatting Differences**
- **docling.md**: More complete statistics summary, notes on data truncation
- **naive.md**: Appears truncated in places (e.g., `"verification..." [1]`)

## Summary
The **docling.md** document is more comprehensive for IOC hashes and domain lists, while **naive.md** includes MITRE ATT&CK mappings that docling.md lacks. Neither appears to be complete.
