#!/usr/bin/env python3
"""One-shot register patch for the 2026-11-16 pass (task BB/BD close-outs):
review.html pass-9 flag table, questions.html Q23-Q25, suggestions.html S-24/S-25."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INJ = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-16_09_15AM.pdf"
G18 = "https://www.nba.com/games?date=2026-11-18"
G15 = "https://www.nba.com/games?date=2026-11-15"
G16 = "https://www.nba.com/games?date=2026-11-16"
TRAD = "https://www.nba.com/stats/teams/traditional"
SURF = "https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/surfaces.py"
LOG = "https://github.com/wingbangboozle1-lang/NBA4/blob/main/docs/verification-pass-7ce5c0cc.md"

FLAG = '<span class="flag">'
FLAG_RED = '<span class="flag flag-red">'
FLAG_GREEN = '<span class="flag flag-green">'
FLAG_BLUE = '<span class="flag flag-blue">'


def frow(fid, sev, what, action, src):
    return (
        f'              <tr><td><strong>{fid}</strong></td><td>{sev}</td><td>{what}</td>'
        f'<td>{action}</td><td>{src}</td></tr>'
    )


rows = "\n".join([
    frow("P9-01", FLAG + "Low</span><br>Printing variance (closed)",
         'The 09:15 AM ET report prints the name cell &ldquo;Bennedict&rdquo; where the 09:00 AM '
         'report prints &ldquo;Benedict&rdquo; (Mathurin). Same status, same reason, one-for-one leftover.',
         'Recorded as a printing variance in the consecutive-revision diff (0 status changes, 0 reason '
         'changes, 1 printing variance), never merged and never reported as &ldquo;no changes&rdquo;.',
         f'<a class="source-link" href="{INJ}" target="_blank" rel="noopener noreferrer">09:15 AM report</a>'),
    frow("P9-02", FLAG_RED + "Open</span><br>Lost team cells (09:15 AM report)",
         '7 rows lost their Team cell at PDF page breaks: MEM@WAS (Jerome Ty / Pippen Jr. Scotty / '
         'Post Quinten / Saunders Richie / Stewart Isaiah) and GSW@NOP (Reese Julian / Watford Trendon).',
         'Team cell left blank and flagged; player names kept; never re-attributed by inference. '
         'Owner decides whether such rows are suppressed instead (Q19).',
         f'<a class="source-link" href="{INJ}" target="_blank" rel="noopener noreferrer">09:15 AM report</a>'),
    frow("P9-03", FLAG_RED + "Open</span><br>GSW rows carry no reason cell",
         'The GSW block prints 6 rows without a reason cell. Butler III&rsquo;s lone status cell reads '
         '&ldquo;Injury/Illness - Right ACL Repair / Surgery&rdquo; with no status word.',
         'Reason left blank and flagged; Butler III&rsquo;s status recorded verbatim as printed with no '
         'status asserted. No status is inferred from a reason string.',
         f'<a class="source-link" href="{INJ}" target="_blank" rel="noopener noreferrer">09:15 AM report</a>'),
    frow("P9-04", FLAG_RED + "Open (owner)</span><br>Tip-off conflicts (rows 266/267 + AN-02)",
         'Games page vs August schedule PDF: row 266 BOS@DEN 9:30 PM ET vs 9:00; row 267 GSW@DAL 8:00 PM ET '
         'vs 9:30 (8:30 local). AN-02 reconfirmed on rows 256 CHA@LAL (11:00 vs 10:00) and 257 UTA@LAC '
         '(10:30 vs 11:00).',
         'Both readings kept side by side in the slate file and page; never reconciled. The August PDF '
         'carries &ldquo;SUBJECT TO CHANGE&rdquo;; the games page is the newer reading. Owner decides '
         'which is authoritative going forward (Q23).',
         f'<a class="source-link" href="{G18}" target="_blank" rel="noopener noreferrer">Games page 11/18</a>'),
    frow("P9-05", FLAG_RED + "Open (owner)</span><br>11/15 quarter scores not transcribed",
         'The scoreboard cards for the nine 11/15 games print finals but no quarter scores; the '
         'brief&rsquo;s row format requires Q1&ndash;Q4 per team. The 11/14 snapshot keeps its full quarter rows.',
         'Quarter cells published blank + flagged (NOT CHECKED), never reconstructed. Settlement of the '
         'day is BLOCKED by this gap and by D-01/IR-T4 (Q24).',
         f'<a class="source-link" href="{G15}" target="_blank" rel="noopener noreferrer">Games page 11/15</a>'),
    frow("P9-06", FLAG + "Medium</span><br>Traditional team-stat page: read gap closed by a parallel pass",
         'This session&rsquo;s fetch of nba.com/stats/teams/traditional served only filter controls '
         '(chunk 0; the rows arrive in later chunks), so no row count was claimed here. The parallel '
         'session&rsquo;s re-check (docs/team-stats-recheck-cbc8e41a.md) read all five chunks and '
         'verified 30 of 30 rows plus the printed 28-column + RANK schema with six machine checks.',
         'Read gap CLOSED by that evidence (P9-06). What remains is an owner decision, not a read gap: '
         'whether the traditional rows are transcribed onto the site at all (the parallel pass kept '
         'full-table publication as an owner decision; this page carries the advanced/opponent rows). '
         'The team-stats provenance table states exactly this.',
         f'<a class="source-link" href="{TRAD}" target="_blank" rel="noopener noreferrer">Traditional page</a>'),
    frow("P9-07", FLAG + "Low</span><br>Superseded snapshot label (closed)",
         'The 11/15 06:15 AM snapshot&rsquo;s matchups_not_in_snapshot list calls the 11/16 LAL game '
         '&ldquo;CHA@LAC&rdquo;; the official game is CHA@LAL (confirmed on the games page and by the '
         'report&rsquo;s own LAL block).',
         'The historical file is not edited (dated record). The correction is published here and the '
         'current renderer uses CHA@LAL; the 11/16 slate row 256 cites the game-id slug that prints '
         '&ldquo;cha-vs-lal&rdquo;.',
         f'<a class="source-link" href="{G16}" target="_blank" rel="noopener noreferrer">Games page 11/16</a>'),
    frow("P9-08", FLAG_RED + "Open (owner)</span><br>Surface audit not wired into the build check",
         'engine/surfaces.py&rsquo;s audit_page_surface is unit-tested and its docstring says '
         'scripts/check_site.py calls it, but no call site exists (found by the 2026-11-16 line-by-line '
         'review, F-S1).',
         'Flagged, not silently wired: wiring needs a policy decision declaring which blocked-field '
         'headers each projection page enforces. Until then the field-level surface registry remains the '
         'enforcement point.',
         f'<a class="source-link" href="{SURF}" target="_blank" rel="noopener noreferrer">engine/surfaces.py</a>'),
    frow("P9-09", FLAG_GREEN + "Closed (decision recorded)</span><br>Engine public API (AN-09 / IR-T1)",
         'PR #53 and the AX set both implement eleven requirement items; PR #52&rsquo;s merge note '
         'demanded a line-by-line review of the unreviewed modules and an explicit public-API decision '
         '(&ldquo;Not silently fixed&rdquo;).',
         'Review completed: 3 defects fixed with regression tests (300 tests OK), 3 items flagged '
         '(P9-08, IR-09, external timestamp anchoring). Decision: one flat public API, both sets '
         'exported; no v1/v2 split. Recorded in docs/engine-modules-7ce5c0cc.md and docs/engine.md.',
         f'<a class="source-link" href="{LOG}" target="_blank" rel="noopener noreferrer">verification pass log</a>'),
])

section = f'''      <section class="section" aria-labelledby="pass9-title">
        <div class="section-heading"><div><h2 id="pass9-title">Verification pass 9 (16 Nov 2026)</h2><p>The ninth daily refresh (session arena/7ce5c0cc-nba4, tasks BB&ndash;BE): official sources re-read at 14:31&ndash;14:52 UTC, the 2026-11-16 snapshots published, the advanced/opponent team-stat pages closed out (AN-04), the three gate-status pages built, and the PR #53 engine modules reviewed line by line. Flags below are this pass&rsquo;s irregularities; the full fetch log is in the pass record.</p></div><a class="section-link" href="{LOG}">Full pass log &rarr;</a></div>
        <div class="table-card table-wrap">
          <table class="data-table">
            <thead><tr><th scope="col">ID</th><th scope="col">Severity</th><th scope="col">Irregularity</th><th scope="col">Action taken or status</th><th scope="col">Source for review</th></tr></thead>
            <tbody>
{rows}
            </tbody>
          </table>
        </div>
      </section>

'''

rev = ROOT / "review.html"
t = rev.read_text(encoding="utf-8")
anchor = '        <article class="panel"><h2>Review sequence</h2>'
assert anchor in t, "review.html anchor not found"
t = t.replace(anchor, section + anchor, 1)
rev.write_text(t, encoding="utf-8")
print("review.html updated")

qrows = (
    '              <tr><td><strong>Q23 &middot; P1</strong><br>Tip authority</td>'
    '<td>When the games page and the August schedule PDF print different tip times, which is '
    'authoritative for publication?</td>'
    '<td>The August PDF says &ldquo;SUBJECT TO CHANGE&rdquo;; the games page is newer and carries '
    'game-id slugs. Both readings are recorded for rows 256, 257, 266, 267 (flags AN-02, P9-04).</td>'
    f'<td>{FLAG_RED}Unresolved</span><br>No owner decision; both readings are kept and never reconciled.</td>'
    '<td>Record a rule: e.g. publish the games-page tip as current with the PDF tip in parentheses '
    'and a revision timestamp; re-check at each refresh.</td>'
    f'<td><a class="source-link" href="{G18}" target="_blank" rel="noopener noreferrer">Games page 11/18</a>'
    '<br><a class="source-link" href="https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf"'
    ' target="_blank" rel="noopener noreferrer">Schedule PDF</a></td></tr>\n'
    '              <tr><td><strong>Q24 &middot; P1</strong><br>Settlement evidence</td>'
    '<td>What evidence closes the 11/15 quarter-score gap (flag P9-05) and who anchors the ledger '
    'hash chain to an external timestamp (review F-L3)?</td>'
    '<td>Game-summary pages were not read this pass; the scoreboard cards print no quarter scores. '
    'The ledger binds its own hashes but cannot bind them to a third-party time source.</td>'
    f'<td>{FLAG_RED}Unresolved</span><br>Settlement BLOCKED (P9-05 + D-01/IR-T4); external anchoring '
    'is an owner decision.</td>'
    '<td>Read the official game-summary pages for 11/15 to transcribe verified quarters; decide on a '
    'transparency-log/notary service before any pick is published.</td>'
    f'<td><a class="source-link" href="{G15}" target="_blank" rel="noopener noreferrer">Games page 11/15</a>'
    '<br><a class="source-link" href="https://www.nba.com/termsofuse" target="_blank" rel="noopener noreferrer">'
    'NBA Terms</a></td></tr>\n'
    '              <tr><td><strong>Q25 &middot; P2</strong><br>Stats extraction</td>'
    '<td>Should the traditional team-stat rows be fetched another way (official stats API or a '
    'rendered capture) to close flag P9-06?</td>'
    '<td>The advanced and opponent pages serve 30 rows each to the extraction; the traditional page '
    'serves only filter controls. No row count is claimed for it.</td>'
    f'<td>{FLAG}Unresolved</span><br>Gap is documented and the decision-relevant columns are carried '
    'from the two pages that do serve rows.</td>'
    '<td>Try the league&rsquo;s official stats endpoints for the traditional rows; if unavailable, '
    'keep the gap flagged rather than transcribing from an unofficial mirror.</td>'
    f'<td><a class="source-link" href="{TRAD}" target="_blank" rel="noopener noreferrer">Traditional page</a>'
    '<br><a class="source-link" href="https://www.nba.com/stats/teams/advanced" target="_blank"'
    ' rel="noopener noreferrer">Advanced page</a></td></tr>\n'
)

q = ROOT / "questions.html"
tq = q.read_text(encoding="utf-8")
idx = tq.index("              <tr><td><strong>Q22")
end = tq.index("</tbody>", idx)
tq = tq[:end] + qrows + tq[end:]
q.write_text(tq, encoding="utf-8")
print("questions.html updated")

srows = (
    '              <tr><td><strong>S-24</strong></td>'
    '<td>Wire the surface-split page audit into scripts/check_site.py with a declared blocked-header '
    'list per projection page.</td>'
    '<td>Closes review flag P9-08: a bet-gated number can then never render on a projection page '
    'without failing the build.</td>'
    '<td>Low</td><td>A policy decision on which headers each page enforces</td>'
    f'<td>{FLAG_BLUE}Proposed</span></td><td>{FLAG_BLUE}Awaiting review</span></td>'
    '<td><a class="source-link" href="https://github.com/wingbangboozle1-lang/NBA4/blob/main/engine/surfaces.py"'
    ' target="_blank" rel="noopener noreferrer">engine surfaces</a></td></tr>\n'
    '              <tr><td><strong>S-25</strong></td>'
    '<td>Adopt a written tip-time authority rule (games page as current, August PDF as historical) '
    'with both readings kept in the snapshot and a revision timestamp.</td>'
    '<td>Ends the AN-02/P9-04 ambiguity without discarding either official reading.</td>'
    '<td>Low</td><td>An owner decision (Q23)</td>'
    f'<td>{FLAG_BLUE}Proposed</span></td><td>{FLAG_BLUE}Awaiting review</span></td>'
    f'<td><a class="source-link" href="{G18}" target="_blank" rel="noopener noreferrer">Games page</a></td></tr>\n'
)

s = ROOT / "suggestions.html"
ts = s.read_text(encoding="utf-8")
idx = ts.rindex("</tbody>")
ts = ts[:idx] + srows + ts[idx:]
s.write_text(ts, encoding="utf-8")
print("suggestions.html updated")
