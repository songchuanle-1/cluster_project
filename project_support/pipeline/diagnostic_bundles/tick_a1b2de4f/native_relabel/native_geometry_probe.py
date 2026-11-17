"""Original native FPS/partition recomputation under physical row relabeling."""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import sys
from native_runtime import acquire, release, save, MANIFEST, ROOT, NAME, sha

parser = argparse.ArgumentParser()
parser.add_argument('--lease', required=True)
args = parser.parse_args()
result = {'execution_completed': False, 'controls_passed': False, 'scientific_admission': False,
          'new_training': 0, 'model_weights_loaded': False, 'native_mask_replays': 0,
          'native_backwards': 0, 'records': [],
          'scope': 'Native unweighted geometry only;physical co-membership is not trained mask efficacy or mechanism admission.'}
try:
    result['before'] = acquire(args.lease)
    sys.path[:0] = [str(ROOT), str(ROOT / 'framework/lib')]
    from tools import train
    import torch
    torch.set_num_threads(1)
    torch.manual_seed(1999)
    module = importlib.import_module('framework.model.Quard_model.' + NAME + '.hier_postprocess')
    fps_module = importlib.import_module('pointnet2.pointnet2_utils')
    backend = importlib.import_module('pointnet2._ext')
    binding = MANIFEST['backend_binding']
    assert sha(fps_module.__file__) == binding['wrapper_sha256']
    assert sha(backend.__file__) == binding['binary_sha256']
    for entry in binding['native_sources']:
        assert sha(entry['path']) == entry['sha256']
    payload_path = Path(__file__).with_name('native_geometry.json')
    assert sha(payload_path) == MANIFEST['geometry_sha256']
    payload = json.loads(payload_path.read_text())
    partitioner = module.PointCloudPartitioner(cluster_layer_nums=[256, 64, 8]).cuda()

    def composed(coords):
        offsets = torch.tensor([0, len(coords)], dtype=torch.int32, device=coords.device)
        ids, _ = partitioner(coords, offsets)
        labels = [ids[0][0].long()]
        for level in (1, 2):
            labels.append(ids[level][0].long().gather(0, labels[-1]))
        return labels

    def groups(labels):
        labels = labels.detach().cpu()
        return tuple(sorted(tuple(torch.nonzero(labels == value).flatten().tolist())
                            for value in torch.unique(labels).tolist()))

    def digest_groups(value):
        return hashlib.sha256(json.dumps(value, separators=(',', ':')).encode()).hexdigest()

    with torch.no_grad():
        for scene in payload['cohort']:
            coords = torch.tensor(scene['coordinates'], dtype=torch.float32, device='cuda').contiguous()
            n = len(coords)
            assert n == scene['valid_superpoints'] and n >= 256
            assert hashlib.sha256(coords.cpu().numpy().tobytes()).hexdigest() == scene['coordinate_sha256']
            permutation = torch.arange(n - 1, -1, -1, device=coords.device)
            inverse = torch.argsort(permutation)
            assert torch.equal(coords[permutation][inverse], coords)
            original = composed(coords)
            identity = composed(coords.clone())
            changed = composed(coords[permutation].contiguous())
            original_first = int(fps_module.FurthestPointSampling.apply(coords.unsqueeze(0), 256)[0, 0])
            changed_first = int(fps_module.FurthestPointSampling.apply(coords[permutation].unsqueeze(0).contiguous(), 256)[0, 0])
            levels = []
            for level in range(3):
                old_groups = groups(original[level])
                identity_groups = groups(identity[level])
                changed_groups = groups(changed[level][inverse])
                levels.append({'level': level, 'original_groups': len(old_groups),
                    'relabeled_groups': len(changed_groups), 'identity_equal': old_groups == identity_groups,
                    'physical_co_membership_changed': old_groups != changed_groups,
                    'original_signature': digest_groups(old_groups),
                    'relabeled_signature': digest_groups(changed_groups)})
            result['records'].append({'scene_id': scene['scene_id'], 'valid_superpoints': n,
                'exact_inverse_permutation': True, 'levels': levels,
                'original_first_physical_row': original_first,
                'relabeled_first_physical_row': int(permutation[changed_first]),
                'first_seed_scope': 'Measured native binary;seed difference alone is not physical partition or task harm.'})
    result['controls_passed'] = all(level['identity_equal'] for scene in result['records'] for level in scene['levels'])
    result['execution_completed'] = True
    result['population_uncertainty'] = 'UNKNOWN;4 fixed TRAIN scene geometries, no checkpoint weights or mask readouts.'
except BaseException as error:
    result.update(error_type=type(error).__name__, error=str(error))
    raise
finally:
    try:
        save('native_relabel_geometry_result.json', result)
    finally:
        release()
