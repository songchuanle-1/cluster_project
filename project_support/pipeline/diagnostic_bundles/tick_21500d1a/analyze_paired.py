"""Scene-clustered analysis of the already-frozen paired checkpoint evidence."""
from collections import defaultdict
from datetime import datetime, timezone
import json
import sys
import numpy as np
from audit_terminal import guard, save, ROOT, OUT, tick

guard()
sys.path.insert(0, str(OUT))
from aligned_evidence import align_pairs

reference = tick.load(OUT / "reference_m95_epoch16.json")
candidate = tick.load(OUT / "candidate_hds_epoch19.json")
manifest = tick.load(OUT / "paired_manifest.json")
assert manifest["analysis_bootstrap_draws"] == 5000 and manifest["analysis_seed"] == 1999
pairs = align_pairs(reference["records"], candidate["records"])
assert len(pairs) == 9508 and all(left["split"] == right["split"] == "val" for left, right in pairs)
groups = defaultdict(list)
for left, right in pairs:
    groups[left["scene_id"]].append((left["piou"], right["piou"]))
scenes = sorted(groups)
counts = np.asarray([len(groups[scene]) for scene in scenes], dtype=np.int64)
left_sums = np.asarray([np.asarray(groups[scene], dtype=np.float64)[:, 0].sum() for scene in scenes])
right_sums = np.asarray([np.asarray(groups[scene], dtype=np.float64)[:, 1].sum() for scene in scenes])
differences = right_sums - left_sums
random = np.random.RandomState(1999)
indices = random.randint(0, len(scenes), size=(5000, len(scenes)))
bootstraps = differences[indices].sum(axis=1) / counts[indices].sum(axis=1)
interval = np.percentile(bootstraps, [2.5, 97.5])
per_scene = [{"scene_id": scene, "expressions": int(counts[i]),
              "reference_mean_float64": float(left_sums[i]/counts[i]),
              "candidate_mean_float64": float(right_sums[i]/counts[i]),
              "paired_delta": float(differences[i]/counts[i])} for i, scene in enumerate(scenes)]
result = {"observed_at": datetime.now(timezone.utc).isoformat(), "paired_expressions": len(pairs),
          "independent_scene_clusters": len(scenes), "reference_checkpoint_epoch": 16,
          "reference_is_historical_champion_weights": "unverified, not claimed",
          "candidate_checkpoint_epoch": 19,
          "reference_native_float32_miou": reference["native_float32_miou"],
          "candidate_native_float32_miou": candidate["native_float32_miou"],
          "native_float32_delta": candidate["native_float32_miou"]-reference["native_float32_miou"],
          "expression_weighted_paired_delta_float64": float(differences.sum()/counts.sum()),
          "macro_scene_paired_delta": float((differences/counts).mean()),
          "expression_weighted_scene_cluster_bootstrap_95ci": interval.tolist(),
          "bootstrap_draws": 5000, "bootstrap_analysis_seed": 1999,
          "candidate_worse_scenes": int((differences < 0).sum()),
          "candidate_better_scenes": int((differences > 0).sum()),
          "equal_scenes": int((differences == 0).sum()), "per_scene": per_scene,
          "optional_predefined_subgroups": "unmeasured; no verified reproducible subgroup labeling contract loaded, no invented labels",
          "independent_repeat_noise_floor": "unmeasured",
          "whole_training_peak_memory": "unmeasured",
          "interpretation": "Fixed-checkpoint matched original VAL population only. This quantifies uncertainty relative to the exact M95epoch16 reference, not historical champion weights, universal mechanism harm, independent replication or cross-dataset generalization.",
          "native_optimizer_steps": 0}
save("paired_analysis.json", result)
work = tick.load(ROOT / "pipeline/research_work.json")
operational = next(c for c in work["candidates"] if c["id"] == "m202-paired-native-evidence-producer")
assert operational["stage"] == "validation"
operational.update(stage="complete", outcome="native_exporter_equivalence_and_frozen_full_val_pair_measured",
    execution_status="4TRAINscenes16expressions native payload/float32 export equality passed; full original VAL9508expressions exported for each exact checkpoint with matching IDs and scene-clustered uncertainty.0optimizer steps. Software completion, not model efficacy PASS.",
    next_action="Reuse the validated exporter without changing frozen predictions. Preserve full paired evidence/reference limitations; future mainline mechanism selection requires TRAIN-only causal/error evidence, not tuning against this VAL comparison. Optional subgroup labels/independent-repeat noise remain unmeasured.")
for name in ("paired_capture_index.json", "paired_analysis.json", "paired_execution_attempt.json"):
    path = OUT/name
    operational["evidence"].append({"path": path.relative_to(ROOT).as_posix(), "sha256": tick.digest(path)})
primary = next(c for c in work["candidates"] if c["id"] == "m95-hierarchical-mask-feature-path-audit")
assert primary["stage"] == "complete"
primary["evidence"].append({"path": (OUT/"paired_analysis.json").relative_to(ROOT).as_posix(), "sha256": tick.digest(OUT/"paired_analysis.json")})
guard()
tick.save(ROOT/"pipeline/research_work.json", work)
print(json.dumps({key: result[key] for key in ("paired_expressions", "independent_scene_clusters", "reference_native_float32_miou", "candidate_native_float32_miou", "expression_weighted_paired_delta_float64", "macro_scene_paired_delta", "expression_weighted_scene_cluster_bootstrap_95ci")}, indent=2))
