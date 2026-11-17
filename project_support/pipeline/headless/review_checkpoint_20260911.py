"""Render six-section provenance review with the complete current goal."""
import json
from pathlib import Path

ROOT = Path("D:/project/cluster_project")
goal = json.loads((ROOT / "pipeline/goal.json").read_text(encoding="utf-8"))
text = """================================================================================
  Motivation Review - cluster_project
  2026-09-11 04:15 Asia/Shanghai
================================================================================

## 1. Goal
Required checker04:08:15: Phase1 NOT YET, ledgerchampion.5020/target.5100/gap+.0080.
Complete authoritative goal snapshot follows;12constraints/11bans unchanged.
```json
""" + json.dumps(goal, ensure_ascii=False, indent=2) + """
```

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Historical context platform improves reference | Descriptive support | Exact M95 .5024607182 vs baseline .4894491136 | Seed fragility; not new novelty |
| Terminal transport beats champion | Unsupported for M186 | .4944996834@17, normal stop27 | Does not explain errors |
| Fixed checkpoint diagnosis is feasible | CPU compatibility verified | Two metadata/log/weight audits | GPU prediction replay and bank collector pending |
| Shared-anchor mechanism addresses measured bottleneck | Provisional | Derivation memo only | No measured errors or verified novelty |

## 3. Experiment Assessment
| Experiment | Exact mIoU | Epoch | Paired Acc50/spmIOU | Evidence role |
|------------|------------|-------|--------------------|---------------|
| Baseline archive20260627_174353 | .4894491136074066 | 15 | .541/.451 | Fixed checkpoint matches log; old analyses misstate epoch/Acc50 |
| M95 archive20260815_101011 | .5024607181549072 | 16 | .557/.465 | Exact checkpoint metric above ledger .5020, still below target |
| M183 | .49154922366142273 | 14 | .545/.455 | Closed tested initialization |
| M186 | .49449968338012695 | 17 | .548/.459 | Closed tested transport; no automatic successor |
| M184/M185/M187/M188 | unfinished | ongoing | live snapshot | Preserve, not final efficacy evidence |
Ledger222rows and224analysis files unchanged. All223 older hashes from
inventory20260910-1324 match; M186 was already analyzed last tick.
This is a supplemental audit, not a new experiment or a rewritten historical result.

## 4. Gap Analysis
- CPU-only worker imported explicit modules, not current automatic fallback.
  Baseline config really was configs/Quard/model_base2.yaml in launch log.
  framework.model.Quard_model.model_base1 fits its learned state; legacy
  model_base2/model_base2 dec.py differs at language-to-instance encoder attention.
  Package naming alone is not historical forward proof; no archived June code
  commit is available in the local git history (initial commit July14).
- Both raw strict loads fail on exactly text_encoder.embeddings.position_ids
  and token_type_ids. Both saved int64[1,514] buffers equal runtime buffers.
  Omitting ONLY these two in memory gives strict load success; no checkpoint
  writes, weight reshaping, missing learned tensors or nonfinite tensor values.
- CUDA_VISIBLE_DEVICES empty; torch.cuda.is_initialized false in both audits.
  One CPU thread, sequential workers; no GPU inference or optimizer steps.
- Checkpoint SHA256 baseline:
  dbc37e8fe8428f0f295121df61fae8a9ffd7dd98c10913ef911354345ff16745.
  M95:fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e.
- Metadata baselineepoch15/best.4894491 and M95epoch16/best.5024607 agree
  with full logs to metadata precision. Exact gain=.01301160455 and
  gap=.00753928185. These are historical audit values, NOT a fresh replay.
  Required goalchecker still uses unmodified ledger .5020/.4894.
- Audit JSONs and two full logs copied locally and SHA-verified; package
  per-file hashes, shapes, full saved YAML and all validations recorded.
- Frozen v2 manifest unchanged:284diagnostic descriptions/71physical scenes;
  4646reserved descriptions/70scenes. Scene sets disjoint; historically reused
  validation is not an independent test set. No new sample selection.
- D1 full candidate masks, selected index, superpoint mapping and GT need an
  isolated collector. Existing predict output returns selected mask only.
  State compatibility does not prove forward equivalence, dataset identity
  across historical dates, numerical replay or error prevalence.

## 5. Design Rationale
Q1: Need reliable baseline/champion replay before diagnosing mask-bank limitation
versus oracle selection gap. Unsupported model fallback could invalidate comparison.
Q2: Explicit import plus exact-buffer-only compatibility removes silent partial
weight loading from the next diagnostic protocol; requires replay, not assumed success.
Q3: D1 should report selected/oracle IoU on the same bank and frozen sample,
then decide ONE mechanism using errors, derivation and verified primary papers.

Coverage: D0 provenance advanced; D1 measurement pending; core derivation and
novelty remain provisional; matched comparison has verified state compatibility
but no predictions; robustness scene split frozen; resource-limited inference
must be checked before any GPU worker. No new numerical configuration or graph.
All12 constraints/11bans retained, no tuning, routing/gates/residuals/repeated
injection, extra seeds, new datasets, schedule changes or resource waiver.

## 6. Next Batch
No new exp_design/model/enqueue: waiting4<capacity4+1 triggers review, but no
new mechanism passes scientific admission. Next productive step: isolated D1
candidate-bank collector with explicit audited modules and buffer checks,
bounded GPU preflight and replay diagnostics; do not edit active packages.
Preserve M189/M190/M191/M193 FIFO and all four running trainers.
Artifacts: reports/d0_checkpoint_identity_20260911-0413/verified_summary.json,
d0_baseline_identity_20260911.json, d0_m95_identity_20260911.json and full logs.
================================================================================
"""
(ROOT / "pipeline/reviews/motivation_review_20260911-041500.md").write_text(text, encoding="utf-8")
