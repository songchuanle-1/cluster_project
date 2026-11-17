"""Frozen full-identity paired VAL analysis; CPU only, no model selection."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import socket

import numpy as np
from aligned_evidence import align_pairs, native_mean, record_key

ROOT = Path(__file__).resolve().parent
assert socket.gethostname() == 'dl04-MS-7E06'
manifest = json.loads((ROOT / 'paired_manifest_isolated.json').read_text())
assert (datetime.fromisoformat(manifest['deadline_at']) - datetime.now(timezone.utc)).total_seconds() > 80


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(pairs):
    scenes = sorted({left['scene_id'] for left, right in pairs})
    if not pairs:
        return {'expressions': 0, 'scenes': 0, 'delta': None, 'status': 'UNKNOWN_EMPTY'}
    scene_index = {scene: index for index, scene in enumerate(scenes)}
    indices = np.array([scene_index[left['scene_id']] for left, right in pairs])
    left = np.array([a['piou'] for a, b in pairs], dtype=np.float64)
    right = np.array([b['piou'] for a, b in pairs], dtype=np.float64)
    count = np.bincount(indices, minlength=len(scenes))
    reference_sum = np.bincount(indices, weights=left, minlength=len(scenes))
    candidate_sum = np.bincount(indices, weights=right, minlength=len(scenes))
    difference = candidate_sum - reference_sum
    means = difference / count
    result = {'expressions': len(pairs), 'scenes': len(scenes),
              'reference_expression_mean_float64': float(left.mean()),
              'candidate_expression_mean_float64': float(right.mean()),
              'delta': float((right-left).mean()),
              'reference_macro_scene_mean': float((reference_sum/count).mean()),
              'candidate_macro_scene_mean': float((candidate_sum/count).mean()),
              'macro_scene_delta': float(means.mean()),
              'scene_positive_negative_zero': [int((means > 0).sum()), int((means < 0).sum()), int((means == 0).sum())],
              'per_scene': [{'scene_id': scene, 'expressions': int(count[i]),
                             'reference': float(reference_sum[i]/count[i]),
                             'candidate': float(candidate_sum[i]/count[i]),
                             'delta': float(means[i])} for i, scene in enumerate(scenes)]}
    if len(scenes) < 10:
        result.update(expression_delta_ci95=None, macro_scene_delta_ci95=None,
                      material_harm='INCONCLUSIVE_FEWER_THAN_10_SCENES')
        return result
    rng = np.random.default_rng(1999)
    draws = rng.integers(0, len(scenes), size=(5000, len(scenes)))
    weighted = difference[draws].sum(axis=1) / count[draws].sum(axis=1)
    macro = means[draws].mean(axis=1)
    ci = np.quantile(weighted, [.025, .975])
    macro_ci = np.quantile(macro, [.025, .975])
    result.update(expression_delta_ci95=ci.tolist(), macro_scene_delta_ci95=macro_ci.tolist(),
                  material_harm='MEETS_PREDECLARED_HARM_RULE' if result['delta'] < -.003 and ci[1] < -.003 else 'INCONCLUSIVE_NOT_ESTABLISHED')
    return result


def controls():
    records = [{'split': 'val', 'scene_id': 'scene'+str(i//2), 'object_ids': [i],
                'ann_id': i, 'piou': float(np.float32(.25 + i/16))} for i in range(6)]
    paired = align_pairs(records, list(reversed(records)))
    assert all(record_key(a) == record_key(b) for a, b in paired)
    result = summarize(paired)
    assert result['delta'] == result['macro_scene_delta'] == 0
    assert result['expression_delta_ci95'] is None
    duplicate_refused = missing_refused = False
    try:
        align_pairs(records, records + [records[0]])
    except ValueError:
        duplicate_refused = True
    try:
        align_pairs(records, records[:-1])
    except ValueError:
        missing_refused = True
    assert duplicate_refused and missing_refused
    return {'identity_order_independent': True, 'duplicate_refused': True,
            'missing_refused': True, 'zero_delta': True, 'small_scene_ci_not_invented': True}


checks = controls()
ref_path = ROOT / 'reference_m95_epoch16.json'
candidate_path = ROOT / 'candidate_fle_epoch13.json'
assert digest(ref_path) == manifest['reference_export_sha256']
reference = json.loads(ref_path.read_text())
candidate = json.loads(candidate_path.read_text())
assert candidate['checkpoint_epoch'] == 13
assert candidate['checkpoint_sha256'] == manifest['conditions']['candidate_fle_epoch13']['checkpoint_sha256']
assert candidate['optimizer_steps'] == 0
pairs = align_pairs(reference['records'], candidate['records'])
assert len(pairs) == 9508
assert all(a['split'] == b['split'] == 'val' for a, b in pairs)
assert len({a['scene_id'] for a, b in pairs}) == 141
for value in (reference, candidate):
    assert native_mean([r['piou'] for r in value['records']]) == value['native_float32_miou']
groups = {'all': pairs,
          'mixed_fine_leaf': [(a, b) for a, b in pairs if b.get('mixed_fine_leaf') is True],
          'no_mixed_fine_leaf': [(a, b) for a, b in pairs if b.get('mixed_fine_leaf') is False],
          'unknown_fine_leaf': [(a, b) for a, b in pairs if b.get('mixed_fine_leaf') is None]}
assert sum(len(groups[name]) for name in groups if name != 'all') == 9508
result = {'observed_at': datetime.now(timezone.utc).isoformat(),
          'controls': checks, 'full_identity_pairing': True,
          'reference_sha256': digest(ref_path), 'candidate_sha256': digest(candidate_path),
          'analysis_sha256': digest(Path(__file__)),
          'bootstrap': {'draws': 5000, 'seed': 1999, 'unit': 'scene',
                        'estimands': ['expression-weighted ratio under scene resampling', 'equal-scene macro mean'],
                        'minimum_scenes_for_ci': 10, 'harm_boundary': -.003},
          'reference_native_miou': reference['native_float32_miou'],
          'candidate_native_miou': candidate['native_float32_miou'],
          'native_float32_delta': candidate['native_float32_miou']-reference['native_float32_miou'],
          'candidate_inference_peak_bytes': candidate['peak_inference_allocated_bytes'],
          'groups': {name: summarize(values) for name, values in groups.items()},
          'noise_floor': 'UNKNOWN_NO_INDEPENDENT_REPEATS',
          'full_training_peak': 'UNKNOWN',
          'scope': 'Single frozen best M203 versus available M95 epoch16, not verified historical champion weights; VAL not TEST; no tuning or mechanistic control claim'}
out = ROOT / 'paired_analysis_result.json'
assert not out.exists()
out.write_text(json.dumps(result, indent=2, allow_nan=False))
print(json.dumps({key: result[key] for key in ('observed_at', 'candidate_native_miou', 'native_float32_delta')}))
print(json.dumps({name: {key: value for key, value in summary.items() if key != 'per_scene'}
                  for name, summary in result['groups'].items()}))
