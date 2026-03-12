# Past incidents of APT42

## Detailed historical campaigns and incidents attributed to APT42, including specific dates, targets, and objectives.

### Summary
APT42 (also known as **Crooked Charms**) is an Iranian state-sponsored threat actor active since at least 2012. The group focuses on cyber espionage and targets dissidents, journalists, academics, government officials, civil society, healthcare/pharma, think tanks, and the Iranian diaspora in the US, UK, and Israel [1][2]. They utilize sophisticated social engineering and advanced malware to infiltrate networks and exfiltrate sensitive information [1][2]. The targeted sectors include Media & Journalism, Academia & Research, Government & Policy, Defense & Foreign Affairs, NGOs & Activism, and Legal Services [10]. Specific victims include freelance journalists, news editors, nuclear physics professors, individuals perceived as threats to the Iranian regime (such as human rights activists, women's rights activists, and NGO leaders), Western think tank researchers and personnel, and individuals affiliated with defense, foreign affairs, and academic issues in the U.S. and Israel [10, 13]. The group also targets current Western government officials (specifically from the US, UK, and Israel), former Iranian government officials, the Iranian diaspora, activists, dissidents, opposition groups, Iranian dual-nationals, and foreign policy officials [13]. Industries targeted include the Pharmaceutical Sector, specifically at the onset of the COVID-19 pandemic [13]. Additionally, APT42 does not primarily focus on the defense industrial base, distinguishing it from other IRGC-affiliated groups [13]. In a specific campaign dubbed \"SpearSpecter,\" APT42 targeted senior defense and government officials, utilizing social engineering and targeting the victims' family members to increase pressure [13]. Specific US political targets include personnel and affiliates of the Kamala Harris and Donald Trump presidential campaigns, as well as affiliates of the Biden campaign and figures like Roger Stone, alongside current and former US government officials [14]. In Israel, targets include former senior Israeli military officials and individuals affiliated with the conflict [14].

### Historical Campaigns and Incidents

**TTPs (Tactics, Techniques, and Procedures):**
*   **Social Engineering:** APT42 poses as journalists and event organizers to build trust through ongoing correspondence and deliver invitations or documents [1].
*   **Credential Harvesting:** They use tailored spear-phishing campaigns to harvest credentials for Microsoft, Yahoo, and Google via fake login pages. The group specifically targets Multi-Factor Authentication (MFA) by capturing SMS-based one-time passwords and registering the Microsoft Authenticator application to their own devices [1][2]. They also use custom malware to steal login and cookie data from common browsers [2].
*   **Lateral Movement:** Once inside a victim's personal email, APT42 uses those credentials to access corporate accounts. They often send follow-on spear-phishing emails from compromised accounts to target colleagues, relatives, and associates [2].
*   **Cloud Operations (Microsoft 365):**
    *   **Initial Access:** Bypasses MFA using fake DUO pages, SMS tokens, or MFA push notifications [1].
    *   **Persistence:** Exploits the Microsoft \"App Password\" feature to maintain access without re-authentication. They also establish persistence via scheduled tasks and Windows registry modifications [1][2].
    *   **Exfiltration:** Uses Thunderbird, Citrix, and Windows RDP to search and steal files. They also utilize tools like GHAMBAR and POWERPOST to collect data [1][2].
*   **Execution:** Relies on PowerShell, VBScript, and Scheduled Tasks [2].
*   **Privilege Escalation:** Utilizes custom malware capable of keylogging and stealing browser cookies (e.g., CHAIRSMACK) [2].
*   **Reconnaissance:** Uses native Windows commands (`whoami`, `net view`). They also use malware, such as GHAMBAR and POWERPOST, to take screenshots and collect system and network information [2].
*   **Defense Evasion:** Relies on built-in Microsoft 365 features and open-source tools to blend in; clears Google Chrome history and utilizes anonymized infrastructure (ExpressVPN, Cloudflare). To evade detection, they delete login notification emails and messages from the Sent folder, as well as clear browser history and mailbox data [1][2].

**Malware Families:**
*   **Android Malware:**
    *   **PINEFLOWER:** Delivered via SMS. Capabilities include recording phone calls and audio, reading SMS inboxes, taking photos, and tracking GPS location [2].
    *   **VINETHORN:** Delivered via a fake VPN application. Capabilities include location tracking, audio/video recording, and contact list access [2].
*   **Windows Malware:**
    *   **CHAIRSMACK:** A C++ backdoor that retrieves plugins for shell execution, screenshot capture, and keylogging [2].
    *   **GHAMBAR:** A Remote Administration Tool (RAT) using SOAP over HTTP for C2. Capabilities include file manipulation, keylogging, and clipboard monitoring [2].
    *   **TABBYCAT:** A Microsoft Word VBA macro dropper that executes PowerShell payloads [2].
    *   **TAMECAT:** A PowerShell toehold that executes arbitrary C# or PowerShell code, communicating with C2 via HTTP and expecting Base64-encoded data [2].
    *   **BROKEYOLK:** A .NET downloader that fetches payloads via HTTP/SOAP [2].
    *   **DOSTEALER:** A dataminer for browser login/cookie data and screenshots; acts as a dropper for SILENTUPLOADER [2].
    *   **SILENTUPLOADER:** An MSIL uploader dropped by DOSTEALER that monitors a folder every 30 seconds to upload files to a remote server [2].
    *   **VBREVSHELL:** A VBA macro that spawns a reverse shell using Windows API calls [2].
    *   **POWERPOST:** A PowerShell reconnaissance tool that collects local host data (system info, user accounts) and exfiltrates it to a hardcoded server via HTTP POST [2].
    *   **NICECURL:** Used for C2 communication [3].

**Infrastructure and Targets:**
*   **Infrastructure:**
    *   **Domains:** Registered domains that masquerade as news outlets, legitimate login services, typo-squatted domains, and fake Google sites [3].
    *   **Hosting:** Hosts malicious documents on AWS, Google Drive, and Dropbox. Uses fake websites for credential harvesting and C2 servers for malware control. Utilizes compromised email accounts for follow-on operations and anonymized infrastructure and Virtual Private Servers (VPSs) [2][3].
*   **Targets:** Dissidents, journalists, academics, government officials, civil society, healthcare/pharma, think tanks, media organizations, and the Iranian diaspora in the US, UK, and Israel [2].

### IOCs
*   prism-west-candy[.]glitch[.]me
*   worried-eastern-salto[.]glitch[.]me
*   accurate-sprout-porpoise[.]glitch[.]me
*   **VINETHORN**
    *   MD5: 8a847b0f466b3174741aac734989aa73
    *   SHA1: 03eadb4ab93a1a0232cb40b7d2ef179a1cd0174d
    *   SHA256: 5d3ff202f20af915863eee45916412a271bae1ea3a0e20988309c16723ce4da5
*   **POWERPOST**
    *   MD5: 96444ed552ea5588dffca6a5a05298e9
    *   SHA1: b66ae149bbdfc7ec6875f59ec9f4a5ae1756f8ba
    *   SHA256: 9410963ede9702e7b74b4057fee952250ded09f85a4bb477d45a64f2352ec811
*   **SILENTUPLOADER**
    *   MD5: 9dd30569aaf57d6115e1d181b78df6b5
    *   SHA1: 280b64c0156f101eaad3f31dbe91f0c1137627dc
    *   SHA256: 9f2bc9aebb3ee87cfbdef1716b5f67834db305cf400b41b278d5458800c5eeeb
*   **TABBYCAT**
    *   MD5: bdf188b3d0939ec837987b4936b19570
    *   SHA1: aba938bf8dc5445df3d5b77a42db4d6643db4383
    *   SHA256: 28de2ccff30a4f198670b66b6f9a0ce5f5f9b7f889c2f5e6a4e365dea1c89d53
*   **TAMECAT**
    *   MD5: 88df70a0e21fb48e0f881fb91a2eaade
    *   SHA1: e8f50ecea1a986b4f8b00836f7f00968a6ecba4f
    *   SHA256: c1664df788f690fd061994ed3eb9d767e2f293448ce9d7ff5bff37549e9e4dab
*   **VBREVSHELL**
    *   MD5: bdf188b3d0939ec837987b4936b19570
    *   SHA1: aba938bf8dc5445df3d5b77a42db4d6643db4383
    *   SHA256: 28de2ccff30a4f198670b66b6f9a0ce5f5f9b7f889c2f5e6a4e365dea1c89d53
*   **DOSTEALER**
    *   MD5: 0a3f454f94ef0f723ac6a4ad3f5bdf01
    *   SHA1: d08982960d71a101b87b1896fd841433b66c7262
    *   SHA256: 6618051ea0c45d667c9d9594d676bc1f4adadd8cb30e0138489fee05ce91a9cb

### References
1. https://cloud.google.com/blog/topics/threat-intelligence/clustering-and-associating-attacker-activity-at-scale
2. https://services.google.com/fh/files/misc/apt42-crooked-charms-cons-and-compromises.pdf
3. https://attack.mitre.org/groups/G1044/
4. https://cloud.google.com/security/resources/insights/apt-groups
5. https://www.picussecurity.com/resource/blog/apt41-cyber-attacks-history-operations-and-full-ttp-analysis
6. https://www.resecurity.com/blog/article/apt-41-threat-intelligence-report-and-malware-analysis
7. https://www.hhs.gov/sites/default/files/apt41-recent-activity.pdf
8. https://www.cybersecuritydive.com/news/state-linked-actors-targeted-us-networks-in-lead-up-to-iran-war/814190/
9. https://hivepro.com/threat-advisory/apt41-cyber-espionage-campaign-targets-u-s-policy-institutions/
10. https://cloud.google.com/blog/topics/threat-intelligence/untangling-iran-apt42-operations
11. https://cloud.google.com/security/resources/insights/apt-groups
12. https://cloud.google.com/blog/topics/threat-intelligence/apt42-charms-cons-compromises
13. https://www.securityweek.com/iranian-hackers-target-defense-and-government-officials-in-ongoing-campaign/
14. https://www.cybersecurityintelligence.com/blog/apt42-iranian-hackers-at-work-7870.html
15. https://thehackernews.com/2024/05/apt42-hackers-pose-as-journalists-to.html