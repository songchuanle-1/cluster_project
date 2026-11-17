"""Stdlib-only guards for a new, private, CPU-only CSO diagnostic stage."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

OWNER = {
    "token": "1aa2d994ab004c93b2ea069c90ef9356",
    "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-10T05:07:20.849412+00:00",
    "deadline_at": "2026-11-10T06:07:20.849412+00:00",
    "context_sha256": "eff960250947a7e168ea5f144742d7a877fd810d38f3f958cca86ab058cc9a93",
    "pending_sha256": "d7e6661624a7282adbfadedf6e35e015206fb97cb7ab4add04a79974af7a6f58",
}
STAGE = Path("/data/songcl/Project/Cluster_project/pipeline/cso_cpu_1aa2d994")
RUNTIME_ROOT = Path("/data/songcl/Project/Cluster_project/Cluster_nsd_20261107")
RUNTIME_HEAD = "d21477b0d85e6ddcef428ea98ddf6b86fcc38f7e"
CORE_SHA256 = "28fa6a138fdecc25dadee894fda0fea285ac2759625284bf26998fa1d93f88ee"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(lease):
    assert "torch" not in sys.modules, "Guards must precede Torch import"
    assert socket.gethostname() == "dl04-MS-7E06"
    assert os.getuid() == os.geteuid() == 1001
    assert Path(__file__).resolve().parent == STAGE
    assert sys.dont_write_bytecode and not sys.flags.isolated
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    assert os.environ.get("CODEX_THREAD_ID") == OWNER["thread_id"]
    assert os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
    assert os.environ.get("OMP_NUM_THREADS") == os.environ.get("MKL_NUM_THREADS") == "1"
    assert not os.environ.get("PYTHONPATH") and not os.environ.get("LD_PRELOAD")
    assert os.environ.get("CONDA_DEFAULT_ENV") == "project_cluster"
    assert (datetime.fromisoformat(OWNER["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 180
    frozen = read(STAGE / "FROZEN.json")
    assert frozen["owner"] == OWNER and frozen["scope"] == "REMOTE_CPU_ONLY_SYNTHETIC_EXACT_CORE_CHECK"
    for name, digest in frozen["files"].items():
        path = (STAGE / name).resolve()
        assert path.is_relative_to(STAGE) and sha(path) == digest, name
    lease_path = Path(lease).resolve()
    assert lease_path == STAGE / "execution_lease.json"
    bound_lease = read(lease_path)
    assert bound_lease["owner"] == OWNER and bound_lease["thread_id"] == OWNER["thread_id"]
    assert bound_lease["scope"] == frozen["scope"]
    assert bound_lease["stage"] == str(STAGE)
    assert bound_lease["allowed_gpus"] == [] and bound_lease["cuda_visible_devices"] == ""
    assert bound_lease["worker_wall_seconds"] == 95
    assert all(bound_lease[key] is False for key in (
        "native_start_allowed", "dataset_access_allowed", "external_pids_mutation_allowed"))
    source = read(STAGE / "source_binding.json")
    assert source["owner"] == OWNER and source["experiment_id"] == "M236-CSO"
    assert source["candidate_id"] == "fine-leaf-full-covariance-shape-composition"
    assert source["source_parent_commit"] == RUNTIME_HEAD
    assert source["source_commit"] is None
    assert source["source_core_sha256"] == sha(STAGE / "covariance_shape.py") == CORE_SHA256
    assert source["source_config_sha256"] == sha(STAGE / "candidate.yaml")
    assert source["executed_source_files"] == ["covariance_shape.py"]
    assert source["native_full_model_or_dataset_import"] is False
    assert len(source["source_files_exact9"]) == 9
    assert source["source_FROZEN_sha256"] == sha(STAGE / "historical_source_FROZEN.json")
    environment = read(STAGE / "environment_binding.json")
    assert environment["owner"] == OWNER and environment["selected_arm"] == "activated_native"
    assert environment["base_conda_source"] == "/data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh"
    assert sha(environment["base_conda_source"]) == environment["base_conda_sha256"] == "6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0"
    assert str(Path(sys.executable)) == environment["python_path"]
    assert sha(sys.executable) == environment["python_sha256"]
    for item in environment["torch"].values():
        if isinstance(item, dict) and "path" in item and "sha256" in item:
            assert sha(item["path"]) == item["sha256"]
    actual = subprocess.check_output(
        ["/usr/bin/git", "--no-optional-locks", "-c", "core.fsmonitor=false",
         "-C", str(RUNTIME_ROOT), "rev-parse", "--verify", "HEAD"],
        text=True, timeout=10).strip()
    assert actual == RUNTIME_HEAD
    return source, environment


def save_result(value):
    value["observed_at"] = datetime.now(timezone.utc).isoformat()
    with (STAGE / "core_result.json").open("x", encoding="utf8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
