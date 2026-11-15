"""Unit tests for the requirement modules added on 2026-11-15 (task AO).

Every fixture is SYNTHETIC (host ``synthetic.invalid``) and exists only to test
mechanics: gates, ordering, integrity and arithmetic. No NBA value, no market
price and no fitted constant appears in this file. Where an expected number is
hand-computed, the calculation is written out in the test so a reviewer can
check it without running anything.

Run:  python3 -m unittest discover -s tests -t .
"""

from __future__ import annotations

import json
import math
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine import injurydiff, luck, markets, officialresults, preregistration  # noqa: E402
from engine import publishedledger, rest, rotations, surfaces, totals, venues  # noqa: E402
from engine.estimators import (  # noqa: E402
    EstimatorOutput,
    blend,
    disagreement,
    home_court_points,
    independence_audit,
    summarise_pair,
)

SRC = "https://synthetic.invalid/fixture"
T0 = "2026-11-15T00:00:00+00:00"


# --- fixture builders -------------------------------------------------------

def quarters(away=(30, 25, 28, 27), home=(28, 26, 30, 29)):
    return tuple(
        officialresults.QuarterScore(label=f"Q{i + 1}", away=a, home=h)
        for i, (a, h) in enumerate(zip(away, home))
    )


def obs(game_id="G1", away_score=110, home_score=113, stamp="2026-11-15T04:00:00+00:00",
        url=SRC, **kw):
    return officialresults.ResultObservation(
        game_id=game_id,
        game_date=kw.pop("game_date", "2026-11-14"),
        away_team=kw.pop("away_team", "Alpha"),
        home_team=kw.pop("home_team", "Beta"),
        away_score=away_score,
        home_score=home_score,
        quarter_scores=kw.pop("quarter_scores", quarters()),
        finality=kw.pop("finality", officialresults.FINALITY_FINAL),
        source_url=url,
        source_revision_stamp=stamp,
        retrieved_at=kw.pop("retrieved_at", "2026-11-15T04:05:00+00:00"),
    )


def report(doc="r1", stamp="2026-11-15T06:15:00+00:00", rows=()):
    return injurydiff.InjuryReport(
        document_id=doc, source_url=SRC, source_revision_stamp=stamp,
        retrieved_at="2026-11-15T07:00:00+00:00", rows=tuple(rows),
    )


def row(game="IND@PHI", team="Indiana", player="Doe, John", status="Out", reason="Injury/Illness - Left knee"):
    return injurydiff.InjuryRow(game, team, player, status, reason)


# --- 1. official per-game result feed --------------------------------------

class ResultFeedTests(unittest.TestCase):
    def test_quarters_must_sum_to_the_final(self):
        good = obs()
        self.assertTrue(good.quarters_sum_to_final())
        broken = obs(away_score=999)
        self.assertFalse(broken.quarters_sum_to_final())

    def test_one_row_per_game_and_corroboration(self):
        store = officialresults.ResultStore()
        self.assertEqual(store.upsert(obs()), "INSERTED")
        # The same score stated by a different official document: corroboration.
        self.assertEqual(store.upsert(obs(stamp="2026-11-15T05:00:00+00:00")), "CORROBORATED")
        self.assertEqual(len(store.rows), 1)
        self.assertEqual(store.rows["G1"].merged()["observation_count"], 2)

    def test_single_source_is_reported_but_not_verified(self):
        store = officialresults.ResultStore()
        store.upsert(obs())
        verdict = store.verdict("G1")
        self.assertFalse(verdict.verified)
        self.assertEqual(verdict.code, "SINGLE_SOURCE")

    def test_disagreeing_officials_are_never_settled(self):
        store = officialresults.ResultStore()
        store.upsert(obs(away_score=110))
        # the second document is internally consistent (quarters sum to 111) but
        # states a different final: the conflict, not the arithmetic, is the block
        store.upsert(obs(away_score=111, stamp="2026-11-15T05:00:00+00:00",
                         quarter_scores=quarters(away=(31, 25, 28, 27))))
        verdict = store.verdict("G1")
        self.assertFalse(verdict.verified)
        self.assertEqual(verdict.code, "SOURCES_DISAGREE")

    def test_two_agreeing_officials_verify_and_settle(self):
        store = officialresults.ResultStore()
        store.upsert(obs())
        store.upsert(obs(stamp="2026-11-15T05:00:00+00:00"))
        row = officialresults.settle_row(store, "G1", "2026-11-15T06:00:00+00:00")
        self.assertTrue(row.settled)
        self.assertEqual(row.settlement_stamp, "2026-11-15T06:00:00+00:00")
        self.assertEqual(officialresults.expected_margin_from_result(row), 3)  # 113 - 110

    def test_settled_row_is_immutable(self):
        store = officialresults.ResultStore()
        store.upsert(obs())
        store.upsert(obs(stamp="2026-11-15T05:00:00+00:00"))
        officialresults.settle_row(store, "G1", "2026-11-15T06:00:00+00:00")
        with self.assertRaises(officialresults.ResultConflict):
            store.upsert(obs(away_score=100, stamp="2026-11-15T09:00:00+00:00"))
        # a duplicate of the settled score is ignored, not appended
        self.assertEqual(store.upsert(obs(stamp="2026-11-15T09:00:00+00:00")),
                         "IGNORED_DUPLICATE_OF_SETTLED")

    def test_settlement_refused_before_verification(self):
        store = officialresults.ResultStore()
        store.upsert(obs())
        with self.assertRaises(officialresults.ResultError):
            officialresults.settle_row(store, "G1", "2026-11-15T06:00:00+00:00")

    def test_provenance_is_mandatory(self):
        with self.assertRaises(officialresults.ResultError):
            obs(url="http://insecure.example/x").validate()
        with self.assertRaises(officialresults.ResultError):
            obs(retrieved_at="2026-11-15 04:05").validate()  # no UTC offset

    def test_in_progress_rows_are_stored_but_not_final(self):
        store = officialresults.ResultStore()
        store.upsert(obs(finality=officialresults.FINALITY_IN_PROGRESS, away_score=None, home_score=None,
                         quarter_scores=quarters()))
        self.assertEqual(store.verdict("G1").code, "NOT_FINAL")

    def test_refresh_gate_requires_a_declared_max_age(self):
        store = officialresults.ResultStore()
        store.upsert(obs())
        gate = officialresults.refresh_gate(store, ["2026-11-14"], T0, None)
        self.assertFalse(gate.passed)
        self.assertEqual(gate.code, "FRESHNESS_POLICY_UNSET")

    def test_refresh_gate_blocks_a_missing_game_day(self):
        store = officialresults.ResultStore()
        store.upsert(obs())
        gate = officialresults.refresh_gate(store, ["2026-11-14", "2026-11-15"], T0, 24)
        self.assertFalse(gate.passed)
        self.assertEqual(gate.code, "FEED_INCOMPLETE")

    def test_refresh_gate_blocks_stale_rows(self):
        store = officialresults.ResultStore()
        store.upsert(obs(retrieved_at="2026-11-13T00:00:00+00:00"))
        gate = officialresults.refresh_gate(store, ["2026-11-14"], T0, 24)
        self.assertFalse(gate.passed)
        self.assertEqual(gate.code, "FEED_STALE")

    def test_refresh_gate_passes_with_fresh_rows_and_reports_unsettled(self):
        store = officialresults.ResultStore()
        store.upsert(obs(retrieved_at="2026-11-14T23:00:00+00:00"))
        gate = officialresults.refresh_gate(store, ["2026-11-14"], T0, 24)
        self.assertTrue(gate.passed)
        self.assertEqual(gate.unverified_rows, ("G1",))  # rebuild allowed, settle is not

    def test_summary_counts(self):
        store = officialresults.ResultStore()
        store.upsert(obs())
        summary = officialresults.summarise(store)
        self.assertEqual(summary["games"], 1)
        self.assertEqual(summary["awaiting_corroboration"], 1)
        self.assertEqual(summary["settled"], 0)


# --- 2. injury archive and consecutive-report diff --------------------------

