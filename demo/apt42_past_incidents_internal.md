Past Incidents and Campaign Operations (Since 2021):

**Operational Activity and Targets**
*   **Group Affiliation:** APT42 is identified as an Iranian state-sponsored cyber espionage group [1].
*   **Timeframe:** Operational activity has been observed since 2021 [1].
*   **Primary Targets:** Western and Middle Eastern media companies, non-governmental organizations (NGOs), academia, legal services, and activist groups [1].

**Tactics and Methods**
*   **Impersonation:** The group impersonates well-known news outlets and event organizers using social engineering techniques [1].
*   **Typo Squatting:** It creates web domains that closely resemble legitimate ones with minor alterations (e.g., changes to names) [1].
*   **Credential Harvesting:** Trust is built by sending realistic conference invitations or documents to obtain credentials and access cloud environments prior to data exfiltration [1].

**Specific Campaigns Observed**
*   **Large-scale Campaign:** Mandiant previously observed a specific campaign utilizing the TAMECAT PowerShell toehold [1].
*   **Targets of Campaign:** Individuals or entities employed by or affiliated with NGOs, government, or intergovernmental organizations around the world [1].
*   **Tools and Scripts:** Operations involved custom backdoors (NICECURL/TAMECAT) delivered via spear-phishing [1].
    *   NICECURL uses VBScript for command execution [1].
    *   TAMECAT uses PowerShell/C# for command execution and downloading modules [1].

**Indicators of Compromise (IoCs)**
*   **Hashes:** The advisory lists SHA256 hashes and MD5 hashes associated with the NICECURL and TAMECAT backdoors [1].
*   **Malicious Domains:** Numerous domains were used in spear-phishing attempts, including specific examples such as `jpost[.]press` [1].

**Data Availability Note**
*   The provided source material is truncated. The text concludes mid-sentence within the \"Background\" section (\"They the\"), indicating that additional context regarding past incidents or specific attack details may be missing from the available document [1].

References:
1. Internal docs - APT42s recent activity.pdf