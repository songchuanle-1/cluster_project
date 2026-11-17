import json
from pathlib import Path
import unittest

from m95_reference_role_screen_20260926 import audit


class RoleScreenTest(unittest.TestCase):
    def load(self):
        root = Path("pipeline/reports")
        return (
            json.loads((root / "mention_role_objective_20260916.json").read_text()),
            json.loads((root / "relation_response_identifiability_20260916.json").read_text()),
        )

    def test_frozen_join(self):
        result = audit(*self.load())
        self.assertEqual(result["summary"]["explicit_other_cue"]["expressions"], 3)
        self.assertEqual(sum(r["mentions"] for r in result["rows"]), 19)

    def test_missing_binding(self):
        role, join = self.load()
        join["role_join"].pop()
        with self.assertRaises(ValueError):
            audit(role, join)


if __name__ == "__main__":
    unittest.main()
