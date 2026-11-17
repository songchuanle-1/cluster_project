"""Synthetic schema tests only; no installed dependency or ELF is inspected."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import dependency_provenance_audit_20260921 as audit
from pinned_diagnostic_imports_20260920 import digest
from saved_dependency_inventory_20260921 import DIRECT_PACKAGES


def file_row(name):
    return {"path": "/opt/cluster/" + name,
            "sha256": hashlib.sha256(name.encode("ascii")).hexdigest()}


def observation():
    return {
        "contract": audit.INPUT_CONTRACT,
        "observed_at": 1789999999.0,
        "runtime": {
            "executable": file_row("env/bin/python"),
            "python": {
                "version": "3.10.13",
                "soabi": "cpython-310-x86_64-linux-gnu",
                "platform": "Linux-5.15-x86_64",
            },
            "torch": {
                "version": "2.1.0",
                "module": file_row("site/torch/__init__.py"),
            },
            "cuda": {
                "version": "12.1",
                "visible_devices": ["GPU-00000000-0000-0000-0000-000000000000"],
            },
        },
        "roots": {
            "conda_source": file_row("conda/etc/profile.d/conda.sh"),
            "environment_root": "/opt/cluster/env",
            "site_packages": ["/opt/cluster/env/lib/python3.10/site-packages"],
            "code_root": "/data/songcl/Project/Cluster_project/Cluster",
            "data_root": "/home/songcl/data/data",
            "work_root": "/data/songcl/Project/Cluster_project/Cluster_checkpoints",
        },
        "bootstrap": [
            {"name": "pinned_diagnostic_imports_20260920",
             **file_row("bootstrap/pinned.py")},
        ],
        "packages": [
            {
                "import_root": name,
                "distribution": name.replace("_", "-"),
                "version": "1.0",
                "module": file_row("site/" + name + "/__init__.py"),
                "metadata": file_row("site/" + name.replace("_", "-")
                                     + "-1.0.dist-info/METADATA"),
            }
            for name in sorted(DIRECT_PACKAGES)
        ],
        "extension": {
            "module": audit.NATIVE_EXTENSION,
            "artifact": file_row(
                "lib/pointgroup_ops/pointgroup_ops_ext.cpython-310-x86_64-linux-gnu.so"),
            "elf": {
                "class": "ELF64",
                "byte_order": "little",
                "machine": "Advanced Micro Devices X86-64",
            },
            "declared_needed": ["libc.so.6", "libtorch.so"],
            "cache_candidates": [
                {"soname": "libc.so.6", **file_row("lib/libc.so.6")},
                {"soname": "libtorch.so", **file_row("lib/libtorch.so")},
            ],
        },
    }


class ProvenanceAuditTests(unittest.TestCase):
    def test_valid_observation_preserves_recorded_abi_facts_only(self):
        receipt = audit.validate_observation(observation())
        self.assertEqual(receipt["contract"], audit.RECEIPT_CONTRACT)
        self.assertEqual(receipt["runtime"]["python"]["soabi"],
                         "cpython-310-x86_64-linux-gnu")
        self.assertEqual(receipt["extension"]["declared_needed"],
                         ["libc.so.6", "libtorch.so"])
        self.assertEqual(receipt["audit"]["direct_package_count"],
                         len(DIRECT_PACKAGES))
        for key in audit.FALSE_GATE_KEYS:
            self.assertIs(receipt[key], False)

    def test_package_missing_added_or_duplicate_rejected(self):
        cases = []
        missing = observation()
        missing["packages"].pop()
        cases.append(missing)
        added = observation()
        extra = copy.deepcopy(added["packages"][0])
        extra["import_root"] = "unexpected"
        extra["distribution"] = "unexpected"
        added["packages"].append(extra)
        cases.append(added)
        duplicate = observation()
        duplicate["packages"][-1] = copy.deepcopy(duplicate["packages"][0])
        cases.append(duplicate)
        for document in cases:
            with self.subTest(document=document):
                with self.assertRaises(ValueError):
                    audit.validate_observation(document)

    def test_duplicate_bootstrap_and_site_root_rejected(self):
        duplicate_bootstrap = observation()
        duplicate_bootstrap["bootstrap"].append(
            copy.deepcopy(duplicate_bootstrap["bootstrap"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate bootstrap"):
            audit.validate_observation(duplicate_bootstrap)
        duplicate_root = observation()
        duplicate_root["roots"]["site_packages"].append(
            duplicate_root["roots"]["site_packages"][0])
        with self.assertRaisesRegex(ValueError, "Duplicate site-packages"):
            audit.validate_observation(duplicate_root)

    def test_canonical_paths_and_hashes_required(self):
        for mutation in (
                lambda doc: doc["runtime"]["executable"].update(path="relative"),
                lambda doc: doc["runtime"]["torch"]["module"].update(
                    sha256="A" * 64),
                lambda doc: doc["extension"]["cache_candidates"][0].update(
                    path="/opt/../lib/libc.so.6")):
            document = observation()
            mutation(document)
            with self.assertRaises(ValueError):
                audit.validate_observation(document)

    def test_extension_declaration_and_cache_candidates_must_match(self):
        document = observation()
        document["extension"]["declared_needed"].append("libm.so.6")
        with self.assertRaisesRegex(ValueError, "sets differ"):
            audit.validate_observation(document)

    def test_elf_fields_are_recorded_but_not_interpreted_as_abi(self):
        for field, value in (
                ("class", "MACHO64"),
                ("byte_order", "middle"),
                ("machine", "")):
            document = observation()
            document["extension"]["elf"][field] = value
            with self.assertRaises(ValueError):
                audit.validate_observation(document)

    def test_strict_json_rejects_duplicate_and_nonfinite(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            audit._strict_json('{"a":1,"a":2}')
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            audit._strict_json('{"a":NaN}')

    def test_receipt_write_is_pinned_fresh_and_canonical(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "observation.json"
            source.write_text(json.dumps(observation()), encoding="ascii")
            source_hash = digest(source.read_bytes())
            output, receipt_hash = audit.write_receipt(
                source, source_hash, root / "receipt.json")
            self.assertEqual(digest(output.read_bytes()), receipt_hash)
            self.assertEqual(
                audit._strict_json(output.read_bytes())["contract"],
                audit.RECEIPT_CONTRACT)
            self.assertEqual(audit.load_receipt(output, receipt_hash)["contract"],
                             audit.RECEIPT_CONTRACT)
            with self.assertRaises(FileExistsError):
                audit.write_receipt(source, source_hash, output)

    def test_observation_hash_drift_blocks_before_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "observation.json"
            source.write_text(json.dumps(observation()), encoding="ascii")
            with self.assertRaisesRegex(ValueError, "hash differs"):
                audit.write_receipt(source, "0" * 64, root / "receipt.json")
            self.assertFalse((root / "receipt.json").exists())


if __name__ == "__main__":
    unittest.main()
