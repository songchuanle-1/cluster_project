"""Bounded unchanged native M95/HDS target-runtime validation, not training."""
import os
os.environ.update(CUDA_DEVICE_ORDER='PCI_BUS_ID', CUDA_VISIBLE_DEVICES='0', PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='1')
import copy, fcntl, hashlib, importlib, json, logging, math, signal, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
signal.alarm(600)
ROOT = Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b')
STAGE = ROOT.parent / 'pipeline/hds_server4_3c22e34d'
BASE = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
NAME = BASE + '_hds_canon_r1'
CONFIG = ROOT / 'configs/Quard/ctf_hcg_csort_hds_canon_r1' / (NAME + '.yaml')
UUID = 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
condition = sys.argv[1]
assert condition in ('baseline', 'candidate', 'transport')
assert subprocess.check_output(['hostname'], text=True).strip() == 'dl04-MS-7E06'
locks = []
for name in ('training', 'diagnostic', 'exclusive'):
    h = open('/tmp/cluster_project_gpu0_' + name + '.lock', 'a+b')
    fcntl.flock(h, fcntl.LOCK_EX | fcntl.LOCK_NB)
    locks.append(h)

def gpu():
    row = subprocess.check_output(['nvidia-smi', '-i', '0', '--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu', '--format=csv,noheader,nounits'], text=True).strip()
    assert row.split(',')[1].strip() == UUID
    contexts = subprocess.check_output(['nvidia-smi', '-i', '0', '--query-compute-apps=pid,used_memory', '--format=csv,noheader,nounits'], text=True).strip()
    assert all((int(line.split(',')[0]) == os.getpid() for line in contexts.splitlines())), 'Foreign GPU context; no eviction.'
    return dict(observed_at=datetime.now(timezone.utc).isoformat(), gpu=row, contexts=contexts)
before = gpu()
assert not before['contexts']
sys.path[:0] = [str(ROOT), str(ROOT / 'framework/lib')]
from tools import train as native_train
import torch, gorilla, numpy as np
from framework.dataset import build_dataset, build_dataloader
from torch.utils.data import DataLoader, Subset
torch.set_num_threads(1)
cfg = gorilla.Config.fromfile(str(CONFIG))
assert cfg.train.seed == 1999 and cfg.train.epochs == 50 and (cfg.lr_scheduler.max_iters == 70)
assert cfg.dataloader.train.batch_size == 2 and cfg.dataloader.train.num_workers == 4
cfg.model.data_root = cfg.data.train.data_root = cfg.data.val.data_root = '/home/songcl/data/data/'
gorilla.set_random_seed(1999)
dataset = build_dataset(copy.deepcopy(cfg.data.train), logging.getLogger('server4-frozen-native'))
if condition == 'transport':
    loader = DataLoader(Subset(dataset, [0, 60, 101, 124]), batch_size=2, shuffle=False, num_workers=4, persistent_workers=True, pin_memory=True, collate_fn=dataset.collate_fn)
    identity = []
    for batch in loader:
        identity.append(dict(scan_ids=batch['scan_ids'], ann_ids=batch['ann_ids']))
    assert len(identity) == 2 and identity[0]['scan_ids'] == ['scene0000_00', 'scene0002_00']
    assert identity[0]['ann_ids'] == [0, 1, 2, 3, 0, 1, 2, 3]
    del loader
    result = dict(condition=condition, passed=True, train_workers=4, persistent_workers=True, sharing_strategy=torch.multiprocessing.get_sharing_strategy(), batches=identity, cuda_initialized=torch.cuda.is_initialized(), optimizer_steps=0)
