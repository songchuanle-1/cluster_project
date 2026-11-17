"""Freeze documents, deploy isolated helpers, and collect the CPU identity audit."""
from datetime import datetime
import json
from pathlib import Path
import subprocess
import yaml
from d1_identity_geometry_20260911 import sha

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
OUT = P / "reports/d1_identity_20260911-0912"
REMOTE = "/tmp/cluster_d1_identity_20260911_0912"


def run(args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, timeout=120, **kwargs).stdout


def prepare():
    assert not OUT.exists()
    OUT.mkdir()
    goal = json.loads((P / "goal.json").read_text(encoding="utf-8"))
    old = P / "reports/d1_instance_20260911-0810"
    pairs = json.loads((old / "protocol.json").read_text(encoding="utf-8"))["pairs"]
    ids = sorted({tuple(pair[role]) for pair in pairs for role in ("error", "control") if pair[role]})
    protocol = dict(created=datetime.now().isoformat(), ids=ids, pairs=pairs,
                    audit_sha256=sha(old / "instance_audit.json"),
                    limits="21 frozen IDs/12 errors/9 controls/3 missing controls, outcome-selected; no causal or prevalence inference. Aggregation label accepted only after exact segment mask equals raw instance mask. Exact lexical label equality is annotation-string equality, not ontology equivalence. Lexical noun candidates are not grounded anchors. Coordinates are preprocessed point frame, units/viewpoint not independently verified; no left/right/front/behind truth. No new inference, external annotation, dataset or reserved-scene analysis.",
                    formulas="c_i=mean(x in object_i); l_i=min(x); u_i=max(x); d_ij=||c_i-c_j||2; g=max(0,l_i-u_j,l_j-u_i) elementwise; ||g||2 is AABB distance lower bound, not contact or language relation truth.")
    (OUT / "protocol.json").write_text(json.dumps(protocol, indent=2), encoding="utf-8")
    review = f"""# Motivation Review - cluster_project
{protocol['created']} Asia/Shanghai
## 1. Goal
```json
{json.dumps(goal, ensure_ascii=False, indent=2)}
```
Checker09:10:30 Phase1 NOT YET; ledgerM95 .5020, baseline .4894, target .5100.
## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Candidate selection headroom | measured, exploratory | baseline90/M95111 recoverable of284 | Error identity |
| Same coarse semantic means same category | not established | unknown71/284, coarseID19 | Raw annotation join |
| Relation/boundary cause | unknown | parser text and overlap only | Grounding and causal controls |
## 3. Experiment Assessment
| Experiment | mIoU | Relation to goal | Contribution |
|---|---|---|---|
| Baseline/M95 historical | .489449/.502461 | Audited references | Not new replay |
| M183/M186 | .491549/.494500 | Legacy negative evidence | No descendants |
| D1 baseline/M95 sample | .535914/.502217 | Error diagnosis | 568 banks verified |
223 historical analyses remain reconciled through immutable inventory.
## 4. Gap Analysis
Same-semantic substitutions alone do not explain M95 extra21 recoverable errors.
Need exact labels for unknown/coarse categories and reproducible geometry.
No frame-grounded relation adjudication or new mechanism novelty established.
## 5. Design Rationale
CPU-only D1 continuation on frozen12 errors and9 controls. Validate aggregation
segment membership against raw object masks before using names or coordinates.
All12constraints/11bans retained. No new model, tuning or training admission.
Six areas: diagnosis now; core derivation/primary novelty N1 pending; existing
controls descriptive only; robustness V1 pending; CPU cost not model benchmark.
## 6. Next Batch
exp_design_20260911-091200.md; D1-IDENTITY only. Scientific admission overrides refill.
"""
    (P / "reviews/motivation_review_20260911-091200.md").write_text(review, encoding="utf-8")
    design = f"""# Experiment Design - cluster_project
{protocol['created']} Asia/Shanghai
## 1. Motivation
Verbatim goal.description: {goal['description']}
Waiting4/capacity4 triggers review; science gate blocks automatic mechanism refill.
## 2. Current Best Results
| ID | Config | State | mIoU | Acc50 | spmIOU | Epochs |
|---|---|---|---|---|---|---|
| Baseline | audited model_base1 | historical | .489449 | .541 | .451 | best15 |
| M95 | csort | historical | .502461 | .557 | .465 | best16 |
| M186 | mqht_tr | done_earlystop | .494500 | .548 | .459 |27|
## 3. Analysis & Direction
Effective: candidate bank audit permits diagnosis. Failed: explicit routing and
banned families remain closed. Unverified: boundary/relationship causes and N1.
Raw objectId and segIndices define a mask; require equality to raw instance==ID.
Exact labels remain annotation strings, never retrofit the full284 semantic labels.
{protocol['formulas']}
Formulas are geometric accounting, not a novel forward/loss; gradients N/A.
Complexity: per-scene O(N*I) sequential masks, O(N+I) temporary storage;
no N-squared attention or new trainable parameters.
Exact token subsequence match only for noun candidates; no synonym guessing.
## 4. Experiment Plan
| # | ID | Config/Inputs | Purpose | Expected Result | Priority | Depends On |
|---|---|---|---|---|---|---|
|1|D1-IDENTITY|frozen21IDs, raw aggregation/segments/points|exact identity provenance|42 paired records|P0|D1 instance|
|2|D1-GEOMETRY|verified object point sets|coordinates and lexical candidates|explicit unknown relations|P0|identity|
## 5. GPU Allocation Plan
| Server | GPU | Assignment | Config | Justification |
|---|---|---|---|---|
|server-4|0/1|preserve M188/M187|existing|CPU diagnostic only|
|server-6|7|preserve M184/M185|existing|both slots occupied|
Server-4 CPU, CUDA hidden, threads1,480s loop guard/600s timeout.
## 6. Implementation Checklist
- [x] Full goal review before design; freeze existing21IDs, no replacements.
- [x] Isolated worker with8 synthetic arithmetic/token checks.
- [ ] Hash sync to both servers preserving deployment diffs.
- [ ] Exact segment/instance joins; local independent geometry validation.
- [ ] Report missingness, fixed-case interpretations, final live snapshot/memory.
Training package/config/commit/enqueue N/A; no mechanism admitted.
## 7. Risk Assessment
{protocol['limits']}
Reject mismatched raw SHA/segment masks, nonfinite coordinates and duplicateIDs.
No manually invented geometry thresholds, category ontology, relation or boundary
labels. Source spelling preserved. <=3 documented helper repairs, no model rerun.
Smell check: diagnostic arithmetic, not proposed numerical model tuning.
Status: APPROVED for CPU diagnostics only; execution.json tracks completion.
"""
    (P / "designs/exp_design_20260911-091200.md").write_text(design, encoding="utf-8")


