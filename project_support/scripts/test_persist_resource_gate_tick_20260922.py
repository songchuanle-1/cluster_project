"""Static contract tests for resource-gate progress persistence."""
import ast
from pathlib import Path
import unittest


SCRIPT = Path(__file__).with_name("persist_resource_gate_tick_20260922.py")


class PersistResourceGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SCRIPT.read_text(encoding="ascii")
        cls.tree = ast.parse(cls.source)

    def test_pins_current_tick_and_evidence(self):
        for marker in (
                "EXPECTED_TICK",
                "baseline_resources_20260922.json",
                "champion_resources_20260922.json",
                "baseline_champion_resource_gate_20260922.json"):
            self.assertIn(marker, self.source)

    def test_does_not_grant_failed_gates(self):
        self.assertIn('"resources_verified": False', self.source)
        self.assertIn('"admission": False', self.source)
        self.assertIn('resources_verified"] is not False', self.source)

    def test_preserves_queue_and_uses_atomic_replace(self):
        self.assertIn("queue_hash", self.source)
        self.assertIn("os.replace(temporary", self.source)
        self.assertIn('output.open("x"', self.source)

    def test_updates_every_due_candidate(self):
        self.assertIn("found != set(due_ids)", self.source)
        self.assertIn("resource_gate_progress", self.source)

    def test_has_no_import_time_filesystem_mutation(self):
        allowed = {
            "ast.parse", "cls.source = SCRIPT.read_text("
        }
        top_level_calls = []
        for node in self.tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                top_level_calls.append(ast.unparse(node.value))
        self.assertTrue(all(call in allowed for call in top_level_calls))


if __name__ == "__main__":
    unittest.main()
