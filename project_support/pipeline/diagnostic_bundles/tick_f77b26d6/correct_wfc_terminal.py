from pathlib import Path
from datetime import datetime, timezone
import base64
import copy
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
HERE = Path(__file__).resolve().parent
TOKEN = "f77b26d64ead4c52bd429009cc78827b"
ID = "M226-WFC"
ARCHIVE = "ead6b5a9edf2466ea96e2587c931c865"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


EXPECTED = load(HERE / "reader_provenance.json")["owner"]


def guard():
    owner = load(P / "headless/.foreground.lockdir/owner.json")
    assert EXPECTED["token"] == TOKEN
    assert {k: owner.get(k) for k in EXPECTED} == EXPECTED
    assert os.environ["CODEX_THREAD_ID"] == EXPECTED["thread_id"]
    assert datetime.now(timezone.utc) < datetime.fromisoformat(EXPECTED["deadline_at"])
    assert sha(P / "headless/.tick_context.json") == EXPECTED["context_sha256"]
    assert sha(P / "headless/.tick_context_state.next.json") == EXPECTED["pending_sha256"]


def save(path, value, exclusive=False):
    guard()
    body = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)
    if exclusive:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(body)
        return
    atomic(path, body)


def atomic(path, body):
    guard()
    temp = path.with_name(path.name + ".f77b26d6_correction.tmp")
    with temp.open("xb") as stream:
        stream.write(body if isinstance(body, bytes) else body.encode("utf-8"))
        stream.flush()
        os.fsync(stream.fileno())
    guard()
    os.replace(temp, path)


