# Verification pass 9b (session `arena/cc82e369-nba4`, 2026-11-16 UTC)

**Scope of this pass.** This session works the engine surface only (tasks BF–BI
on the [coordination board](../COORDINATION.md)), so this pass verifies the
official sources those engine modules rest on and nothing else. The slate,
injury-report, results and standings refresh for 2026-11-16 belongs to session
`arena/2b0e7d87-nba4` (tasks BB–BE) and is not duplicated here.

Fetch times in this document are UTC. The three team-stat pages were read on
**2026-11-16 between 14:33 and 14:41 UTC**.

## 1. What was verified, and how

| Step | What was done | Result | Source |
| --- | --- | --- | --- |
| Team-stat pages re-read | All three pages fetched in full: traditional (5 chunks), opponent (2 chunks), advanced (2 chunks) | 30 of 30 rows read on each page, closing the AN-04 half-read on the [Flagged for Review page](../review.html) | [Teams Traditional](https://www.nba.com/stats/teams/traditional) |
| Glossary definitions | PACE, Poss and PPP entries read and quoted | The three definitions the possession re-cut needs are quoted verbatim in section 2 | [Stat Glossary](https://www.nba.com/stats/help/glossary) |
| Internal consistency | Recomputed OffRtg, DefRtg, NetRtg and POSS for every team from the traditional and opponent pages | See section 4: the recomputation reproduces the printed ratings, worst gap 0.48 rating points | [Teams Advanced](https://www.nba.com/stats/teams/advanced) |
| End-to-end module check | The 30 rows were fed through `engine/teamstats.recut` itself | 30 of 30 teams joined, no flags, every check passes at the module's default tolerances | [Teams Traditional](https://www.nba.com/stats/teams/traditional) |
| Cross-check | Compared the win-loss columns with the 2026-11-15 standings snapshot already in the repository | Differences found and explained, not reconciled: see CC-02 | [NBA.com standings](https://www.nba.com/standings) |

## 2. The official definitions the re-cut relies on

Quoted from [NBA Stats glossary](https://www.nba.com/stats/help/glossary), chunk 5, read 2026-11-16:

* **PACE** — "Name: Pace. Definition: The number of possessions per 48 minutes for a team or player. Type: Advanced. Contexts: Player, Team."
* **Poss** — "Name: Possessions. Definition: The number of possessions played by a player or team. Please note: an Offensive Rebound does not create another possession, it simply makes the existing possession longer. Type: Play Type. Contexts: Play Type, Player, Team."
* **PPP** — "Name: Points Per Possession. Definition: The number of points a player or team scores per possession. Type: Play Type. Contexts: Play Type, Player, Team."

The second sentence of the Poss definition is the one that matters for the
model: an offensive rebound extends a possession rather than starting a new
one, which is why the re-cut divides points by possessions rather than adding
two scoring averages together.


## 3. The three pages, all 30 rows of each

The pages print a "30 Rows" counter and "Page All 1 of 1"; the rows are
reproduced below in the order the page printed them (sorted by winning
percentage, descending). Values are per game as the page served them, except
the advanced page's MIN and POSS, which are season totals as printed.

### 3.1 Traditional page — the team's own box score

| Team | GP | W | L | MIN | PTS | FGA | FGM | FTA | OREB | TOV | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Los Angeles Lakers | 14 | 12 | 2 | 48.0 | 122.8 | 83.8 | 42.1 | 30.2 | 11.4 | 16.8 | [traditional](https://www.nba.com/stats/teams/traditional) |
| San Antonio Spurs | 14 | 12 | 2 | 48.4 | 118.8 | 91.5 | 42.8 | 26.0 | 12.9 | 12.3 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Boston Celtics | 13 | 11 | 2 | 48.4 | 115.5 | 87.8 | 40.4 | 23.2 | 13.5 | 14.5 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Houston Rockets | 14 | 11 | 3 | 48.0 | 118.4 | 87.1 | 42.3 | 25.6 | 13.5 | 14.4 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Philadelphia 76ers | 14 | 11 | 3 | 48.0 | 112.6 | 87.9 | 40.1 | 25.9 | 10.0 | 12.8 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Portland Trail Blazers | 12 | 9 | 3 | 48.0 | 119.6 | 84.7 | 39.8 | 30.7 | 11.5 | 16.3 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Memphis Grizzlies | 13 | 9 | 4 | 48.4 | 120.6 | 89.4 | 42.1 | 24.7 | 12.5 | 15.8 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Minnesota Timberwolves | 13 | 9 | 4 | 48.4 | 118.3 | 90.9 | 43.4 | 25.5 | 13.8 | 15.9 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Detroit Pistons | 12 | 8 | 4 | 48.8 | 115.7 | 88.4 | 40.9 | 25.8 | 12.2 | 14.3 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Oklahoma City Thunder | 14 | 9 | 5 | 48.0 | 112.1 | 90.5 | 41.5 | 22.3 | 11.6 | 13.4 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Denver Nuggets | 11 | 7 | 4 | 48.5 | 114.6 | 85.2 | 41.5 | 26.5 | 10.1 | 13.4 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Golden State Warriors | 13 | 8 | 5 | 48.4 | 116.7 | 87.0 | 40.0 | 25.1 | 12.5 | 16.0 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Atlanta Hawks | 14 | 8 | 6 | 48.4 | 117.8 | 96.4 | 43.5 | 21.4 | 13.9 | 15.4 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Miami Heat | 13 | 7 | 6 | 48.4 | 118.7 | 89.5 | 42.0 | 28.7 | 10.5 | 14.4 | [traditional](https://www.nba.com/stats/teams/traditional) |
| New York Knicks | 13 | 7 | 6 | 48.4 | 109.9 | 88.8 | 38.7 | 22.4 | 13.6 | 14.7 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Cleveland Cavaliers | 14 | 7 | 7 | 48.4 | 117.5 | 88.7 | 41.8 | 24.3 | 10.7 | 13.5 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Dallas Mavericks | 14 | 7 | 7 | 48.0 | 112.1 | 88.4 | 40.6 | 23.1 | 12.6 | 16.0 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Orlando Magic | 12 | 5 | 7 | 48.4 | 108.3 | 85.8 | 38.4 | 22.6 | 11.0 | 16.8 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Phoenix Suns | 12 | 5 | 7 | 48.0 | 112.7 | 88.8 | 41.4 | 20.8 | 10.9 | 14.2 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Toronto Raptors | 13 | 5 | 8 | 48.4 | 113.8 | 91.7 | 41.5 | 26.0 | 14.0 | 14.5 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Indiana Pacers | 14 | 5 | 9 | 48.0 | 112.1 | 87.1 | 40.9 | 24.0 | 9.6 | 14.5 | [traditional](https://www.nba.com/stats/teams/traditional) |
| LA Clippers | 12 | 4 | 8 | 48.4 | 112.3 | 84.4 | 39.3 | 24.4 | 10.1 | 17.8 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Charlotte Hornets | 13 | 4 | 9 | 48.0 | 99.1 | 87.0 | 34.8 | 18.8 | 15.2 | 19.3 | [traditional](https://www.nba.com/stats/teams/traditional) |
| New Orleans Pelicans | 14 | 4 | 10 | 49.1 | 115.9 | 86.2 | 40.1 | 32.1 | 10.6 | 16.1 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Washington Wizards | 14 | 4 | 10 | 48.7 | 110.6 | 87.3 | 39.9 | 25.9 | 10.9 | 14.9 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Brooklyn Nets | 12 | 3 | 9 | 48.4 | 110.2 | 83.9 | 37.1 | 28.3 | 11.6 | 17.7 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Chicago Bulls | 12 | 3 | 9 | 48.4 | 114.6 | 89.4 | 39.9 | 29.0 | 12.6 | 17.3 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Sacramento Kings | 13 | 1 | 12 | 48.0 | 107.8 | 85.9 | 39.1 | 22.5 | 9.8 | 17.5 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Milwaukee Bucks | 14 | 1 | 13 | 48.0 | 106.1 | 88.9 | 37.7 | 21.1 | 13.6 | 16.9 | [traditional](https://www.nba.com/stats/teams/traditional) |
| Utah Jazz | 14 | 1 | 13 | 48.7 | 107.1 | 87.0 | 38.0 | 24.4 | 11.9 | 16.6 | [traditional](https://www.nba.com/stats/teams/traditional) |

### 3.2 Opponent page — the opposition's box score

Every column on this page is prefixed "Opp" by the page itself. The final
column is labelled "+/-" but it prints the **opponent's** margin: for every one
of the 30 rows it is the negative of the team's own margin on the traditional
page (for example Charlotte: -10.8 there, +10.8 here). It is recorded here
because averaging the two columns, or reading this one as the team's margin,
would invert the sign of every team in the league. This is flag CC-01.

| Team | Opp PTS | Opp FGA | Opp FGM | Opp FTA | Opp OREB | Opp TOV | +/- (opponent's) | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Los Angeles Lakers | 114.9 | 86.1 | 39.2 | 28.2 | 13.6 | 18.4 | -7.9 | [opponent](https://www.nba.com/stats/teams/opponent) |
| San Antonio Spurs | 105.9 | 89.2 | 38.9 | 19.1 | 10.9 | 14.5 | -12.9 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Boston Celtics | 102.4 | 84.8 | 35.4 | 22.4 | 12.6 | 16.8 | -13.2 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Houston Rockets | 108.2 | 87.5 | 39.6 | 22.4 | 12.1 | 15.0 | -10.1 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Philadelphia 76ers | 110.4 | 87.5 | 40.1 | 24.1 | 11.0 | 14.8 | -2.1 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Memphis Grizzlies | 111.7 | 90.0 | 40.5 | 24.2 | 12.0 | 14.2 | -8.9 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Minnesota Timberwolves | 106.8 | 89.0 | 38.6 | 23.3 | 12.3 | 16.8 | -11.5 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Oklahoma City Thunder | 107.1 | 88.9 | 37.3 | 21.9 | 12.0 | 14.9 | -5.1 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Portland Trail Blazers | 111.8 | 87.1 | 38.8 | 27.6 | 11.5 | 14.0 | -7.8 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Atlanta Hawks | 116.1 | 87.2 | 41.8 | 25.1 | 11.6 | 18.9 | -1.7 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Detroit Pistons | 110.3 | 87.3 | 38.6 | 26.8 | 13.0 | 17.7 | -5.4 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Golden State Warriors | 112.4 | 88.2 | 40.6 | 23.4 | 12.2 | 16.3 | -4.3 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Cleveland Cavaliers | 115.9 | 92.5 | 41.6 | 23.5 | 12.7 | 12.6 | -1.6 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Dallas Mavericks | 114.6 | 89.1 | 42.1 | 23.4 | 12.6 | 15.6 | 2.5 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Denver Nuggets | 112.8 | 90.2 | 41.5 | 19.9 | 12.9 | 14.4 | -1.8 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Miami Heat | 119.8 | 89.5 | 43.1 | 23.1 | 11.4 | 16.7 | 1.2 | [opponent](https://www.nba.com/stats/teams/opponent) |
| New York Knicks | 104.0 | 86.4 | 37.4 | 22.1 | 10.9 | 13.4 | -5.9 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Indiana Pacers | 114.5 | 89.3 | 40.9 | 23.7 | 11.5 | 14.9 | 2.4 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Orlando Magic | 112.8 | 85.3 | 39.8 | 25.9 | 10.3 | 15.2 | 4.4 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Phoenix Suns | 117.3 | 86.8 | 40.6 | 28.1 | 14.0 | 17.2 | 4.7 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Toronto Raptors | 112.8 | 81.0 | 38.4 | 28.8 | 10.7 | 18.9 | -1.0 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Charlotte Hornets | 109.8 | 82.5 | 39.2 | 22.0 | 8.6 | 14.2 | 10.8 | [opponent](https://www.nba.com/stats/teams/opponent) |
| LA Clippers | 116.5 | 88.0 | 42.6 | 24.7 | 12.1 | 16.1 | 4.2 | [opponent](https://www.nba.com/stats/teams/opponent) |
| New Orleans Pelicans | 124.9 | 87.9 | 43.4 | 31.0 | 11.4 | 15.7 | 9.1 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Washington Wizards | 118.0 | 93.9 | 43.2 | 22.5 | 14.3 | 13.7 | 7.4 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Brooklyn Nets | 116.4 | 84.6 | 39.6 | 29.2 | 10.7 | 16.3 | 6.3 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Chicago Bulls | 125.9 | 94.8 | 45.2 | 28.7 | 14.0 | 14.3 | 11.3 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Milwaukee Bucks | 119.7 | 92.4 | 42.6 | 25.6 | 14.6 | 13.4 | 13.6 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Sacramento Kings | 121.2 | 85.5 | 42.2 | 28.9 | 10.3 | 14.6 | 13.5 | [opponent](https://www.nba.com/stats/teams/opponent) |
| Utah Jazz | 118.0 | 87.6 | 39.8 | 31.4 | 11.1 | 13.8 | 10.9 | [opponent](https://www.nba.com/stats/teams/opponent) |

### 3.3 Advanced page — the page's own rates

| Team | GP | MIN (season) | PACE | POSS | OffRtg | DefRtg | NetRtg | eFG% | TOV% | OREB% | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Los Angeles Lakers | 14 | 672.0 | 100.64 | 1408 | 122.1 | 114.0 | 8.0 | 58.8 | 16.7 | 33.3 | [advanced](https://www.nba.com/stats/teams/advanced) |
| San Antonio Spurs | 14 | 677.0 | 98.77 | 1395 | 119.2 | 106.6 | 12.6 | 53.5 | 12.3 | 33.3 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Boston Celtics | 13 | 629.0 | 96.53 | 1263 | 118.9 | 105.1 | 13.9 | 55.4 | 15.0 | 33.3 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Houston Rockets | 14 | 672.0 | 97.68 | 1367 | 121.2 | 110.7 | 10.5 | 55.9 | 14.8 | 35.9 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Philadelphia 76ers | 14 | 672.0 | 100.21 | 1404 | 112.3 | 110.3 | 2.0 | 52.6 | 12.7 | 27.5 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Memphis Grizzlies | 13 | 629.0 | 100.46 | 1318 | 119.0 | 110.4 | 8.5 | 55.8 | 15.6 | 34.2 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Minnesota Timberwolves | 13 | 629.0 | 101.27 | 1326 | 116.0 | 104.5 | 11.5 | 55.5 | 15.6 | 35.4 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Oklahoma City Thunder | 14 | 672.0 | 98.82 | 1384 | 113.4 | 108.4 | 5.1 | 51.9 | 13.5 | 32.1 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Portland Trail Blazers | 12 | 576.0 | 100.67 | 1208 | 118.8 | 111.1 | 7.7 | 56.3 | 16.2 | 33.3 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Atlanta Hawks | 14 | 677.0 | 103.69 | 1462 | 112.8 | 111.1 | 1.7 | 52.7 | 14.7 | 33.0 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Detroit Pistons | 12 | 586.0 | 99.48 | 1217 | 114.1 | 109.2 | 4.9 | 53.9 | 14.1 | 29.8 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Golden State Warriors | 13 | 629.0 | 99.66 | 1307 | 116.1 | 112.0 | 4.1 | 55.4 | 15.9 | 32.7 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Cleveland Cavaliers | 14 | 677.0 | 99.72 | 1407 | 116.9 | 115.4 | 1.6 | 55.8 | 13.4 | 29.1 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Dallas Mavericks | 14 | 672.0 | 100.18 | 1404 | 111.8 | 114.5 | -2.7 | 53.2 | 16.0 | 32.9 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Denver Nuggets | 11 | 533.0 | 97.67 | 1087 | 116.0 | 114.7 | 1.3 | 55.0 | 13.5 | 30.2 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Miami Heat | 13 | 629.0 | 102.49 | 1345 | 114.7 | 116.2 | -1.5 | 54.5 | 13.9 | 30.3 | [advanced](https://www.nba.com/stats/teams/advanced) |
| New York Knicks | 13 | 629.0 | 95.66 | 1257 | 113.7 | 108.2 | 5.5 | 51.9 | 15.2 | 36.7 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Indiana Pacers | 14 | 672.0 | 101.25 | 1415 | 110.9 | 112.9 | -2.0 | 53.8 | 14.3 | 24.6 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Orlando Magic | 12 | 581.0 | 98.23 | 1185 | 109.7 | 113.4 | -3.7 | 52.8 | 17.0 | 31.7 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Phoenix Suns | 12 | 576.0 | 98.79 | 1183 | 114.3 | 118.5 | -4.2 | 54.3 | 14.4 | 30.0 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Toronto Raptors | 13 | 629.0 | 99.55 | 1302 | 113.6 | 112.2 | 1.4 | 51.7 | 14.4 | 35.8 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Charlotte Hornets | 13 | 624.0 | 96.65 | 1256 | 102.5 | 113.6 | -11.1 | 48.0 | 20.0 | 36.5 | [advanced](https://www.nba.com/stats/teams/advanced) |
| LA Clippers | 12 | 581.0 | 100.05 | 1210 | 111.4 | 115.3 | -3.9 | 55.1 | 17.6 | 29.6 | [advanced](https://www.nba.com/stats/teams/advanced) |
| New Orleans Pelicans | 14 | 687.0 | 101.83 | 1457 | 111.3 | 120.0 | -8.6 | 51.9 | 15.4 | 29.7 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Washington Wizards | 14 | 682.0 | 99.73 | 1416 | 109.4 | 116.5 | -7.1 | 51.6 | 14.7 | 28.9 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Brooklyn Nets | 12 | 581.0 | 99.47 | 1204 | 109.8 | 116.0 | -6.2 | 52.9 | 17.6 | 32.1 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Chicago Bulls | 12 | 581.0 | 103.81 | 1257 | 109.4 | 120.3 | -10.9 | 51.7 | 16.5 | 30.7 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Milwaukee Bucks | 14 | 672.0 | 100.68 | 1410 | 105.4 | 118.9 | -13.6 | 50.9 | 16.7 | 30.5 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Sacramento Kings | 13 | 624.0 | 101.08 | 1312 | 106.8 | 119.8 | -13.0 | 52.7 | 17.3 | 28.4 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Utah Jazz | 14 | 682.0 | 100.22 | 1426 | 105.1 | 116.2 | -11.1 | 50.8 | 16.3 | 29.0 | [advanced](https://www.nba.com/stats/teams/advanced) |

## 4. Internal consistency: does the possession model reproduce the page?

For each team, possessions per game were recomputed from the printed pace and
the traditional page's own MIN column (`possessions = PACE x MIN/48`), then
points were divided by that number. The result is compared with the OffRtg,
DefRtg, NetRtg and POSS the advanced page prints for itself.

* Largest absolute difference, offensive rating: **0.36** rating points
* Largest absolute difference, defensive rating: **0.48** (Orlando Magic)
* Largest absolute difference, net rating: **0.84**
* Largest absolute difference, season possessions: **3.99** on 1,185 (0.34%, Orlando Magic)

Two things are worth saying plainly about those numbers rather than rounding
them away.

First, the identity `POSS = PACE x (total minutes / 48)` **does not hold
exactly** on the advanced page. It holds to within 0.04 possessions for the
teams whose season minutes are exactly 48 per game, and drifts by up to 4
possessions for teams that played overtime. The page counts possessions; this
re-cut derives them from a printed per-48-minute rate. The drift is the
difference between those two things, and it is one-directional enough to be
visible team by team in the table below.

Second, because the drift scales with the season, the module's tolerance is
declared **in percent** (1% of the printed possession total, measured against a
largest observed gap of 0.34%) and the rating tolerance is **1.0 rating point**
(measured against a largest observed gap of 0.48). Both are measured on the
live pages, not chosen to make anything pass; a genuine modelling error - such
as dividing by a scoring average instead of possessions - moves a rating by
whole points and still fails the check.

Feeding the same 30 rows through `engine/teamstats.recut` itself joins 30 of 30
teams with no flags and passes every per-team check at those defaults.

| Team | Poss/game (recomputed) | OffRtg recomputed | OffRtg printed | diff | DefRtg recomputed | DefRtg printed | diff | NetRtg recomputed | NetRtg printed | diff | POSS recomputed | POSS printed | diff | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Los Angeles Lakers | 100.64 | 122.0 | 122.1 | -0.08 | 114.2 | 114.0 | +0.17 | 7.8 | 8.0 | -0.15 | 1409.0 | 1408 | +0.96 | [advanced](https://www.nba.com/stats/teams/advanced) |
| San Antonio Spurs | 99.59 | 119.3 | 119.2 | +0.09 | 106.3 | 106.6 | -0.27 | 13.0 | 12.6 | +0.35 | 1393.1 | 1395 | -1.93 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Boston Celtics | 97.33 | 118.7 | 118.9 | -0.24 | 105.2 | 105.1 | +0.10 | 13.5 | 13.9 | -0.44 | 1264.9 | 1263 | +1.95 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Houston Rockets | 97.68 | 121.2 | 121.2 | +0.01 | 110.8 | 110.7 | +0.07 | 10.4 | 10.5 | -0.06 | 1367.5 | 1367 | +0.52 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Philadelphia 76ers | 100.21 | 112.4 | 112.3 | +0.06 | 110.2 | 110.3 | -0.13 | 2.2 | 2.0 | +0.20 | 1402.9 | 1404 | -1.06 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Portland Trail Blazers | 100.67 | 118.8 | 118.8 | +0.00 | 111.1 | 111.1 | -0.04 | 7.7 | 7.7 | +0.05 | 1208.0 | 1208 | +0.04 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Memphis Grizzlies | 101.30 | 119.1 | 119.0 | +0.06 | 110.3 | 110.4 | -0.13 | 8.8 | 8.5 | +0.29 | 1316.4 | 1318 | -1.56 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Minnesota Timberwolves | 102.11 | 115.9 | 116.0 | -0.15 | 104.6 | 104.5 | +0.09 | 11.3 | 11.5 | -0.24 | 1327.1 | 1326 | +1.06 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Detroit Pistons | 101.14 | 114.4 | 114.1 | +0.30 | 109.1 | 109.2 | -0.14 | 5.3 | 4.9 | +0.44 | 1214.5 | 1217 | -2.51 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Oklahoma City Thunder | 98.82 | 113.4 | 113.4 | +0.04 | 108.4 | 108.4 | -0.02 | 5.1 | 5.1 | -0.04 | 1383.5 | 1384 | -0.52 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Denver Nuggets | 98.69 | 116.1 | 116.0 | +0.12 | 114.3 | 114.7 | -0.40 | 1.8 | 1.3 | +0.52 | 1084.5 | 1087 | -2.46 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Golden State Warriors | 100.49 | 116.1 | 116.1 | +0.03 | 111.9 | 112.0 | -0.15 | 4.3 | 4.1 | +0.18 | 1306.0 | 1307 | -1.04 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Atlanta Hawks | 104.55 | 112.7 | 112.8 | -0.13 | 111.0 | 111.1 | -0.06 | 1.6 | 1.7 | -0.07 | 1462.5 | 1462 | +0.46 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Miami Heat | 103.34 | 114.9 | 114.7 | +0.16 | 115.9 | 116.2 | -0.28 | -1.1 | -1.5 | +0.44 | 1343.0 | 1345 | -1.95 | [advanced](https://www.nba.com/stats/teams/advanced) |
| New York Knicks | 96.46 | 113.9 | 113.7 | +0.24 | 107.8 | 108.2 | -0.38 | 6.1 | 5.5 | +0.62 | 1253.5 | 1257 | -3.46 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Cleveland Cavaliers | 100.55 | 116.9 | 116.9 | -0.04 | 115.3 | 115.4 | -0.14 | 1.6 | 1.6 | -0.01 | 1406.5 | 1407 | -0.53 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Dallas Mavericks | 100.18 | 111.9 | 111.8 | +0.10 | 114.4 | 114.5 | -0.11 | -2.5 | -2.7 | +0.20 | 1402.5 | 1404 | -1.48 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Orlando Magic | 99.05 | 109.3 | 109.7 | -0.36 | 113.9 | 113.4 | +0.48 | -4.5 | -3.7 | -0.84 | 1189.0 | 1185 | +3.99 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Phoenix Suns | 98.79 | 114.1 | 114.3 | -0.22 | 118.7 | 118.5 | +0.24 | -4.7 | -4.2 | -0.46 | 1185.5 | 1183 | +2.48 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Toronto Raptors | 100.38 | 113.4 | 113.6 | -0.23 | 112.4 | 112.2 | +0.17 | 1.0 | 1.4 | -0.40 | 1304.5 | 1302 | +2.52 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Indiana Pacers | 101.25 | 110.7 | 110.9 | -0.18 | 113.1 | 112.9 | +0.19 | -2.4 | -2.0 | -0.37 | 1417.5 | 1415 | +2.50 | [advanced](https://www.nba.com/stats/teams/advanced) |
| LA Clippers | 100.88 | 111.3 | 111.4 | -0.08 | 115.5 | 115.3 | +0.18 | -4.2 | -3.9 | -0.26 | 1211.0 | 1210 | +1.02 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Charlotte Hornets | 96.65 | 102.5 | 102.5 | +0.03 | 113.6 | 113.6 | +0.01 | -11.1 | -11.1 | +0.03 | 1256.5 | 1256 | +0.45 | [advanced](https://www.nba.com/stats/teams/advanced) |
| New Orleans Pelicans | 104.16 | 111.3 | 111.3 | -0.03 | 119.9 | 120.0 | -0.09 | -8.6 | -8.6 | -0.04 | 1457.4 | 1457 | +0.44 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Washington Wizards | 101.18 | 109.3 | 109.4 | -0.09 | 116.6 | 116.5 | +0.12 | -7.3 | -7.1 | -0.21 | 1417.0 | 1416 | +1.00 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Brooklyn Nets | 100.30 | 109.9 | 109.8 | +0.07 | 116.1 | 116.0 | +0.05 | -6.2 | -6.2 | +0.02 | 1204.0 | 1204 | +0.00 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Chicago Bulls | 104.68 | 109.5 | 109.4 | +0.08 | 120.3 | 120.3 | -0.02 | -10.8 | -10.9 | +0.10 | 1256.5 | 1257 | -0.47 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Sacramento Kings | 101.08 | 106.6 | 106.8 | -0.15 | 119.9 | 119.8 | +0.11 | -13.3 | -13.0 | -0.26 | 1314.0 | 1312 | +2.04 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Milwaukee Bucks | 100.68 | 105.4 | 105.4 | -0.02 | 118.9 | 118.9 | -0.01 | -13.5 | -13.6 | +0.09 | 1409.5 | 1410 | -0.48 | [advanced](https://www.nba.com/stats/teams/advanced) |
| Utah Jazz | 101.68 | 105.3 | 105.1 | +0.23 | 116.0 | 116.2 | -0.15 | -10.7 | -11.1 | +0.38 | 1424.0 | 1426 | -2.04 | [advanced](https://www.nba.com/stats/teams/advanced) |

### 4.1 League-level checks

| Check | Expected | Observed | Agrees | Source |
| --- | --- | --- | --- | --- |
| League wins equal league losses | equal | 197 W / 197 L | yes | [traditional](https://www.nba.com/stats/teams/traditional) |
| Team-games counted twice (one per team per game) | even | 394 team-games | yes | [traditional](https://www.nba.com/stats/teams/traditional) |
| Opponent-page W/L match the traditional page | equal column for column | see 3.2 | yes | [opponent](https://www.nba.com/stats/teams/opponent) |
| Every team appears on all three pages | 30 of 30 | 30 of 30 | yes | [advanced](https://www.nba.com/stats/teams/advanced) |


## 5. Cross-check against the 2026-11-15 standings snapshot

The repository already holds `data/snapshots/standings-2026-11-15.json`, fetched
2026-11-15T11:49Z. The three team-stat pages were read about 27 hours later, so
the two are not expected to agree: games played on 11/15 and 11/16 are in the
pages and not in the snapshot. The comparison is published rather than
reconciled, because a reader who sees a mismatch should be able to see why.

| Team | Standings 11/15 (W-L) | Stat pages 11/16 (W-L) | Same | Source |
| --- | --- | --- | --- | --- |
| Boston Celtics | 10-2 | 11-2 | no | [standings 11/15](https://www.nba.com/standings) |
| Philadelphia 76ers | 10-3 | 11-3 | no | [standings 11/15](https://www.nba.com/standings) |
| Detroit Pistons | 8-4 | 8-4 | yes | [standings 11/15](https://www.nba.com/standings) |
| Miami Heat | 7-6 | 7-6 | yes | [standings 11/15](https://www.nba.com/standings) |
| Atlanta Hawks | 7-6 | 8-6 | no | [standings 11/15](https://www.nba.com/standings) |
| Cleveland Cavaliers | 7-7 | 7-7 | yes | [standings 11/15](https://www.nba.com/standings) |
| New York Knicks | 6-6 | 7-6 | no | [standings 11/15](https://www.nba.com/standings) |
| Toronto Raptors | 5-7 | 5-8 | no | [standings 11/15](https://www.nba.com/standings) |
| Orlando Magic | 5-7 | 5-7 | yes | [standings 11/15](https://www.nba.com/standings) |
| Indiana Pacers | 5-8 | 5-9 | no | [standings 11/15](https://www.nba.com/standings) |
| Charlotte Hornets | 4-8 | 4-9 | no | [standings 11/15](https://www.nba.com/standings) |
| Washington Wizards | 4-9 | 4-10 | no | [standings 11/15](https://www.nba.com/standings) |
| Brooklyn Nets | 3-9 | 3-9 | yes | [standings 11/15](https://www.nba.com/standings) |
| Chicago Bulls | 3-9 | 3-9 | yes | [standings 11/15](https://www.nba.com/standings) |
| Milwaukee Bucks | 1-12 | 1-13 | no | [standings 11/15](https://www.nba.com/standings) |
| San Antonio Spurs | 11-2 | 12-2 | no | [standings 11/15](https://www.nba.com/standings) |
| Los Angeles Lakers | 11-2 | 12-2 | no | [standings 11/15](https://www.nba.com/standings) |
| Houston Rockets | 10-3 | 11-3 | no | [standings 11/15](https://www.nba.com/standings) |
| Portland Trail Blazers | 9-3 | 9-3 | yes | [standings 11/15](https://www.nba.com/standings) |
| Minnesota Timberwolves | 9-4 | 9-4 | yes | [standings 11/15](https://www.nba.com/standings) |
| Memphis Grizzlies | 9-4 | 9-4 | yes | [standings 11/15](https://www.nba.com/standings) |
| Denver Nuggets | 7-4 | 7-4 | yes | [standings 11/15](https://www.nba.com/standings) |
| Golden State Warriors | 8-5 | 8-5 | yes | [standings 11/15](https://www.nba.com/standings) |
| Oklahoma City Thunder | 8-5 | 9-5 | no | [standings 11/15](https://www.nba.com/standings) |
| Dallas Mavericks | 7-6 | 7-7 | no | [standings 11/15](https://www.nba.com/standings) |
| Phoenix Suns | 5-6 | 5-7 | no | [standings 11/15](https://www.nba.com/standings) |
| New Orleans Pelicans | 4-10 | 4-10 | yes | [standings 11/15](https://www.nba.com/standings) |
| LA Clippers | 3-8 | 4-8 | no | [standings 11/15](https://www.nba.com/standings) |
| Sacramento Kings | 1-11 | 1-12 | no | [standings 11/15](https://www.nba.com/standings) |
| Utah Jazz | 1-12 | 1-13 | no | [standings 11/15](https://www.nba.com/standings) |

**18 of 30 teams changed** between the 11/15 standings snapshot and the
11/16 stat pages, which is the expected direction for a live season table read
a day later. This is recorded as flag CC-02: the two documents are different
as-of states and must never be joined as if they were one.

## 6. Requirements coverage for the items this session implemented

| Brief item | Module | What it does | State |
| --- | --- | --- | --- |
| "Extend the scheduled job to refresh the official schedule, standings, team statistics and injury report for each rolling slate, then rebuild only after freshness and provenance gates pass" | [`engine/refresh.py`](../engine/refresh.py) | Seven declared feeds, each with a freshness tolerance and a completeness rule; `refresh_decision` returns a binary may-we-rebuild | implemented, 39 tests, no data fetched | [injury index](https://www.nba.com/stats/teams/opponent) |
| "Capture per-player game logs (minutes, points, rebounds, assists, and the opponent) for at least the players who appear on an injury report" | [`engine/playerlogs.py`](../engine/playerlogs.py) | One row per player-game with the opponent required; coverage report against the injury-report roster | implemented, 32 tests | [NBA injury report](https://official.nba.com/nba-injury-report-2026-27-season/) |
| "Re-read the three official team-stat pages (traditional, opponent, advanced) and re-cut the model inputs" | [`engine/teamstats.py`](../engine/teamstats.py) | Read-completeness gate, possession-first re-cut, cross-check against the printed ratings | implemented, 38 tests, pages re-read here | [Teams Advanced](https://www.nba.com/stats/teams/advanced) |
| The CLI gap recorded on task AV | [`engine/cli.py`](../engine/cli.py) | `refresh`, `teamstats`, `playerlogs`, `modules` and `surfaces` subcommands; every gated one exits 1 when blocked | implemented | [NBA Terms of Use](https://www.nba.com/termsofuse) |

## 7. Irregularities found

| Id | Finding | Status | Source |
| --- | --- | --- | --- |
| CC-01 | The opponent page labels its last column "+/-" but prints the **opponent's** margin, the negative of the team's own margin on the traditional page (all 30 rows). Reading it as the team's margin inverts the sign of the whole league. `engine/teamstats.py` stores it as `opponent_plus_minus` and the two are never averaged. | open, published | [opponent](https://www.nba.com/stats/teams/opponent) |
| CC-02 | The 11/15 standings snapshot and the 11/16 stat pages are different as-of states: 18 of 30 teams have different W-L. They must not be joined as one table. | open, published | [standings](https://www.nba.com/standings) |
| CC-03 | None of the three team-stat pages prints a revision stamp or an "as of" line. The only timestamp available is the retrieval time, which is why `engine/refresh.py` measures their freshness from retrieval and says so in the verdict basis. | open, published | [advanced](https://www.nba.com/stats/teams/advanced) |
| CC-04 | The pages are served in more than one chunk (traditional 5, opponent 2, advanced 2). A reader that stops after one chunk gets 13 of 30 rows and no error - exactly the AN-04 failure this pass closes. `engine/refresh.py` therefore requires a chunk count for these feeds and `engine/teamstats.py` refuses a partial read. | open, published | [traditional](https://www.nba.com/stats/teams/traditional) |
| CC-05 | Two sessions were mid-flight when this session started and both had independently written a task row lettered BB (`arena/2b0e7d87-nba4` and `arena/4b8d8ab1-nba4`). Recorded on the board, not edited. | open, board record | [COORDINATION.md on GitHub](https://github.com/wingbangboozle1-lang/NBA4/blob/main/COORDINATION.md) |

## 8. What this pass did **not** re-read

Honesty about the boundary of a pass matters as much as the pass itself.

* The 2026-27 schedule PDF was not re-fetched: the slate refresh is session
  `arena/2b0e7d87-nba4`'s task BB and duplicating it would risk two different
  windows on the same branch.
* The injury-report index and PDFs were not transcribed here (only the index
  page was opened to confirm 11/16 reports exist), for the same reason.
* [NBA.com Terms of Use](https://www.nba.com/termsofuse) and the
  [Stats FAQ](https://www.nba.com/stats/help/faq) were **not** re-read in this
  pass. The rights gate the new modules enforce is the same one the repository
  already quotes; the clauses are not re-asserted as newly verified here.
* A deliberate omission: running the re-cut over these rows also produces a
  projected total for any real matchup (for example Boston at the Lakers:
  229.8 from the possession model against 238.3 from the sum of the two scoring
  averages). **That number is not published here.** It is an originated line
  derived from NBA statistics, and the owner decision recorded as D-01/IR-T4 on
  the [Flagged for Review page](../review.html) keeps originated lines off the
  site until the data rights are cleared. The gap between the two methods is
  demonstrated instead on the labelled synthetic fixture in
  `tests/test_engine_teamstats.py` (236.55 against 230.00), which reproduces
  the same arithmetic without touching a real game.
* Nothing else on this page publishes a model output. No line, price,
  probability or pick appears in any table above: every figure is either printed
  by the official page or arithmetic on figures the page printed, and the
  arithmetic is labelled as such.

