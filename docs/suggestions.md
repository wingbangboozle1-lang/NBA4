# Suggestions register

**Status:** proposals only. Nothing in this document has been implemented. Its rendered form is [`suggestions.html`](../suggestions.html), which is the version to review.

**Purpose.** The dashboard is deliberately empty of numerical outputs. That is honest, but it leaves a reviewer with no clear next action. This register converts “we cannot compute anything yet” into a small number of decisions and a prioritised build list, so a path can be chosen before implementation starts.

## Method

Each suggestion was written against a gap that is visible in the current repository, not against a hypothetical product. Every entry carries:

- a **problem** statement tied to an existing page or document;
- at least two **options** with an explicit trade-off, because a single-option proposal is a decision that has already been made;
- an **effort** estimate for one working session;
- a **status** — `Proposed`, `Needs a decision`, `Blocked`, or `Rejected`;
- an **official source** for the factual basis or the method, on the same approved-domain rule as the rest of the site.

Suggestions that would require data the project is not permitted to use are marked `Blocked` rather than quietly deprioritised. Suggestions that would weaken an honesty control are marked `Rejected` with the reason.

## The four gating decisions

Nothing else can be built until these are answered. They are reproduced on the site as the “Decision queue”.

| Decision | Path A | Path B | Consequence of choosing |
| --- | --- | --- | --- |
| D-1 Data rights | Licence a provider that permits betting use in writing | Stay private and non-commercial, publish no numbers | A unlocks model work and public lines; B keeps the site an evidence shell. NBA Stats directly is not an option either way — see [NBA Terms §9](https://www.nba.com/termsofuse). |
| D-2 Product type | Informational analytics, no wagers or rewards | Picks/leaderboard with rewards | A is served by the current static host; B is a regulated activity needing classification, age controls and different hosting — see [Ksa](https://kansspelautoriteit.nl/remote-gambling-act-force). |
| D-3 First market | One single-bet market (e.g. game total) | Player props or same-game parlays | A needs team-level inputs only; B needs joint distributions and a validated minutes model first — see [NBA Stats glossary](https://www.nba.com/stats/help/glossary). |
| D-4 Success rule | Calibration-first (proper score plus reliability curve) | Return-first (ROI against a benchmark price) | A can be tested without a price feed; B cannot begin until licensed prices and settlement exist — see [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html). |

**Recommended order:** D-1 → D-2 → D-4 → D-3. Rights and product type are legal preconditions; the success rule must be fixed before any holdout is looked at; the market choice follows from which inputs are actually licensed.

## Why the order matters

A common failure mode in this kind of project is to build the ranking and reward layer first, because it is the visible part, and to bolt validation on afterwards. That produces a leaderboard of strategies whose apparent skill cannot be distinguished from the sample they were selected on. The ordering above deliberately puts the unglamorous, blocking work first.

The second failure mode is treating “no pick” as a defect. On this site a blank cell is a control: it means the evidence chain did not close. Suggestion S-10 exists so that a cell can distinguish *not computed* from *computed and excluded*, without ever implying a number that is not supported.

## Open questions the suggestions cannot answer

These need input from the project owner; no source can settle them:

1. Is the intent personal research, a public tipster page, or a commercial product with rewards?
2. Is there a budget for a licensed data feed? Without one, every numerical output stays off by design.
3. Which jurisdictions would see picks, and would any page link to a bookmaker?
4. Is a correctly empty dashboard acceptable while validation runs, or is a measurable — even if unprofitable — pipeline needed sooner?
5. Who is the accountable decision-maker when a suggestion is accepted or rejected?

## Maintenance rule

Additions to this register follow the same rule as the rest of the repository: a suggestion must state its options and its trade-off, and any factual claim in it must carry an official source link. A suggestion without an alternative is a request, not a suggestion, and should be recorded as one.
