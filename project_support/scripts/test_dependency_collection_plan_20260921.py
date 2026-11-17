"""Synthetic tests for target-runtime dependency plan materialization."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import dependency_observation_collector_20260921 as collector
import dependency_collection_plan_20260921 as planner


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _posix(path):
    return str(path).replace("\\", "/")


class PlanMaterializerTests(unittest.TestCase):
    def _fixture(self, root):
        code = root / "code"
        data = root / "data"
        work = root / "work"
        prefix = root / "env"
        purelib = prefix / "lib/python3.8/site-packages"
        for path in (code, data, work, purelib):
            path.mkdir(parents=True)
        conda = _write(root / "conda.sh", b"export CONDA=1\n")
        bootstrap = _write(
            code / "framework/lib/pointgroup_ops/__init__.py",
            b"BOOTSTRAP = True\n")
        extension_dir = code / "framework/lib/pointgroup_ops"
        extension = _write(
            extension_dir / "pointgroup_ops_ext.cpython-38-x86_64-linux-gnu.so",
            b"\x7fELF")
        seed = {
            "contract": planner.SEED_CONTRACT,
            "roots": {
                "conda_source": _posix(conda),
                "code_root": _posix(code),
                "data_root": _posix(data),
                "work_root": _posix(work),
            },
            "bootstrap": [{
                "name": "pointgroup_ops",
                "relative_path": "framework/lib/pointgroup_ops/__init__.py",
            }],
            "cuda_version": "not-observed",
            "extension_relative_dir": "framework/lib/pointgroup_ops",
            "extension_stem": "pointgroup_ops_ext",
            "distribution_overrides": {},
            "library_overrides": {},
        }
        return seed, prefix, purelib, bootstrap, extension

    def test_plan_uses_target_prefix_and_exact_extension_suffix(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            seed, prefix, purelib, bootstrap, extension = self._fixture(root)
            plan = planner.build_plan(
                seed, prefix=_posix(prefix), purelib=_posix(purelib),
                platlib=_posix(purelib),
                ext_suffix=".cpython-38-x86_64-linux-gnu.so")
            self.assertEqual(plan["contract"], planner.PLAN_CONTRACT)
            self.assertEqual(
                Path(plan["roots"]["environment_root"]).resolve(),
                prefix.resolve())
            self.assertEqual(
                Path(plan["roots"]["site_packages"][0]).resolve(),
                purelib.resolve())
            self.assertEqual(
                Path(plan["bootstrap"][0]["path"]).resolve(),
                bootstrap.resolve())
            self.assertEqual(
                Path(plan["extension_artifact"]).resolve(),
                extension.resolve())
            self.assertEqual(plan["cuda_version"], "not-observed")
            with mock.patch.object(
                    collector, "_canonical_absolute",
                    side_effect=lambda value, label: value):
                collector._validate_plan(plan)

    def test_plan_writer_is_fresh_and_canonical(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            seed, prefix, purelib, _, _ = self._fixture(root)
            plan = planner.build_plan(
                seed, prefix=_posix(prefix), purelib=_posix(purelib),
                platlib=_posix(purelib), ext_suffix=".cpython-38-x86_64-linux-gnu.so")
            output = root / "plan.json"
            path, sha256 = planner.write_plan(plan, output)
            self.assertEqual(path, output.resolve())
            self.assertEqual(len(sha256), 64)
            self.assertEqual(json.loads(output.read_text(encoding="ascii")), plan)
            with self.assertRaisesRegex(ValueError, "fresh"):
                planner.write_plan(plan, output)

    def test_bootstrap_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            seed, prefix, purelib, _, _ = self._fixture(root)
            seed["bootstrap"][0]["relative_path"] = "../outside.py"
            with self.assertRaisesRegex(ValueError, "escapes"):
                planner.build_plan(
                    seed, prefix=_posix(prefix), purelib=_posix(purelib),
                    platlib=_posix(purelib),
                    ext_suffix=".cpython-38-x86_64-linux-gnu.so")

    def test_site_packages_must_stay_inside_environment(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            seed, prefix, _, _, _ = self._fixture(root)
            outside = root / "outside-site-packages"
            outside.mkdir()
            with self.assertRaisesRegex(ValueError, "escapes"):
                planner.build_plan(
                    seed, prefix=_posix(prefix),
                    purelib=_posix(outside), platlib=_posix(outside),
                    ext_suffix=".cpython-38-x86_64-linux-gnu.so")

    def test_missing_target_suffix_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            seed, prefix, purelib, _, _ = self._fixture(root)
            with self.assertRaisesRegex(ValueError, "extension artifact"):
                planner.build_plan(
                    seed, prefix=_posix(prefix), purelib=_posix(purelib),
                    platlib=_posix(purelib), ext_suffix=".cpython-310-x86_64-linux-gnu.so")

    def test_seed_requires_exact_schema_and_unique_json_keys(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            duplicate = _write(root / "duplicate.json", b'{"a":1,"a":2}')
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                planner._load_seed(duplicate)
            missing = _write(root / "missing.json", b'{"contract":"x"}')
            with self.assertRaisesRegex(ValueError, "schema"):
                planner._load_seed(missing)


if __name__ == "__main__":
    unittest.main()
