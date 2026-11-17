"""CPU-only checks for the outcome-blind lexical pair audit."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "lexical_pair", ROOT / "scripts/m95_native31_lexical_pair_20260928.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class LexicalPairTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MODULE.MANIFEST.read_text(encoding="utf-8"))
        cls.keys = MODULE.class_keys(MODULE.SOURCE)

    def test_frozen_pairs_and_control_key_overlap(self):
        result = MODULE.audit(self.manifest, self.keys)
        self.assertEqual((result["edge_count"], result["same_key_edges"]), (30, 2))
        self.assertEqual(result["curtain_key_by_arm"]["phrase"], {"present": 11, "absent": 0})
        self.assertEqual(
            {(e["exposed"], e["control"]) for e in result["edges"] if e["same_keys"]},
            {(1, 46), (1, 49)},
        )
        self.assertNotIn("shower curtain", {"x" for e in result["edges"] for x in e["exposed_keys"]})

    def test_changed_physical_target_fails_closed(self):
        changed = copy.deepcopy(self.manifest)
        pair = changed["pairs"][0]
        control_id = pair["all_controls"][0]["ann_id"]
        row = next(r for r in changed["records"]
                   if r["scene"] == pair["scene"] and r["ann_id"] == control_id)
        row["target_instances"] = [999]
        with self.assertRaisesRegex(ValueError, "physical target"):
            MODULE.audit(changed, self.keys)

    def test_changed_pair_count_fails_closed(self):
        changed = copy.deepcopy(self.manifest)
        changed["pairs"][0]["all_controls"].pop()
        with self.assertRaisesRegex(ValueError, "pair count"):
            MODULE.audit(changed, self.keys)


if __name__ == "__main__":
    unittest.main()
