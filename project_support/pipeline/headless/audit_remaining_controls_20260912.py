"""Audit preserved parent/child comparisons without changing training state."""
import csv
from datetime import datetime
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

from close_m185_20260912 import parse_log

ROOT = Path("D:/project/cluster_project")
PIPE = ROOT / "pipeline"
BASE = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
STAMP = "20260912-191500"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protected = {p.name: sha(p) for p in [
        PIPE / "goal.json", PIPE / "queue.json", PIPE / "running.json",
        PIPE / "experiments.csv",
    ]}
    output = PIPE / "reports" / f"remaining_control_audit_{STAMP}"
    output.mkdir(exist_ok=True)
    corpus = []
    for path in sorted((PIPE / "analyses").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        corpus.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path),
                           characters=len(text)))
    with (PIPE / "experiments.csv").open(encoding="utf-8-sig", newline="") as stream:
        ledger = list(csv.DictReader(stream))
    pairs = []
    for child, parent, suffix in [(189, 177, "mqbc"), (190, 178, "mqtd"),
                                  (191, 176, "mqsd"), (193, 174, "mqhc")]:
        eid = f"M{child}-CTF-HCG-CSORT-{suffix.upper()}-TR"
        pid = f"M{parent}-CTF-HCG-CSORT-{suffix.upper()}"
        exp = json.loads((PIPE / "experiments" / f"{eid}.json").read_text(encoding="utf-8"))
        parent_exp = json.loads((PIPE / "experiments" / f"{pid}.json").read_text(encoding="utf-8"))
        parent_dir = ROOT / "Cluster/framework/model/Quard_model" / f"{BASE}_{suffix}"
        child_dir = parent_dir.with_name(f"{BASE}_{suffix}_tr")
        pfiles = {p.relative_to(parent_dir).as_posix(): p for p in parent_dir.rglob("*.py")}
        cfiles = {p.relative_to(child_dir).as_posix(): p for p in child_dir.rglob("*.py")}
        assert pfiles.keys() == cfiles.keys()
        changed = [name for name in pfiles if sha(pfiles[name]) != sha(cfiles[name])]
        assert changed == ["dec.py"], changed
        before = pfiles["dec.py"].read_text(encoding="utf-8")
        after = cfiles["dec.py"].read_text(encoding="utf-8")
        expected = before.replace(
            "if previous_masks is not None:",
            "if layer_i == len(self.decoder_layers) - 1 and previous_masks is not None:")
        only_recurrence = expected == after
        assert only_recurrence == (child != 190)
        diff = "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                          fromfile=pid, tofile=eid))
        (output / f"M{child}_dec.diff").write_text(diff, encoding="utf-8")
        pcfg = ROOT / "Cluster" / parent_exp["config"]
        ccfg = ROOT / "Cluster" / exp["config"]
        assert pcfg.read_bytes() == ccfg.read_bytes()
        log_paths = list((ROOT / "Checkpoints" / parent_exp["server"] /
                          f"{BASE}_{suffix}").rglob("*.log"))
        assert len(log_paths) == 1, log_paths
        log = log_paths[0]
        log_text = log.read_text(encoding="utf-8")
        rows = parse_log(log_text)
        assert [r["epoch"] for r in rows] == list(range(1, len(rows) + 1))
        best = max(rows, key=lambda r: r["miou"])
        assert {"acc50", "spmiou"} <= best.keys()
        stale = len(rows) - best["epoch"]
        assert stale == (5 if parent == 174 else 10)
        if parent_exp.get("log_sha256"):
            assert sha(log) == parent_exp["log_sha256"]
        entry = dict(child=eid, parent=pid, child_status=exp["status"],
                     parent_best=best, parent_validations=len(rows), parent_stale=stale,
                     parent_log=str(log.relative_to(ROOT)), parent_log_sha256=sha(log),
                     config_byte_identical=True, changed_files=changed,
                     recurrence_only=only_recurrence,
                     package_files={name: dict(parent=sha(pfiles[name]), child=sha(cfiles[name]))
                                    for name in pfiles})
        if child in (189, 190):
            run_stamp = "20260912_030730" if child == 189 else "20260912_050805"
            remote = ("/data/songcl/Project/Cluster_project/Cluster_checkpoints/"
                      f"{BASE}_{suffix}_tr/{run_stamp}/{run_stamp}.log")
            result = subprocess.run(
                ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=12",
                 "songcl@192.168.1.137", f"cat {remote}"],
                check=True, capture_output=True, timeout=60)
            snapshot = output / f"M{child}_live_snapshot.log"
            snapshot.write_bytes(result.stdout)
            live = parse_log(result.stdout.decode("utf-8"))
            complete = [r for r in live if {"acc50", "spmiou"} <= r.keys()]
            live_best = max(complete, key=lambda r: r["miou"])
            entry["live"] = dict(best=live_best, completed_validations=len(complete),
                                 snapshot_sha256=sha(snapshot),
                                 snapshot_at=datetime.now().isoformat(),
                                 no_improve=len(complete) - live_best["epoch"])
        pairs.append(entry)
    assert protected == {name: sha(PIPE / name) for name in protected}
    evidence = dict(created_at=datetime.now().isoformat(), protected_state=protected,
                    analysis_inventory=corpus, ledger_rows=len(ledger), pairs=pairs)
    (output / "audit.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    table = "\n".join(
        f"| {p['child']} | {p['parent']} | {p['parent_best']['miou']:.10f} | "
        f"{p['parent_best']['epoch']}/{p['parent_validations']} | "
        f"{p['parent_stale']} | {'recurrence only' if p['recurrence_only'] else 'recurrence + padding fix'} |"
        for p in pairs)
    report = f"""# Remaining Legacy Control Audit

2026-09-12, tick #20260912-1907. CPU-only audit of the four preserved pairs,
selected from the original queue, not from current scores. No new experiment.

| Child | Parent | Parent exact best | Best/final epoch | Post-best validations | Source change |
|-------|--------|-------------------|------------------|-----------------------|---------------|
{table}

All four numerical YAMLs are byte-identical to their parents; all four
packages differ only in dec.py. For M189/M191/M193, the complete source
difference is the final-layer condition replacing the recurrent condition.
M190 additionally slices padded cluster features to each scene's real
cluster count. This confirms the already documented repair; it is not a new
bug or permission to change the active trainer.

## Interpretation Boundaries

- M189 vs M177: a source-level recurrence intervention with full-patience
  parent evidence; one seed and no paired scene predictions still preclude
  a statistically established recurrence effect.
- M190 vs M178: padding correction and recurrence removal are two changed
  behaviors. A future score difference cannot isolate recurrence alone.
- M191 vs M176: source-level recurrence intervention, but parent ran on
  server-6 and child is assigned server-4. Hardware and training environment
  matching remain unverified; do not claim they are controlled.
- M193 vs M174: parent has only five post-best validations due to historical
  monitor-parser stopping error. A future full-patience child comparison is
  censored on the parent side.
- All four parents exceeded the current 10G gate in archived analyses.
  Their scores remain historical comparisons, not resource-qualified baselines.
- Live M189/M190 are censored observations, not terminal results. Waiting
  M191/M193 have no outcome. No successors or reruns follow this audit.

## Evidence And Limits

All {len(corpus)} analysis documents and {len(ledger)} ledger rows were read.
JSON inventories every analysis hash, four parent log hashes, exact paired
best metrics, package hashes and two timestamped live-log snapshots. Hashes
are local integrity records; this tick does not claim fresh remote hash
verification of the four parent archives.

This audit addresses correctness of existing comparisons. It supplies no new
measured error, forward/loss derivation, novelty, robustness or efficiency result.
The admission gap remains open. goal/queue/running/ledger bytes are unchanged.
"""
    (output / "audit.md").write_text(report, encoding="utf-8")
    goal = (PIPE / "goal.json").read_text(encoding="utf-8")
    assessment = "\n".join(
        f"| {r['id']} | {r['best_miou'] or 'missing'} | {r['state']} | "
        "Historical evidence; retain prior analysis and route closure |" for r in ledger)
    review = f"""# Motivation Review - cluster_project
2026-09-12 19:15, tick #20260912-1907.

## 1. Goal
Full authoritative goal:
```json
{goal.strip()}
```
check_goal19:10: Phase1 NOT YET; target .5100; ledger champion .5020/gap .0080.
Exact M95 .5024607181549072; baseline .4894491136074066; exact gap .0075392818450928.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Historical context gains | supported historically | M95 above baseline | Not a novel mechanism |
| Same-category selection bottleneck | exploratory support | Frozen D1/D2 audits | Independent confirmation |
| Terminal-readout controls beat M95 | unsupported so far | 0/5 completed M184-M188 | Four preserved runs censored/waiting |
| Remaining controls uniformly isolate recurrence | not true | M190 padding repair; M174 partial patience | Confounded comparisons |

## 3. Experiment Assessment
Complete current corpus: {len(corpus)} analyses, {len(ledger)} ledger rows,
hash-inventoried in reports/remaining_control_audit_{STAMP}/audit.json.
Old waiting ledger rows are not current dispatch state.

| Experiment | mIoU ledger | State | Motivation assessment |
|------------|-------------|-------|-----------------------|
{assessment}

Focused audit: M189/M191/M193 change only recurrence at source level;
M190 also fixes padding. M174 parent stopped after five stale validations.
These limits must carry into future terminal analyses.

## 4. Gap Analysis
Q1: A specific diagnostic error still needs a derived, primary-source-distinct
mechanism. Historical control correctness does not fill this scientific gap.
Closed score/ranking/relation and upstream-coupling routes remain closed.
Do not reuse repeatedly mined validation banks as independent confirmation.

## 5. Design Rationale
Q2: Check existing code/log comparisons before interpreting pending outcomes.
Q3: Prevent a recurrence-only claim from a two-change or censored comparison.
Constraints1-8: no compute/training/schedule/seed change; no tuning, routing
or repeated-injection revival. Constraints9-12: evidence/derivation/novelty/
matched controls/validation gates retained; admission precedes depth.
All11 bans checked: no candidate graph or numeric change is proposed.
Smell check: offline correctness audit only, not a new training mechanism.

## 6. Next Batch
No admitted new mechanism; no exp_design, implementation, enqueue or sync.
Preserve live M189/M190 and original server-4 FIFO M191 then M193.
Queue2/5 triggers review but does not override scientific admission.
"""
    (PIPE / "reviews" / f"motivation_review_{STAMP}.md").write_text(review, encoding="utf-8")
    print(json.dumps(dict(output=str(output), pairs=pairs,
                          analyses=len(corpus), ledger_rows=len(ledger)), indent=2))


if __name__ == "__main__":
    main()
