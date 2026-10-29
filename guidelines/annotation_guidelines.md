# Annotation guidelines (schema_version 0.1)

For every field in `schemas/facts.schema.json` and `schemas/findings.schema.json` (see
`docs/team_plan/contracts.md` section 1). One definition, what counts and what doesn't, and one
real quote per field/defect type, drawn from the judgment PDFs we've actually read so far
(`data/raw/pilot_reading/`: UPHC010748612025 *Rajesh Kumar Singh*, UPHC020953002025 *M/S Agarwal
and Company*, KAHC010289442026 *M/S Shivneel Gas Sales*, WBCHCJ0026132026 *M/s Garg Enterprises*).
Court PDFs are the only source of truth — never Kanoon/Taxscan/LiveLaw/model memory. **Where a
field or defect type has no real example below, don't invent one.** Add the quote the first time
a reviewer hits a real case that has it, and extend this file (small PRs welcome — this file isn't
schema-frozen, only `contracts.md`/the schema JSON files are).

Every `quote` you write must appear **verbatim** in the judgment text (a script checks this; no
verified quote, no gold). `para` is the judgment's own paragraph number, not a line number.

---

## 1. Fact fields (`schemas/facts.schema.json`)

### `provision`
**What it is:** the section (73 or 74) the demand proceeding was started under. **Counts:** the
section under which the SCN/order was issued, stated anywhere in the judgment (recitals, prayer, or
the court's own description). **Doesn't count:** a section the petitioner argues *should* have been
used instead (e.g. "this should have been under s.73, not s.74" is a `section_74_ingredients`
defect, not a correction to this field — record what was actually used).
> *"order dated 09.10.2024 (Annexure - 8) passed under Section 73(9) of the Act"* (UPHC010748612025, para 1).

### `financial_years`
**What it is:** the FY(s) the proceeding covers. More than one FY in a single `notices[]` entry
means a consolidated/clubbed notice (relevant to `consolidated_scn`). **Counts:** the tax period as
stated, converted to FY form (`"2020-21"` for Apr 2020–Mar 2021). **Doesn't count:** the FY of the
writ petition or of an unrelated earlier proceeding mentioned in passing.
> *"For the tax period April, 2018 to March, 2019, the return of the petitioner was scrutinized"*
> → `["2018-19"]` (UPHC010748612025, para 2).

### `notices[].date`, `.reply_due`, `.hearing_date_given`, `.hearing_date`
**What it is:** the SCN's own issue date, the reply deadline it states, and whether/when it fixed a
personal hearing. **`hearing_date_given`** is `false` for "NA" or a blank hearing column, not just a
genuinely absent field — if the judgment quotes the notice and the hearing column says "N.A.", that
is `hearing_date_given: false`, `hearing_date: null`, with the "N.A." text as the quote. **Counts:**
dates the notice itself states. **Doesn't count:** the date a reminder or a later notice gives if
this is a different, earlier notice in `notices[]` — one entry per actual notice (CLAUDE.md: two
notices in one case → two `notices[]` entries, not one merged entry).
> *"the date indicated by which reply was to be submitted was 20.01.2024 and date of personal
> hearing was also fixed on the same date"* (UPHC010748612025, para 3) → `reply_due: "2024-01-20"`,
> `hearing_date_given: true`, `hearing_date: "2024-01-20"` (same-date defect — see `hearing_75_4`).
>
> *"The column in which date of personal hearing has to be mentioned, only N.A. is mentioned
> without mentioning any date"* (UPHC020953002025, para 10, quoting a departmental office memo
> describing the general practice) — use this pattern (an explicit "N.A." in the notice) as the
> model for `hearing_date_given: false`; this particular sentence describes the memo's general
> complaint, not this petitioner's own notice, so don't attribute it to this case's `notices[]`
> entry without the judgment also saying this notice did it (see "quoted passages" hard case below).

