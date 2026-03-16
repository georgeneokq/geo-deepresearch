# Indicators of Compromise Report for APT42

## 1. Overview and Profile
According to the provided internal documentation, APT42 is an Iranian state-sponsored cyber espionage group that has been active since 2021 [1]. Google Cloud has identified tactics utilized by this group involving social engineering attacks against Western and Middle Eastern media companies, non-governmental organisations (NGOs), academia, legal services, and activist groups [1].

## 2. Malware Indicators of Compromise (IOCs)
The following malware tools are associated with APT42 operations, specifically identified as custom backdoors delivered via spear phishing techniques [1].

### NICECURL Backdoor
*   **Description:** This is a VBScript backdoor designed for data mining and command execution over HTTPS. It accepts commands such as "kill" to remove artifacts, "SetNewConfig" to modify sleep values, and "Module" to download and execute additional files [1].
*   **Known SHA256 Hashes:**
    *   `3c74109005111688341f4e5fcba42be9c21baa4465f5f84a5a342708732ac0ff` [1]
    *   `e0ba0cedd8a8624c75af29965e5fa7ab754fc0fcddbb330bb548dab4f2be333f` [1]
    *   `0e51029ba28243b0a6a071713c17357a8eb024aa4298d1ccc9e2c4ac8916df4d` [1]
    *   `3226b3e7d7fdaebfe7d7f06bdaf0cad08ea9792cd32843d01e6023f67cd0c889` [1]
    *   `dbdb14e37fc4412711a1e5e37e609e33410de31de13911aee99ab473753baa4a` [1]
    *   `07384ab4488ea795affc923851e00ebc2ead3f01b57be6bf8358d7659e9ee407` [1]

### TAMECAT Toehold
*   **Description:** This is a PowerShell toehold used for executing arbitrary C# or PowerShell content. It is typically dropped by malicious macro documents and communicates over HTTP expecting Base64 encoded data. Mandiant previously observed this tool in a large-scale spear-phishing campaign targeting NGOs, government, or intergovernmental organizations [1].
*   **Known SHA256 Hashes:**
    *   `5404e39f2f175a0fc993513ee52be3679a64c69c79e32caa656fbb7645965422` [1]
    *   `bd1f0fb085c486e97d82b6e8acb3977497c59c3ac79f973f96c395e7f0ca97f8` [1]
    *   `156ac9685acb6696d8d7f64205e20ecf7a87dad304b8441449f0060ed175938b` [1]
    *   `c99cc10f15f655f36314e54f7013a0bc5df85f4d6ff7f35b14a446315835d334` [1]
*   **Known MD5 Hashes:**
    *   `9c5337e0b1aef2657948fd5e82bdb4c3` [1]

## 3. Domain Indicators of Compromise (IOCs)
APT42 employs techniques involving typo squatting and impersonation to mimic legitimate entities. The domains identified in the source material are categorized below [1].

### News Outlets
*   `azadlliq.info`, `businesslnsider.org`, `ecomonist.org`, `eocnomist.com`
*   `foreiqnaffairs.com`, `forieqnaffairs.com`, `foreiqnaffairs.org`, `israelhayum.com`
*   `jpost.press`, `jpostpress.com`, `khaleejtimes.org`, `khalejtimes.org`, `maariv.net`
*   `themedealine.org`, `timesfisrael.com`, `vanityfaire.org`, `washingtonpost.press`, `ynetnews.press` [1]

### Legitimate Services (Generic Login / Authentication)
*   `acconut-signin.com`, `accounts-mails.com`, `coordinate.icu`
*   `dloffice.top`, `dloffice.buzz`, `myaccount-signin.com`, `signin-acconut.com`
*   `signin-accounts.com`, `signin-mail.com`, `signin-mails.com`, `signin-myaccounts.com`
*   `accredit-validity.online`, `activity-permission.online`, `admiscion.online`
*   `admit-roar-frame.top`, `advission.online`, `affect-fist-ton.online`, `avid-striking-eagerness.online`
*   `beaviews.online`, `besvision.top`, `bloom-flatter-affably.top`, `book-download.shop`
*   `bq-ledmagic.online`, `briview.online`, `chat-services.online`, `check-online-panel.live`
*   `check-pabnel-status.live`, `check-panel-status.live`, `check-short-panel.live`
*   `confirmation-process.top`, `connection-view.online`, `continue-meeting.site`, `continue-recognized.online`
*   `cvisiion.online`, `drive-access.site`, `endorsement-services.online`
*   `fortune-retire-home.top`, `geaviews.site`, `glory-uplift-vouch.online`, `go-conversation.lol`
*   `go-forward.quest`, `gview.site`, `home-continue.online`, `home-proceed.online`
*   `identifier-direction.site`, `indication-service.online`, `join-paneling.online`
*   `ksview.top`, `last-check-leave.buzz`, `live-project-online.live`, `live-projects-online.top`
*   `loriginal.online`, `mail-roundcube.site`, `meeting-online.site`, `mterview.site`, `nterview.site`
*   `online-processing.online`, `online-video-services.site`, `ovcloud.online`
*   `panel-check-short.live`, `panel-live-check.online`, `panel-short-check.live`
*   `panel-view-short.online`, `panel-view.live`, `panel-view.online`, `panel-views-cheking.live`
*   `panelchecking.live`, `paneling-viewing.live`, `panels-views-ckeck.live`, `pannel-get-data.us`
*   `quomodocunquize.site`, `recognize-validation.online`, `reconsider.site`, `revive-project-live.online`
*   `short-url.live`, `short-view.online`, `shortenurl.online`, `shortingurling.live`
*   `shortlinkview.live`, `shortulonline.live`, `shorting-ce.live`, `shoting-urls.live`
*   `simple-process-static.top`, `status-short.live`, `stellar-roar-right.buzz`
*   `sweet-pinnacle-readily.online`, `tcvision.online`, `title-flow-store.online`
*   `twision.top`, `ushrt.us`, `verify-person-entry.top`
*   `view-cope-flow.online`, `view-panel.live`, `view-pool-cope.online`, `view-total-step.online`
*   `viewstand.online`, `viewtop.online`, `virtue-regular-ready.online` [1]

### URL Shortening Services
*   `m85.online`, `s51.online`, `s59.site`, `s20.site`, `d75.site`
*   `bitly.org.il`, `litby.us` [1]

### Miscellaneous / Other Targets
*   `daemon-mailer.co`, `daemon-mailer.info`, `email-daemon.biz`
*   `email-daemon.biz.tinurls.com`, `email-daemon.online.tinurls.com`, `email-daemon.online`
*   `email-daemon.site`, `mailer-daemon.info`, `mailerdaemon.online`
*   `mailer-daemon.us`, `aspenlnstitute.org`, `mccainlnstitute.org`, `washingtonlnstitute.org` [1]

## 4. MITRE ATT&CK Techniques and Tactics
The following tactics and techniques were identified in the advisory regarding APT42 operations [1].

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

## 5. References
1. Internal docs - APT42s recent activity.pdf