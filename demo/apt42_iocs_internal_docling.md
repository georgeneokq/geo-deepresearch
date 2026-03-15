# APT42 Indicators of Compromise (IOCs) Report

## Executive Summary

This report compiles technical indicators of compromise (IOCs) associated with the Advanced Persistent Threat group known as APT42, based on recent activity analysis published in May 2024 [1].

## Malware Backdoors and Technical IOCs

APT42 employs custom backdoors designed for data exfiltration and command execution capabilities [1]. These tools are typically delivered via spear-phishing campaigns targeting NGOs and government entities [1].

### NICECURL (VBScript Backdoor)

**Description:** NICECURL is a backdoor written in VBScript that can download additional modules to be executed, including data mining and arbitrary command execution [1]. It communicates over HTTPS with Command & Control servers [1].

**Commands:**
- `kill` - Removes artifacts and ends execution [1]
- `SetNewConfig` - Sets sleep value configuration [1]
- `Module` - Downloads and executes files [1]

**SHA256 Hash Indicators of Compromise:**
- `3c74109005111688341f4e5fcba42be9c21baa4465f5f84a5a342708732ac0ff` [1]
- `e0ba0cedd8a8624c75af29965e5fa7ab754fc0fcddbb330bb548dab4f2be333f` [1]
- `0e51029ba28243b0a6a071713c17357a8eb024aa4298d1ccc9e2c4ac8916df4d` [1]
- `3226b3e7d7fdaebfe7d7f06bdaf0cad08ea9792cd32843d01e6023f67cd0c889` [1]
- `dbdb14e37fc4412711a1e5e37e609e33410de31de13911aee99ab473753baa4a` [1]
- `07384ab4488ea795affc923851e00ebc2ead3f01b57be6bf8358d7659e9ee407` [1]

### TAMECAT (PowerShell Backdoor)

**Description:** TAMECAT is a PowerShell toehold that can execute arbitrary PowerShell or C# content. It communicates with Command & Control via HTTP using Base64 encoded data [1]. The backdoor is dropped by malicious macro documents during spear-phishing campaigns [1].

**SHA256 Hash Indicators of Compromise:**
- `5404e39f2f175a0fc993513ee52be3679a64c69c79e32caa656fbb7645965422` [1]
- `bd1f0fb085c486e97d82b6e8acb3977497c59c3ac79f973f96c395e7f0ca97f8` [1]
- `156ac9685acb6696d8d7f64205e20ecf7a87dad304b8441449f0060ed175938b` [1]
- `c99cc10f15f655f36314e54f7013a0bc5df85f4d6ff7f35b14a446315835d334` [1]

**MD5 Hash Indicator of Compromise:**
- `9c5337e0b1aef2657948fd5e82bdb4c3` (TAMECAT) [1]

## Domain Indicators of Compromise

APT42 utilizes domain impersonation tactics to deceive targets, including news outlet mimics, legitimate service impersonation, and URL shortening services [1].

### News Outlet Impersonation Domains
The group has employed typo squatting techniques to create domains resembling well-known news outlets since 2021 [1]:
- `azadlliq.info` [1]
- `businesslnsider.org` [1]
- `ecomonist.org` [1]
- `eocnomist.com` [1]
- `foreiqnaffairs.com` [1]
- `forieqnaffairs.com` [1]

Additional news-related domains observed include:
- `israelhayum.com` [1]
- `jpost.press` [1]
- `jpostpress.com` [1]
- `khaleejtimes.org` [1]
- `maariv.net` [1]
- `themedealine.org` [1]
- `timesfisrael.com` [1]
- `vanityfaire.org` [1]
- `washinqtonpost.press` [1]
- `ynetnews.press` [1]

### Legitimate Service Impersonation Domains
APT42 uses domains to impersonate legitimate services including account sign-in portals:
- `acconut-signin.com` [1]
- `accounts-mails.com` [1]
- `coordinate.icu` [1]
- `dloffice.top` [1]
- `dloffice.buzz` [1]
- `myaccount-signin.com` [1]
- `signin-acconut.com` [1]
- `signin-accounts.com` [1]
- `signin-mail.com` [1]
- `signin-mails.com` [1]
- `signin-myaccounts.com` [1]
- `accredit-validity.online` [1]

**Generic Login Services:**
- `activity-permission.online` [1]
- `admin-stable-right.top` [1]
- `admiscion.online` [1]
- `admit-roar-frame.top` [1]
- `advission.online` [1]
- `affect-fist-ton.online` [1]
- `avid-striking-eagerness.online` [1]
- `beaviews.online` [1]
- `besvision.top` [1]
- `bloom-flatter-affably.top` [1]

**Miscellaneous Services:**
- `book-download.shop` [1]
- `bq-ledmagic.online` [1]
- `briview.online` [1]
- `chat-services.online` [1]
- `check-online-panel.live` [1]
- `drive-access.site` [1]
- `endorsement-services.online` [1]

### URL Shortening and Generic Services Domains
APT42 employs various URL shortening services alongside generic domain services:
- `m85.online` [1]
- `s51.online` [1]
- `s59.site` [1]
- `s20.site` [1]
- `d75.site` [1]
- `bitly.org.il` [1]
- `litby.us` [1]
- `daemo-mailer.co` [1]

**Miscellaneous/Other Domains:**
- `aspenlnstitute.org` [1]
- `mccainlnstitute.org` [1]
- `washingtonlnstitute.org` [1]
- `youtransfer.live` [1]
- `g-online.org` [1]

## References and Citations

| # | Citation Source | File Name |
|---|----------------|-----------|
| 1 | Internal documents - APT42s recent activity.pdf | https://internal/docs/ |

## Notes on Data Completeness

The provided source material appears truncated at the end of the SHA256 Hash table for NICECURL. The text ends abruptly with: `| 3c74109005111688341f4e5fcba42be9c21baa4465f5f84a5a342708732ac0ff | NICE`. It is possible that further IOCs or descriptions for "NICE" were intended but missing due to truncation [1].

## Summary Statistics

- **Total Malware Backdoors Identified:** 2 (NICECURL, TAMECAT)
- **SHA256 Hashes Available:** 13 (combined)
- **MD5 Hashes Available:** 1 (TAMECAT)
- **Domain IOCs Listed:** 41+ unique domain names across news, service impersonation, and URL shortening categories

---

*Report generated on: Sunday, Mar 15, 2026 | 16:37 UTC*
*Data Source: APT42s recent activity.pdf - Original report published May 02, 2024: 'UNCHARMED: UNTANGLING IRAN'S APT42 OPERATIONS' [1]*
