"""Correct two fallback classifications using exact, hash-verified trainer logs."""
import csv
from datetime import datetime
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path("D:/project/cluster_project")
SPECS = (
    ("M178-CTF-HCG-CSORT-MQTD", "server-4", "mqtd", "20260908_180933", 34, 24, 10.178109868),
    ("M175-CTF-HCG-CSORT-MQHF", "server-6", "mqhf", "20260907_015059", 27, 17, 11.175240108),
)


def main():
    spec = importlib.util.spec_from_file_location(
        "terminal_monitor", ROOT.parent / ".claude/skills/songcl_research_pipeline/pipeline_monitor.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    lock = m.acquire_lock(str(ROOT))
    if lock is None:
        raise RuntimeError("Pipeline lock busy")
    try:
        servers = m.load_servers(str(ROOT))
        ledger_path = ROOT / "pipeline/experiments.csv"
        ledger_before = ledger_path.read_bytes()
        rows = list(csv.DictReader(io.StringIO(ledger_before.decode("utf-8"))))
        ownership = m.load_running(str(ROOT))
        facts = []
        for eid, server, suffix, stamp, count, best_epoch, flops in SPECS:
            srv = servers[server]
            name = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_" + suffix
            remote = f"{srv['work_dir']}/{name}/{stamp}/{stamp}.log"
            local = ROOT / "Checkpoints" / server / name / stamp / f"{stamp}.log"
            raw = local.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                   f"{srv['user']}@{srv['host']}"]
            remote_digest = subprocess.check_output(
                ssh + [f"sha256sum '{remote}'"], text=True, timeout=20).split()[0]
            assert digest == remote_digest
            processes = m.find_running_processes(srv["host"], srv["user"], srv["remote_code_root"])
            assert not any(Path(c).stem == name for c in processes)
            text = raw.decode("utf-8")
            vals, epoch = [], None
            for line in text.splitlines():
                training = re.search(r"Epoch \[(\d+)/50\]", line)
                if training:
                    epoch = int(training[1])
                exact = re.search(r"\bmIoU : ([0-9.]+)", line)
                if exact:
                    vals.append(dict(epoch=epoch, miou=float(exact[1]),
                                     remote_time=line.split(" - ")[0]))
                elif vals:
                    acc = re.search(r"\bmIOU:.*?\bAcc_50: ([0-9.]+)", line)
                    spm = re.search(r"\bspmIOU: ([0-9.]+)", line)
                    if acc:
                        vals[-1]["acc50"] = float(acc[1].rstrip("."))
                    if spm:
                        vals[-1]["spmiou"] = float(spm[1].rstrip("."))
            assert [v["epoch"] for v in vals] == list(range(1, count + 1))
            best = max(vals, key=lambda x: x["miou"])
            assert best["epoch"] == best_epoch and count - best_epoch == 10
            assert text.rstrip().endswith(
                f"Early stopping at epoch {count}: no improvement for 10 epochs (best={best['miou']:.4f})")
            exp = m.load_experiment(str(ROOT), eid)
            matched = [r for r in rows if r["id"] == eid]
            assert len(matched) == 1
            row = matched[0]
            assert exp["status"] in ("stopped_unknown", "done_earlystop")
            analysis = ROOT / f"pipeline/analyses/{eid}_done_earlystop_20260910-075300.md"
            if exp["status"] != "done_earlystop":
                exp.setdefault("history", []).append({
                    "ts": datetime.now().isoformat(), "action": "terminal_evidence_corrected",
                    "previous_state": exp["status"], "previous_ledger_row": dict(row),
                    "decision": "20260910-075236_other.md"})
            exp.update(status="done_earlystop", log_local=str(local),
                       best_miou_exact=best["miou"], best_epoch=best_epoch,
                       best_acc50=best["acc50"], best_spmiou=best["spmiou"],
                       ended_at_remote=text.splitlines()[-1].split(" - ")[0],
                       validations_completed=count, no_improve_final=10,
                       measured_flops_g=flops, resource_eligible=False, log_sha256=digest,
                       analysis=str(analysis))
            row.update(state="done_earlystop", gpu=str(exp["gpu"]), log_local=str(local))
            slots = ownership.get(server, {})
            for gpu, owner in list(slots.items()):
                if owner == eid:
                    del slots[gpu]
                elif isinstance(owner, list) and eid in owner:
                    slots[gpu] = [x for x in owner if x != eid]
                    if not slots[gpu]:
                        del slots[gpu]
            if not slots:
                ownership.pop(server, None)
            start = text.splitlines()[0].split(" - ")[0]
            end = exp["ended_at_remote"]
            duration = datetime.strptime(end, "%Y-%m-%d %H:%M:%S,%f") - datetime.strptime(start, "%Y-%m-%d %H:%M:%S,%f")
            analysis.write_text(f"""================================================================================
  Experiment Result Analysis - cluster_project
  Experiment: {eid} | State: done_earlystop
================================================================================

## 1. Basic Info
- ID: {eid}
- Config: {exp['config']}
- Server: {server} | GPU: {exp['gpu']}
- Launch (local): {exp['launched']}; logger start/end: {start} / {end}.
- Duration in logger clock: {duration}. Server-6 uses UTC with clock offset;
  server-4 uses local clock. Do not mix clocks.
- Original fallback reconciliation time retained: {exp['finished_at']}.
- State corrected from stopped_unknown using explicit normal-stop evidence;
  original history and previous ledger row retained. No duplicate CSV row.
- Source: {local.relative_to(ROOT).as_posix()}
- SHA256 verified remote/local: {digest}.

## 2. Best Metrics
| Metric | Value | @ Epoch |
|--------|-------|---------|
| mIoU | {best['miou']} | {best_epoch} |
| Acc@50 | {best['acc50']} | {best_epoch} |
| spmIOU | {best['spmiou']} | {best_epoch} |
Acc@50/spmIOU are rounded values paired at the exact best-mIoU epoch.
Startup FLOPs={flops}G exceeds10G; resource-ineligible.

## 3. Convergence Summary
- Verified actual epoch sequence1..{count}, one logger, no concatenated streams.
- Best first at{best_epoch}; ten real post-best validations through{count}.
- Final mIoU={vals[-1]['miou']}, paired Acc50={vals[-1]['acc50']}/spm={vals[-1]['spmiou']}.
- Trainer explicitly reports early stop with patience10; no crash evidence.

## 4. Comparison
- vs baseline .4894: {best['miou'] - .4894:+.10f}.
- vs M95 champion .5020: {best['miou'] - .5020:+.10f}.
- vs M169 .5000: {best['miou'] - .5000:+.10f}; M169 has partial-patience bias.
- Single-seed comparisons descriptive, not statistical or causal proof.

## 5. Conclusion
- Above baseline but below champion and resource-ineligible.
- This recurrent hierarchy retrieval did not improve the champion; no score,
  coefficient or depth tuning. Keep independent terminal-readout tests.
- Preserve checkpoint and evidence; no automatic rerun or model hot edit.

## 6. Crash Info (if crashed)
- No crash; model repair attempts0. Fallback metadata corrected under lock.
- Decision:20260910-075236_other.md. Previous finished_at/launch preserved.
================================================================================
""", encoding="utf-8")
            m.save_experiment(str(ROOT), exp)
            facts.append(dict(id=eid, best=best, final=vals[-1], log_sha256=digest,
                              ended_at_remote=end, analysis=str(analysis)))
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        if any(r["state"] == "stopped_unknown" for r in csv.DictReader(
                io.StringIO(ledger_before.decode("utf-8"))) if r["id"] in [s[0] for s in SPECS]):
            backup = ROOT / "pipeline/reports/ledger_before_terminal_correction_20260910.csv"
            if not backup.exists():
                backup.write_bytes(ledger_before)
            temp = ledger_path.with_suffix(".csv.tmp")
            temp.write_text(output.getvalue(), encoding="utf-8", newline="")
            os.replace(temp, ledger_path)
        m.save_running(str(ROOT), ownership)
        print(json.dumps(facts, indent=2))
        assert ownership == {"server-4": {"1": "M183-CTF-HCG-CSORT-HQI"}}
    finally:
        lock.close()


if __name__ == "__main__":
    main()
