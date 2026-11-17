"""Scoped runtime grant, process discovery and unchanged native launcher contracts."""

import ast
import copy
import inspect
import json
from pathlib import Path
import shlex
import tempfile
import unittest
from unittest.mock import patch

import closure
import isolated_runtime as runtime
import pipeline_monitor as monitor


class IsolatedRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "lighttext_project"
        (self.root / "pipeline/admissions").mkdir(parents=True)
        self.save("SERVERS.yaml", {})
        self.save("pipeline/goal.json", {"target": 0.51})
        self.save("pipeline/execution_mode.json", {"mode": "foreground", "target_thread_id": "owner"})
        self.save("pipeline/closure_policy.json", {"enabled": True, "path_mappings": []})
        self.base = dict(host="192.168.1.120", user="songcl", allowed_gpus=[0, 1],
            remote_code_root="/sdc1/songcl/Project/LightText_project/deployments/production/lighttext",
            conda_source="/production/runtime/activate.sh", conda_env="project_lighttext",
            data_root="/data", work_dir="/work")
        self.private = "/sdc1/songcl/Project/LightText_project/foreground_checks/token/dlpm_native/lighttext"
        self.activation = str(Path(self.private).parent).replace("\\", "/") + "/runtime/activate.sh"
        self.receipt = dict(id="dlpm4_ef", config="configs/model_base_early_exit_4_dlpm.yaml",
            code_commit="1" * 40, goal_sha256=runtime.digest(self.root / "pipeline/goal.json"))
        self.save("pipeline/admissions/receipt.json", self.receipt)
        self.save("pipeline/tested_runtime.json", dict(remote_code_root=self.private, conda_source=self.activation))
        self.grant = dict(kind="isolated_parallel_training", authorization_granted=True,
            source="owning_chat_explicit_reply", user_reply="Approved isolated GPU1 parallel training",
            project="lighttext_project", thread_id="owner", task_id="dlpm4_ef", config=self.receipt["config"],
            code_commit=self.receipt["code_commit"], server="server-3", host=self.base["host"], user=self.base["user"],
            gpu=1, original_depends_on=["dplf4_ef"], base_code_root=self.base["remote_code_root"],
            goal_sha256=self.receipt["goal_sha256"], servers_sha256=runtime.digest(self.root / "SERVERS.yaml"),
            admission_receipt=self.ref("pipeline/admissions/receipt.json"), tested_runtime=self.ref("pipeline/tested_runtime.json"),
            code_root=self.private, conda_source=self.activation)
        self.task = dict(self.receipt, server="server-3", gpu="1", depends_on=[], status="running", pid=123,
            admission_receipt="pipeline/admissions/receipt.json", isolated_runtime=dict(code_root=self.private,
                conda_source=self.activation, original_depends_on=["dplf4_ef"]))
        self.resign()

    def save(self, path, data):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data), encoding="utf-8")

    def ref(self, path):
        return dict(path=path, sha256=runtime.digest(self.root / path))

    def resign(self):
        self.save("pipeline/grant.json", self.grant)
        self.task["isolated_runtime"]["authorization"] = self.ref("pipeline/grant.json")

    def test_default_returns_original_server(self):
        self.assertIs(runtime.runtime_server("unrelated_project", self.base, {}), self.base)

    def test_exact_grant_overrides_only_two_paths(self):
        before = copy.deepcopy(self.base)
        result = runtime.runtime_server(self.root, self.base, self.task)
        self.assertEqual(self.base, before)
        self.assertEqual({k for k in result if result[k] != before[k]}, {"remote_code_root", "conda_source"})
        self.assertEqual(result["remote_code_root"], self.private)

    def test_bad_task_identity_config_commit_server_gpu_and_dependency(self):
        for bad in (dict(id="other"), dict(config="configs/other.yaml"), dict(code_commit="2" * 40),
                    dict(server="server-2"), dict(gpu="0"), dict(claimed_gpu="0"), dict(depends_on=["dplf4_ef"])):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                runtime.runtime_server(self.root, self.base, dict(self.task, **bad))

    def test_bad_human_and_resource_scope_even_when_rehashed(self):
        original = copy.deepcopy(self.grant)
        for bad in (dict(authorization_granted=False), dict(source="inferred"), dict(user_reply=""),
                    dict(thread_id="other"), dict(project="other"), dict(gpu=True), dict(gpu=0),
                    dict(original_depends_on=[]), dict(base_code_root="/other")):
            with self.subTest(bad=bad):
                self.grant = dict(original, **bad)
                self.resign()
                with self.assertRaises(ValueError):
                    runtime.runtime_server(self.root, self.base, self.task)

    def test_changed_policy_and_receipt_and_evidence_are_rejected(self):
        for path, data in (("SERVERS.yaml", {"new": True}), ("pipeline/goal.json", {"target": 1}),
                           ("pipeline/admissions/receipt.json", {}), ("pipeline/tested_runtime.json", {})):
            with self.subTest(path=path):
                original = (self.root / path).read_bytes()
                self.save(path, data)
                with self.assertRaises(ValueError):
                    runtime.runtime_server(self.root, self.base, self.task)
                (self.root / path).write_bytes(original)

    def test_only_exact_already_tested_private_paths(self):
        original = copy.deepcopy(self.grant)
        for bad in (dict(code_root="/tmp/lighttext"), dict(code_root=self.private + "/../lighttext"),
                    dict(code_root=self.private.replace("token", "different")), dict(conda_source="/outside/activate.sh")):
            with self.subTest(bad=bad):
                self.grant = dict(original, **bad)
                self.resign()
                with self.assertRaises(ValueError):
                    runtime.runtime_server(self.root, self.base, self.task)

    def test_artifact_path_escape_and_tampering(self):
        for ref in (dict(path="../outside", sha256="0" * 64), dict(path="pipeline/grant.json", sha256="0" * 64), {}):
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                runtime.artifact(self.root, ref)

    def test_no_runtime_rejected_for_other_project(self):
        other = self.root.parent / "other_project"
        with self.assertRaises(ValueError):
            runtime.runtime_server(other, self.base, self.task)

    def test_finder_merges_only_exact_registered_private_process(self):
        regular = {"configs/dplf.yaml": ("5", "configs/dplf.yaml", "0", None, "native")}
        private = {self.task["config"]: ("123", self.task["config"], "1", None, "native"),
            "configs/foreign.yaml": ("888", "configs/foreign.yaml", "1", None, "foreign")}
        with patch.object(monitor, "PROJECT_ROOT", str(self.root.parent)), patch.object(
                monitor, "find_running_processes", side_effect=[regular, private]) as finder:
            result = monitor.find_project_processes(self.root.name, "server-3", self.base,
                {"gpu_queues": {"server-3": [self.task]}})
        self.assertEqual(set(result), {"configs/dplf.yaml", self.task["config"]})
        self.assertEqual(finder.call_args_list[1].args[-1], self.private)

    def test_finder_identity_or_grant_failure_is_unknown_not_death(self):
        with patch.object(monitor, "PROJECT_ROOT", str(self.root.parent)), patch.object(
                monitor, "find_running_processes", side_effect=[{}, {self.task["config"]: ("999", self.task["config"], "1", None, "native")} ]):
            result = monitor.find_project_processes(self.root.name, "server-3", self.base,
                {"gpu_queues": {"server-3": [self.task]}})
        self.assertIsNone(result)

    def test_default_finder_unchanged(self):
        with patch.object(monitor, "find_running_processes", return_value={"native": "record"}) as finder:
            self.assertEqual(monitor.find_project_processes("lighttext_project", "server-3", self.base, {}), {"native": "record"})
        self.assertEqual(finder.call_count, 1)

    def test_dispatch_source_launch_progress_share_scoped_server(self):
        tree = ast.parse(inspect.getsource(monitor._process_queue))
        for attribute in ("safe_sync", "safe_launch", "verify_progress"):
            calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                     and isinstance(n.func, ast.Attribute) and n.func.attr == attribute]
            self.assertEqual(len(calls), 1)
            self.assertTrue(any(isinstance(arg, ast.Name) and arg.id == "task_server" for arg in calls[0].args))

    def test_native_launcher_private_cwd_B_no_schedule_override(self):
        actual = runtime.runtime_server(self.root, self.base, self.task)
        captured = []
        def ssh(host, user, command):
            tokens = shlex.split(command)
            self.assertEqual(tokens[-4:-1], ["python", "-B", "-c"])
            program = tokens[-1]
            tree = ast.parse(program, feature_version=(3, 8))
            captured.append(program)
            opened = next(n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "open")
            return json.dumps(dict(pid=456, log=ast.literal_eval(opened.args[0])))
        with patch.object(monitor, "load_servers", return_value={"server-3": self.base}):
            result = closure.safe_launch(str(self.root), actual, self.task, "1", ssh)
        self.assertEqual(result["pid"], 456)
        self.assertIn("cwd=root", captured[0])
        self.assertIn("['python', '-B']", captured[0])
        self.assertNotIn("--skip_training", captured[0])
        self.assertNotIn("--patience", captured[0])
        with patch.object(monitor, "load_servers", return_value={"server-3": self.base}), self.assertRaises(ValueError):
            closure.safe_launch(str(self.root), self.base, self.task, "1", ssh)

    def use_workflow_binding(self):
        self.private = self.private.replace("dlpm_native", "dplv_native")
        self.activation = self.activation.replace("dlpm_native", "dplv_native")
        self.workflow_grant = dict(scope="project_experiment_workflow",
            project="lighttext_project", authorization_granted=True,
            source_thread_id="original-approval-chat", human_reply="Approved",
            resource_expansion=False,
            operations=["existing_safe_sync", "admit_queue_and_train_within_current_limits"])
        self.save("pipeline/workflow_grant.json", self.workflow_grant)
        self.authorization = self.ref("pipeline/workflow_grant.json")
        self.save("pipeline/closure_policy.json", dict(enabled=True, path_mappings=[],
            experiment_first=dict(enabled=True, authorization=self.authorization)))
        self.receipt.update(id="dplv4_ef", config="configs/model_base_early_exit_4_dplv.yaml",
            profile="experiment_first", authorization=self.authorization)
        self.save("pipeline/observation.json", {"observed": True})
        self.smoke = dict(self.receipt, steps=2, losses=[9.7, 6.3],
            native_data_loaded=True, backward_finite=True, intended_path_observed=True,
            split="train", data_source=dict(data_root="/data"),
            command=repr(["python", "-B", "native_smoke.py", "--root", self.private,
                "--config", self.receipt["config"], "--commit", self.receipt["code_commit"],
                "--gpu", "1"]), evidence=[self.ref("pipeline/observation.json")])
        self.save("pipeline/smoke.json", self.smoke)
        self.receipt["native_smoke"] = self.ref("pipeline/smoke.json")
        self.save("pipeline/admissions/receipt.json", self.receipt)
        self.save("pipeline/tested_runtime.json", dict(remote_code_root=self.private,
            conda_source=self.activation, activation_sha256="a" * 64))
        self.binding = dict(kind="experiment_first_tested_runtime",
            authorization=self.authorization, project="lighttext_project", thread_id="owner",
            task_id="dplv4_ef", config=self.receipt["config"], code_commit=self.receipt["code_commit"],
            server="server-3", host=self.base["host"], user=self.base["user"], gpu=1,
            depends_on=[], base_code_root=self.base["remote_code_root"],
            goal_sha256=self.receipt["goal_sha256"], servers_sha256=runtime.digest(self.root / "SERVERS.yaml"),
            admission_receipt=self.ref("pipeline/admissions/receipt.json"),
            tested_runtime=self.ref("pipeline/tested_runtime.json"), code_root=self.private,
            conda_source=self.activation, activation_sha256="a" * 64)
        self.task = dict(id="dplv4_ef", config=self.receipt["config"],
            code_commit=self.receipt["code_commit"], server="server-3", gpu="1",
            status="waiting", admission_receipt="pipeline/admissions/receipt.json")
        self.resign_binding()

    def resign_binding(self):
        self.save("pipeline/binding.json", self.binding)
        self.task["isolated_runtime"] = dict(binding=self.ref("pipeline/binding.json"),
            code_root=self.private, conda_source=self.activation)

    def test_workflow_reuses_project_approval_without_fabricating_human_reply(self):
        self.use_workflow_binding()
        before = copy.deepcopy(self.base)
        result = runtime.runtime_server(self.root, self.base, self.task)
        self.assertEqual({k for k in result if result[k] != before[k]},
            {"remote_code_root", "conda_source"})
        self.assertEqual(self.base, before)
        self.assertEqual(result["remote_code_root"], self.private)
        self.assertNotIn("user_reply", self.binding)

    def test_workflow_rejects_disabled_legacy_or_wrong_snapshot(self):
        self.use_workflow_binding()
        policies = [
            dict(enabled=False),
            dict(enabled=True, experiment_first=dict(enabled=False)),
            dict(enabled=True, experiment_first=dict(enabled=True,
                authorization=dict(path="pipeline/workflow_grant.json", sha256="0" * 64)))]
        for policy in policies:
            with self.subTest(policy=policy):
                self.save("pipeline/closure_policy.json", policy)
                with self.assertRaises(ValueError):
                    runtime.runtime_server(self.root, self.base, self.task)

    def test_workflow_rejects_identity_dependency_and_resource_changes(self):
        self.use_workflow_binding()
        original = copy.deepcopy(self.binding)
        for bad in (dict(task_id="other"), dict(config="configs/other.yaml"),
                    dict(code_commit="2" * 40), dict(server="server-2"), dict(host="elsewhere"),
                    dict(gpu=True), dict(gpu=0), dict(thread_id="other"), dict(project="other"),
                    dict(depends_on=["dplf4_ef"]), dict(base_code_root="/other"),
                    dict(goal_sha256="0" * 64), dict(servers_sha256="0" * 64),
                    dict(authorization_granted=True), dict(user_reply="Invented")):
            with self.subTest(bad=bad):
                self.binding = dict(original, **bad)
                self.resign_binding()
                with self.assertRaises(ValueError):
                    runtime.runtime_server(self.root, self.base, self.task)

    def test_workflow_rejects_changed_original_grant_or_unapproved_operations(self):
        self.use_workflow_binding()
        self.workflow_grant["operations"] = []
        self.save("pipeline/workflow_grant.json", self.workflow_grant)
        with self.assertRaises(ValueError):
            runtime.runtime_server(self.root, self.base, self.task)
        self.authorization = self.ref("pipeline/workflow_grant.json")
        self.binding["authorization"] = self.authorization
        self.save("pipeline/closure_policy.json", dict(enabled=True,
            experiment_first=dict(enabled=True, authorization=self.authorization)))
        self.resign_binding()
        with self.assertRaises(ValueError):
            runtime.runtime_server(self.root, self.base, self.task)

    def test_workflow_rejects_unbound_receipt_runtime_and_activation(self):
        self.use_workflow_binding()
        original = copy.deepcopy(self.binding)
        for bad in (dict(admission_receipt=self.ref("pipeline/observation.json")),
                    dict(tested_runtime=self.ref("pipeline/observation.json")),
                    dict(activation_sha256="b" * 64),
                    dict(code_root="/tmp/lighttext"), dict(conda_source="/outside/activate.sh")):
            with self.subTest(bad=bad):
                self.binding = dict(original, **bad)
                self.resign_binding()
                with self.assertRaises(ValueError):
                    runtime.runtime_server(self.root, self.base, self.task)

    def test_workflow_requires_real_smoke_and_exact_tested_location(self):
        self.use_workflow_binding()
        original = copy.deepcopy(self.smoke)
        for bad in (dict(steps=1), dict(backward_finite=False), dict(split="val"),
                    dict(losses=[float("nan"), 6.3]), dict(evidence=[]),
                    dict(command=original["command"].replace("dplv_native", "untested")),
                    dict(command=original["command"].replace("'--gpu', '1'", "'--gpu', '0'")),
                    dict(command="not a command list")):
            with self.subTest(bad=bad):
                self.save("pipeline/smoke.json", dict(original, **bad))
                self.receipt["native_smoke"] = self.ref("pipeline/smoke.json")
                self.save("pipeline/admissions/receipt.json", self.receipt)
                self.binding["admission_receipt"] = self.ref("pipeline/admissions/receipt.json")
                self.resign_binding()
                with self.assertRaises(ValueError):
                    runtime.runtime_server(self.root, self.base, self.task)

    def test_workflow_does_not_reuse_or_expand_old_task_specific_grant(self):
        self.use_workflow_binding()
        self.task["isolated_runtime"] = dict(authorization=self.ref("pipeline/grant.json"),
            code_root=self.private, conda_source=self.activation,
            original_depends_on=["dplf4_ef"])
        with self.assertRaises(ValueError):
            runtime.runtime_server(self.root, self.base, self.task)

    def test_workflow_runtime_is_discovered_by_existing_monitor(self):
        self.use_workflow_binding()
        self.task.update(status="running", pid=123)
        private = {self.task["config"]: ("123", self.task["config"], "1", None, "native")}
        with patch.object(monitor, "PROJECT_ROOT", str(self.root.parent)), patch.object(
                monitor, "find_running_processes", side_effect=[{}, private]):
            result = monitor.find_project_processes(self.root.name, "server-3", self.base,
                {"gpu_queues": {"server-3": [self.task]}})
        self.assertEqual(result, private)

    def test_workflow_native_launcher_keeps_yaml_GPU_and_private_cwd(self):
        self.use_workflow_binding()
        actual = runtime.runtime_server(self.root, self.base, self.task)
        captured = []

        def ssh(host, user, command):
            program = shlex.split(command)[-1]
            captured.append(program)
            tree = ast.parse(program, feature_version=(3, 8))
            opened = next(n for n in ast.walk(tree) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name) and n.func.id == "open")
            return json.dumps(dict(pid=456, log=ast.literal_eval(opened.args[0])))

        with patch.object(monitor, "load_servers", return_value={"server-3": self.base}):
            result = closure.safe_launch(str(self.root), actual, self.task, "1", ssh)
        self.assertEqual(result["pid"], 456)
        self.assertIn("cwd=root", captured[0])
        self.assertIn(self.task["config"], captured[0])
        self.assertNotIn("--resume", captured[0])
        self.assertNotIn("--patience", captured[0])
        with patch.object(monitor, "load_servers", return_value={"server-3": self.base}), self.assertRaises(ValueError):
            closure.safe_launch(str(self.root), self.base, self.task, "1", ssh)


if __name__ == "__main__":
    unittest.main()
