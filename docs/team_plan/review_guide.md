# Review: turning drafts into gold (30 Oct)

**Goal for today:** 60 gold cases (16 of them checked by two people), so the system and baselines can be scored tonight for the mid submission. **Finish your list by 4 pm.**

Each person has **19 cases**: 15 of their own and 4 marked **2nd review**, which another reviewer also does. The list is in [`data/splits/review_queue.csv`](../../data/splits/review_queue.csv). It is a balanced pick (courts mixed, every case where the court rejected a complaint, few Delhi template orders), so it does not matter whose pre-fill share a case came from. The 4th person can review even while their own pre-fill is still running.

## Start
```
git checkout main
git pull
python -m review_app.server
```
A page opens in your browser (if not, open http://127.0.0.1:8501). Pick your id (`r1`..`r4`) at the top left. Your 19 cases are listed; work through them in order. Nothing to install beyond what the pre-fill needed.

## Each case (about 10 minutes)
The judgment is on the left, with every quote highlighted. The draft is on the right. Everything is checked live: red means a quote is not in the judgment word for word, or a rule is broken. "Save as reviewed" only works when everything is green and ticked.

1. **In scope?** Yes = a GST demand under s.73/74 (tax periods up to 2023-24) and the court rules on, or is asked to rule on, at least one procedural complaint. No = anything else (refund, registration, s.74A, no procedural complaint argued). If no, write why in Notes and click "Save as out of scope".
2. **Complaints and findings: check every one against the judgment.** This is the answer key, so it matters most.
   - Is the type right? Did the petitioner really argue it? Delete it if not.
   - Is the finding right (rules below)? Does the quote say it, in the court's own words?
   - Did the model miss a complaint? Add it.
   - Tick "checked against the judgment".
3. **Outcome:** disposition, remanded or not, and the quote.
4. **Facts: quick check.** Wrong values are rare; empty ones are more common. Fix them in the JSON box if the judgment states them. Tick "quick-checked".
5. Click **Save as reviewed**. The next case opens.

**2nd review cases:** do them on your own. Don't ask the other reviewer or look at their file, or the agreement score means nothing.

## Finding rules
| Finding | When |
|---|---|
| `defect_found` | The court says in its own words that the department made this mistake. Quote the court. |
| `defect_rejected` | The court says the mistake did not happen, or is not a valid ground. Quote the court. |
| `not_decided` | Argued, but no firm ruling: consent remand, "one more opportunity", "contentions kept open", a "prima facie" view only, left to the appeal, pending in the Supreme Court. Quote the court if it says something, otherwise the argument (set "quote from" to argument). |

Decided cases (from the schema session):
- **A remand alone is not `defect_found`.** Another chance "in the interest of justice" or "on equitable grounds" is `not_decided` (Kalika).
- **A clear conclusion wins over the words "prima facie".** "Prima facie, the order cannot be said to be non-speaking" is `defect_rejected` (Garg). A tentative view with no conclusion is `not_decided`.
- **Delhi "Additional Notices" tab:** if the order is set aside because the notice was only uploaded under that tab, it is `service_169`, `defect_found`.
- **Disputed facts, "no records before us", or "raise it in the appeal"** are `not_decided`, even if the petition is dismissed.
- **Liberty to issue a fresh notice is not a remand.**
- `extension_notification_validity` is a challenge to the s.168A extension notifications themselves; `limitation` is "the notice or order came too late". Use both only if both are argued.
- `contested` is ticked only if **this judgment** mentions conflicting High Court views or a pending Supreme Court case.
- `other_procedural` needs a short note on what the ground is.

Full rules: [`schema_proposal_v0_1.md`](schema_proposal_v0_1.md), "Rules" and "Judgement calls".

## When a quote is red
- Select the right sentence in the left pane, copy it, and paste it in place of the quote. Keep it short (one sentence or less).
- Garbled text (broken Hindi, jumbled table text from Madras templates): choose another sentence that says the same thing. For a fact with no readable quote, set both its value and its quote to `null`. **No verified quote, no gold.**
- Para numbers matter less than the words; fix them if they are clearly wrong.

## Unsure?
Pick your best answer, start the Notes with `UNSURE:` and say why. We go through these together at 4 pm. Don't spend more than 15 minutes on one case: save it with "Save, finish later" and come back.

## Save your work to git (every 5 cases or so)
Your reviews are saved in `data/gold/annotations/<your id>/`. Nobody else writes there, so pushes never conflict:
```
git add data/gold/annotations/
git commit -m "Reviews r2"
git pull --rebase
git push
```

## At 4 pm
Neill runs `python -I scripts/build_gold.py`. It builds `data/gold/records.jsonl` (the gold), `data/splits/test.txt`, and the two files for the agreement score. Then the system and the baselines are scored on it.
