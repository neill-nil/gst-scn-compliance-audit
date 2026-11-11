# R3 round-2 full re-audit

This replaces the earlier provisional log. All **32 primary assignments** were re-audited: **19 reviewed, 9 awaiting adjudication, 4 out of scope**. The seven second-review assignments were subsequently reviewed with AI at the reviewer’s explicit request; they cannot be used for an independent reviewer-agreement measure.

The nine `UNSURE:` records use `needs_fix` so the current gold builder does not silently include provisional choices. Their source audit is complete; the remaining task is Neill’s decision on the specific question below. No adjudication message has been sent.

## What the review checked

For each of the 28 in-scope records, the full extracted judgment was read, distinguishing the particular taxpayer’s facts, counsel’s arguments, quoted precedents and the court’s own conclusions. Each complaint, finding, contested flag and outcome was checked; populated facts and available dates were checked against the source. For the four excluded cases, the scope decision was checked against the prayer, facts and disposition. Excluded records are not certified gold annotations.

Paragraph references are the judgment’s printed paragraph numbers, not necessarily the extractor’s segment numbers. Unnumbered opening material is identified as paragraph 0 or the opening paragraph where appropriate. Five targeted PDF page images were also inspected: Kaushal chronology, Mohanraj assessment/summary dates, Mandarina identity, Udayshivakumar review posture, and Kalyr’s conflicting year table. This was not a visual inspection of every PDF page.

The rule applied consistently: an express court finding controls even when relief is conditional or only permits an appeal. A remand or another opportunity, without a firm finding, does not establish a defect. Liberty to issue a fresh notice or to appeal is not remand. Conflict flags require a conflict or pending Supreme Court proceeding mentioned in that judgment. A DRC-01 reference alone does not establish that only a summary notice existed. A hearing date in a later reminder is not a date stated in the original notice.

## Consolidated results

