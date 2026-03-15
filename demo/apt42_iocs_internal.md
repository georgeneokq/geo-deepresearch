# Indicators of Compromise (IOCs) for APT42

This report summarizes indicators of compromise (IOCs) associated with the Advanced Persistent Threat group APT42, based on internal advisory documentation. The information focuses on identified malware hashes, domain names, and operational techniques utilized during recent activity.

## Malware IOCs
APT42 operations are associated with custom backdoors and trojans deployed via spear-phishing mechanisms. Specific hashes have been documented in the provided sources.

### NICECURL Backdoor
NICECURL is identified as a VBScript-based backdoor capable of downloading additional modules for execution, including data mining and command execution capabilities. It communicates over HTTPS to download files and accepts commands such as "kill", "SetNewConfig", and "Module".
*   **SHA256:** `e0ba0cedd8a8624c75af29965e5fa7ab754fc0fcddbb330bb548dab4f2be333f` [1]

### TAMECAT Toehold
TAMECAT is identified as a PowerShell Toehold designed to execute arbitrary PowerShell or C# content. It is typically dropped by malicious macro documents and communicates with command-and-control (C2) infrastructure via HTTP using Base64 encoded data.
*   **SHA256 Hashes:**
    *   `bd1f0fb085c486e97d82b6e8acb3977497c59c3ac79f973f96c395e7f0ca97f8` [1]
    *   `156ac9685acb6696d8d7f64205e20ecf7a87dad304b8441449f0060ed175938b` [1]
    *   `c99cc10f15f655f36314e54f7013a0bc5df85f4d6ff7f35b14a446315835d334` [1]
*   **MD5 Hash:** `9c5337e0b1aef2657948fd5e82bdb4c3` [1]

## Domain IOCs
APT42 employs typo-squatting and impersonation techniques targeting media outlets, non-governmental organizations (NGOs), and login services. The following domain indicators were identified in the source material:

### Impersonating News Outlets
The group has created domains that closely resemble legitimate news sources with minor alterations to evade detection by security systems [1].
*   `azadlliq.info`
*   `businesslnsider.org`
*   `ecomonist.org`
*   `eocnomist.com`
*   `foreiqnaffairs.com`
*   `forieqnaffairs.com`
*   `foreiqnaffairs.org`
*   `israelhayum.com`
*   `jpost.press` [1]

### Impersonating Legitimate Services and Login Platforms
Targeted services include account management and authentication platforms. Common typos in usernames or services include "acconut", "admiscion", and generic "signin" variations [1].
*   `account-signin.com`
*   `acconut-signin.com`
*   `accounts-mails.com`
*   `coordinate.icu`
*   `dloffice.top`
*   `myaccount-signin.com`
*   `signin-acconut.com`
*   `admin-stable-right.top`
*   `admiscion.online`
*   `admit-roar-frame.top`
*   `check-pabnel-status.live`
*   `panel-view.live`
*   `verification...` [1]

### URL Shortening and Think Tank Impersonation
APT42 utilizes shortened domains to bypass some security filters and impersonates reputable research institutions.
*   **URL Shortening:** `s51.online`, `bitly.org.il` [1]
*   **Think Tanks:** `aspenlnstitute.org`, `mccainlnstitute.org`, `washingtonlnstitute.org` [1]

## Operational Techniques (MITRE ATT&CK)
The advisory documents that APT42 utilizes specific MITRE ATT&CK tactics and techniques during operations. These map to the following Tactic: Technique IDs:

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

## Operational Context
Based on the source material, APT42 operations began in 2021. The group has been documented impersonating well-known news outlets and employing typo-squatting to create web domains resembling legitimate entities [1]. Recent malware operations typically involve custom backdoors such as NICECURL and TAMECAT delivered via spear-phishing campaigns [1].

### References
1. Internal docs - APT42s recent activity.pdf