class InjuryDiffTests(unittest.TestCase):
    def test_banner_carries_revision_and_retrieval_time(self):
        banner = report(rows=[row()]).banner()
        self.assertEqual(banner["revision_time"], "2026-11-15T06:15:00+00:00")
        self.assertEqual(banner["retrieval_time"], "2026-11-15T07:00:00+00:00")
        self.assertEqual(banner["row_count"], "1")
        self.assertEqual(len(banner["content_hash"]), 64)

    def test_report_without_both_timestamps_is_refused(self):
        with self.assertRaises(injurydiff.InjuryArchiveError):
            report(stamp="").validate()
        with self.assertRaises(injurydiff.InjuryArchiveError):
            report().source_url  # attribute exists; validation below is the gate
            injurydiff.InjuryReport("x", SRC, "2026-11-15T06:15:00+00:00", "nope", ()).validate()

    def test_status_change_between_consecutive_reports(self):
        before = report(doc="r1", stamp="2026-11-14T22:00:00+00:00", rows=[row(status="Probable")])
        after = report(doc="r2", stamp="2026-11-15T06:15:00+00:00", rows=[row(status="Out")])
        diff = injurydiff.diff_reports(before, after, "IND@PHI")
        self.assertEqual(len(diff.status_changes), 1)
        change = diff.status_changes[0]
        self.assertEqual((change.before_status, change.after_status), ("Probable", "Out"))
        self.assertEqual(diff.summary[injurydiff.CHANGE_STATUS], 1)

    def test_added_removed_and_unchanged_are_separated(self):
        before = report(doc="r1", stamp="2026-11-14T22:00:00+00:00",
                        rows=[row(player="A, One", status="Out"), row(player="B, Two", status="Questionable")])
        after = report(doc="r2", stamp="2026-11-15T06:15:00+00:00",
                       rows=[row(player="A, One", status="Out"), row(player="C, Three", status="Out")])
        diff = injurydiff.diff_reports(before, after, "IND@PHI")
        kinds = sorted(c.kind for c in diff.changes)
        self.assertEqual(kinds, [injurydiff.CHANGE_ADDED, injurydiff.CHANGE_REMOVED])
        self.assertEqual(diff.unchanged_players, ("A, One",))

    def test_name_spelling_drift_is_flagged_not_merged(self):
        before = report(doc="r1", stamp="2026-11-14T22:00:00+00:00", rows=[row(player="Embdi, Joel")])
        after = report(doc="r2", stamp="2026-11-15T06:15:00+00:00", rows=[row(player="Embiid, Joel")])
        diff = injurydiff.diff_reports(before, after, "IND@PHI")
        self.assertEqual(len(diff.name_drift_candidates), 1)
        self.assertEqual(len(diff.changes), 0)  # not counted as a removal plus an addition
        self.assertIn("NOT merged", diff.name_drift_candidates[0].note)

    def test_normalise_name_strips_suffix_accents_and_case(self):
        self.assertEqual(injurydiff.normalise_name("Smaldedge, Jr., Tyrese"), "smaldedge tyrese")
        self.assertEqual(injurydiff.normalise_name("MUÑOZ, TRISTAN"), "munoz tristan")

    def test_reason_only_change_is_a_separate_kind(self):
        before = report(doc="r1", stamp="2026-11-14T22:00:00+00:00", rows=[row(reason="Injury/Illness - Left knee")])
        after = report(doc="r2", stamp="2026-11-15T06:15:00+00:00", rows=[row(reason="Injury/Illness - Right knee")])
        diff = injurydiff.diff_reports(before, after, "IND@PHI")
        self.assertEqual([c.kind for c in diff.changes], [injurydiff.CHANGE_REASON])
        self.assertEqual(diff.summary.get(injurydiff.CHANGE_STATUS, 0), 0)

    def test_reversed_chronology_is_an_error(self):
        newer = report(doc="r2", stamp="2026-11-15T06:15:00+00:00", rows=[row()])
        older = report(doc="r1", stamp="2026-11-14T22:00:00+00:00", rows=[row()])
        with self.assertRaises(injurydiff.InjuryArchiveError):
            injurydiff.diff_reports(newer, older, "IND@PHI")

    def test_self_diff_is_refused(self):
        one = report(doc="r1", rows=[row()])
        with self.assertRaises(injurydiff.InjuryArchiveError):
            injurydiff.diff_reports(one, one, "IND@PHI")

    def test_submission_marker_is_not_a_status(self):
        marker = row(player="", status="", reason=injurydiff.NOT_YET_SUBMITTED)
        self.assertTrue(marker.is_submission_marker)
        before = report(doc="r1", stamp="2026-11-14T22:00:00+00:00", rows=[marker])
        after = report(doc="r2", stamp="2026-11-15T06:15:00+00:00", rows=[row()])
        diff = injurydiff.diff_reports(before, after, "IND@PHI")
        self.assertEqual(diff.submission_marker_flip, ("Indiana",))
        self.assertEqual([c.kind for c in diff.changes], [injurydiff.CHANGE_ADDED])

    def test_archive_round_trip_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = injurydiff.ReportArchive(Path(tmp))
            archive.store(report(doc="r1", rows=[row(player="A, One"), row(player="B, Two")]))
            loaded = archive.load("r1")
            self.assertEqual(len(loaded.rows), 2)
            self.assertEqual(len(archive.all()), 1)
            path = Path(tmp) / "r1.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["rows"][0]["status"] = "Available"  # edit after archiving
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(injurydiff.InjuryArchiveError):
                archive.load("r1")

    def test_duplicate_rows_in_one_report_are_refused(self):
        with self.assertRaises(injurydiff.InjuryArchiveError):
            report(rows=[row(), row()]).validate()

    def test_diff_consecutive_walks_every_adjacent_pair(self):
        r1 = report(doc="r1", stamp="2026-11-14T21:00:00+00:00", rows=[row(status="Questionable")])
        r2 = report(doc="r2", stamp="2026-11-14T22:00:00+00:00", rows=[row(status="Probable")])
        r3 = report(doc="r3", stamp="2026-11-15T06:15:00+00:00", rows=[row(status="Out")])
        diffs = injurydiff.diff_consecutive([r3, r1, r2])
        self.assertEqual(len(diffs), 2)
        self.assertEqual([d.before_document for d in diffs], ["r1", "r2"])
        self.assertEqual([len(d.status_changes) for d in diffs], [1, 1])


# --- 3. pre-registration ----------------------------------------------------

def draft(**overrides):
    base = dict(
        strategy_id="S-EDGE-1",
        version="1.0.0",
        owner_session="synthetic",
        created_at="2026-11-15T09:00:00+00:00",
        signal={"name": "rest-adjusted margin", "inputs": ["days_rest", "estimator_disagreement"]},
        thresholds={"minimum_edge": 0.02, "minimum_sample": 300,
                    "maximum_trials": 12, "significance_alpha": 0.05},
        universe={"season": "2026-27", "start_date": "2026-11-01", "end_date": "2027-03-01",
                  "markets": ["spread", "total"], "teams": "all"},
        settlement_rule={
            "source_of_record": "official league finals",
            "outcome_fields": "final score, quarter scores",
            "push_and_void_handling": "push refunds at 1.00; void refunds",
            "price_convention": "decimal",
            "settled_when": "two agreeing official observations",
        },
    )
    base.update(overrides)
    return preregistration.Preregistration(**base)


