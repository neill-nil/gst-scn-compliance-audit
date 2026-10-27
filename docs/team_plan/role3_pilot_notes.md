# Role 3 pilot notes (rows 11–15)

Read on 2026-10-27 from the SHA-256-checked eCourts PDFs fetched with
`python3 scripts/fetch_data.py --reasoned-only`. Paragraph numbers below are
the judgments' printed numbers; a prayer or party submission is **not** a
court finding. These are meeting notes, not gold labels.

| CNR | Record facts and issues | Court's finding and result | Provisions actually cited in judgment |
|---|---|---|---|
| `KAHC010212752025` (Karnataka, 2025-07-09) | FY 2017-18; SCN 2023-07-31, DRC-01 2023-08-01, adjudication order 2023-09-05, DRC-07 2023-09-06. Notice and order addressed to a proprietor who died 2018-03-18. Petitioner challenged the Central and Karnataka extension notifications and limitation (paras 1–4). | Court held proceedings against the deceased person non-est, quashed the challenged documents and remitted for fresh consideration through the legal heir (para 5). It expressly left limitation for the authority to consider; **no limitation finding** (paras 4–5). | CGST Act s.73(9), s.168A; Notification 09/2023-CT; Karnataka Notification 06/2023; Constitution arts. 226–227 (prayer). |
| `KAHC010289442026` (Karnataka, 2026-09-30) | FY 2017-18; SCN and DRC-01 2023-09-30, order 2023-12-01, DRC-07 2023-12-02. The petition challenges extension notifications and raises an input-tax-credit issue (prayer; paras 1–4). | Court held that retrospectively inserted s.16(5) applied to returns filed before 2021-11-30; quashed the order and remitted for a formal order. It **did not decide the extension-notification challenge** (paras 4–5, order). This is primarily a substantive ITC case, despite its rule-generated `limitation` pilot flag. | CGST/KGST Act s.73(9), s.16(4), s.16(5), s.168A; Notification 09/2023-CT; Karnataka Notification 06/2023 (some only in prayer). |
| `HCMA010739082025` (Madras, 2025-04-04) | Tax period 2022-11 to 2023-03; DRC-07/detailed order 2024-06-18 and rectification DRC-08/detailed order 2025-01-25. Petitioner said SCN and reminders were portal-only, no hearing, penalty rose on rectification, and about 50% was recovered (paras 2–3). | Portal upload was legally sufficient service, but the officer should have explored another s.169 mode after no response; court found no personal-hearing opportunity and set aside both orders, with a fresh hearing on remand (paras 5–7). The record does **not** establish that every portal-only notice is invalid. | GST Act s.169 and s.169(1) (court); Constitution art. 226 (prayer). |
| `HCMA011417792025` (Madras, 2025-07-09) | FY 2019-20; ASMT-10 2023-11-28, DRC-01 with annexure 2024-01-10; reply due 2024-02-10 but proposed hearing 2024-01-24; three reminders; order/DRC-07 2024-08-21; appeal 2025-02-13 rejected in APL-02 2025-03-25. Notices and order were on “View Additional Notices” tab (paras 3–6). | Court found lack of an effective opportunity to respond/hear the taxpayer, quashed both assessment and appeal-rejection orders, and remitted (paras 9–14). It said portal upload can be sufficient legal service, while urging an alternate s.169 mode after silence (paras 11–12). It did **not** expressly decide that the hearing-before-reply date alone invalidated the notice. | TNGST Act s.73 (notice/order); TNGST Act s.107 (appeal, party account); CGST Act s.169 and s.169(1) (court). |
| `HCMA011876792024` (Madras, 2024-10-22) | FY 2018-19; SCN 2023-08-30 and order/DRC-07 2024-04-23 on “Additional Notices” tab; petitioner said there was no notice or hearing (paras 1, 4). | Court found no prior notice or hearing opportunity and ordered a fresh hearing. Quashing only takes effect after payment of 10% of disputed tax (paras 7–9). The SCN's existence and the court's “no prior notice” wording need to be retained separately, not reconciled by guesswork. | CGST/TNGST Act s.73 (opening/prayer); Constitution art. 226 (prayer). |

## Feedback for the schema meeting

1. Distinguish **asserted defects** from **decided findings**. The first two
   Karnataka cases mention limitation and extension validity, but the court
   leaves those points undecided. The second is mainly about substantive ITC;
   its pilot `limitation` flag must not become a gold finding.
2. The single `notice` and `order` objects do not represent an SCN plus DRC-01
   on different dates, an order plus DRC-07, or a later DRC-08 rectification.
   Preserve document type, date, and relationships separately, or define a
   documented rule for choosing the primary dates.
3. `service_169` needs separate fields for **legal mode**, **portal location**,
   **awareness/effective opportunity**, and the court's conclusion. The Madras
   cases say portal upload can be legally sufficient, while still faulting an
   ex parte process after silence.
4. A notice-hearing date can precede the reply due date (MNT Electronics).
   Preserve both dates without automatically assigning a court finding to
   that sequence.
5. Consider how to encode a notice/order addressed to a deceased person,
   conditional quashing after a deposit, appeals quashed with the assessment,
   and multiple writ petitions decided by one judgment. These appear in the
   assigned pilots but do not fit cleanly in the draft record.
6. Preserve the applicable State GST Act and State notification alongside
   CGST references; do not silently convert a State reference to CGST.