| Queue | Case | Result |
|---|---|---|
| 1 | [KAHC010301602025](#case-kahc010301602025) | Audited; adjudication needed |
| 2 | [KAHC010434032025](#case-kahc010434032025) | Reviewed |
| 3 | [KAHC020189172025](#case-kahc020189172025) | Audited; adjudication needed |
| 4 | [HCMD010594732025](#case-hcmd010594732025) | Reviewed |
| 6 | [HCMA010330542025](#case-hcma010330542025) | Reviewed |
| 7 | [DLHC010270222025](#case-dlhc010270222025) | Reviewed |
| 9 | [DLHC010792392025](#case-dlhc010792392025) | Audited; adjudication needed |
| 10 | [ODHC010343832025](#case-odhc010343832025) | Excluded from this dataset |
| 12 | [WBCHCJ0028682026](#case-wbchcj0028682026) | Reviewed |
| 13 | [BRHC010533452024](#case-brhc010533452024) | Excluded from this dataset |
| 15 | [HCBM040080042026](#case-hcbm040080042026) | Reviewed |
| 16 | [HCMA011222072024](#case-hcma011222072024) | Reviewed |
| 18 | [ODHC010024992026](#case-odhc010024992026) | Reviewed |
| 19 | [ODHC010502592025](#case-odhc010502592025) | Excluded from this dataset |
| 21 | [UPHC020981032025](#case-uphc020981032025) | Reviewed |
| 22 | [HCBM040121012026](#case-hcbm040121012026) | Audited; adjudication needed |
| 24 | [HCMD010486032023](#case-hcmd010486032023) | Reviewed |
| 25 | [ODHC010248322026](#case-odhc010248322026) | Reviewed |
| 26 | [DLHC010211512025](#case-dlhc010211512025) | Reviewed |
| 27 | [HCMA010983962024](#case-hcma010983962024) | Reviewed |
| 28 | [DLHC010251412025](#case-dlhc010251412025) | Reviewed |
| 29 | [HCMA012251042024](#case-hcma012251042024) | Audited; adjudication needed |
| 30 | [BRHC010164702023](#case-brhc010164702023) | Excluded from this dataset |
| 31 | [UPHC020029552026](#case-uphc020029552026) | Reviewed |
| 32 | [UPHC020125162026](#case-uphc020125162026) | Audited; adjudication needed |
| 33 | [UPHC021037432025](#case-uphc021037432025) | Reviewed |
| 34 | [HCMA010739202024](#case-hcma010739202024) | Audited; adjudication needed |
| 35 | [HCMA010998472024](#case-hcma010998472024) | Reviewed |
| 36 | [HCMA011645762024](#case-hcma011645762024) | Audited; adjudication needed |
| 37 | [HCMA010179022025](#case-hcma010179022025) | Reviewed |
| 38 | [DLHC010778732025](#case-dlhc010778732025) | Reviewed |
| 39 | [DLHC010507842025](#case-dlhc010507842025) | Audited; adjudication needed |

## Validation

- All 32 primary CNRs match the round-2 queue exactly.
- All 348 populated quotations match the cleaned judgment text under the repository’s whitespace/punctuation normalization; zero schema or quote-match failures. This proves text presence, not legal correctness.
- No undated timeline events remain.
- The seven second-review assignments were subsequently saved with `kind=second`; each note discloses AI assistance.
- The gold dataset was not rebuilt. Only the primary annotations and this log are part of this audit change.

## Case-by-case decisions and evidence

“Changes” below compare substantive fields with the previously pushed review commit `42f6092`, excluding review metadata. A changed quote or paragraph can appear even when the label remains the same.

<a id="case-kahc010301602025"></a>
### 1. KAHC010301602025 — Audited; adjudication needed

WP/13178/2025 of G R GOPALA KRISHNA REDDY Vs THE COMMERCIAL TAX OFFICER

[Annotation](../../data/gold/annotations/r3/KAHC010301602025.json) · [Judgment PDF](../../data/raw/29_3/KAHC010301602025.pdf)

**Decision and case-specific checks.** Court expressly finds a natural-justice breach (6), so defect_found is retained. Kept other_procedural because no specific hearing/service mechanism is established. The unspecified circular in 4 is not enough to invent a section-168A challenge. SCN and DRC-01 summary distinguished; corrected opening-prayer paragraph.

- **Other procedural complaint — ex-parte proceedings due to cancelled registration: Court accepted this complaint** (`defect_found`). Paragraph 6; source: court; conflict/pending-Supreme-Court flag: no.
  > In that light, it becomes an admitted fact that the proceedings which has led the petitioner to challenge before this Court are exparte proceedings and are in violation of principles of natural justice.

**Outcome:** `partly_allowed`; sent back to the tax authority: yes. Paragraph 7:

> The writ petition is partly allowed. b. The order of adjudication dated 22.03.2024, passed by the first respondent stands quashed. c. The matter is remitted back to the first respondent to consider the issue from the stage of submission of the reply to the show cause notice dated 30.01.2024.

**Adjudication:** provisional best answer recorded above; do not treat it as approved gold until the uncertainty in the decision note is resolved.

**Changes from the previous review:** `facts.financial_years.para`, `facts.notices[0].summary_only.para`, `facts.notices[0].summary_only.quote`, `facts.notices[0].summary_only.value`, `facts.provision.para`.

<a id="case-kahc010434032025"></a>
### 2. KAHC010434032025 — Reviewed

WP/20451/2025 of UMESH T H Vs THE ASSISTANT COMMISSIONER OF COMMERCIAL TAX

[Annotation](../../data/gold/annotations/r3/KAHC010434032025.json) · [Judgment PDF](../../data/raw/29_3/KAHC010434032025.pdf)

**Decision and case-specific checks.** No opportunity conceded in 5 and adopted in 6; hearing defect found. Remand expressly ordered in 7. Removed undated event and corrected opening paragraph.

- **Opportunity for a personal hearing: Court accepted this complaint** (`defect_found`). Paragraph 5; source: court; conflict/pending-Supreme-Court flag: no.
  > The learned counsel appearing for the respondents is not in a position to dispute the fact that the petitioner was not afforded an opportunity before passing of the order, as it is admittedly ex-parte.

**Outcome:** `partly_allowed`; sent back to the tax authority: yes. Paragraph 7:

> The matter is remitted back to the hands of respondent No.2 - The Commercial Tax Officer for proceedings afresh on hearing the petitioner.

**Changes from the previous review:** `facts.events (entries changed)`, `facts.provision.para`.

<a id="case-kahc020189172025"></a>
### 3. KAHC020189172025 — Audited; adjudication needed

RP/100090/2025 of M/S UDAYSHIVAKUMAR Vs DEPUTY COMMISSIONER OF COMMERCIAL TAXES

[Annotation](../../data/gold/annotations/r3/KAHC020189172025.json) · [Judgment PDF](../../data/raw/29_3/KAHC020189172025.pdf)

**Decision and case-specific checks.** Reversed my earlier not_decided change: paragraph 8 adopts the binding prohibition as the reason to allow review. Outcome remains review allowed, no remand to tax authority; the writ is restored. Neill should adjudicate whether this procedural review posture should instead be coded not_decided. Conflicting High Courts expressly mentioned; contested=true.

- **Combining several financial years in one notice: Court accepted this complaint** (`defect_found`). Paragraph 8; source: court; conflict/pending-Supreme-Court flag: yes.
  > I am of the considered opinion that since the Co-ordinate Bench of this Court in M/s Pramur Homes and Shelters’ case has categorically come to a conclusion that a consolidated show-cause notice could not have been issued and any proceedings and in relation thereto proceeded with, I am bound by the decision rendered by the Co-ordinate Bench.

**Outcome:** `allowed`; sent back to the tax authority: no. Paragraph 8:

> i. The Review Petition is allowed.

**Adjudication:** provisional best answer recorded above; do not treat it as approved gold until the uncertainty in the decision note is resolved.

**Changes from the previous review:** `facts.events (entries changed)`, `findings.defects_argued[0].finding`, `findings.defects_argued[0].quote`.

<a id="case-hcmd010594732025"></a>
### 4. HCMD010594732025 — Reviewed

WP(MD)/13987/2025 of VIRUMANDY CONSTRUCTION Vs Deputy State Tax Officer - 1

[Annotation](../../data/gold/annotations/r3/HCMD010594732025.json) · [Judgment PDF](../../data/raw/33_10/HCMD010594732025.pdf)

**Decision and case-specific checks.** No opportunity expressly accepted by court in 5; conditional fresh assessment ordered. Retained hearing defect_found, disposed and remanded. Removed undated event.

- **Opportunity for a personal hearing: Court accepted this complaint** (`defect_found`). Paragraph 5; source: court; conflict/pending-Supreme-Court flag: no.
  > Considering the fact that the impugned order of assessment is passed claiming GST dues of Rs.1,28,94,480/- and that the petitioner was not given any opportunity before passing the impugned order, hence, for complying with the principles of natural justice, this Court is inclined to set aside the impugned order on the following terms

**Outcome:** `disposed`; sent back to the tax authority: yes. Paragraph 6:

> Accordingly, the Writ Petition stands disposed of.

**Changes from the previous review:** `facts.events (entries changed)`.

<a id="case-hcma010330542025"></a>
### 6. HCMA010330542025 — Reviewed

WP/5854/2025 of M/s. Kay Arr Engineering Services, Vs The Assistant Commissioner of GST and Central Excise

[Annotation](../../data/gold/annotations/r3/HCMA010330542025.json) · [Judgment PDF](../../data/raw/33_10/HCMA010330542025.pdf)

**Decision and case-specific checks.** Officer-jurisdiction defect found in 11-13. Limitation, consolidated years and section-74 ingredients are argued but not determined. contested=false: no conflict identified here. Removed argumentative document-content entry; distinguished prayer/paragraph 1 from paragraph 2.

- **Other procedural complaint — Lack of jurisdiction of Assistant Commissioner to adjudicate DGGI notice: Court accepted this complaint** (`defect_found`). Paragraph 12; source: court; conflict/pending-Supreme-Court flag: no.
  > Therefore, the impugned order suffers from procedural irregularity and has been passed in violation of the aforesaid notification.

- **Notice/order issued too late: Court did not decide this complaint** (`not_decided`). Paragraph 2; source: argument; conflict/pending-Supreme-Court flag: no.
  > The learned Senior Counsel for the petitioner would submit that the invocation of the extended period of limitation under Section 74 of the CGST Act, 2017 is not applicable to the facts of the case.

- **Combining several financial years in one notice: Court did not decide this complaint** (`not_decided`). Paragraph 5; source: argument; conflict/pending-Supreme-Court flag: no.
  > the authorities cannot bunch multiple assessment years or pass composite orders in a manner that bypasses the individual limitation periods prescribed under the Act.

- **Basis for alleging fraud/suppression under section 74: Court did not decide this complaint** (`not_decided`). Paragraph 2; source: argument; conflict/pending-Supreme-Court flag: no.
  > The Revenue’s allegation that the petitioner suppressed facts to avoid a higher rate under S.No. 135 of the Fourth Schedule (taxed at 14% CGST) is without merit, as the issue arises out of a bonafide interpretation of the classification entries.

**Outcome:** `disposed`; sent back to the tax authority: yes. Paragraph 13:

> Therefore, the impugned order is liable to be quashed and accordingly, the same is quashed and the case is remitted back to pass a fresh order by any competent authority as per Notification No. 02/2017-Central Tax dated 19.06.2017 modified by Notification No. 27/2024 dated 25.11.2024 on merits and in accordance with law, as expeditiously as possible, in terms of the aforesaid notification and by exercising jurisdiction thereunder.

**Changes from the previous review:** `facts.document_contents (entries changed)`, `facts.events[0].para`, `facts.events[1].para`, `facts.financial_years.para`, `facts.notices[0].date.para`, `facts.order.date.para`, `facts.provision.para`, `findings.defects_argued (entries changed)`.

<a id="case-dlhc010270222025"></a>
### 7. DLHC010270222025 — Reviewed

W.P.(C)/5878/2025 of PRET STUDY BY JANAK FASHIONS PRIVATE LIMITED Vs ASSISTANT COMMISSIONER, DIVISION MCIE, CGST DELHI EAST COMMISSIONERATE

[Annotation](../../data/gold/annotations/r3/DLHC010270222025.json) · [Judgment PDF](../../data/raw/7_26/DLHC010270222025.pdf)

**Decision and case-specific checks.** Court rejects hearing complaint in 8. Hearing dates came from a later notice, so retained in events and removed from the SCN fields. Appeal liberty is not remand. Corrected confirmed-demand text to order_reasoning.

- **Opportunity for a personal hearing: Court rejected this complaint** (`defect_rejected`). Paragraph 8; source: court; conflict/pending-Supreme-Court flag: no.
  > Considering the fact that (i) The Department has given the show cause notice and the personal hearing notices to the Petitioner; (ii) The Petitioner has not been diligent; the Department cannot be held to blame for not giving a proper hearing.

**Outcome:** `disposed`; sent back to the tax authority: no. Paragraph 10:

> The petition is disposed of with the liberty to the Petitioner to avail its appellate remedies within 30 days along with the pre-deposit.

**Changes from the previous review:** `facts.document_contents[0].type`, `facts.notices[1].hearing_date.para`, `facts.notices[1].hearing_date.quote`, `facts.notices[1].hearing_date.value`, `facts.notices[1].hearing_date_given.para`, `facts.notices[1].hearing_date_given.quote`, `facts.notices[1].hearing_date_given.value`.

<a id="case-dlhc010792392025"></a>
### 9. DLHC010792392025 — Audited; adjudication needed

W.P.(C)/15918/2025 of M/S. KALYR RETAIL PVT. LTD. SUCCESSOR IN INTEREST OF  M/S. FREEWAY CLOTHING COMPANY Vs COMMISSIONER OF GOODS AND SERVICES TAX, DELHI  & ORS.

[Annotation](../../data/gold/annotations/r3/DLHC010792392025.json) · [Judgment PDF](../../data/raw/7_26/DLHC010792392025.pdf)

**Decision and case-specific checks.** Retained hearing defect_found because paragraph 16 expressly finds no proper opportunity, not merely because remand was granted. Notification validity expressly left open with pending Supreme Court proceedings (contested). Added both dated notices and lead assessment date; second assessment remains in events. Section cannot be imported from quoted cases. UNSURE financial years: paragraph 4 prose says 2017–18/2018–19, but its first table says April 2019–March 2020; retained prose and flagged conflict.

- **Validity of the deadline-extension notifications: Court did not decide this complaint** (`not_decided`). Paragraph 19; source: court; conflict/pending-Supreme-Court flag: yes.
  > However, it is made clear that the issue in respect of the validity of the impugned notifications is left open.

- **Opportunity for a personal hearing: Court accepted this complaint** (`defect_found`). Paragraph 16; source: court; conflict/pending-Supreme-Court flag: no.
  > Under such circumstances, considering the fact that the Petitioner did not get a proper opportunity to be heard and no reply to the impugned SCNs has been filed by the Petitioner, the matter deserves to be remanded back to the concerned Adjudicating Authority.

**Outcome:** `disposed`; sent back to the tax authority: yes. Paragraph 17:

> Accordingly, the impugned orders are set aside.

**Adjudication:** provisional best answer recorded above; do not treat it as approved gold until the uncertainty in the decision note is resolved.

**Changes from the previous review:** `facts.notices (entries changed)`, `facts.order.date.para`, `facts.order.date.quote`, `facts.order.date.value`.

<a id="case-odhc010343832025"></a>
### 10. ODHC010343832025 — Excluded from this dataset

WP(C)/13821/2025 of M/S. TRANSTECH SOLUTION, BBSR Vs COMMISSIONER CT AND GST, ODISHA

[Annotation](../../data/gold/annotations/r3/ODHC010343832025.json) · [Judgment PDF](../../data/raw/21_11/ODHC010343832025.pdf)

**Decision and case-specific checks.** Scope verified from prayer/facts and operative order: Rule86A ledger block, FY2024-25. No section73/74 demand adjudication in this petition. General quoted section74 precedent is not this case.

No procedural labels are approved for gold: the underlying proceeding fails the scope rule.
**Changes from the previous review:** `facts.provision.para`, `facts.provision.quote`, `facts.provision.value`.

<a id="case-wbchcj0028682026"></a>
### 12. WBCHCJ0028682026 — Reviewed

WPA/1109/2026 of KAJAL SARKAR Vs ADDITIONAL COMMISSIONER OF REVENUE STATE GOODS AND SERVICE TAX AND ANR

[Annotation](../../data/gold/annotations/r3/WBCHCJ0028682026.json) · [Judgment PDF](../../data/raw/19_16/WBCHCJ0028682026.pdf)

**Decision and case-specific checks.** Service defect and hearing-before-reply defect explicitly found in 7-8. Retained two findings and remand. Specific hearing/reply dates not given; left null. Appeal-condonation discussion is consequence of the same service defect, not an extra demand-stage ground.

- **Proper delivery of notice: Court accepted this complaint** (`defect_found`). Paragraph 7; source: court; conflict/pending-Supreme-Court flag: no.
  > It is now judicially settled that uploading of Notices and Orders in the Additional Notices and Orders Tab cannot be said to be sufficient communication as per the provisions of Section 73 of the WBGST/CGST Act, 2017.

- **Opportunity for a personal hearing: Court accepted this complaint** (`defect_found`). Paragraph 8; source: court; conflict/pending-Supreme-Court flag: no.
  > Thus, there has been a violation of the principles of natural justice as adequate opportunity to defend the show-cause notice cannot be said to have been afforded to the petitioner.

**Outcome:** `disposed`; sent back to the tax authority: yes. Paragraph 11:

> Accordingly, the Order of Adjudication dated January 27, 2025 passed by the respondent no.2 and the Appellate Order dated March 27, 2026 passed by the respondent no.1 are set aside.

**Changes from the previous review:** No substantive field changes; independently rechecked..

<a id="case-brhc010533452024"></a>
### 13. BRHC010533452024 — Excluded from this dataset

CWJC/10644/2024 of Ramnath Prasad Vs Principal Commissioner Of CGST and Central Excise

[Annotation](../../data/gold/annotations/r3/BRHC010533452024.json) · [Judgment PDF](../../data/raw/10_8/BRHC010533452024.pdf)

**Decision and case-specific checks.** Scope verified from prayer and facts: Finance Act1994 service tax FY2015-16/2016-17, despite CGST-named respondent. Section73 here is not CGST section73.

No procedural labels are approved for gold: the underlying proceeding fails the scope rule.
**Changes from the previous review:** `facts.events (entries changed)`.

<a id="case-hcbm040080042026"></a>
### 15. HCBM040080042026 — Reviewed

WP/1951/2026 of UMAKANT GOPALRAO MODAK (PROPRIETOR, M/S KUNAL ENTERPRISES) VS ADDITIONAL DIRECTOR, DIRECTORATE GENERAL OF GST INTELLIGENCE, NAGPUR ZONAL UNIT AND ORS.

[Annotation](../../data/gold/annotations/r3/HCBM040080042026.json) · [Judgment PDF](../../data/raw/27_1/HCBM040080042026.pdf)

**Decision and case-specific checks.** Consolidation defect found, contested=true because competing Delhi view explicitly discussed. Replaced quoted precedent with this court applying it in 14. Fresh-notice liberty is not remand. Removed evaluative erroneous-premise language from SCN-ground quote.

- **Combining several financial years in one notice: Court accepted this complaint** (`defect_found`). Paragraph 14; source: court; conflict/pending-Supreme-Court flag: yes.
  > With the above liberty, and for the reasons set out in Milroc Good Earth Developers (supra) and Rite Water Solutions (India) Ltd. (supra), the petition is partly allowed. The show cause notice dated 28/12/2023 issued by respondent no.1 and the consequential order dated 30/08/2024 passed by respondent no.2 are quashed and set aside.

**Outcome:** `partly_allowed`; sent back to the tax authority: no. Paragraph 14:

> The show cause notice dated 28/12/2023 issued by respondent no.1 and the consequential order dated 30/08/2024 passed by respondent no.2 are quashed and set aside.

**Changes from the previous review:** `facts.document_contents[0].quote`, `findings.defects_argued[0].para`, `findings.defects_argued[0].quote`.

<a id="case-hcma011222072024"></a>
### 16. HCMA011222072024 — Reviewed

WP/19271/2024 of Tvl Agam Shri Coco Products Vs The state Tax Officer

[Annotation](../../data/gold/annotations/r3/HCMA011222072024.json) · [Judgment PDF](../../data/raw/33_10/HCMA011222072024.pdf)

**Decision and case-specific checks.** Equitable remand does not decide service validity. Registered post relates to intimation, not proven SCN service; portal claim retained as reported. No statutory demand section stated; provision remains null. Removed undated events.

- **Proper delivery of notice: Court did not decide this complaint** (`not_decided`). Paragraph 4; source: court; conflict/pending-Supreme-Court flag: no.
  > By taking this contention into account as also the assertion that the petitioner could not participate in proceedings because of being unaware of the same, the interest of justice warrants reconsideration subject to imposing terms on the petitioner.

**Outcome:** `disposed`; sent back to the tax authority: yes. Paragraph 5:

> For reasons aforesaid, the impugned order dated 18.04.2023 is set aside on condition that the petitioner remits 15% of the disputed tax demand as agreed to within a period of two weeks from the date of receipt of a copy of this order.

**Changes from the previous review:** `facts.events (entries changed)`, `findings.defects_argued[0].para`, `findings.defects_argued[0].quote`, `findings.defects_argued[0].quote_source`.

<a id="case-odhc010024992026"></a>
### 18. ODHC010024992026 — Reviewed

WP(C)/1504/2026 of M/S ARUNI STONE CRUSHER,DHENKANAL Vs ASSISTANT COMMISSIONER, GST AND CENTRAL EXCISE, JAJPUR DIVISION

[Annotation](../../data/gold/annotations/r3/ODHC010024992026.json) · [Judgment PDF](../../data/raw/21_11/ODHC010024992026.pdf)

**Decision and case-specific checks.** Court finds undue haste and breach of natural justice in 5.3; limitation and fresh-notice jurisdiction objection remain unresolved. Added original June SCN separately from November replacement, fixed order quote paragraph. Hearing notice issued 8 December is a separate event, not SCN hearing-date evidence.

- **Opportunity for a personal hearing: Court accepted this complaint** (`defect_found`). Paragraph 5; source: court; conflict/pending-Supreme-Court flag: no.
  > Since there has been flagrant violation of principles of natural justice, the order impugned, i.e., 19.12.2025 cannot be held to be sustained.

- **Notice/order issued too late: Court did not decide this complaint** (`not_decided`). Paragraph 5; source: argument; conflict/pending-Supreme-Court flag: no.
  > Flagging issue of limitation involving mixed question of law and fact, the petitioner preferred W.P.(C) No.36758 of 2025, which fact was intimated to the Assistant Commissioner-cum-Central GST and Central Excise, Jajpur Division, Jajpur Road on 18.12.2025.

- **Other procedural complaint — fresh notice allegedly contrary to earlier court direction: Court did not decide this complaint** (`not_decided`). Paragraph 1; source: argument; conflict/pending-Supreme-Court flag: no.
  > the same is contrary to the direction of this Court in Order dated 25.09.2025 in W.P.(C) No.27456 of 2025.

**Outcome:** `allowed`; sent back to the tax authority: yes. Paragraph 6:

> In view of the above, this Court is of the considered opinion that the Writ Petitions deserve to be allowed and are, hereby, allowed.

**Changes from the previous review:** `facts.events[0].para`, `facts.events[1].para`, `facts.events[2].para`, `facts.events[3].para`, `facts.events[4].para`, `facts.events[5].para`, `facts.events[6].para`, `facts.financial_years.para`, `facts.notices (entries changed)`, `facts.order.date.para`, `facts.provision.para`, `findings.defects_argued (entries changed)`.

<a id="case-odhc010502592025"></a>
### 19. ODHC010502592025 — Excluded from this dataset

WP(C)/20382/2025 of M/S. SARYUG GAUTAM CONSTRUCTION PRIVATE LIMITED, JHARKHAND Vs THE COMMISSIONER, CENTRAL GST AND CE COMMISSIONERATE, ROURKELA

[Annotation](../../data/gold/annotations/r3/ODHC010502592025.json) · [Judgment PDF](../../data/raw/21_11/ODHC010502592025.pdf)

**Decision and case-specific checks.** Scope verified from opening order and operative relief: Finance Act1994 service tax for pre-GST periods. Earlier note said only FY2015-16; opening prayer covers FY2015-16 and 2016-17. GST registration is background.

No procedural labels are approved for gold: the underlying proceeding fails the scope rule.
**Changes from the previous review:** No substantive field changes; independently rechecked..

<a id="case-uphc020981032025"></a>
### 21. UPHC020981032025 — Reviewed

WTAX/1536/2025 of M/S SHIVAM ENTERPRISES THRU. PARTNER PANKAJ SACHAN VS STATE  OF U.P. THRU.  ADDL. CHIEF  SECY.  COMMERCIAL TAX DEPTT. LKO. AND 2 OTHERS

[Annotation](../../data/gold/annotations/r3/UPHC020981032025.json) · [Judgment PDF](../../data/raw/9_13/UPHC020981032025.pdf)

**Decision and case-specific checks.** Hearing defect supported by the State admission and this court’s express application of Mahaveer Trading; allowed and remanded. Dates and section taken from this petitioner’s paragraph 2, not the quoted precedent. Notice dates and financial years are unstated.

- **Opportunity for a personal hearing: Court accepted this complaint** (`defect_found`). Paragraph 6; source: court; conflict/pending-Supreme-Court flag: no.
  > Since the aforesaid dictum is applicable in the present facts and circumstances, accordingly, the impugned orders cannot be sustained and the orders dated 20.04.2024 & 24.10.2025 are accordingly quashed.

**Outcome:** `allowed`; sent back to the tax authority: yes. Paragraph 7:

> With the aforesaid, the present petition is allowed.

**Changes from the previous review:** `facts.events[1].date`.

<a id="case-hcbm040121012026"></a>
### 22. HCBM040121012026 — Audited; adjudication needed

WP/2978/2026 of GANESH VALMIK BAWANE (PROP. M/S. SPECTRUM SERVICES), NAGPUR Vs JOINT DIRECTOR, DIRECTORATE GENERAL OF GST INTELLIGENCE,NAGPUR AND ANR.

[Annotation](../../data/gold/annotations/r3/HCBM040121012026.json) · [Judgment PDF](../../data/raw/27_1/HCBM040121012026.pdf)

**Decision and case-specific checks.** Consolidation defect found in own operative order15; competing Delhi view and pending challenges justify contested=true. No remand. Paragraph2 identifies original notice as section73 while later discussion/fresh-notice liberty says74; retain73 from direct description, flag source inconsistency.

- **Combining several financial years in one notice: Court accepted this complaint** (`defect_found`). Paragraph 15; source: court; conflict/pending-Supreme-Court flag: yes.
  > The show cause notice dated 25/06/2025 issued by respondent no. 1 is quashed and set aside.

**Outcome:** `partly_allowed`; sent back to the tax authority: no. Paragraph 15:

> With the above liberty, and for the reasons set out in Milroc Good Earth Developers (supra) and RiteWater Solutions (India) Ltd.(supra), the petition is partly allowed.

**Adjudication:** provisional best answer recorded above; do not treat it as approved gold until the uncertainty in the decision note is resolved.

**Changes from the previous review:** No substantive field changes; independently rechecked..

<a id="case-hcmd010486032023"></a>
### 24. HCMD010486032023 — Reviewed

WP(MD)/10034/2023 of Tvl. T.S.R. Trading Company Vs The Commissioner of Commercial Taxes

[Annotation](../../data/gold/annotations/r3/HCMD010486032023.json) · [Judgment PDF](../../data/raw/33_10/HCMD010486032023.pdf)

**Decision and case-specific checks.** Personal hearing/cross-examination requests unresolved; court declines factual review and grants appeal liberty. DRC-01 is mentioned without date, so added an unknown-date notice instead of empty notices. Removed duplicate 4Feb reply event and corrected paragraph 3.1 references; no section73/74 inferred.

- **Opportunity for a personal hearing: Court did not decide this complaint** (`not_decided`). Paragraph 4; source: argument; conflict/pending-Supreme-Court flag: no.
  > Personal hearing was also sought for by the petitioner placing reliance upon Asia L.P.G. Pvt. Ltd. vs State Of Karnataka And Others reported in (1997) 107 STC 29.

- **Other procedural complaint — denial of cross-examination: Court did not decide this complaint** (`not_decided`). Paragraph 4; source: argument; conflict/pending-Supreme-Court flag: no.
  > The petitioner had prayed for cross examination, placing reliance upon the following judgments of the Hon'ble Supreme Court: (i) State of Kerala Vs K.T.Shaduli Grocery Dealer reported in (1977) 39 STC 478, (ii) T.M.Rajaganapathi Traders VS. Commercial Tax Officer, Salem reported in (2005) 142 STC 130

**Outcome:** `disposed`; sent back to the tax authority: no. Paragraph 10:

> In view thereof, the challenge to the order of assessment stands rejected.

**Changes from the previous review:** `facts.document_contents[1].para`, `facts.document_contents[2].para`, `facts.document_contents[3].para`, `facts.events (entries changed)`, `facts.notices (entries changed)`.

<a id="case-odhc010248322026"></a>
### 25. ODHC010248322026 — Reviewed

WP(C)/11162/2026 of JANARDAN PANDA Vs THE COMMISSIONER COMMERCIAL TAX AND GST, ODISHA

[Annotation](../../data/gold/annotations/r3/ODHC010248322026.json) · [Judgment PDF](../../data/raw/21_11/ODHC010248322026.pdf)

**Decision and case-specific checks.** All three findings are explicit in 6.1-6.3: no hearing, ignored reply, no reasons for discarding it. SCN, reply, original assessment and rectification dates are supported; no hearing date inferred from demand for a hearing.

- **Opportunity for a personal hearing: Court accepted this complaint** (`defect_found`). Paragraph 6; source: court; conflict/pending-Supreme-Court flag: no.
  > Ergo, the order dated 26th December, 2025 and 6th January, 2026 cannot be held to be tenable in the eye of law for want of affording an opportunity of hearing to the petitioner and non- consideration of reply to show cause notice.

- **Failure to consider the taxpayer’s reply: Court accepted this complaint** (`defect_found`). Paragraph 6; source: court; conflict/pending-Supreme-Court flag: no.
  > Ergo, the order dated 26th December, 2025 and 6th January, 2026 cannot be held to be tenable in the eye of law for want of affording an opportunity of hearing to the petitioner and non- consideration of reply to show cause notice.

- **Order without adequate reasons: Court accepted this complaint** (`defect_found`). Paragraph 6; source: court; conflict/pending-Supreme-Court flag: no.
  > The points raised by way of reply to show cause notice does not find place in the order impugned; as such the orders of the adjudicating authority smacks arbitrariness.

**Outcome:** `disposed`; sent back to the tax authority: yes. Paragraph 7:

> In the result, the writ petition stands disposed of with the above observation and direction.

**Changes from the previous review:** No substantive field changes; independently rechecked..

<a id="case-dlhc010211512025"></a>
### 26. DLHC010211512025 — Reviewed

W.P.(C)/4897/2025 of SHRI KRISHNA INDUSTRIES THROUGH IT PROPRIETOR PROP MOHAN LAL Vs COMMISSIONER OF CENTRAL GOODS AND SERVICES TAX AND ORS

[Annotation](../../data/gold/annotations/r3/DLHC010211512025.json) · [Judgment PDF](../../data/raw/7_26/DLHC010211512025.pdf)

**Decision and case-specific checks.** Added missing non-supply-of-documents and Central-demand-overlap complaints, both not_decided (34,38-40). State/Central jurisdiction objection expressly rejected (32,42), although appellate reconsideration remains open. Two Central SCNs and orders retained in events; single order field selects 31 January, with 10 January preserved separately. Earlier State FY not automatically copied into Central facts.

- **Other procedural complaint — bar under section 6(2)(b) due to prior state proceedings: Court rejected this complaint** (`defect_rejected`). Paragraph 32; source: court; conflict/pending-Supreme-Court flag: no.
  > This Court is, therefore, unable to accept the contention of the Petitioner that the proceedings initiated by the Central GST authorities under Section 74 are, on the material placed before this Court, ex facie barred by Section 6(2)(b) of the CGST Act.

- **Failure to consider the taxpayer’s reply: Court did not decide this complaint** (`not_decided`). Paragraph 34; source: court; conflict/pending-Supreme-Court flag: no.
  > These objections essentially require examination of the adjudication record.

- **Order without adequate reasons: Court did not decide this complaint** (`not_decided`). Paragraph 34; source: court; conflict/pending-Supreme-Court flag: no.
  > These objections essentially require examination of the adjudication record.

- **Basis for alleging fraud/suppression under section 74: Court did not decide this complaint** (`not_decided`). Paragraph 40; source: court; conflict/pending-Supreme-Court flag: no.
  > The same can appropriately be urged before the appellate authority, which is competent to examine the material relied upon by the Department as well as the defence raised by the Petitioner.

- **Other procedural complaint — non-supply of relied-upon investigation material: Court did not decide this complaint** (`not_decided`). Paragraph 34; source: court; conflict/pending-Supreme-Court flag: no.
  > Likewise, the question whether the relied-upon material was duly supplied and whether the adjudicating authorities correctly dealt with the defence raised by the Petitioner can be examined in the statutory appellate proceedings.

- **Other procedural complaint — overlapping demands in the two Central proceedings: Court did not decide this complaint** (`not_decided`). Paragraph 38; source: court; conflict/pending-Supreme-Court flag: no.
  > Whether any liability has, in fact, been duplicated or whether the two proceedings concern identical transactions is a matter which would require examination of the respective Show Cause Notices and adjudication records.

**Outcome:** `dismissed`; sent back to the tax authority: no. Paragraph 44:

> In view of the aforesaid discussion, the present Writ Petition is devoid of merit and is, accordingly, dismissed.

**Changes from the previous review:** `findings.defects_argued (entries changed)`.

<a id="case-hcma010983962024"></a>
### 27. HCMA010983962024 — Reviewed

WP/15307/2024 of MANDARINA APARTMNT OWNERS WELFARE Vs COMMERCIAL TAX OFFICER

[Annotation](../../data/gold/annotations/r3/HCMA010983962024.json) · [Judgment PDF](../../data/raw/33_10/HCMA010983962024.pdf)

**Decision and case-specific checks.** Corrected cross-petition contamination: this CNR is Mandarina, WP15307, not Gani Fashion WP15330. Removed reply-not-considered defect from the companion petition. Retained rejection of ASMT-10 prerequisite and added Mandarina portal-service complaint as not_decided. Own FY2018-19, SCN28Dec2023 and order11Apr2024 retained; conditional remand applies under 20(i).

- **Other procedural complaint — non-issuance of Form GST ASMT-10 notice under Section 61: Court rejected this complaint** (`defect_rejected`). Paragraph 17; source: court; conflict/pending-Supreme-Court flag: no.
  > On closely examining both Sections 61 and Section 73, I find no indication in either provision that scrutiny of returns and the issuance of notice in Form ASMT-10 constitute a mandatory pre-requisite for adjudication even in cases where returns were scrutinized.

- **Proper delivery of notice: Court did not decide this complaint** (`not_decided`). Paragraph 18; source: court; conflict/pending-Supreme-Court flag: no.
  > Since the petitioner asserted that such failure to participate was on account of not being aware of proceedings, the interest of justice warrants that an opportunity be provided to the petitioner to contest the tax demand on merits by putting the petitioner on terms.

**Outcome:** `disposed`; sent back to the tax authority: yes. Paragraph 20:

> In the above facts and circumstances, these writ petitions are disposed of with the following directions

**Changes from the previous review:** `findings.defects_argued[1].finding`, `findings.defects_argued[1].para`, `findings.defects_argued[1].quote`, `findings.defects_argued[1].type`.

<a id="case-dlhc010251412025"></a>
### 28. DLHC010251412025 — Reviewed

W.P.(C)/5658/2025 of M/S SHRI BALAJI PLASTIC Vs ADDITIONAL COMMISSIONER, CGST, DELHI NORTH

[Annotation](../../data/gold/annotations/r3/DLHC010251412025.json) · [Judgment PDF](../../data/raw/7_26/DLHC010251412025.pdf)

**Decision and case-specific checks.** Consolidated-notice objection rejected by this court’s adoption in paragraph 5; appeal liberty is not remand. Removed section 74 from facts because its quotation belongs to Ambika Traders, discusses both sections 73 and 74, and does not identify the provision of this petitioner’s notice. No conflict or pending Supreme Court challenge is mentioned here, so contested remains false.

- **Combining several financial years in one notice: Court rejected this complaint** (`defect_rejected`). Paragraph 5; source: court; conflict/pending-Supreme-Court flag: no.
  > The above decision has thus, decided the issue of consolidated notice for multiple years.

**Outcome:** `disposed`; sent back to the tax authority: no. Paragraph 9:

> Accordingly, the present petition is disposed of with liberty given to the Petitioner to file an appeal under Section 107 of the Central Goods and Service Tax Act, 2017, before the Appellate Authority by 30th September, 2025, along with the requisite pre-deposit.

**Changes from the previous review:** `facts.provision.para`, `facts.provision.quote`, `facts.provision.value`.

<a id="case-hcma012251042024"></a>
### 29. HCMA012251042024 — Audited; adjudication needed

WP/36706/2024 of R A Metal Finishers Private Limited Vs THE STATE TAX OFFICER

[Annotation](../../data/gold/annotations/r3/HCMA012251042024.json) · [Judgment PDF](../../data/raw/33_10/HCMA012251042024.pdf)

**Decision and case-specific checks.** Court expressly finds ignored reconciliation and one-line non-speaking order in 5; ASMT-10 objection left unanswered. DRC-01 does not prove summary-only. Recorded both 30 May notice recital and 31 May summary described by court; uncertain whether distinct documents or date inconsistency, for adjudication.

- **Failure to consider the taxpayer’s reply: Court accepted this complaint** (`defect_found`). Paragraph 5; source: court; conflict/pending-Supreme-Court flag: no.
  > This reconciliation statement has not been taken note of by the respondent.

- **Order without adequate reasons: Court accepted this complaint** (`defect_found`). Paragraph 5; source: court; conflict/pending-Supreme-Court flag: no.
  > The impugned order is a one line non-speaking order.

- **Other procedural complaint — Issued SCN without serving FORM GST ASMT-10: Court did not decide this complaint** (`not_decided`). Paragraph 2; source: argument; conflict/pending-Supreme-Court flag: no.
  > The petitioner would submit that without serving an intimation in FORM GSTASMT-10, the respondent has directly issued a show cause notice in FORM GRT DRC-01 dated 30.05.2024.

**Outcome:** `allowed`; sent back to the tax authority: yes. Paragraph 6:

> Therefore, the Writ Petition is allowed, the impugned order is set aside and the matter is remitted back to the respondent to consider the afresh the demand in the show cause notice and the reply.

**Adjudication:** provisional best answer recorded above; do not treat it as approved gold until the uncertainty in the decision note is resolved.

**Changes from the previous review:** `facts.notices (entries changed)`.

<a id="case-brhc010164702023"></a>
### 30. BRHC010164702023 — Excluded from this dataset

CWJC/3390/2023 of M/S Singh Caterers and Vendors Vs Directorate General of GST Intelligence (Govt. of India)

[Annotation](../../data/gold/annotations/r3/BRHC010164702023.json) · [Judgment PDF](../../data/raw/10_8/BRHC010164702023.pdf)

**Decision and case-specific checks.** Scope verified from prayer, demand and disposition: railway catering licence service-tax demand under Finance Act1994 section73, preserved by CGST section174, not a CGST demand.

No procedural labels are approved for gold: the underlying proceeding fails the scope rule.
**Changes from the previous review:** `facts.provision.para`, `facts.provision.quote`, `facts.provision.value`.

<a id="case-uphc020029552026"></a>
### 31. UPHC020029552026 — Reviewed

WTAX/199/2026 of M/S AJAY KISHORE ZARI COLLECTION THRU. PROPRIETOR SHRI MANISH KUMAR JAIN VS STATE OF U.P. THRU. COMMISSIONER  STATE GOODS AND SERVICES TAX  LKO. AND 2 OTHERS

[Annotation](../../data/gold/annotations/r3/UPHC020029552026.json) · [Judgment PDF](../../data/raw/9_13/UPHC020029552026.pdf)

**Decision and case-specific checks.** Hearing defect supported by the State admission and this court’s express application of Mahaveer Trading; allowed and remanded. Dates and section taken from this petitioner’s paragraph 2, not the quoted precedent. Notice dates and financial years are unstated.

- **Opportunity for a personal hearing: Court accepted this complaint** (`defect_found`). Paragraph 7; source: court; conflict/pending-Supreme-Court flag: no.
  > Since the aforesaid dictum is applicable in the present facts and circumstances, accordingly, the impugned orders cannot be sustained and the orders dated 05.02.2025 & 28.01.2026 are accordingly quashed.

**Outcome:** `allowed`; sent back to the tax authority: yes. Paragraph 8:

> With the aforesaid, the present petition is allowed.

**Changes from the previous review:** No substantive field changes; independently rechecked..

<a id="case-uphc020125162026"></a>
### 32. UPHC020125162026 — Audited; adjudication needed

WTAX/346/2026 of M/S KAUSHAL TRADERS THRU. PROPRIETORS RAM MILAN KAUSHAL VS STATE OF U.P. THRU. ADDL. CHIEF SECY. COMMERCIAL TAX DEPTT. LKO AND 2 OTHERS

[Annotation](../../data/gold/annotations/r3/UPHC020125162026.json) · [Judgment PDF](../../data/raw/9_13/UPHC020125162026.pdf)

**Decision and case-specific checks.** Hearing defect supported by the State admission and this court’s express application of Mahaveer Trading; allowed and remanded. Dates and section taken from this petitioner’s paragraph 2, not the quoted precedent. Notice dates and financial years are unstated. Source itself dates the appeal 10 February 2025 before the assessment of 29 September 2025; retained the printed dates without inventing a correction. Chronology requires adjudication.

- **Opportunity for a personal hearing: Court accepted this complaint** (`defect_found`). Paragraph 7; source: court; conflict/pending-Supreme-Court flag: no.
  > Since the aforesaid dictum is applicable in the present facts and circumstances, accordingly, the impugned orders cannot be sustained and the orders dated 29.09.2025 & 10.02.2025 are accordingly quashed.

**Outcome:** `allowed`; sent back to the tax authority: yes. Paragraph 9:

> Matter is remanded to the assessing authority to pass fresh order after giving an opportunity of hearing to the petitioner.

**Adjudication:** provisional best answer recorded above; do not treat it as approved gold until the uncertainty in the decision note is resolved.

**Changes from the previous review:** No substantive field changes; independently rechecked..

<a id="case-uphc021037432025"></a>
### 33. UPHC021037432025 — Reviewed

WTAX/1734/2025 of M/S JITENDRA  KUMAR  SRIVASTAVA  PROP.  SRI JITENDRA  KUMAR  SRIVASTAVA VS STATE OF U.P. THRU. PRIN. SECY. DEPTT.  OF COMMERCIAL TAX LKO. AND 2 OTHERS

[Annotation](../../data/gold/annotations/r3/UPHC021037432025.json) · [Judgment PDF](../../data/raw/9_13/UPHC021037432025.pdf)

**Decision and case-specific checks.** Hearing defect supported by the State admission and this court’s express application of Mahaveer Trading; allowed and remanded. Dates and section taken from this petitioner’s paragraph 2, not the quoted precedent. Notice dates and financial years are unstated.

- **Opportunity for a personal hearing: Court accepted this complaint** (`defect_found`). Paragraph 6; source: court; conflict/pending-Supreme-Court flag: no.
  > Since the aforesaid dictum is applicable in the present facts and circumstances, accordingly, the impugned orders cannot be sustained and the orders dated 19.02.2024 & 14.10.2025 are accordingly quashed.

**Outcome:** `allowed`; sent back to the tax authority: yes. Paragraph 8:

> Matter is remanded to the assessing authority to pass fresh order after giving an opportunity of hearing to the petitioner.

**Changes from the previous review:** No substantive field changes; independently rechecked..

<a id="case-hcma010739202024"></a>
### 34. HCMA010739202024 — Audited; adjudication needed

WP/11461/2024 of TVL.KCP INFRA LIMITED, Vs THE STATE TAX OFFICER,

[Annotation](../../data/gold/annotations/r3/HCMA010739202024.json) · [Judgment PDF](../../data/raw/33_10/HCMA010739202024.pdf)

**Decision and case-specific checks.** Inspection reply ignored was argued; court grants conditional opportunity despite taxpayer missing SCN response/hearing, without explicit fault finding. Retain not_decided, flag adjudication. Added actual inspection-reply date. Section 73/74 is not stated, so provision remains null.

- **Failure to consider the taxpayer’s reply: Court did not decide this complaint** (`not_decided`). Paragraph 6; source: court; conflict/pending-Supreme-Court flag: no.
  > Although the petitioner should have responded to the intimation and show cause notice and availed of the opportunity of personal hearing, in the above facts and circumstances, the impugned assessment order calls for interference albeit by putting the petitioner on terms.

**Outcome:** `disposed`; sent back to the tax authority: yes. Paragraph 7:

> For reasons set out above, the impugned assessment order is quashed subject to the condition that the petitioner remits a sum of Rs.15,00,000/- as agreed to towards the disputed tax demand within a maximum period of two weeks from the date of receipt of a copy of this order.

**Adjudication:** provisional best answer recorded above; do not treat it as approved gold until the uncertainty in the decision note is resolved.

**Changes from the previous review:** `facts.events[1].date`, `facts.events[1].para`, `facts.events[1].quote`.

<a id="case-hcma010998472024"></a>
### 35. HCMA010998472024 — Reviewed

WP/15599/2024 of M/s P R Earth And Contracts Vs The State Tax Officer

[Annotation](../../data/gold/annotations/r3/HCMA010998472024.json) · [Judgment PDF](../../data/raw/33_10/HCMA010998472024.pdf)

**Decision and case-specific checks.** Court says courier likely had not arrived; no established ignored reply. Retained not_decided. Distinguished reply document date from filing/receipt; retained dispatch date separately.

- **Failure to consider the taxpayer’s reply: Court did not decide this complaint** (`not_decided`). Paragraph 5; source: court; conflict/pending-Supreme-Court flag: no.
  > It is likely that the courier was not received as on the date of issuance of the impugned assessment order.

**Outcome:** `disposed`; sent back to the tax authority: yes. Paragraph 7:

> The writ petition is disposed of on the above terms without any order as to costs.

**Changes from the previous review:** `facts.events[4].date`, `facts.events[4].para`, `facts.events[4].quote`, `facts.events[4].type`, `facts.events[5].date`, `facts.events[5].para`, `facts.events[5].quote`, `facts.events[5].type`, `facts.events[6].date`, `facts.events[6].para`, `facts.events[6].quote`, `facts.events[6].type`, `findings.defects_argued[0].para`, `findings.defects_argued[0].quote`, `findings.defects_argued[0].quote_source`.

<a id="case-hcma011645762024"></a>
### 36. HCMA011645762024 — Audited; adjudication needed

WP/26335/2024 of R.MOHANRAJ AND CO Vs COMMERCIAL TAX OFFICER

[Annotation](../../data/gold/annotations/r3/HCMA011645762024.json) · [Judgment PDF](../../data/raw/33_10/HCMA011645762024.pdf)

**Decision and case-specific checks.** Conditional interest-of-justice reconsideration: retain hearing/service not_decided, with court narrative ambiguity flagged. DRC-01 mention alone does not establish summary-only. Prayer distinguishes assessment 20 April from DRC-07 summary 24 April; corrected order date and removed undated event.

- **Opportunity for a personal hearing: Court did not decide this complaint** (`not_decided`). Paragraph 4; source: argument; conflict/pending-Supreme-Court flag: no.
  > However, the impugned order was passed without providing the petitioner with an opportunity for a personal hearing.

- **Proper delivery of notice: Court did not decide this complaint** (`not_decided`). Paragraph 4; source: argument; conflict/pending-Supreme-Court flag: no.
  > The petitioner was unaware of the notices issued by the respondent, as they were only uploaded on the GST common portal and were not physically served, thereby depriving the petitioner of an effective opportunity to respond to the show cause notice or to correct the clerical mistake in the GSTR-9 filing.

**Outcome:** `disposed`; sent back to the tax authority: yes. Paragraph 5:

> With the above directions, the writ petition is disposed of.

**Adjudication:** provisional best answer recorded above; do not treat it as approved gold until the uncertainty in the decision note is resolved.

**Changes from the previous review:** `facts.events[0].date`, `facts.events[0].quote`, `facts.events[0].type`, `facts.events[1].date`, `facts.events[1].quote`, `facts.events[1].type`, `facts.events[2].date`, `facts.events[3].date`, `facts.events[3].quote`, `facts.events[3].type`, `facts.events[4].date`, `facts.events[4].para`, `facts.events[4].quote`, `facts.notices[0].summary_only.para`, `facts.notices[0].summary_only.quote`, `facts.notices[0].summary_only.value`, `facts.order.date.para`, `facts.order.date.quote`, `facts.order.date.value`.

<a id="case-hcma010179022025"></a>
### 37. HCMA010179022025 — Reviewed

WP/3308/2025 of TVL MARK METRO Vs State Tax Officer

[Annotation](../../data/gold/annotations/r3/HCMA010179022025.json) · [Judgment PDF](../../data/raw/33_10/HCMA010179022025.pdf)

**Decision and case-specific checks.** Reply ignored is an express court finding in paragraphs 6–7, corroborated by the respondent concession. Both assessment and rectification rejection set aside; remand explicit. Corrected dated assessment event to a quotation that actually supplies its date. DRC-01 does not establish summary-only; section unstated.

- **Failure to consider the taxpayer’s reply: Court accepted this complaint** (`defect_found`). Paragraph 7; source: court; conflict/pending-Supreme-Court flag: no.
  > In this case, the impugned assessment order was passed without considering the reply filed by the petitioner, which is a clear violation of principles of natural justice and hence, the said assessment order is liable to be set aside.

**Outcome:** `disposed`; sent back to the tax authority: yes. Paragraph 8:

> With the above directions, these writ petitions are disposed of.

**Changes from the previous review:** `facts.events[2].para`, `facts.events[2].quote`.

<a id="case-dlhc010778732025"></a>
### 38. DLHC010778732025 — Reviewed

W.P.(C)/15643/2025 of MS MARKEX BRANDING SOLUTIONS PVT LTD Vs THE COMMISSIONER OF DELHI GOODS AND SERVICES TAX & ORS.

[Annotation](../../data/gold/annotations/r3/DLHC010778732025.json) · [Judgment PDF](../../data/raw/7_26/DLHC010778732025.pdf)

**Decision and case-specific checks.** Changed hearing to defect_found: paragraph 12 expressly finds no proper opportunity, consistently with Kalyr paragraph 16; costs for taxpayer non-response do not erase that express finding. Notification issue remains not_decided and contested. Removed later reminder hearing details from the earlier SCN fields; retained 5/12 August events and corrected their paragraph to actual paragraph 9 (not extractor segment 11). Removed undated event. Section not imported from precedents.

- **Validity of the deadline-extension notifications: Court did not decide this complaint** (`not_decided`). Paragraph 16; source: court; conflict/pending-Supreme-Court flag: yes.
  > However, it is made clear that the issue in respect of the validity of the impugned notifications is left open.

- **Opportunity for a personal hearing: Court accepted this complaint** (`defect_found`). Paragraph 12; source: court; conflict/pending-Supreme-Court flag: no.
  > Under such circumstances, considering the fact that the Petitioner did not get a proper opportunity to be heard and no reply to the impugned SCN has been filed by the Petitioner, the matter deserves to be remanded to the concerned Adjudicating Authority.

**Outcome:** `disposed`; sent back to the tax authority: yes. Paragraph 13:

> Accordingly, the impugned order is set aside subject to the Petitioner depositing a sum of Rs.25,000/- with the Sales Tax Bar Association, as costs for delay.

**Changes from the previous review:** `facts.events (entries changed)`, `facts.notices[0].hearing_date.para`, `facts.notices[0].hearing_date.quote`, `facts.notices[0].hearing_date.value`, `facts.notices[0].hearing_date_given.para`, `facts.notices[0].hearing_date_given.quote`, `facts.notices[0].hearing_date_given.value`, `findings.defects_argued[1].finding`.

<a id="case-dlhc010507842025"></a>
### 39. DLHC010507842025 — Audited; adjudication needed

W.P.(C)/11102/2025 of M/S DHRL INDIA SERVICES PVT LTD Vs THE SALES TAX OFFICER CLASS II/ AVATO

[Annotation](../../data/gold/annotations/r3/DLHC010507842025.json) · [Judgment PDF](../../data/raw/7_26/DLHC010507842025.pdf)

**Decision and case-specific checks.** Paragraph 9 expressly finds no opportunity to reply or attend hearing; changed hearing to defect_found despite appeal-only relief (an explicit finding controls over disposition). No remand. Source inconsistencies remain: paragraph 3 says SCN 23 May, paragraphs 4/6 say 28 May; retained the latter detailed account. Reminder 8 January 2025 postdates order 29 August 2024. Demand differs between paragraphs 4 and 9. These are source conflicts, not corrected by inference; require adjudication.

- **Opportunity for a personal hearing: Court accepted this complaint** (`defect_found`). Paragraph 9; source: court; conflict/pending-Supreme-Court flag: no.
  > This Court notes that, for whatever reasons, the Petitioner was not afforded an opportunity to file a reply or even appear for the hearing, yet a demand to the tune of Rs. 88,474/- has been raised against the Petitioner.

**Outcome:** `disposed`; sent back to the tax authority: no. Paragraph 12:

> The petition is disposed of in the above terms, along with pending application(s), if any.

**Adjudication:** provisional best answer recorded above; do not treat it as approved gold until the uncertainty in the decision note is resolved.

**Changes from the previous review:** `findings.defects_argued[0].finding`, `findings.defects_argued[0].para`, `findings.defects_argued[0].quote`, `findings.defects_argued[0].quote_source`.

## Subsequent review of the seven second assignments

These reviews used AI at r3’s explicit request. Their annotations are useful as case reviews, but they are not independent observations for reviewer-agreement scoring.

| Queue | Case | Saved status | Key decision |
|---|---|---|---|
| 5 | DLHC010742252025 | reviewed | Additional Notices objection rejected; lack of proper opportunity found; notification validity open; remanded with costs. |
| 8 | HCMA011201082025 | reviewed | Hearing defect expressly found after reply; order set aside and remanded. |
| 11 | HCMD010052922025 | needs_fix | Failure to determine tax and follow circular found; section 73/74 scope uncertain because judgment says section 74 was not invoked. |
| 14 | UPHC020961672025 | out_of_scope | Own assessment described under section 75 only; section 73/74 demand unestablished, pending scope adjudication. |
| 17 | UPHC021037272025 | reviewed | Own order under section 74(9); hearing defect found and remanded. |
| 20 | HCMA010285922025 | reviewed | Filed reply ignored; remanded. Later hearing direction is the remedy. |
| 23 | DLHC010599232024 | reviewed | DRC-01A argument and notification validity left undecided; further opportunity given; prior ASMT-11 is not a reply to the SCN. |
