"""Offline resume regressions: no SSH, torch, CUDA, or real child process."""
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import shlex
import tempfile
import unittest
from unittest.mock import Mock, patch

import cluster_resume
import closure
import pipeline_monitor as monitor


class ClusterResumeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "cluster_project"
        self.root.mkdir()
        (self.root / "pipeline").mkdir()
        self.remote = self.root / "remote"
        (self.remote / "configs").mkdir(parents=True)
        self.data = self.remote / "data"
        self.data.mkdir()
        self.pretrain = self.remote / "pretrain.pth"
        self.pretrain.write_bytes(b"unused backbone checkpoint")
        self.checkpoint = self.remote / "last.pth"
        self.checkpoint.write_bytes(b"frozen complete checkpoint (not loaded in tests)")
        # A rooted POSIX spelling also addresses this test file on Windows;
        # production contracts deliberately reject Windows drive spellings.
        self.checkpoint_path = self.checkpoint.as_posix()[len(self.checkpoint.drive):]
        self.config = "configs/candidate.yaml"
        self.config_bytes = ("model:\n  data_root: " + self.data.as_posix()
                             + "\ntrain:\n  pretrain: " + self.pretrain.as_posix()
                             + "\n# Preserve exact deployed YAML bytes\n").encode()
        (self.remote / self.config).write_bytes(self.config_bytes)
        self.commit = "a" * 40
        self.server = dict(name="server-4", host="unused", user="unused",
                           remote_code_root=self.remote.as_posix(), allowed_gpus=[0],
                           conda_source="/unused/conda.sh", conda_env="unused",
                           data_root=self.data.as_posix())
        (self.root / "pipeline/closure_policy.json").write_text(json.dumps(dict(
            enabled=True, path_mappings=[dict(source="/old/data", server_key="data_root")])))
        self.task = dict(id="M206-CGCA", config=self.config, code_commit=self.commit,
                         status="waiting", server="server-4", gpu="0",
                         admission_receipt="pipeline/receipt.json",
                         resume_from=self.checkpoint_path)
        self.common = dict(schema_version=1, purpose="cluster_native_resume",
                           id=self.task["id"], config=self.config, code_commit=self.commit,
                           server="server-4", gpu="0", remote_code_root=self.remote.as_posix(),
                           resume_from=self.checkpoint_path,
                           checkpoint_sha256=hashlib.sha256(self.checkpoint.read_bytes()).hexdigest())
        self.authorization = dict(self.common, authorization_granted=True,
                                  source="human", human_request="只使用GPU0，M206保留完整状态续训")
        self.evidence = dict(self.common, cpu_inspection=dict(
            map_location="cpu", load_succeeded=True, model_state_present=True,
            optimizer_state_present=True, scheduler_state_present=True,
            model_state_nonempty=True, optimizer_state_nonempty=True,
            scheduler_state_nonempty=True,
            meta=dict(epoch=5, best_miou=0.12, epochs_no_improve=2)))
        self.write_documents()

    def write_documents(self):
        for key, value in (("resume_authorization", self.authorization),
                           ("resume_checkpoint_evidence", self.evidence)):
            path = self.root / "pipeline" / (key + ".json")
            path.write_text(json.dumps(value), encoding="utf-8")
            self.task[key] = dict(path="pipeline/" + path.name, sha256=closure.digest(path))

    def validate(self, gpu="0", server=None):
        return cluster_resume.validate(self.root, server or self.server, self.task, gpu)

    def use_gpu(self, gpu, allowed_gpus=(0, 1)):
        self.server["allowed_gpus"] = list(allowed_gpus)
        self.task["gpu"] = str(gpu)
        self.authorization["gpu"] = str(gpu)
        self.evidence["gpu"] = str(gpu)
        self.authorization["human_request"] = "使用server4 GPU" + str(gpu) + "续训同一M206实验"
        self.write_documents()

    def launch(self, *, duplicate=False, gpu=None):
        self.commands = []
        self.started = Mock(return_value=Mock(pid=321))
        original_glob = Path.glob
        def controlled_glob(path, pattern):
            if path.name == "proc" and pattern == "[0-9]*/cmdline":
                return [Mock(read_bytes=lambda: b"python\0tools/train.py\0configs/candidate.yaml\0")] if duplicate else []
            return original_glob(path, pattern)
        def execute_remote(_host, _user, command):
            program = shlex.split(command)[-1]
            self.commands.append(program)
            output = io.StringIO()
            with contextlib.redirect_stdout(output), patch("subprocess.Popen", self.started), \
                    patch.object(Path, "glob", controlled_glob), \
                    patch.dict(os.environ, CONDA_PREFIX=str(self.root / "conda"),
                               TMPDIR=str(self.root / "tmp")):
                exec(compile(program, "<mock remote native launcher>", "exec"), {})
            return output.getvalue()
        with patch.object(closure, "admission") as admission, \
                patch.object(closure, "git", return_value=self.commit), \
                patch.object(cluster_resume.source_integrity, "verify_git") as verify:
            try:
                return closure.safe_launch(self.root, self.server, self.task,
                                           self.task["gpu"] if gpu is None else gpu, execute_remote)
            finally:
                admission.assert_called_once_with(self.root, self.task)
                verify.assert_called_once_with(self.server, self.commit,
                    [("/old/data", self.data.as_posix())], execute_remote)

    def test_valid_full_checkpoint_contract(self):
        self.assertEqual(self.validate()["resume_from"], self.checkpoint_path)

    def test_bad_artifact_hash_rejected(self):
        self.task["resume_checkpoint_evidence"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Artifact hash mismatch"):
            self.validate()

    def test_missing_or_incomplete_state_rejected(self):
        for key in ("model_state_present", "optimizer_state_nonempty", "scheduler_state_present"):
            with self.subTest(key=key):
                saved = copy.deepcopy(self.evidence)
                self.evidence["cpu_inspection"][key] = False
                self.write_documents()
                with self.assertRaisesRegex(ValueError, "Incomplete full-checkpoint"):
                    self.validate()
                self.evidence = saved
        self.write_documents()
        del self.task["resume_authorization"]
        with self.assertRaisesRegex(ValueError, "Missing resume_authorization"):
            self.validate()

    def test_nonhuman_or_mismatched_identity_rejected(self):
        for key, value in (("source", "agent"), ("id", "new-experiment"),
                           ("config", "configs/other.yaml"),
                           ("remote_code_root", "/another/root"),
                           ("code_commit", "b" * 40)):
            saved = copy.deepcopy(self.authorization)
            self.authorization[key] = value
            self.write_documents()
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate()
            self.authorization = saved

    def test_wrong_gpu_or_missing_whitelist_rejected(self):
        with self.assertRaisesRegex(ValueError, "GPU0"):
            self.validate(gpu="1")
        with self.assertRaisesRegex(ValueError, "GPU0"):
            self.validate(server=dict(self.server, allowed_gpus=[1]))

    def test_gpu1_with_matching_authorization_and_whitelist_is_valid(self):
        self.use_gpu(1, allowed_gpus=(1,))
        self.assertEqual(self.validate(gpu="1")["gpu"], "1")

    def test_gpu1_requires_current_whitelist_and_matching_task(self):
        self.use_gpu(1, allowed_gpus=(0,))
        with self.assertRaisesRegex(ValueError, "server-4 GPU0 or GPU1"):
            self.validate(gpu="1")
        self.server["allowed_gpus"] = [0, 1]
        with self.assertRaisesRegex(ValueError, "server-4 GPU0 or GPU1"):
            self.validate(gpu="0")

    def test_gpu1_requires_both_artifacts_to_match_its_card(self):
        self.use_gpu(1)
        for key in ("authorization", "evidence"):
            with self.subTest(document=key):
                document = getattr(self, key)
                document["gpu"] = "0"
                self.write_documents()
                with self.assertRaisesRegex(ValueError, "identity mismatch"):
                    self.validate(gpu="1")
                document["gpu"] = "1"
        self.write_documents()

    def test_gpu1_still_requires_explicit_human_authorization(self):
        self.use_gpu(1)
        self.authorization["authorization_granted"] = False
        self.write_documents()
        with self.assertRaisesRegex(ValueError, "human resume authorization"):
            self.validate(gpu="1")

    def test_other_server_or_gpu_is_rejected_even_if_whitelisted(self):
        self.use_gpu(2, allowed_gpus=(0, 1, 2))
        with self.assertRaisesRegex(ValueError, "server-4 GPU0 or GPU1"):
            self.validate(gpu="2")
        self.use_gpu(1)
        with self.assertRaisesRegex(ValueError, "server-4 GPU0 or GPU1"):
            self.validate(gpu="1", server=dict(self.server, name="server-3"))
        self.task["server"] = "server-3"
        with self.assertRaisesRegex(ValueError, "server-4 GPU0 or GPU1"):
            self.validate(gpu="1")

    def test_bad_meta_rejected(self):
        for key, value in (("epoch", True), ("epoch", -1),
                           ("best_miou", float("nan")), ("epochs_no_improve", -1)):
            saved = copy.deepcopy(self.evidence)
            self.evidence["cpu_inspection"]["meta"][key] = value
            self.write_documents()
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.validate()
            self.evidence = saved

    def test_absolute_fixed_checkpoint_required(self):
        for path in ("last.pth", "/checkpoints/../last.pth", ""):
            self.task["resume_from"] = path
            with self.assertRaisesRegex(ValueError, "absolute POSIX"):
                self.validate()

    def test_exact_old_commit_verified_without_sync_or_current_head(self):
        with patch.object(closure, "git", return_value=self.commit) as git, \
                patch.object(cluster_resume.source_integrity, "verify_git") as verify, \
                patch.object(closure, "safe_sync") as sync:
            cluster_resume.verify_source(self.root, self.root, self.server, self.task, "0", Mock())
        git.assert_called_once_with(self.root, "rev-parse", self.commit + "^{commit}")
        self.assertEqual(verify.call_args.args[1], self.commit)
        sync.assert_not_called()

    def test_old_source_mismatch_rejected(self):
        ssh = Mock()
        with patch.object(closure, "git", return_value=self.commit), \
                patch.object(cluster_resume.source_integrity, "verify_git",
                             side_effect=ValueError("Source integrity mismatch")):
            with self.assertRaisesRegex(ValueError, "Source integrity"):
                cluster_resume.verify_source(self.root, self.root, self.server, self.task, "0", ssh)
        ssh.assert_not_called()

    def test_actual_launch_contains_resume_once_and_preserves_yaml(self):
        self.assertEqual(self.launch()["pid"], 321)
        argv = self.started.call_args.args[0]
        self.assertEqual(argv, ["python", "tools/train.py", self.config,
            "--gpu_ids", "0", "--num_gpus", "1", "--resume", self.checkpoint_path])
        self.assertEqual((self.remote / self.config).read_bytes(), self.config_bytes)

    def test_gpu1_launch_resumes_once_without_changing_yaml(self):
        self.use_gpu(1)
        self.assertEqual(self.launch()["pid"], 321)
        self.assertEqual(self.started.call_args.args[0], ["python", "tools/train.py", self.config,
            "--gpu_ids", "1", "--num_gpus", "1", "--resume", self.checkpoint_path])
        self.assertEqual((self.remote / self.config).read_bytes(), self.config_bytes)

    def test_changed_checkpoint_refuses_before_popen(self):
        self.checkpoint.write_bytes(b"changed after CPU inspection")
        with self.assertRaisesRegex(AssertionError, "checkpoint SHA256"):
            self.launch()
        self.started.assert_not_called()

    def test_existing_same_config_refuses_before_popen(self):
        with self.assertRaisesRegex(RuntimeError, "already running"):
            self.launch(duplicate=True)
        self.started.assert_not_called()

    def test_direct_launch_still_requires_original_admission(self):
        ssh = Mock()
        with patch.object(closure, "admission", side_effect=ValueError("Goal changed")):
            with self.assertRaisesRegex(ValueError, "Goal changed"):
                closure.safe_launch(self.root, self.server, self.task, "0", ssh)
        ssh.assert_not_called()

    def test_omitted_resume_path_cannot_fall_back_to_fresh_launch(self):
        del self.task["resume_from"]
        ssh = Mock()
        self.assertTrue(cluster_resume.requested(self.root, self.task))
        with patch.object(closure, "admission"), patch("subprocess.Popen") as start:
            with self.assertRaisesRegex(ValueError, "fixed absolute POSIX"):
                closure.safe_launch(self.root, self.server, self.task, "0", ssh)
        ssh.assert_not_called()
        start.assert_not_called()

    def test_only_cluster_resume_requests_are_special(self):
        self.assertTrue(cluster_resume.requested(self.root, self.task))
        self.assertFalse(cluster_resume.requested(self.root, dict(config=self.config)))
        self.assertFalse(cluster_resume.requested(self.root.parent / "other_project", self.task))

    def test_monitor_old_commit_resume_reuses_same_id_and_never_syncs(self):
        queue = dict(gpu_queues={"server-4": [self.task]})
        monitor.save_experiment(self.root, dict(id=self.task["id"], history=[dict(action="paused")]))
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(monitor, "ssh", return_value="0, 0, 0, 80000"))
            stack.enter_context(patch.object(monitor, "load_active_gpu_reservations", return_value={}))
            stack.enter_context(patch.object(monitor, "load_servers", return_value={"server-4": self.server}))
            stack.enter_context(patch.object(monitor, "log_decision"))
            stack.enter_context(patch.object(closure, "enabled", return_value=True))
            admission = stack.enter_context(patch.object(closure, "admission"))
            stack.enter_context(patch.object(closure, "validate_foreground_dispatch_budget"))
            git = stack.enter_context(patch.object(closure, "git", return_value=self.commit))
            verify = stack.enter_context(patch.object(cluster_resume.source_integrity, "verify_git"))
            sync = stack.enter_context(patch.object(closure, "safe_sync"))
            launch = stack.enter_context(patch.object(closure, "safe_launch", return_value=dict(pid=321, log="/new/log")))
            stack.enter_context(patch.object(closure, "verify_progress", return_value=True))
            with contextlib.redirect_stdout(io.StringIO()):
                monitor._process_queue(queue, "server-4", "unused", "unused", self.root, set(), {"0"}, [])
        admission.assert_called_once()
        git.assert_called_once_with(self.root, "rev-parse", self.commit + "^{commit}")
        verify.assert_called_once()
        sync.assert_not_called()
        launch.assert_called_once()
        self.assertEqual(self.task["status"], "running")
        self.assertEqual(monitor.load_running(self.root)["server-4"]["0"], "M206-CGCA")
        experiment = monitor.load_experiment(self.root, "M206-CGCA")
        self.assertEqual(experiment["history"][0]["action"], "paused")


if __name__ == "__main__":
    unittest.main()
