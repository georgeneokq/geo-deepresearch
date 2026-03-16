# APT42 Indicators of Compromise (IOCs) Report

## Executive Summary
This report details the Indicators of Compromise (IOCs) associated with the Advanced Persistent Threat group APT42, based on internal documentation regarding their recent operational activity. The document outlines specific malicious domains, custom backdoors, and URL shortening services utilized by the group. It also summarizes the MITRE ATT&CK techniques employed during these operations.

## Indicators of Compromise (IOCs)

### Custom Backdoors
APT42 utilizes custom backdoors for initial access and command execution [1].

*   **NICECURL**
    *   **Description:** A VBScript backdoor used to download modules for data mining and arbitrary command execution. It communicates over HTTPS.
    *   **SHA256:** `3c74109005111688341f4e5fcba42be9c21baa4465f5f84a5a342708732ac0ff` [1]
    *   **Supported Commands:** "kill", "SetNewConfig", "Module" [1]

*   **TAMECAT**
    *   **Description:** A PowerShell toehold that executes arbitrary PowerShell or C# content. It communicates via HTTP and expects Base64 encoded data from the C2 node [1].
    *   **SHA256:** `5404e39f2f175a0fc993513ee52be3679a64c69c79e32caa656fbb7645965422` [1]
    *   **SHA256:** `bd1f0fb085c486e97d82b6e8acb3977497c59c3ac79f973f96c395e7f0ca97f8` [1]
    *   **SHA256:** `156ac9685acb6696d8d7f64205e20ecf7a87dad304b8441449f0060ed175938b` [1]
    *   **SHA256:** `c99cc10f15f655f36314e54f7013a0bc5df85f4d6ff7f35b14a446315835d334` [1]
    *   **MD5:** `9c5337e0b1aef2657948fd5e82bdb4c3` [1]

### Malicious Domains
APT42 employs typo squatting to create domains resembling legitimate news outlets and impersonates journalists or event organizers for credential harvesting [1].

**Domains Impersonating News Outlets:**
*   `azadlliq.info` [1]
*   `businesslnsider.org` [1]
*   `ecomonist.org` [1]
*   `eocnomist.com` [1]
*   `foreiqnaffairs.com` [1]

**Domains Impersonating Legitimate Services:**
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
*   `accredit-validity.online` [1]
*   `activity-permission.online` [1]
*   `admin-stable-right.top` [1]
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
*   `check-pabnel-status.live` [1]
*   `check-panel-status.live` [1]
*   `check-short-panel.live` [1]
*   `confirmation-process.top` [1]
*   `connection-view.online` [1]
*   `continue-meeting.site` [1]
*   `continue-recognized.online` [1]
*   `cvisiion.online` [1]
*   `drive-access.site` [1]
*   `endorsement-services.online` [1]
*   `fortune-retire-home.top` [1]
*   `geaviews.site` [1]
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
*   `mterview.site` [1]
*   `nterview.site` [1]
*   `online-processing.online` [1]
*   `online-video-services.site` [1]
*   `ovcloud.online` [1]
*   `panel-check-short.live` [1]
*   `panel-live-check.online` [1]
*   `panel-short-check.live` [1]
*   `panel-view-short.online` [1]
*   `panel-view.live` [1]
*   `panel-view.online` [1]
*   `panel-views-cheking.live` [1]
*   `panelchecking.live` [1]
*   `paneling-viewing.live` [1]
*   `panels-views-ckeck.live` [1]
*   `pannel-get-data.us` [1]
*   `quomodocunquize.site` [1]
*   `recognize-validation.online` [1]
*   `reconsider.site` [1]
*   `revive-project-live.online` [1]
*   `short-url.live` [1]
*   `short-view.online` [1]
*   `shortenurl.online` [1]
*   `shortingurling.live` [1]
*   `shortlinkview.live` [1]
*   `shortulonline.live` [1]
*   `shorting-ce.live` [1]
*   `shoting-urls.live` [1]
*   `simple-process-static.top` [1]
*   `status-short.live` [1]
*   `stellar-roar-right.buzz` [1]
*   `sweet-pinnacle-readily.online` [1]
*   `tcvision.online` [1]
*   `title-flow-store.online` [1]
*   `twision.top` [1]
*   `ushrt.us` [1]
*   `verify-person-entry.top` [1]
*   `view-cope-flow.online` [1]
*   `view-pool-cope.online` [1]
*   `view-total-step.online` [1]
*   `viewstand.online` [1]
*   `viewtop.online` [1]
*   `virtue-regular-ready.online` [1]
*   `we-transfer.shop` [1]

### URL Shortening Services
APT42 utilizes domains posing as URL shortening services to facilitate communication or link delivery [1].
*   `m85.online` [1]
*   `s51.online` [1]
*   `s59.site` [1]
*   `s20.site` [1]
*   `d75.site` [1]
*   `bitly.org.il` [1]
*   `litby.us` [1]

### Miscellaneous and File Sharing Domains
Additional domains associated with APT42 activities include those posing as think tanks, file sharing services, or generic online access providers [1].
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
*   `washingtonlnstitute.org` [1]
*   `youtransfer.live` (File Sharing Services) [1]
*   `g-online.org` [1]
*   `online-access.live` [1]
*   `youronlineregister.com` [1]

## Operational Tactics and Techniques
APT42 employs specific MITRE ATT&CK techniques during their campaigns [1].

*   **Initial Access**
    *   T1566.001: Phishing - Spearphishing Attachment [1]
    *   T1566.002: Phishing - Spearphishing Link [1]
*   **Execution**
    *   T1059.001: Command and Scripting Interpreter - PowerShell [1]
    *   T1059.007: Command and Scripting Interpreter - JavaScript [1]
*   **Persistence**
    *   T1098.005: Account Manipulation - Device Registration [1]
*   **Defense Evasion**
    *   T1027: Obfuscated Files or Information [1]
    *   T1070: Indicator Removal - File Deletion [1]
*   **Discovery**
    *   T1083: File and Directory Discovery [1]
*   **Collection**
    *   T1005: Data from Local System [1]
*   **Exfiltration**
    *   T1041: Exfiltration Over C2 Channel [1]

## Summary of Activity
*   **Targeting:** Western and Middle Eastern media companies, non-governmental organizations (NGOs), academia, legal services, and activist groups [1].
*   **Modus Operandi:** The group uses typo squatting to create domains resembling legitimate news outlets and impersonates journalists or event organizers to send realistic conference invitations/documents for credential harvesting. They build trust before discreetly exfiltrating data using built-in features and open-source tools [1].
*   **Delivery:** Malware operations involve custom backdoors (NICECURL, TAMECAT) delivered via spear phishing [1].
*   **Communication:** NICECURL communicates over HTTPS; TAMECAT communicates with its C2 node via HTTP [1].

---

### References
1. Internal docs - APT42s recent activity.pdf