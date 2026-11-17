"""Resolve explicitly authorized, admission-bound LightText task runtimes."""

import copy
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def artifact(project, reference):
    if not isinstance(reference, dict) or set(reference) != {"path", "sha256"}:
        raise ValueError("Exact project-local evidence reference required")
    root = Path(project).resolve()
    path = (root / reference["path"]).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        raise ValueError("Runtime evidence outside project") from None
    if not path.is_file() or digest(path) != reference["sha256"]:
        raise ValueError("Runtime authorization/evidence changed")
    return json.loads(path.read_text(encoding="utf-8"))


def workflow_runtime(project, server, task, scope):
    """Bind an unchanged admitted task to its tested runtime, not a new grant."""
    import experiment_first

    policy = experiment_first.effective(project)
    if not policy or set(scope) != {"binding", "code_root", "conda_source"}:
        raise ValueError("Tested runtime requires the current experiment-first policy")
    binding = artifact(project, scope["binding"])
    grant = artifact(project, policy["authorization"])
    operations = {"existing_safe_sync", "admit_queue_and_train_within_current_limits"}
    mode = json.loads((project / "pipeline/execution_mode.json").read_text(encoding="utf-8"))
    if (binding.get("kind") != "experiment_first_tested_runtime"
            or binding.get("authorization") != policy["authorization"]
            or not operations.issubset(grant.get("operations", []))
            or any(key in binding for key in ("authorization_granted", "user_reply"))
            or binding.get("project") != project.name
            or mode.get("mode") != "foreground"
            or binding.get("thread_id") != mode.get("target_thread_id")
            or binding.get("task_id") != task.get("id")
            or binding.get("config") != task.get("config")
            or binding.get("code_commit") != task.get("code_commit")
            or binding.get("server") != task.get("server")
            or task.get("server") != "server-3"
            or binding.get("host") != server.get("host")
            or server.get("host") != "192.168.1.120"
            or binding.get("user") != server.get("user")
            or server.get("allowed_gpus") != [0, 1]
            or type(binding.get("gpu")) is not int or binding["gpu"] != 1
            or str(task.get("gpu")) != "1"
            or (task.get("claimed_gpu") is not None and str(task["claimed_gpu"]) != "1")
            or binding.get("depends_on") != (task.get("depends_on") or [])
            or binding.get("base_code_root") != server.get("remote_code_root")
            or binding.get("goal_sha256") != digest(project / "pipeline/goal.json")
            or binding.get("servers_sha256") != digest(project / "SERVERS.yaml")):
        raise ValueError("Tested runtime differs from the existing project authorization")
    receipt_ref = binding.get("admission_receipt")
    receipt = artifact(project, receipt_ref)
    if (receipt_ref["path"] != task.get("admission_receipt")
            or receipt.get("profile") != "experiment_first"
            or receipt.get("authorization") != policy["authorization"]
            or any(receipt.get(key) != binding.get(key)
                   for key in ("config", "code_commit", "goal_sha256"))
            or receipt.get("id") != task["id"]):
        raise ValueError("Tested runtime is not bound to the original admitted model")
    experiment_first.validate_smoke(project, receipt)
    smoke = artifact(project, receipt["native_smoke"])
    tested = artifact(project, binding.get("tested_runtime"))
    root = PurePosixPath(binding.get("code_root", ""))
    activation = PurePosixPath(binding.get("conda_source", ""))
    boundary = PurePosixPath("/sdc1/songcl/Project/LightText_project/foreground_checks")
    if (not root.is_absolute() or ".." in root.parts or boundary not in root.parents
            or root.name != "lighttext" or not activation.is_absolute() or ".." in activation.parts
            or root.parent not in activation.parents or tested.get("remote_code_root") != str(root)
            or tested.get("conda_source") != str(activation)
            or not re.fullmatch(r"[0-9a-f]{64}", str(tested.get("activation_sha256", "")))
            or binding.get("activation_sha256") != tested["activation_sha256"]
            or scope["code_root"] != str(root) or scope["conda_source"] != str(activation)
            or smoke.get("data_source", {}).get("data_root") != server.get("data_root")):
        raise ValueError("Only the exact native-tested project-private runtime is allowed")
    try:
        command = ast.literal_eval(smoke["command"])
        expected = {"--root": str(root), "--config": task["config"],
                    "--commit": task["code_commit"], "--gpu": "1"}
        valid = (isinstance(command, list) and all(isinstance(v, str) for v in command)
                 and all(command.count(key) == 1
                         and command[command.index(key) + 1] == value
                         for key, value in expected.items()))
    except (ValueError, TypeError, SyntaxError, IndexError):
        valid = False
    if not valid:
        raise ValueError("Native smoke did not execute this exact runtime/config/commit/GPU")
    result = copy.deepcopy(server)
    result.update(remote_code_root=str(root), conda_source=str(activation))
    return result


