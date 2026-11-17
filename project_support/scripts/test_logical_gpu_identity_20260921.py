"""Synthetic child CUDA facade; never imports torch or initializes a real GPU."""
import copy
from contextlib import ExitStack
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from saved_physical_location_20260920 import collect_logical_gpu_identity
from test_cpu_diagnostic_bootstrap_20260920 import EXECUTABLE, observation
from test_gpu_runtime_validation_20260921 import UUID


class LogicalIdentityTests(unittest.TestCase):
    def setUp(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        self.runtime = dict(observation(), cuda_visible_devices=UUID)
        self.observe = stack.enter_context(patch(
            "cpu_diagnostic_bootstrap_20260920.observe_runtime",
            return_value=self.runtime))
        self.clock = stack.enter_context(patch("time.time", side_effect=[1000, 1001]))
        self.capacity = dict(
            server="server-4", gpu=0, gpu_uuid=UUID, observed_at=999,
            memory_total_mib=32000, memory_used_mib=500,
            utilization_percent=0, process_count=0)
        self.cuda = Mock()
        self.cuda.is_initialized.return_value = False
        self.cuda.is_available.return_value = True
        self.cuda.device_count.return_value = 1
        self.cuda.current_device.return_value = 0
        self.cuda.get_device_properties.return_value = SimpleNamespace(uuid=UUID[4:])
        self.torch = SimpleNamespace(
            cuda=self.cuda, version=SimpleNamespace(cuda="12.8", hip=None))
        self.loader = Mock(return_value=self.torch)

    def collect(self, **kwargs):
        return collect_logical_gpu_identity(**dict(dict(
            expected_executable=EXECUTABLE, gpu=0, capacity=self.capacity,
            required_memory_mib=20000, coordinated_slot=True,
            dependency_loader=self.loader), **kwargs))

    def test_both_physical_cards_observed_as_logical_zero_without_admission(self):
        for gpu in (0, 1):
            self.clock.side_effect = [1000, 1001]
            result = self.collect(gpu=gpu, capacity=dict(self.capacity, gpu=gpu))
            self.assertEqual(result["device"]["logical_uuid"], UUID)
            self.assertEqual(result["device"]["physical_index"], gpu)
            self.assertTrue(result["logical_device_observed"])
            self.assertTrue(result["capacity_observed_before_cuda"])
            for key in ("native_execution_authorized", "native_dependencies_verified",
                        "native_backward_verified", "admission"):
                self.assertIs(result[key], False)
            self.assertFalse(result["validation"]["admission"])
        self.cuda.get_device_properties.assert_called_with(0)

    def test_loader_precedes_every_cuda_call(self):
        events = Mock()
        events.attach_mock(self.loader, "load")
        events.attach_mock(self.cuda, "cuda")
        self.collect()
        self.assertEqual([call[0] for call in events.mock_calls], [
            "load", "cuda.is_initialized", "cuda.is_available", "cuda.device_count",
            "cuda.current_device", "cuda.get_device_properties"])

    def test_bad_host_before_loader_or_cuda(self):
        self.observe.return_value = dict(self.runtime, addresses=["100.64.3.28"])
        with self.assertRaises(ValueError):
            self.collect()
        self.loader.assert_not_called()
        self.assertEqual(self.cuda.mock_calls, [])

    def test_bad_capacity_before_loader(self):
        for changes in (dict(gpu=7), dict(coordinated_slot=False),
                        dict(required_memory_mib=40000)):
            self.clock.side_effect = [1000, 1001]
            with self.assertRaises(ValueError):
                self.collect(**changes)
        self.loader.assert_not_called()

    def test_busy_or_stale_capacity_before_loader(self):
        for changes in (dict(process_count=1), dict(observed_at=939),
                        dict(utilization_percent=10), dict(memory_used_mib=1024)):
            self.clock.side_effect = [1000, 1001]
            with self.assertRaises(ValueError):
                self.collect(capacity=dict(self.capacity, **changes))
        self.loader.assert_not_called()

    def test_bad_visibility_or_physical_uuid_before_loader(self):
        for value in ("0", "GPU-short", None, UUID + ",other"):
            self.clock.side_effect = [1000, 1001]
            self.observe.return_value = dict(self.runtime, cuda_visible_devices=value)
            with self.assertRaises(ValueError):
                self.collect()
        self.observe.return_value = self.runtime
        self.clock.side_effect = [1000, 1001]
        with self.assertRaises(ValueError):
            self.collect(capacity=dict(self.capacity, gpu_uuid="GPU-short"))
        self.loader.assert_not_called()

    def test_loader_failure_never_touches_cuda(self):
        self.loader.side_effect = RuntimeError("Unverified native ABI")
        with self.assertRaisesRegex(RuntimeError, "ABI"):
            self.collect()
        self.assertEqual(self.cuda.mock_calls, [])

    def test_missing_loader_rejected(self):
        with self.assertRaises(ValueError):
            self.collect(dependency_loader=None)
        self.assertEqual(self.cuda.mock_calls, [])

    def test_changed_runtime_after_loader_before_cuda(self):
        self.observe.side_effect = [self.runtime, dict(self.runtime, user="root")]
        with self.assertRaisesRegex(ValueError, "dependency"):
            self.collect()
        self.assertEqual(self.cuda.mock_calls, [])

    def test_cpu_and_rocm_builds_before_cuda(self):
        for cuda, hip in ((None, None), ("", None), ("12.8", "6.2")):
            self.clock.side_effect = [1000, 1001]
            self.torch.version = SimpleNamespace(cuda=cuda, hip=hip)
            with self.assertRaises(ValueError):
                self.collect()
        self.assertEqual(self.cuda.mock_calls, [])

    def test_preinitialized_child_rejected(self):
        self.cuda.is_initialized.return_value = True
        with self.assertRaises(ValueError):
            self.collect()
        self.cuda.is_available.assert_not_called()

    def test_unavailable_before_device_count(self):
        self.cuda.is_available.return_value = False
        with self.assertRaises(ValueError):
            self.collect()
        self.cuda.device_count.assert_not_called()

    def test_invalid_count_before_current_device(self):
        for value in (0, 2, True):
            self.clock.side_effect = [1000, 1001]
            self.cuda.device_count.return_value = value
            with self.assertRaises(ValueError):
                self.collect()
        self.cuda.current_device.assert_not_called()

    def test_invalid_current_device_before_properties(self):
        for value in (1, False):
            self.clock.side_effect = [1000, 1001]
            self.cuda.current_device.return_value = value
            with self.assertRaises(ValueError):
                self.collect()
        self.cuda.get_device_properties.assert_not_called()

    def test_logical_uuid_not_inferred_from_visibility(self):
        self.cuda.get_device_properties.return_value.uuid = UUID[4:-1] + "c"
        with self.assertRaisesRegex(ValueError, "must agree"):
            self.collect()

    def test_unsupported_uuid_or_missing_property_fails_closed(self):
        for value in (None, "", "0", UUID, UUID[4:] + "\n"):
            self.clock.side_effect = [1000, 1001]
            self.cuda.get_device_properties.return_value = SimpleNamespace(uuid=value)
            with self.assertRaises(ValueError):
                self.collect()
        self.clock.side_effect = [1000, 1001]
        self.cuda.get_device_properties.return_value = SimpleNamespace()
        with self.assertRaises(AttributeError):
            self.collect()

    def test_cuda_error_propagates_without_fallback(self):
        self.cuda.get_device_properties.side_effect = RuntimeError("driver failed")
        with self.assertRaisesRegex(RuntimeError, "driver failed"):
            self.collect()

    def test_runtime_change_after_cuda_rejected(self):
        self.observe.side_effect = [
            self.runtime, self.runtime, dict(self.runtime, cuda_visible_devices="0")]
        with self.assertRaisesRegex(ValueError, "CUDA observation"):
            self.collect()

    def test_elapsed_time_and_capacity_expiry_rejected(self):
        for finished in (999, 1060, 1061, float("nan"), True):
            self.clock.side_effect = [1000, finished]
            with self.assertRaises(ValueError):
                self.collect()

    def test_input_and_returned_snapshots_are_independent(self):
        before = copy.deepcopy((self.runtime, self.capacity))
        result = self.collect()
        result["runtime"]["addresses"].clear()
        result["validation"]["capacity"]["observation"]["gpu"] = 7
        self.assertEqual(before, (self.runtime, self.capacity))


if __name__ == "__main__":
    unittest.main()
