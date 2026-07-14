#!/usr/bin/env python
"""
Benchmark _qcond_refine performance (old vs new implementation)
"""
import torch
import time
import sys

sys.path.insert(0, '/data/songcl/3dres/Cluster_project2/Cluster')

from framework.model.Quard_model.model_base1_quard2_c2f_enc_lite_qcond.hier_postprocess import C2F_ClusterAttn_QCond


def create_test_data(B=4, N=1000, Q=32, C=256, num_scales=3, cluster_sizes=[256, 64, 8]):
    """Create realistic test data"""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    point_feats = torch.randn(B, N, C, device=device)
    query = torch.randn(B, Q, C, device=device)
    point_mask = torch.zeros(B, N, dtype=torch.bool, device=device)

    # Create cluster_feats_list
    cluster_feats_list = []
    cluster_ids_list = []
    child_cluster_maps = []
    cluster_point_lists = []

    for lvl, K in enumerate(cluster_sizes):
        cluster_feats = torch.randn(B, K, C, device=device)
        cluster_feats_list.append(cluster_feats)

        # Random cluster assignments
        cluster_ids = torch.randint(0, K, (B, N), device=device)
        cluster_ids_list.append(cluster_ids)

        # Build point lists
        point_lists = []
        for b in range(B):
            batch_point_lists = []
            for k in range(K):
                mask = cluster_ids[b] == k
                indices = mask.nonzero(as_tuple=True)[0]
                batch_point_lists.append(indices)
            point_lists.append(batch_point_lists)
        cluster_point_lists.append(point_lists)

        # Build child cluster maps (except for last level)
        if lvl < num_scales - 1:
            maps = []
            for b in range(B):
                mapping = {}
                parent_K = cluster_sizes[lvl + 1]
                for pk in range(parent_K):
                    # Each parent has ~K/parent_K children
                    children = list(range(pk * (K // parent_K), (pk + 1) * (K // parent_K)))
                    mapping[pk] = children
                maps.append(mapping)
            child_cluster_maps.append(maps)

    # Create all_selected (simulating C2F routing output)
    all_selected = []
    for lvl, K in enumerate(cluster_sizes):
        topk = min(8, K // 2)
        selected = torch.randint(0, K, (B, Q, topk), device=device)
        all_selected.append(selected)

    return (point_feats, query, point_mask, cluster_feats_list,
            cluster_ids_list, child_cluster_maps, cluster_point_lists, all_selected)


def benchmark_old_style():
    """Simulate old triple-loop implementation"""
    print("Benchmarking OLD implementation (triple loop + .item())...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    B, N, Q, C = 4, 1000, 32, 256
    cluster_sizes = [256, 64, 8]
    num_scales = 3

    # Create test data
    data = create_test_data(B, N, Q, C, num_scales, cluster_sizes)
    point_feats, query, point_mask, cluster_feats_list, cluster_ids_list, child_cluster_maps, cluster_point_lists, all_selected = data

    # Warmup
    for _ in range(3):
        for lvl in range(num_scales):
            sel = all_selected[num_scales - 1 - lvl]
            pl_lvl = cluster_point_lists[lvl]
            topk = sel.shape[2]

            bc_batch_idx = []
            bc_point_idx = []

            for b in range(B):
                Kb = len(pl_lvl[b])
                for k_idx in range(topk):
                    for q_idx in range(Q):
                        cid = sel[b, q_idx, k_idx].item()  # Old style
                        if cid < Kb:
                            bc_batch_idx.append(b)
                            bc_point_idx.append(pl_lvl[b][cid])

    # Measure
    if torch.cuda.is_available():
        torch.cuda.synchronize()

    start = time.perf_counter()
    for _ in range(10):
        for lvl in range(num_scales):
            sel = all_selected[num_scales - 1 - lvl]
            pl_lvl = cluster_point_lists[lvl]
            topk = sel.shape[2]

            bc_batch_idx = []
            bc_point_idx = []

            for b in range(B):
                Kb = len(pl_lvl[b])
                for k_idx in range(topk):
                    for q_idx in range(Q):
                        cid = sel[b, q_idx, k_idx].item()
                        if cid < Kb:
                            bc_batch_idx.append(b)
                            bc_point_idx.append(pl_lvl[b][cid])

    if torch.cuda.is_available():
        torch.cuda.synchronize()

    old_time = (time.perf_counter() - start) / 10
    print(f"  OLD time: {old_time*1000:.2f} ms")
    return old_time


def benchmark_new():
    """Benchmark new optimized implementation"""
    print("Benchmarking NEW implementation (unique() + minimal .item())...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Initialize model
    model = C2F_ClusterAttn_QCond(
        d_model=256,
        nhead=8,
        cluster_layer_nums=[256, 64, 8],
        per_layer_topk_list=[4, 6, 8],
        dropout=0.0
    ).to(device)

    B, N, Q, C = 4, 1000, 32, 256
    cluster_sizes = [256, 64, 8]
    num_scales = 3

    # Create test data
    data = create_test_data(B, N, Q, C, num_scales, cluster_sizes)
    point_feats, query, point_mask, cluster_feats_list, cluster_ids_list, child_cluster_maps, cluster_point_lists, all_selected = data

    # Warmup
    with torch.no_grad():
        for _ in range(3):
            refined_list = model._qcond_refine(
                point_feats, query, cluster_point_lists,
                all_selected, point_mask
            )

    # Measure
    if torch.cuda.is_available():
        torch.cuda.synchronize()

    start = time.perf_counter()
    with torch.no_grad():
        for _ in range(10):
            refined_list = model._qcond_refine(
                point_feats, query, cluster_point_lists,
                all_selected, point_mask
            )

    if torch.cuda.is_available():
        torch.cuda.synchronize()

    new_time = (time.perf_counter() - start) / 10
    print(f"  NEW time: {new_time*1000:.2f} ms")
    return new_time


if __name__ == '__main__':
    print("="*60)
    print("QCond Performance Benchmark")
    print("="*60)
    print(f"Device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
    print()

    old_time = benchmark_old_style()
    print()
    new_time = benchmark_new()
    print()

    print("="*60)
    print("RESULTS")
    print("="*60)
    print(f"Speedup: {old_time/new_time:.2f}x")
    print(f"Time saved: {(old_time - new_time)*1000:.2f} ms per call")
    print()
    print("Expected training impact (B=4, Q=128, typical config):")
    print(f"  OLD: ~{old_time * (128/32) * 1000:.0f} ms/step")
    print(f"  NEW: ~{new_time * (128/32) * 1000:.0f} ms/step")
    print(f"  Improvement: ~{(old_time - new_time) * (128/32) * 1000:.0f} ms/step")
