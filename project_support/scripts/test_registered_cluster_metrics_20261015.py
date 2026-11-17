"""Replay the actual rounded-lineage failure; all SSH calls are mocked."""

import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import pipeline_monitor as monitor

FOLDER = Path("D:/project/cluster_project/pipeline/diagnostic_bundles/tick_7db522a6c6dd4300918a67f77dc020c5")
LOG = FOLDER / "20261014_154431.log"
CFG = "model_bps"
WD = "/project/checkpoints"
LOGGER = WD + "/" + CFG + "/run/run.log"


class NativeMetricsTests(unittest.TestCase):
    def test_actual_lineage_replay(self):
        content = LOG.read_text(encoding="utf-8")
        result = monitor.parse_native_lineage(content, resumed=True)
        audit = json.loads((FOLDER / "resource_diagnosis.json").read_text(encoding="utf-8"))
        self.assertEqual(result[0], audit["native_full_precision_values"])
        self.assertEqual(result[1], audit["checkpoint_metas"]["last.pth"]["best_miou"])
        self.assertEqual(result[2], audit["checkpoint_metas"]["last.pth"]["epochs_no_improve"])
        rounded = audit["stdout_rounded_values"]
        old_missed = len(rounded) - rounded.index(max(rounded)) - 1
        self.assertEqual(old_missed, 11)
        self.assertEqual(result[2], 8)
        self.assertFalse(monitor.should_early_stop({}, {"patience": 10}, result[2], 26, 50))

    def test_subrounding_improvement_resets_counter(self):
        text = "resume start_epoch:27,best_miou:0.4897165596485138,epochs_no_improve:8!\n"
        text += "mIoU : 0.489848792552948\nmIoU : 0.48\n"
        self.assertEqual(monitor.parse_native_lineage(text, True)[1:], (0.489848792552948, 1))

    def test_restored_patience_survives_new_log(self):
        text = "resume start_epoch:27,best_miou:0.489848792552948,epochs_no_improve:8!\n"
        text += "mIoU : 0.48\nmIoU : 0.481\n"
        self.assertEqual(monitor.parse_native_lineage(text, True)[1:], (0.489848792552948, 10))

    def test_missing_or_invalid_precision_is_unknown(self):
        cases = ["mIOU: 0.490", "mIoU : 0.49",
                 "resume start_epoch:0,best_miou:0.4,epochs_no_improve:8!\nmIoU : 0.49",
                 "resume start_epoch:27,best_miou:0.4,epochs_no_improve:8!\nmIoU : 1.2",
                 "resume start_epoch:27,best_miou:0.4,epochs_no_improve:8!\nmIoU : 1e999",
                 "resume start_epoch:27,best_miou:0.4,epochs_no_improve:8!\nmIoU : 0.4\n"
                 "resume start_epoch:27,best_miou:0.4,epochs_no_improve:8!"]
        for value in cases:
            self.assertEqual(monitor.parse_native_lineage(value, True), (None, None, None))

    def test_exact_live_logger_and_alignment(self):
        rounded = ([0.490, 0.480], 0.490, 1)
        native = "resume start_epoch:27,best_miou:0.4897,epochs_no_improve:8!\n"
        native += "mIoU : 0.489848792552948\nmIoU : 0.48\n"
        with patch.object(monitor, "parse_miou_from_logs", return_value=rounded):
            with patch.object(monitor, "ssh", side_effect=[LOGGER, native]):
                result = monitor.parse_running_miou(["/stdout"], 123, CFG, WD, "host", "user",
                                                     "/resume.pth", registered_native=True)
        self.assertEqual(result[1:], (0.489848792552948, 1))

    def test_unavailable_or_misaligned_logger_cannot_stop(self):
        rounded = ([0.490], 0.490, 0)
        for replies in ([""], [LOGGER, ""], [LOGGER + "\n" + LOGGER.replace("/run/", "/other/")],
                        [LOGGER, "resume start_epoch:9,best_miou:0.4,epochs_no_improve:0!\nmIoU : 0.45"]):
            with patch.object(monitor, "parse_miou_from_logs", return_value=rounded):
                with patch.object(monitor, "ssh", side_effect=replies):
                    self.assertEqual(monitor.parse_running_miou(
                        ["/stdout"], 123, CFG, WD, "host", "user", "/resume.pth",
                        registered_native=True), (None, None, None))

    def test_non_opt_in_resume_behavior_is_unchanged(self):
        old = ([.49], .49, 0)
        with patch.object(monitor, "parse_miou_from_logs", return_value=old):
            with patch.object(monitor, "ssh") as ssh:
                self.assertEqual(monitor.parse_running_miou(
                    ["/stdout"], 123, CFG, WD, "host", "user", "/resume.pth"), old)
                ssh.assert_not_called()


if __name__ == "__main__":
    unittest.main()
