# Report: Updated Analysis of Indicators of Compromise (IOCs) Attributed to APT42

## 1. Executive Summary
This report updates the analysis of Indicators of Compromise (IOCs) for the **APT42** threat group based on new source material. While specific technical artifacts such as IP addresses and domain names were previously absent from the provided documents, this update identifies two primary custom backdoors (**NICECURL** and **TAMECAT**) attributed to APT42, along with associated infrastructure, file hashes, and operational tactics. The group remains identified as Iranian government-backed (IRGC-IO), utilizing a mix of credential harvesting and specialized malware deployment against high-value geopolitical targets.

## 2. Technical Indicators of Compromise (IOCs)
The following specific technical artifacts have been attributed to APT42 in the provided sources:

### 2.1 Malware Family: NICECURL
APT42 utilizes **NICECURL**, a VBScript-based backdoor that functions as a command execution interface and a jumping point for deploying additional malware.
*   **Functionality:** Communicates over HTTPS to execute commands such as "kill" (remove artifacts), "SetNewConfig" (set sleep values), and "Module" (download/execute files) [3].
*   **Delivery Vectors:** Distributed via malicious Windows Shortcut (.lnk) files masquerading as benign documents or forms. Example filenames include `onedrive-form.pdf.lnk` and `kuzen.vbs` [3].
*   **C2 Infrastructure & Domains:**
    *   Primary C2 URL: `prism-west-candy.glitch.me` [3].
    *   Secondary download target: `tnt200.mywire.org/Do1` [3].
    *   Lure domain observed: `drive-file-share.site/OneDrive-Form.pdf.lnk` [3].
*   **File Hashes (MD5):**
    *   `d5a05212f5931d50bb024567a2873642` (Linked to `onedrive-form.pdf.lnk`) [3].
    *   `347b273df245f5e1fcbef32f5b836f1d` (Linked to `kuzen.vbs`) [3].
    *   `2f6bf8586ed0a87ef3d156124de32757` (Decoy file `question-Em.pdf`) [3].
    *   `13aa118181ac6a202f0a64c0c7a61ce7` (Encrypted RAR file) [3].
    *   `c23663ebdfbc340457201dbec7469386` (Cited in YARA rule `M_APT_Backdoor_NICECURL`) [3].
    *   `853687659483d215309941dae391a68f` [3].

### 2.2 Malware Family: TAMECAT
APT42 utilizes **TAMECAT**, a PowerShell-based "toehold" capable of executing arbitrary PowerShell or C# content, serving as a jumping point for further malware deployment.
*   **Functionality:** Communicates via HTTP with Base64 encoded data; encrypts data using AES.
    *   **AES Key:** `kNz0CXiP0wEQnhZXYbvraigXvRVYHk1B` [3].
    *   **Initialization Vector (IV):** Derived from the string `ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz` with a randomly generated 16-character IV [3].
*   **Delivery Vectors:** Typically delivered via malicious macro documents [3].
*   **C2 Infrastructure & Domains:**
    *   Primary C2 Domain: `accurate-sprout-porpoise.glitch.me` [3].
    *   Secondary C2 Domain (Operation 1): `worried-eastern-salto.glitch.me` [3].
*   **File Hashes (MD5):**
    *   `d7bf138d1aa2b70d6204a2f3c3bc72a7` (File: `a2.vbs`, the VBScript downloader) [3].
    *   `081419a484bbf99f278ce636d445b9d8` (File: `nconf.txt`, contains obfuscated AES-encrypted TAMECAT backdoor) [3].
    *   `c3b9191f3a3c139ae886c0840709865e` (Decoded payload script `df32s.txt`) [3].
    *   `dd2653a2543fa44eaeeff3ca82fe3513` [3].
    *   `9c5337e0b1aef2657948fd5e82bdb4c3` [3].
*   **Execution Environment:**
    *   Utilizes Windows Management Instrumentation (WMI) [3].
    *   Leverages `conhost` when executing PowerShell commands [3].
    *   Uses `cmd.exe` and `Curl` in other scenarios [3].
    *   Writes a likely victim identifier to `%LOCALAPPDATA%\config.txt` [3].

### 2.3 Credential Harvesting Infrastructure (Typosquatting & Phishing)
APT42 employs distinct clusters of infrastructure for credential harvesting, often masquerading as legitimate news outlets or generic login pages.

*   **Cluster A: News Outlets and NGOs**
    *   **Masquerade:** Targets include The Washington Post, The Economist, The Jerusalem Post, Khaleej Times, Azadliq [3].
    *   **Observed Domains:** `azadlliq.info`, `businesslnsider.org`, `foreiqnaffairs.com`, `ecomonist.org`, `israelhayum.com`, `khaleejtimes.org` [3].
    *   **Typosquatting Example:** `washin**q**tonpost.press` [3].

