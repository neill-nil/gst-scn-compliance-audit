# Role 1 pilot drafts — for review

Drafted by Claude in the draft schema (`docs/team_plan/contracts.md`). Every quote was checked by
`python -m src.prefill.verify_quotes` and appears word for word in the judgment (60/60).

**How to review:** open the PDF next to this page. For each line, tick it if right, or write the correction
after it. Paragraph numbers are the judgment's own. `—` means the judgment doesn't say.

**What to check most carefully:** the findings (found / rejected / not decided). Those are the answer key.

## 1. Allahabad — Writ Tax No. 526 of 2025 (decided 2025-02-19)

PDF: [`UPHC010748612025.pdf`](../../raw/9_13/UPHC010748612025.pdf) · JSON: [`UPHC010748612025.json`](UPHC010748612025.json)

| Field | Draft value | OK? |
|---|---|---|
| Section | 73 | [ ] |
| Tax period | 2018-04 to 2019-03 (FY 2018-19) | [ ] |
| Officer | Deputy Commissioner, State Tax, Mirzapur (state) | [ ] |
| Notice | form —, dated 2023-12-23, reply due 2024-01-20 | [ ] |
| Hearing in notice | 2024-01-20 | [ ] |
| How served / signed | — / — | [ ] |
| Order | dated 2024-04-30, amount — | [ ] |

**Timeline**

- [ ] — · `other` · s.61 scrutiny notice; reply due 22.02.2023; hearing denied in that notice (para 2)
- [ ] 2023-12-23 · `scn_issued` · s.73(1) notice, ITC difference (para 3)
- [ ] 2024-01-18 · `reply_filed` · reply on reverse charge mechanism with invoices (para 4)
- [ ] 2024-04-30 · `order_passed` · s.73(9) order, reply partly accepted (para 5)
- [ ] 2024-10-09 · `other` · s.161 rectification application rejected (para 6)

**Defects argued → court's finding** (the answer key)

| Defect | Finding | Contested | Para | Court's words |
|---|---|---|---|---|
| `hearing_75_4` | **defect_found** | no | 12 | “This Court has repeatedly frowned on the action of the respondents in fixing identical date of reply and date of hearing” |
| `reply_not_considered` | **defect_found** | no | 13 | “the respondent no. 2 did not deal with the said aspect at all and a wholly cursory finding” |
| `non_speaking_order` | **defect_found** | no | 14 | “Such a cursory disposal of the objection raised in reply to the show cause notice cannot be countenanced” |
| `other_procedural` | **not_decided** | no | 16 | “rejection of the said application under Section 161 of the Act loses its significance” |

**Outcome:** allowed, sent back to the officer (para 18) [ ]

**Notes and schema questions:** Schema gaps: no event type for the s.61 scrutiny notice; 'hearing on the same day reply is due' could be its own flag. Para 17 says the order was under 'Section 79(3)' but paras 1 and 5 say s.73(9): judgment typo, recorded as s.73(9). Para 13 quotes the officer's order in Hindi; text extraction garbles it, so it cannot be quoted.

---

## 2. Allahabad — Writ Tax No. 1479 of 2025 (decided 2025-12-04)

PDF: [`UPHC020953002025.pdf`](../../raw/9_13/UPHC020953002025.pdf) · JSON: [`UPHC020953002025.json`](UPHC020953002025.json)

| Field | Draft value | OK? |
|---|---|---|
| Section | 73 | [ ] |
| Tax period | — to — (FY —) | [ ] |
| Officer | — (state) | [ ] |
| Notice | form —, dated —, reply due — | [ ] |
| Hearing in notice | — | [ ] |
| How served / signed | — / — | [ ] |
| Order | dated 2024-04-29, amount — | [ ] |

**Timeline**

- [ ] 2024-04-29 · `order_passed` · s.73 order (para 2)
- [ ] 2025-04-01 · `other` · appeal dismissed as filed beyond limitation (para 2)

**Defects argued → court's finding** (the answer key)

