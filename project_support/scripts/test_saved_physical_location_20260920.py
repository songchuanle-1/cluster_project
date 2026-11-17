"""Synthetic relocation and allocation checks; never deserialize native tensors."""
import copy
import json
import unittest
from unittest.mock import Mock

from frozen_capture_contract_20260916 import fingerprint
from saved_replay_migration_20260920 import ROOT, PHYSICAL, PRIOR, build_contract
from saved_physical_location_20260920 import SavedPhysicalLocation, check_server4_capacity


class LocationTest(unittest.TestCase):
    def setUp(self):
        self.physical = json.loads((ROOT / PHYSICAL).read_text(encoding="utf-8"))
        self.prior = json.loads((ROOT / PRIOR).read_text(encoding="utf-8"))
        self.contract = build_contract(self.physical, self.prior)
        binding = self.contract["original_binding"]
        self.source = {k: v for k, v in binding.items()
                       if k not in ("dataset_source_sha256", "registry_sha256")}
        self.source_check = Mock(return_value=copy.deepcopy(binding))
        self.inspect = Mock(side_effect=self.inspect_file)
        self.payloads = {}
        for row in self.physical["items"]:
            index = row["dataset_index"]
            payload = dict(dataset_index=index, source_binding=self.source,
                           item=["synthetic", index], axes=[{}] * row["expressions"])
            row["native_input_sha256"] = fingerprint(payload["item"])
            self.payloads["item_%d.pth" % index] = payload
        self.ids = self.contract["physical_pair_ids"] + ["missing:%d" % i for i in range(27)]
        self.joins = dict(
            requested=31, counts={"bound": 4, "missing_capture": 27},
            dispositions=[dict(pair_id=p, status="bound" if i < 4 else "missing_capture")
                          for i, p in enumerate(self.ids)],
            bindings=[dict(pair_id=p) for p in self.ids[:4]], source_binding=self.source,
            dataset_source_sha256=binding["dataset_source_sha256"],
            registry_sha256=binding["registry_sha256"])
        self.rehash()
        self.exporter = Mock()
        self.exporter.source_binding = self.source
        self.exporter.dataset_source_sha256 = binding["dataset_source_sha256"]
        self.exporter.plan = dict(registry_sha256=binding["registry_sha256"])
        self.exporter.manifest.return_value = self.joins
        self.read_json = Mock(side_effect=lambda p: copy.deepcopy(self.joins))
        self.load = Mock(side_effect=lambda p: copy.deepcopy(self.payloads[p.rsplit("/", 1)[1]]))

    def rehash(self):
        self.joins["payload_sha256"] = fingerprint(
            {k: v for k, v in self.joins.items() if k != "payload_sha256"})

    def inspect_file(self, path):
        row = next(r for r in self.contract["artifact_transfers"] +
                   self.contract["data_verification"] if r["destination"] == path)
        return dict(regular_file=True, symlink=False, parent_chain_verified=True,
                    bytes=row.get("bytes", 1), sha256=row["sha256"])

    def adapter(self):
        return SavedPhysicalLocation(self.contract, self.physical, self.prior,
                                     self.inspect, self.source_check)

    def run_load(self):
        return self.adapter().load_items(
            self.exporter, self.ids, self.read_json, self.load)

    def test_relocated_load_preserves_original_provenance_and_full_denominator(self):
        before = copy.deepcopy((self.contract, self.physical, self.prior))
        prepared, joins = self.run_load()
        self.assertEqual([p["dataset_index"] for p, _ in prepared], [3040, 3893])
        self.assertEqual(joins["requested"], 31)
        self.assertEqual((self.contract, self.physical, self.prior), before)
        self.assertEqual(self.inspect.call_count, 18)
        self.assertEqual(self.source_check.call_count, 2)
        self.assertEqual(self.exporter.export_item.call_count, 2)
        for call in self.load.call_args_list:
            self.assertTrue(call.args[0].startswith("/data/songcl/Project/Cluster_project/"))
        self.assertFalse(self.contract["native_execution_authorized"])

    def test_real_metadata_contract_constructs_without_native_loading(self):
        physical = json.loads((ROOT / PHYSICAL).read_text(encoding="utf-8"))
        result = SavedPhysicalLocation(self.contract, physical, self.prior,
                                       self.inspect, self.source_check).verify()
        self.assertEqual(result["data_count"], 6)
        self.assertFalse(result["native_execution_authorized"])
        self.load.assert_not_called()

    def test_contract_tamper_rejected_before_io(self):
        self.contract["artifact_transfers"][0]["destination"] = "/tmp/x"
        with self.assertRaisesRegex(ValueError, "contract"):
            self.adapter()
        self.inspect.assert_not_called()

    def test_source_drift_before_loading(self):
        self.source_check.return_value["checkpoint_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source"):
            self.run_load()
        self.load.assert_not_called()

    def test_each_destination_file_drift_blocks_deserialization(self):
        paths = [r["destination"] for r in self.contract["artifact_transfers"] +
                 self.contract["data_verification"]]
        for path in paths:
            def inspect(p):
                value = self.inspect_file(p)
                if path == p:
                    value["sha256"] = "0" * 64
                return value
            self.inspect.side_effect = inspect
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.run_load()
        self.load.assert_not_called()

    def test_symlink_and_parent_chain_uncertainty_rejected(self):
        for change in (dict(symlink=True), dict(parent_chain_verified=False),
                       dict(regular_file=False)):
            self.inspect.side_effect = lambda p: dict(self.inspect_file(p), **change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.run_load()
        self.load.assert_not_called()

    def test_denominator_identity_status_and_fingerprint_drift_rejected(self):
        original = copy.deepcopy(self.joins)
        for kind in ("count", "missing", "duplicate", "substitution", "status",
                     "binding", "hash"):
            self.joins = copy.deepcopy(original)
            if kind == "count":
                self.joins["requested"] = 4
            elif kind == "missing":
                self.joins["dispositions"].pop()
            elif kind == "duplicate":
                self.joins["dispositions"][-1] = self.joins["dispositions"][-2]
            elif kind == "substitution":
                self.joins["dispositions"][-1]["pair_id"] = "other"
            elif kind == "status":
                self.joins["dispositions"][-1]["status"] = "bound"
            elif kind == "binding":
                self.joins["bindings"][0]["pair_id"] = "other"
            self.rehash()
            if kind == "hash":
                self.joins["payload_sha256"] = "0" * 64
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                self.run_load()
        self.load.assert_not_called()

    def test_incomplete_or_duplicate_registry_rejected(self):
        for ids in (self.ids[:4], self.ids[:-1] + [self.ids[0]]):
            with self.assertRaises(ValueError):
                self.adapter().validate_denominator(self.joins, ids)

    def test_exporter_binding_drift_blocks_loading(self):
        self.exporter.source_binding = {}
        with self.assertRaisesRegex(ValueError, "Exporter"):
            self.run_load()
        self.load.assert_not_called()

    def test_payload_identity_input_or_axis_drift_rejected(self):
        original = copy.deepcopy(self.payloads["item_3040.pth"])
        for key, value in (("dataset_index", True), ("dataset_index", 3893),
                           ("source_binding", {}), ("item", []), ("axes", [])):
            self.payloads["item_3040.pth"] = dict(original, **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.run_load()

    def test_mutating_exporter_rejected(self):
        self.exporter.export_item.side_effect = lambda i, item, axes: item.append("changed")
        with self.assertRaisesRegex(ValueError, "mutated"):
            self.run_load()

    def test_reconstruction_mismatch_rejected(self):
        self.exporter.manifest.return_value = {}
        with self.assertRaisesRegex(ValueError, "Reconstructed"):
            self.run_load()

    def test_load_time_source_drift_rejected(self):
        self.source_check.side_effect = [self.contract["original_binding"], {}]
        with self.assertRaisesRegex(ValueError, "source"):
            self.run_load()
        self.assertEqual(self.load.call_count, 2)

    def test_load_time_destination_drift_rejected(self):
        def inspect(path):
            result = self.inspect_file(path)
            if self.load.call_count:
                result["sha256"] = "0" * 64
            return result
        self.inspect.side_effect = inspect
        with self.assertRaises(ValueError):
            self.run_load()
        self.assertEqual(self.load.call_count, 2)


class CapacityTest(unittest.TestCase):
    def setUp(self):
        self.observation = dict(server="server-4", gpu=0, observed_at=1000,
                                memory_total_mib=32000, memory_used_mib=500,
                                utilization_percent=0, process_count=0)

    def check(self, **kwargs):
        args = dict(server="server-4", gpu=0, observation=self.observation,
                    now=1001, required_memory_mib=20000, coordinated_slot=True)
        return check_server4_capacity(**dict(args, **kwargs))

    def test_both_authorized_gpus_without_granting_launch(self):
        for gpu in (0, 1):
            result = self.check(gpu=gpu, observation=dict(self.observation, gpu=gpu))
            self.assertTrue(result["measured_memory_sufficient"])
            self.assertFalse(result["native_execution_authorized"])

    def test_allocation_and_coordination_rejected(self):
        for change in (dict(server="server-6"), dict(gpu=7), dict(gpu=True),
                       dict(coordinated_slot=False), dict(gpu=1)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.check(**change)

    def test_busy_stale_invalid_or_insufficient_observation_rejected(self):
        for key, value in (("observed_at", 940), ("observed_at", 1002),
                           ("process_count", 1), ("process_count", True),
                           ("memory_used_mib", 1024), ("memory_used_mib", -1),
                           ("memory_total_mib", 10000), ("utilization_percent", 10),
                           ("utilization_percent", float("nan")),
                           ("memory_total_mib", float("inf")), ("gpu", True)):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.check(observation=dict(self.observation, **{key: value}))

    def test_memory_requirement_must_be_measured_positive_finite(self):
        for value in (0, -1, True, None, float("nan"), 33000):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.check(required_memory_mib=value)


if __name__ == "__main__":
    unittest.main()
