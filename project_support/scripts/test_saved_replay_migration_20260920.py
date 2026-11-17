"""Local static/synthetic migration tests; never load native data."""
import copy
import json
import unittest

from saved_replay_migration_20260920 import (
    ROOT, PHYSICAL, PRIOR, SOURCE, DESTINATION, build_contract, mapped_path,
    verify_destination_artifacts)


class MigrationTest(unittest.TestCase):
    def setUp(self):
        self.physical = json.loads((ROOT / PHYSICAL).read_text(encoding="utf-8"))
        self.prior = json.loads((ROOT / PRIOR).read_text(encoding="utf-8"))

    def contract(self):
        return build_contract(self.physical, self.prior)

    def test_real_metadata_preserves_provenance_and_denominator(self):
        before = copy.deepcopy(self.physical)
        value = self.contract()
        self.assertEqual(self.physical, before)
        self.assertEqual(value["original_dataset_indices"], [3040, 3893])
        self.assertEqual(value["bundle_binding_counts"], {"bound": 4, "missing_capture": 27})
        self.assertEqual(value["registry_denominator"], 31)
        self.assertEqual(value["cumulative_physical_count"], 9)
        self.assertEqual(value["model_geometry_captures"], 0)
        self.assertFalse(value["native_execution_authorized"])
        self.assertEqual(len(value["data_verification"]), 6)

    def test_uncanonical_or_external_paths_rejected(self):
        for path in ("/data3/songcl/Project/Cluster_project/../other/x",
                     str(SOURCE) + "//x", str(SOURCE) + "/./x",
                     str(SOURCE) + "other/x", "relative/file", str(SOURCE) + "/x\\y"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                mapped_path(path, SOURCE, DESTINATION)

    def test_duplicates_and_missing_artifacts_rejected(self):
        for rows in (self.physical["artifacts"][:2],
                     self.physical["artifacts"] + self.physical["artifacts"][:1]):
            with self.subTest(count=len(rows)), self.assertRaises(ValueError):
                build_contract(dict(self.physical, artifacts=rows), self.prior)

    def test_invalid_hash_size_and_scratch_rejected(self):
        for key, value in (("sha256", "x" * 64), ("bytes", True), ("bytes", -1)):
            changed = copy.deepcopy(self.physical)
            changed["artifacts"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                build_contract(changed, self.prior)
        self.physical["scratch"] += "_other"
        with self.assertRaises(ValueError):
            self.contract()

    def test_denominator_and_union_drift_rejected(self):
        for change in ({"registry_denominator": 4}, {"physical_bindings_verified": 10},
                       {"model_geometry_captures": 1},
                       {"cumulative_pair_ids": ["duplicated"] * 9}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                build_contract(self.physical, dict(self.prior, **change))

    def test_incomplete_native_provenance_rejected(self):
        for change in ({"sources_stable": False}, {"error": "failure"},
                       {"gpu_initialized": True}, {"selected_indices": [3893, 3040]}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                build_contract(dict(self.physical, **change), self.prior)

    def test_source_binding_change_rejected(self):
        self.prior["observed_binding"]["checkpoint_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.contract()

    def test_destination_checks_do_not_authorize_execution(self):
        contract = self.contract()
        rows = {row["destination"]: row for row in contract["artifact_transfers"]}
        def inspect(path):
            row = rows[path]
            return dict(regular_file=True, symlink=False, parent_chain_verified=True,
                        bytes=row["bytes"], sha256=row["sha256"])
        result = verify_destination_artifacts(contract, inspect)
        self.assertTrue(result["destination_artifact_bytes_verified"])
        self.assertFalse(result["native_execution_authorized"])
        self.assertFalse(contract["destination_bytes_verified"])

    def test_destination_mutation_or_symlinks_rejected(self):
        contract = self.contract()
        for change in (dict(symlink=True), dict(parent_chain_verified=False),
                       dict(bytes=0), dict(sha256="0" * 64), dict(regular_file=False)):
            def inspect(path):
                row = next(r for r in contract["artifact_transfers"] if r["destination"] == path)
                return dict(dict(regular_file=True, symlink=False, parent_chain_verified=True,
                                 bytes=row["bytes"], sha256=row["sha256"]), **change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                verify_destination_artifacts(contract, inspect)

    def test_destination_mapping_tamper_rejected_before_inspection(self):
        contract = self.contract()
        contract["artifact_transfers"][0]["destination"] = "/tmp/untrusted"
        def inspect(path):
            self.fail("Must reject before inspecting")
        with self.assertRaises(ValueError):
            verify_destination_artifacts(contract, inspect)


if __name__ == "__main__":
    unittest.main()
