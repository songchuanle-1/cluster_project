"""Repair the verified M193 log archive without changing experiment status."""
import csv
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil

ROOT = Path("D:/project/cluster_project")
PIPE = ROOT / "pipeline"
EXP = "M193-CTF-HCG-CSORT-MQHC-TR"
EXPECTED = "1dd701c5715610a95e41ee6d60a96ede3a0ab2d2e2d2b9aa580c50583d8a079e"
source = PIPE / "reports/tick_evidence_20260913-2110/M193.log"
archive = ROOT / ("Checkpoints/server-4/"
                  "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqhc_tr/"
                  "20260913_020753/20260913_020753.log")
assert hashlib.sha256(source.read_bytes()).hexdigest() == EXPECTED
spec = importlib.util.spec_from_file_location(
    "pipeline_monitor", "D:/project/.claude/skills/songcl_research_pipeline/pipeline_monitor.py")
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)
lock = monitor.acquire_lock(str(ROOT))
assert lock is not None, "Pipeline busy; no changes made"
try:
    queue = json.loads((PIPE / "queue.json").read_text(encoding="utf-8"))
    task = [t for tasks in queue["gpu_queues"].values() for t in tasks if t["id"] == EXP]
    assert len(task) <= 1
    assert not task or task[0]["status"] == "done_earlystop"
    running = json.loads((PIPE / "running.json").read_text(encoding="utf-8"))
    assert EXP not in json.dumps(running), "Experiment remains active"
    ledger = PIPE / "experiments.csv"
    reader = csv.DictReader(io.StringIO(ledger.read_text(encoding="utf-8")))
    fields = reader.fieldnames
    rows = list(reader)
    matches = [r for r in rows if r["id"] == EXP]
    assert len(matches) == 1 and matches[0]["state"] == "done_earlystop"
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        assert hashlib.sha256(archive.read_bytes()).hexdigest() == EXPECTED
    else:
        shutil.copyfile(source, archive)
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == EXPECTED
    matches[0]["log_local"] = str(archive)
    temp = ledger.with_suffix(".csv.m193.tmp")
    with temp.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temp, ledger)
    print(json.dumps({"id": EXP, "archive": str(archive), "sha256": EXPECTED,
                      "status_changed": False, "rows": len(rows)}, indent=2))
finally:
    lock.close()
