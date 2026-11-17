"""Root-only precise NEC terminal bookkeeping; no remote/checkpoint/source operation."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import copy
import csv
import hashlib
import io
import json
import os
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
HERE = Path(__file__).resolve().parent
ID = "M228-NEC"
CID = "hierarchy-coupled-node-edge-state-composition"
COMMIT = "6bc36adfe42764aac2209e6600fb3a783e2fa374"
ARCHIVE = "35d448b2c70544049fa18e199081d30d"
EXPECTED = {
    "nec_terminal_observation.json": "3ab15a934ea0bb12976dab3b750eb602538838517487f41e5197a08cafe33881",
    "nec_native_terminal_metrics.json": "0ca147c16846033ada9baf0ddd5d4d3e00d8e9c69f08632d1f8760c38a3d6c32",
    "nec_checkpoint_cpu_observation.json": "3b5ad87436d94003b48aaf9c3ad75f98dd8347e4e0cee1665dae4290e18d89d6",
    "nec_terminal_independent_review.json": "703f4c75107fdb44fc05f8fa3223a0ee9f50117205da65a210c5d1dffdbe2e05",
}


def rd(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path.read_bytes())}


def digest(value):
    return sha(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode())


OWNER = rd(HERE / "nec_terminal_observation.json")["owner"]


def guard():
    live = rd(P / "headless/.foreground.lockdir/owner.json")
    assert all(live.get(k) == v for k, v in OWNER.items()), "Owner changed"
    assert os.environ.get("CODEX_THREAD_ID") == OWNER["thread_id"], "Root owning chat required"
    assert datetime.now(timezone.utc) < datetime.fromisoformat(OWNER["deadline_at"])
    assert sha((P / "headless/.tick_context.json").read_bytes()) == OWNER["context_sha256"]
    assert sha((P / "headless/.tick_context_state.next.json").read_bytes()) == OWNER["pending_sha256"]


def exclusive_json(path, value):
    guard()
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def replace_bytes(path, data):
    guard()
    temporary = path.with_name(path.name + "." + OWNER["token"][:8] + ".terminal.tmp")
    with temporary.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    guard()
    os.replace(temporary, path)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def protected():
    git = ["C:/Program Files (x86)/Git/cmd/git.exe", "--no-optional-locks",
           "-c", "core.fsmonitor=false", "-C", str(ROOT / "Cluster")]
    def query(*args):
        return subprocess.check_output(git + list(args))
    index = Path(query("rev-parse", "--git-path", "index").decode().strip())
    if not index.is_absolute():
        index = ROOT / "Cluster" / index
    source = {}
    names = query("ls-files", "--cached", "--others", "--exclude-standard", "-z").split(b"\0")
    for raw in names:
        if not raw:
            continue
        name = raw.decode("utf-8")
        f = ROOT / "Cluster" / name
        if f.suffix in {".py", ".pyi", ".yaml", ".yml", ".json", ".sh", ".cpp", ".cu", ".h"} and f.is_file():
            source[name] = sha(f.read_bytes())
    files = [ROOT / "SERVERS.yaml", P / "queue.json", P / "running.json",
             P / "goal.json", P / "closure_policy.json"]
    files += list((P / "admissions").glob("*.json"))
    files += [f for f in (P / "experiments").glob("*.json") if f.name != ID + ".json"]
    files += list((P / "authorizations").glob("*.json"))
    return {"head": query("rev-parse", "HEAD").decode().strip(),
            "status_hex": query("status", "--porcelain=v1", "--untracked-files=all", "-z").hex(),
            "index_sha256": sha(index.read_bytes()), "source": source,
            "unrelated_ledgers_and_settings": {f.relative_to(ROOT).as_posix(): sha(f.read_bytes()) for f in files}}


def facts():
    entries = {}
    for name, expected in EXPECTED.items():
        f = HERE / name
        assert sha(f.read_bytes()) == expected, name
        entries[name] = rd(f)
    terminal = entries["nec_terminal_observation.json"]
    metrics = entries["nec_native_terminal_metrics.json"]
    checkpoint = entries["nec_checkpoint_cpu_observation.json"]
    for record in (terminal, metrics, checkpoint):
        assert record["owner"] == OWNER and record["returncode"] == 0
    assert terminal["observation"]["source"] == COMMIT
    run = metrics["observation"]["runs"]
    assert len(run) == 1
    scalars = run[0]["validation_scalars"]["val/mIOU"]
    assert [z["step"] for z in scalars] == list(range(1, 24))
    values = [z["value"] for z in scalars]
    best = max(values)
    best_epoch = values.index(best) + 1
    assert best == 0.49454113841056824 and best_epoch == 13
    assert values[-1] == 0.48924651741981506 and all(v < best for v in values[13:])
    assert any("Early stopping at epoch 23: no improvement for 10 epochs" in x
               for x in terminal["observation"]["log"]["terminal_lines"])
    cpu = checkpoint["observation"]
    assert cpu["torch_cuda_initialized"] is False and cpu["GPU_computation"] is False
    assert cpu["signals_sent"] is False and cpu["mutations"] is False
    rows = {Path(z["path"]).name: z for z in cpu["rows"]}
    assert rows["best.pth"]["native_meta"] == {"epoch": 13, "best_miou": best, "epochs_no_improve": 0}
    assert rows["last.pth"]["native_meta"] == {"epoch": 22, "best_miou": best, "epochs_no_improve": 9}
    return {"status": "done_earlystop", "best_miou": best, "best_epoch": best_epoch,
            "last_validation_miou": values[-1], "terminal_epoch": 23, "no_improve": 10,
            "completed_validation_count": 23, "validation_values": values,
            "best_checkpoint": rows["best.pth"], "last_checkpoint": rows["last.pth"],
            "native_log_observation": rows["20261104_230851.log"],
            "event_file_observation": next(z for n, z in rows.items() if n.startswith("events.out.")),
            "checkpoint_note": "Native early-stop break precedes save; actual CPU meta confirms last epoch22/no-improve9.",
            "evidence": [ref(HERE / name) for name in EXPECTED]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP", "experiment": ID}))
        return
    guard()
    sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
    import pipeline_monitor as mon
    lock = mon.acquire_lock(str(ROOT))
    assert lock is not None, "Monitor lock busy; no mutation"
    try:
        guard()
        intent = HERE / "nec_terminal_correction_intent.json"
        assert not intent.exists(), "Prior correction intent exists: reconcile, never replay"
        actual = facts()
        protected_before = protected()
        experiment_path = P / "experiments" / (ID + ".json")
        exp_bytes = experiment_path.read_bytes()
        old_exp = json.loads(exp_bytes)
        assert old_exp["id"] == ID and old_exp["archive_id"] == ARCHIVE
        assert old_exp["status"] == "done_earlystop" and old_exp["code_commit"] == COMMIT
        assert old_exp["launch_verified"] is True
        queue = rd(P / "queue.json")
        assert not any(t.get("id") == ID and t.get("status") in ("running", "claiming", "waiting")
                       for group in queue["gpu_queues"].values() for t in group)
        assert ID not in rd(P / "running.json").get("server-4", {}).values()
        csv_path = P / "experiments.csv"
        csv_before = csv_path.read_bytes()
        lines = csv_before.splitlines(keepends=True)
        header = next(csv.reader([lines[0].decode("utf-8-sig")]))
        id_column = header.index("id")
        matches = []
        for i, line in enumerate(lines[1:], 1):
            cells = next(csv.reader([line.decode("utf-8")]))
            if cells and cells[id_column] == ID:
                matches.append((i, cells))
        assert len(matches) == 1
        row_index, row = matches[0]
        new_row = list(row)
        new_row[header.index("best_miou")] = repr(actual["best_miou"])
        ending = "\r\n" if lines[row_index].endswith(b"\r\n") else "\n"
        out = io.StringIO(newline="")
        csv.writer(out, lineterminator=ending).writerow(new_row)
        new_lines = list(lines)
        new_lines[row_index] = out.getvalue().encode("utf-8")
        assert all(a == b for i, (a, b) in enumerate(zip(lines, new_lines)) if i != row_index)
        work_path = P / "research_work.json"
        work_bytes = work_path.read_bytes()
        old_work = json.loads(work_bytes)
        old_candidates = {c["id"]: digest(c) for c in old_work["candidates"]}
        work = copy.deepcopy(old_work)
        c = next(c for c in work["candidates"] if c["id"] == CID and c["experiment_id"] == ID)
        assert c["stage"] == "training" and c["code_commit"] == COMMIT
        new_exp = copy.deepcopy(old_exp)
        new_exp["final_best"] = repr(actual["best_miou"])
        new_exp["training_status"] = "done_earlystop"
        new_exp["native_terminal_metrics"] = actual
        new_exp["terminal_metric_correction"] = {
            "recorded_at": datetime.now(timezone.utc).isoformat(), "owner_token": OWNER["token"],
            "previous_final_best": old_exp.get("final_best"), "previous_training_status": old_exp.get("training_status"),
            "previous_experiment_sha256": sha(exp_bytes), "previous_csv_row": row,
            "reason": "Replace rounded generic stdout summary with actual native scalar and CPU checkpoint evidence.",
            "log_local_note": "Existing local log field retained; no local full log path is fabricated."}
        assert all(new_exp[k] == value for k, value in old_exp.items()
                   if k not in ("final_best", "training_status"))
        new_exp_bytes = json_bytes(new_exp)
        c.update(stage="complete", training_status="done_earlystop",
                 terminal_status="done_earlystop", terminal_epoch=23,
                 final_best_miou=actual["best_miou"], last_validation_miou=actual["last_validation_miou"],
                 terminal_archive_id=ARCHIVE,
                 terminal_experiment={"path": "pipeline/experiments/M228-NEC.json", "sha256": sha(new_exp_bytes)},
                 current_live_observation=actual,
                 next_action="Preserve exact natural early-stop result below champion M95. No automatic resume/revision or hypothesis-wide falsification; retain all independent experiment holds.")
        for entry in actual["evidence"]:
            if entry not in c.setdefault("evidence", []):
                c["evidence"].append(entry)
        work["updated_at"] = datetime.now(timezone.utc).isoformat()
        assert all(digest(z) == old_candidates[z["id"]] for z in work["candidates"] if z["id"] != CID)
        exclusive_json(intent, {"owner": OWNER, "helper_sha256": sha(Path(__file__).read_bytes()),
                               "experiment_before": old_exp, "experiment_before_hex": exp_bytes.hex(),
                               "csv_target_before_hex": lines[row_index].hex(),
                               "candidate_before": next(z for z in old_work["candidates"] if z["id"] == CID),
                               "work_before_sha256": sha(work_bytes), "csv_before_sha256": sha(csv_before),
                               "protected_before": protected_before, "actual": actual})
        guard()
        assert experiment_path.read_bytes() == exp_bytes and csv_path.read_bytes() == csv_before
        assert work_path.read_bytes() == work_bytes and protected() == protected_before
        replace_bytes(experiment_path, new_exp_bytes)
        replace_bytes(csv_path, b"".join(new_lines))
        replace_bytes(work_path, json_bytes(work))
        assert protected() == protected_before
        assert rd(experiment_path)["archive_id"] == ARCHIVE
        after_lines = csv_path.read_bytes().splitlines(keepends=True)
        assert len(after_lines) == len(lines)
        assert all(a == b for i, (a, b) in enumerate(zip(lines, after_lines)) if i != row_index)
        exclusive_json(HERE / "nec_terminal_precise_correction.json",
                       {"owner": OWNER, "recorded_at": datetime.now(timezone.utc).isoformat(),
                        "experiment": ref(experiment_path), "csv": ref(csv_path), "work": ref(work_path),
                        "canonical_archive_identity_and_unrelated_bytes_preserved": True,
                        "exact_result": actual, "intent": ref(intent), "checkpoint_or_source_modified": False})
        print(json.dumps({"status": "NEC_PRECISE_TERMINAL_CORRECTED", "archive_id": ARCHIVE,
                          "best_miou": actual["best_miou"], "terminal_epoch": 23,
                          "evidence": str(HERE / "nec_terminal_precise_correction.json")}))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
