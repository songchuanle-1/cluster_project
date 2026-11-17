"""Synthetic import-boundary checks; no native data, Torch or remote execution."""
import importlib
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

from pinned_diagnostic_imports_20260920 import PinnedDiagnosticImports, digest


class PinnedImportsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bundle = self.root / "bundle"
        self.bundle.mkdir()
        self.name = "_synthetic_pinned_producer"
        self.dep = "_synthetic_pinned_dependency"
        self.source = self.bundle / (self.name + ".py")
        self.source.write_text("VALUE = 17\n", encoding="ascii")
        self.rows = [{"path": self.source.name, "sha256": digest(self.source.read_bytes())}]
        self.manifest = self.bundle / "manifest.json"
        self.publish()
        self.addCleanup(sys.modules.pop, self.name, None)
        self.addCleanup(sys.modules.pop, self.dep, None)

    def publish(self):
        self.manifest.write_text(json.dumps({"files": self.rows}), encoding="ascii")
        self.expected = digest(self.manifest.read_bytes())

    def boundary(self):
        return PinnedDiagnosticImports(self.bundle, self.expected, [self.name])

    def test_exact_source_loaded_without_bytecode_and_cleaned(self):
        before = list(sys.meta_path)
        with self.boundary() as boundary:
            module = importlib.import_module(self.name)
            self.assertEqual(module.VALUE, 17)
            self.assertEqual(module.__file__, str(self.source))
            boundary.verify()
        self.assertEqual(sys.meta_path, before)
        self.assertNotIn(self.name, sys.modules)
        self.assertFalse((self.bundle / "__pycache__").exists())

    def test_wrong_manifest_digest_rejected(self):
        with self.assertRaisesRegex(ValueError, "manifest hash"):
            PinnedDiagnosticImports(self.bundle, "0" * 64, [self.name])

    def test_source_drift_before_construction_rejected(self):
        self.source.write_text("VALUE = 99", encoding="ascii")
        with self.assertRaisesRegex(ValueError, "source hash"):
            self.boundary()

    def test_source_drift_before_enter_rejected(self):
        boundary = self.boundary()
        self.source.write_text("VALUE = 99", encoding="ascii")
        with self.assertRaisesRegex(ValueError, "source hash"):
            with boundary:
                self.fail("Must fail before producer execution")

    def test_source_drift_inside_boundary_prevents_import(self):
        with self.boundary():
            self.source.write_text("VALUE = 99", encoding="ascii")
            with self.assertRaisesRegex(ValueError, "source hash"):
                importlib.import_module(self.name)
            # Restore exact original bytes so the successful exit recheck passes.
            self.source.write_text("VALUE = 17\n", encoding="ascii")

    def test_manifest_drift_on_exit_rejected_and_cleanup_runs(self):
        before = list(sys.meta_path)
        with self.assertRaisesRegex(ValueError, "manifest changed"):
            with self.boundary():
                importlib.import_module(self.name)
                self.manifest.write_text("{}", encoding="ascii")
        self.assertEqual(sys.meta_path, before)
        self.assertNotIn(self.name, sys.modules)

    def test_cached_module_rejected_even_when_file_matches(self):
        cached = ModuleType(self.name)
        cached.__file__ = str(self.source)
        sys.modules[self.name] = cached
        with self.assertRaisesRegex(ValueError, "already imported"):
            with self.boundary():
                pass
        self.assertIs(sys.modules[self.name], cached)

    def test_alias_cached_producer_rejected(self):
        alias = "_synthetic_cached_alias"
        cached = ModuleType(alias)
        cached.__file__ = str(self.root / self.source.name)
        sys.modules[alias] = cached
        self.addCleanup(sys.modules.pop, alias, None)
        with self.assertRaisesRegex(ValueError, "already imported"):
            with self.boundary():
                pass

    def test_search_path_shadow_ignored(self):
        shadow = self.root / self.source.name
        shadow.write_text("raise RuntimeError('wrong path')", encoding="ascii")
        sys.path.insert(0, str(self.root))
        self.addCleanup(sys.path.remove, str(self.root))
        with self.boundary():
            self.assertEqual(importlib.import_module(self.name).VALUE, 17)

    def test_declared_dependency_also_byte_pinned(self):
        dep = self.bundle / (self.dep + ".py")
        dep.write_text("VALUE = 23\n", encoding="ascii")
        self.source.write_text("from %s import VALUE\n" % self.dep, encoding="ascii")
        self.rows[0]["sha256"] = digest(self.source.read_bytes())
        self.rows.append({"path": dep.name, "sha256": digest(dep.read_bytes())})
        self.publish()
        with self.boundary():
            self.assertEqual(importlib.import_module(self.name).VALUE, 23)
        self.assertNotIn(self.dep, sys.modules)

    def test_invalid_paths_rejected(self):
        for path in ("../outside.py", "/outside.py", "./x.py", "a//x.py",
                     "a\\x.py", "C:/outside.py", "file.py:stream"):
            with self.subTest(path=path):
                self.rows.append({"path": path, "sha256": "a" * 64})
                self.publish()
                with self.assertRaisesRegex(ValueError, "bundle path"):
                    self.boundary()
                self.rows.pop()

    def test_duplicate_module_stem_rejected(self):
        self.rows.append({"path": "sub/" + self.source.name, "sha256": "a" * 64})
        self.publish()
        with self.assertRaisesRegex(ValueError, "unique flat"):
            self.boundary()

    def test_duplicate_path_rejected(self):
        self.rows.append(dict(self.rows[0]))
        self.publish()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.boundary()

    def test_missing_required_module_rejected(self):
        with self.assertRaisesRegex(ValueError, "Required producer"):
            PinnedDiagnosticImports(self.bundle, self.expected, ["absent"])

    def test_bad_digest_rejected(self):
        for value in ("", "A" * 64, "a" * 63, None):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "SHA256"):
                    PinnedDiagnosticImports(self.bundle, value, [self.name])

    def test_import_exception_restores_boundary_and_modules(self):
        self.source.write_text("raise RuntimeError('synthetic error')", encoding="ascii")
        self.rows[0]["sha256"] = digest(self.source.read_bytes())
        self.publish()
        before = list(sys.meta_path)
        with self.assertRaisesRegex(RuntimeError, "synthetic error"):
            with self.boundary():
                importlib.import_module(self.name)
        self.assertEqual(sys.meta_path, before)
        self.assertNotIn(self.name, sys.modules)

    def test_module_origin_mutation_rejected(self):
        with self.assertRaisesRegex(ValueError, "identity differs"):
            with self.boundary():
                importlib.import_module(self.name).__file__ = "wrong.py"
        self.assertNotIn(self.name, sys.modules)

    def test_symlink_source_rejected(self):
        other = self.root / "real.py"
        other.write_bytes(self.source.read_bytes())
        self.source.unlink()
        try:
            self.source.symlink_to(other)
        except OSError as exc:
            self.skipTest("Symlink creation unavailable: " + str(exc))
        with self.assertRaisesRegex(ValueError, "Symlink"):
            self.boundary()

    def test_non_python_manifest_entry_is_also_verified(self):
        other = self.bundle / "registry.json"
        other.write_text("{}", encoding="ascii")
        self.rows.append({"path": other.name, "sha256": digest(other.read_bytes())})
        self.publish()
        boundary = self.boundary()
        other.write_text("[]", encoding="ascii")
        with self.assertRaisesRegex(ValueError, "source hash"):
            with boundary:
                pass

    def test_symlink_guard_portable_mock(self):
        with patch.object(Path, "is_symlink", return_value=True):
            with self.assertRaisesRegex(ValueError, "Symlink"):
                self.boundary()

    def test_existing_pyc_not_used(self):
        import py_compile
        self.source.write_text("raise RuntimeError('stale bytecode')", encoding="ascii")
        py_compile.compile(str(self.source), doraise=True)
        self.source.write_text("VALUE = 17\n", encoding="ascii")
        with self.boundary():
            self.assertEqual(importlib.import_module(self.name).VALUE, 17)


if __name__ == "__main__":
    unittest.main()
