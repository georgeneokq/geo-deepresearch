# Report: Current Indicators of Compromise (IOCs) for APT42 Group

## Executive Summary
This report compiles current Indicators of Compromise (IOCs) for the APT42 group, an Iranian state-sponsored cyber espionage unit active since 2021. Based on the analysis of recent activity reports published on May 02, 2024, the following IOCs have been identified. These indicators include file hashes associated with known backdoors and malicious domains used for social engineering and impersonation.

APT42 primarily targets Western and Middle Eastern media companies, NGOs, academia, legal services, and activist groups. Their operations utilize spearphishing (both via attachments and links), custom backdoors (**NICECURL** and **TAMECAT**), and the creation of typo-squatting domains to impersonate legitimate news outlets and services [1].

## Indicators of Compromise (IOCs)

### 1. Malicious File Hashes
The following SHA-256 and MD5 hashes have been identified in association with APT42 tools, specifically the **NICECURL** and **TAMECAT** backdoors.

**SHA-256 Hashes**
*   `3c74109005111688341f4e5fcba42be9c21baa4465f5f84a5a342708732ac0ff` (Associated with **NICECURL**) [1]
*   `5404e39f2f175a0fc993513ee52be3679a64c69c79e32caa656fbb7645965422` (Associated with **TAMECAT**) [1]
*   `bd1f0fb085c486e97d82b6e8acb3977497c59c3ac79f973f96c395e7f0ca97f8` (Associated with **TAMECAT**) [1]
*   `156ac9685acb6696d8d7f64205e20ecf7a87dad304b8441449f0060ed175938b` (Associated with **TAMECAT**) [1]
*   `c99cc10f15f655f36314e54f7013a0bc5df85f4d6ff7f35b14a446315835d334` (Associated with **TAMECAT**) [1]
*   `e0ba0cedd8a8624c75af29965e5fa7ab754fc0fcddbb330bb548dab4f2be333f` [1]
*   `0e51029ba28243b0a6a071713c17357a8eb024aa4298d1ccc9e2c4ac8916df4d` [1]
*   `3226b3e7d7fdaebfe7d7f06bdaf0cad08ea9792cd32843d01e6023f67cd0c889` [1]
*   `dbdb14e37fc4412711a1e5e37e609e33410de31de13911aee99ab473753baa4a` [1]
*   `07384ab4488ea795affc923851e00ebc2ead3f01b57be6bf8358d7659e9ee407` [1]

**MD5 Hashes**
*   `9c5337e0b1aef2657948fd5e82bdb4c3` (Associated with **TAMECAT**) [1]

### 2. Malicious Domains
APT42 utilizes a large number of domains to impersonate news outlets, legitimate services, and login portals. These include typo-squatting variants of well-known organizations.

**Domains Posing as News Outlets (Typo Squatting)**
*   `azadlliq.info` [1]
*   `businesslnsider.org` [1]
*   `ecomonist.org` [1]
*   `eocnomist.com` [1]
*   `foreiqnaffairs.com` (Listed as typo variant) [1]
*   `forieqnaffairs.com` (Listed as typo variant) [1]
*   `foreiqnaffairs.org` [1]
*   `israelhayum.com` [1]
*   `jpost.press` [1]
*   `jpostpress.com` [1]
*   `khaleejtimes.org` (Listed as typo variant) [1]
*   `maariv.net` [1]
*   `themedealine.org` [1]
*   `timesfisrael.com` [1]
*   `washinqtonpost.press` (Listed as typo variant) [1]
*   `ynetnews.press` [1]

