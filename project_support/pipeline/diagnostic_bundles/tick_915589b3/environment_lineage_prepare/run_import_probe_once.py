"""Default NOP. Root-only fixed contrast; no remote files, model or GPU."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
OWNER = {"token": "915589b3154c4c3c99b1db658f610a1f", "thread_id": "01a159c5-29ab-7a22-ba7f-e79174757253",
    "generated_at": "2026-11-09T01:12:12.491733+00:00", "deadline_at": "2026-11-09T02:12:12.491733+00:00",
    "context_sha256": "dada34d7594e909fafb5912692a196a80a7f11a55681e45cb7b1736039e08e5e",
    "pending_sha256": "d5e94794b90053aff865886bb78f0d94483538397354b954968aa5e13566ffd7"}
BASE = "/data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh"
BASE_SHA = "6c80f3659817b63d1dfb79555dded6e2a486cc4cd75685b462a3082c4a2885d0"
ARMS = ("direct_isolated", "activated_native", "activated_isolated")
BOOTSTRAP = r"""
import base64,hashlib,json,os,socket,sys
assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001
assert os.environ.get('CUDA_VISIBLE_DEVICES')=='' and sys.dont_write_bytecode
payload=json.load(sys.stdin)
raw=base64.b64decode(payload['producer_base64'],validate=True)
assert hashlib.sha256(raw).hexdigest()==payload['producer_sha256']
assert payload['owner']['token']=='915589b3154c4c3c99b1db658f610a1f'
sys.argv=['<fresh-pointnet-import-provenance>','--execute-root','--arm',payload['arm']]
scope={'__name__':'__main__','__file__':'<fresh-pointnet-import-provenance>',
 'BOUND_OWNER':payload['owner'],'BOUND_PRODUCER_SHA':payload['producer_sha256']}
exec(compile(raw,'<fresh-pointnet-import-provenance>','exec'),scope)
"""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save(path, value):
    with Path(path).open("x", encoding="utf8", newline="\n") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def guard(args):
    assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
    assert os.environ.get("CODEX_THREAD_ID") == OWNER["thread_id"]
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert {key: owner[key] for key in OWNER} == OWNER
    assert (datetime.fromisoformat(OWNER["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 300
    for name, key in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == OWNER[key]
    frozen = read(HERE / "FROZEN.json")
    assert frozen["owner"] == OWNER
    assert all(sha(HERE / name) == value for name, value in frozen["files"].items())
    review_path = Path(args.review).resolve()
    assert review_path.is_relative_to(ROOT.resolve()) and sha(review_path) == args.review_sha256
    review = read(review_path)
    assert review["passed"] is True and review["owner"] == OWNER
    assert review["FROZEN_sha256"] == sha(HERE / "FROZEN.json")
    assert review["producer_sha256"] == sha(HERE / "import_provenance.py")
    assert review["transport_sha256"] == sha(__file__)
    assert review["reviewer_thread_id"] not in (OWNER["thread_id"], "/root/fresh_ops")
    assert review["material_concerns"] == []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--review")
    parser.add_argument("--review-sha256")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_TORCH_SSH_OR_MUTATION"}))
        return
    assert args.review and args.review_sha256
    guard(args)
    intent, actual = HERE / "probe_intent.json", HERE / "probe_actual.json"
    assert not intent.exists() and not actual.exists(), "Existing or uncertain contrast: never replay"
    producer = (HERE / "import_provenance.py").read_bytes()
    producer_sha = hashlib.sha256(producer).hexdigest()
    save(intent, {"owner": OWNER, "producer_sha256": producer_sha, "transport_sha256": sha(__file__),
        "independent_review_sha256": args.review_sha256, "fixed_arms": list(ARMS),
        "remote_files_written": False, "GPU_use": False, "no_replay": True})
    record = {"owner": OWNER, "producer_sha256": producer_sha, "intent_sha256": sha(intent), "arms": [],
              "certainty": "uncertain", "remote_files_written": False, "GPU_use": False}
    try:
        for arm in ARMS:
            guard(args)
            interpreter = ["/home/songcl/.conda/envs/project_cluster/bin/python", "-I", "-B", "-c", BOOTSTRAP]
            if arm.startswith("activated"):
                verify = "import hashlib,pathlib,os,socket;assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001;assert hashlib.sha256(pathlib.Path(" + repr(BASE) + ").read_bytes()).hexdigest()==" + repr(BASE_SHA)
                prefix = "/usr/bin/python3 -I -B -c " + shlex.quote(verify)
                selected = ["python"] + (["-I"] if arm == "activated_isolated" else []) + ["-B", "-c", BOOTSTRAP]
                shell = prefix + " && source " + shlex.quote(BASE) + " && conda activate project_cluster && exec " + shlex.join(selected)
                interpreter = ["bash", "-lc", shell]
            command = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=8",
                "songcl@192.168.1.115", "CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 " + shlex.join(interpreter)]
            payload = {"owner": OWNER, "arm": arm, "producer_sha256": producer_sha,
                       "producer_base64": base64.b64encode(producer).decode("ascii")}
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True, encoding="utf8", errors="replace")
            entry = {"arm": arm, "local_ssh_pid": process.pid, "certainty": "uncertain"}
            record["arms"].append(entry)
            try:
                stdout, stderr = process.communicate(json.dumps(payload), timeout=90)
            except subprocess.TimeoutExpired:
                entry["reason"] = "No signal, retry or further arm after uncertain outcome"
                save(actual, record)
                raise SystemExit(75)
            entry.update(certainty="terminal", returncode=process.returncode, stdout=stdout, stderr=stderr)
            try:
                entry["observation"] = json.loads(stdout)
            except json.JSONDecodeError:
                entry["observation"] = None
            assert process.returncode == 0 and entry["observation"] is not None
            observation = entry["observation"]
            assert observation["owner"] == OWNER and observation["producer_sha256"] == producer_sha
            assert observation.get("cuda_initialized_after", False) is False
        record["certainty"] = "terminal"
    except Exception as error:
        record.update(error_type=type(error).__name__, error=str(error))
        save(actual, record)
        raise
    save(actual, record)
    print(json.dumps({"path": str(actual), "sha256": sha(actual), "GPU_use": False,
        "results": [{"arm": value["arm"], "import_passed": value["observation"]["import_passed"],
                     "python": value["observation"]["python"]["path"],
                     "extension": value["observation"].get("resolved_extension")} for value in record["arms"]]}))


if __name__ == "__main__":
    main()
