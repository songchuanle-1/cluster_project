import tempfile
import unittest
from pathlib import Path

from repair_evidence_drift_20260924 import EXPECTED, evidence_scan, migrate


class EvidenceDriftRepairTest(unittest.TestCase):
    def test_unknown_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "other.txt").write_text("new")
            work = {"candidates": [{
                "id": "referent-supervision-axis",
                "evidence": [{"path": "other.txt", "sha256": "0" * 64}],
            }]}
            with self.assertRaisesRegex(ValueError, "Unexpected evidence drift"):
                evidence_scan(root, work)

    def test_archives_old_bytes_without_reinterpreting_them(self):
        path = next(iter(EXPECTED))
        old = next(iter(EXPECTED[path]))
        current = {name: "a" * 64 for name in EXPECTED}
        work = {"candidates": [
            {"id": identifier, "evidence": [{"path": path, "sha256": old}]}
            for identifier in (
                "referent-supervision-axis", "referent-causality-audit",
                "modality-identity-preservation", "referent-discrimination",
                "instance-identity-representation")
        ]}
        report = {"path": "report.json", "sha256": "b" * 64}
        decision = {"path": "decision.md", "sha256": "c" * 64}
        changed = migrate(work, current, report, decision)
        self.assertEqual(len(changed), 5)
        for item in work["candidates"]:
            self.assertIn({"path": path, "sha256": "a" * 64}, item["evidence"])
            self.assertNotIn({"path": path, "sha256": old}, item["evidence"])
            archived = item["superseded_source_evidence"][0]
            self.assertEqual(archived["sha256"], old)
            self.assertTrue(archived["not_current_proof"])
            self.assertFalse(item["evidence_drift_repair_20260924"]["admission"])


if __name__ == "__main__":
    unittest.main()
