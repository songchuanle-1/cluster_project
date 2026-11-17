"""Synthetic static audit tests; no native packages or saved tensors."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import saved_dependency_inventory_20260921 as audit


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        for name in audit.SOURCES:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# synthetic\n", encoding="ascii")
        self.dataset = self.root / audit.SOURCES[2]
        self.dataset.write_text(
            "\n".join("import " + name for name in sorted(audit.DIRECT_PACKAGES))
            + "\nraise RuntimeError('must never execute')\n", encoding="ascii")

    def test_inventory_is_static_and_not_admission(self):
        result = audit.inventory(self.root)
        self.assertEqual(len(result["sources"]), 5)
        self.assertEqual(result["direct_packages"], sorted(audit.DIRECT_PACKAGES))
        for key in ("admission", "native_environment_verified",
                    "native_execution_completed", "external_dependency_attestation",
                    "scientific_validation_complete"):
            self.assertIs(result[key], False)
        self.assertEqual(result["sources"][2]["sha256"],
                         hashlib.sha256(self.dataset.read_bytes()).hexdigest())

    def test_constructor_directory_requirement_and_assets(self):
        requirements = audit.inventory(self.root)["constructor_requirements"]
        self.assertEqual(requirements["scene_file_listing"]["minimum_entries"], 1)
        self.assertFalse(requirements["scene_file_listing"]["contents_loaded_by_constructor"])
        self.assertEqual(set(requirements["required_assets"]), audit.REQUIRED_ASSETS)
        self.assertEqual(requirements["scene_file_listing"]["pattern"],
                         "scannetv2/train/*_refer.pth")

    def test_added_external_dependency_rejected(self):
        self.dataset.write_bytes(self.dataset.read_bytes() + b"\nimport unexpected_package\n")
        with self.assertRaisesRegex(ValueError, "inventory drift"):
            audit.inventory(self.root)

    def test_missing_external_dependency_rejected(self):
        self.dataset.write_text(
            self.dataset.read_text(encoding="ascii").replace("import dgl\n", ""),
            encoding="ascii")
        with self.assertRaisesRegex(ValueError, "inventory drift"):
            audit.inventory(self.root)

    def test_missing_source_rejected(self):
        self.dataset.unlink()
        with self.assertRaisesRegex(ValueError, "Missing or redirected"):
            audit.inventory(self.root)

    def test_symlink_guard(self):
        with patch.object(Path, "is_symlink", return_value=True):
            with self.assertRaisesRegex(ValueError, "redirected"):
                audit.inventory(self.root)

    def test_source_change_during_audit(self):
        real = audit.source_requirements
        def change(raw, filename):
            result = real(raw, filename)
            if filename == audit.SOURCES[-1]:
                self.dataset.write_bytes(self.dataset.read_bytes() + b"\n# drift\n")
            return result
        with patch.object(audit, "source_requirements", side_effect=change):
            with self.assertRaisesRegex(ValueError, "changed during audit"):
                audit.inventory(self.root)

    def test_function_imports_relative_extension_and_dynamic_calls(self):
        result = audit.source_requirements(b"""
from . import pointgroup_ops_ext
def load(name):
    import scipy.sparse
    importlib.import_module(name)
    __import__('literal')
""", "synthetic.py")
        self.assertEqual(result["imports"][0]["names"], ["pointgroup_ops_ext"])
        self.assertEqual(result["imports"][0]["level"], 1)
        self.assertEqual(result["imports"][1]["module"], "scipy.sparse")
        self.assertEqual([r["literal"] for r in result["dynamic_imports"]], [None, "literal"])
        self.assertTrue(all(r["resolved"] is False for r in result["dynamic_imports"]))

    def test_invalid_source_rejected_without_execution(self):
        self.dataset.write_bytes(b"def invalid(\n")
        with self.assertRaises(SyntaxError):
            audit.inventory(self.root)

    def test_returned_assets_are_independent(self):
        before = copy.deepcopy(audit.REQUIRED_ASSETS)
        result = audit.inventory(self.root)
        result["constructor_requirements"]["required_assets"].clear()
        self.assertEqual(audit.REQUIRED_ASSETS, before)


if __name__ == "__main__":
    unittest.main()