def main():
    guard()
    sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
    import pipeline_monitor as mon
    lock = mon.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        guard()
        observation = load(HERE / "wfc_terminal_observation.json")
        assert observation["returncode"] == 0 and observation["owner"] == EXPECTED
        x = observation["observation"]
        assert x["original_pid_absent"] and not x["signals_sent"]
        assert not x["new_model_or_backward_executed"]
        assert x["source_commit"] == "94c4fe61b38f46f321a7ee84236fea70ade04d9b"
        peer_path = HERE / "wfc_terminal_independent_review.json"
        assert peer_path.is_file()
        peer = load(peer_path)
        assert peer.get("passed") is True
        native = HERE / "native_logger_terminal_full.log"
        stdout = HERE / "stdout_terminal_full.log"
        assert sha(native) == x["logs"]["native_logger"]["sha256"]
        assert sha(stdout) == x["logs"]["stdout"]["sha256"]
        text = native.read_text(encoding="utf-8")
        vals, best, noimp = mon.parse_native_lineage(text, resumed=True)
        assert len(vals) == 5 and best == 0.49711745977401733 and noimp == 10
        assert vals[-1] == 0.48382365703582764
        assert x["logs"]["native_logger"]["early_stopping"] == [["30", "10", "0.4971"]]
        assert not x["logs"]["native_logger"]["errors"] and not x["logs"]["stdout"]["errors"]
        assert "363/363" in stdout.read_text(encoding="utf-8")[-6000:]
        refs = [ref(HERE / "wfc_terminal_observation.json"), ref(peer_path), ref(native), ref(stdout),
                ref(HERE / "wfc_canonical_reconcile_confirmed.json")]
        exp_path = P / "experiments/M226-WFC.json"
        csv_path = P / "experiments.csv"
        work_path = P / "research_work.json"
        before_exp = load(exp_path)
        assert (before_exp["archive_id"], before_exp["status"], before_exp["final_best"],
                before_exp["epochs_final"], before_exp["log_local"]) == (
                    ARCHIVE, "done_earlystop", "0.4840", "30/50", "")
        before_work = load(work_path)
        work = copy.deepcopy(before_work)
        candidate = next(c for c in work["candidates"] if c.get("experiment_id") == ID)
        assert candidate["stage"] == "training"
        now = datetime.now(timezone.utc).isoformat()
        exp = copy.deepcopy(before_exp)
        exp.update(final_best=format(best, ".4f"), native_final_best=best,
                   training_status="done_earlystop", log_local=str(native),
                   log_local_sha256=sha(native), native_result_evidence=refs)
        exp["history"].append(dict(
            ts=now, action="native_full_log_resumed_result_correction",
            status="done_earlystop", previous_final_best="0.4840", previous_log_local="",
            best_miou_exact=best, best_miou=exp["final_best"], log_local=str(native),
            evidence=refs,
            scope="Preserve canonical archive/history/source/admission/finish. Correct derived metrics using restored best plus exact five resumed validations. No new archive, rerun or process action."))
        raw_csv = csv_path.read_bytes()
        lines = raw_csv.decode("utf-8").splitlines(keepends=True)
        header = next(csv.reader([lines[0]]))
        out, found = [lines[0]], 0
        for line in lines[1:]:
            row = next(csv.reader([line]))
            record = dict(zip(header, row))
            if record.get("id") != ID:
                out.append(line)
                continue
            found += 1
            assert (record["state"], record["best_miou"], record["epochs"], record["log_local"]) == (
                "done_earlystop", "0.4840", "30/50", "")
            record["best_miou"], record["log_local"] = exp["final_best"], str(native)
            stream = io.StringIO(newline="")
            csv.writer(stream, lineterminator="\r\n" if line.endswith("\r\n") else "\n").writerow(
                [record[k] for k in header])
            out.append(stream.getvalue())
        assert found == 1
        new_csv = "".join(out).encode("utf-8")
        candidate.update(
            stage="complete", queued=False, final_best_miou=best,
            terminal_status="done_earlystop", terminal_epoch=30,
            terminal_archive_id=ARCHIVE,
            current_live_observation=dict(
                observed_at=x["observed_at"], status="done_earlystop",
                original_process_present=False, native_resumed_validation_count=5,
                best_miou=best, no_improve=10, epochs_final="30/50",
                original_admitted_source_commit=x["source_commit"], evidence=refs,
                scope="Same experiment naturally early-stopped under original patience10. Below champion; no hypothesis-wide falsification, resume or revision."),
            next_action="Preserve complete original WFC earlystop30 result, source94, original/restored checkpoints and launch/admission history. Champion remains M95 .5020. No automatic restart, migration or successor derived from this result; continue independently prepared authorized candidates.")
        candidate["evidence"].extend(refs)
        work["updated_at"] = now
        fixed = {n: sha(P / n) for n in (
            "queue.json", "running.json", "admissions/M226-WFC.json",
            "experiments/M227-LFT.json", "experiments/M206-CGCA.json")}
        save(HERE / "terminal_result_correction_intent.json", dict(
            owner=EXPECTED, recorded_at=now, before_experiment=before_exp,
            before_experiment_base64=base64.b64encode(exp_path.read_bytes()).decode(),
            before_csv_base64=base64.b64encode(raw_csv).decode(),
            before_work_sha256=sha(work_path), before_candidate=next(
                c for c in before_work["candidates"] if c.get("experiment_id") == ID),
            exact_best=best, no_improve=noimp, terminal_epoch=30, evidence=refs,
            protected_fixed=fixed), True)
        assert load(exp_path) == before_exp and load(work_path) == before_work
        assert csv_path.read_bytes() == raw_csv
        save(exp_path, exp)
        atomic(csv_path, new_csv)
        candidate["terminal_experiment"] = ref(exp_path)
        save(work_path, work)
        analysis = f"""# Experiment Result Analysis — cluster_project

## 1. Basic Info
- ID: M226-WFC; server-4 physical GPU0; source94.
- State: done_earlystop; native epoch30/50. The original resumed process is absent.
- Native stop: 2026-11-04 19:39:40.758 server log time (Asia/Shanghai).
- Canonical archive: {ARCHIVE}; original archive time and history retained.

## 2. Best Metrics
| Metric | Value | Epoch |
|---|---|---|
| mIoU, complete experiment best | {best!r} | Restored history; exact best epoch not re-established here |
| Last validation mIoU | {vals[-1]!r} | 30 |
| Acc@50 at best | Unknown in this resumed log | Unknown |
| spmIoU at best | Unknown in this resumed log | Unknown |

## 3. Convergence Summary
Restored epoch25/best={best!r}/no-improve5; resumed epochs26–30 produced {vals!r}.
No validation exceeded the restored best. The exact lineage reaches no-improve10,
and stdout plus native logger both record the original patience10 stop at epoch30.
The native break precedes checkpoint saving, so last.pth may remain epoch29;
its recorded SHA is evidence of preserved bytes, not a CPU inspection of its body.

## 4. Comparison
Against baseline .4894: {best - .4894:+.10f}. Against champion M95 .5020:
{best - .5020:+.10f}. Target .5100 remains unmet; champion remains unchanged.

## 5. Interpretation
This complete experiment did not improve the champion. This observation does
not establish a hypothesis-wide failure or justify tuning, restart or migration.
Generic archival recorded .4840 from rounded resumed-only stdout and an empty
local-log path; a separate evidence-backed correction retains that original history.

## 6. Next Action
Preserve source, checkpoints, admissions and original pause/resume lineage.
Continue existing independent NEC/MIC candidates under GPU0-only authorization.
Evidence: {refs!r}
"""
        analysis_path = P / "analyses" / f"M226-WFC_done_earlystop_{ARCHIVE}_native.md"
        with analysis_path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(analysis)
        assert {n: sha(P / n) for n in fixed} == fixed
        assert all(a == b for a, b in zip(before_work["candidates"], work["candidates"])
                   if a.get("experiment_id") != ID)
        save(HERE / "terminal_result_correction_result.json", dict(
            owner=EXPECTED, recorded_at=now, archive_id_preserved=ARCHIVE,
            best_miou_exact=best, final_no_improve=noimp, final_epoch=30,
            after_experiment=ref(exp_path), after_csv=ref(csv_path),
            after_work=ref(work_path), analysis=ref(analysis_path),
            only_WFC_candidate_changed=True, other_csv_rows_byte_identical=True,
            queue_running_pauses_admission_preserved=True,
            no_source_process_policy_change=True), True)
        print(json.dumps(dict(status="WFC_TERMINAL_PRECISELY_RECORDED",
                              result=ref(HERE / "terminal_result_correction_result.json")),
                         ensure_ascii=False))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
