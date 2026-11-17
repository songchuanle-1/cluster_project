import unittest
from copy import deepcopy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from referent_due_consolidation_20260922 import apply_resolution


class ReferentDueConsolidationTest(unittest.TestCase):
    def setUp(self):
        self.ids = [
            "same-target-description-grounding",
            "referent-query-selection",
            "input-modality-distinguishability",
            "referent-supervision-axis",
            "referent-causality-audit",
            "referent-discrimination",
            "instance-identity-representation",
            "modality-identity-preservation",
        ]
        self.work = {
            "candidates": [{"id": identifier} for identifier in self.ids],
            "last_event_tick": {"due_ids": list(self.ids)},
        }
        self.report = {
            "generated_at": "2026-09-22T05:16:00+08:00",
            "source_evidence": [{"path": "evidence.json", "sha256": "a" * 64}],
            "resolutions": [
                {
                    "id": identifier,
                    "stage": "blocked",
                    "disposition": "external_blocker",
                    "reason": "blocked",
                    "next_action": "retry",
                    "evidence": [],
                    "blocker": "server unreachable",
                    "retry_after": "2026-09-22T06:20:00+08:00",
                    "unblock_condition": "server reachable",
                    "alternatives_attempted": "preflight attempted",
                }
                for identifier in self.ids
            ],
            "next_action": "review in design mode",
        }

    def test_resolution_clears_due_queue_without_touching_candidates_order(self):
        original_order = list(self.ids)
        work = deepcopy(self.work)
        apply_resolution(work, self.report)
        self.assertEqual(
            [candidate["id"] for candidate in work["candidates"]],
            original_order,
        )
        self.assertEqual(work["last_event_tick"]["due_ids"], [])
        self.assertTrue(
            all(candidate["stage"] == "blocked" for candidate in work["candidates"])
        )

    def test_resolution_records_unblock_condition(self):
        work = deepcopy(self.work)
        apply_resolution(work, self.report)
        for candidate in work["candidates"]:
            resolution = candidate["due_resolution_20260922"]
            self.assertEqual(resolution["blocker"], "server unreachable")
            self.assertEqual(
                resolution["retry_after"], "2026-09-22T06:20:00+08:00"
            )
            self.assertEqual(resolution["unblock_condition"], "server reachable")
            self.assertEqual(resolution["alternatives_attempted"], "preflight attempted")


if __name__ == "__main__":
    unittest.main()
