"""Synthetic tests for the stdlib-only dependency observation collector."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock

import dependency_observation_collector_20260921 as collector
import dependency_provenance_audit_20260921 as validator


def _classname():
    return "collector"


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _synthetic_elf():
    strings = b"\0libc.so.6\0libtorch.so\0"
    dynamic_offset = 0x40
    strings_offset = 0x80
    section_offset = 0x100
    data = bytearray(section_offset + 3 * 64)
    data[:4] = b"\x7fELF"
    data[4] = 2
    data[5] = 1
    struct.pack_into("<H", data, 18, 62)
    struct.pack_into("<Q", data, 40, section_offset)
    struct.pack_into("<H", data, 58, 64)
    struct.pack_into("<H", data, 60, 3)
    struct.pack_into("<QQ", data, dynamic_offset, 1, 1)
    struct.pack_into("<QQ", data, dynamic_offset + 16, 1, 11)
    struct.pack_into("<QQ", data, dynamic_offset + 32, 0, 0)
    data[strings_offset:strings_offset + len(strings)] = strings

    def section(index, fields):
        offset = section_offset + index * 64
        struct.pack_into("<IIQQQQIIQQ", data, offset, *fields)

    section(0, (0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
    section(1, (0, 6, 0, 0, dynamic_offset, 48, 2, 0, 8, 16))
    section(2, (0, 3, 0, 0, strings_offset, len(strings), 0, 0, 1, 0))
    return bytes(data)


def _make_packages(site):
    for import_root in sorted(collector.DIRECT_PACKAGES):
        _write(site / import_root / "__init__.py",
               ("NAME = %r\n" % import_root).encode("ascii"))
        distribution = collector.DISTRIBUTION_CANDIDATES.get(
            import_root, (import_root,))[0]
        metadata = site / (distribution + "-1.0.dist-info") / "METADATA"
        _write(metadata,
               ("Metadata-Version: 2.1\nName: %s\nVersion: 1.0\n" %
                distribution).encode("ascii"))
        _write(metadata.parent / "RECORD",
               ((distribution + "-1.0.dist-info/METADATA,,\n")
                .encode("ascii")))


class CollectorTests(unittest.TestCase):
    def test_elf_parser_reads_dynamic_needed_without_execution(self):
        parsed = collector.inspect_elf(_synthetic_elf())
        self.assertEqual(parsed["class_"], "ELF64")
        self.assertEqual(parsed["byte_order"], "little")
        self.assertEqual(parsed["machine"], "Advanced Micro Devices X86-64")
        self.assertEqual(parsed["declared_needed"],
                         ["libc.so.6", "libtorch.so"])

    def test_ldconfig_parser_is_bounded(self):
        rows = collector.parse_ldconfig(
            "libc.so.6 (libc6,x86-64) => /lib/libc.so.6\n"
            "not a cache row\n")
        self.assertEqual(rows, [{"soname": "libc.so.6",
                                 "path": "/lib/libc.so.6"}])

    def test_collection_uses_static_files_and_forced_observations(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            site = root / "site-packages"
            _make_packages(site)
            env_root = root / "environment"
            code_root = root / "code"
            data_root = root / "data"
            work_root = root / "work"
            for path in (env_root, code_root, data_root, work_root):
                path.mkdir()
            conda_source = _write(root / "conda.sh", b"export CONDA=1\n")
            bootstrap = _write(root / "bootstrap.py", b"BOOTSTRAP = True\n")
            extension = _write(root / "pointgroup_ops_ext.so", _synthetic_elf())
            libraries = {
                "libc.so.6": _write(root / "libc.so.6", b"libc"),
                "libtorch.so": _write(root / "libtorch.so", b"torch"),
            }
            plan = {
                "contract": collector.PLAN_CONTRACT,
                "roots": {
                    "conda_source": str(conda_source).replace("\\", "/"),
                    "environment_root": str(env_root).replace("\\", "/"),
                    "site_packages": [str(site).replace("\\", "/")],
                    "code_root": str(code_root).replace("\\", "/"),
                    "data_root": str(data_root).replace("\\", "/"),
                    "work_root": str(work_root).replace("\\", "/"),
                },
                "bootstrap": [{
                    "name": "bootstrap",
                    "path": str(bootstrap).replace("\\", "/"),
                }],
                "cuda_version": "12.1",
                "extension_artifact": str(extension).replace("\\", "/"),
                "distribution_overrides": {},
                "library_overrides": {},
            }
            before = set(sys.modules)
            with mock.patch.object(
                    collector, "_canonical_absolute",
                    side_effect=lambda value, label: value):
                observation = collector.collect_observation(
                    plan,
                    environ={"CUDA_VISIBLE_DEVICES": "0,1"},
                    elf_reader=lambda path: collector.inspect_elf(
                        Path(path).read_bytes()),
                    cache_reader=lambda: [
                        {"soname": name, "path": str(path)}
                        for name, path in libraries.items()
                    ])
            self.assertEqual(observation["contract"],
                             collector.OBSERVATION_CONTRACT)
            self.assertEqual(observation["runtime"]["cuda"]["visible_devices"],
                             ["0", "1"])
            self.assertEqual(len(observation["packages"]),
                             len(collector.DIRECT_PACKAGES))
            self.assertEqual(
                {row["soname"] for row in
                 observation["extension"]["cache_candidates"]},
                {"libc.so.6", "libtorch.so"})
            self.assertFalse(
                any(name in sys.modules and name not in before
                    for name in collector.DIRECT_PACKAGES))

    def test_duplicate_plan_keys_and_missing_output_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            collector._strict_json('{"a":1,"a":2}')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "observation.json"
            output.write_text("occupied", encoding="ascii")
            with self.assertRaisesRegex(ValueError, "fresh"):
                collector.write_observation({}, output)

    def test_missing_declared_package_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            site = root / "site-packages"
            site.mkdir()
            with mock.patch.object(
                    collector, "_canonical_absolute",
                    side_effect=lambda value, label: value):
                with self.assertRaisesRegex(ValueError, "distribution"):
                    collector._collect_packages(
                        {"site_packages": [str(site).replace("\\", "/")]}, {})

    def test_visible_devices_must_come_from_environment(self):
        with self.assertRaisesRegex(ValueError, "CUDA_VISIBLE_DEVICES"):
            collector._visible_devices({})
        with self.assertRaisesRegex(ValueError, "Unique"):
            collector._visible_devices({"CUDA_VISIBLE_DEVICES": "0,0"})

    def test_posix_fixture_crosses_collector_and_validator(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            site = root / "site-packages"
            _make_packages(site)
            env_root = root / "environment"
            code_root = root / "code"
            data_root = root / "data"
            work_root = root / "work"
            for path in (env_root, code_root, data_root, work_root):
                path.mkdir()
            conda_source = _write(root / "conda.sh", b"export CONDA=1\n")
            bootstrap = _write(root / "bootstrap.py", b"BOOTSTRAP = True\n")
            extension = _write(root / "pointgroup_ops_ext.so", _synthetic_elf())
            libraries = {
                "libc.so.6": _write(root / "libc.so.6", b"libc"),
                "libtorch.so": _write(root / "libtorch.so", b"torch"),
            }
            posix_to_real = {
                "/fixture/site-packages": site,
                "/fixture/environment": env_root,
                "/fixture/code": code_root,
                "/fixture/data": data_root,
                "/fixture/work": work_root,
                "/fixture/conda.sh": conda_source,
                "/fixture/bootstrap.py": bootstrap,
                "/fixture/pointgroup_ops_ext.so": extension,
                "/fixture/libc.so.6": libraries["libc.so.6"],
                "/fixture/libtorch.so": libraries["libtorch.so"],
            }

            def fixture_real(value):
                if isinstance(value, str) and value in posix_to_real:
                    return posix_to_real[value]
                return Path(value).resolve()

            def fixture_file_row(value, label):
                if isinstance(value, str) and value in posix_to_real:
                    real = posix_to_real[value]
                    posix = value
                else:
                    real = Path(value).resolve()
                    if real == Path(sys.executable).resolve():
                        posix = "/fixture/runtime/python"
                    else:
                        relative = real.relative_to(root)
                        posix = "/fixture/" + relative.as_posix()
                if not real.is_file():
                    raise ValueError(label + " is not a regular file")
                return {"path": posix, "sha256": _sha256(real)}

            def fixture_resolve(value, label, directory=False):
                real = fixture_real(value)
                if directory and not real.is_dir():
                    raise ValueError(label + " is not a directory")
                if not directory and not real.is_file():
                    raise ValueError(label + " is not a regular file")
                return real

            plan = {
                "contract": collector.PLAN_CONTRACT,
                "roots": {
                    "conda_source": "/fixture/conda.sh",
                    "environment_root": "/fixture/environment",
                    "site_packages": ["/fixture/site-packages"],
                    "code_root": "/fixture/code",
                    "data_root": "/fixture/data",
                    "work_root": "/fixture/work",
                },
                "bootstrap": [{
                    "name": "bootstrap",
                    "path": "/fixture/bootstrap.py",
                }],
                "cuda_version": "12.1",
                "extension_artifact": "/fixture/pointgroup_ops_ext.so",
                "distribution_overrides": {},
                "library_overrides": {},
            }
            with mock.patch.object(
                    collector, "_canonical_absolute",
                    side_effect=lambda value, label: value), \
                    mock.patch.object(
                        collector, "_resolve_path",
                        side_effect=fixture_resolve), \
                    mock.patch.object(
                        collector, "_directory_path",
                        side_effect=lambda value, label: value), \
                    mock.patch.object(
                        collector, "_file_row",
                        side_effect=fixture_file_row):
                observation = collector.collect_observation(
                    plan,
                    environ={"CUDA_VISIBLE_DEVICES": "0,1"},
                    elf_reader=lambda path: collector.inspect_elf(
                        Path(path).read_bytes()),
                    cache_reader=lambda: [
                        {"soname": name, "path": posix}
                        for name, posix in (
                            ("libc.so.6", "/fixture/libc.so.6"),
                            ("libtorch.so", "/fixture/libtorch.so"))
                    ])

            observation_path, observation_sha256 = collector.write_observation(
                observation, root / "observation.json")
            receipt_path, receipt_sha256 = validator.write_receipt(
                observation_path, observation_sha256, root / "receipt.json")
            receipt = validator.load_receipt(receipt_path, receipt_sha256)

            self.assertEqual(receipt["source_contract"],
                             collector.OBSERVATION_CONTRACT)
            self.assertEqual(receipt["runtime"]["cuda"]["visible_devices"],
                             ["0", "1"])
            self.assertEqual(receipt["audit"]["direct_package_count"],
                             len(collector.DIRECT_PACKAGES))
            self.assertEqual(
                receipt["extension"]["declared_needed"],
                ["libc.so.6", "libtorch.so"])
            self.assertFalse(receipt["abi_compatibility_checked"])
            self.assertFalse(receipt["runtime_loader_resolution_verified"])
            self.assertFalse(receipt["native_execution_completed"])
            self.assertFalse(receipt["admission"])


if __name__ == "__main__":
    unittest.main()
