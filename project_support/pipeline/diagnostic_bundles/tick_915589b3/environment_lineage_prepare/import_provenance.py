"""Default NOP. Three fixed read-only import/loader lineage observations."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import pickle
import random
import socket
import subprocess
import sys
import traceback

OWNER = {"token": "915589b3154c4c3c99b1db658f610a1f", "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-09T01:12:12.491733+00:00", "deadline_at": "2026-11-09T02:12:12.491733+00:00",
    "context_sha256": "dada34d7594e909fafb5912692a196a80a7f11a55681e45cb7b1736039e08e5e",
    "pending_sha256": "d5e94794b90053aff865886bb78f0d94483538397354b954968aa5e13566ffd7"}
ROOT = Path("/data/songcl/Project/Cluster_project/Cluster_nsd_20261107")
BASE = Path("/data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh")
BASE_SHA = "6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def file_info(path):
    path = Path(path)
    result = {"path": str(path), "exists": path.is_file()}
    if path.is_file():
        result.update(realpath=str(path.resolve()), bytes=path.stat().st_size)
        if path.stat().st_size <= 67108864:
            result["sha256"] = sha(path)
        else:
            result["sha256"] = "NOT_HASHED_OVER_64MiB"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--arm", choices=("direct_isolated", "activated_native", "activated_isolated"))
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_TORCH_IMPORT_OR_EXTERNAL_ACTION"}))
        return
    assert args.arm and globals()["BOUND_OWNER"] == OWNER
    assert socket.gethostname() == "dl04-MS-7E06" and os.getuid() == os.geteuid() == 1001
    assert sys.dont_write_bytecode and os.environ.get("PYTHONDONTWRITEBYTECODE") == "1"
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    assert bool(sys.flags.isolated) == (args.arm != "activated_native")
    assert datetime.now(timezone.utc) < datetime.fromisoformat(OWNER["deadline_at"])
    assert sha(BASE) == BASE_SHA
    head = subprocess.check_output(["/usr/bin/git", "--no-optional-locks", "-c", "core.fsmonitor=false",
        "-C", str(ROOT), "rev-parse", "HEAD"], text=True, timeout=15).strip()
    assert head == "0747f6acec1c61018ec99acf2efa5329c9b3523c"
    os.chdir(ROOT)
    result = {"owner": OWNER, "arm": args.arm, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "producer_sha256": globals()["BOUND_PRODUCER_SHA"], "runtime_HEAD": head, "hostname": socket.gethostname(),
        "python": file_info(sys.executable), "prefix": sys.prefix, "base_prefix": sys.base_prefix,
        "flags": {"isolated": sys.flags.isolated, "ignore_environment": sys.flags.ignore_environment,
                  "no_user_site": sys.flags.no_user_site},
        "environment": {key: os.environ.get(key) for key in (
            "CONDA_PREFIX", "CONDA_DEFAULT_ENV", "PATH", "LD_LIBRARY_PATH", "LD_PRELOAD",
            "PYTHONPATH", "CUDA_HOME", "CUDA_VISIBLE_DEVICES")},
        "sys_path_before_runtime": list(sys.path), "base_conda": file_info(BASE),
        "root_pointnet_init": file_info(ROOT / "pointnet2/__init__.py"),
        "root_pointnet_utils": file_info(ROOT / "pointnet2/pointnet2_utils.py"),
        "GPU_use": False, "model_data_or_training_imported": False}
    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    result["sys_path"] = list(sys.path)
    python_rng = random.getstate()
    torch, cpu_rng, np_rng, np_state = None, None, None, None
    try:
        import torch
        assert not torch.cuda.is_initialized()
        result["cuda_initialized_before"] = False
        cpu_rng = torch.get_rng_state().clone()
        numpy = sys.modules.get("numpy")
        if numpy is not None:
            np_rng = numpy.random
            np_state = pickle.dumps(np_rng.get_state())
        result["torch"] = {"version": torch.__version__, "module": file_info(torch.__file__),
            "extension": file_info(torch._C.__file__)}
        package = importlib.import_module("pointnet2")
        result["pointnet_package"] = {"file": getattr(package, "__file__", None),
            "path": list(package.__path__), "loader_type": type(package.__loader__).__module__ + "." + type(package.__loader__).__qualname__}
        result["pointnet_extension_candidates"] = [
            file_info(path) for directory in package.__path__ for path in sorted(Path(directory).glob("_ext*.so"))]
        # Same import site as the actual failed hierarchy; no tensor/kernel operation.
        utils = importlib.import_module("pointnet2.pointnet2_utils")
        extension = importlib.import_module("pointnet2._ext")
        result["import_passed"] = True
        result["resolved_utils"] = file_info(utils.__file__)
        result["resolved_extension"] = file_info(extension.__file__)
    except Exception as error:
        result["import_passed"] = False
        result["error"] = {"type": type(error).__name__, "message": str(error),
                           "traceback": traceback.format_exc()[-16000:]}
    finally:
        paths = set()
        for line in Path("/proc/self/maps").read_text().splitlines():
            fields = line.split()
            if len(fields) >= 6 and fields[-1].startswith("/"):
                path = fields[-1]
                if any(name in Path(path).name for name in ("libc10", "libtorch", "libstdc++", "libcudart")):
                    paths.add(path)
        result["mapped_native_libraries"] = [file_info(path) for path in sorted(paths)]
        random.setstate(python_rng)
        result["python_rng_restored_exact"] = random.getstate() == python_rng
        if cpu_rng is not None:
            torch.set_rng_state(cpu_rng)
            result["torch_CPU_rng_restored_exact"] = torch.equal(torch.get_rng_state(), cpu_rng)
        if np_state is not None:
            np_rng.set_state(pickle.loads(np_state))
            result["numpy_rng_restored_exact"] = pickle.dumps(np_rng.get_state()) == np_state
        if torch is not None:
            result["cuda_initialized_after"] = torch.cuda.is_initialized()
    print(json.dumps(result, sort_keys=True))
    assert result["python_rng_restored_exact"]
    if torch is not None:
        assert result["cuda_initialized_after"] is False


if __name__ == "__main__":
    main()
