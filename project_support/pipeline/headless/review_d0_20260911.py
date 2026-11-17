"""Render the diagnostic review with an unabridged authoritative goal snapshot."""
import json
from pathlib import Path

ROOT = Path("D:/project/cluster_project")
goal = json.loads((ROOT / "pipeline/goal.json").read_text(encoding="utf-8"))
text = """================================================================================
  Motivation Review - cluster_project
  2026-09-11 03:19 Asia/Shanghai
================================================================================

## 1. Goal
Target .5100; champion M95 .5020; gap+.0080. Phase1 NOT YET at03:14:52.
Complete goal.json snapshot (12 constraints / 11 bans, no changes):

```json
""" + json.dumps(goal, ensure_ascii=False, indent=2) + """
```

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Existing context benefits the original platform | Historical support | A1 .5012 vs .4894 | Not a new contribution |
| Terminal hierarchy transport improves champion | Not supported in this run | M186 .4944996834@17, normal stop27 | Does not identify failure cause |
| Shared physical anchors solve observed errors | Provisional | Mathematical memo only | No measured failure prevalence or verified novelty |
| Candidate quality versus selection is diagnosable | Data access partially verified | D0 inventory and frozen manifest v2 | Need full candidate-bank outputs and verified checkpoints |

## 3. Experiment Assessment
| Experiment | mIoU | Relation to motivation | Contribution |
|------------|------|------------------------|--------------|
| Baseline model_base1 | .4894 | Historical reference | Folder contains model_base2.yaml; checkpoint/config identity needs audit |
| M95 | .5020 | Best recorded platform | Seed and historical patience limitations, not a robust mechanism proof |
| M169 | .5000 | Parent clue for legacy M188 | Compromised patience prevents clean full-run comparison |
| M183 | .4915492237 | Fixed ancestor initialization | Below champion; close tested variant |
| M186 | .4944996834 | Terminal transport | +.0050996834 baseline, -.0075003166 champion; close tested variant |
| M184/M185/M187/M188 | unfinished | Existing admitted legacy controls | Preserve, no efficacy conclusions |
All223 historical analysis hashes matched inventory20260910-1324; one new M186
analysis gives224 files, not224 independent experiments. Ledger222rows includes
historical duplicates/placeholders. Original analyses preserved, not rewritten.

## 4. Gap Analysis
- D0 source: existing remote ScanRefer_val_new.json;9508 unique compound IDs,
  141scan IDs/141physical scene prefixes. All141 required refer.pth files exist.
- Authoritative sample_manifest_v2.json:71 diagnostic physical scenes/284
  descriptions (four per scan);70 reserved scenes/4646 descriptions. Other4578
  diagnostic-scene descriptions are unsampled, not moved into evaluation.
- Split and within-scene sampling use fixed SHA256 ordering before prediction.
  v1 preserved but superseded before any inference. v2 uses physical scene
  grouping defensively; this annotation subset actually has one scan per prefix.
- ManifestSHA25684a7d60f85ecd5bec44b77b304140ff00c8c1fa00177dc12ecf7ef5ebfabb468.
- AnnotationSHA2564455b8857ade37aaafa32581537a961a77bcc756b22d8143ed4021bc88b7931f.
- Champion best/last checkpoint files exist (936269892bytes each); candidate
  baseline best/last exist (854106664bytes). Contents/metadata not loaded yet.
  Baseline saved YAML naming discrepancy must be resolved before matched evaluation.
- No prediction exports found in the two inspected run directories through depth4.
  This is scoped absence, not a global assertion that exports do not exist anywhere.
- tools/test.py saves selected masks; M95 network.predict_by_feat selects
  argmax softmax(indis) and returns only the chosen point mask. Full bank required
  for o=max IoU is unavailable in these returned outputs.
- No error frequencies, oracle values, boundary labels or causal bottleneck measured.
- Prospective reserved validation is historically reused, not an untouched test set.
  Equal-scene samples cannot be reported as population-weighted prevalence.

## 5. Design Rationale
Q1: Missing quantified errors, verified checkpoint identity and full bank outputs.
Q2: D0 first freezes evidence sources and samples; next audit checkpoint metadata
and use an isolated evaluation collector without modifying active model packages.
Q3: D1 will distinguish bank limitation from selection headroom; only then choose
one mechanism, derive it and verify primary papers. No novelty claim here.

Coverage: diagnosis=D0 partial/D1 pending; derivation=provisional memo, not admitted;
novelty=unverified; matched controls=baseline identity pending; robustness=scene
separation frozen, perturbations pending; efficiency=legacy admission retained,
new mechanism profiling not applicable. Inference capacity and memory must be
checked before a bounded evaluation worker; no extra trainer authorized.

All12 constraints and11 bans remain binding: no tuning, schedule/seed changes,
gates, explicit/language routing, residual/repeated injection, N^2 attention or
resource exemption. No proposed new graph passes scientific admission this tick.

## 6. Next Batch
No new exp_design or training enqueue: scientific admission overrides waiting4
versus capacity4+1. Continue D0 checkpoint provenance, then D1 candidate-bank
collector and error measurement on the frozen diagnostic sample.
No automatic sibling pooling/selector/readback family, no multiseed campaign,
new dataset, external annotation API or Phase2 work. Preserve M189/M190/M191/M193.
Artifacts: reports/d0_inventory_20260911-0316/{inventory.json,sample_manifest_v2.json}.
================================================================================
"""
out = ROOT / "pipeline/reviews/motivation_review_20260911-031900.md"
out.write_text(text, encoding="utf-8")
print(out)
