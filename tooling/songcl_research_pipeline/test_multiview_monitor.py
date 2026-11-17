import unittest
from unittest.mock import patch
import pipeline_monitor as monitor


class MultiviewMonitorTests(unittest.TestCase):
    def test_server_loader_preserves_launch_environment(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "SERVERS.yaml").write_text(
                "servers:\n  gpu:\n    role: gpu_server\n    host: host\n"
                "    user: user\n    conda_source: /opt/conda.sh\n"
                "    conda_env: /env/train\n", encoding="utf-8")
            config = monitor.load_servers(directory)["gpu"]
            self.assertEqual(config["conda_source"], "/opt/conda.sh")
            self.assertEqual(config["conda_env"], "/env/train")

    def test_task_minimum_and_unknown_schedule(self):
        task = {"min_epochs": 30, "patience": 30}
        self.assertFalse(monitor.should_early_stop(task, {}, 48, 25, 30))
        self.assertFalse(monitor.should_early_stop(task, {}, 48, 25, 0))
        self.assertTrue(monitor.should_early_stop(task, {}, 48, 30, 30))
        self.assertEqual(monitor.effective_min_epochs({}, {"min_epochs": 7}), 7)
        self.assertEqual(monitor.effective_min_epochs({"min_epochs": 0}, {"min_epochs": 7}), 0)

    def test_native_metrics_ignore_splits_partials_and_rounding_ties(self):
        text = """
Start training epoch 0
Validation Epoch: [0] Total time: 0:58:13
Validation results: refer_iou_score: 0.0000 (0.0111)
Saved best model at epoch 0 with val_metric: 0.0111
Global IoU based: Mean IoU: 0.0257
Start training epoch 1
Validation Epoch: [1] Total time: 0:58:13
Validation results: refer_iou_score: 0.0000 (0.0111)
Saved best model at epoch 1 with val_metric: 0.0111
Start training epoch 2
Validation Epoch: [2] Total time: 0:58:13
Validation results: refer_iou_score: 0.0000 (0.0090)
Validation results: refer_iou_score: 0.0000 (0.0090)
Start training epoch 3
Validation Epoch: [3] [10/1188] refer_iou_score: 0.9 (0.8)
"""
        self.assertEqual(monitor.parse_multiview_metrics(text), ([.0111, .0111, .009], .0111, 1))

    def test_native_dispatch_never_falls_back_to_generic_splits(self):
        with patch.object(monitor, "ssh", return_value="Start training epoch 0") as ssh:
            self.assertEqual(monitor.parse_miou_from_logs(["x"], "h", "u"), (None, None, None))
            self.assertEqual(ssh.call_count, 1)

    def test_native_schedule_precedes_foreign_epoch_format(self):
        text = "Number of epochs = 30\nStart training epoch 25\nEpoch [25/50]"
        with patch.object(monitor, "ssh", return_value=text):
            self.assertEqual(monitor.get_epoch_info("x", "h", "u")[:3], ("25/30", 25, 30))
        self.assertEqual(monitor.parse_multiview_epoch_progress(
            "num_epoch: 30\nStart training epoch 29\nValidation Epoch: [29] Total time: 1"), ("29/30", 29, 30))

    def test_alias_collision_fails_closed_and_terminal_blocks_fallback(self):
        config = "configs/train/train_mvggt_refer_m85_sib.yaml"
        a = {"id": "m85_sib", "config": config, "status": "done_earlystop", "patience": 30}
        b = dict(a, id="train_mvggt_refer_m85_sib", status="running", patience=10)
        with patch.object(monitor, "load_queue", return_value={"gpu_queues": {"s": [a, b]}}):
            self.assertIsNone(monitor.match_task("p", "s", "train_mvggt_refer_m85_sib"))
        with patch.object(monitor, "load_queue", return_value={"gpu_queues": {"s": [a]}}):
            self.assertEqual(monitor.match_task("p", "s", "train_mvggt_refer_m85_sib"), a)

    def test_trainer_selected_not_accelerate_or_worker(self):
        processes = ("10 1 python /env/bin/accelerate launch scripts/train_mvggt.py train=test\n"
                     "11 10 python scripts/train_mvggt.py train=test\n"
                     "12 11 python scripts/train_mvggt.py train=test")
        with patch.object(monitor, "ssh", side_effect=[
            processes, "10 /code\n11 /code\n12 /code",
            "10 MVGGT_GPU=1\n11 MVGGT_GPU=1\n12 MVGGT_GPU=1"]):
            result = monitor.find_running_processes("h", "u", "/code")
        self.assertEqual(result["configs/train/test.yaml"][0], "11")

    def test_project_specific_config_directory_is_detected(self):
        processes = (
            "36242 1 /env/bin/python -S tools/train.py "
            "configs_song/model_paper5/adares_b2_metric_indicator_res.yaml "
            "--dist --num_gpus 2 --gpu_ids 0 1"
        )
        with patch.object(monitor, "ssh", side_effect=[
            processes,
            "36242 /code",
            "36242 CUDA_VISIBLE_DEVICES=0,1",
        ]):
            result = monitor.find_running_processes("h", "u", "/code")
        config = "configs_song/model_paper5/adares_b2_metric_indicator_res.yaml"
        self.assertEqual(result[config][0], "36242")
        self.assertEqual(result[config][2], "0,1")

    def test_hydra_gpu_slot_count_deduplicates_workers(self):
        processes = (
            "10 1 python /env/bin/accelerate launch scripts/train_mvggt.py train=first\n"
            "11 10 python scripts/train_mvggt.py train=first\n"
            "12 11 python scripts/train_mvggt.py train=first\n"
            "20 1 python /env/bin/accelerate launch scripts/train_mvggt.py train=second\n"
            "21 20 python scripts/train_mvggt.py train=second\n"
            "22 21 python scripts/train_mvggt.py train=second"
        )
        with patch.object(monitor, "ssh", side_effect=[
            processes,
            "10 /code\n11 /code\n12 /code\n20 /code\n21 /code\n22 /code",
            ("10 MVGGT_GPU=4\n11 MVGGT_GPU=4\n12 MVGGT_GPU=4\n"
             "20 MVGGT_GPU=4\n21 MVGGT_GPU=4\n22 MVGGT_GPU=4"),
        ]):
            count = monitor._count_procs_on_gpu("h", "u", "4", "/code")
        self.assertEqual(count, 2)

    def test_project_task_cap_blocks_dispatch_before_gpu_scan(self):
        queue = {
            "gpu_queues": {
                "server-6": [
                    {
                        "id": "queued",
                        "config": "configs/train/queued.yaml",
                        "status": "waiting",
                    }
                ]
            }
        }
        with patch.object(monitor, "ssh") as ssh:
            monitor._process_queue(
                queue,
                "server-6",
                "host",
                "user",
                "project",
                set(),
                {"0", "1"},
                [],
                max_tasks_total=2,
                current_tasks=2,
            )
            ssh.assert_not_called()


if __name__ == "__main__":
    unittest.main()
