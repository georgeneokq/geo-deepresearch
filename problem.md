### IOCs Found:
- **Malware (NICECURL):** `e0ba0cedd8a8624c75af29965e5fa7ab754fc0fcddbb330bb548dab4f2be333f` (SHA256) [1], [2], [3]
- **Malware (TAMECAT):** `0e51029ba28243b0a6a071713c17357a8eb024aa4298d1ccc9e2c4ac8916df4d` (SHA256) [1], [2], [3]
- **Malware (TAMECAT):** `9c5337e0b1aef2657948fd5e82bdb4c3` (MD5) [1], [2], [3]
- **Phishing Domain (News Outlet):** `jpost.press`, `jpostpress.com` [1], [2], [3]
- **Phishing Domain (News Outlet):** `foreiqnaffairs.com`, `foreiqnaffairs.org` [1], [2], [3]
- **Phishing Domain (Generic Login):** `signin-acconut.com`, `acconut-signin.com` [1], [2], [3]
- **Phishing Domain (Think Tank):** `washingtonlnstitute.org` [1], [2], [3]

### References:
1. Internal docs - APT42s recent activity.pdf
2. Internal docs - APT42s recent activity.pdf
3. Internal docs - APT42s recent activity.pdf

---

### Updated Summary: Historical cyber incidents and attack campaigns attributed to APT42 (Cozy Bear) from 2015 to 2026

**Overview & Attribution:**
APT42 (also known as Cozy Bear) is an Iranian state-sponsored cyber espionage group. According to recent technical advisories (specifically the "UNCHARMED" advisory published in May 2024), the group has maintained a focus on intelligence gathering rather than direct disruption or ransomware deployment. Their primary objective involves obtaining credentials and strategic information through sophisticated social engineering and custom backdoors [1], [2], [3].

**Operational Timeline & Data Availability:**
*   **2021–Present:** The available data confirms sustained activity since 2021, with specific major campaigns observed in 2024. The group shifted tactics around this time to impersonate well-known news outlets and think tanks using "typo squatting" [1], [2], [3].
*   **2015–2020:** The retrieved internal documents explicitly state that the provided text is heavily truncated and focuses almost exclusively on activity observed since 2021. There is a significant lack of specific historical details regarding incidents from 2015–2020 in the current source material. While the group is known to be active during this period, the specific case studies, campaign names, and victim lists for the 2015–2020 period are not detailed in the provided excerpts [1], [2], [3].

**Modus Operandi (2021–Present):**
*   **Impersonation & Typo Squatting:** APT42 creates web domains closely resembling legitimate news outlets (e.g., *jpost*, *washingtonpost*, *theatlantic*) and think tanks (e.g., *washingtonlnstitute.org*) with minor spelling alterations to trick users [1], [2], [3].
*   **Social Engineering:** The group builds trust by impersonating journalists and event organizers, sending realistic conference invitations or documents to gather credentials and access cloud environments [1], [2], [3].
*   **Target Audience:** Western and Middle Eastern media companies, NGOs, academia, legal services, and activist groups [1], [2], [3].

**Malware & Tools:**
*   **NICECURL:** A VBScript backdoor used to download additional modules (data mining, command execution). It communicates over HTTPS and accepts commands like `kill` (remove artifacts) and `Module` [1], [2], [3].
*   **TAMECAT:** A PowerShell "toehold" dropped via malicious macro documents. It executes arbitrary PowerShell/C# content and communicates via HTTP, expecting Base64-encoded data from its C2 node [1], [2], [3].
*   **Exfiltration:** Data is discreetly exfiltrated using built-in features and open-source tools to evade detection [1], [2], [3].

**MITRE ATT&CK Alignment:**
*   **Initial Access:** Spearphishing Attachment (T1566.001), Spearphishing Link (T1566.002) [1], [2], [3].
*   **Execution:** Command and Scripting Interpreter: PowerShell (T1059.001), JavaScript (T1059.007) [1], [2], [3].
*   **Persistence:** Account Manipulation: Device Registration (T1098.005) [1], [2], [3].
*   **Defense Evasion:** Obfuscated Files or Information (T1027), Indicator Removal: File Deletion (T1070) [1], [2], [3].
*   **Discovery:** File and Directory Discovery (T1083) [1], [2], [3].
*   **Collection:** Data from Local System (T1005) [1], [2], [3].
*   **Exfiltration:** Exfiltration Over C2 Channel (T1041) [1], [2], [3].

**Indicators of Compromise (IoCs):**
*   **Malware Hashes:** SHA256 hashes for NICECURL and TAMECAT variants have been identified, including `e0ba0cedd8a8624c75af29965e5fa7ab754fc0fcddbb330bb548dab4f2be333f` (NICECURL) and `0e51029ba28243b0a6a071713c17357a8eb024aa4298d1ccc9e2c4ac8916df4d` (TAMECAT) [1], [2], [3].
*   **Phishing Domains:** A vast array of domains are used, including news outlets (`azadlliq.info`, `businesslnsider.org`), generic login portals (`account-signin.com`, `acconut-signin.com`), and URL shorteners (`s51.online`, `bitly.org.il`) [1], [2], [3].

**Limitations:**
The current research is limited by the truncation of the source document. While it confirms APT42's methodology and recent (post-2021) campaigns, it does not provide a comprehensive historical timeline of incidents from 2015–2020 or specific campaign names for that earlier period [1], [2], [3].