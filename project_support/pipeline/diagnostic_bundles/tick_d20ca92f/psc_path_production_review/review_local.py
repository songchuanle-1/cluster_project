"""Independent local production-controller review. No SSH/GPU/shared mutation."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
from contextlib import redirect_stdout, redirect_stderr
from types import ModuleType, SimpleNamespace
from unittest.mock import patch
import ast
import base64
import copy
import hashlib
import importlib.util
import io
import json
import os
import shlex
import stat
import subprocess
import sys
import yaml

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
PACKET = HERE.parent / "psc_path_production_prepare"
OLD = ROOT / "pipeline/diagnostic_bundles/tick_0bb87433"
SKILL = Path("C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
CHECKS = []


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    return {"path": Path(path).relative_to(ROOT).as_posix(), "sha256": sha(path)}


def check(name, condition):
    assert condition, name
    CHECKS.append({"name": name, "passed": True})


def refused(name, call, error=AssertionError):
    with redirect_stderr(io.StringIO()):
        try:
            call()
        except error:
            check(name, True)
            return
    raise AssertionError("Expected refusal: " + name)


def top_function(source, name):
    return next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == name)


def main():
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    check("actual_current_owner", owner["token"] == "d20ca92f1b654e24ba9cf29f634307b7"
          and owner["thread_id"] == "01a159c5-29ab-7a22-ba7f-e79174757253"
          and datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"]))
    protected_names = ("SERVERS.yaml", "pipeline/goal.json", "pipeline/queue.json", "pipeline/running.json",
                       "pipeline/research_work.json", "pipeline/codex_memory.md")
    before = {name: sha(ROOT / name) for name in protected_names}
    check("packet_FROZEN_exact_requested", sha(PACKET / "FROZEN.json") ==
          "771579c9df5f1d84199eec1ff85639a90a7e77e7e4acf097c2d43128db89ad6f")
    frozen = read(PACKET / "FROZEN.json")
    for name, digest in frozen["files"].items():
        check("frozen_hash:" + name, sha(PACKET / name) == digest)
    check("full_packet_file_set", {p.name for p in PACKET.iterdir()} == set(frozen["files"]) | {"FROZEN.json"})
    check("reviewer_independent_of_author", os.environ.get("CODEX_THREAD_ID") != frozen["author_thread_id"])
    for name in ("lock_core.py", "entry_factory.py", "production_controller.py"):
        compile((PACKET / name).read_bytes(), name, "exec")
        if name != "production_controller.py":
            check("proved_byte_exact:" + name, (PACKET / name).read_bytes() ==
                  (OLD / "psc_path_lock_prepare/v2" / name).read_bytes())
    proof = OLD / "psc_cpu_path_proof_actual.json"
    review = OLD / "psc_cpu_path_proof_actual_independent_review.json"
    check("actual_prior_CPU_proof_hash", sha(proof) == "8b8bf96b56fd828659a780b628010d9e836615fcd8250f1c889405861eae1073")
    check("actual_prior_independent_CPU_review_hash", sha(review) ==
          "ce4d57c001c6dd4a7c2ea1491563c56fc7a7c4ab4371cc2aedae663b73fcac82")
    actual, reviewed = read(proof), read(review)
    check("actual_Linux_CPU_proof_reused_not_reexecuted", actual["returncode"] == 0
          and reviewed["passed"] is True and reviewed["checks_passed"] == 32
          and len(reviewed["three_actual_FDs"]) == len(reviewed["three_actual_kernel_FLOCK_WRITE"]) == 3
          and reviewed["production_activation_passed"] is False)
    controller_source = (PACKET / "production_controller.py").read_text(encoding="utf8")
    tree = ast.parse(controller_source)
    tree.body = [node for node in tree.body if not (
        isinstance(node, ast.ImportFrom) and node.module == "pathlib")]
    controller = ModuleType("independent_POSIX_controller_fixture")
    controller.__dict__.update(Path=PurePosixPath, __file__="/fixture/production_controller.py")
    exec(compile(tree, "production_controller.py", "exec"), controller.__dict__)
    check("exact_prospective_PSC_runtime_source", str(controller.RUNTIME) ==
          "/data/songcl/Project/Cluster_project/Cluster_psc_20261106"
          and controller.COMMIT == "0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d")
    version = read(HERE.parent / "psc_current_activation/native/source_version_binding.json")
    expected8 = {name: digest for name, digest in version["source_files"].items() if name.endswith(".py")}
    check("exact_original_PSC_eight_code_hashes", controller.EXPECTED_SOURCES == expected8 and len(expected8) == 8)
    check("existing_three_production_lock_paths", controller.LOCK_PATHS == [
        "/tmp/cluster_project_gpu0_" + kind + ".lock" for kind in ("training", "diagnostic", "exclusive")])
    check("original_interpreter_and_PREFIX", controller.PYTHON ==
          "/home/songcl/.conda/envs/project_cluster/bin/python"
          and controller.PREFIX == "/home/songcl/.conda/envs/project_cluster")
    for name in ("collect_request.draft.json", "render_request.draft.json"):
        request = read(PACKET / name)
        check("draft_disabled:" + name, request["execution_authorized"] is False
              and request["training_launch_authorized"] is False)
        check("draft_owner_current:" + name, request["owner"] ==
              {key: owner[key] for key in request["owner"]})
        check("draft_exact_all3_producer_hashes:" + name, request["files"] ==
              {filename: sha(PACKET / filename) for filename in ("production_controller.py", "lock_core.py", "entry_factory.py")})
        check("draft_maps_exact:" + name, request["path_mappings"] == controller.MAPPINGS)
    evidence = json.dumps({"scope": "local software fixture only"}).encode("utf8")
    item = {"bytes_base64": base64.b64encode(evidence).decode(), "sha256": hashlib.sha256(evidence).hexdigest()}
    check("embedded_evidence_digest_verifier_actual_function", controller.embedded_evidence(item) ==
          {"scope": "local software fixture only"})
    refused("changed_embedded_receipt_digest_refused", lambda: controller.embedded_evidence({**item, "sha256": "0" * 64}))
    # Capture the real canonical safe_launch command. Fake SSH only records;
    # no remote process or generated training program is executed.
    sys.path.insert(0, str(SKILL))
    import closure
    server = copy.deepcopy(yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf8"))["servers"]["server-4"])
    server.update(remote_code_root=str(controller.RUNTIME),
                  conda_source=str(controller.PRODUCTION / "conda_source.sh"))
    captured = {}
    def fake_ssh(host, user, command):
        words = shlex.split(command)
        program = words[-1]
        parsed = ast.parse(program)
        with_node = next(node for node in parsed.body if isinstance(node, ast.With))
        logfile = ast.literal_eval(with_node.items[0].context_expr.args[0])
        captured.update(host=host, user=user, command=command, words=words, program=program)
        return json.dumps({"pid": 424242, "log": logfile})
    task = {"id": "M231-PSC", "config": controller.CONFIG, "server": "server-4"}
    result = closure.safe_launch(str(ROOT), server, task, 0, fake_ssh)
    check("canonical_safe_launch_captured_no_SSH", result["pid"] == 424242
          and captured["host"] == "192.168.1.115" and captured["user"] == "songcl")
    words = captured["words"]
    check("canonical_outer_python_c_reaches_PATH_file", words[:-1] == [
        "source", str(controller.PRODUCTION / "conda_source.sh"), "&&",
        "conda", "activate", "project_cluster", "&&", "python", "-c"])
    program_tree = ast.parse(captured["program"])
    popen = next(node for node in ast.walk(program_tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                 and node.func.value.id == "subprocess" and node.func.attr == "Popen")
    argv = eval(compile(ast.Expression(popen.args[0]), "literal_canonical_argv", "eval"),
                {"__builtins__": {}, "cfg": controller.CONFIG})
    check("canonical_direct_Popen_PATH_python_exact6_arguments", argv == ["python"] + controller.EXACT_ARGS)
    check("canonical_direct_Popen_keeps_PATH_environment", next(node.value.id for node in popen.keywords if node.arg == "env") == "env")
    check("canonical_direct_Popen_default_close_fds_and_new_session", "close_fds" not in [node.arg for node in popen.keywords]
          and next(node.value.value for node in popen.keywords if node.arg == "start_new_session") is True)
    adapt_node = top_function(captured["program"], "adapt")
    values = {}
    exec(compile(ast.Module(body=[adapt_node], type_ignores=[]), "actual_canonical_adapt_only", "exec"), values)
    yaml_bytes = (HERE.parent / "psc_current_activation/native/candidate.yaml").read_bytes()
    canonical_bytes = yaml.safe_dump(values["adapt"](yaml.safe_load(yaml_bytes)), sort_keys=False).encode("utf8")
    preview_node = next(node for node in ast.walk(top_function(controller_source, "observe"))
                        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "preview_program" for t in node.targets))
    preview_program = ast.literal_eval(preview_node.value)
    preview_output = io.StringIO()
    with patch.object(sys, "argv", ["fixture", base64.b64encode(yaml_bytes).decode(), json.dumps(controller.MAPPINGS)]), redirect_stdout(preview_output):
        exec(compile(preview_program, "actual_controller_preview_only", "exec"), {})
    preview = json.loads(preview_output.getvalue())
    check("controller_preview_byte_exact_real_canonical_YAML_adaptation",
          base64.b64decode(preview["bytes_base64"]) == canonical_bytes
          and preview["sha256"] == hashlib.sha256(canonical_bytes).hexdigest())
    shim = controller.shim_source("e" * 64)
    check("shim_exact_base_hash_entry_hash_deadline_and_activation_PATH", all(text in shim for text in (
        controller.BASE_SHA, "e" * 64, controller.OWNER_DEADLINE,
        "__conda_activate", 'export PATH="$_psc_bin:$PATH"', "hash -r",
        '$(type -P python)', '$(type -t python)', "unset -f python")))
    bash_candidates = [Path("C:/Program Files (x86)/Git/bin/bash.exe"), Path("C:/Program Files/Git/bin/bash.exe")]
    bash = next((path for path in bash_candidates if path.is_file()), None)
    if bash:
        syntax = subprocess.run([str(bash), "-n"], input=shim, text=True, capture_output=True, timeout=15)
        check("independent_actual_Bash_n_generated_production_shim", syntax.returncode == 0)
    core_source = (PACKET / "lock_core.py").read_text(encoding="utf8")
    names = ("refuse", "script_target", "is_training", "validate_training", "check_lock_inode")
    core_values = {"Path": PurePosixPath, "sys": SimpleNamespace(stderr=io.StringIO()),
                   "stat": stat, "BINDING": {"kind": "production", "argv": controller.EXACT_ARGS}}
    exec(compile(ast.Module(body=[top_function(core_source, name) for name in names], type_ignores=[]),
                 "exact_proved_core_selected_pure_checks", "exec"), core_values)
    check("exact_core_detects_canonical_training_argv", core_values["is_training"](core_values["script_target"](controller.EXACT_ARGS)))
    for label, argv_ in (
        ("GPU1", [*controller.EXACT_ARGS[:3], "1", *controller.EXACT_ARGS[4:]]),
        ("resume", controller.EXACT_ARGS + ["--resume", "/foreign/checkpoint"]),
        ("python_B", ["-B"] + controller.EXACT_ARGS),
        ("module_clustered", ["-Bm", "tools.train", controller.CONFIG]),
        ("absolute_train", ["/foreign/tools/train.py"] + controller.EXACT_ARGS[1:]),
    ):
        refused("actual_core_exact_argv_refuses_" + label,
                lambda argv_=argv_: core_values["validate_training"](argv_), SystemExit)
    specification = {"path": "/tmp/cluster_project_gpu0_training.lock", "dev": 2048, "ino": 12345}
    metadata = SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_dev=2048, st_ino=12345, st_uid=1001, st_nlink=1)
    fake_os = SimpleNamespace(fstat=lambda fd: metadata, lstat=lambda path: metadata)
    core_values.update(os=fake_os, BINDING={"uid": 1001})
    core_values["check_lock_inode"](7, specification)
    check("actual_proved_core_accepts_exact_existing_inode_fixture", True)
    for label, changed in (("wrong_inode", {**specification, "ino": 99999}), ("unknown_inode", {**specification, "ino": None})):
        refused("actual_proved_core_refuses_" + label, lambda changed=changed: core_values["check_lock_inode"](7, changed), SystemExit)
    for label, fields in (("foreign_owner", {"st_uid": 1002}), ("multiple_links", {"st_nlink": 2}), ("symlink_mode", {"st_mode": stat.S_IFLNK | 0o777})):
        bad = SimpleNamespace(**{**vars(metadata), **fields})
        fake_os.fstat = lambda fd, bad=bad: bad
        refused("actual_proved_core_refuses_" + label, lambda: core_values["check_lock_inode"](7, specification), SystemExit)
    check("controller_source_has_no_training_invocation_or_lock_mutation",
          "fcntl.flock" not in controller_source and "os.kill" not in controller_source
          and "os.unlink" not in controller_source and "shutil.rmtree" not in controller_source)
    check("three_core_lock_open_no_create_and_inheritable_exec", all(text in core_source for text in (
        "os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC", "os.set_inheritable(descriptor, True)",
        "fcntl.LOCK_EX | fcntl.LOCK_NB", "os.O_WRONLY | os.O_CREAT | os.O_EXCL",
        'os.execve(BINDING["python"]')))
    check("all_original_frozen_files_unchanged_after_review", all(sha(PACKET / name) == digest for name, digest in frozen["files"].items()))
    check("protected_shared_files_unchanged", {name: sha(ROOT / name) for name in protected_names} == before)
    report = {
        "schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(), "passed": True,
        "decision": "PASS_LOCAL_DISABLED_CONTROLLER_FOR_ROOT_ACTUAL_COLLECT_RENDER_REVIEW_ONLY",
        "actual_reviewer_thread_id": os.environ.get("CODEX_THREAD_ID"),
        "author_thread_id": frozen["author_thread_id"], "FROZEN": ref(PACKET / "FROZEN.json"),
        "actual_check_count": len(CHECKS), "checks": CHECKS, "material_concerns": [],
        "proved_core_and_factory_byte_exact": True, "CPU_proof": ref(proof), "CPU_proof_review": ref(review),
        "canonical_launcher": {"path": str(SKILL / "closure.py"), "sha256": sha(SKILL / "closure.py"),
                               "actual_function_called_with_capture_only_fake_SSH": True,
                               "captured_exact_inner_argv": argv, "outer_PATH_python_c_and_direct_Popen_covered": True},
        "source_YAML_interpreter_three_lock_inode_binding": "Controller code verified; actual remote observed facts and rendered production graph remain NOT_RUN here.",
        "UUID_memory_concurrency_scope": "UUID GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c/GPU0/20000MiB/max1 are literal production contract metadata. Controller is CPU-only; core does not query NVML. Root existing fresh resource/UUID/queue guard remains required.",
        "owner_scope": "Fixed current token/thread/deadline and four-field request owner verified; root six-field foreground/context/pending guard remains upstream, never impersonated by this review.",
        "required_root_followup": [
            "Canonical actual PSC resource/admission and independent source deployment precede collect/render.",
            "Fresh root request and actual remote source/YAML/interpreter/three original inode observation must be independently reviewed.",
            "Rendered production entry/binding/shim hash graph and actual PATH observation require separate independent review before SERVERS switch/unique launch.",
            "Actual launch still requires PID/starttime/argv/cwd/source, three original FD/kernel FLOCK identities and increasing native TRAIN steps."
        ],
        "actual_production_observation": "NOT_RUN", "production_render_or_install": "NOT_RUN",
        "trainer_launch": "NOT_RUN", "native_training_or_resources_pass_claimed": False,
        "SSH_GPU_source_deployment_or_shared_mutation": False,
        "local_subprocess_scope": "Git Bash -n generated shim only, when available; no training or remote command."
    }
    with (HERE.parent / "psc_path_production_independent_review.json").open("x", encoding="utf8", newline="\n") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"decision": report["decision"], "check_count": len(CHECKS),
                      "review": ref(HERE.parent / "psc_path_production_independent_review.json")}))


if __name__ == "__main__":
    main()