### `notices[].service_mode`, `order.service_mode`
**What it is:** how the notice/order reached the taxpayer. **Counts:** `portal_additional_notices_tab`
/`portal_notices_tab` only if the judgment *names* that tab; otherwise `portal_unspecified` if it
just says "uploaded on the portal". **Doesn't count:** guessing the tab from context — if the
judgment never names it, it's `portal_unspecified`, not `portal_additional_notices_tab`, even if
that's the more common defect pattern in similar cases.
*(No example yet in the four cases read for this draft — none of them turn on the portal tab.)*

### `notices[].signed`, `order.signed`
**What it is:** whether the notice/order was signed or authenticated. **Counts:** an explicit
statement either way. **Doesn't count:** a bare allegation in the petition that is then left
undetermined by the court — that's a fact gap (`null`), not `signed: false`; see `signature` below
for how this interacts with `finding`.
> Contrast: the petitioner alleged the DRC-01A pre-SCN intimation "has not been signed by the
> proper officer/has invalid signature" (WBCHCJ0026132026, para 3(a)) — an **argument**, not a
> court-established fact. The court declined to determine it on the papers (para 8), so
> `notices[].signed` for this case stays `null`; what goes in `defects_argued` is `finding:
> "not_decided"` (see hard case 1 below), with `quote_source: "argument"`.

### `notices[].summary_only`
**What it is:** true if only the DRC-01 summary was issued, no detailed notice behind it.
**Counts:** the judgment or the parties agreeing a detailed notice does/doesn't exist. **Doesn't
count:** the petitioner's bare assertion if the court finds a detailed notice on record.
> *"the documents disclosed by the petitioner would demonstrate that the detailed show cause is
> available on the file"* → `summary_only: false` (WBCHCJ0026132026, para 8), even though the
> petition had alleged a summary-only notice at para 3(c).

### `order.date`
**What it is:** the date of the s.73(9)/74(9) demand order being challenged. If the judgment
mentions both a DRC-07 and the adjudication order with *different* dates, use the adjudication
order's date here and record the DRC-07/summary date as a separate `order_passed`-type `events[]`
entry (or `order_uploaded` style note) — don't silently prefer one.
> Adjudication order 01.12.2023 vs. its DRC-07 summary dated 02.12.2023, one day later
> (KAHC010289442026, paras 1 table / Sl. 1–2) — `order.date` = `"2023-12-01"`; the 02.12.2023 summary
> date goes in `events[]`, not into `order.date`.

### `events[]`
**What it is:** the dated steps of the proceeding. **Counts:** only a date the judgment itself
states, with the event type from the frozen enum. **Doesn't count:** inferring an event happened
just because a defect was later argued about it — e.g. don't add a `reply_not_filed` event unless
the judgment says the reply was never filed; a defect argued about the reply (or anything else)
with no stated date is a `defects_argued` entry, not an `events[]` entry.
> *"The petitioner filed his reply on 18.01.2024 to the show cause notice"* →
> `{"date": "2024-01-18", "type": "reply_filed", ...}` (UPHC010748612025, para 4).

