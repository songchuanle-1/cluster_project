"""Synthetic packages only; never imports installed Torch or native extensions."""
import importlib
import importlib.machinery
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

from pinned_diagnostic_imports_20260920 import PreIdentityTorchImports, digest


class PreIdentityImportsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rows = []
        self.before = dict(sys.modules)
        self.path = list(sys.path)
        self.meta = list(sys.meta_path)
        self.addCleanup(self.cleanup)
        self.add("torch", "VALUE = 7\n", package=True)

    def cleanup(self):
        sys.path[:] = self.path
        sys.meta_path[:] = self.meta
        for name in set(sys.modules) - set(self.before):
            del sys.modules[name]
        for name, module in self.before.items():
            sys.modules[name] = module

    def add(self, name, source, package=False):
        path = self.root.joinpath(*name.split("."))
        path = path / "__init__.py" if package else path.with_suffix(".py")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="ascii")
        self.rows.append(dict(name=name, path=str(path), is_package=package,
                              sha256=digest(path.read_bytes())))
        return path

    def change(self, name, source):
        row = next(r for r in self.rows if r["name"] == name)
        Path(row["path"]).write_text(source, encoding="ascii")
        row["sha256"] = digest(Path(row["path"]).read_bytes())

    def boundary(self):
        return PreIdentityTorchImports(self.rows)

    def test_exact_package_and_submodule_with_relative_imports(self):
        self.change("torch", "from .version import VALUE\n")
        self.add("torch.version", "VALUE = 19\n")
        with self.boundary() as loader:
            self.assertEqual(loader.load_torch().VALUE, 19)
        self.assertEqual(sys.meta_path, self.meta)
        self.assertIn("torch", sys.modules)  # Native imports must not be "rolled back".
        self.assertFalse(list(self.root.rglob("*.pyc")))

    def test_declared_external_dependency(self):
        self.change("torch", "from synthetic_dep import VALUE\n")
        self.add("synthetic_dep", "VALUE = 31\n")
        with self.boundary() as loader:
            self.assertEqual(loader.load_torch().VALUE, 31)

    def test_shadow_package_and_pyc_ignored(self):
        import py_compile
        path = Path(self.rows[0]["path"])
        path.write_text("raise RuntimeError('stale')\n", encoding="ascii")
        py_compile.compile(str(path), doraise=True)
        path.write_text("VALUE = 7\n", encoding="ascii")
        shadow = self.root / "shadow"
        (shadow / "torch").mkdir(parents=True)
        (shadow / "torch/__init__.py").write_text("raise RuntimeError('shadow')")
        sys.path.insert(0, str(shadow))
        with self.boundary() as loader:
            self.assertEqual(loader.load_torch().VALUE, 7)

    def test_preimported_root_or_submodule_rejected(self):
        for name in ("torch", "torch.cuda", "spconv"):
            with self.subTest(name=name):
                sys.modules[name] = ModuleType(name)
                with self.assertRaisesRegex(ValueError, "already imported"):
                    with self.boundary():
                        pass
                del sys.modules[name]

    def test_alias_with_declared_origin_rejected(self):
        module = ModuleType("synthetic_alias")
        module.__file__ = self.rows[0]["path"]
        sys.modules[module.__name__] = module
        with self.assertRaisesRegex(ValueError, "already imported"):
            with self.boundary():
                pass

    def test_hash_drift_before_import_rejected(self):
        boundary = self.boundary()
        Path(self.rows[0]["path"]).write_text("VALUE = 8\n")
        with self.assertRaisesRegex(ValueError, "hash differs"):
            with boundary:
                pass

    def test_hash_drift_after_import_rejected(self):
        with self.assertRaisesRegex(ValueError, "hash differs"):
            with self.boundary() as loader:
                loader.load_torch()
                Path(self.rows[0]["path"]).write_text("VALUE = 8\n")
        self.assertEqual(sys.meta_path, self.meta)

    def test_origin_and_package_path_mutation_rejected(self):
        for field, value in (("__file__", "wrong.py"), ("__path__", ["wrong"])):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "origin/identity"):
                    with self.boundary() as loader:
                        setattr(loader.load_torch(), field, value)
                sys.modules.pop("torch", None)

    def test_changed_sys_path_rejected_without_restoring_foreign_state(self):
        with self.assertRaisesRegex(ValueError, "sys.path"):
            with self.boundary() as loader:
                loader.load_torch()
                sys.path.append("untrusted")
        self.assertIn("untrusted", sys.path)

    def test_undeclared_dependency_blocks_execution(self):
        self.change("torch", "import synthetic_missing_dependency\n")
        with self.assertRaisesRegex(ImportError, "Undeclared"):
            with self.boundary() as loader:
                loader.load_torch()
        self.assertNotIn("synthetic_missing_dependency", sys.modules)
        self.assertEqual(sys.meta_path, self.meta)

    def test_model_import_cannot_be_admitted_by_manifest(self):
        self.add("spconv", "VALUE = 0\n")
        with self.assertRaisesRegex(ValueError, "forbidden"):
            self.boundary()

    def test_caught_undeclared_import_still_poisoned(self):
        self.change("torch", "try:\n import synthetic_missing_dependency\nexcept ImportError:\n pass\n")
        with self.assertRaisesRegex(ValueError, "Failed dependency"):
            with self.boundary() as loader:
                loader.load_torch()

    def test_module_cache_injection_rejected(self):
        self.change("torch", "import sys, types\nsys.modules['synthetic_injected'] = types.ModuleType('x')\n")
        with self.assertRaisesRegex(ValueError, "Untracked"):
            with self.boundary() as loader:
                loader.load_torch()

    def test_loader_single_use(self):
        boundary = self.boundary()
        with boundary:
            boundary.load_torch()
            with self.assertRaisesRegex(ValueError, "unused"):
                boundary.load_torch()
        with self.assertRaisesRegex(ValueError, "single-use"):
            with boundary:
                pass

    def test_load_outside_boundary_rejected(self):
        with self.assertRaisesRegex(ValueError, "active"):
            self.boundary().load_torch()

    def test_parent_package_required(self):
        self.add("synthetic_absent.child", "VALUE = 0\n")
        with self.assertRaisesRegex(ValueError, "parent"):
            self.boundary()

    def test_bad_manifest_paths_flags_names_and_hashes(self):
        base = dict(self.rows[0])
        for changes in (dict(path="relative.py"), dict(is_package=1),
                        dict(sha256="A" * 64), dict(name="bad-name")):
            with self.subTest(changes=changes):
                self.rows[0] = dict(base, **changes)
                with self.assertRaises(ValueError):
                    self.boundary()
        self.rows[0] = base

    def test_symlink_path_rejected_portably(self):
        with patch.object(Path, "is_symlink", return_value=True):
            with self.assertRaisesRegex(ValueError, "Symlink"):
                self.boundary()

    def test_native_extension_protocol_only_mocked(self):
        suffix = importlib.machinery.EXTENSION_SUFFIXES[0]
        path = self.root / "torch" / ("_C" + suffix)
        path.write_bytes(b"synthetic-not-a-binary")
        self.rows.append(dict(name="torch._C", path=str(path),
                              sha256=digest(path.read_bytes()), is_package=False))
        self.change("torch", "from . import _C\nVALUE = _C.VALUE\n")
        with patch("pinned_diagnostic_imports_20260920.importlib.machinery.ExtensionFileLoader") as factory:
            factory.return_value.create_module.side_effect = lambda spec: ModuleType(spec.name)
            factory.return_value.exec_module.side_effect = lambda module: setattr(module, "VALUE", 29)
            with self.boundary() as loader:
                self.assertEqual(loader.load_torch().VALUE, 29)
            factory.return_value.create_module.assert_called_once()
            factory.return_value.exec_module.assert_called_once()

    def test_deferred_missing_dependency_rejected_while_identity_boundary_active(self):
        self.change("torch", "def later():\n import synthetic_missing_dependency\n")
        with self.assertRaisesRegex(ImportError, "Undeclared"):
            with self.boundary() as loader:
                loader.load_torch().later()

    def test_manifest_is_copied_and_invalid_duplicate_rows_rejected(self):
        boundary = self.boundary()
        self.rows[0]["sha256"] = "0" * 64
        with boundary:
            self.assertEqual(boundary.load_torch().VALUE, 7)
        sys.modules.pop("torch")
        self.rows[0]["sha256"] = digest(Path(self.rows[0]["path"]).read_bytes())
        self.rows.append(dict(self.rows[0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.boundary()

    def test_replaced_meta_finder_rejected(self):
        with self.assertRaisesRegex(ValueError, "import boundary"):
            with self.boundary() as loader:
                loader.load_torch()
                sys.meta_path.remove(loader)
        self.assertTrue(loader.failed)

    def test_caught_failed_import_cannot_return_torch_to_cuda_caller(self):
        self.change("torch", "try:\n import synthetic_missing_dependency\nexcept ImportError:\n pass\n")
        with self.assertRaisesRegex(ValueError, "Failed dependency"):
            with self.boundary() as loader:
                with self.assertRaisesRegex(ValueError, "Failed dependency"):
                    loader.load_torch()

    def test_dependency_exception_requires_discarded_child(self):
        self.change("torch", "raise RuntimeError('synthetic failure')\n")
        boundary = self.boundary()
        with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
            with boundary:
                boundary.load_torch()
        self.assertTrue(boundary.failed)
        self.assertEqual(sys.meta_path, self.meta)

    def test_existing_logical_identity_collector_uses_pinned_synthetic_torch(self):
        from test_logical_gpu_identity_20260921 import LogicalIdentityTests
        from test_gpu_runtime_validation_20260921 import UUID
        fixture = LogicalIdentityTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.change("torch",
                    "from types import SimpleNamespace as S\n"
                    "version = S(cuda='12.8', hip=None)\n"
                    "cuda = S(is_initialized=lambda: False, is_available=lambda: True,\n"
                    " device_count=lambda: 1, current_device=lambda: 0,\n"
                    " get_device_properties=lambda i: S(uuid=" + repr(UUID[4:]) + "))\n")
        with self.boundary() as loader:
            result = fixture.collect(dependency_loader=loader.load_torch)
            self.assertEqual(result["device"]["logical_uuid"], UUID)
            self.assertFalse(result["admission"])
            loader.verify()


if __name__ == "__main__":
    unittest.main()
