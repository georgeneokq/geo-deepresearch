# Report: Indicators of Compromise (IOCs) for APT42

## Executive Summary
This report details the Indicators of Compromise (IOCs) associated with the Advanced Persistent Threat group APT42, based on the analysis of internal documents regarding their recent activity. The identified IOCs are categorized into Malware Hashes, Malicious Domains, and MITRE ATT&CK techniques utilized during operations.

## 1. Malware Hashes
APT42 utilizes custom backdoors delivered primarily via spear-phishing campaigns. The following hashes have been identified in the source material:

### NICECURL (VBScript Backdoor)
*   **SHA256:** `3c74109005111688341f4e5fcba42be9c21baa4465f5f84a5a342708732ac0ff` [1]

### TAMECAT (PowerShell Toehold)
Multiple SHA256 hashes and one MD5 hash have been associated with the TAMECAT backdoor:
*   **SHA256:** `5404e39f2f175a0fc993513ee52be3679a64c69c79e32caa656fbb7645965422` [1]
*   **SHA256:** `bd1f0fb085c486e97d82b6e8acb3977497c59c3ac79f973f96c395e7f0ca97f8` [1]
*   **SHA256:** `156ac9685acb6696d8d7f64205e20ecf7a87dad304b8441449f0060ed175938b` [1]
*   **SHA256:** `c99cc10f15f655f36314e54f7013a0bc5df85f4d6ff7f35b14a446315835d334` [1]
*   **MD5:** `9c5337e0b1aef2657948fd5e82bdb4c3` [1]

## 2. Malicious Domains
APT42 employs typo-squatting and impersonation tactics to mimic news outlets, legitimate services, generic login portals, file-sharing services, and think tanks. The following domains were identified in the source material:

### Impersonating News Outlets
*   `azadlliq.info` [1]
*   `businesslnsider.org` [1]
*   `ecomonist.org` [1]
*   `eocnomist.com` [1]
*   `foreiqnaffairs.com` [1]
*   `forieqnaffairs.com` [1]
*   `foreiqnaffairs.org` [1]
*   `israelhayum.com` [1]
*   `jpost.press` [1]
*   `jpostpress.com` [1]
*   `khaleejtimes.org` [1]
*   `khalejtimes.org` [1]
*   `maariv.net` [1]
*   `themedealine.org` [1]
*   `timesfisrael.com` [1]
*   `vanityfaire.org` [1]
*   `washinqtonpost.press` [1]
*   `ynetnews.press` [1]

### Posing as Legitimate Services (Login/Account Portals)
*   `account-signin.com` [1]
*   `acconut-signin.com` [1]
*   `accounts-mails.com` [1]
*   `coordinate.icu` [1]
*   `dloffice.top` [1]
*   `dloffice.buzz` [1]
*   `myaccount-signin.com` [1]
*   `signin-acconut.com` [1]
*   `signin-accounts.com` [1]
*   `signin-mail.com` [1]
*   `signin-mails.com` [1]
*   `signin-myaccounts.com` [1]

### URL Shortening Services
*   `m85.online` [1]
*   `s51.online` [1]
*   `s59.site` [1]
*   `s20.site` [1]
*   `d75.site` [1]
*   `bitly.org.il` [1]
*   `litby.us` [1]

### Email/Mailer Services
*   `daemon-mailer.co` [1]
*   `daemon-mailer.info` [1]
*   `email-daemon.biz` [1]
*   `email-daemon.biz.tinurls.com` [1]
*   `email-daemon.online.tinurls.com` [1]
*   `email-daemon.online` [1]
*   `email-daemon.site` [1]
*   `mailer-daemon.info` [1]
*   `mailerdaemon.online` [1]
*   `mailerdaemon.us` [1]

### Miscellaneous and Other Impersonations
*   `aspenlnstitute.org` (Posing as Think Tanks) [1]
*   `mccainlnstitute.org` (Posing as Think Tanks) [1]
*   `washingtonlnstitute.org` (Posing as Think Tanks) [1]
*   `youtransfer.live` (File Sharing Services) [1]
*   `g-online.org` [1]
*   `online-access.live` [1]
*   `yoronlineregister.com` [1]

## 3. MITRE ATT&CK Techniques
The following tactics and techniques have been associated with APT42 operations based on the source document:

| Tactic | Technique ID | Technique Name |
| :--- | :--- | :--- |
| Initial Access | T1566.001 | Phishing: Spearphishing Attachment [1] |
| Initial Access | T1566.002 | Phishing: Spearphishing Link [1] |
| Execution | T1059.001 | Command and Scripting Interpreter: PowerShell [1] |
| Execution | T1059.007 | Command and Scripting Interpreter: JavaScript [1] |
| Persistence | T1098.005 | Account Manipulation: Device Registration [1] |
| Defense Evasion | T1027 | Obfuscated Files or Information [1] |
| Defense Evasion | T1070 | Indicator Removal: File Deletion [1] |
| Discovery | T1083 | File and Directory Discovery [1] |
| Collection | T1005 | Data from Local System [1] |
| Exfiltration | T1041 | Exfiltration Over C2 Channel [1] |

## References
1. Internal docs - APT42s recent activity.pdf