### `document_contents[]`
**What it is:** what the notice/reply/order *said*, as the judgment reports it — never the court's
opinion of it. **Counts:** `"the order states no evidence of RCM payment was produced"` (a
description). **Doesn't count:** `"the order is cursory"` (an opinion — that belongs in
`defects_argued`, not here). Max 8 entries; only what bears on a defect.
> *order_reasoning*: the Hindi order text recording that on 3 of 10 points, "no evidence has been
> produced pertaining to deposit of tax through RCM and the accounts books have not been verified"
> (UPHC010748612025, para 13) — a description of what the order said, feeding the
> `non_speaking_order` check; the court's own opinion that this was "a wholly cursory finding"
> (same para, court's framing) stays out of `document_contents` and instead supports the
> `defects_argued` entry below.

---

## 2. Defect types (`schemas/findings.schema.json` → `defects_argued[].type`)

For each: definition, what counts/doesn't, one real example. Several types have no example yet —
marked explicitly; don't fill them with a guess.

### `hearing_75_4` — no personal hearing, or a sham one, before an adverse order
**Counts:** no hearing date given at all; "NA" in the hearing column; hearing date identical to or
before the reply-due date (an "empty formality"); hearing offered but never actually held with no
fault of the taxpayer. **Doesn't count:** taxpayer waived the hearing or simply didn't attend one
properly offered — that's not a defect by the department.
> `defect_found`: *"A bare look at the show cause notice ... would reveal that date of filing of
> reply and date of personal hearing are the same i.e. 20.01.2024. This Court has repeatedly
> frowned on the action of the respondents in fixing identical date of reply and date of hearing, as
> the same apparently is an empty formality and essentially results in violation of principle of
> natural justice."* (UPHC010748612025, para 12).

### `adjournment_75_5` — adjournments refused or mishandled (statutory limit is three)
*(No example yet — none of the four read cases argue this.)*

### `reply_not_considered` — reply was filed but the order ignores it or claims none was filed
**Counts:** order doesn't engage with a specific point raised in the reply. **Doesn't count:** order
disagrees with the reply after considering it (that's a merits disagreement, not this defect,
unless it's also so threadbare it's `non_speaking_order`).
*(No example yet in the four read cases — UPHC010748612025's reply was substantively engaged with,
just cursorily, which is why it's coded `non_speaking_order` there instead.)*

### `non_speaking_order` — order gives no real reasons, copies boilerplate
**Counts:** order disposes of a specific, detailed plea with only a generic/cursory line.
**Doesn't count:** a short order that still engages with the substance — brevity alone isn't the
defect, absence of reasoning is. A `"prima facie"`-hedged finding, where the court itself won't
commit, is `not_decided`, not `defect_rejected` (see hard case 1).
> `defect_found`: *"It would be seen that show cause notice was issued on 10 points and while on 7
> points, the same was accepted, that also without indicating any reason, on 3 points only a cursory
> observation has been made that no evidence has been produced... Such a cursory disposal of the
> objection raised in reply to the show cause notice cannot be countenanced when plea raised is very
> specific."* (UPHC010748612025, para 14).
>
> `not_decided` (contrast — don't code this one `defect_rejected`): *"I find that though prima facie
> sufficient reason has been provided in the aforesaid order, the order cannot be said to be
> non-speaking, however, these are all disputed factual issues."* (WBCHCJ0026132026, para 9) — see
> hard case 1.

### `demand_beyond_scn` — order demands more, or on other grounds, than the notice
*(No example yet in the four read cases.)*

### `service_169` — notice or order not properly served
*(No example yet in the four read cases — none turn on the portal tab or an alternate mode of service.)*

### `signature` — notice or order not signed or authenticated
**Counts:** a specific, examinable allegation that a particular document lacks a signature.
**Doesn't count:** when the court says the point can't be resolved on the papers (disputed fact,
no document production) and leaves it to another forum — that's `not_decided`, not `defect_found`
or `defect_rejected`.
> `not_decided`: petitioner's ground that the pre-SCN intimation "has not been signed by the proper
> officer/has invalid signature" (WBCHCJ0026132026, para 3(a)); the court: *"there is no scope for
> this Court to make such a determination in absence of the records being produced... these are all
> factual aspects and ordinarily cannot be gone into by the writ Court"* (para 8). `quote_source:
> "argument"` for the ground itself if you also want the court's refusal quoted, use `quote_source:
> "court"` with the para-8 sentence instead — pick whichever quote actually carries the
> `not_decided` call; don't record both as if they were two separate findings.

### `summary_only` — only the DRC-01 summary issued, no proper notice
**Counts:** the court/record establishing no detailed notice exists. **Doesn't count:** petitioner's
unexamined allegation if the judgment goes on to find a detailed notice did exist.
> `defect_rejected`: *"the documents disclosed by the petitioner would demonstrate that the detailed
> show cause is available on the file"* (WBCHCJ0026132026, para 8) — ground 3(c) ("show cause notice
> ... is vague, non specific ... no specific taxable event or essential ingredients ... disclosed")
> is effectively answered by this finding, since a detailed notice (not just the DRC-01 summary)
> was on record.

### `limitation` — notice or order issued after the time limit
*(No example yet — KAHC010289442026 raises a *substantive* ITC-eligibility argument under s.16(5),
not a time-limit argument, even though the rules-based screening pass on `schema_pilot.csv` flagged
it under "limitation"; see hard case 5's companion note below on not trusting the screening keyword.)*

### `extension_notification_validity` — challenge to the s.168A time-extension notifications
*(No example yet in the four read cases — **always `contested: true`** when it appears, by definition.)*

### `consolidated_scn` — one notice covering several financial years / periods clubbed together
**Counts:** a specific objection that periods were improperly clubbed into one SCN. **Doesn't
count:** multiple periods named in one notice where the judgment affirmatively finds there was no
improper clubbing (check the actual SCN/summary, not just that several months are mentioned).
> `defect_rejected`: ground (d) was *"the show cause notice issued under Section 74 ... deals with
> different periods which had been clubbed together, the same is not permissible in law"*
> (WBCHCJ0026132026, para 3(d)); the court: *"There is no clubbing of periods in the summary of
> show-cause in Form DRC 01, the detailed reasons of the show-cause have been, however, provided in
> a composite format. In this context, it must be noted that serious allegations of smuggling ...
> was involved, which was unearthed during investigation, as such the consolidated show-cause was
> issued."* (para 8).

### `section_74_ingredients` — s.74 invoked without fraud/wilful-misstatement/suppression
*(No example yet in the four read cases.)*

### `other_procedural` — any other procedural ground; name it in `note`
*(No example yet. Reserve for a real procedural ground that doesn't fit the twelve above — e.g. a
jurisdictional defect like WBCHCJ0026132026's ground (e), "the authority who received the response
is not the same who had heard the matter" (para 3(e)), **if** a case ever gets a firm ruling on it;
in WBCHCJ0026132026 itself the court found "it is an admitted position that the authority who heard
the petitioner was a proper officer ... and it is the same proper office who had passed the order"
(para 9) — `defect_rejected`, `note: "different officer received reply vs. heard matter"`.)*

---

## 3. `outcome`

**`disposition`**: what the writ petition itself was decided as — not the underlying tax demand.
`remanded` is a **separate boolean**, not a disposition value; a remand is always
`disposition: "allowed"` (or `"partly_allowed"`) + `remanded: true`, never `disposition: "remanded"`.
> `allowed` + `remanded: true`: *"Consequently, the petition is allowed. The order impugned dated
> 30.04.2024 ... is quashed and set aside. ... The matter is remanded back to the Deputy
> Commissioner, State Tax, Mirzapur for deciding the matter afresh after providing opportunity of
> hearing to the petitioner."* (UPHC010748612025, paras 17–18).
>
> `dismissed`: *"Accordingly, the writ petition stands dismissed."* (WBCHCJ0026132026, para 12) — on
> alternative-remedy/jurisdiction grounds, without the court reaching most of the procedural
> defects argued; most of this case's `defects_argued` entries are therefore `not_decided`, not
> `defect_rejected`, even though the petition as a whole lost (losing the petition is not the same
> as losing on the merits of a specific ground — check each ground's own finding).

Reminder: a case can be `allowed` + `remanded: true` with **no entries in `defects_argued` at all**
if the remand is for a substantive reason unrelated to our procedural taxonomy.
> KAHC010289442026: petition allowed, adjudication order quashed and the matter remanded, but the
> entire basis was a retrospective ITC amendment (s.16[5]) that post-dated the order — *"this
> amendment was not on the Statute Book when the impugned Order is passed... this Court is of the
> considered view that whether there must be any enforcement in the light of this amendment must be
> reconsidered with opportunity to the petitioner with a formal order"* (paras 4–5). No hearing,
> signature, service, limitation, or any other procedural ground was argued or decided here — leave
> `defects_argued: []`. (The rule-based screening that produced `data/splits/schema_pilot.csv` flagged
> this case `defects_flagged_by_rules: limitation` from keyword matching on "within the time
> prescribed"/"amendment" language; it is wrong for this case — treat that column as a candidate list
> to check, never as a label, per CLAUDE.md "gold labels never come from the system under test".)

---

## 4. Hard cases (CLAUDE.md, Mon 27 Oct agenda)

**1. Consent / "one more opportunity" remands → `not_decided`.**
Any remand granted because the court won't commit to a ruling — "prima facie" language, a remand by
consent, "contentions kept open", or (as in WBCHCJ0026132026 on the signature point) a refusal to
determine disputed facts and a push toward the statutory remedy — is `not_decided`, even if the
petition is otherwise `allowed`/`dismissed` and even if the court uses sympathetic language toward
one side. Real example: the signature ground in WBCHCJ0026132026 (para 8, quoted under `signature`
above) and the `non_speaking_order` ground in the same case (para 9, "prima facie" hedge, quoted
above). *A stronger "consent remand"/"one more opportunity" phrasing specifically hasn't turned up
in the four cases read for this draft — add a quote once one does; the KAHC010289442026 remand (s.3
above) is NOT this pattern, since the court there gives a firm, reasoned basis for remanding on the
ITC point, it just isn't about a procedural defect.*

**2. Court relying on another judgment ("covered by") → a finding only if applied to this case's facts.**
UPHC020953002025 is the clean real example. The court doesn't independently reason about *this*
petitioner's hearing; it quotes *Mahaveer Trading Company* (paras 5–11 of that judgment, reproduced
verbatim in paras 7, 51–61 of this one) and then explicitly closes the loop: *"Since the aforesaid
dictum is applicable in the present facts and circumstances, accordingly, the impugned orders cannot
be sustained."* (para 6). Because the court states the dictum applies *here*, this is
`hearing_75_4: defect_found` for **this** case — quote the applying sentence (para 6), not only the
borrowed dictum, as the primary quote; the dictum itself can be cited as supporting context but the
"applies to this case" sentence is what makes it a finding at all. If a judgment instead only cited
another case's holding in the abstract (a string of citations, a general proposition) without this
kind of "applicable in the present facts" sentence, record nothing for that case — it's not a
finding on this case's facts.

**3. Quoted passages from other cases → never this case's facts.**
Same UPHC020953002025 example, the other side of it: paras 7(i)–(iii) and the office memo text
reproduced in para 10 describe **Mahaveer Trading Company's** petitioner (hearing dates
23/9/2022, 7/10/2022, 27/10/2022) and a general departmental memo about "N.A." hearing columns —
none of that is *this* petitioner's (Agarwal and Company's) `notices[]` data. This case's own notice
facts are genuinely thin in the judgment (the respondent's counsel merely "states that... no date was
fixed for personal hearing", para 4) — record only that admission for `notices[0].hearing_date_given`
(`value: false`), and leave the rest of this case's notice fields `null` rather than borrowing dates
out of the quoted Mahaveer paragraphs.

**4. Batch judgments covering many petitions → record only facts common to all, or mark per-petition facts `null`.**
*(No example yet in the four cases read — all four are single-petitioner. When one turns up: if the
judgment gives one shared SCN/order date, provision, etc. across all petitioners, record it; any
fact that differs petitioner-to-petitioner, or isn't individually stated for the petitioner this gold
record is about, goes `null` rather than copying another petitioner's figure.)*

**5. Limitation questions involving the extension notifications → `contested: true`.**
*(No real example yet — `extension_notification_validity` always gets `contested: true` by
definition the moment it's argued; a `limitation` entry should also be marked `contested: true`
specifically when the court's limitation computation itself turns on whether the s.168A extension
notifications validly pushed out the deadline, since High Courts are split on that question. Watch
for this in the fuller pilot set; KAHC010289442026, despite being flagged "limitation" by the
screening keyword pass, turns out on a full read to be an ITC-eligibility case, not a limitation one
— see the §3 note above.)*
