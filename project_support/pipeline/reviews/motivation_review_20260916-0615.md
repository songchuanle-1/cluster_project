# Motivation Review - Context Instance Coverage
2026-09-16 06:15 Asia/Shanghai.

## 1. Goal
Authoritative goal.json unchanged;Phase1 target.51,exactM95.5024607181549072.
Existing TRAIN only,scientific admission before slots,server6GPU7 native probe.

## 2. Story Status
Category-union fields lose instance partition;graph signatures distinguish
textual inputs but not physical instances. Need deployable instance evidence.
Question:can current target-conditioned query masks directly supply that bank?

## 3. Experiment Assessment
Fixed123TRAIN expressions16batches,32scenes;native mask threshold sigmoid>=.5,
IoU intersection/(union+1e-6),no threshold change or optimizer update.
| Group | Instance-expression pairs | Sampled seed present | Any mask IoU>.5 | Own-seed mask IoU>.5 |
|---|---:|---:|---:|---:|
| Target |123|117|118|110|
| Non-target |4381|2850|379|353|
| Exact other-noun, non-target |335|270|55|53|
Exact matching uses raw aggregation names;it is not intended-anchor annotation.
Counts repeat physical instances across expressions;not independent trials.
These are descriptive fixedTRAIN results,not VAL rates or causal attribution.
Worker completed all16batches,exit0;one run,no repair.

## 4. Gap Analysis
Target masks cannot be presumed to represent contextual instances. Many
non-target instances have sampled seeds but no accurate mask in the current bank.
Native loss supervises masks for matched target seeds,not full-scene instances.
This source observation is consistent with coverage difference,not causal proof.
Reusing masks as latent anchors without explicit instance learning is unsupported.
Poor pretrained coverage does NOT prove that a properly supervised trainable
new branch cannot learn;no pretrained-one-step improvement gate is introduced.

## 5. Design Rationale
Next complete candidate must specify how non-target instance identity is learned
and retained while grounding the target;GT instance IDs only in training losses.
Simply adding generic all-instance mask supervision is not yet a novel mechanism.
Compare whole computation against ORD/CoT3DRef/NS3D and closed shared-witness
proposal;its historical rejection concerns joint-anchor priorart,soft-gap formula
and limited applicability,not an impossibility theorem for instance learning.
Concurrent06:13 graph observability evidence preserved;no repeated graph audit.

## 6. Next Batch
Derive instance-preserving relation computation and its supervised interface;
decide complete mechanism before any independent package/config.
Native backward,matched resources,eight-gate admission,ffsync,launch pending.
Do not repeat target/context coverage or add a mask reranker to fill slots.
Evidence:context_instance_coverage_20260916.json;decision061522.
