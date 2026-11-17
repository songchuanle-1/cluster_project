"""Static contract tests for the full-model champion diagnostic."""
import ast
from pathlib import Path
import unittest


SCRIPT = Path(__file__).with_name(
    "champion_full_model_native_backward_20260922.py")
EXPECTED_MODEL_SHA = (
    "cf4ce01548cecf186ba4677f5c13977f9fa527b2e33af6c82f564a7150a4c1d0")
EXPECTED_CONFIG_SHA = (
    "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a")


class FullModelDiagnosticContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SCRIPT.read_text(encoding="ascii")
        cls.tree = ast.parse(cls.source)

    def test_bound_identity_literals_are_pinned(self):
        self.assertIn(EXPECTED_MODEL_SHA, self.source)
        self.assertIn(EXPECTED_CONFIG_SHA, self.source)

    def test_calls_production_forward_and_backward(self):
        self.assertIn('model(batch, mode="loss")', self.source)
        self.assertIn("loss.backward()", self.source)

    def test_all_required_components_have_assertions(self):
        for marker in (
                '"text_encoder": 1',
                '"decoder": 1',
                '"cluster_attention": 1',
                '"sampling_module": 1',
                '"criterion": 1'):
            self.assertIn(marker, self.source)

    def test_uses_fresh_output_and_no_training_side_effects(self):
        self.assertIn("os.O_EXCL", self.source)
        self.assertIn('"optimizer_step": False', self.source)
        self.assertIn('"training_started": False', self.source)
        self.assertIn('"checkpoint_loaded": False', self.source)

    def test_has_no_import_time_cuda_execution(self):
        top_level_calls = []
        for node in self.tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                top_level_calls.append(ast.unparse(node.value))
        self.assertFalse(
            any("cuda" in call or "Network(" in call for call in top_level_calls))


if __name__ == "__main__":
    unittest.main()
