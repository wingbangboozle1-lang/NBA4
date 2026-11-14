# Suggestions register and decision queue

**Status: proposals only. Nothing in this document has been implemented unless its status says so.** This document merges two independent proposal sets that were written in parallel sessions and must not silently overwrite each other: the **decision queue** (four gating decisions plus twelve prioritised proposals from the PR #3 implementation, session `arena/ddc81141-nba4`) and the **review register** (23 proposals with a reviewer Decision column from session `arena/248bb9ab-nba4`). The rendered form is [`suggestions.html`](../suggestions.html), which is the version to review.

Suggested statuses: `Proposed` (awaiting review), `Needs decision` / `Needs a decision` (a dependency must be resolved first), `Accepted` (approved for implementation), `Blocked` (needs data or permission the project does not have), `Rejected`, `Deferred`.

## A. The four gating decisions (decision queue)

Nothing else can be built until these are answered. They are reproduced on the site as the “Decision queue”.

| Decision | Path A | Path B | Consequence of choosing | Source |
| --- | --- | --- | --- | --- |
| D-1 Data rights | Licence a provider that permits betting use in writing | Stay private and non-commercial, publish no numbers | A unlocks model work and public lines; B keeps the site an evidence shell. NBA Stats directly is not an option either way. | [NBA Terms §9](https://www.nba.com/termsofuse) |
| D-2 Product type | Informational analytics, no wagers or rewards | Picks/leaderboard with rewards | A is served by the current static host; B is a regulated activity needing classification, age controls and different hosting. | [Ksa: Remote Gambling Act](https://kansspelautoriteit.nl/remote-gambling-act-force) |
| D-3 First market | One single-bet market (e.g. game total) | Player props or same-game parlays | A needs team-level inputs only; B needs joint distributions and a validated minutes model first. | [NBA Stats glossary](https://www.nba.com/stats/help/glossary) |
| D-4 Success rule | Calibration-first (proper score plus reliability curve) | Return-first (ROI against a benchmark price) | A can be tested without a price feed; B cannot begin until licensed prices and settlement exist. | [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html) |

**Recommended order:** D-1 → D-2 → D-4 → D-3. Rights and product type are legal preconditions; the success rule must be fixed before any holdout is looked at; the market choice follows from which inputs are actually licensed.

**Why the order matters.** A common failure mode in this kind of project is to build the ranking and reward layer first, because it is the visible part, and to bolt validation on afterwards. That produces a leaderboard of strategies whose apparent skill cannot be distinguished from the sample they were selected on. The ordering above deliberately puts the unglamorous, blocking work first. The second failure mode is treating “no pick” as a defect. On this site a blank cell is a control: it means the evidence chain did not close. Proposals P-10 and S-06/S-10 exist so that a cell can distinguish *not computed* from *computed and excluded*, without ever implying a number that is not supported.

## B. Decision-queue proposals (P-01 … P-12)

These twelve proposals were numbered S-01 … S-12 in the PR #3 implementation. They are re-lettered **P-01 … P-12** here because the review register below uses S-01 … S-23 for a different set; nothing is discarded, and the overlap map at the end shows where the two sets say the same thing.

| ID | Suggestion | Options and trade-off | Effort | Status | Source link |
| --- | --- | --- | --- | --- | --- |
| P-01 | Publish a rights decision record for data: which provider, which contract clause, which fields, which territories, which retention | A: licensed provider covering betting use — unblocks everything, costs money and negotiation time. B: private non-commercial research only — cheap, still bars picks and any public numbers. C: no data — the site stays an evidence shell. Mixed A+B is impossible to display safely, because the display itself is the restricted act. | 1 session plus legal review | Needs a decision | [NBA.com Terms §9](https://www.nba.com/termsofuse) · [NBA Stats FAQ](https://www.nba.com/stats/help/faq) |
| P-02 | Add a data-source matrix page: every required input, its owner, refresh cadence, timestamp field, correction policy and permission status | A: one table per input type (schedule, box score, lineup, injury, price, settlement). B: single flat table — faster to read, harder to maintain. A is recommended, because permissions differ per field and a flat table hides that. | ½ session | Proposed | [NBA injury report policy](https://official.nba.com/nba-injury-report-2026-27-season/) |
| P-03 | Add an immutable forecast ledger schema, so every future line is stored with model version, input snapshot IDs and issue time before the event | A: append-only JSON/CSV with a hash per record. B: database table with version rows. Both are static-hostable if written at build time; A is simpler and diffable in Git, B needs a backend the current host cannot run. | 1 session (schema only) | Proposed | [scikit-learn: time-series validation](https://scikit-learn.org/stable/modules/cross_validation.html) |
| P-04 | Turn the validation gates into a pass/fail scorecard with an explicit “first failing gate” column | A: binary pass/fail per gate. B: pass/fail plus a distance-to-threshold. B risks implying partial credit for an unvalidated model, so A is recommended until real data exists. | ½ session | Proposed | [scikit-learn: metrics and scoring](https://scikit-learn.org/stable/modules/model_evaluation.html) |
| P-05 | Pre-register the leaderboard rules (objective, baselines, holdout, tie-breaks, reward terms) as a dated, versioned document before any model is scored | A: preregister now, reward-free. B: wait for data then preregister — risks rules being fitted to results. A is strongly preferred; the whole point is that rules precede results. | 1 session | Needs a decision | [scikit-learn: proper scoring rules](https://scikit-learn.org/stable/modules/calibration.html) |
| P-06 | Add a correlation worksheet: leg pair, conditioning set, estimator, sample count, game-clustered interval, shrinkage rule | A: residual Pearson for continuous legs plus joint-frequency for threshold legs. B: one generic coefficient for everything — misleading, because a parlay needs a joint probability, not a linear association. A is recommended. | ½ session (template only) | Proposed | [NIST: correlation definition](https://www.itl.nist.gov/div898/handbook/glossary.htm) · [NIST: bootstrap uncertainty](https://www.itl.nist.gov/div898/handbook/eda/section3/bootplot.htm) |
| P-07 | Build the injury-to-production chain as four separately validated steps: status, availability, minutes, production | A: four models with separate error reporting. B: one end-to-end model — fewer moving parts, but it hides which step failed and invites treating a status label as an impact estimate. A is recommended. | 2 sessions (design), blocked on data | Blocked | [NBA injury reporting policy](https://official.nba.com/nba-injury-report-2026-27-season/) |
| P-08 | Keep a decision log page: date, question, options, choice, who decided, and what would reverse it | A: a table on this site. B: an ADR folder in the repository. Both are cheap; A is visible to a non-technical reviewer, B is better for versioning. Doing both with A as a rendered view of B avoids duplicate truth. | ½ session | Proposed | [NBA4 repository](https://github.com/wingbangboozle1-lang/NBA4) |
| P-09 | Add a staleness banner that flips the whole slate page to “no picks” whenever its newest source timestamp exceeds a declared threshold | A: hard suppression. B: a warning while still showing numbers — rejected, because a stale line that looks current is exactly the failure mode that costs money. | ½ session (logic spec only until data exists) | Proposed | [NBA injury report (continual updates)](https://official.nba.com/nba-injury-report-2026-27-season/) |
| P-10 | Separate “no edge found” from “no data” everywhere a blank appears | A: three states — not computed, computed and excluded, computed and eligible. B: keep one blank state. A is recommended: the current single blank makes a tested-and-rejected strategy look identical to an untested one. | ½ session | Proposed | [scikit-learn: calibration limits](https://scikit-learn.org/stable/modules/calibration.html) |
| P-11 | Move commercial or live functionality to permitted hosting if, and only if, the product becomes commercial | A: stay static and informational. B: backend host with secrets and access control. B is required the moment there are accounts, rewards, paid access or live ingestion; the current host cannot serve it. | Depends on scope | Proposed | [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) |
| P-12 | Show a responsible-use and age note beside any future reward or contest content | A: static notice. B: age-gate. B is a compliance decision, not a design one; both belong to legal review for the target jurisdictions. | Minutes (copy), gated by review | Blocked | [Ksa: 10 tips for gambling safely](https://kansspelautoriteit.nl/10-tips-gambling-safely) |

## C. Review register (S-01 … S-23)

**The Decision column is deliberately empty: it is filled in by the reviewer, not by the agent.** Each row states the suggestion, the decision-making benefit, the effort, what it depends on, and a source link.

### C1. Decision-making improvements

| ID | Suggestion | Why it improves decisions | Effort | Depends on | Status | Decision | Source link |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S-01 | Show a per-page **as-of timestamp and data-freshness badge** on every table | Readers can tell instantly whether a page reflects today's evidence or a stale snapshot; it removes the most common misreading of a research dashboard | Low | Nothing (already implemented in the engine's freshness check) | Proposed |  | [engine pipeline](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/pipeline.py) · [injury policy](https://official.nba.com/nba-injury-report-2026-27-season/) |
| S-02 | Add a **"what changed since last snapshot"** column to the source register | Distinguishes a genuinely new source from a reworded one, and makes wording drift visible instead of silent | Low | Nothing | Proposed |  | [verified source register](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/source-verification.md) |
| S-03 | Publish the **gate-by-gate status of each candidate strategy** on the strategies page | Turns "not validated" into a checklist a reviewer can act on, instead of a single status word | Medium | Nothing (the gate definitions already exist) | Proposed |  | [validation plan](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/validation-plan.md) · [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html) |
| S-04 | Add a **comparison view that puts the model line, the benchmark line and the de-vigged probability side by side** | Makes the separation between an originated line and a market quote visible, which is the core integrity claim of the project | Medium | A licensed price feed and a written market specification | Needs decision |  | [line origination](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/line-origination.md) · [NBA Terms](https://www.nba.com/termsofuse) |
| S-05 | Add an **uncertainty column** next to every probability, with the interval width and the sample size | A probability without an interval invites over-reading; the interval is what makes the number honest | Medium | A licensed dataset to measure on | Needs decision |  | [NIST bootstrap](https://www.itl.nist.gov/div898/handbook/eda/section3/bootplot.htm) |
| S-06 | Add a **"why no pick" panel** driven by the pipeline's reason codes | Converts a blank table into an explanation, so a reader learns why nothing was issued instead of assuming a fault | Low | Nothing (the reason codes exist in the engine) | Proposed |  | [engine pipeline](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/pipeline.py) |
| S-07 | Add a **scenario panel** (competitive / separation risk) with the trigger definition and its coverage | Turns game-flow narrative into something checkable, and shows when the model does not know | Medium | An authorised game-level history and a preregistered scenario definition | Needs decision |  | [NBA metric definitions](https://www.nba.com/stats/help/glossary) |
| S-08 | Add a **correlation matrix view** with sample counts and cluster intervals beside each coefficient | A bare coefficient hides how little data may sit behind it | Medium | A licensed dataset | Needs decision |  | [NIST correlation](https://www.itl.nist.gov/div898/handbook/glossary.htm) |
| S-09 | Add a **reliability-diagram page** next to the leaderboard | A proper score alone does not prove calibration; the diagram shows it | Medium | A validated model and a holdout | Needs decision |  | [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html) |
| S-10 | Add a **filterable "unverified values" index** that lists every blank cell and its reason | Makes the gap between known and unknown auditable in one place | Low | Nothing | Proposed |  | [decision register](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/decision-register.md) |

### C2. Product and compliance improvements

| ID | Suggestion | Why it improves decisions | Effort | Depends on | Status | Decision | Source link |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S-11 | Keep the public site **strictly informational** and publish no picks, no prices and no rewards until the gates pass | Removes the legal exposure that comes from publishing betting recommendations or inducements before the product is classified | Low | Nothing | Proposed |  | [NBA Terms](https://www.nba.com/termsofuse) · [Ksa licensing](https://kansspelautoriteit.nl/remote-gambling-act-force) |
| S-12 | Publish a **plain-language "how this site decides not to publish" notice** in the landing page | Sets expectations for reviewers and users before a single number appears | Low | Nothing | Proposed |  | [Ksa consumer guidance](https://kansspelautoriteit.nl/10-tips-gambling-safely) |
| S-13 | Add a **responsible-gambling notice** with the jurisdiction's own consumer guidance and no promotional language | Required if the site is ever classified as advertising or affiliate; also the right default | Low | Nothing (a link only) | Proposed |  | [Ksa: 10 tips for gambling safely](https://kansspelautoriteit.nl/10-tips-gambling-safely) |
| S-14 | Add an **age-restriction and territory statement** | Clarifies who the site is for and what it is not | Low | A decision on target territories | Needs decision |  | [Ksa affiliate guidance](https://kansspelautoriteit.nl/ksa-attendeert-affiliatewebsites-op-regels-voor-reclame-kansspelen) |
| S-15 | Move to a **separate application host** if the product ever becomes live, commercial or account-based | GitHub Pages is not permitted for commercial SaaS or transaction-driven sites | Medium | The product decision | Needs decision |  | [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) |
| S-16 | Keep the **data-rights gate as a build-time check**, not a documentation note | Turns the blocking rule into something that fails loudly if it is ever bypassed | Low | Nothing (already implemented; needs to be wired into the publish step) | Proposed |  | [engine contracts](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/contracts.py) |

### C3. Engineering and research improvements

| ID | Suggestion | Why it improves decisions | Effort | Depends on | Status | Decision | Source link |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S-17 | Add a **provider adapter interface** so each licensed feed has one small, reviewable adapter | Keeps the engine independent of any single vendor and makes the rights check a single place | Medium | A signed provider contract | Needs decision |  | [decision register](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/decision-register.md) |
| S-18 | Add a **scheduled daily run** (CI schedule or task runner) with an alert on suppression | Makes the three-day slate genuinely automatic and surfaces failures instead of hiding them | Medium | A hosting decision for the job | Needs decision |  | [Pages is static](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) |
| S-19 | Add a **reproducibility bundle**: model version, code hash, input snapshot hash and environment per run | Lets an independent reviewer rerun a published forecast | Medium | Nothing | Proposed |  | [engine contracts](https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/contracts.py) |
| S-20 | Add a **baseline suite** (market line, recent-average, opponent-adjusted) so every candidate is compared to something simple | Without baselines, a model can look skilled while being worse than a one-line average | Medium | A licensed dataset | Needs decision |  | [scikit-learn cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) |
| S-21 | Add a **multiple-testing register** that counts every candidate variant examined | Protects against picking the luckiest of many tests | Low | Nothing | Proposed |  | [scikit-learn cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) |
| S-22 | Add **shadow (no-bet) operation** before any promotion, with a reconciliation report | Produces prospective evidence without staking anything | Medium | A licensed dataset and a market specification | Needs decision |  | [validation plan](https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/validation-plan.md) |
| S-23 | Add **automated link and source checking** to the publish pipeline so a dead source is caught before publication | A broken source link undermines every table that cites it | Low | Network access in the job runner | Proposed |  | [site checker](https://github.com/wingbangboozle1-lang/NBA4/blob/main/scripts/check_site.py) |

## D. Overlap map between the two registers

The two proposal sets were written independently and overlap on several ideas. The overlaps are listed so the reviewer can accept one wording and reject the duplicate, rather than quietly losing either:

- **P-10 ↔ S-06 / S-10** — distinguishing “no data”, “no edge” and “not computed” wherever a cell is blank.
- **P-11 ↔ S-15** — moving commercial or live functionality off the static host only if the product becomes commercial.
- **P-12 ↔ S-13 / S-14** — responsible-use and age/territory notices.
- **P-04 ↔ S-03** — gate-by-gate status made visible (scorecard vs checklist).
- **P-06 ↔ S-08** — correlation reporting with sample counts and clustered intervals.
- **P-03 ↔ S-19** — reproducibility of every issued forecast (ledger schema vs reproducibility bundle).
- **P-05 ↔ S-21** — pre-registered rules and multiple-testing discipline.

## E. Open questions the suggestions cannot answer

These need input from the project owner; no source can settle them:

1. Is the intent personal research, a public tipster page, or a commercial product with rewards?
2. Is there a budget for a licensed data feed? Without one, every numerical output stays off by design.
3. Which jurisdictions would see picks, and would any page link to a bookmaker?
4. Is a correctly empty dashboard acceptable while validation runs, or is a measurable — even if unprofitable — pipeline needed sooner?
5. Who is the accountable decision-maker when a suggestion is accepted or rejected?

## F. Review notes and maintenance rule

1. Rows marked **Needs decision** / **Blocked** cannot be implemented before the dependency in the "Depends on" column is closed; implementing them earlier would create a number that cannot be justified.
2. The **Decision** column is the reviewer's field. Suggested values: `Accept`, `Reject`, `Defer`, or a note. An empty cell means "not yet reviewed".
3. Suggestions marked **Accepted** are implemented only after the decision is recorded here and in [`COORDINATION.md`](../COORDINATION.md), so the change history stays traceable.
4. No suggestion may add a number that an official source does not support. Every implemented page keeps the rule that a value without an official source stays blank and flagged - see the [source register](sources.md) and the [site specification](site-spec.md).
5. Additions to this register follow the same rule as the rest of the repository: a suggestion must state its options and its trade-off, and any factual claim in it must carry an official source link. A suggestion without an alternative is a request, not a suggestion, and should be recorded as one.
