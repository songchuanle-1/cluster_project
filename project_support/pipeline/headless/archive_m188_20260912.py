"""Verify and backfill M188 log evidence without repeating its transition."""
import csv
from datetime import datetime
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path

from close_m185_20260912 import parse_log, run

ROOT = Path("D:/project/cluster_project")
PIPE = ROOT / "pipeline"
SKILL = ROOT.parent / ".claude/skills/songcl_research_pipeline"
EID = "M188-CTF-HCG-CSORT-MQB-TR"
STAMP = "20260912-181200"
LOG = ROOT / ("Checkpoints/server-4/"
              "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mqb_tr/"
              "20260911_031407/20260911_031407.log")
SHA = "92790e62ccd35df7fee0310ac8b5c179a7623df29fd64da27df0fe0c445ea0bc"
ANALYSIS = PIPE / f"analyses/{EID}_done_earlystop_{STAMP}.md"
EVIDENCE = PIPE / f"reports/m188_archive_audit_{STAMP}.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    os.environ["PROJECT_ROOT"] = "D:/project"
    spec = importlib.util.spec_from_file_location("monitor_archive", SKILL / "pipeline_monitor.py")
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    assert digest(LOG) == SHA
    text = LOG.read_text(encoding="utf-8")
    rows = parse_log(text)
    assert [r["epoch"] for r in rows] == list(range(1, 24))
    assert all(set(r) == {"epoch", "miou", "acc50", "spmiou"} for r in rows)
    best = max(rows, key=lambda r: r["miou"])
    assert best == dict(epoch=13, miou=0.49161195755004883, acc50=0.544, spmiou=0.457)
    assert all(r["miou"] < best["miou"] for r in rows[13:])
    assert text.rstrip().endswith(
        "Early stopping at epoch 23: no improvement for 10 epochs (best=0.4916)")
    assert text.count("Evaluate referring segmentation: 9508") == 23
    start = datetime.strptime(text.splitlines()[0].split(" - ")[0], "%Y-%m-%d %H:%M:%S,%f")
    end = datetime.strptime(text.splitlines()[-1].split(" - ")[0], "%Y-%m-%d %H:%M:%S,%f")
    delta_base = best["miou"] - 0.4894491136074066
    delta_champ = best["miou"] - 0.5024607181549072
    analysis = f"""================================================================================
  Experiment Result Analysis - cluster_project
  Experiment: {EID} | State: done_earlystop
================================================================================

## 1. Basic Info
- Config: configs/Quard/ctf_hcg_csort_mqb_tr/{LOG.parent.parent.name}.yaml
- Server: server-4 | GPU: 0 | State: done_earlystop (already archived).
- Logger start: {start}; finish: {end}; duration: {end - start}.
  Server-4 clock verified +08:00. Registry launch 2026-09-11 03:14:09 and
  terminal detection 2026-09-12 04:08:31 are operational timestamps.
- Archive: {LOG.relative_to(ROOT).as_posix()}
- Remote/local SHA256: {SHA}
- This evidence supplement supersedes rounded metrics and approximate final
  mIoU in the earlier M188 analysis; historical documents remain intact.

## 2. Best Metrics
| Metric | Value | @ Epoch |
|--------|-------|---------|
| mIoU | {best['miou']} | 13 |
| Acc@50 | 0.544 | 13 |
| spmIOU | 0.457 | 13 |

## 3. Convergence Summary
- 23 contiguous validations, each evaluating 9508 expressions.
- Best first reached at epoch 13; all ten later validations failed to improve.
- Final epoch 23: mIoU {rows[-1]['miou']}, Acc@50 0.538, spmIOU 0.448.
- Initial improvement then fluctuating plateau. Explicit normal early stop;
  no retry, new transition, or checkpoint transfer.

## 4. Comparison
- Baseline model_base1 0.4894491136074066: delta {delta_base:+.10f}.
- Champion M95 0.5024607181549072: delta {delta_champ:+.10f}.
- Target 0.5100: gap {0.51 - best['miou']:.10f}.
- Parent M169 has ledger 0.5000 (rounded): descriptive delta about -0.0084.
  Parent raw precision and paired scene predictions are not verified here.
- M186 0.49449968338012695 is a different topology, not a matched control.

## 5. Conclusion
- Positive vs baseline, failed vs champion in this single-seed legacy run.
- Removing intermediate feedback under this configuration does not retain
  champion-level performance; this is not proof about all recurrence.
- Keep this variant closed without successor. Exact-log recovery does not
  supply a novel mechanism or independently confirm a causal claim.
- The M184-M188 synthesis remains 0/5 above M95; 4/5 parents never trained.
  All five child logs are now locally hash-verifiable. No pooled significance
  estimate is justified across different architectures.

## 6. Crash Info
- Not crashed. Model repair attempts: 0. No training or deployment edits.
================================================================================
"""
    lock = monitor.acquire_lock(str(ROOT))
    if lock is None:
        raise RuntimeError("Active pipeline writer; refusing metadata update")
    try:
        protected = {name: digest(PIPE / name) for name in ("queue.json", "running.json", "goal.json")}
        exp = monitor.load_experiment(str(ROOT), EID)
        assert exp["status"] == "done_earlystop" and exp["epochs_final"] == "23/50"
        old_history = list(exp["history"])
        with (PIPE / "experiments.csv").open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            fields = reader.fieldnames
            ledger = list(reader)
        matches = [r for r in ledger if r["id"] == EID]
        assert len(matches) == 1 and matches[0]["best_miou"] == "0.4916"
        print(run([
            monitor.bash_executable(), str(SKILL / "log_decision.sh"),
            "cluster_project", "other",
            "Can the missing M188 raw log be recovered without repeating its terminal transition?",
            "Archive verified M188 log; supplement exact metrics and log_local only; preserve state, history and FIFO.",
            "Matching remote/local SHA256;23 contiguous 9508-expression validations;best .49161195755004883 at13;normal stop23.",
            str(ANALYSIS),
        ]))
        ANALYSIS.write_text(analysis, encoding="utf-8")
        if not any(h.get("action") == "log_archive_backfill" for h in old_history):
            exp["history"].append({"ts": datetime.now().isoformat(), "action": "log_archive_backfill",
                                   "log_sha256": SHA, "analysis": str(ANALYSIS)})
        exp.update(log_local=str(LOG), log_sha256=SHA, best_miou_exact=best["miou"],
                   best_epoch=13, best_acc50=0.544, best_spmiou=0.457,
                   validations_completed=23, no_improve_final=10,
                   ended_at_remote=str(end), analysis=str(ANALYSIS))
        monitor.save_experiment(str(ROOT), exp)
        matches[0]["log_local"] = str(LOG)
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(ledger)
        (PIPE / "experiments.csv").write_bytes(output.getvalue().encode("utf-8"))
        assert exp["history"][:len(old_history)] == old_history
        assert all(digest(PIPE / name) == value for name, value in protected.items())
        assert len(ledger) == 226
        corpus = []
        for path in sorted((PIPE / "analyses").glob("*.md")):
            content = path.read_text(encoding="utf-8")
            corpus.append(dict(path=path.relative_to(ROOT).as_posix(), sha256=digest(path),
                               chars=len(content)))
        prior = json.loads((PIPE / "reports/terminal_control_synthesis_20260912-171503.json").read_text())
        terminals = prior["terminal"]
        for item in terminals:
            if item["id"] == EID:
                item.update(best=best["miou"], precision="exact", log_verified=True,
                            analysis=ANALYSIS.relative_to(ROOT).as_posix(),
                            analysis_sha256=digest(ANALYSIS),
                            delta_baseline=delta_base, delta_champion=delta_champ)
            record = monitor.load_experiment(str(ROOT), item["id"])
            assert digest(Path(record["log_local"])) == record["log_sha256"]
        evidence = dict(verified_at=datetime.now().isoformat(), best=best, validations=rows,
                        log_sha256=SHA, protected_state=protected, terminal=terminals,
                        ledger_rows=len(ledger), analyses=corpus)
        EVIDENCE.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(json.dumps({k: v for k, v in evidence.items() if k not in ("analyses", "validations", "terminal")}, indent=2))
    finally:
        lock.close()


if __name__ == "__main__":
    main()