def main():
    prepare()
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    evidence = dict(started=datetime.now().isoformat(), deployments={})
    worker = P / "headless/d1_identity_geometry_20260911.py"
    for name in ("server-4", "server-6"):
        s = servers[name]
        host = f"{s['user']}@{s['host']}"
        ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host]
        before = run(ssh + [f"git -C {s['remote_code_root']} diff --binary HEAD"])
        run(ssh + [f"mkdir {REMOTE}"])
        files = [worker, OUT / "protocol.json",
                 P / "reports/d1_instance_20260911-0810/instance_audit.json"]
        evidence["deployments"][name] = {}
        for path in files:
            run(["scp", "-q", str(path), f"{host}:{REMOTE}/{path.name}"])
            digest = run(ssh + [f"sha256sum {REMOTE}/{path.name}"]).decode().split()[0]
            assert digest == sha(path)
            evidence["deployments"][name][path.name] = digest
        assert before == run(ssh + [f"git -C {s['remote_code_root']} diff --binary HEAD"])
    s = servers["server-4"]
    host = f"{s['user']}@{s['host']}"
    command = (
        f"set -e\nsource {s['conda_source']}\nconda activate {s['conda_env']}\n"
        "export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1\n"
        f"timeout 600s python -u {REMOTE}/{worker.name} --protocol {REMOTE}/protocol.json "
        f"--audit {REMOTE}/instance_audit.json --data-root {s['data_root']} --out {REMOTE}/result\n")
    result = subprocess.run(["ssh", "-o", "BatchMode=yes", host, "bash -s"],
                            input=command.encode(), capture_output=True, timeout=640)
    (OUT / "worker.log").write_bytes(result.stdout + result.stderr)
    evidence.update(returncode=result.returncode, finished=datetime.now().isoformat())
    (OUT / "execution.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print((result.stdout + result.stderr).decode(errors="replace")[-5000:])
    result.check_returncode()
    run(["scp", "-q", f"{host}:{REMOTE}/result/identity_geometry.json", str(OUT)])
    digest = run(["ssh", host, f"sha256sum {REMOTE}/result/identity_geometry.json"]).decode().split()[0]
    assert digest == sha(OUT / "identity_geometry.json")
    print("DOWNLOADED", digest)


if __name__ == "__main__":
    main()
