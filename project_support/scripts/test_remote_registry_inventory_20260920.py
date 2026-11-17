import ast
import json
import unittest

from remote_registry_inventory_20260920 import REMOTE, ROOT, training_steps


class InventoryTest(unittest.TestCase):
    def test_native_progress_format(self):
        tail = "Train[25/50]:  80%|bar| 3728/4686 [2:55]\rTrain[25/50]: 80%|bar| 3729/4686 [2:56]"
        rows = training_steps(tail)
        self.assertEqual([r["step"] for r in rows], [3728, 3729])
        self.assertEqual(rows[1]["epoch"], 25)

    def test_nonprogress_is_not_training(self):
        self.assertEqual(training_steps("pid1134192 best=0.4924"), [])

    def test_validation_is_distinct(self):
        self.assertEqual(training_steps("Val[25/50]: 20%|bar| 20/100 [00:01]")[0]["phase"], "Val")

    def test_probe_has_no_native_import(self):
        tree = ast.parse(REMOTE.replace("REQUEST", repr("{}"), 1))
        imports = {alias.name for n in ast.walk(tree) if isinstance(n, ast.Import)
                   for alias in n.names}
        self.assertFalse(imports & {"torch", "gorilla", "framework"})
        self.assertIn("ast", imports)

    def test_executed_registry_denominators(self):
        report = json.loads((ROOT / "pipeline/reports/remote_registry_inventory_20260920-0215.json").read_text())
        plan = report["metadata_plan"]
        self.assertEqual(len(plan["rows"]), 31)
        self.assertEqual(len({r["scene"] for r in plan["rows"]}), 17)
        self.assertEqual(plan["counts"], {"planned": 31})
        self.assertEqual(len({r["pair_id"] for r in plan["rows"]}), 31)
        self.assertFalse(plan["native_execution_verified"])
        self.assertTrue(report["remote"]["annotation"]["stable_after_grouping"])

    def test_saved_progress_and_metadata_source(self):
        report = json.loads((ROOT / "pipeline/reports/remote_registry_inventory_20260920-0215.json").read_text())
        rows = training_steps(report["remote"]["training"]["tail"])
        self.assertGreater(len(rows), 1)
        self.assertEqual(rows[-1]["step"], 3729)
        self.assertGreater(rows[-1]["step"], rows[0]["step"])
        block = report["remote"]["dataset_grouping_source"]
        local = (ROOT / "Cluster/framework/dataset/scannetv2.py").read_text(encoding="utf-8")
        import textwrap
        self.assertIn(textwrap.indent(block, "        "), local)
        self.assertFalse(report["remote"]["native_dataset_instantiated"])


if __name__ == "__main__":
    unittest.main()
