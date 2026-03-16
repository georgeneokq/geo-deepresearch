# Report: Latest IOCs for APT42 in March 2026

## Executive Summary
Based on the provided source material, there is **no specific information regarding Indicators of Compromise (IOCs) for the period of March 2026**. The available document details APT42 activities and known IOCs up to May 2024. Consequently, this report compiles the historical IOCs (IPs, domains, hashes) identified in the source material as the most current data available within the provided context.

## 1. Malware Hashes
The following SHA-256 and MD-5 hashes have been associated with APT42 operations according to the source document [1]. These include samples linked to specific backdoors such as NICECURL and TAMECAT.

### SHA-256 Hashes
| SHA-256 Hash | Associated Backdoor/Context |
| :--- | :--- |
| `e0ba0cedd8a8624c75af29965e5fa7ab754fc0fcddbb330bb548dab4f2be333f` | General APT42 activity |
| `0e51029ba28243b0a6a071713c17357a8eb024aa4298d1ccc9e2c4ac8916df4d` | General APT42 activity |
| `3226b3e7d7fdaebfe7d7f06bdaf0cad08ea9792cd32843d01e6023f67cd0c889` | General APT42 activity |
| `3c74109005111688341f4e5fcba42be9c21baa4465f5f84a5a342708732ac0ff` | **NICECURL** backdoor |
| `dbdb14e37fc4412711a1e5e37e609e33410de31de13911aee99ab473753baa4a` | General APT42 activity |
| `07384ab4488ea795affc923851e00ebc2ead3f01b57be6bf8358d7659e9ee407` | General APT42 activity |
| `5404e39f2f175a0fc993513ee52be3679a64c69c79e32caa656fbb7645965422` | **TAMECAT** backdoor |
| `bd1f0fb085c486e97d82b6e8acb3977497c59c3ac79f973f96c395e7f0ca97f8` | **TAMECAT** backdoor |
| `156ac9685acb6696d8d7f64205e20ecf7a87dad304b8441449f0060ed175938b` | **TAMECAT** backdoor |
| `c99cc10f15f655f36314e54f7013a0bc5df85f4d6ff7f35b14a446315835d334` | **TAMECAT** backdoor |

### MD-5 Hashes
| MD-5 Hash | Associated Backdoor/Context |
| :--- | :--- |
| `9c5337e0b1aef2657948fd5e82bdb4c3` | **TAMECAT** backdoor |

## 2. Malicious Domains
The source document lists numerous domains used by APT42, categorized by their impersonation targets [1]. These domains are intended for phishing and credential harvesting.

### Impersonating News Outlets
| Domain | Targeted Outlet/Type |
| :--- | :--- |
| `azadlliq.info` | News |
| `businesslnsider.org` | News (Typo: Insider) |
| `ecomonist.org` / `eocnomist.com` | News (Typo: Economist) |
| `foreiqnaffairs.com` / `forieqnaffairs.org` / `foreiqnaffairs.org` | News (Typo: Foreign Affairs) |
| `israelhayum.com` | News |
| `jpost.press` / `jpostpress.com` | News |
| `khaleejtimes.org` / `khalejtimes.org` | News (Typo: Khaleej Times) |
| `maariv.net` | News |
| `themedealine.org` | News |
| `timesfisrael.com` | News |
| `vanityfaire.org` | News |
| `washinqtonpost.press` | News (Typo: Washington Post) |
| `ynetnews.press` | News |

