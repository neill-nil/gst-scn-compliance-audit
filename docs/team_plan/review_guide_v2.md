# Review round 2 (11–13 Nov)

**Why:** the final results need more verified cases than the 52 we reviewed for the mid, plus one High Court that the system never sees during development (Karnataka, the "held-out" court). Your reviews become the answer key that NoticeCheck and the baselines are scored against.

**Deadline: Thursday 13 Nov, 12:00 noon.** Whatever is reviewed by then goes into the final results.
**Minimum: your first 15 cases.** More is better; the list is in priority order.

## Your cases
The full list is in [`data/splits/review_queue_v2.csv`](../../data/splits/review_queue_v2.csv). The review tool shows it for you; you don't need to open the file.

| Reviewer | Total | Held-out (Karnataka) | Test | Second reviews (test) | Dev (last, optional) |
|---|---|---|---|---|---|
| r1 (Neill) | 24 | 2 | 13 | 5 | 4 |
| r2 | 39 | 3 | 23 | 7 | 6 |
| r3 | 39 | 3 | 24 | 7 | 5 |
| r4 | 39 | 2 | 24 | 8 | 5 |

**Do them in the order shown:** held-out first, then test (second reviews are mixed in), dev last. If time runs out, the dev cases can be skipped.

Labels in the tool:
- **heldout** / **dev**: which set the case belongs to. Unlabelled cases are test cases.
- **2nd review, no AI**: someone else also reviews this case. **Do it entirely on your own, with no AI help and without asking the other reviewer.** These cases measure how much reviewers agree, and AI help would make that number meaningless.

The first 15 cases are about 120–145 pages per person, about 10 minutes per case.

## Setup (5 minutes)
```
git fetch origin
git checkout noticecheck-core
git pull
python scripts/fetch_data.py --reasoned-only     # judgment PDFs for these cases, about 1 minute
python -m review_app.server                      # opens the review tool in your browser
```
Pick your id (r1–r4) at the top left. The tool now opens the round-2 list by default.

## How to review
Exactly as in round 1. Read [`review_guide.md`](review_guide.md), sections "Each case", "Finding rules" and "When a quote is red". In short, for each case:
1. **In scope?** A GST demand under s.73/74 where the court rules on a procedural complaint. If not: Notes + "Save as out of scope".
2. **Complaints and findings:** check every card against the judgment: type, finding (found / rejected / not decided), the court's own words as the quote. Add any complaint the model missed. Tick each card.
3. **Outcome**, then a **quick check of the facts** (fix red quotes).
4. **Save as reviewed.** If unsure, start the Notes with `UNSURE:`; Neill decides.

Two reminders from round 1:
- "Sent back to the officer" is **not** the same as "defect found". Remands by consent, or for "one more opportunity" / "in the interest of justice", are **not decided**.
- If a card's quote is the lawyer's argument, look for the court's answer to that argument a few paragraphs later.

## Save your work (every 5 cases)
Your reviews go to `data/gold/annotations/<your id>/`. Nobody else writes there, so pushes don't clash:
```
git add data/gold/annotations/
git commit -m "Round 2 reviews r2"
git pull --rebase
git push
```

## Problems
| What you see | What to do |
|---|---|
| The page says "no draft" or the judgment is empty | Run `git pull` and `python scripts/fetch_data.py --reasoned-only` again |
| `git push` is rejected | `git pull --rebase`, then `git push` |
| Anything else | Message Neill with the case number |
