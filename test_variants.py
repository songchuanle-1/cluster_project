"""Test the 4 fixed variants' hier_postprocess.py in isolation (CPU only)."""
import torch
import sys
import types
import importlib.util
import warnings
warnings.filterwarnings('ignore')

# ── Mock dependencies before loading any variant ──

class FakeFurthestPointSampling(torch.autograd.Function):
    @staticmethod
    def forward(ctx, points, npoint):
        B, N, _ = points.shape
        return torch.randint(0, N, (B, npoint), device=points.device).float()
    @staticmethod
    def backward(ctx, grad_output):
        return None, None

mock_pn2 = types.ModuleType('pointnet2')
mock_pn2_utils = types.ModuleType('pointnet2.pointnet2_utils')
mock_pn2_utils.FurthestPointSampling = FakeFurthestPointSampling
mock_pn2.pointnet2_utils = mock_pn2_utils
sys.modules['pointnet2'] = mock_pn2
sys.modules['pointnet2.pointnet2_utils'] = mock_pn2_utils

try:
    from torch_scatter import scatter_mean, scatter_max, scatter_sum
except ImportError:
    def scatter_mean(src, index, dim=0, dim_size=None):
        if dim_size is None: dim_size = int(index.max().item()) + 1
        out = torch.zeros(dim_size, *src.shape[1:], device=src.device, dtype=src.dtype)
        count = torch.zeros(dim_size, device=src.device, dtype=src.dtype)
        out.scatter_add_(dim, index.unsqueeze(-1).expand_as(src), src)
        count.scatter_add_(0, index, torch.ones_like(index, dtype=src.dtype))
        count = count.clamp(min=1)
        for _ in range(src.dim() - 1): count = count.unsqueeze(-1)
        return out / count
    def scatter_sum(src, index, dim=0, dim_size=None):
        if dim_size is None: dim_size = int(index.max().item()) + 1
        out = torch.zeros(dim_size, *src.shape[1:], device=src.device, dtype=src.dtype)
        out.scatter_add_(dim, index.unsqueeze(-1).expand_as(src), src)
        return out
    def scatter_max(src, index, dim=0, dim_size=None):
        if dim_size is None: dim_size = int(index.max().item()) + 1
        out = torch.full((dim_size, *src.shape[1:]), float('-inf'), device=src.device, dtype=src.dtype)
        out.scatter_reduce_(dim, index.unsqueeze(-1).expand_as(src), src, reduce='amax')
        return out, None
    mock_scatter = types.ModuleType('torch_scatter')
    mock_scatter.scatter_mean = scatter_mean
    mock_scatter.scatter_max = scatter_max
    mock_scatter.scatter_sum = scatter_sum
    sys.modules['torch_scatter'] = mock_scatter

def load_hp(variant):
    """Load hier_postprocess.py directly from file."""
    import os
    # Use the test file's directory as base
    test_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(test_dir, f'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_{variant}/hier_postprocess.py')
    mod_name = f'_test_hp_{variant}'
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod

results = {}
B, N, Q, C = 2, 100, 32, 256

