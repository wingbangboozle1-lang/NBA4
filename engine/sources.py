"""Verified source registry.

Every entry records the primary URL, the publisher, the statement that was
checked on the official page and the date of that check. The registry is the
single place where the site and the documents get their source rows from, so
the site's table and ``docs/sources.md`` stay in step.

``verified_statement`` is the wording that was actually read on the official
page. It is not an interpretation and it never contains a project opinion.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

__all__ = ["Source", "SOURCES", "source_by_id", "checked_on"]

CHECKED_ON = date(2026, 11, 14)


@dataclass(frozen=True)
class Source:
    """One verified primary source."""

    source_id: str
    publisher: str
    title: str
    url: str
    verified_statement: str
    limits: str
    checked: date = CHECKED_ON

    def as_row(self) -> dict[str, str]:
        return {
            "id": self.source_id,
            "publisher": self.publisher,
            "title": self.title,
            "url": self.url,
            "statement": self.verified_statement,
            "limits": self.limits,
            "checked": self.checked.isoformat(),
        }


SOURCES: tuple[Source, ...] = (
    Source(
        source_id="NBA-01",
        publisher="NBA",
        title="NBA.com/Stats Frequently Asked Questions",
        url="https://www.nba.com/stats/help/faq",
        verified_statement=(
            "\"Our stats are not available for download for either academic or personal use. "
            "They are for viewing and enjoying on NBA.com/Stats\""
        ),
        limits=(
            "An access/use statement, not a licence or API grant. The same page also shows "
            "statistical examples dated 2013, which are not used as current values."
        ),
    ),
    Source(
        source_id="NBA-02",
        publisher="NBA",
        title="NBA.com Terms of Use",
        url="https://www.nba.com/termsofuse",
        verified_statement=(
            "Section 1: no Basketball Content may be reproduced, republished, publicly displayed "
            "or otherwise used without the written permission of the Operator. Section 9: NBA "
            "Statistics may only be used for legitimate news reporting or private, non-commercial "
            "purposes, and may not be used in connection with any gambling activity (including "
            "legal gambling activity), with any fantasy game or other commercial product or "
            "service, with any product presenting a live or archived play-by-play account, or "
            "with any product featuring a database of comprehensive, regularly updated statistics "
            "without the Operator's express prior consent."
        ),
        limits=(
            "Read the current Terms and obtain qualified legal review; a citation is not a "
            "permission. This is the blocking data-rights gate for a betting product."
        ),
    ),
    Source(
        source_id="NBA-03",
        publisher="NBA Official",
        title="NBA Injury Report: 2026-27 Season",
        url="https://official.nba.com/nba-injury-report-2026-27-season/",
        verified_statement=(
            "Teams must designate a participation status and a specific reason by 5 p.m. local "
            "time the day before a game, submit a game-day report between 11 a.m. and 1 p.m. "
            "local time, and \"Reports are updated on a continual basis throughout the day.\""
        ),
        limits=(
            "A reporting policy, not a minutes projection, availability probability, historical "
            "feed or guarantee of participation."
        ),
    ),
    Source(
        source_id="NBA-04",
        publisher="NBA Official",
        title="NBA Official Injury Report (2026-11-13, 07:30 PM ET)",
        url="https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-13_07_30PM.pdf",
        verified_statement=(
            "The document header reads \"Injury Report: 11/13/26 07:30 PM\" and the columns are "
            "Game Date, Game Time, Matchup, Team, Player Name, Current Status and Reason."
        ),
        limits=(
            "A dated snapshot for the games it lists. It is stale for later updates; the column "
            "structure is cited, the individual player rows are not republished."
        ),
    ),
    Source(
        source_id="NBA-05",
        publisher="NBA",
        title="2026-27 NBA Regular Season Schedule (by date)",
        url="https://cdn.nba.com/manage/2026/08/2026-27-NBA-Regular-Season-Schedule-By-Date.pdf",
        verified_statement=(
            "The document header reads \"2026-27 NBA REGULAR SEASON SCHEDULE - AS OF AUGUST 13, "
            "2026 | SUBJECT TO CHANGE\"."
        ),
        limits=(
            "A dated, changeable reference, not a live schedule or change feed. The dashboard "
            "links to it for review and does not republish its fixture rows."
        ),
    ),
    Source(
        source_id="NBA-06",
        publisher="NBA",
        title="NBA Stats glossary",
        url="https://www.nba.com/stats/help/glossary",
        verified_statement=(
            "Pace is defined as \"The number of possessions per 48 minutes for a team or player\"; "
            "the glossary also defines Points Per Possession, Usage Percentage and Offensive "
            "Rating among other measures."
        ),
        limits=(
            "Metric definitions only. No player or team values and no predictive relationships "
            "are taken from it."
        ),
    ),
    Source(
        source_id="GH-01",
        publisher="GitHub",
        title="What is GitHub Pages?",
        url="https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages",
        verified_statement=(
            "\"GitHub Pages is a static site hosting service that takes HTML, CSS, and JavaScript "
            "files straight from a repository on GitHub, optionally runs the files through a build "
            "process, and publishes a website.\""
        ),
        limits=(
            "Static hosting only. A Pages site cannot by itself protect credentials, ingest a "
            "licensed feed or run a secure live model service."
        ),
    ),
    Source(
        source_id="GH-02",
        publisher="GitHub",
        title="Creating a GitHub Pages site",
        url="https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site",
        verified_statement=(
            "\"GitHub Pages publishes any static files that you push to your repository\", the "
            "entry file must be index.html, index.md or README.md at the top level of the "
            "publishing source, and it can take up to 10 minutes for changes to publish."
        ),
        limits=(
            "Operational guidance for this repository's deployment. The published site must be "
            "checked after each merge."
        ),
    ),
    Source(
        source_id="GH-03",
        publisher="GitHub",
        title="GitHub Pages limits",
        url="https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits",
        verified_statement=(
            "\"GitHub Pages is not intended for or allowed to be used as a free web-hosting service "
            "to run your online business, e-commerce site, or any other website that is primarily "
            "directed at either facilitating commercial transactions or providing commercial "
            "software as a service (SaaS).\""
        ),
        limits=(
            "Whether the intended product falls into that category depends on the product "
            "design; it is a hosting decision requiring review, not a legal determination here."
        ),
    ),
    Source(
        source_id="GH-04",
        publisher="GitHub",
        title="Pages configuration for this repository (REST API)",
        url="https://api.github.com/repos/wingbangboozle1-lang/NBA4/pages",
        verified_statement=(
            "The API reports the site as enabled and built, published from branch \"main\" at "
            "path \"/\", with HTTPS enforced and no custom domain."
        ),
        limits=(
            "A repository setting that can change. It is not a guarantee that a future "
            "deployment succeeded."
        ),
    ),
    Source(
        source_id="GH-05",
        publisher="GitHub",
        title="NBA4 source repository",
        url="https://github.com/wingbangboozle1-lang/NBA4",
        verified_statement=(
            "The repository history records the starting state (a single README line at commit "
            "d6f5066), the research documents, the reference engine and the published site."
        ),
        limits="Records repository state, not an NBA or product fact.",
    ),
    Source(
        source_id="KSA-01",
        publisher="Kansspelautoriteit (Ksa)",
        title="Remote Gambling Act in force",
        url="https://kansspelautoriteit.nl/remote-gambling-act-force",
        verified_statement=(
            "\"The entry into force of the Remote Gambling Act makes it legal to offer gambling "
            "via the internet in the Netherlands. In order to do so, operators need a licence from "
            "the Netherlands Gambling Authority (Kansspelautoriteit, Ksa).\""
        ),
        limits=(
            "Does not classify an information, analytics, affiliate or rewards product; obtain "
            "advice for the actual user journey and territories."
        ),
    ),
    Source(
        source_id="KSA-02",
        publisher="Kansspelautoriteit (Ksa)",
        title="Belangrijkste regels voor kansspelreclame (key gambling advertising rules)",
        url="https://kansspelautoriteit.nl/belangrijkste-regels-voor-kansspelreclame",
        verified_statement=(
            "\"Deze informatie is een samenvatting van de geldende regelgeving ... Aan de "
            "onderstaande informatie kunnen geen rechten worden ontleend: de tekst in wet- en "
            "regelgeving is leidend.\" The page also states that without a Ksa licence no "
            "advertising may be made at all, and lists separate rules for sports-betting "
            "licencees."
        ),
        limits=(
            "An issue-spotting summary. Use the underlying legislation and rules for decisions; "
            "the page is in Dutch."
        ),
    ),
    Source(
        source_id="KSA-03",
        publisher="Kansspelautoriteit (Ksa)",
        title="Affiliate websites and gambling advertising rules",
        url="https://kansspelautoriteit.nl/ksa-attendeert-affiliatewebsites-op-regels-voor-reclame-kansspelen",
        verified_statement=(
            "The Ksa describes affiliate websites that forward the public to a gambling website "
            "via a banner, link or quotation, and states that advertising is only allowed for "
            "operators licensed in the Netherlands; otherwise the affiliate site is also in "
            "breach."
        ),
        limits=(
            "Context for the unresolved affiliate/marketing question; this project's user flow "
            "has not been classified."
        ),
    ),
    Source(
        source_id="KSA-04",
        publisher="Kansspelautoriteit (Ksa)",
        title="10 tips for gambling safely",
        url="https://kansspelautoriteit.nl/10-tips-gambling-safely",
        verified_statement=(
            "Tip 8: \"Winning or losing is almost always determined by coincidence or chance, not "
            "by your insight or practice, and certainly not by superstition\"; tip 4 notes that "
            "on average you will end up losing more than you win."
        ),
        limits=(
            "General consumer guidance, not a basketball-specific model study. It supports "
            "avoiding luck-free promises; it is not evidence for or against any strategy."
        ),
    ),
    Source(
        source_id="ML-01",
        publisher="scikit-learn",
        title="Cross-validation: evaluating estimator performance",
        url="https://scikit-learn.org/stable/modules/cross_validation.html",
        verified_statement=(
            "Section 3.1.2.6 states that for time series data \"it is very important to evaluate "
            "our model for time series data on the 'future' observations least like those that "
            "are used to train the model\", and section 3.1.3 warns that shuffling "
            "time-ordered data will \"likely lead to a model that is overfit and an inflated "
            "validation score\"."
        ),
        limits=(
            "Method reference only. Choosing splits, features, embargo lengths and thresholds "
            "remains a project decision."
        ),
    ),
    Source(
        source_id="ML-02",
        publisher="scikit-learn",
        title="Metrics and scoring: quantifying the quality of predictions",
        url="https://scikit-learn.org/stable/modules/model_evaluation.html",
        verified_statement=(
            "The Brier score is listed among the strictly consistent scoring functions for the "
            "mean of a probabilistic forecast, and the documentation notes that the Brier score "
            "is the squared error for one-hot encoded classification targets."
        ),
        limits=(
            "General prediction metrics, not sports evidence. A scoring rule measures the "
            "forecast; it does not by itself establish calibration or profit."
        ),
    ),
    Source(
        source_id="ML-03",
        publisher="scikit-learn",
        title="Probability calibration",
        url="https://scikit-learn.org/stable/modules/calibration.html",
        verified_statement=(
            "\"Strictly proper scoring rules for probabilistic predictions like "
            "brier_score_loss and log_loss assess calibration (reliability) and discriminative "
            "power (resolution) of a model, as well as the randomness of the data (uncertainty) "
            "at the same time ... A lower Brier loss, for instance, does not necessarily mean a "
            "better calibrated model.\""
        ),
        limits=(
            "Method reference. Reliability curves are the check to pair with a proper scoring "
            "rule; a single score must not be read as proof of calibration."
        ),
    ),
    Source(
        source_id="STAT-01",
        publisher="NIST",
        title="NIST/SEMATECH e-Handbook glossary",
        url="https://www.itl.nist.gov/div898/handbook/glossary.htm",
        verified_statement=(
            "\"Correlation is a measure of the strength of the (usually linear) relationship "
            "between two variables. The usual correlation coefficient, called the Pearson "
            "correlation coefficient, ranges from -1 to 1.\""
        ),
        limits=(
            "A definition of the estimator. No NBA coefficient is supplied and correlation does "
            "not establish causality."
        ),
    ),
    Source(
        source_id="STAT-02",
        publisher="NIST",
        title="1.3.3.4 Bootstrap Plot",
        url="https://www.itl.nist.gov/div898/handbook/eda/section3/bootplot.htm",
        verified_statement=(
            "\"The bootstrap plot is used to estimate the uncertainty of a statistic\", "
            "subsamples are generated with replacement, and \"the bootstrap is not appropriate "
            "for all distributions and statistics\"."
        ),
        limits=(
            "Generic method. Cluster resampling by game/date must still be justified for the "
            "chosen outcome structure."
        ),
    ),
)


def source_by_id(source_id: str) -> Source:
    """Look up a source by its identifier."""
    for source in SOURCES:
        if source.source_id == source_id:
            return source
    raise KeyError(f"unknown source id: {source_id!r}")


def checked_on() -> str:
    """The date on which the registry entries were last checked."""
    return CHECKED_ON.isoformat()
