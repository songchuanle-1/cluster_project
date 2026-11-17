"""Synthetic observations only; no CUDA packages, data or device execution."""
import copy
import unittest

from cpu_diagnostic_bootstrap_20260920 import validate_runtime
from saved_physical_location_20260920 import validate_gpu_runtime
from test_cpu_diagnostic_bootstrap_20260920 import EXECUTABLE, observation


UUID = "GPU-12345678-1234-5678-90ab-1234567890ab"


class GpuRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.runtime = dict(observation(), cuda_visible_devices=UUID)
        self.device = dict(
            server="server-4", physical_index=0, physical_uuid=UUID,
            logical_uuid=UUID, logical_device_count=1, current_logical_device=0,
            cuda_available=True, observed_at=1000)
        self.capacity = dict(
            server="server-4", gpu=0, gpu_uuid=UUID, observed_at=1000,
            memory_total_mib=32000, memory_used_mib=500,
            utilization_percent=0, process_count=0)

    def check(self, **kwargs):
        arguments = dict(
            runtime=self.runtime, expected_executable=EXECUTABLE,
            device=self.device, gpu=0, capacity=self.capacity, now=1001,
            required_memory_mib=20000, coordinated_slot=True)
        return validate_gpu_runtime(**dict(arguments, **kwargs))

    def test_both_physical_cards_map_to_logical_zero_without_authorization(self):
        for gpu in (0, 1):
            result = self.check(
                gpu=gpu, device=dict(self.device, physical_index=gpu),
                capacity=dict(self.capacity, gpu=gpu))
            self.assertEqual(result["logical_device"], 0)
            self.assertEqual(result["physical_gpu"], gpu)
            self.assertTrue(result["device_mapping_validated"])
            for field in ("native_execution_authorized", "native_dependencies_verified",
                          "source_assets_verified", "native_backward_verified", "admission"):
                self.assertIs(result[field], False)

    def test_input_observations_unchanged(self):
        before = copy.deepcopy((self.runtime, self.device, self.capacity))
        result = self.check()
        self.assertEqual(before, (self.runtime, self.device, self.capacity))
        result["capacity"]["observation"]["gpu"] = 7
        self.assertEqual(self.capacity["gpu"], 0)

    def test_cpu_validation_still_rejects_visible_gpu(self):
        with self.assertRaisesRegex(ValueError, "CPU process"):
            validate_runtime(self.runtime, EXECUTABLE)
        self.assertTrue(validate_runtime(observation(), EXECUTABLE)["runtime_preflight_passed"])

    def test_no_numeric_multi_device_empty_or_short_uuid_visibility(self):
        for value in ("0", "1", "0,1", "", None, UUID[:12], UUID + ",other"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.check(runtime=dict(self.runtime, cuda_visible_devices=value))

    def test_host_and_process_contract_is_not_bypassed(self):
        for key, value in (
                ("platform", "Windows"), ("addresses", ["100.64.3.28"]),
                ("user", "root"), ("conda_env", "base"),
                ("executable", "/usr/bin/python"), ("isolated", False),
                ("dont_write_bytecode", False), ("paths", {})):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.check(runtime=dict(self.runtime, **{key: value}))

    def test_device_mapping_mismatch(self):
        for key, value in (
                ("server", "server-6"), ("physical_index", 1), ("physical_index", True),
                ("logical_uuid", UUID[:-1] + "c"), ("logical_device_count", 2),
                ("logical_device_count", True), ("current_logical_device", 1),
                ("current_logical_device", False), ("cuda_available", 1)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.check(device=dict(self.device, **{key: value}))

    def test_full_uuid_required(self):
        for value in ("GPU-x", "MIG-" + UUID[4:], "", None, 1, UUID + "\n"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.check(device=dict(self.device, physical_uuid=value))

    def test_capacity_uuid_must_agree(self):
        for value in (None, "GPU-other", UUID[:-1] + "c"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.check(capacity=dict(self.capacity, gpu_uuid=value))

    def test_stale_future_nonfinite_or_boolean_device_time(self):
        for value in (940, 1002, float("nan"), float("inf"), True, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.check(device=dict(self.device, observed_at=value))

    def test_capacity_conditions_still_required(self):
        for key, value in (
                ("observed_at", 940), ("process_count", 1),
                ("memory_used_mib", 1024), ("utilization_percent", 10),
                ("memory_total_mib", 10000), ("gpu", 1)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.check(capacity=dict(self.capacity, **{key: value}))

    def test_slot_allocation_and_memory_requirement_not_bypassed(self):
        for changes in (dict(coordinated_slot=False), dict(gpu=7), dict(gpu=True),
                        dict(required_memory_mib=0), dict(now=float("nan"))):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.check(**changes)

    def test_every_device_field_is_required(self):
        for key in self.device:
            device = dict(self.device)
            del device[key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.check(device=device)


if __name__ == "__main__":
    unittest.main()