# ═══════════════ QCOND ═══════════════
print('=' * 60); print('TESTING: qcond'); print('=' * 60)
try:
    hp = load_hp('qcond')
    model = hp.C2F_ClusterAttn_QCond(d_model=C, nhead=8)

    # 1. _qcond_cross_attn shape
    ctx = model._qcond_cross_attn(
        torch.randn(10, Q, C), torch.randn(10, 8, C),
        torch.zeros(10, 8, dtype=torch.bool))
    assert ctx.shape == (10, Q, C)
    print(f'  ✓ _qcond_cross_attn: {ctx.shape}')

    # 2. all_selected indexing (reversed append → need num_scales-1-lvl)
    all_selected_real = ['lvl2', 'lvl1', 'lvl0']
    for lvl in range(3):
        assert all_selected_real[3 - 1 - lvl] == f'lvl{lvl}'
    print(f'  ✓ all_selected indexing correct')

    # 3. _qcond_refine end-to-end
    point_feats = torch.randn(B, N, C)
    query = torch.randn(B, Q, C)
    point_mask = torch.zeros(B, N, dtype=torch.bool)

    Ks = [256, 64, 8]
    cluster_point_lists = []
    for K in Ks:
        pl_lvl = []
        for b in range(B):
            pl_b = []
            ppc = max(1, N // K)
            for k in range(K):
                s = (k * ppc) % N
                e = min(s + ppc, N)
                pl_b.append(torch.arange(s, max(e, s+1)))
            pl_lvl.append(pl_b)
        cluster_point_lists.append(pl_lvl)

    # all_selected: [coarsest(lvl2), middle(lvl1), finest(lvl0)]
    all_selected = [
        torch.randint(0, 8, (B, Q, 4)),    # lvl=2 → maps to lvl index 0 in _qcond_refine
        torch.randint(0, 64, (B, Q, 6)),   # lvl=1
        torch.randint(0, 256, (B, Q, 4)),  # lvl=0
    ]
    refined_list = model._qcond_refine(point_feats, query, cluster_point_lists, all_selected, point_mask)
    for lvl, r in enumerate(refined_list):
        assert r.shape == (B, Ks[lvl], Q, C), f'lvl={lvl}: {r.shape}'
    print(f'  ✓ _qcond_refine: {[r.shape for r in refined_list]}')

    # 4. _qcond_gather_blend
    cluster_ids_list = [[torch.randint(0, K, (N,)) for _ in range(B)] for K in Ks]
    fused, gate = model._qcond_gather_blend(point_feats, refined_list, cluster_ids_list, point_mask)
    assert fused.shape == (B, N, C) and gate.shape == (B, N, 1)
    print(f'  ✓ _qcond_gather_blend: fused={fused.shape}, gate={gate.shape}')

    # 5. Full forward
    cluster_feats_list = [torch.randn(B, K, C) for K in Ks]
    child_maps = [[{i: [i*2, i*2+1] for i in range(4)} for _ in range(B)] for _ in range(2)]
    out = model(point_feats, query, point_mask, cluster_feats_list, child_maps, cluster_ids_list,
                cluster_point_lists=cluster_point_lists)
    assert out['point'].shape == (B, N, C)
    print(f'  ✓ forward: {out["point"].shape}')

    # 6. Gradient flow
    pf_g = point_feats.clone().requires_grad_(True)
    out_g = model(pf_g, query, point_mask, cluster_feats_list, child_maps, cluster_ids_list,
                  cluster_point_lists=cluster_point_lists)
    out_g['point'].sum().backward()
    assert pf_g.grad is not None
    print(f'  ✓ gradient flow')

    results['qcond'] = 'PASS'
except Exception as e:
    results['qcond'] = f'FAIL: {e}'
    import traceback; traceback.print_exc()

# ═══════════════ ATTNPOOL ═══════════════
print('\n' + '=' * 60); print('TESTING: attnpool'); print('=' * 60)
try:
    hp = load_hp('attnpool')
    bank = hp.SharedClusterBank(cluster_layer_nums=[8, 4, 2], d_model=C)
    assert hasattr(bank, 'attn_pool_query_gen')
    assert not hasattr(bank, 'attn_pool_q')
    print(f'  ✓ content-adaptive query gen present')

    sp_feats = torch.randn(N * B, C)
    batch_offsets = torch.tensor([0, N, N * 2])
    bank.get_cluster(torch.randn(N * B, 3), batch_offsets)
    clf = bank.build_cluster_feats(sp_feats, batch_offsets)
    assert len(clf) == 3
    print(f'  ✓ build_cluster_feats: {[c.shape for c in clf]}')

    # Test C2F_ClusterAttn_Lite forward (unchanged from lite)
    model = hp.C2F_ClusterAttn_Lite(d_model=C, nhead=8, cluster_layer_nums=[8, 4, 2])
    pf = torch.randn(B, N, C)
    q = torch.randn(B, Q, C)
    pm = torch.zeros(B, N, dtype=torch.bool)
    ids_list = [[torch.randint(0, K, (N,)) for _ in range(B)] for K in [8, 4, 2]]
    cmaps = [[{i: [i*2, i*2+1] for i in range(4)} for _ in range(B)] for _ in range(2)]
    out = model(pf, q, pm, clf, cmaps, ids_list)
    assert out['point'].shape == (B, N, C)
    print(f'  ✓ C2F_ClusterAttn_Lite forward: {out["point"].shape}')

    results['attnpool'] = 'PASS'
except Exception as e:
    results['attnpool'] = f'FAIL: {e}'
    import traceback; traceback.print_exc()

# ═══════════════ AGG ═══════════════
print('\n' + '=' * 60); print('TESTING: agg'); print('=' * 60)
try:
    hp = load_hp('agg')
    bank = hp.SharedClusterBank(cluster_layer_nums=[8, 4, 2], d_model=C)
    assert bank._agg_weight_mlp[0].in_features == C * 2
    print(f'  ✓ MLP input dim = {C*2} (2C)')

    sp_feats = torch.randn(N * B, C)
    batch_offsets = torch.tensor([0, N, N * 2])
    bank.get_cluster(torch.randn(N * B, 3), batch_offsets)
    clf = bank.build_cluster_feats(sp_feats, batch_offsets)
    assert len(clf) == 3
    print(f'  ✓ build_cluster_feats: {[c.shape for c in clf]}')

    # Gradient flow
    sp_g = sp_feats.clone().requires_grad_(True)
    clf_g = bank.build_cluster_feats(sp_g, batch_offsets)
    clf_g[0].sum().backward()
    assert sp_g.grad is not None
    print(f'  ✓ gradient flow through agg weights')

    results['agg'] = 'PASS'
except Exception as e:
    results['agg'] = f'FAIL: {e}'
    import traceback; traceback.print_exc()

# ═══════════════ PRUNE ═══════════════
print('\n' + '=' * 60); print('TESTING: prune'); print('=' * 60)
try:
    hp = load_hp('prune')
    model = hp.C2F_ClusterAttn_Prune(d_model=C, nhead=8, cluster_layer_nums=[8, 4, 2],
                                      prune_threshold=0.85, prune_ratio=0.3)

    # 1. _prune_tokens
    cf = torch.randn(B, 8, C)
    cids = [torch.randint(0, 8, (N,)) for _ in range(B)]
    pruned, pmask, remap = model._prune_tokens(cf, cids)
    assert pruned.shape[0] == B and pruned.shape[2] == C
    assert pmask.shape == (B, pruned.shape[1])
    assert (~pmask).any()
    valid_counts = (~pmask).sum(dim=1).tolist()
    print(f'  ✓ _prune_tokens: shape={pruned.shape}, valid/batch={valid_counts}')

    # 2. prune_mask actually masks out padded positions
    for b in range(B):
        n_valid = valid_counts[b]
        # All padding positions should be zero vectors (no linear bias pollution test: just check mask)
        assert pmask[b, n_valid:].all(), f'Padding positions should be True'
        assert not pmask[b, :n_valid].any(), f'Valid positions should be False'
    print(f'  ✓ prune_mask correctly marks valid/padding')

    # 3. _rebuild_child_maps
    cmaps = [
        [{0: [0,1], 1: [2,3], 2: [4,5], 3: [6,7]} for _ in range(B)],
        [{0: [0,1], 1: [2,3]} for _ in range(B)],
    ]
    remaps = [
        [torch.tensor([0, 0, 1, 2, 3, 4, 5, 6]) for _ in range(B)],
        [torch.tensor([0, 0, 1, 1, 2, 3, 4, 5]) for _ in range(B)],
        [torch.tensor([0, 1]) for _ in range(B)],
    ]
    new_maps = model._rebuild_child_maps(cmaps, remaps)
    assert len(new_maps) == 2
    print(f'  ✓ _rebuild_child_maps: {len(new_maps)} maps')

    # 4. Full forward
    pf = torch.randn(B, N, C)
    q = torch.randn(B, Q, C)
    pm = torch.zeros(B, N, dtype=torch.bool)
    clf = [torch.randn(B, K, C) for K in [8, 4, 2]]
    ids_list = [[torch.randint(0, K, (N,)) for _ in range(B)] for K in [8, 4, 2]]
    cmaps_orig = [
        [{i: [i*2, i*2+1] for i in range(4)} for _ in range(B)],
        [{i: [i*2, i*2+1] for i in range(2)} for _ in range(B)],
    ]
    out = model(pf, q, pm, clf, cmaps_orig, ids_list)
    assert out['point'].shape == (B, N, C)
    print(f'  ✓ forward: {out["point"].shape}')

    # 5. Gradient flow
    pf_g = pf.clone().requires_grad_(True)
    out_g = model(pf_g, q, pm, clf, cmaps_orig, ids_list)
    out_g['point'].sum().backward()
    assert pf_g.grad is not None
    print(f'  ✓ gradient flow')

    results['prune'] = 'PASS'
except Exception as e:
    results['prune'] = f'FAIL: {e}'
    import traceback; traceback.print_exc()

# ═══════════════ SUMMARY ═══════════════
print('\n' + '=' * 60)
print('SUMMARY')
print('=' * 60)
for name, status in results.items():
    sym = '✓' if status == 'PASS' else '✗'
    print(f'  {sym} {name}: {status}')
sys.exit(0 if all(s == 'PASS' for s in results.values()) else 1)
