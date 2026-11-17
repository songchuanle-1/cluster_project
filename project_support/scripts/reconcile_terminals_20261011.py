"""Archive exact native logs and reconcile only PDC/BEI under the owned lease."""
import csv
from datetime import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path("C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
sys.path.insert(0, str(SKILL))
import foreground_tick as fg
import pipeline_monitor as monitor

TOKEN = "b395a8b5064a4b6a810cc2285c82c890"
REMOTE = "/data3/songcl/Project/Cluster_project/Cluster_checkpoints"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "songcl@100.64.3.28"]
SPECS = [("M198-PDC", "pdc", "20261009_015852"),
         ("M199-BEI", "bei", "20261009_024904")]


def main():
    owner = fg.load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None, "Pipeline lock busy"
    try:
        ledger = ROOT / "pipeline/experiments.csv"
        original = ledger.read_bytes()
        rows = list(csv.DictReader(io.StringIO(original.decode("utf-8"))))
        fields = list(rows[0])
        fg.save(ROOT / "pipeline/reports/terminal_ledger_before_20261011.json",
                [r for r in rows if r["id"] in {s[0] for s in SPECS}])
        running = monitor.load_running(str(ROOT))
        queue = monitor.load_queue(str(ROOT))
        facts = []
        for eid, suffix, stamp in SPECS:
            exp = monitor.load_experiment(str(ROOT), eid)
            assert exp["server"] == "server-6" and str(exp["gpu"]) == "7"
            name = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_" + suffix
            remote = f"{REMOTE}/{name}/{stamp}/{stamp}.log"
            local = ROOT / f"Checkpoints/server-6/{name}/{stamp}/{stamp}.log"
            local.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["scp", "-q", "-o", "BatchMode=yes",
                            f"songcl@100.64.3.28:{remote}", str(local)],
                           check=True, timeout=60)
            digest = hashlib.sha256(local.read_bytes()).hexdigest()
            remote_digest = subprocess.check_output(SSH + [f"sha256sum '{remote}'"],
                                                   text=True, timeout=20).split()[0]
            assert digest == remote_digest
            process = subprocess.run(SSH + [f"test ! -e /proc/{exp['pid']}"],
                                     timeout=20)
            assert process.returncode == 0, "Recorded training PID remains alive"
            vals, epoch = [], None
            text = local.read_text(encoding="utf-8")
            for line in text.splitlines():
                train = re.search(r"Epoch \[(\d+)/50\]", line)
                if train:
                    epoch = int(train[1])
                exact = re.search(r"\bmIoU : ([0-9.]+)", line)
                if exact:
                    vals.append({"epoch": epoch, "miou": float(exact[1])})
                elif vals:
                    acc = re.search(r"\bmIOU:.*?\bAcc_50: ([0-9.]+)", line)
                    spm = re.search(r"\bspmIOU: ([0-9.]+)", line)
                    if acc:
                        vals[-1]["acc50"] = float(acc[1].rstrip("."))
                    if spm:
                        vals[-1]["spmiou"] = float(spm[1].rstrip("."))
            terminal = re.search(r"Early stopping at epoch (\d+): no improvement for (\d+) epochs \(best=([0-9.]+)\)$",
                                 text.rstrip())
            assert terminal is not None
            count, patience = int(terminal[1]), int(terminal[2])
            assert [v["epoch"] for v in vals] == list(range(1, count + 1))
            best = max(vals, key=lambda v: v["miou"])
            assert count - best["epoch"] == patience == 10
            assert f"{best['miou']:.4f}" == terminal[3]
            matched = [r for r in rows if r["id"] == eid]
            assert len(matched) <= 1
            previous_row = dict(matched[0]) if matched else None
            exp.setdefault("history", []).append({
                "ts": datetime.now().isoformat(), "action": "terminal_evidence_corrected",
                "previous_state": exp["status"], "previous_final_best": exp.get("final_best"),
                "previous_ledger_row": previous_row, "log_sha256": digest})
            exp.update(status="done_earlystop", final_best=f"{best['miou']:.4f}",
                       best_miou_exact=best["miou"], best_epoch=best["epoch"],
                       best_acc50=best["acc50"], best_spmiou=best["spmiou"],
                       validations_completed=count, no_improve_final=patience,
                       epochs_final=f"{count}/50", log_local=str(local),
                       log_sha256=digest, ended_at_remote=text.splitlines()[-1].split(" - ")[0])
            exp.setdefault("finished_at", datetime.now().isoformat(timespec="seconds"))
            exp["terminal_evidence"] = "pipeline/reports/terminal_facts_20261011.json"
            row = matched[0] if matched else {key: "" for key in fields}
            row.update(finished_at=exp["finished_at"], id=eid, config=exp["config"],
                       server="server-6", gpu="7", state="done_earlystop",
                       best_miou=f"{best['miou']:.4f}", epochs=f"{count}/50",
                       log_local=str(local))
            if not matched:
                rows.append(row)
            for gpu, ids in list(running.get("server-6", {}).items()):
                if ids == eid:
                    del running["server-6"][gpu]
                elif isinstance(ids, list):
                    running["server-6"][gpu] = [i for i in ids if i != eid]
                    if not running["server-6"][gpu]:
                        del running["server-6"][gpu]
            if "server-6" in running and not running["server-6"]:
                del running["server-6"]
            if queue and queue.get("gpu_queues", {}).get("server-6"):
                queue["gpu_queues"]["server-6"] = [
                    t for t in queue["gpu_queues"]["server-6"] if t.get("id") != eid]
            monitor.save_experiment(str(ROOT), exp)
            facts.append({"id": eid, "best": best, "final": vals[-1],
                          "validations": count, "patience": patience,
                          "log_path": local.relative_to(ROOT).as_posix(),
                          "log_sha256": digest, "ended_at_remote": exp["ended_at_remote"],
                          "previous_state": exp["history"][-1]["previous_state"],
                          "observed_at": datetime.now().astimezone().isoformat()})
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        temp = ledger.with_suffix(".csv.tmp")
        temp.write_text(output.getvalue(), encoding="utf-8", newline="")
        os.replace(temp, ledger)
        monitor.save_running(str(ROOT), running)
        if queue:
            monitor.save_queue(str(ROOT), queue)
        fg.save(ROOT / "pipeline/reports/terminal_facts_20261011.json", facts)
        print(json.dumps({"facts": facts, "remaining_running": running}, indent=2))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