*   **Cluster B: Legitimate Services & Generic Login Pages**
    *   **Masquerade:** Mimics Google, Yahoo, Microsoft 365, Hotmail, Dropbox, YouTube [3].
    *   **TLDs:** `.top`, `.online`, `.site`, `.live` with hyphenated multi-word names (e.g., `panel-live-check.online`) [3].
    *   **Observed Domains:** `review.modification-check.online`, `nterview.site`, `shortlinkview.live`, `reconsider.site`, `ksview.top`, `mterview.site` [3].

*   **Cluster C: URL Shorteners & Mailer Daemon**
    *   **URL Shorteners:**
        *   `n9.cl` (Used in Nov-Dec 2023 campaigns) [3].
        *   Bitly (`bitly.org.il`) and YouTransfer (`youtransfer.live`) used for ICT-2023 lures [3].
        *   Generic shorteners: `ovcloud.online`, `panel-check-short.live`, `shortlinkview.live`, `reconsider.site` [3].
    *   **Mailer Daemon Domains:** `email-daemon.online`, `mailer-daemon.us`, `daemon-mailer.co` [3].

### 2.4 Post-Exploitation Indicators
Following credential harvesting, APT42 targets Microsoft 365 environments to exfiltrate data.
*   **Tools & Commands:**
    *   Access achieved via **Thunderbird** by altering user permissions [3].
    *   Uses **Citrix** applications and **Windows Remote Desktop Protocol (RDP)** [3].
    *   Reconnaissance commands: `whoami`, `net view`, `cd`, `explorer`, `net share`, `hostname`, `ls`, `type`, `ping`, `net user`, `gci`, `mkdir`, `notepad`, `mv`, `exit`, `rm`, `dir`, `del` [3].
    *   PowerShell Automation: Uses cmdlets including `set-ExecutionPolicy`, `Import-Module`, and `Invoke-HuntSMBShares` (from the open-source tooling module **PowerHuntShares**) to identify users with excessive network share permissions [3].
*   **Defense Evasion:**
    *   Clears Google Chrome browser history after reviewing documents of interest [3].
    *   Uses ephemeral VPS servers and ExpressVPN nodes for anonymity [3].
    *   Bypasses MFA by serving cloned websites to capture MFA tokens or sending MFA push notifications to the victim [3].

## 3. Operational Context and Attribution
*   **Affiliation:** Operates on behalf of the **Islamic Revolutionary Guard Corps Intelligence Organization (IRGC-IO)** with moderate confidence [3].
*   **Aliases:** Partially coincides with public reporting on threat clusters including TA453 (Bad Blood), Yellow Garuda, ITG18, Phosphorus, and Charming Kitten [3].
*   **Front Companies:** Mandiant assesses with moderate confidence that the IRGC-IO uses at least two front companies: **Najee Technology** and **Afkar System** [3].
*   **Revengers Persona:** Linked to Ahmad Khatibi and associated with the Lab Dookhtegan Telegram account. This persona offered data and access primarily to Israeli companies for sale on Telegram between February and September 2021 [3].
*   **Targeting Patterns:**
    *   Primary Targets: Western think tanks, researchers, journalists, current/former government officials (Iranian and Western), and the Iranian diaspora [3].
    *   Geographic Focus: Primarily the Middle East region [3].
    *   Evolution of Targets: Shifted focus to the pharmaceutical sector in March 2020; targeted opposition groups prior to Iranian presidential elections [3].

## 4. Clarification on Previously Reported Tools (Non-APT42)
The previous sources mentioned several other tools and actors that were **not** attributed to APT42 in the provided text:
*   **Gemini Usage:** While APT42 utilizes Google's Gemini model for engineering and reconnaissance, specific technical IOCs related to the "Data Processing Agent" or general Gemini usage were found associated with other actors (UNC1069/MASAN, UNC4899/PUKCHONG) in the initial document set.
*   **PROMPTSTEAL:** This malware family is attributed to **APT28/FROZENLAKE**, not APT42 [3].
*   **OSSTUN:** This C2 framework tool was observed with **APT41**, not APT42 [3].
*   **UNC2448 (Phosphorus):** While Microsoft reported a connection between APT42 activity clusters and UNC2448, Mandiant states it has **not observed technical overlaps** between the two groups [3].

## 5. References
1. https://cloud.google.com/blog/topics/threat-intelligence/threat-actor-usage-of-ai-tools
2. https://cloud.google.com/blog/topics/threat-intelligence/distillation-experimentation-integration-ai-adversarial-use
3. https://cloud.google.com/blog/topics/threat-intelligence/apt42-charms-cons-compromises
4. https://cloud.google.com/blog/topics/threat-intelligence/untangling-iran-apt42-operations

---
*Report generated on Monday, Mar 16, 2026 | 12:34 UTC*