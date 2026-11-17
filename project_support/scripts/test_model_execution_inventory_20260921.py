"""Synthetic static tests; no model imports or native data."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import model_execution_inventory_20260921 as audit


class ModelInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        for name in audit.SOURCES + (audit.CONFIG,):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# synthetic\n", encoding="ascii")
        self.network = self.root / audit.SOURCES[1]
        self.network.write_text(
            "import spconv.pytorch\nfrom pointnet2 import ops\n"
            "raise RuntimeError('never execute')\n"
            "def constructor():\n"
            "    return RobertaModel.from_pretrained('local')\n", encoding="ascii")

    def test_static_inventory_never_executes_sources(self):
        result = audit.inventory(self.root)
        self.assertEqual(len(result["sources"]), 9)
        self.assertEqual(result["absolute_import_roots"], ["pointnet2", "spconv"])
        self.assertEqual(len(result["sources"][1]["calls"]), 1)
        for key in ("native_environment_verified", "native_execution_completed",
                    "production_execution_validator_implemented", "admission"):
            self.assertIs(result[key], False)

    def test_contract_preserves_separate_gates(self):
        result = audit.inventory(self.root)
        self.assertEqual([s["stage"] for s in result["execution_validator_contract"]],
                         ["before_deserialization", "before_model_allocation", "after_capture"])
        text = str(result)
        for expected in ("logical0", "native backward", "tokenizer files alone",
                         "M197 recovery", "not a GPU validator"):
            self.assertIn(expected, text)

    def test_missing_source_rejected(self):
        self.network.unlink()
        with self.assertRaisesRegex(ValueError, "Missing or redirected"):
            audit.inventory(self.root)

    def test_missing_config_rejected(self):
        (self.root / audit.CONFIG).unlink()
        with self.assertRaises(ValueError):
            audit.inventory(self.root)

    def test_symlink_guard(self):
        with patch.object(Path, "is_symlink", return_value=True):
            with self.assertRaises(ValueError):
                audit.inventory(self.root)

    def test_invalid_syntax_rejected(self):
        self.network.write_bytes(b"def broken(")
        with self.assertRaises(SyntaxError):
            audit.inventory(self.root)

    def test_concurrent_change_rejected(self):
        real = audit.source_requirements
        def change(raw, name):
            result = real(raw, name)
            if name == audit.SOURCES[-1]:
                self.network.write_bytes(b"# changed\n")
            return result
        with patch.object(audit, "source_requirements", side_effect=change):
            with self.assertRaisesRegex(ValueError, "source changed"):
                audit.inventory(self.root)

    def test_calls_do_not_claim_reachability(self):
        self.network.write_bytes(b"if __name__ == '__main__':\n    model.cuda()\n")
        call = audit.inventory(self.root)["sources"][1]["calls"][0]
        self.assertFalse(call["runtime_reachability_verified"])

    def test_bounded_dependency_expansion_never_imports(self):
        for name in audit.BOUNDARY_SOURCES:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"import matplotlib.pyplot\nraise RuntimeError('never')\n")
        result = audit.boundary_inventory(self.root)
        self.assertEqual(len(result["sources"]), 17)
        self.assertEqual(result["absolute_import_roots"], ["matplotlib"])
        self.assertFalse(result["transitive_closure_complete"])
        self.assertFalse(result["native_environment_verified"])
        self.assertFalse(result["pointnet2"]["actual_loaded_path_verified"])
        self.assertTrue(all(not p["exists"] for p in result["pointnet2"]["inspected_paths"]))

    def test_boundary_missing_source_rejected(self):
        with self.assertRaises(ValueError):
            audit.boundary_inventory(self.root)


if __name__ == "__main__":
    unittest.main()