### Impersonating Legitimate Services & Accounts
| Domain | Targeted Service/Type |
| :--- | :--- |
| `acconut-signin.com` / `signin-acconut.com` | Account Sign-in (Typo: Acconut) |
| `accounts-mails.com` / `signin-accounts.com` / `signin-mails.com` | Mail Services |
| `coordinate.icu` | Legitimate Service Impersonation |
| `dloffice.top` / `dloffice.buzz` | Legitimate Service Impersonation (Typo: Office?) |
| `myaccount-signin.com` | Account Sign-in |
| `accredit-validity.online` | Authentication |
| `activity-permission.online` | Permission Check |
| `admin-stable-right.top` / `admiscion.online` | Admin Services (Typo: Admision?) |
| `admit-roar-frame.top` | Legitimate Service Impersonation |
| `advission.online` | Advice/Advisory (Typo: Advison?) |
| `affect-fist-ton.online` | Legitimate Service Impersonation |
| `avid-striking-eagerness.online` | Legitimate Service Impersonation |
| `beaviews.online` / `geaviews.site` | Views/News (Typo: Geaviews) |
| `besvision.top` | Vision Services (Typo: Besvision?) |
| `bloom-flatter-affably.top` | Legitimate Service Impersonation |
| `book-download.shop` | File Download |
| `briview.online` | Views/News |
| `chat-services.online` | Chat Services |
| `check-online-panel.live` / `check-pabnel-status.live` / `check-panel-status.live` | Panel Status (Typo: Pabnel) |
| `check-short-panel.live` | Panel Check |
| `confirmation-process.top` | Verification |
| `connection-view.online` | Connection Services |
| `continue-meeting.site` / `continue-recognized.online` | Meeting Services |
| `cvisiion.online` | Vision Services (Typo: Cvisiion) |
| `drive-access.site` | Drive Access |
| `endorsement-services.online` | Endorsement Services |
| `fortune-retire-home.top` | Legitimate Service Impersonation |
| `glory-uplift-vouch.online` | Vouching Services |
| `go-conversation.lol` / `go-forward.quest` | Conversation/Forwarding |
| `gview.site` | Views/News (Typo: Geaviews) |
| `home-continue.online` / `home-proceed.online` | Home Services |
| `identifier-direction.site` | Identification |
| `indication-service.online` | Indication Services |
| `join-paneling.online` | Panel Joining |
| `ksview.top` | Views/News (Typo: Ksview?) |
| `last-check-leave.buzz` | Legitimate Service Impersonation |
| `live-project-online.live` / `live-projects-online.top` | Live Projects |
| `loriginal.online` | Legitimate Service Impersonation |
| `mail-roundcube.site` | Mail Services |
| `meeting-online.site` | Meeting Services |
| `mterview.site` / `nterview.site` | Interview (Typo: M/Nterview) |
| `online-processing.online` | Processing Services |
| `online-video-services.site` | Video Services |
| `ovcloud.online` | Cloud Services |
| `panel-check-short.live` / `panel-live-check.online` / `panel-short-check.live` | Panel Check |
| `panel-view-short.online` / `panel-view.live` / `panel-view.online` | Panel View |
| `panel-views-cheking.live` / `panelchecking.live` / `panels-views-ckeck.live` | Panel Checking (Typo: Ckecking/Ceck) |
| `pannel-get-data.us` | Data Retrieval (Typo: Pannel) |
| `quomodocunquize.site` | Legitimate Service Impersonation |
| `recognize-validation.online` | Validation Services |
| `reconsider.site` | Review Services |
| `revive-project-live.online` | Project Revival |
| `short-url.live` / `short-view.online` / `shortenurl.online` / `shortingurling.live` / `shortlinkview.live` / `shortulonline.live` / `shoting-urls.live` | URL Shortening (Typo: Shortulonline/Shoting) |
| `simple-process-static.top` | Static Processing |
| `status-short.live` | Status Check |
| `stellar-roar-right.buzz` | Legitimate Service Impersonation |
| `sweet-pinnacle-readily.online` | Legitimate Service Impersonation |
| `tcvision.online` | Vision Services (Typo: Tcvision?) |
| `title-flow-store.online` | Title/Flow Store |
| `twision.top` | Views/News (Typo: Twision) |
| `ushrt.us` | Legitimate Service Impersonation |
| `verify-person-entry.top` | Verification Entry |
| `view-cope-flow.online` / `view-pool-cope.online` / `view-total-step.online` / `viewstand.online` / `viewtop.online` | View Services |
| `virtue-regular-ready.online` | Legitimate Service Impersonation |
| `we-transfer.shop` | File Transfer |

### URL Shortening Services
| Domain | Type |
| :--- | :--- |
| `m85.online` / `s51.online` / `s59.site` / `s20.site` / `d75.site` | Generic Shorteners |
| `bitly.org.il` | Bitly (Israel) |
| `litby.us` | Litby |

### Email/Service Daemons
| Domain | Type |
| :--- | :--- |
| `daemon-mailer.co` / `email-daemon.biz` / `mailer-daemon.info` / `mailerdaemon.online` | Mail Daemon Services |
| `email-daemon.biz.tinurls.com` / `email-daemon.online.tinurls.com` | Mail Daemon + Shortener |
| `email-daemon.online` / `email-daemon.site` | Mail Daemon Services |
| `mailerdaemon.us` | Mail Daemon Services |

### Other Impersonations
| Domain | Targeted Type |
| :--- | :--- |
| `aspenlnstitute.org` / `mccainlnstitute.org` / `washingtonlnstitute.org` | Think Tanks/Research Institutes (Typo: Lnstitute) |
| `youtransfer.live` | File Sharing Services |
| `g-online.org` / `online-access.live` / `youronlineregister.com` | Miscellaneous Online Access |

## 3. MITRE ATT&CK Techniques
The source material identifies the following tactics and techniques utilized by APT42 [1]:

*   **Initial Access**:
    *   T1566.001 (Spearphishing Attachment)
    *   T1566.002 (Spearphishing Link)
*   **Execution**:
    *   T1059.001 (PowerShell Scripted Command)
    *   T1059.007 (JavaScript File Execution)
*   **Persistence**:
    *   T1098.005 (Device Registration)
*   **Defense Evasion**:
    *   T1027 (Obfuscated Files or Information)
    *   T1070 (Delete or Disable Files/Folders/Processes)
*   **Discovery**:
    *   T1083 (File and Directory Discovery)
*   **Collection**:
    *   T1005 (Data from Local System)
*   **Exfiltration**:
    *   T1041 (Exfiltration Over C2 Channel)

## 4. Operational Capabilities
According to the provided document [1], APT42 has been focused on intelligence gathering since 2021. The group utilizes custom backdoors, specifically **NICECURL** and **TAMECAT**, which are delivered primarily via spear-phishing campaigns.

---

### References
1. Internal docs - APT42s recent activity.pdf