def runtime_server(project, server, task):
    scope = task.get("isolated_runtime")
    if scope is None:
        return server
    project = Path(project)
    if project.name != "lighttext_project" or not isinstance(scope, dict):
        raise ValueError("Isolated task runtime is restricted to LightText")
    if "binding" in scope:
        return workflow_runtime(project, server, task, scope)
    grant = artifact(project, scope.get("authorization"))
    mode = json.loads((project / "pipeline/execution_mode.json").read_text(encoding="utf-8"))
    if (grant.get("kind") != "isolated_parallel_training" or grant.get("authorization_granted") is not True
            or grant.get("source") != "owning_chat_explicit_reply" or not grant.get("user_reply")
            or grant.get("project") != project.name or grant.get("thread_id") != mode.get("target_thread_id")
            or grant.get("task_id") != task.get("id") or grant.get("config") != task.get("config")
            or grant.get("code_commit") != task.get("code_commit")
            or grant.get("server") != task.get("server") or grant.get("server") != "server-3"
            or grant.get("host") != server.get("host") or server.get("host") != "192.168.1.120"
            or grant.get("user") != server.get("user") or server.get("allowed_gpus") != [0, 1]
            or type(grant.get("gpu")) is not int or grant.get("gpu") != 1 or str(task.get("gpu")) != "1"
            or (task.get("claimed_gpu") is not None and str(task["claimed_gpu"]) != "1")
            or task.get("depends_on") or grant.get("original_depends_on") != ["dplf4_ef"]
            or scope.get("original_depends_on") != grant["original_depends_on"]
            or grant.get("base_code_root") != server.get("remote_code_root")
            or grant.get("goal_sha256") != digest(project / "pipeline/goal.json")
            or grant.get("servers_sha256") != digest(project / "SERVERS.yaml")):
        raise ValueError("Isolated runtime scope, resource or human authorization mismatch")
    receipt_ref = grant.get("admission_receipt")
    receipt = artifact(project, receipt_ref)
    if (receipt_ref["path"] != task.get("admission_receipt") or receipt.get("id") != task["id"]
            or receipt.get("config") != task["config"] or receipt.get("code_commit") != task["code_commit"]
            or receipt.get("goal_sha256") != grant["goal_sha256"]):
        raise ValueError("Runtime grant is not bound to the original admitted model")
    tested = artifact(project, grant.get("tested_runtime"))
    root = PurePosixPath(grant.get("code_root", ""))
    activation = PurePosixPath(grant.get("conda_source", ""))
    boundary = PurePosixPath("/sdc1/songcl/Project/LightText_project/foreground_checks")
    if (not root.is_absolute() or ".." in root.parts or boundary not in root.parents
            or root.name != "lighttext" or not activation.is_absolute() or ".." in activation.parts
            or root.parent not in activation.parents or tested.get("remote_code_root") != str(root)
            or tested.get("conda_source") != str(activation)
            or scope.get("code_root") != str(root) or scope.get("conda_source") != str(activation)):
        raise ValueError("Only the exact already-tested project-private runtime is allowed")
    result = copy.deepcopy(server)
    result.update(remote_code_root=str(root), conda_source=str(activation))
    return result
