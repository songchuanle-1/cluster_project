"""Synthetic NVIDIA XML and mocked collection only; no GPU/native imports."""
from contextlib import ExitStack
import subprocess
import unittest
from unittest.mock import patch

from saved_physical_location_20260920 import collect_gpu_inventory, parse_gpu_inventory
from test_cpu_diagnostic_bootstrap_20260920 import EXECUTABLE, observation
from test_gpu_runtime_validation_20260921 import UUID


XML = """<?xml version="1.0" ?>
<!DOCTYPE nvidia_smi_log SYSTEM "nvsmi_device_v12.dtd">
<nvidia_smi_log><gpu id="00000000:01:00.0">
<uuid>GPU-12345678-1234-5678-90ab-1234567890ab</uuid>
<fb_memory_usage><total>32000 MiB</total><used>500 MiB</used></fb_memory_usage>
<utilization><gpu_util>0 %</gpu_util></utilization>
<processes></processes></gpu></nvidia_smi_log>"""


class InventoryParserTests(unittest.TestCase):
    def parse(self, xml=XML, **kwargs):
        return parse_gpu_inventory(
            xml, **dict(dict(gpu=0, expected_uuid=UUID, observed_at=1000), **kwargs))

    def test_both_selected_cards_and_no_authorization(self):
        for gpu in (0, 1):
            result = self.parse(gpu=gpu)
            self.assertEqual(result["gpu"], gpu)
            self.assertEqual(result["memory_total_mib"], 32000)
            self.assertEqual(result["process_count"], 0)
            self.assertFalse(result["native_execution_authorized"])

    def test_graphics_and_compute_processes_count(self):
        result = self.parse(XML.replace("<processes></processes>", (
            "<processes><process_info><pid>11</pid><type>G</type></process_info>"
            "<process_info><pid>22</pid><type>C</type></process_info></processes>")))
        self.assertEqual(result["process_ids"], [11, 22])
        self.assertEqual(result["process_count"], 2)

    def test_invalid_arguments(self):
        for changes in (dict(gpu=True), dict(gpu=7), dict(expected_uuid="GPU-x"),
                        dict(observed_at=True), dict(observed_at=float("nan")),
                        dict(observed_at=-1)):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.parse(**changes)

    def test_missing_duplicate_wrong_or_multiple_uuid(self):
        for xml in (
                XML.replace("<uuid>" + UUID + "</uuid>", ""),
                XML.replace("</uuid>", "</uuid><uuid>" + UUID + "</uuid>"),
                XML.replace(UUID, UUID[:-1] + "c"),
                XML.replace("</nvidia_smi_log>", "<gpu/></nvidia_smi_log>")):
            with self.subTest(xml=xml), self.assertRaises(ValueError):
                self.parse(xml)

    def test_units_na_and_range(self):
        for before, after in (("32000 MiB", "N/A"), ("32000 MiB", "0 MiB"),
                              ("500 MiB", "33000 MiB"), ("500 MiB", "-1 MiB"),
                              ("500 MiB", "500 MB"), ("0 %", "101 %"),
                              ("0 %", "nan %"), ("0 %", "N/A")):
            with self.subTest(after=after), self.assertRaises(ValueError):
                self.parse(XML.replace(before, after))

    def test_unavailable_missing_and_unknown_process_inventory(self):
        for value in ("<processes>N/A</processes>", "", "<processes><unknown/></processes>",
                      "<processes><process_info><pid>0</pid></process_info></processes>",
                      "<processes><process_info/></processes>"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.parse(XML.replace("<processes></processes>", value))

    def test_duplicate_pid_rejected(self):
        process = "<process_info><pid>11</pid></process_info>"
        with self.assertRaises(ValueError):
            self.parse(XML.replace("<processes></processes>",
                                   "<processes>" + process * 2 + "</processes>"))

    def test_malformed_oversized_internal_dtd_and_nontext(self):
        for value in ("<broken>", "x" * (1024 * 1024 + 1), None, b"xml",
                      '<!DOCTYPE x [<!ENTITY x "abc">]><x>&x;</x>'):
            with self.subTest(kind=type(value)), self.assertRaises(ValueError):
                self.parse(value)

    def test_missing_or_duplicate_measurements(self):
        for xml in (XML.replace("<used>500 MiB</used>", ""),
                    XML.replace("</used>", "</used><used>500 MiB</used>"),
                    XML.replace("<gpu_util>0 %</gpu_util>", "<gpu_util/>")):
            with self.assertRaises(ValueError):
                self.parse(xml)


class InventoryCollectorTests(unittest.TestCase):
    def setUp(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        self.runtime = dict(observation(), cuda_visible_devices=UUID)
        self.observe = stack.enter_context(patch(
            "cpu_diagnostic_bootstrap_20260920.observe_runtime", return_value=self.runtime))
        self.run = stack.enter_context(patch(
            "bounded_collation_process_20260921.bounded_process",
            return_value=subprocess.CompletedProcess([], 0, XML, "")))
        self.hash = stack.enter_context(patch(
            "frozen_capture_contract_20260916.file_sha256", return_value="a" * 64))
        self.file = stack.enter_context(patch("pathlib.Path.is_file", return_value=True))
        self.link = stack.enter_context(patch("pathlib.Path.is_symlink", return_value=False))
        self.clock = stack.enter_context(patch("time.time", side_effect=[1000, 1001]))

    def collect(self, **kwargs):
        return collect_gpu_inventory(**dict(dict(
            expected_executable=EXECUTABLE, gpu=0, expected_uuid=UUID,
            nvidia_smi="/usr/bin/nvidia-smi", nvidia_smi_sha256="a" * 64), **kwargs))

    def test_explicit_bounded_read_only_command_and_unobserved_logical_device(self):
        result = self.collect()
        self.assertEqual(self.run.call_args.args[0],
                         ["/usr/bin/nvidia-smi", "-q", "-x", "-i", "0"])
        self.assertEqual(self.run.call_args.kwargs,
                         dict(timeout=10, max_output_bytes=1024 * 1024))
        self.assertEqual(result["capacity"]["observed_at"], 1000)
        self.assertEqual(len(result["inventory_xml_sha256"]), 64)
        for key in ("logical_device_observed", "native_execution_authorized", "admission"):
            self.assertFalse(result[key])
        self.assertEqual(self.hash.call_count, 2)
        self.assertEqual(self.observe.call_count, 2)

    def test_wrong_host_before_command(self):
        self.observe.return_value = dict(self.runtime, addresses=["100.64.3.28"])
        with self.assertRaises(ValueError):
            self.collect()
        self.run.assert_not_called()

    def test_bad_visibility_before_command(self):
        self.observe.return_value = dict(self.runtime, cuda_visible_devices="0")
        with self.assertRaises(ValueError):
            self.collect()
        self.run.assert_not_called()

    def test_bad_executable_before_command(self):
        for value in ("nvidia-smi", "/usr/../bin/nvidia-smi", "/usr//bin/nvidia-smi"):
            with self.assertRaises(ValueError):
                self.collect(nvidia_smi=value)
        self.run.assert_not_called()

    def test_hash_mismatch_before_command(self):
        self.hash.return_value = "b" * 64
        with self.assertRaises(ValueError):
            self.collect()
        self.run.assert_not_called()

    def test_symlink_before_command(self):
        self.link.return_value = True
        with self.assertRaises(ValueError):
            self.collect()
        self.run.assert_not_called()

    def test_command_failure_warning_timeout_and_overflow(self):
        for result in (subprocess.CompletedProcess([], 1, "", "error"),
                       subprocess.CompletedProcess([], 0, XML, "warning")):
            self.clock.side_effect = [1000, 1001]
            self.run.return_value = result
            with self.assertRaises(ValueError):
                self.collect()
        for error in (TimeoutError("deadline"), ValueError("overflow"), OSError("absent")):
            self.clock.side_effect = [1000, 1001]
            self.run.side_effect = error
            with self.assertRaises(type(error)):
                self.collect()

    def test_changed_executable_after_command(self):
        self.hash.side_effect = ["a" * 64, "b" * 64]
        with self.assertRaises(ValueError):
            self.collect()

    def test_runtime_changes_after_command(self):
        self.observe.side_effect = [self.runtime, dict(self.runtime, user="root")]
        with self.assertRaises(ValueError):
            self.collect()

    def test_clock_jumps_fail_closed(self):
        for finished in (999, 1016, float("nan")):
            self.clock.side_effect = [1000, finished]
            with self.assertRaises(ValueError):
                self.collect()

    def test_busy_inventory_never_becomes_idle(self):
        self.run.return_value = subprocess.CompletedProcess([], 0, XML.replace(
            "<processes></processes>",
            "<processes><process_info><pid>33</pid></process_info></processes>"), "")
        result = self.collect()
        self.assertEqual(result["capacity"]["process_count"], 1)
        self.assertFalse(result["admission"])


if __name__ == "__main__":
    unittest.main()
