# Round 3: check NoticeCheck's answers on 20 new judgments

## In one sentence
NoticeCheck has already read 20 new High Court judgments and given its answers; you read the same judgments and
say, for each answer, whether it is right.

## What these cases are (same kind as before)
- They are **High Court judgments**, exactly like the 125 test cases. **There are no real show cause notices
  anywhere in this project**: real notices are not public. A judgment describes the notice, the reply, the hearing and
  the order, and then the court says which steps were defective. So one judgment gives us both the facts and the
  right answer.
- The only difference from before: these 20 were picked **after** the system was finished, and nobody has looked at
  them. This checks how the system does on brand-new cases.

## What the system already did (you don't run anything)
1. Our fine-tuned model read each judgment and wrote down the facts (notice date, hearing, reply, order, ...).
2. NoticeCheck checked those facts step by step and gave an answer for each defect type: **defect**, **no defect**,
   **contested** (courts disagree on this point) or **can't tell**.

We only check the first three. "Can't tell" is left out.

## What you do
Your sheet has one row per answer. For each row:
1. Read what NoticeCheck said (for example: "Order ignores the reply: **defect**", with the words it quoted).
2. Find that part of the judgment and see what the judgment actually says.
3. Fill in three boxes:

| Box | Write | Meaning |
|---|---|---|
| **YOUR_VERDICT** | `correct` | The judgment backs up NoticeCheck's answer |
| | `wrong` | The judgment shows the opposite, or the quote doesn't say what NoticeCheck claims |
| | `cant_verify` | The judgment doesn't say enough to tell |
| **COURT_DECIDED** | `found` | The court said this step was defective |
| | `rejected` | The court said this step was fine |
| | `not_decided` | The court sent it back without deciding (e.g. "one more opportunity") |
| | `not_argued` | Nobody raised this point in the case |
| **COMMENT** | a few words | Why, if it isn't obvious |

The last row of each case is **MISSED?**: if the court found a defect that NoticeCheck did not call a defect, write
its name in COMMENT; otherwise write `none`.

**For a "contested" answer:** mark it `correct` if the point really comes up in this case (one notice for several
years, or the COVID time-limit extensions); `wrong` if it doesn't come up at all.

## A worked example (r1's first case, APHC010457982026, 4 pages)
The sheet says:

| check | defect_type | what_it_means | noticecheck_says | noticecheck_evidence |
|---|---|---|---|---|
| 1 | consolidated_scn | One notice covers several financial years | contested | [judgment] "the order of respondent No.3 covering tax period for the different Assessment Years i.e., 2021-22 to 2024-25 is not sustainable" ... |
| 2 | MISSED? | Any defect the court found that NoticeCheck did not call a defect? | | |

Open the judgment (`data/raw/28_2/APHC010457982026.pdf`) and read it. Para 6 says the order "is liable to be set
aside on the ground that the same is a composite order covering the tax periods 2021-22 to 2024-25", and para 4 says
the department has appealed the earlier ruling to the Supreme Court. So you fill in:

| check | YOUR_VERDICT | COURT_DECIDED | COMMENT |
|---|---|---|---|
| 1 | correct | found | para 6: order set aside as one order for 2021-22 to 2024-25; SC appeal pending, so "contested" fits |
| 2 | | | none (court did not decide the other contentions, para 6) |

Note that **COURT_DECIDED comes from the judgment, never from NoticeCheck**. NoticeCheck never says what the court
decided; that is exactly what you add.

## Where things are
- **Your sheet:** `docs/team_plan/fresh_check/r1.csv` (or r2, r3, r4). Open it in Excel, LibreOffice or Google
  Sheets. About 1 hour of work.
- **The judgments:** run `git pull` and then `python scripts/fetch_data.py --reasoned-only`. Each row's
  `judgment_pdf` column gives the file, e.g. `data/raw/7_26/DLHC010740672025.pdf`. Use Ctrl+F with a few words of
  NoticeCheck's quote to find the right place.

| You | Calls to check |
|---|---|
| r1 (Neill) | 18 |
| r2 | 20 |
| r3 | 33 |
| r4 | 10 |

## Rules
- **Deadline: Saturday 15 Nov, 11:00.**
- You can ask an AI to help you find the right paragraph, but you decide every answer by reading the judgment.
  If you used AI, start your first COMMENT with `AI`.
- Save as CSV with the same name, then push (`git add docs/team_plan/fresh_check/`, commit, `git pull --rebase`,
  `git push`), or just send the file to Neill.

## Why we do this
Our automatic scoring can only check answers on points the court ruled on. NoticeCheck also flags points nobody
argued, and only a person reading the judgment can say whether those are real problems or false alarms. Your checks
answer that.