class PreRegistrationTests(unittest.TestCase):
    def test_all_four_sections_are_required(self):
        for section in preregistration.REQUIRED_SECTIONS:
            empty = draft(**{section: {}})
            self.assertIn(section.split(" ")[0], " ".join(empty.missing_sections()), section)
            with self.assertRaises(preregistration.PreRegistrationError):
                empty.freeze()

    def test_placeholder_values_fail(self):
        bad = draft(thresholds={"minimum_edge": "TBD", "minimum_sample": 300,
                               "maximum_trials": 12, "significance_alpha": 0.05})
        with self.assertRaises(preregistration.PreRegistrationError):
            bad.freeze()

    def test_missing_threshold_key_fails_loudly(self):
        bad = draft(thresholds={"minimum_edge": 0.02, "minimum_sample": 300, "significance_alpha": 0.05})
        with self.assertRaises(preregistration.PreRegistrationError) as ctx:
            bad.freeze()
        self.assertIn("maximum_trials", str(ctx.exception))

    def test_incomplete_settlement_rule_fails(self):
        rule = dict(draft().settlement_rule)
        rule.pop("push_and_void_handling")
        with self.assertRaises(preregistration.PreRegistrationError):
            draft(settlement_rule=rule).freeze()

    def test_freeze_seals_a_hash_and_cannot_be_repeated(self):
        sealed = draft().freeze(frozen_at="2026-11-15T10:00:00+00:00")
        self.assertEqual(len(sealed.content_hash), 64)
        self.assertEqual(sealed.content_hash, sealed.compute_hash())
        with self.assertRaises(preregistration.PreRegistrationError):
            sealed.freeze()

    def test_edit_after_freezing_is_detected_as_tampering(self):
        sealed = draft().freeze(frozen_at="2026-11-15T10:00:00+00:00")
        edited = preregistration.Preregistration(**{**sealed.__dict__,
                                                    "thresholds": {**sealed.thresholds, "minimum_edge": 0.09}})
        with self.assertRaises(preregistration.PreRegistrationError) as ctx:
            edited.verify()
        self.assertIn("mismatch", str(ctx.exception))

    def test_a_bet_before_the_freeze_is_refused(self):
        sealed = draft().freeze(frozen_at="2026-11-15T10:00:00+00:00")
        allowed, reason = sealed.authorises_bet_at("2026-11-15T09:30:00+00:00")
        self.assertFalse(allowed)
        self.assertTrue(reason.startswith("FROZEN_AFTER_FIRST_BET"))

    def test_a_bet_after_the_freeze_and_inside_the_universe_is_authorised(self):
        sealed = draft().freeze(frozen_at="2026-11-15T10:00:00+00:00")
        self.assertEqual(sealed.authorises_bet_at("2026-11-16T01:00:00+00:00"), (True, "PRE_REGISTERED"))

    def test_a_bet_outside_the_registered_universe_is_refused(self):
        sealed = draft().freeze(frozen_at="2026-11-15T10:00:00+00:00")
        allowed, reason = sealed.authorises_bet_at("2027-04-01T01:00:00+00:00")
        self.assertFalse(allowed)
        self.assertIn("OUTSIDE_UNIVERSE", reason)

    def test_unfrozen_registration_authorises_nothing(self):
        allowed, reason = draft().authorises_bet_at("2026-11-16T01:00:00+00:00")
        self.assertFalse(allowed)
        self.assertIn("NOT_FROZEN", reason)

    def test_round_trip_through_disk_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "s-edge-1-1.0.0.json"
            sealed = draft().freeze(frozen_at="2026-11-15T10:00:00+00:00")
            preregistration.write_preregistration(path, sealed)
            self.assertEqual(preregistration.read_preregistration(path).content_hash, sealed.content_hash)
            other = draft(version="1.0.1").freeze(frozen_at="2026-11-15T11:00:00+00:00")
            with self.assertRaises(preregistration.PreRegistrationError):
                preregistration.write_preregistration(path, other)

    def test_report_row_shape(self):
        row = preregistration.registration_report(draft().freeze(frozen_at="2026-11-15T10:00:00+00:00"))
        self.assertEqual(row["status"], "FROZEN")
        self.assertEqual(row["missing_sections"], "none")
        self.assertIn("minimum_edge=0.02", row["thresholds"])


# --- 4. tamper-evident published ledger ------------------------------------

class PublishedLedgerTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ledger = publishedledger.PublishedLedger(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def pick(self, pick_id="P1", game_date="2026-11-15", tip="2026-11-15T23:00:00+00:00"):
        return {"pick_id": pick_id, "game_date": game_date, "market": "total", "line": 227.5}

    def test_hash_is_deterministic_and_key_order_free(self):
        a = publishedledger.pick_hash({"b": 2, "a": 1})
        b = publishedledger.pick_hash({"a": 1, "b": 2})
        self.assertEqual(a, b)
        self.assertEqual(len(a), 64)

    def test_publish_after_tip_is_refused(self):
        with self.assertRaises(publishedledger.LedgerError) as ctx:
            self.ledger.publish(self.pick(), "P1", "2026-11-15T23:00:00+00:00", "2026-11-15T23:30:00+00:00", [SRC])
        self.assertIn("before tip", str(ctx.exception))

    def test_publish_requires_https_sources(self):
        with self.assertRaises(publishedledger.LedgerError):
            self.ledger.publish(self.pick(), "P1", "2026-11-15T23:00:00+00:00", T0, ["http://x.test/a"])

    def test_a_published_pick_is_never_rewritten(self):
        self.ledger.publish(self.pick(), "P1", "2026-11-15T23:00:00+00:00", T0, [SRC])
        with self.assertRaises(publishedledger.LedgerError):
            self.ledger.publish(self.pick(), "P1", "2026-11-15T23:00:00+00:00", T0, [SRC])

    def test_seal_root_matches_an_independent_recomputation(self):
        for i, pick_id in enumerate(("P1", "P2")):
            self.ledger.publish({"pick_id": pick_id, "game_date": "2026-11-15", "line": 220 + i},
                                pick_id, "2026-11-15T23:00:00+00:00", T0, [SRC])
        seal = self.ledger.seal_day("2026-11-15", "2026-11-15T22:00:00+00:00")
        leaves = [publishedledger.pick_hash({"pick_id": "P1", "game_date": "2026-11-15", "line": 220}),
                  publishedledger.pick_hash({"pick_id": "P2", "game_date": "2026-11-15", "line": 221})]
        self.assertEqual(seal["root"], publishedledger.merkle_root(leaves))
        self.assertEqual(seal["count"], 2)

    def test_inclusion_proof_verifies_and_rejects_a_forgery(self):
        self.ledger.publish(self.pick(), "P1", "2026-11-15T23:00:00+00:00", T0, [SRC])
        self.ledger.seal_day("2026-11-15", "2026-11-15T22:00:00+00:00")
        verdict = self.ledger.verify_against_seal("P1")
        self.assertTrue(verdict["verified"])
        self.assertEqual(verdict["code"], "MATCHES_SEAL")
        forged = publishedledger.pick_hash({"pick_id": "P1", "game_date": "2026-11-15", "line": 999})
        root = publishedledger.merkle_root([forged])
        self.assertFalse(publishedledger.verify_merkle_proof(
            forged, publishedledger.merkle_proof([forged], 0), publishedledger.merkle_root(
                [publishedledger.pick_hash(self.pick())])))
        self.assertEqual(root, publishedledger.merkle_root([forged]))

    def test_seal_after_tip_is_refused(self):
        self.ledger.publish(self.pick(), "P1", "2026-11-15T23:00:00+00:00", T0, [SRC])
        with self.assertRaises(publishedledger.LedgerError):
            self.ledger.seal_day("2026-11-15", "2026-11-16T00:30:00+00:00")

    def test_seal_of_an_empty_day_is_refused(self):
        with self.assertRaises(publishedledger.LedgerError):
            self.ledger.seal_day("2026-11-15", T0)

    def test_settlement_requires_verified_finals_and_a_seal(self):
        self.ledger.publish(self.pick(), "P1", "2026-11-15T23:00:00+00:00", T0, [SRC])
        unverified = {"verified": False, "code": "SINGLE_SOURCE", "detail": "one document"}
        with self.assertRaises(publishedledger.LedgerError):
            self.ledger.settle("P1", "2026-11-16T06:00:00+00:00", [{}], {}, unverified)
        self.ledger.seal_day("2026-11-15", "2026-11-15T22:30:00+00:00")
        with self.assertRaises(publishedledger.LedgerError):
            self.ledger.settle("P1", "2026-11-16T06:00:00+00:00", [{}], {}, unverified)
        verified = {"verified": True, "code": "MATCH", "detail": "two observations agree"}
        entry = self.ledger.settle("P1", "2026-11-16T06:00:00+00:00", [{"score": "110-113"}],
                                   {"outcome": "LOSE"}, verified)
        self.assertEqual(entry.payload["settled_at"], "2026-11-16T06:00:00+00:00")
        stamps = self.ledger.settlement_stamps()
        self.assertEqual(stamps[0]["settlement_stamp"], "2026-11-16T06:00:00+00:00")
        self.assertEqual(stamps[0]["settled_after_tip_hours"], 7.0)  # 23:00Z tip -> 06:00Z next day

    def test_chain_tampering_is_detected(self):
        self.ledger.publish(self.pick(), "P1", "2026-11-15T23:00:00+00:00", T0, [SRC])
        self.ledger.publish({"pick_id": "P2", "game_date": "2026-11-15", "line": 221.5}, "P2",
                            "2026-11-16T00:00:00+00:00", T0, [SRC])
        self.assertTrue(self.ledger.verify_chain()["intact"])
        path = self.ledger.path
        lines = path.read_text(encoding="utf-8").splitlines()
        first = json.loads(lines[0])
        first["payload"]["pick"]["line"] = 999.0
        lines[0] = json.dumps(first, sort_keys=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        reopened = publishedledger.PublishedLedger(Path(self._tmp.name))
        report = reopened.verify_chain()
        self.assertFalse(report["intact"])
        self.assertEqual(report["broken_at"], [0])

    def test_audit_counts_and_pending_settlements(self):
        self.ledger.publish(self.pick(), "P1", "2026-11-15T23:00:00+00:00", T0, [SRC])
        audit = self.ledger.audit(now="2026-11-16T12:00:00+00:00")
        self.assertEqual(audit["published"], 1)
        self.assertEqual(audit["settled"], 0)
        self.assertEqual(audit["past_tip_but_unsettled"], ["P1"])

    def test_reload_from_disk_keeps_the_head(self):
        self.ledger.publish(self.pick(), "P1", "2026-11-15T23:00:00+00:00", T0, [SRC])
        head = self.ledger.verify_chain()["head"]
        reopened = publishedledger.PublishedLedger(Path(self._tmp.name))
        self.assertEqual(reopened.verify_chain()["head"], head)
        self.assertEqual(len(reopened.entries), 1)


# --- 5. two estimators, disagreement headline, pinned HCA -------------------

def est(a_id="A-ratings", b_id=None, game_id="G1", spread=-3.5, total=226.0, prob=0.63, inputs=("margin",),
        kind="ratings"):
    return EstimatorOutput(estimator_id=a_id, kind=kind, game_id=game_id, spread_points=spread,
                           total_points=total, home_win_probability=prob, inputs_used=inputs, version="1.0.0")


class EstimatorTests(unittest.TestCase):
    def test_disagreement_is_the_headline_and_uses_absolute_gaps(self):
        d = disagreement(est(spread=-3.5), est("B-pace", spread=-1.0, total=230.0, prob=0.58,
                                               inputs=("pace", "efficiency")), bands=(0.5, 2.0))
        self.assertEqual(d.spread_gap_points, 2.5)      # | -3.5 - (-1.0) |
        self.assertEqual(d.total_gap_points, 4.0)       # | 226 - 230 |
        self.assertAlmostEqual(d.win_prob_gap, 0.05, places=10)
        self.assertEqual(d.band, "MATERIAL_GAP")        # 4.0 > the large band, same direction
        self.assertIn("MATERIAL_GAP", d.headline)

    def test_a_sign_disagreement_is_a_split_not_just_a_big_gap(self):
        d = disagreement(est(spread=-0.5), est("B", spread=+0.5, total=226.1, prob=0.51,
                                               inputs=("pace",)), bands=(0.5, 2.0))
        self.assertEqual(d.band, "SPLIT")
        self.assertEqual(d.spread_gap_points, 1.0)

    def test_agreement_band(self):
        d = disagreement(est(spread=-3.5), est("B", spread=-3.3, total=226.2, prob=0.62, inputs=("pace",)),
                         bands=(0.5, 2.0))
        self.assertEqual(d.band, "AGREEMENT")

    def test_unregistered_bands_cannot_read_as_reassurance(self):
        d = disagreement(est(), est("B", inputs=("pace",)), bands=None)
        self.assertEqual(d.band, "UNBANDED")

    def test_shared_inputs_kill_the_confidence_claim(self):
        d = disagreement(est(inputs=("margin", "pace")), est("B", inputs=("pace",)), bands=(0.5, 2.0))
        self.assertFalse(d.independent)
        self.assertIn("NOT PUBLISHABLE", d.headline)
        self.assertIn("pace", d.note)

    def test_an_estimator_cannot_be_compared_with_itself(self):
        with self.assertRaises(ValueError):
            disagreement(est(), est(), bands=(0.5, 2.0))

    def test_empty_estimator_is_not_publishable(self):
        with self.assertRaises(ValueError):
            EstimatorOutput("X", "ratings", "G1", None, None, None, ("margin",), "1.0.0").validate()

    def test_blend_is_footnote_only(self):
        mixed = blend(est(spread=-4.0, total=228.0, prob=0.60),
                      est("B", spread=-2.0, total=224.0, prob=0.70, inputs=("pace",)))
        self.assertEqual(mixed.spread_points, -3.0)     # 0.5*-4 + 0.5*-2
        self.assertEqual(mixed.total_points, 226.0)
        self.assertAlmostEqual(mixed.home_win_probability, 0.65)
        self.assertFalse(mixed.headline_allowed)
        self.assertIn("SECONDARY", mixed.label)

    def test_bad_weights_are_refused(self):
        with self.assertRaises(ValueError):
            blend(est(), est("B", inputs=("pace",)), weights=(0.7, 0.7))

    def test_independence_audit_reports_the_shared_field_set(self):
        out = independence_audit(
            {"A": ["margin", "pace"], "B": ["efficiency"], "C": ["pace", "shot-quality"]},
            [("A", "B"), ("A", "C")],
        )
        self.assertTrue(out["pairs"][0]["independent"])
        self.assertFalse(out["pairs"][1]["independent"])
        self.assertEqual(out["pairs"][1]["shared_fields"], "pace")
        self.assertFalse(out["all_independent"])

    def test_home_court_is_pinned_to_a_measured_rate(self):
        # Phi^-1(0.5) = 0 exactly, so a 50% home rate must give 0.0 points.
        even = home_court_points(0.5, 12.0, SRC, "2026-27")
        self.assertAlmostEqual(even.value_points, 0.0, places=9)
        home = home_court_points(0.60, 12.0, SRC, "2026-27")
        self.assertGreater(home.value_points, 0.0)
        self.assertGreater(home.value_points, even.value_points)  # monotone in the rate
        self.assertIn("0.6000", home.label)
        self.assertEqual(home.source_url, SRC)

    def test_home_court_refuses_assumed_constants(self):
        for bad in (None, 0.0, 1.0):
            with self.assertRaises(ValueError):
                home_court_points(bad, 12.0, SRC, "2026-27")
        with self.assertRaises(ValueError):
            home_court_points(0.55, None, SRC, "2026-27")
        with self.assertRaises(ValueError):
            home_court_points(0.55, 12.0, "http://insecure", "2026-27")

    def test_summary_puts_the_gap_first_and_the_blend_underneath(self):
        row = summarise_pair(est(spread=-4.0), est("B", spread=-2.0, inputs=("pace",)), bands=(0.5, 2.0))
        keys = list(row)
        self.assertLess(keys.index("headline"), keys.index("blend_spread_points"))
        self.assertEqual(row["headline_surface"], "headline")
        self.assertEqual(row["footnote_surface"], "footnote")
        self.assertFalse(row["blend_headline_allowed"])


# --- 6. luck as a per-team z-score ------------------------------------------

class LuckTests(unittest.TestCase):
    def test_zscore_is_hand_checkable(self):
        # z = (45 - 40) / sqrt(25) = 5 / 5 = 1.00
        policy = luck.LuckPolicy(z_threshold=1.5, alpha=0.05, correlated_inflation=1.15,
                                registered_by="owner", registered_at=T0)
        score = luck.team_luck("Alpha", "2026-11-01..2026-11-15", 60, 45, 40.0, 25.0, policy, SRC)
        self.assertAlmostEqual(score.z, 1.0)
        self.assertEqual(score.band, "INSIDE")

    def test_binomial_variance_helper(self):
        # 60 games at p = 0.5: 60 * 0.5 * 0.5 = 15
        self.assertAlmostEqual(luck.binomial_variance(60, 0.5), 15.0)
        with self.assertRaises(ValueError):
            luck.binomial_variance(0, 0.5)
        with self.assertRaises(ValueError):
            luck.binomial_variance(60, 1.0)

    def test_unmeasured_expectation_yields_no_z_and_no_publish(self):
        policy = luck.LuckPolicy(z_threshold=1.5, alpha=0.05, correlated_inflation=1.15,
                                registered_by="owner", registered_at=T0)
        score = luck.team_luck("Alpha", "w", 60, 45, None, None, policy, SRC)
        self.assertIsNone(score.z)
        self.assertEqual(score.band, luck.BAND_UNSET)
        gate = luck.strategy_luck_gate("S-1", ["Alpha"], {"Alpha": score}, policy)
        self.assertFalse(gate.publish)
        self.assertEqual(gate.code, "LUCK_UNMEASURED")

    def test_strategy_leaning_on_an_outlier_team_is_refused(self):
        policy = luck.LuckPolicy(z_threshold=1.5, alpha=0.05, correlated_inflation=1.15,
                                registered_by="owner", registered_at=T0)
        lucky = luck.team_luck("Alpha", "w", 60, 52, 40.0, 25.0, policy, SRC)   # z = 2.40
        steady = luck.team_luck("Beta", "w", 60, 42, 40.0, 25.0, policy, SRC)  # z = 0.40
        self.assertEqual(lucky.band, "OUTSIDE")
        gate = luck.strategy_luck_gate("S-1", ["Alpha", "Beta"], {"Alpha": lucky, "Beta": steady}, policy)
        self.assertFalse(gate.publish)
        self.assertEqual(gate.code, "LUCK_LEAN_OUTSIDE_BAND")
        self.assertEqual(gate.offenders, ("Alpha",))
        clean = luck.strategy_luck_gate("S-1", ["Beta"], {"Beta": steady}, policy)
        self.assertTrue(clean.publish)
        self.assertIn("the rights, leakage, calibration and sample gates", clean.detail)

    def test_unregistered_band_blocks_everything(self):
        unregistered = luck.LuckPolicy(None, None, None, "", None)
        self.assertFalse(unregistered.registered)
        gate = luck.strategy_luck_gate("S-1", ["Alpha"], {}, unregistered)
        self.assertEqual(gate.code, luck.BAND_UNSET)

    def test_undeclared_lean_cannot_be_checked(self):
        policy = luck.LuckPolicy(1.5, 0.05, 1.15, "owner", T0)
        gate = luck.strategy_luck_gate("S-1", [], {}, policy)
        self.assertEqual(gate.code, "UNDECLARED_UNIVERSE")

    def test_a_variance_inflation_below_one_is_not_a_registered_policy(self):
        # 0.9 would *shrink* the noise band, i.e. make the gate more permissive;
        # the policy type refuses to treat that as registered.
        bad = luck.LuckPolicy(1.5, 0.05, 0.9, "owner", T0)
        self.assertFalse(bad.registered)
        self.assertEqual(bad.band_for(9.0), luck.BAND_UNSET)

    def test_table_rows_blank_the_unmeasured_cells(self):
        policy = luck.LuckPolicy(1.5, 0.05, 1.15, "owner", T0)
        rows = luck.luck_table_rows({
            "Alpha": luck.team_luck("Alpha", "w", 60, 45, 40.0, 25.0, policy, SRC),
            "Beta": luck.team_luck("Beta", "w", 60, None, None, None, policy, SRC),
        })
        self.assertEqual(rows[0]["z"], "+1.00")
        self.assertEqual(rows[1]["z"], "")
        self.assertEqual(rows[1]["band"], luck.BAND_UNSET)


# --- 7. minutes redistribution ---------------------------------------------

def rotation(team="Alpha", minutes=None, verified=False):
    minutes = minutes or {"A, One": 36.0, "B, Two": 34.0, "C, Three": 32.0, "D, Four": 30.0,
                          "E, Five": 28.0, "F, Six": 24.0, "G, Seven": 20.0, "H, Eight": 16.0,
                          "I, Nine": 10.0, "J, Ten": 8.0}
    return rotations.TeamRotation(
        team=team, window="2026-11-01..2026-11-15",
        players=tuple(rotations.PlayerMinutes(name, mins, 1) for name, mins in minutes.items()),
        verified=verified, source_url=SRC, source_stamp=T0,
    )


class RotationTests(unittest.TestCase):
    def test_top8_shares_use_the_240_minute_budget(self):
        # top eight sum to 36+34+32+30+28+24+20+16 = 220 minutes of 240.
        self.assertEqual(rotations.TOP_N, 8)
        self.assertAlmostEqual(rotation().top8_share_sum(), 220 / 240)
        self.assertAlmostEqual(rotation().top8_share_sum(), 0.9166666666666666, places=10)

    def test_budget_over_commitment_is_rejected(self):
        fat = rotations.TeamRotation("X", "w", (rotations.PlayerMinutes("A", 200, 1),
                                               rotations.PlayerMinutes("B", 60, 1)), source_url=SRC)
        with self.assertRaises(rotations.RotationError):
            fat.validate()

    def test_redistribution_conserves_the_minutes_budget(self):
        result = rotations.redistribution(rotation(), {"A, One": 36.0},
                                          {"B, Two": 0.4, "C, Three": 0.35, "I, Nine": 0.25})
        self.assertEqual(result["freed_minutes"], 36.0)
        self.assertEqual(result["unallocated_minutes"], 0.0)
        self.assertAlmostEqual(result["budget_check"], 220 + 10 + 8 - 36 + 36)  # 238 = total, unchanged
        added = result["added"]
        self.assertAlmostEqual(added["B, Two"], 14.4)   # 36 * 0.4
        self.assertAlmostEqual(added["C, Three"], 12.6)  # 36 * 0.35
        self.assertAlmostEqual(added["I, Nine"], 9.0)    # 36 * 0.25

    def test_top8_membership_can_change_under_injury(self):
        result = rotations.redistribution(
            rotation(), {"A, One": 36.0, "H, Eight": 16.0},
            {"I, Nine": 0.5, "J, Ten": 0.5},
        )
        before_names = [name for name, _ in result["top8_before"]]
        after_names = [name for name, _ in result["top8_after"]]
        self.assertIn("H, Eight", before_names)
        self.assertNotIn("H, Eight", after_names)
        self.assertIn("I, Nine", after_names)  # 10 + 16 = 26 minutes now beats 20-minute "G, Seven"

    def test_unallocated_minutes_are_reported_not_silently_spread(self):
        result = rotations.redistribution(rotation(), {"A, One": 36.0}, {"B, Two": 0.25})
        self.assertAlmostEqual(result["added"]["B, Two"], 9.0)
        self.assertAlmostEqual(result["unallocated_minutes"], 27.0)

    def test_weights_summing_above_one_are_rescaled_to_the_freed_pool(self):
        result = rotations.redistribution(rotation(), {"A, One": 36.0}, {"B, Two": 1.0, "C, Three": 1.0})
        self.assertAlmostEqual(result["added"]["B, Two"], 18.0)
        self.assertAlmostEqual(result["added"]["C, Three"], 18.0)
        self.assertAlmostEqual(result["unallocated_minutes"], 0.0)

    def test_missing_inputs_are_refused_not_assumed(self):
        with self.assertRaises(rotations.RotationError):
            rotations.redistribution(rotation(), {}, {"B, Two": 1.0})
        with self.assertRaises(rotations.RotationError):
            rotations.redistribution(rotation(), {"A, One": 36.0}, {})
        with self.assertRaises(rotations.RotationError):
            rotations.redistribution(rotation(), {"Nobody, Here": 10.0}, {"B, Two": 1.0})
        with self.assertRaises(rotations.RotationError):
            rotations.redistribution(rotation(), {"A, One": 136.0}, {"B, Two": 1.0})
        with self.assertRaises(rotations.RotationError):
            rotations.redistribution(rotation(), {"A, One": 36.0}, {"A, One": 1.0})

    def test_availability_column_without_a_minutes_source(self):
        column = rotations.availability_column(None, ["A, One"], ["B, Two"])
        self.assertIn("UNAVAILABLE", column["text"])
        self.assertEqual(column["flag"], "NO_MINUTES_SOURCE")
        self.assertIsNone(column["top8_share"])

    def test_availability_column_flags_an_unstable_rotation(self):
        column = rotations.availability_column(rotation(), ["A, One", "B, Two", "C, Three"], [],
                                               max_reported_out=2)
        self.assertEqual(column["flag"], "ROTATION_UNSTABLE")
        self.assertTrue(column["rotation_unstable"])
        self.assertIn("reported out", column["text"])

    def test_availability_column_reports_unresolved_reports(self):
        column = rotations.availability_column(rotation(), [], ["X, Y"])
        self.assertEqual(column["flag"], "UNRESOLVED_REPORTS")


# --- 8. venues and travel ---------------------------------------------------

class VenueTests(unittest.TestCase):
    def test_great_circle_hand_checks(self):
        # 1 degree of longitude at the equator: R * pi/180 = 3958.7613 * 0.0174533 = 69.096 miles
        self.assertAlmostEqual(venues.great_circle_miles((0.0, 0.0), (0.0, 1.0)),
                               3958.7613 * math.pi / 180.0, places=6)
        # quarter meridian: R * pi/2
        self.assertAlmostEqual(venues.great_circle_miles((0.0, 0.0), (90.0, 0.0)),
                               3958.7613 * math.pi / 2.0, places=6)
        self.assertAlmostEqual(venues.great_circle_km((0.0, 0.0), (0.0, 1.0)),
                               6371.0088 * math.pi / 180.0, places=6)

    def test_distance_is_not_fabricated_when_a_row_is_missing(self):
        leg = venues.travel_leg("Alpha", "2026-11-14", "2026-11-15", table={})
        self.assertIsNone(leg.miles)
        self.assertEqual(leg.code, venues.TRAVEL_NO_SOURCE)
        self.assertFalse(leg.verified)

    def test_a_row_without_coordinates_is_usable_as_a_name_but_not_a_distance(self):
        partial = venues.Venue("Test Arena", "Alpha", "Testville", "US", None, None, SRC, T0)
        self.assertFalse(partial.usable)
        self.assertIn("no coordinates", partial.unusable_reason())
        table = {"Alpha": partial}
        leg = venues.leg_between("Alpha", "2026-11-14", "2026-11-15", "Alpha", "Alpha", table)
        self.assertIsNone(leg.miles)
        self.assertEqual(leg.code, venues.TRAVEL_UNVERIFIED)

    def test_wrong_datum_is_refused_rather_than_mixed(self):
        other = venues.Venue("Test Arena", "Alpha", "Testville", "US", 1.0, 2.0, SRC, T0, datum="NAD27")
        self.assertIn("datum", other.unusable_reason())
        with self.assertRaises(venues.VenueError):
            other.validate()

    def test_out_of_range_coordinates_are_unusable(self):
        bad = venues.Venue("Test Arena", "Alpha", "Testville", "US", 95.0, 0.0, SRC, T0)
        self.assertFalse(bad.has_coordinates)

    def test_registry_is_empty_and_says_so(self):
        audit = venues.table_audit()
        self.assertEqual(audit["registered_rows"], 0)
        self.assertEqual(audit["status"], "NOT_STARTED")
        self.assertEqual(audit["teams_needed"], 30)

    def test_loader_accepts_a_sourced_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "venues.json"
            path.write_text(json.dumps([
                {"team": "Alpha", "arena": "A Arena", "city": "Testville", "country": "US",
                 "latitude": 40.0, "longitude": -75.0, "source_url": SRC, "source_stamp": T0},
                {"team": "Beta", "arena": "B Arena", "city": "Othertown", "country": "US",
                 "latitude": 35.0, "longitude": -80.0, "source_url": SRC, "source_stamp": T0},
            ]), encoding="utf-8")
            table = venues.load_coordinate_table(path)
            self.assertEqual(len(table), 2)
            leg = venues.leg_between("Alpha", "2026-11-14", "2026-11-15", "Alpha", "Beta", table)
            self.assertTrue(leg.verified)
            # 40,-75 -> 35,-80 hand check
            expected = venues.great_circle_miles((40.0, -75.0), (35.0, -80.0))
            self.assertAlmostEqual(leg.miles, round(expected, 2), places=2)
            self.assertGreater(leg.miles, 300)
            audit = venues.table_audit(table)
            self.assertEqual(audit["usable_rows"], 2)
            self.assertEqual(audit["status"], "READY")

    def test_loader_rejects_a_row_without_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text(json.dumps([{"arena": "", "team": ""}]), encoding="utf-8")
            with self.assertRaises(venues.VenueError):
                venues.load_coordinate_table(path)


# --- 9. rest, back-to-back and 3-in-4 --------------------------------------

def slate_rows(specs):
    return [rest.ScheduleRow(date, away, home, tip, f"row {i}", SRC)
            for i, (date, away, home, tip) in enumerate(specs, start=1)]


class RestTests(unittest.TestCase):
    def test_days_rest_and_back_to_back(self):
        cal = rest.TeamCalendar(slate_rows([
            ("2026-11-14", "Alpha", "Beta", "19:00"),
            ("2026-11-15", "Beta", "Gamma", "19:00"),
        ]))
        state = rest.rest_state(cal, "Beta", "2026-11-15", "Gamma")
        self.assertEqual(state.days_rest, 1)
        self.assertTrue(state.back_to_back)
        self.assertEqual(state.games_in_last_4, 2)
        self.assertFalse(state.three_in_four)

    def test_three_in_four_counts_the_game_itself(self):
        cal = rest.TeamCalendar(slate_rows([
            ("2026-11-12", "Alpha", "Beta", "19:00"),
            ("2026-11-14", "Gamma", "Alpha", "19:00"),
            ("2026-11-15", "Alpha", "Delta", "19:00"),
        ]))
        state = rest.rest_state(cal, "Alpha", "2026-11-15", "Delta")
        self.assertEqual(state.games_in_last_4, 3)   # 12th, 14th, 15th inside [11/12..11/15]
        self.assertTrue(state.three_in_four)
        self.assertEqual(state.games_in_last_3, 2)   # 11/14 and 11/15 inside [11/13..11/15]
        self.assertTrue(state.two_in_three)

    def test_four_in_six_and_rest_differential(self):
        cal = rest.TeamCalendar(slate_rows([
            ("2026-11-10", "Alpha", "Beta", "19:00"),
            ("2026-11-12", "Alpha", "Gamma", "19:00"),
            ("2026-11-13", "Alpha", "Delta", "19:00"),
            ("2026-11-15", "Alpha", "Epsilon", "19:00"),
            ("2026-11-15", "Zeta", "Epsilon", "19:00"),
        ]))
        state = rest.rest_state(cal, "Alpha", "2026-11-15", "Epsilon")
        self.assertEqual(state.games_in_last_6, 4)   # 10, 12, 13, 15 inside [11/10..11/15]
        self.assertTrue(state.four_in_six)
        # Alpha's previous game is 11/13 (2 days rest); Epsilon has only 11/15 listed as home
        # and no earlier game inside coverage, so the differential is unknown rather than 2.
        self.assertIsNone(state.rest_advantage)

    def test_rest_differential_when_both_sides_are_known(self):
        # Beta last played 11/13 (2 days rest); Gamma last played 11/14 (1 day),
        # so Beta's differential is +1 day.
        cal = rest.TeamCalendar(slate_rows([
            ("2026-11-13", "Alpha", "Beta", "19:00"),
            ("2026-11-14", "Gamma", "Delta", "19:00"),
            ("2026-11-15", "Beta", "Gamma", "20:00"),
        ]))
        state = rest.rest_state(cal, "Beta", "2026-11-15", "Gamma")
        self.assertEqual(state.days_rest, 2)
        self.assertEqual(state.rest_advantage, 1)
        away = rest.rest_state(cal, "Gamma", "2026-11-15", "Beta")
        self.assertEqual(away.days_rest, 1)
        self.assertTrue(away.back_to_back)
        self.assertEqual(away.rest_advantage, -1)

    def test_no_prior_game_is_not_zero_days_rest(self):
        cal = rest.TeamCalendar(slate_rows([("2026-11-15", "Alpha", "Beta", "19:00")]))
        state = rest.rest_state(cal, "Alpha", "2026-11-15", "Beta")
        self.assertIsNone(state.days_rest)
        self.assertIsNone(state.back_to_back)
        self.assertTrue(any("unmeasurable" in n or "unknown" in n for n in state.notes))

    def test_coverage_gap_is_reported(self):
        cal = rest.TeamCalendar(slate_rows([("2026-11-15", "Alpha", "Beta", "19:00")]))
        self.assertTrue(rest.coverage_gaps(cal, ["2026-10-01"]))
        self.assertFalse(rest.coverage_gaps(cal, ["2026-11-15"]))

    def test_duplicate_games_on_one_date_are_an_error(self):
        cal = rest.TeamCalendar(slate_rows([
            ("2026-11-15", "Alpha", "Beta", "17:00"),
            ("2026-11-15", "Alpha", "Gamma", "20:00"),
        ]))
        with self.assertRaises(rest.RestError):
            rest.rest_state(cal, "Alpha", "2026-11-15")

    def test_row_without_teams_is_refused(self):
        with self.assertRaises(rest.RestError):
            rest.ScheduleRow("2026-11-15", "Alpha", "", source_url=SRC).validate()

    def test_travel_join_stays_blank_without_a_venue_table(self):
        cal = rest.TeamCalendar(slate_rows([
            ("2026-11-14", "Beta", "Alpha", "19:00"),
            ("2026-11-15", "Alpha", "Gamma", "19:00"),
        ]))
        joined = rest.rest_and_travel(cal, "Alpha", "2026-11-15", "Gamma", venue_table={},
                                      previous_opponent="Beta")
        self.assertEqual(joined["rest"]["days_rest"], 1)
        self.assertTrue(joined["rest"]["back_to_back"])
        self.assertEqual(joined["travel"]["code"], venues.TRAVEL_NO_SOURCE)
        self.assertIsNone(joined["travel"]["miles"])

    def test_slate_table_shape(self):
        cal = rest.TeamCalendar(slate_rows([
            ("2026-11-14", "Alpha", "Beta", "19:00"),
            ("2026-11-15", "Beta", "Gamma", "19:00"),
            ("2026-11-15", "Alpha", "Delta", "19:00"),
        ]))
        rows = rest.slate_rest_table(cal, [("2026-11-15", "Beta", "Gamma"), ("2026-11-15", "Alpha", "Delta")])
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(r["sources"] == [SRC] for r in rows))
        self.assertEqual({r["team"] for r in rows}, {"Alpha", "Beta", "Gamma", "Delta"})


# --- 10. market anchoring and parlay pricing --------------------------------

class MarketTests(unittest.TestCase):
    def test_anchor_weight_is_inverse_log_loss(self):
        # ll_model 0.65, ll_close 0.69, p = 1 ->
        # w_model = (1/0.65) / ((1/0.65) + (1/0.69)) = 1.53846 / 2.98777 = 0.51492
        weights = markets.anchor_weight(0.65, 0.69, sample_size=500, sharpness_exponent=1.0, minimum_sample=200)
        self.assertAlmostEqual(weights.weight_model, 0.51492, places=4)  # hand value, 4 dp
        self.assertAlmostEqual(
            weights.weight_model, (1 / 0.65) / ((1 / 0.65) + (1 / 0.69)), places=12)
        self.assertAlmostEqual(weights.weight_model + weights.weight_close, 1.0)
        self.assertTrue(weights.anchored)

    def test_the_better_scorer_gets_more_weight(self):
        weights = markets.anchor_weight(0.60, 0.70, 500, 1.0, 200)
        self.assertGreater(weights.weight_model, 0.5)
        weights = markets.anchor_weight(0.70, 0.60, 500, 1.0, 200)
        self.assertLess(weights.weight_model, 0.5)

    def test_no_measurement_means_no_blend(self):
        with self.assertRaises(markets.MarketError):
            markets.anchor_weight(None, 0.69, 500, 1.0, 200)
        with self.assertRaises(markets.MarketError):
            markets.anchor_weight(0.65, None, 500, 1.0, 200)
        with self.assertRaises(markets.MarketError):
            markets.anchor_weight(0.65, 0.69, 500, None, 200)   # exponent must be declared
        with self.assertRaises(markets.MarketError):
            markets.anchor_weight(0.0, 0.69, 500, 1.0, 200)     # a zero log-loss is a leak

    def test_small_sample_leaves_the_line_unanchored(self):
        weights = markets.anchor_weight(0.65, 0.69, sample_size=10, sharpness_exponent=1.0, minimum_sample=200)
        self.assertFalse(weights.anchored)
        self.assertEqual(weights.code, "SAMPLE_BELOW_REGISTERED_MINIMUM")
        result = markets.anchored_line(-3.5, -2.0, weights)
        self.assertEqual(result["line"], -3.5)      # model line passes through untouched
        self.assertFalse(result["anchored"])

    def test_anchored_line_blends_with_the_measured_weights(self):
        weights = markets.anchor_weight(0.65, 0.69, 500, 1.0, 200)
        result = markets.anchored_line(-4.0, -2.0, weights)
        expected = weights.weight_model * -4.0 + weights.weight_close * -2.0
        self.assertAlmostEqual(result["line"], expected, places=10)
        self.assertTrue(result["anchored"])
        self.assertGreater(result["line"], -4.0)    # pulled toward the closer line
        self.assertLess(result["line"], -2.0)

    def test_naive_product_is_printed_next_to_the_correlated_price(self):
        pricing = markets.price_parlay([("leg-1", 0.55), ("leg-2", 0.55)], rho=0.35, draws=8000)
        self.assertAlmostEqual(pricing.naive_product, 0.55 * 0.55, places=12)
        self.assertIsNotNone(pricing.correlated_probability)
        self.assertGreater(pricing.correlated_probability, pricing.naive_product)
        self.assertGreater(pricing.dependence_effect, 0.0)
        rows = markets.pricing_table_rows(pricing)
        self.assertEqual(len(rows), 2)
        self.assertIn("naive product", rows[0]["method"])
        self.assertIn("measured-rho", rows[1]["method"])
        self.assertIn("rho", rows[1]["method"] + rows[1]["note"])

    def test_positive_rho_above_the_independent_product_and_negative_below(self):
        positive = markets.price_parlay([("a", 0.6), ("b", 0.6)], rho=0.6, draws=8000)
        negative = markets.price_parlay([("a", 0.6), ("b", 0.6)], rho=-0.6, draws=8000)
        naive = 0.36
        self.assertGreater(positive.correlated_probability, naive)
        self.assertLess(negative.correlated_probability, naive)
        self.assertLess(abs(positive.correlated_probability - 0.36), 0.35)
        self.assertLess(negative.correlated_probability, 0.36)

    def test_perfect_correlation_bounds_are_respected(self):
        # rho = +1 forces both legs onto one normal draw: P(both) = min(p) = 0.45
        perfect = markets.price_parlay([("a", 0.45), ("b", 0.55)], rho=1.0, draws=6000)
        self.assertAlmostEqual(perfect.correlated_probability, 0.45, delta=0.02)
        # rho = -1 with 50/50 legs is nearly impossible jointly
        opposite = markets.price_parlay([("a", 0.5), ("b", 0.5)], rho=-1.0, draws=6000)
        self.assertLess(opposite.correlated_probability, 0.02)

    def test_without_a_measured_rho_the_correlated_price_is_not_invented(self):
        pricing = markets.price_parlay([("a", 0.55), ("b", 0.55)])
        self.assertIsNone(pricing.correlated_probability)
        self.assertEqual(pricing.method, "BOUNDED_NOT_PRICED")
        self.assertAlmostEqual(pricing.naive_product, 0.3025, places=10)
        rows = markets.pricing_table_rows(pricing)
        self.assertEqual(rows[1]["probability"], "")
        self.assertEqual(rows[1]["fair_american"], "not priced")

    def test_rho_interval_gives_a_range_not_a_point(self):
        pricing = markets.price_parlay([("a", 0.55), ("b", 0.55)], rho_interval=(0.1, 0.4), draws=6000)
        self.assertIsNone(pricing.correlated_probability)
        self.assertIn("INTERVAL", pricing.method)
        self.assertEqual(len(pricing.rho_interval), 2)

    def test_american_conversions(self):
        self.assertEqual(markets.american_from_decimal(2.0), "+100")
        self.assertEqual(markets.american_from_decimal(1.5), "-200")
        self.assertEqual(markets.american_from_decimal(3.0), "+200")
        self.assertAlmostEqual(markets.decimal_from_probability(0.5), 2.0)
        with self.assertRaises(markets.MarketError):
            markets.american_from_decimal(1.0)

    def test_hold_must_be_declared_and_sane(self):
        self.assertIsNone(markets.hold_adjusted(2.0, None))
        self.assertAlmostEqual(markets.hold_adjusted(2.0, 1.05), 2.0 / 1.05)
        with self.assertRaises(markets.MarketError):
            markets.hold_adjusted(2.0, 0.95)

    def test_a_single_leg_is_not_a_parlay(self):
        with self.assertRaises(markets.MarketError):
            markets.price_parlay([("a", 0.5)])


# --- 11. totals as possessions x PPP ----------------------------------------

class TotalTests(unittest.TestCase):
    def test_model_total_hand_check(self):
        # 96 possessions x (1.18 + 1.15) = 96 x 2.33 = 223.68
        projection = totals.project_total("G1", 96.0, 1.18, 1.15)
        self.assertAlmostEqual(projection.model_total, 223.68, places=6)
        self.assertEqual(projection.status, totals.PPP_LABEL)

    def test_naive_baseline_gap_is_reported(self):
        # naive 112 + 110 = 222; 222 - 223.68 = -1.68
        projection = totals.project_total("G1", 96.0, 1.18, 1.15, scoring_averages=(112.0, 110.0))
        self.assertAlmostEqual(projection.naive_total, 222.0, places=6)
        self.assertAlmostEqual(projection.naive_minus_model, -1.68, places=6)

    def test_missing_inputs_block_the_number_not_the_row(self):
        projection = totals.project_total("G1", None, 1.18, 1.15, scoring_averages=(112.0, 110.0))
        self.assertTrue(projection.status.startswith("INPUTS_MISSING"))
        self.assertIn("possessions", projection.status)
        self.assertTrue(math.isnan(projection.model_total))
        self.assertEqual(projection.naive_total, 222.0)
        rows = totals.compare_totals([projection])
        self.assertIsNone(rows[0]["model_total"])
        self.assertEqual(rows[0]["naive_total"], 222.0)

    def test_possessions_formula_needs_declared_coefficients(self):
        with self.assertRaises(totals.TotalError):
            totals.possessions_from_components(60, 30, 10, 20, 12, {}, SRC)
        with self.assertRaises(totals.TotalError):
            totals.possessions_from_components(60, 30, 10, 20, 12,
                                              {"missed_field_goal_weight": 0.98}, SRC)
        with self.assertRaises(totals.TotalError):
            totals.possessions_from_components(
                60, 30, 10, 20, 12,
                {"missed_field_goal_weight": 0.98, "free_throw_attempt_weight": 0.44}, "http://x")
        result = totals.possessions_from_components(
            60, 30, 10, 20, 12,
            {"missed_field_goal_weight": 0.98, "free_throw_attempt_weight": 0.44}, SRC)
        # 60 - 10 + 0.98*(60-30) + 0.44*20 + 12 = 50 + 29.4 + 8.8 + 12 = 100.2
        self.assertAlmostEqual(result["possessions"], 100.2, places=6)
        with self.assertRaises(totals.TotalError):
            totals.possessions_from_components(30, 60, 10, 20, 12,
                                             {"missed_field_goal_weight": 0.98,
                                              "free_throw_attempt_weight": 0.44}, SRC)

    def test_ppp_from_a_per_100_rate(self):
        self.assertAlmostEqual(totals.ppp_from_rating(114.5), 1.145)
        self.assertIsNone(totals.ppp_from_rating(None))
        with self.assertRaises(totals.TotalError):
            totals.ppp_from_rating(-1.0)

    def test_opponent_adjustment_forms(self):
        # multiplicative: 1.18 * (1.12/1.10) = 1.20145...
        self.assertAlmostEqual(totals.adjusted_ppp(1.18, 1.12, 1.10), 1.18 * (1.12 / 1.10), places=12)
        # additive: 1.18 + (1.12 - 1.10) = 1.20
        self.assertAlmostEqual(totals.adjusted_ppp(1.18, 1.12, 1.10, form="additive"), 1.20, places=12)
        with self.assertRaises(totals.TotalError):
            totals.adjusted_ppp(1.18, 1.12, 1.10, form="vibes")
        with self.assertRaises(totals.TotalError):
            totals.adjusted_ppp(1.18, 1.12, 0.0)

    def test_pace_rules_are_separate_choices(self):
        # (99 * 101) / 100 = 100.0 - the two candidate rules differ on purpose
        self.assertAlmostEqual(totals.pace_product_over_league(99.0, 101.0, 100.0), 99.99, places=10)
        self.assertAlmostEqual(totals.pace_weighted_mean(99.0, 101.0, (0.5, 0.5)), 100.0, places=10)
        with self.assertRaises(totals.TotalError):
            totals.pace_weighted_mean(99.0, 101.0, (0.7, 0.7))
        with self.assertRaises(totals.TotalError):
            totals.pace_product_over_league(99.0, 101.0, 0.0)


# --- 12. projection / bet surface split ------------------------------------

class SurfaceTests(unittest.TestCase):
    def test_every_declared_field_sits_on_exactly_one_surface(self):
        for name, surface in surfaces.FIELD_SURFACES.items():
            self.assertIn(surface, surfaces.SURFACES, name)
            self.assertEqual(name, name.strip(), f"{name} has whitespace in its key")
        self.assertGreater(len(surfaces.PROJECTION), 0)

    def test_an_undeclared_field_is_an_error(self):
        with self.assertRaises(surfaces.SurfaceError):
            surfaces.classify("something_new")
        self.assertEqual(surfaces.classify("days_rest"), surfaces.PROJECTION)
        self.assertEqual(surfaces.classify("fair_price"), surfaces.BET)

    def test_projection_view_drops_gated_fields_and_says_so(self):
        view = surfaces.project_view({"days_rest": 1, "fair_price": 1.91, "matchup": "A@B"})
        self.assertEqual(view["days_rest"], 1)
        self.assertNotIn("fair_price", view)
        self.assertIn("fair_price", view["_withheld"])

    def test_bet_view_is_gated_by_default(self):
        record = {"fair_price": 1.91, "edge_vs_market": 0.04}
        gate = surfaces.BetGate.blocked(["G0_RIGHTS_NOT_CLEARED", "G4_NOT_RUN"], T0)
        view = surfaces.bet_view(record, gate)
        self.assertEqual(view["_gate"]["reasons"], ["G0_RIGHTS_NOT_CLEARED", "G4_NOT_RUN"])
        self.assertIsNone(view["fair_price"]["value"])
        self.assertEqual(view["fair_price"]["status"], "GATED")
        cleared = surfaces.BetGate(True, (), T0, evidence=("licence on file",))
        self.assertEqual(surfaces.bet_view(record, cleared)["fair_price"], 1.91)

    def test_mixing_surfaces_raises_on_a_value(self):
        with self.assertRaises(surfaces.SurfaceError):
            surfaces.assert_not_mixed({"days_rest": 1, "fair_price": 1.91}, surfaces.PROJECTION, "slate row")
        # a gated stub inside a projection payload is legal and legible
        surfaces.assert_not_mixed({"days_rest": 1, "fair_price": {"value": None, "status": "GATED"}},
                                  surfaces.PROJECTION, "slate row")
        surfaces.assert_not_mixed({"fair_price": 1.91}, surfaces.BET, "bet row")

    def test_page_audit_catches_a_number_under_a_gated_heading(self):
        html = ('<table><thead><tr><th>Edge vs market</th></tr></thead>'
                "<tbody><tr><td>0.041</td></tr></tbody></table>")
        problems = surfaces.audit_page_surface(html, ["Edge vs market"])
        self.assertEqual(len(problems), 1)
        self.assertIn("projection page", problems[0])
        clean = ('<table><tbody><tr><td>GATED (G0)</td></tr></tbody></table>')
        self.assertEqual(surfaces.audit_page_surface(clean, ["Edge vs market"]), [])
        self.assertEqual(surfaces.audit_page_surface(clean, []), [])

    def test_summary_counts_match_the_registry(self):
        summary = surfaces.surface_summary()
        self.assertEqual(summary["projection_fields"], len(surfaces.fields_of(surfaces.PROJECTION)))
        self.assertEqual(summary["bet_fields"], len(surfaces.fields_of(surfaces.BET)))
        self.assertEqual(summary["bet_fields_blocked"], summary["bet_fields"])

    def test_no_surface_field_leaks_a_real_team_or_price(self):
        # the registry is metadata about fields, not data: values are keys only
        self.assertTrue(all(isinstance(k, str) for k in surfaces.FIELD_SURFACES))
        self.assertTrue(all(v in surfaces.SURFACES for v in surfaces.FIELD_SURFACES.values()))


if __name__ == "__main__":
    unittest.main()