| Defect | Finding | Contested | Para | Court's words |
|---|---|---|---|---|
| `hearing_75_4` | **defect_found** | no | 6 | “the impugned orders cannot be sustained and the orders dated 29.04.2024 & 01.04.2025 are accordingly quashed” |
| `demand_beyond_scn` | **not_decided** | no | 3 | “the order is also violative of Section 75(7) of the Act of 2017” |

**Outcome:** allowed, sent back to the officer (para 8) [ ]

**Notes and schema questions:** Almost no notice facts are stated: no notice date, tax period or amount. The State's own counsel admits no hearing date was fixed (para 4). The finding (para 6) applies a precedent (Mahaveer Trading, quoted in para 5) to this case. The s.75(7) argument (para 3) is never ruled on, so not_decided; the quote is the argument, not a finding. Schema gap: the appellate order (appeal dismissed as time-barred) was quashed too; no field for it. Paras 6-8 are the court's own but the splitter merges them into para 5 (they start mid-line after the quoted precedent).

---

## 3. Bombay — Writ Petition No. 8397 of 2025 (decided 2026-01-17)

PDF: [`HCBM040404632025.pdf`](../../raw/27_1/HCBM040404632025.pdf) · JSON: [`HCBM040404632025.json`](HCBM040404632025.json)

| Field | Draft value | OK? |
|---|---|---|
| Section | 74 | [ ] |
| Tax period | 2018-04 to 2024-03 (FY 2018-19, 2019-20, 2020-21, 2021-22, 2022-23, 2023-24) | [ ] |
| Officer | Joint Commissioner, CGST & Central Excise, Nagpur-II (order); respondents 3 and 4 (notices) (central) | [ ] |
| Notice | form —, dated 2025-06-29, reply due — | [ ] |
| Hearing in notice | — | [ ] |
| How served / signed | — / — | [ ] |
| Order | dated 2025-09-26, amount — | [ ] |

**Timeline**

- [ ] 2025-06-29 · `scn_issued` · first s.74 notice, FY 2018-19 to 2023-24, by respondent 4 (para 2)
- [ ] 2025-09-18 · `scn_issued` · second s.74 notice, FY 2019-20 to 2023-24, by respondent 3 (para 2)
- [ ] 2025-09-26 · `order_passed` · order by respondent 1 (para 2)

**Defects argued → court's finding** (the answer key)

| Defect | Finding | Contested | Para | Court's words |
|---|---|---|---|---|
| `consolidated_scn` | **defect_found** | yes | 11 | “The argument of Counsel for respondent no.1, therefore, cannot be accepted.” |

**Outcome:** partly_allowed (para 14) [ ]

**Notes and schema questions:** Contested: the court notes the Delhi HC (Mathur Polymers) allows consolidated notices and the Supreme Court dismissed the SLP in limine; Bombay follows its own Milroc / Rite Water line (paras 6-11). Schema gaps: TWO show cause notices from two different officers; the schema has one notice object (first one recorded, second in events). Outcome is 'partly allowed' with notices and order quashed and liberty to re-issue, not a remand. Odd fact not argued: the order (26/9/2025) came 8 days after the second notice (18/9/2025). Bombay numbers paragraphs '2]', first paragraph is just 'Heard.'

---

## 4. Calcutta — WPA 991 of 2026 (decided 2026-09-02)

PDF: [`WBCHCJ0026132026.pdf`](../../raw/19_16/WBCHCJ0026132026.pdf) · JSON: [`WBCHCJ0026132026.json`](WBCHCJ0026132026.json)

| Field | Draft value | OK? |
|---|---|---|
| Section | 74 | [ ] |
| Tax period | 2020-01 to 2023-11 (FY 2019-20, 2020-21, 2021-22, 2022-23, 2023-24) | [ ] |
| Officer | Additional Commissioner, CGST & Central Excise, Siliguri Commissionerate (central) | [ ] |
| Notice | form DRC-01, dated 2025-08-14, reply due — | [ ] |
| Hearing in notice | — | [ ] |
| How served / signed | portal_unspecified / — | [ ] |
| Order | dated 2026-03-27, amount — | [ ] |

