"""CPU-only native TRAIN incidence capture; no prediction or efficacy claims."""
import argparse
import hashlib
import importlib.util
import json
import logging
import os
from pathlib import Path
import sys


def components(edges, labels):
    boundary = set()
    for a, b in edges:
        if labels[a] != labels[b]:
            boundary.update((int(a), int(b)))
    adjacency = {v: set() for v in boundary}
    for a, b in edges:
        if a in boundary and b in boundary:
            adjacency[a].add(int(b))
            adjacency[b].add(int(a))
    remaining, result = set(boundary), []
    while remaining:
        stack = [min(remaining)]
        remaining.remove(stack[0])
        members = []
        while stack:
            vertex = stack.pop()
            members.append(vertex)
            for other in sorted(adjacency[vertex] & remaining):
                remaining.remove(other)
                stack.append(other)
        members.sort()
        count = sum(bool(labels[v]) for v in members)
        assert 0 < count < len(members)
        result.append(dict(members=members, size=len(members), positives=count))
    return result


def controls():
    assert components([], [False]) == []
    assert components([(0, 1)], [True, True]) == []
    separate = components([(0, 1), (2, 3)], [True, False, False, True])
    assert [r["size"] for r in separate] == [2, 2]
    # Same-label edges connect crossing-edge endpoints in the induced graph.
    joined = components([(0, 1), (2, 3), (1, 2)], [True, False, False, True])
    assert joined == [dict(members=[0, 1, 2, 3], size=4, positives=2)]
    assert components([(b, a) for a, b in [(0, 1), (2, 3)]],
                      [False, True, True, False]) == separate


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--data-root")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    controls()
    if args.self_test:
        print("PASS: empty, homogeneous, disconnected, induced-edge, complement controls")
        return
    os.environ.update(CUDA_VISIBLE_DEVICES="", OMP_NUM_THREADS="1",
                      OPENBLAS_NUM_THREADS="1")
    sys.path[:0] = [str(args.root), str(args.root / "framework/lib")]
    import torch
    import gorilla
    from framework.dataset import build_dataset, build_dataloader
    helper = args.root / ("framework/model/Quard_model/"
        "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bca/"
        "boundary_assignment.py")
    spec = importlib.util.spec_from_file_location("boundary_helper", helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    torch.set_num_threads(1)
    gorilla.set_random_seed(1999)
    cfg = gorilla.Config.fromfile(str(args.config))
    cfg.data.train.data_root = args.data_root
    dataset = build_dataset(cfg.data.train, logging.getLogger("components"))
    loader = build_dataloader(dataset, batch_size=2, num_workers=0,
                              persistent_workers=False)
    rows, graph_hashes = [], []
    for step, batch in enumerate(loader):
        graphs = module.scene_contacts(batch["voxel_coords"], batch["p2v_map"],
                                       batch["superpoints"], batch["batch_offsets"])
        offset = 0
        for scene, (edges, length) in enumerate(zip(graphs, batch["scenes_len"].tolist())):
            graph_hashes.append(dict(step=step, scene=batch["scan_ids"][scene],
                sha256=hashlib.sha256(edges.tobytes()).hexdigest()))
            for b in range(offset, offset + length):
                labels = batch["gt_spmasks"][b].flatten().bool().tolist()
                groups = components(edges.tolist(), labels)
                rows.append(dict(step=step, scene=batch["scan_ids"][scene],
                    ann_id=int(batch["ann_ids"][b]),
                    object_ids=[int(v) for v in batch["object_idss"][b]],
                    components=groups, component_count=len(groups),
                    boundary_n=sum(g["size"] for g in groups),
                    boundary_k=sum(g["positives"] for g in groups),
                    missing_fields=[]))
            offset += length
        assert offset == len(batch["gt_spmasks"])
        print(f"Captured batch {step + 1}/16; expressions={len(rows)}", flush=True)
        if step == 15:
            break
    summary = dict(batches=step + 1, expressions=len(rows),
        scenes=len({r["scene"] for r in rows}),
        empty=sum(r["component_count"] == 0 for r in rows),
        connected=sum(r["component_count"] == 1 for r in rows),
        disconnected=sum(r["component_count"] > 1 for r in rows),
        missing=0, controls="PASS")
    report = dict(summary=summary, rows=rows, graph_hashes=graph_hashes,
        sources={str(p): digest(p) for p in
                 [Path(__file__), helper, args.config,
                  args.root / "framework/dataset/scannetv2.py"]},
        scope="16 native augmented TRAIN batches, seed1999, workers0. "
              "Bounded incidence only, not full-epoch prevalence or efficacy. "
              "No model forward, selected logits, full-loss gradients or admission.")
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