else:
    checkpoint = STAGE / 'frozen_m95.pth'
    assert hashlib.sha256(checkpoint.read_bytes()).hexdigest() == 'fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e'
    module = importlib.import_module('framework.model.Quard_model.' + (BASE if condition == 'baseline' else NAME))
    model = module.Network(**cfg.model)
    state = torch.load(checkpoint, map_location='cpu')['model']
    extra = set(state) - set(model.state_dict())
    assert extra <= {'text_encoder.embeddings.position_ids', 'text_encoder.embeddings.token_type_ids'}
    assert all((torch.equal(state[k], dict(model.named_buffers())[k]) for k in extra))
    model.load_state_dict({k: v for k, v in state.items() if k not in extra}, strict=True)
    del state
    torch.cuda.set_per_process_memory_fraction(0.25, 0)
    dummy = torch.zeros(1, device='cuda')
    torch.cuda.synchronize()
    own = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,gpu_uuid', '--format=csv,noheader,nounits'], text=True)
    assert any((int(row.split(',')[0]) == os.getpid() and UUID in row for row in own.splitlines()))
    del dummy
    model.cuda().train()
    FOREGROUND_TOKEN = '3c22e34d7205421387d37c5797f29a24'
    FOREGROUND_DEADLINE = '2026-10-16T09:59:08.113105+00:00'
    REMATERIALIZATION_SOURCE = '"""Rematerialize only pure pre-cluster encoder/decoder pairs."""\nfrom functools import wraps\nimport torch\nfrom torch.utils.checkpoint import checkpoint\n\n\ndef _wrap_forward(module):\n    original = module.forward\n\n    @wraps(original)\n    def forward(*args, **kwargs):\n        if not module.training or not torch.is_grad_enabled():\n            return original(*args, **kwargs)\n\n        def invoke(*values):\n            return original(*values, **kwargs)\n\n        return checkpoint(invoke, *args, use_reentrant=False,\n                          preserve_rng_state=True)\n\n    module.forward = forward\n\n\ndef install_prefix_rematerialization(decoder):\n    if getattr(decoder, \'_prefix_rematerialization_installed\', False):\n        raise RuntimeError(\'Prefix rematerialization is already installed.\')\n    indices = [i for i, layer in enumerate(decoder.encoder_layers)\n               if not layer.use_cluster]\n    if not indices or indices != list(range(len(indices))):\n        raise ValueError(\'Expected a nonempty contiguous pure prefix.\')\n    if len(indices) == len(decoder.encoder_layers):\n        raise ValueError(\'The cluster-bearing final layer must remain outside.\')\n    names = []\n    for index in indices:\n        _wrap_forward(decoder.encoder_layers[index])\n        _wrap_forward(decoder.decoder_layers[index])\n        names.extend([\'encoder_layers.\' + str(index),\n                      \'decoder_layers.\' + str(index)])\n    decoder._prefix_rematerialization_installed = True\n    return names\n'
    observations = []
    observe = lambda stage: dict(stage=stage, **gpu())
    'Actual native prefix arguments, paired plain/rematerialized gradients.'
    import gc
    helper = {}
    exec(compile(REMATERIALIZATION_SOURCE, '<frozen-prefix-rematerialization>', 'exec'), helper)
    gorilla.set_random_seed(1999)
    batches = list(DataLoader(Subset(dataset, [0, 60, 101, 124]), batch_size=2, shuffle=False, num_workers=0, collate_fn=dataset.collate_fn))
    expected = [(['scene0000_00', 'scene0002_00'], [0, 1, 2, 3, 0, 1, 2, 3], [0, 667, 2996]), (['scene0003_00', 'scene0004_00'], [0, 1, 2, 3, 36, 37, 38, 39], [0, 406, 1847])]
    for entry, (scans, anns, offsets) in zip(batches, expected):
        assert entry['scan_ids'] == scans and entry['ann_ids'] == anns
        assert entry['batch_offsets'].tolist() == offsets
    prefix = [i for i, layer in enumerate(model.dec.encoder_layers) if not layer.use_cluster]
    assert prefix == [0, 1, 2, 3, 4]
    modules = {}
    for index in prefix:
        modules['encoder_layers.' + str(index)] = model.dec.encoder_layers[index]
        modules['decoder_layers.' + str(index)] = model.dec.decoder_layers[index]
    captures = []
    current_pair = None
    handles = []

    def capture(name):

        def hook(module, args):
            values = tuple((x.detach().cpu().clone() if torch.is_tensor(x) else copy.deepcopy(x) for x in args))
            captures.append({'pair': current_pair, 'name': name, 'args': values, 'cpu_rng': torch.get_rng_state().clone(), 'cuda_rng': torch.cuda.get_rng_state().clone()})
        return hook
    for name, entry in modules.items():
        handles.append(entry.register_forward_pre_hook(capture(name)))
    try:
        for current_pair, entry in enumerate(batches):
            assert (datetime.fromisoformat(FOREGROUND_DEADLINE) - datetime.now(timezone.utc)).total_seconds() > 120
            gorilla.set_random_seed(1999)
            with torch.no_grad():
                captured_loss, _ = model(copy.deepcopy(entry), mode='loss')
            assert torch.isfinite(captured_loss).all()
            del captured_loss
    finally:
        for handle in handles:
            handle.remove()
    assert len(captures) == 20
    originals = {name: entry.forward for name, entry in modules.items()}
    installed = helper['install_prefix_rematerialization'](model.dec)
    assert set(installed) == set(modules)
    records = []

    def flatten(value):
        if torch.is_tensor(value):
            return [value]
        if isinstance(value, (tuple, list)):
            return [item for entry in value for item in flatten(entry)]
        if isinstance(value, dict):
            return [item for key in sorted(value) for item in flatten(value[key])]
        return []

    def replay(record, checkpointed):
        model.zero_grad(set_to_none=True)
        values = []
        for value in record['args']:
            if torch.is_tensor(value):
                value = value.to('cuda').detach().clone()
                if value.is_floating_point():
                    value.requires_grad_(True)
            else:
                value = copy.deepcopy(value)
            values.append(value)
        torch.set_rng_state(record['cpu_rng'])
        torch.cuda.set_rng_state(record['cuda_rng'])
        function = modules[record['name']] if checkpointed else originals[record['name']]
        outputs = function(*values)
        tensors = flatten(outputs)
        assert tensors and all((torch.isfinite(x).all() for x in tensors))
        scalar = sum(((value * torch.linspace(-1, 1, value.numel(), dtype=value.dtype, device=value.device).reshape(value.shape)).sum() / max(value.numel(), 1) for value in tensors if value.is_floating_point()))
        scalar.backward()
        torch.cuda.synchronize()
        result = {'outputs': [x.detach().cpu().clone() for x in tensors], 'inputs': [None if not torch.is_tensor(x) or x.grad is None else x.grad.detach().cpu().clone() for x in values], 'parameters': {name: None if p.grad is None else p.grad.detach().cpu().clone() for name, p in modules[record['name']].named_parameters()}}
        del values, outputs, tensors, scalar
        model.zero_grad(set_to_none=True)
        return result

    def compare(left, right):
        assert type(left) == type(right)
        if left is None:
            return 0.0
        if torch.is_tensor(left):
            assert left.shape == right.shape and torch.isfinite(left).all() and torch.isfinite(right).all()
            return float((left - right).abs().max()) if left.numel() else 0.0
        if isinstance(left, list):
            assert len(left) == len(right)
            return max([compare(a, b) for a, b in zip(left, right)] + [0.0])
        assert left.keys() == right.keys()
        return max([compare(left[k], right[k]) for k in left] + [0.0])
    for captured in captures:
        assert (datetime.fromisoformat(FOREGROUND_DEADLINE) - datetime.now(timezone.utc)).total_seconds() > 120
        plain = replay(captured, False)
        remat = replay(captured, True)
        errors = {key: compare(plain[key], remat[key]) for key in plain}
        fingerprints = [hashlib.sha256(x.numpy().tobytes()).hexdigest() if torch.is_tensor(x) else None for x in captured['args']]
        records.append({'pair': captured['pair'], 'module': captured['name'], 'errors': errors, 'passed': max(errors.values()) <= 1e-06, 'argument_sha256': fingerprints, 'argument_shapes': [list(x.shape) if torch.is_tensor(x) else None for x in captured['args']]})
        del plain, remat
        gc.collect()
        torch.cuda.empty_cache()
    observations.append(observe('after_native_module_controls'))
    result = {'observed_at': datetime.now(timezone.utc).isoformat(), 'token': FOREGROUND_TOKEN, 'revision': 2, 'check_count': len(records), 'passed': sum((r['passed'] for r in records)), 'failures': [r for r in records if not r['passed']], 'records': records, 'max_errors': {key: max((r['errors'][key] for r in records)) for key in ('outputs', 'inputs', 'parameters')}, 'native_capture_forwards': 2, 'native_module_forwards': 40, 'native_module_backwards': 40, 'full_model_backward': False, 'installed_modules': installed, 'allocator_fraction': 0.25, 'train_groups': [0, 60, 101, 124], 'scenes': 4, 'expressions': 16, 'optimizer_steps': 0, 'new_training': False, 'observations': observations, 'scope': 'Actual frozen native prefix-module arithmetic/gradient equivalence only, not full-model native backward or resource admission.'}
    print('HIER_NATIVE_RESULT=' + json.dumps(result))
    raise SystemExit(0)
result.update(observed_at=datetime.now(timezone.utc).isoformat(), pid=os.getpid(), before=before, scope='Fixed four TRAIN scenes and one VAL expression resource-only. No training/efficacy/whole-training-memory guarantee or reconstructing the failed source batch.')
print('HDS_SERVER4_NATIVE_RESULT=' + json.dumps(result), flush=True)
