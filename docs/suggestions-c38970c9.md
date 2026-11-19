# Suggestions — session `arena/c38970c9-nba4` (2026-11-19)

Task DP. Ten proposals, each resting on a measurement made in this session, each with the
verification that would be required before it is implemented. None is implemented except
where the *Status* column says so, and nothing here is presented as chosen.

The reviewer's field is the **Decision** column: Accept, Reject or Defer. A blank means no
decision has been recorded. This register is append-only relative to the existing proposals
(`docs/suggestions.md`, `docs/suggestions-2c06c7f9.md`, `docs/suggestions-634f12d9.md`);
those are not renumbered or removed.

| ID | Suggestion | Evidence | Options (trade-off) | Verification required | Status | Source |
| --- | --- | --- | --- | --- | --- | --- |
| DO-01 | Correct the "prints no at token" premise in `scripts/build_snapshots.py`, the `slate-2026-11-17.json` basis text and the pass-7 review wording, then delete the guard test that keeps the phrase off the page | the PDF prints ` at ` on row 253 and 1,197 times document-wide; 21/21 published rows already match | A. all three (recommended); B. build script only; C. leave it and keep DS-01 open | verified here with three extractors and a proven negative test (`SchedulePdfAtTokenTests`); a second session should re-run it | Pending owner — files are other sessions' scope | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| DO-02 | Make the site check fail when the published injury transcription is older than 24 h | `check_site.py --with-tests` PASSed while `scheduled_refresh.py` reported the transcription 39.3 h old on 2026-11-19T06:57Z | A. hard fail; B. warning only; C. show the age and never fail | a test that fires on a stale snapshot and stays quiet on a fresh one | Proposed | [Injury-report index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| DO-03 | Automate the injury-row transcription so "no manual input" is literally true | the daily job is automated; the 60-row table is transcribed by a session; the index lists 9 → 44 revisions a day | A. licensed feed (needs DP-01); B. automated parse with a human diff review; C. keep manual and publish the age | a licensed source, or a parser validated against every revision of one full day including page-break cells | Blocked on DP-01 | [Injury-report index](https://official.nba.com/nba-injury-report-2026-27-season/) |
| DO-04 | Adopt a written PDF-evidence standard: two extractors before any statement about what a PDF does **not** print | one extractor, read column-major, produced the false premise that survived four passes | A. two-extractor rule in the checker (recommended); B. content-stream read only; C. no rule | a fixture PDF with one changed cell must fail the check (proven in the pass log §1) | Proposed | [Schedule PDF](https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf) |
| DO-05 | Transcribe and diff the newest listed injury revision each cycle, and keep the revision rule in one place | 11/19 index lists 02:00 AM against a published 01:45 AM; 11/17 index listed 10:45 AM against a published 10:30 AM | A. newest-before-tip (recommended); B. first of the day; C. every revision | apply the rule to the index's link list, which is the authority; each new transcription diffs against its predecessor | Pending owner — flag DS-05 | [11/19 01:45 AM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-19_01_45AM.pdf) |
| DO-06 | Publish the transport audit in the daily job summary so every run states how many statistics surfaces answered 200 with no payload | 4 of 4 statistics pages answer 200 and carry nothing, on both capture dates | A. job summary (recommended, no new permission); B. make it a gate; C. leave it manual | the auditor must stay offline and its three marker traps must keep failing their tests | Implemented as a script, not wired into CI | [Standings page](https://www.nba.com/standings) |
| DO-07 | Replace the single headline rating with the two-estimator disagreement once inputs exist; until then print **unmeasured** with the reason rather than a blank | `engine/dualestimate.py` computes banded disagreement; the live column is empty because every game is NO PICK | A. "unmeasured" + reason (recommended); B. hide the column; C. show the blend (contradicts the brief) | wording must not imply a number exists; the surface-split audit must confirm no bet-gated value leaks | Proposed | [dualestimate.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/dualestimate.py) |
| DO-08 | Give the leaderboard a "first failing gate" column per registered strategy instead of an empty table | `engine/leaderboard.py` evaluates G0–G12 per candidate | A. first failing gate (recommended); B. empty table with explanation; C. narrative only | each row must name a real gate that refused, with the module and test behind it | Proposed | [leaderboard.py](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/leaderboard.py) |
| DO-09 | Show a "verification budget" line on the review page: documents read, documents fetched from a hosted runner, claims that could not be checked | this session read 0 NBA pages live and 2 captured documents; earlier sessions had different limits and the page says so nowhere | A. line on the review page (recommended); B. per-flag note; C. nothing | counts must be generated from the pass log, not typed | Proposed | [Pass log](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/verification-pass-c38970c9.md) |
| DO-10 | Add a "what would change if DP-01 were answered" panel to the overview so the owner sees the unlock cost of each option | the pass log §9 lays out four options; the overview only says "no picks" | A. panel on the overview (recommended); B. keep it in the pass log; C. questions page only | no option may look chosen; the panel must render identically for all four | Proposed | [NBA Terms of Use](https://www.nba.com/termsofuse) |

## Why these ten and not more

Three of the ten (DO-01, DO-02, DO-04) fix statements or gaps that this session measured
directly. Two (DO-03, DO-05) remove the manual step the owner said they do not want. Four
(DO-06 … DO-09) make the evidence easier to act on. One (DO-10) is about the single decision
that unlocks everything else. Nothing in this list adds a number, a line, a probability or a
pick, and nothing asks for a change that the measurements do not support.

The first draft of this session's work included two further items that were **dropped after
measurement**, not deferred: (a) "add stale-year guards for the refresh dates" — the gates
already handle staleness and the real gap was that the *site* check ignores it, which is
DO-02; (b) "probe-mode JSON run-record defect" — no defect exists, the 2026-11-18 failure was
four failing gates, recorded as DS-08 on the review page.
