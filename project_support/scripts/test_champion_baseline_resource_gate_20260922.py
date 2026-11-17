"""Static contract tests for the paired baseline/champion resource gate."""
import ast
from pathlib import Path
import unittest


SCRIPT = Path(__file__).with_name(
    "champion_baseline_resource_gate_20260922.py")
EXPECTED_BASELINE_CONFIG = (
    "492dae84bf33cf795293625262a8b1a3f2a4b5ec7fdc9da009363e5f0726893c")
EXPECTED_BASELINE_MODEL = (
    "be91ac86fc7d0844b078ce37f986453669223e502175be81310498a1ca06b04e")
EXPECTED_CHAMPION_CONFIG = (
    "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a")
EXPECTED_CHAMPION_MODEL = (
    "cf4ce01548cecf186ba4677f5c13977f9fa527b2e33af6c82f564a7150a4c1d0")


class ResourceGateContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SCRIPT.read_text(encoding="ascii")
        cls.tree = ast.parse(cls.source)

    def test_bound_identity_literals_are_pinned(self):
        for digest in (
                EXPECTED_BASELINE_CONFIG, EXPECTED_BASELINE_MODEL,
                EXPECTED_CHAMPION_CONFIG, EXPECTED_CHAMPION_MODEL):
            self.assertIn(digest, self.source)

    def test_uses_historical_protocol(self):
        for marker in (
                "FlopCountAnalysis", "WARMUP = 20", "REPEAT = 100",
                '"median", "p90"', "torch.cuda.max_memory_allocated"):
            self.assertIn(marker, self.source)

    def test_profiles_historical_predict_path(self):
        self.assertIn('return self.wrapped_model(inputs, mode="predict")',
                      self.source)
        self.assertIn('model(copy.deepcopy(batch), mode="predict")',
                      self.source)
        self.assertIn('"forward_mode": "predict"', self.source)

    def test_uses_real_validation_batch(self):
        self.assertIn("build_dataset", self.source)
        self.assertIn("build_dataloader", self.source)
        self.assertIn("training=False", self.source)
        self.assertIn('"real_validation_input": True', self.source)

    def test_separate_target_processes_and_fresh_outputs(self):
        self.assertIn('choices=sorted(TARGETS)', self.source)
        self.assertIn("os.O_EXCL", self.source)
        self.assertIn('"optimizer_step": False', self.source)

    def test_absolute_limit_is_checked(self):
        self.assertIn("ABSOLUTE_FLOP_LIMIT_G = 10.0", self.source)
        self.assertIn("champion_absolute_flop_overage_g", self.source)
        self.assertIn('"absolute_flops_le_10g"', self.source)

    def test_has_no_import_time_cuda_execution(self):
        top_level_calls = []
        for node in self.tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                top_level_calls.append(ast.unparse(node.value))
        self.assertFalse(
            any("cuda" in call or "Network(" in call for call in top_level_calls))


if __name__ == "__main__":
    unittest.main()