**Timeline**

- [ ] — · `other` · pre-show-cause notice in Form DRC-01A; hearing record notes invalid signatures (para 8)
- [ ] 2025-08-14 · `scn_uploaded` · DRC-01 summaries uploaded on portal (para 8)
- [ ] 2026-03-17 · `other` · earlier writ (WPA 11 of 2026) withdrawn; High Court allowed a belated reply (para 6)
- [ ] — · `hearing_attended` · heard, represented by an advocate (para 9)
- [ ] 2026-03-27 · `order_passed` · s.74 order (para 6)

**Defects argued → court's finding** (the answer key)

| Defect | Finding | Contested | Para | Court's words |
|---|---|---|---|---|
| `signature` | **not_decided** | no | 8 | “there is no scope for this Court to make such a determination in absence of the records being produced” |
| `consolidated_scn` | **defect_rejected** | no | 8 | “There is no clubbing of periods in the summary of show-cause in From DRC 01” |
| `other_procedural` | **defect_rejected** | no | 9 | “it is an admitted position that the authority who heard the petitioner was a proper officer within the meaning of the said Act” |
| `non_speaking_order` | **defect_rejected** | no | 9 | “the order cannot be said to be non- speaking” |
| `reply_not_considered` | **not_decided** | no | 9 | “these are all disputed factual issues” |
| `section_74_ingredients` | **not_decided** | no | 3 | “no specific taxable event or essential ingredients to invoke Section 74 of the said Act has been disclosed” |

**Outcome:** dismissed (para 12) [ ]

**Notes and schema questions:** Dismissed mainly because an appeal was available and the petitioner refused the mandatory pre-deposit (paras 10-12), yet the judge still comments on several defects. Hard calls for the meeting: (1) non-speaking rejected only 'prima facie' - is that defect_rejected or not_decided? (2) consolidated notice rejected here but found in the Bombay case (AR Traders): should 'contested' come from the judgment's own text or from our global list? (3) the signature argument targets the DRC-01A pre-notice and DRC-01 summary, not the order. The s.74 ingredients argument (para 3) gets no ruling; quote is the argument.

---

## 5. Delhi — W.P.(C) 2436/2025 (decided 2025-07-14)

PDF: [`DLHC010095492025.pdf`](../../raw/7_26/DLHC010095492025.pdf) · JSON: [`DLHC010095492025.json`](DLHC010095492025.json)

| Field | Draft value | OK? |
|---|---|---|
| Section | 73 | [ ] |
| Tax period | — to — (FY —) | [ ] |
| Officer | Sales Tax Officer Class II/AVATO, Ward 71, Zone 6, Delhi (state) | [ ] |
| Notice | form —, dated 2023-09-22, reply due — | [ ] |
| Hearing in notice | — | [ ] |
| How served / signed | portal_additional_notices_tab / — | [ ] |
| Order | dated 2023-12-23, amount 10457420 | [ ] |

**Timeline**

- [ ] 2023-09-22 · `scn_issued` · s.73 notice (para 2)
- [ ] — · `hearing_missed` · no reply filed, hearing not availed, order ex parte (para 2)
- [ ] 2023-12-23 · `order_passed` · ex parte demand order (para 2)

**Defects argued → court's finding** (the answer key)

| Defect | Finding | Contested | Para | Court's words |
|---|---|---|---|---|
| `service_169` | **defect_found** | no | 6 | “much prior to the time when this issue was rectified by the Department, it is deemed appropriate to set aside the impugned order” |

**Outcome:** disposed, sent back to the officer (para 6) [ ]

**Notes and schema questions:** Service mode is the petitioner's allegation (para 4) which the court accepts by applying earlier rulings (para 5, quoted, and para 6). Para 5 quotes other judgments (Neelgiri Machinery, which quotes ACE Cardiopathy and others): ignore their facts. Para 3 quotes the court's own earlier order in this case asking when the petitioner learnt of the order. Disposition 'disposed' but in substance the taxpayer won (order set aside, remanded).

---