**Domains Posing as Legitimate Services / Generic Login Services**
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
*   `accredit-validity.online` [1]
*   `activity-permission.online` [1]
*   `admiscion.online` [1]
*   `admit-roar-frame.top` [1]
*   `advission.online` [1]
*   `affect-fist-ton.online` [1]
*   `avid-striking-eagerness.online` [1]
*   `beaviews.online` [1]
*   `besvision.top` [1]
*   `bloom-flatter-affably.top` [1]
*   `book-download.shop` [1]
*   `bq-ledmagic.online` [1]
*   `briview.online` [1]
*   `chat-services.online` [1]
*   `check-online-panel.live` [1]
*   `check-pabnel-status.live` (Listed as typo variant) [1]
*   `check-panel-status.live` [1]
*   `check-short-panel.live` [1]
*   `confirmation-process.top` [1]
*   `connection-view.online` [1]
*   `continue-meeting.site` [1]
*   `continue-recognized.online` [1]
*   `cvisiion.online` (Listed as typo variant) [1]
*   `drive-access.site` [1]
*   `endorsement-services.online` [1]
*   `fortune-retire-home.top` [1]
*   `geaviews.site` (Listed as typo variant) [1]
*   `glory-uplift-vouch.online` [1]
*   `go-conversation.lol` [1]
*   `go-forward.quest` [1]
*   `gview.site` [1]
*   `home-continue.online` [1]
*   `home-proceed.online` [1]
*   `identifier-direction.site` [1]
*   `indication-service.online` [1]
*   `join-paneling.online` [1]
*   `ksview.top` [1]
*   `last-check-leave.buzz` [1]
*   `live-project-online.live` [1]
*   `live-projects-online.top` [1]
*   `loriginal.online` [1]
*   `mail-roundcube.site` [1]
*   `meeting-online.site` [1]
*   `mterview.site` (Listed as typo variant) [1]
*   `nterview.site` (Listed as typo variant) [1]
*   `online-processing.online` [1]
*   `online-video-services.site` [1]
*   `ovcloud.online` [1]
*   `panel-check-short.live` [1]
*   `panel-live-check.online` [1]
*   `panel-short-check.live` [1]
*   `panel-view-short.online` [1]
*   `panel-view.live` [1]
*   `panel-view.online` [1]
*   `panel-views-cheking.live` (Listed as typo variant) [1]
*   `panelchecking.live` [1]
*   `paneling-viewing.live` [1]
*   `panels-views-ckeck.live` (Listed as typo variant) [1]
*   `pannel-get-data.us` (Listed as typo variant) [1]
*   `quomodocunquize.site` [1]
*   `recognize-validation.online` [1]
*   `reconsider.site` [1]
*   `revive-project-live.online` [1]
*   `short-url.live` [1]
*   `short-view.online` [1]
*   `shortenurl.online` [1]
*   `shortingurling.live` [1]
*   `shortlinkview.live` [1]
*   `shortulonline.live` (Listed as typo variant) [1]
*   `shorting-ce.live` [1]
*   `shoting-urls.live` (Listed as typo variant) [1]
*   `simple-process-static.top` [1]
*   `status-short.live` [1]
*   `stellar-roar-right.buzz` [1]
*   `sweet-pinnacle-readily.online` [1]
*   `tcvision.online` [1]
*   `title-flow-store.online` [1]
*   `twision.top` (Listed as typo variant) [1]
*   `ushrt.us` [1]
*   `verify-person-entry.top` [1]
*   `view-cope-flow.online` [1]
*   `view-panel.live` [1]
*   `view-pool-cope.online` [1]
*   `view-total-step.online` [1]
*   `viewstand.online` [1]
*   `viewtop.online` [1]
*   `virtue-regular-ready.online` [1]
*   `we-transfer.shop` [1]

**URL Shortening Services / Miscellaneous Domains**
*   `m85.online` [1]
*   `s51.online` [1]
*   `s59.site` [1]
*   `s20.site` [1]
*   `d75.site` [1]
*   `bitly.org.il` [1]
*   `litby.us` [1]
*   `daemon-mailer.co` [1]
*   `daemon-mailer.info` [1]
*   `email-daemon.biz` [1]
*   `email-daemon.biz.tinurls.com` [1]
*   `email-daemon.online.tinurls.com` [1]
*   `email-daemon.online` [1]
*   `email-daemon.site` [1]
*   `mailer-daemon.info` [1]
*   `mailerdaemon.online` [1]
*   `mailer-daemon.us` [1]
*   `aspenlnstitute.org` [1]
*   `mccainlnstitute.org` (Posing as Think Tanks & Research Institutes) [1]
*   `washingtonlnstitute.org` (Listed as typo variant) [1]
*   `youtransfer.live` [1]
*   `g-online.org` [1]
*   `online-access.live` [1]
*   `yoronlineregister.com` [1]

## Tactics, Techniques, and Procedures (MITRE ATT&CK)
The following MITRE ATT&CK techniques have been identified as associated with APT42's operations based on the analyzed activity report:

| Tactic | Technique ID | Technique Name |
| :--- | :--- | :--- |
| Initial Access | T1566.001 | Phishing: Spearphishing Attachment |
| Initial Access | T1566.002 | Phishing: Spearphishing Link |
| Execution | T1059.001 | Command and Scripting Interpreter: PowerShell |
| Execution | T1059.007 | Command and Scripting Interpreter: JavaScript |
| Persistence | T1098.005 | Account Manipulation: Device Registration |
| Defense Evasion | T1027 | Obfuscated Files or Information |
| Defense Evasion | T1070 | Indicator Removal: File Deletion |
| Discovery | T1083 | File and Directory Discovery |
| Collection | T1005 | Data from Local System |
| Exfiltration | T1041 | Exfiltration Over C2 Channel |

## Backdoor Descriptions
*   **NICECURL**: A VBScript backdoor that downloads additional modules (e.g., data mining, command execution). It accepts commands such as "kill" (to remove artifacts), "SetNewConfig" (to set sleep values), and "Module" (to download/execute files). It communicates over HTTPS [1].
*   **TAMECAT**: A PowerShell toehold that executes arbitrary PowerShell or C# content. It is dropped by malicious macro documents, communicates with its C2 node via HTTP, and expects Base64 encoded data from the C2 [1].

## References
1. Internal docs - APT42s recent activity.pdf