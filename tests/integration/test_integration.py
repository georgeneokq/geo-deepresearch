import pytest
from geo_deepresearch.util.testing import extract_citation_count
from langfuse import observe

@pytest.fixture
def test_report():
    return """
IOCs found:
- **News Outlets:** washinqtonpost[.]press, jpost[.]press, jpostpress[.]com, khaleejtimes[.]org, ynetnews[.]press, israelhayum[.]com [1]
- **Generic Services:** admin-stable-right[.]top, last-check-leave[.]buzz, panel-view[.]live, s51[.]online, g-online[.]org [1]
- **Mailers:** bitly[.]org[.]il, daemon-mailer[.]co, email-daemon[.]biz, mailerdaemon[.]online [1]
- **Think Tanks:** aspenlnstitute[.]org, washingtonlnstitute[.]org, mccainlnstitute[.]org [1]
- **File Sharing:** youtransfer[.]live [1]
- **NICECURL Domains:** drive-file-share[.]site, prism-west-candy[.]glitch[.]me [1]
- **NICECURL MD5s:** d5a05212f5931d50bb024567a2873642, 347b273df245f5e1fcbef32f5b836f1d, 2f6bf8586ed0a87ef3d156124de32757, 13aa118181ac6a202f0a64c0c7a61ce7, c23663ebdfbc340457201dbec7469386, 853687659483d215309941dae391a68f [1]
- **TAMECAT Domains:** tnt200[.]mywire[.]org, accurate-sprout-porpoise[.]glitch[.]me [1]
- **TAMECAT MD5s:** d7bf138d1aa2b70d6204a2f3c3bc72a7, 081419a484bbf99f278ce636d445b9d8, c3b9191f3a3c139ae886c0840709865e, dd2653a2543fa44eaeeff3ca82fe3513, 9c5337e0b1aef2657948fd5e82bdb4c3 [1]
- **Cluster 1 (Active 2022-2024):** beparas[.]com, parasil[.]me, darakeh[.]me, kandovani[.]org, topwor4u[.]com, opthrltd[.]me, joinoptimahr[.]com, optimax-hr[.]com, optimac-hr[.]com, optima-hr[.]com, titanium-hr[.]com [3]
- **Cluster 2 (Active 2017-2023):** azadijobs[.]me, bilal1com[.]com, damavand-hr[.]me, damkahill[.]com, dream-jobs[.]org, dream-jobs[.]vip, dreamy-job[.]com, dreamy-jobs[.]com, dreamycareer[.]com, golanjobs[.]me, hat-cast[.]com, irnjobs[.]me, jomehjob[.]com, radabala[.]com, rostam-hr[.]vip, salamjobs[.]me, shirazicom[.]com, syrtime[.]me, topiranjobs[.]me, trnjobs[.]me, vipjobsglobal[.]com, wazayif-halima[.]com, wazayif-halima[.]org, wehatcast[.]com, youna101[.]me, younamesh[.]com [3]

**References:**
1. https://cloud.google.com/blog/topics/threat-intelligence/untangling-iran-apt42-operations
2. https://cloud.google.com/blog/topics/threat-intelligence/apt42-charms-cons-compromises
3. https://cloud.google.com/blog/topics/threat-intelligence/uncovering-iranian-counterintelligence-operation

**Errors Browsing URLs**
1. https://cloud.google.com/security/resources/insights/apt-groups
""".strip()

@pytest.mark.integration
@pytest.mark.asyncio
@observe(name="Test: Citation count extraction")
async def test_citation_count_extraction(test_report):
    result = await extract_citation_count(test_report)
    assert result == 3