# Pilot reading for the schema meeting

**Before the meeting:** run `python scripts/fetch_data.py --reasoned-only` (about 1 minute), then read your cases below and fill in one note per case (template at the bottom). You don't need to know the law: you are recording what the court says, not judging it. About 10 minutes per case.

## Who reads what
| Role | Court | Case | Pages | File |
|---|---|---|---|---|
| 1 | Allahabad | Rajesh Kumar Singh (**worked example below**) | 4 | [UPHC010748612025.pdf](../../data/raw/9_13/UPHC010748612025.pdf) |
| 1 | Allahabad | Agarwal and Company | 4 | [UPHC020953002025.pdf](../../data/raw/9_13/UPHC020953002025.pdf) |
| 1 | Bombay | AR Traders | 7 | [HCBM040404632025.pdf](../../data/raw/27_1/HCBM040404632025.pdf) |
| 1 | Calcutta | Garg Enterprises | 6 | [WBCHCJ0026132026.pdf](../../data/raw/19_16/WBCHCJ0026132026.pdf) |
| 1 | Delhi | Priyanka Goyal | 4 | [DLHC010095492025.pdf](../../data/raw/7_26/DLHC010095492025.pdf) |
| 2 | Delhi | Tata Play Ltd (the proposal's example; long) | 26 | [DLHC010209162025.pdf](../../data/raw/7_26/DLHC010209162025.pdf) |
| 2 | Delhi | Nspira Management Services | 4 | [DLHC010889882024.pdf](../../data/raw/7_26/DLHC010889882024.pdf) |
| 2 | Madras | Aswath Industries | 5 | [HCMD010983492026.pdf](../../data/raw/33_10/HCMD010983492026.pdf) |
| 2 | Madras | Kalika Engineering and Constructions (tricky: may not be a real ruling) | 6 | [HCMD010841222026.pdf](../../data/raw/33_10/HCMD010841222026.pdf) |
| 3 | Delhi | Avik Polymers | 8 | [DLHC010251272025.pdf](../../data/raw/7_26/DLHC010251272025.pdf) |
| 3 | Delhi | Dev Enterprises | 8 | [DLHC010903322024.pdf](../../data/raw/7_26/DLHC010903322024.pdf) |
| 3 | Delhi | Sight and Sound India | 12 | [DLHC011072492025.pdf](../../data/raw/7_26/DLHC011072492025.pdf) |
| 3 | Karnataka | Dwarak Shamanth | 6 | [KAHC010212752025.pdf](../../data/raw/29_3/KAHC010212752025.pdf) |
| 3 | Karnataka | Shivneel Gas Sales | 8 | [KAHC010289442026.pdf](../../data/raw/29_3/KAHC010289442026.pdf) |
| 4 | Madras | Sri Rahul Transport and Earth Movers | 8 | [HCMA010739082025.pdf](../../data/raw/33_10/HCMA010739082025.pdf) |
| 4 | Madras | MNT Electronics | 11 | [HCMA011417792025.pdf](../../data/raw/33_10/HCMA011417792025.pdf) |
| 4 | Madras | Nunez Engineering Works | 7 | [HCMA011876792024.pdf](../../data/raw/33_10/HCMA011876792024.pdf) |
| 4 | Madras | Glo Shipping Logistics | 8 | [HCMA012077192024.pdf](../../data/raw/33_10/HCMA012077192024.pdf) |
| 4 | Madras | NPS Painting Contractor | 7 | [HCMA012313612024.pdf](../../data/raw/33_10/HCMA012313612024.pdf) |

## What you're reading
These are **High Court judgments**, not show cause notices. A taxpayer got a show cause notice (DRC-01) and a demand order (DRC-07), then went to the High Court saying the procedure was broken. The judge describes what happened and rules on it. We use the description as the system's input and the ruling as the answer key.

## How a judgment is laid out
1. **Top:** who vs who, the court, the judges, the date.
2. **Facts:** "The present petition has been filed…": notice, order, dates.
3. **Arguments:** "learned counsel for the petitioner submits…". Claims by each side, **not** facts.
4. **Court's reasoning:** starts at phrases like "We have considered…", "this Court is of the view…". **This is what counts.**
5. **The order** (last 1–3 paragraphs): "allowed", "set aside", "remanded", "dismissed", "disposed of".

**Shortcut:** read the last 3–4 paragraphs first (what was decided), then find where the court starts speaking, then go back to the facts at the top.

## Words you'll see
| Word | Meaning |
|---|---|
| Petitioner | The taxpayer who went to court |
| Respondent | The tax department or officer |
| SCN / DRC-01 | Show cause notice: "explain why you shouldn't pay this" |
| Impugned order / DRC-07 | The demand order being challenged |
| Section 73 / 74 | Normal tax demand / demand alleging fraud or hiding facts |
| Personal hearing | Meeting where the taxpayer explains to the officer |
| Ex parte | Decided without the taxpayer taking part |
| Set aside / quash | Cancelled |
| Remand / remit | Sent back to the officer to decide again |
| Petition allowed | Taxpayer wins (usually the order is cancelled and sent back) |
| Dismissed | Taxpayer loses |
| Disposed of | Case closed; read what the court directed |
| "Contentions kept open" | The court did not decide the point |
| "Additional Notices tab" | A GST portal tab where notices were easy to miss |

## The one trap: quoted judgments
Courts paste in long passages from *other* cases ("held as under:-", text in quotation marks). Those facts and outcomes belong to the other case. Skip them.

## Worked example: Rajesh Kumar Singh (Allahabad HC)
```
Case:            Rajesh Kumar Singh v Commissioner of Commercial Tax, Writ Tax 526/2025,
                 Allahabad HC (Chief Justice's bench), decided 19.02.2025
Section:         73                                    (para 3: "notice ... under Section 73(1)")
Tax year:        April 2018 – March 2019 = FY 2018-19  (para 2)
Notice date:     23.12.2023                            (para 3)
Reply due:       20.01.2024                            (para 3)
Hearing date:    20.01.2024  <- SAME DAY as reply due  (para 3, para 12)
How served:      not stated
Signed?:         not stated
Reply filed:     18.01.2024 (argued tax was under reverse charge, attached invoices)  (para 4)
Order date:      30.04.2024 under s.73(9), partly accepted the reply   (para 5)
Amount:          not stated
Later events:    rectification application (s.161) rejected 09.10.2024  (para 6)

Defects argued (paras 7–8):
 1. No real hearing (hearing_75_4)                -> FOUND    (para 12, 15)
 2. Order ignores the reply / gives no reasons    -> FOUND    (para 13–15)
    (reply_not_considered + non_speaking_order)
 3. Rectification rejection wrong                 -> NOT DECIDED ("loses its significance", para 16)

Outcome:         Petition allowed, order set aside, sent back to the officer for a
                 fresh decision after a hearing  (para 17–18)

Didn't fit the schema / odd things:
 - A scrutiny notice under s.61 came BEFORE the show cause notice (para 2). No event type for it.
 - "Hearing on the same day the reply is due" is a recurring pattern. Its own flag, or part of hearing_75_4?
 - Para 17 says "Section 79(3)" but paras 1 and 5 say s.73(9): a typo in the judgment. Record s.73(9) and note it.
 - Para 13 quotes the officer's order in Hindi; the text comes out garbled. Can't be used as a quote.
```
How it was found: paras 1–6 are the facts in date order; paras 7–8 are the taxpayer's arguments (= defects argued); paras 9–10 are the department's side (claims, not facts); para 11 "We have considered…" is where the court's voice starts; paras 12–16 are the findings; paras 17–18 the outcome.

## Note template (one per case)
```
Case:
Section (73/74):        Tax year:
Notice date:            Reply due:          Hearing date:
How served:             Signed?:            Order date:          Amount:
Other events (reply, adjournments, rectification, appeal):
Defects argued:         -> found / rejected / not decided  (para no.)
Outcome:
Didn't fit the schema / confusing:
```
If something confuses you, write down what. That's exactly what the meeting needs.
