"""Default NOP. Root-only read-only snapshot at the already deployed NDE source."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
CODE = ROOT / "Cluster"
HERE = Path(__file__).resolve().parent
TICK = HERE.parent
EXPECTED_OWNER = {'token': '8a3431facc69449d9cbb681e512733aa', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-11-08T17:12:25.818193+00:00', 'deadline_at': '2026-11-08T18:12:25.818193+00:00', 'context_sha256': '17d3570ccf2b9677ea549d0757a5615a23f8d370950789ff485f59cc821814c9', 'pending_sha256': '5ac1360d2e0a47c22aa15d5e24144abb7cfd41f5ee33467a735bce1e6101ba06'}
SOURCE = "0747f6acec1c61018ec99acf2efa5329c9b3523c"
HISTORICAL_BASELINE = {'path': 'pipeline/diagnostic_bundles/tick_2218a502/nde_deployment_baseline.json', 'sha256': '3824e0969aa9c6166ee0533848aa1ebef1ca82b55c743af43ba8d0544ecc99d8'}
HISTORICAL_FF = {'path': 'pipeline/diagnostic_bundles/tick_2218a502/nde_deployment_execute/ff_result.json', 'sha256': '0a383a5b827fb0947e5313df3843fc5c0525f07cd0bfe516e59a08af9181fb39'}
HISTORICAL_FF_OWNER = {'token': '2218a50249ea45588e5138890a7f4160', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-11-08T15:32:25.884685+00:00', 'deadline_at': '2026-11-08T16:32:25.884685+00:00', 'context_sha256': 'b168aa4faa7cfc1d40895a3f2b99a3df67b31a4d635e91ba0f76653e5db5c1e8', 'pending_sha256': '562c3d37dc43a6c9dc205de189e87ee42d46c367cd63bb06f50a0784f858ddf3'}
GIT = "C:/Program Files (x86)/Git/cmd/git.exe"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def guard(seconds=60):
    assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
    raw = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert {k: raw[k] for k in EXPECTED_OWNER} == EXPECTED_OWNER
    assert os.environ.get("CODEX_THREAD_ID") == EXPECTED_OWNER["thread_id"]
    assert (datetime.fromisoformat(raw["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > seconds
    mode = read(ROOT / "pipeline/execution_mode.json")
    assert mode == {"mode": "foreground", "target_thread_id": EXPECTED_OWNER["thread_id"]}
    for name, field in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == EXPECTED_OWNER[field]
    assert sha(__file__) == read(HERE / "FROZEN.json")["files"]["prepare_nde_current_baseline.py"]


def git(*args):
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", GIT_CONFIG_NOSYSTEM="1",
               GIT_CONFIG_SYSTEM=os.devnull, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_COUNT="0")
    return subprocess.check_output([GIT, "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(CODE), *args], env=env, timeout=30)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_SNAPSHOT_OR_MUTATION"}))
        return
    guard(90)
    historical_path = ROOT / HISTORICAL_BASELINE["path"]
    ff_path = ROOT / HISTORICAL_FF["path"]
    assert sha(historical_path) == HISTORICAL_BASELINE["sha256"]
    assert sha(ff_path) == HISTORICAL_FF["sha256"]
    historical = read(historical_path)
    ff = read(ff_path)
    assert ff["owner"] == historical["owner"] == HISTORICAL_FF_OWNER
    assert ff["local_head"] == SOURCE and ff["source_verified"] is True
    assert ff["exact9_additions"] is True and ff["prior_tree_and_index_entries_preserved"] is True
    assert ff["user28_and_original_sources_preserved"] is True
    names = read(HERE / "protected_name_sets.json")
    assert sha(HERE / "protected_name_sets.json") == read(HERE / "FROZEN.json")["files"]["protected_name_sets.json"]
    assert set(names["dirty_files"]) == set(historical["dirty_files"]) and len(names["dirty_files"]) == 28
    assert set(names["protected_project_files"]) == set(historical["protected_project_files"])
    assert git("rev-parse", "HEAD").decode().strip() == SOURCE
    status = git("status", "--porcelain=v1", "--untracked-files=all", "-z")
    assert hashlib.sha256(status).hexdigest() == historical["status_sha256"]
    assert not git("diff", "--cached", "--name-only", "-z")
    index = Path(git("rev-parse", "--git-path", "index").decode().strip())
    if not index.is_absolute():
        index = CODE / index
    index_sha = sha(index)
    entries_sha = hashlib.sha256(git("ls-files", "--stage", "-z")).hexdigest()
    assert index_sha == ff["index_sha256_after"] and entries_sha == ff["index_entries_sha256_after"]
    dirty = {n: sha(CODE / n) for n in names["dirty_files"]}
    assert dirty == historical["dirty_files"]
    protected = {n: sha(ROOT / n) for n in names["protected_project_files"]}
    assert all(protected[n] == old for n, old in historical["protected_project_files"].items() if n.startswith("Cluster/"))
    value = {
        "schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "owner": EXPECTED_OWNER, "main_head": SOURCE, "head": SOURCE,
        "dirty_files": dirty, "files": dirty, "protected_project_files": protected,
        "status_sha256": hashlib.sha256(status).hexdigest(), "status_hex": status.hex(),
        "cached_paths_count": 0, "index_sha256": index_sha, "index_entries_sha256": entries_sha,
        "historical_FF": HISTORICAL_FF, "historical_preFF_baseline": HISTORICAL_BASELINE,
        "original_protected_assets": historical["original_protected_assets"],
        "historical_owners_retained": True, "current_HEAD_snapshot_only": True,
        "source_or_shared_mutation": False, "source_or_index_mutation": False,
    }
    guard(30)
    assert git("rev-parse", "HEAD").decode().strip() == SOURCE and sha(index) == index_sha
    assert git("status", "--porcelain=v1", "--untracked-files=all", "-z") == status
    assert hashlib.sha256(git("ls-files", "--stage", "-z")).hexdigest() == entries_sha
    assert all(sha(CODE / n) == d for n, d in dirty.items())
    assert all(sha(ROOT / n) == d for n, d in protected.items())
    assert sha(historical_path) == HISTORICAL_BASELINE["sha256"] and sha(ff_path) == HISTORICAL_FF["sha256"]
    dest = TICK / "protected_assets_before.json"
    with dest.open("x", encoding="utf8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": "CURRENT_BASELINE_RECORDED_ONLY", "path": dest.relative_to(ROOT).as_posix(),
                      "sha256": sha(dest), "user_files": len(dirty), "protected_files": len(protected),
                      "main_head": SOURCE, "source_or_index_mutation": False}))


if __name__ == "__main__":
    main()
