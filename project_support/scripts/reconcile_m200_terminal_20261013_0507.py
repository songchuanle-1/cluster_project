"""Reconcile M200 only after exact native early-stop and absent-PID evidence."""
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

TOKEN = "f3d67c69338443d28eee4349fd8576ab"
EID = "M200-TMR"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "songcl@100.64.3.28"]
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_tmr"
STAMP = "20261012_010313"
REMOTE = f"/data3/songcl/Project/Cluster_project/Cluster_checkpoints/{NAME}/{STAMP}/{STAMP}.log"


def main():
    owner = fg.load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None, "Project pipeline lock busy"
    try:
        exp = monitor.load_experiment(str(ROOT), EID)
        assert exp["server"] == "server-6" and str(exp["gpu"]) == "7"
        assert exp["status"] == "running" and exp["pid"] == 3639592
        local = ROOT / f"Checkpoints/server-6/{NAME}/{STAMP}/{STAMP}.log"
        assert not local.exists()
        local.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["scp", "-q", "-o", "BatchMode=yes",
                        f"songcl@100.64.3.28:{REMOTE}", str(local)], check=True, timeout=60)
        digest = hashlib.sha256(local.read_bytes()).hexdigest()
        assert subprocess.check_output(SSH + [f"sha256sum '{REMOTE}'"],
                                       text=True, timeout=20).split()[0] == digest
        subprocess.run(SSH + [f"test ! -e /proc/{exp['pid']}"], check=True, timeout=20)
        text = local.read_text(encoding="utf-8")
        values, epoch = [], None
        for line in text.splitlines():
            match = re.search(r"Epoch \[(\d+)/50\]", line)
            if match:
                epoch = int(match[1])
            match = re.search(r"\bmIoU : ([0-9.]+)", line)
            if match:
                values.append({"epoch": epoch, "miou": float(match[1])})
            elif values:
                match = re.search(r"\bmIOU:.*?\bAcc_50: ([0-9.]+)", line)
                if match:
                    values[-1]["acc50"] = float(match[1].rstrip("."))
                match = re.search(r"\bspmIOU: ([0-9.]+)", line)
                if match:
                    values[-1]["spmiou"] = float(match[1].rstrip("."))
        terminal = re.search(r"Early stopping at epoch (\d+): no improvement for (\d+) epochs \(best=([0-9.]+)\)$",
                             text.rstrip())
        assert terminal is not None and int(terminal[1]) == 23 and int(terminal[2]) == 10
        assert [v["epoch"] for v in values] == list(range(1, 24))
        best = max(values, key=lambda v: v["miou"])
        assert 23 - best["epoch"] == 10
        assert f"{best['miou']:.4f}" == terminal[3]
        before = ROOT / "pipeline/reports/m200_terminal_before_20261013_0507.json"
        assert not before.exists()
        ledger = ROOT / "pipeline/experiments.csv"
        rows = list(csv.DictReader(io.StringIO(ledger.read_text(encoding="utf-8"))))
        matched = [r for r in rows if r["id"] == EID]
        assert len(matched) <= 1
        fg.save(before, {"experiment": exp, "ledger_rows": matched})
        facts = {
            "id": EID, "observed_at_local": datetime.now().astimezone().isoformat(),
            "observed_at_remote": subprocess.check_output(SSH + ["date --iso-8601=seconds"],
                                                          text=True, timeout=20).strip(),
            "pid_absent": exp["pid"], "state": "done_earlystop", "validations": 23,
            "patience": 10, "best": best, "last": values[-1], "values": values,
            "remote_log": REMOTE, "log_path": local.relative_to(ROOT).as_posix(),
            "log_sha256": digest, "terminal_line": text.splitlines()[-1],
            "baseline": 0.4894, "champion": 0.5020,
            "baseline_delta": best["miou"] - 0.4894,
            "champion_delta": best["miou"] - 0.5020,
            "scope": "Single native seed1999 screen; no scene-clustered uncertainty or subgroup-harm claim."
        }
        output = ROOT / "pipeline/reports/m200_terminal_facts_20261013_0507.json"
        assert not output.exists()
        fg.save(output, facts)
        exp.setdefault("history", []).append({
            "ts": datetime.now().isoformat(), "action": "native_terminal_verified",
            "previous_status": "running", "log_sha256": digest,
            "terminal_evidence": output.relative_to(ROOT).as_posix()
        })
        exp.update(status="done_earlystop", final_best=f"{best['miou']:.4f}",
                   best_miou_exact=best["miou"], best_epoch=best["epoch"],
                   best_acc50=best["acc50"], best_spmiou=best["spmiou"],
                   validations_completed=23, no_improve_final=10, epochs_final="23/50",
                   log_local=str(local), log_sha256=digest,
                   finished_at=datetime.now().isoformat(timespec="seconds"),
                   terminal_evidence=output.relative_to(ROOT).as_posix())
        monitor.save_experiment(str(ROOT), exp)
        if matched:
            matched[0].update(state="done_earlystop", best_miou=exp["final_best"],
                              epochs="23/50", log_local=str(local),
                              finished_at=exp["finished_at"])
            target = io.StringIO(newline="")
            writer = csv.DictWriter(target, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
            temp = ledger.with_suffix(".csv.tmp")
            temp.write_text(target.getvalue(), encoding="utf-8", newline="")
            os.replace(temp, ledger)
        else:
            monitor.ledger_append(str(ROOT), finished_at=exp["finished_at"], id=EID,
                                  config=exp["config"], server="server-6", gpu="7",
                                  state="done_earlystop", best_miou=exp["final_best"],
                                  epochs="23/50", log_local=str(local))
        running, queue = monitor.load_running(str(ROOT)), monitor.load_queue(str(ROOT))
        for gpu, ids in list(running.get("server-6", {}).items()):
            if ids == EID:
                del running["server-6"][gpu]
            elif isinstance(ids, list):
                running["server-6"][gpu] = [i for i in ids if i != EID]
                if not running["server-6"][gpu]:
                    del running["server-6"][gpu]
        if "server-6" in running and not running["server-6"]:
            del running["server-6"]
        monitor.save_running(str(ROOT), running)
        if queue and queue.get("gpu_queues", {}).get("server-6"):
            queue["gpu_queues"]["server-6"] = [t for t in queue["gpu_queues"]["server-6"]
                                              if t.get("id") != EID]
            monitor.save_queue(str(ROOT), queue)
        print(json.dumps({k: v for k, v in facts.items() if k != "values"}, indent=2))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
