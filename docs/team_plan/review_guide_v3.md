# Review round 3: 20 fresh cases (14–15 Nov)

**Why:** every number so far is on cases we picked before the system was finished. These 20 judgments were picked
on 14 Nov, after NoticeCheck was frozen, and nobody has looked at them. NoticeCheck runs on them separately
(Kaggle notebook H). Your review is the answer key; together they show how the full system does on brand-new cases.

**Deadline: Saturday 15 Nov, 11:00.** Each of us has **5 cases** (4–30 pages each, about 1 hour in total).

| Reviewer | Cases | Pages |
|---|---|---|
| r1 (Neill) | 5 | 28 |
| r2 | 5 | 40 |
| r3 | 5 | 59 |
| r4 | 5 | 52 |

## Setup (5 minutes)
```
git checkout noticecheck-core
git pull
python scripts/fetch_data.py --reasoned-only     # also downloads the 20 fresh judgments
python -m review_app.server                      # opens the review tool; it now shows the fresh list
```
Pick your id (r1–r4) at the top left.

## What to do for each case
Same as before ([`review_guide.md`](review_guide.md), sections "Each case" and "Finding rules"), with the focus on
**complaints and findings**, which is what gets scored:
1. **In scope?** A GST demand under s.73/74 where the court rules on a procedural complaint. If not: Notes +
   "Save as out of scope". (A quick filter picked these cases, so expect one or two to be out of scope.)
2. **Complaints and findings:** for every procedural complaint the petitioner makes, check the type, the
   finding (found / rejected / not decided) and the court's own words as the quote. Add anything the draft missed;
   delete cards that are not procedural complaints (the merits of the tax are not a card).
3. **Outcome**, then **Save as reviewed**. A quick look at the facts is welcome but not required this time.

Reminders:
- "Sent back to the officer" is **not** "defect found". Remands by consent or "for one more opportunity" are **not decided**.
- If a card's quote is the lawyer's argument, find the court's answer a few paragraphs later.
- If unsure, start the Notes with `UNSURE:`; Neill decides.

## AI help
You may use an AI assistant to find the right paragraphs faster, but **you** decide every label by reading the
judgment, and every quote must turn green in the tool (it checks quotes word for word). Two rules:
- **Never look at NoticeCheck's outputs** for these cases (`runs/fresh_nc*`, `runs/rq2_fresh`) before you save,
  and never give them to your AI. That would make the test meaningless.
- If you used AI, start the Notes with `AI-ASSISTED:` (we report how the labels were made).

## Save your work
```
git add data/gold/annotations/
git commit -m "Round 3 fresh reviews r2"
git pull --rebase
git push
```
