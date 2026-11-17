"""One-shot, evidence-gated M187 completion. GPU1 is deliberately not refilled."""
import copy
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess

import yaml

ROOT = Path("D:/project/cluster_project")
SKILL = ROOT.parent / ".claude/skills/songcl_research_pipeline"
BASE = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
OLD = "M187-CTF-HCG-CSORT-MQFC-TR"
HEAD = "05335bdd15d83d106d410e03498b0c38dc9ad414"
DIGEST = "44a7665d7b66d83171ec67713bfae2059acd4eeb5ecaa626ac0c6a73112c04df"
RELLOG = f"{BASE}_mqfc_tr/20260910_131327/20260910_131327.log"
LOG = ROOT / "Checkpoints/server-4" / RELLOG
ANALYSIS = ROOT / "pipeline/analyses/M187-CTF-HCG-CSORT-MQFC-TR_done_earlystop_20260911-211200.md"
EVIDENCE = ROOT / "pipeline/reports/m187_transition_20260911.json"
BEST = 0.49029025435447693


def run(args):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                          errors="strict", check=True, timeout=90).stdout


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    spec = importlib.util.spec_from_file_location("scoped_monitor", SKILL / "pipeline_monitor.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

    def decision(project, kind, question, action, basis="", evidence=""):
        return run([m.bash_executable(), str(SKILL / "log_decision.sh"),
                    "cluster_project", kind, question, action, basis, evidence])

    m.log_decision = decision
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    srv = servers["server-4"]
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
           f"{srv['user']}@{srv['host']}"]
    remote, q = srv["remote_code_root"], shlex.quote
    remote_log = srv["work_dir"] + "/" + RELLOG

    # ---- Evidence: the local archive and the remote file must be the same terminal log.
    assert hashlib.sha256(LOG.read_bytes()).hexdigest() == DIGEST
    assert run(ssh + [f"sha256sum {q(remote_log)}"]).split()[0] == DIGEST
    rows, epoch = [], None
    text = LOG.read_text(encoding="utf-8")
    for line in text.splitlines():
        training = re.search(r"Epoch \[(\d+)/50\]", line)
        if training:
            epoch = int(training[1])
        exact = re.search(r"\bmIoU : ([0-9.]+)", line)
        if exact:
            rows.append(dict(epoch=epoch, miou=float(exact[1])))
        elif rows:
            acc = re.search(r"\bmIOU:.*?Acc_50: ([0-9.]+)", line)
            spm = re.search(r"\bspmIOU: ([0-9.]+)", line)
            if acc:
                rows[-1]["acc50"] = float(acc[1].rstrip("."))
            if spm:
                rows[-1]["spmiou"] = float(spm[1].rstrip("."))
    assert [r["epoch"] for r in rows] == list(range(1, 28))
    best = max(rows, key=lambda r: r["miou"])
    assert best == dict(epoch=17, miou=BEST, acc50=.541, spmiou=.454)
    assert all(r["miou"] < best["miou"] for r in rows[17:])
    assert text.rstrip().endswith(
        "Early stopping at epoch 27: no improvement for 10 epochs (best=0.4903)")
    assert ANALYSIS.is_file()

    lock = m.acquire_lock(str(ROOT))
    if lock is None:
        raise RuntimeError("Another pipeline writer is active")
    try:
        queue = m.load_queue(str(ROOT))
        before = copy.deepcopy(m.load_running(str(ROOT)))
        tasks = {t["id"]: t for group in queue["gpu_queues"].values() for t in group}
        processes = m.find_running_processes(srv["host"], srv["user"], remote)
        # The trainer is gone; the co-tenant on GPU1 is not ours.
        assert not any(Path(c).stem == BASE + "_mqfc_tr" for c in processes)
        assert sorted({str(p[2]) for p in processes.values()}) == ["0"]
        assert before["server-4"] == {"0": "M188-CTF-HCG-CSORT-MQB-TR", "1": OLD}

        # ---- Close M187 as a terminal early stop.
        assert tasks[OLD]["status"] == "running"
        import csv
        ledger = list(csv.DictReader((ROOT / "pipeline/experiments.csv").open(encoding="utf-8-sig")))
        assert not any(r["id"] == OLD for r in ledger)
        original = m.load_experiment(str(ROOT), OLD)
        decision(str(ROOT), "other", "M187 normal early stop verified at27; finalize?",
                 "Archive M187 done_earlystop and release only the registry slot on server-4 GPU1.",
                 "Best.49029025435447693@17;27 contiguous validations;10 stale;PID absent;"
                 "log hash matches remote.",
                 str(ANALYSIS))
        events = []
        m.pull_log = lambda *a: str(LOG)
        m.write_analysis_md = lambda *a: str(ANALYSIS)
        m.finalize_task(str(ROOT), queue, "server-4", srv["host"], srv["user"],
                        tasks[OLD], BASE + "_mqfc_tr", "done_earlystop",
                        best["miou"], "27/50", "1", remote_log, events)
        exp = m.load_experiment(str(ROOT), OLD)
        assert exp["history"][:len(original["history"])] == original["history"]
        exp.update(best_epoch=17, best_acc50=.541, best_spmiou=.454,
                   validations_completed=27, no_improve_final=10, log_sha256=DIGEST,
                   analysis=str(ANALYSIS),
                   terminal_evidence="Explicit trainer marker and contiguous epochs; no kill")
        m.save_experiment(str(ROOT), exp)
        dw = m.load_deathwatch(str(ROOT))
        dw.get("server-4", {}).pop(BASE + "_mqfc_tr", None)
        m.save_deathwatch(str(ROOT), dw)
        after = m.load_running(str(ROOT))
        assert after["server-4"] == {"0": "M188-CTF-HCG-CSORT-MQB-TR"}
        assert OLD not in {t["id"] for t in m.load_queue(str(ROOT))["gpu_queues"]["server-4"]}

        # ---- GPU1 is not strictly idle: an external co-tenant holds ~1GB.
        stats = run(ssh + ["nvidia-smi -i 1 --query-gpu=utilization.gpu,memory.used,memory.total "
                          "--format=csv,noheader,nounits"]).strip()
        util, used, total = (int(x) for x in stats.split(","))
        apps = run(ssh + ["nvidia-smi -i 1 --query-compute-apps=pid,used_memory "
                          "--format=csv,noheader,nounits"]).strip()
        our_pids = {str(p[0]) for p in processes.values()}
        foreign = [a for a in apps.splitlines() if a.strip() and a.split(",")[0].strip() not in our_pids]
        assert foreign, "expected a non-project process on GPU1"
        allowed_free = m.FREE_MEM_MB
        assert util < m.FREE_UTIL and used >= allowed_free
        new_queue = m.load_queue(str(ROOT))
        nxt = next(t for t in new_queue["gpu_queues"]["server-4"] if t["status"] == "waiting")
        assert nxt["id"] == "M189-CTF-HCG-CSORT-MQBC-TR" and not nxt.get("dispatch_hold")
        decision(str(ROOT), "question",
                 f"server-4 GPU1 has no project trainer but a foreign process holds {used}MiB "
                 f"(strict idle needs <{allowed_free}MiB); dispatch waiting FIFO M189-BC-TR?",
                 "Hold M189 in waiting FIFO; do not force overlay on server-4 without an explicit "
                 "allow_external_overlay opt-in. Re-evaluate when GPU1 becomes strictly idle.",
                 "current idle gate is util<%d%% and mem<%dMiB; server-4 has no overlay flag, and the "
                 "co-tenant is another user's job" % (m.FREE_UTIL, m.FREE_MEM_MB),
                 f"nvidia-smi gpu1={stats}; apps={apps}; queue=pipeline/queue.json")
        events.append(f"[{BASE}_mqfc_tr] 终态=done_earlystop Best=.4903 @27/50；GPU1 释放但未补位（外部共占 {used}MiB）")
        evidence = dict(verified_at=datetime.now().isoformat(), terminal=best, validations=rows,
                        log_sha256=DIGEST, gpu1=dict(util=util, used_mb=used, total_mb=total,
                                                     foreign_apps=apps.splitlines()),
                        running=after, events=events)
        EVIDENCE.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        m.daily_report(str(ROOT), events)
        print(json.dumps(evidence, indent=2))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
