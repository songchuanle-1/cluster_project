"""CPU-only physical-contact diagnostic on existing frozen validation banks."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES="", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def graph(xyz, sp):
    vox = (xyz * 50 - (xyz * 50).min(0)).astype(np.int64)
    unique, inverse = np.unique(vox, axis=0, return_inverse=True)
    pairs, count = np.unique(np.stack([inverse, sp], axis=1), axis=0, return_counts=True)
    order = np.lexsort((pairs[:, 1], -count, pairs[:, 0]))
    ranked = pairs[order]
    _, first = np.unique(ranked[:, 0], return_index=True)
    owner = ranked[first, 1]
    ambiguous = int((np.bincount(pairs[:, 0]) > 1).sum())
    dims = unique.max(0) + 2
    encode = lambda a: (a[:, 0] * dims[1] + a[:, 1]) * dims[2] + a[:, 2]
    keys = encode(unique)
    edges = []
    for axis in range(3):
        shifted = unique.copy()
        shifted[:, axis] += 1
        wanted = encode(shifted)
        index = np.searchsorted(keys, wanted)
        safe = index.clip(max=len(keys)-1)
        good = (index < len(keys)) & (keys[safe] == wanted)
        a, b = owner[good], owner[safe[good]]
        edges.append(np.sort(np.stack([a[a != b], b[a != b]], axis=1), axis=1))
    edges = np.unique(np.concatenate(edges), axis=0)
    n = int(sp.max())+1
    a, b = edges.T
    adj = csr_matrix((np.ones(2*len(a)), (np.r_[a,b], np.r_[b,a])), shape=(n,n))
    return edges, adj, dict(voxels=len(unique), ambiguous_voxels=ambiguous, edges=len(edges))


def components(adj, mask):
    return int(connected_components(adj[mask][:, mask], directed=False)[0]) if mask.any() else 0


def iou(a, b):
    return float((a & b).sum() / max(1, (a | b).sum()))


def main():
    torch.set_num_threads(1)
    toy = csr_matrix(np.array([[0,1,0],[1,0,0],[0,0,0]]))
    assert components(toy, np.ones(3,dtype=bool)) == 2
    assert components(toy, np.zeros(3,dtype=bool)) == 0
    assert iou(np.array([1,0],bool),np.array([1,1],bool)) == .5
    root = Path("/tmp/cluster_semantic_projection_20260912/full")
    output = Path("/tmp/boundary_adjacency_audit_20260914.json")
    assert not output.exists()
    manifest = json.loads((root/"summary.json").read_text())
    rng = np.random.default_rng(1999)
    rows, graphs = [], {}
    for scene in sorted({r["scene_id"] for r in manifest["rows"]}):
        raw = Path("/home/songcl/data/data/scannetv2/val")/(scene+"_refer.pth")
        xyz, _, sp, _, _ = torch.load(raw,map_location="cpu",weights_only=False)
        _, mapping = np.unique(sp,return_inverse=True)
        edges, adj, info = graph(np.asarray(xyz),mapping)
        info["raw_sha256"] = sha(raw)
        graphs[scene] = info
        for item in [r for r in manifest["rows"] if r["scene_id"] == scene]:
            p = root/item["artifact"]
            assert sha(p) == item["artifact_sha256"]
            bank = torch.load(p,map_location="cpu",weights_only=False)
            t = bank["tensors"]
            assert np.array_equal(mapping,t["superpoints"].numpy().ravel())
            gt = t["gt_spmask"].numpy().ravel() > .5
            hard = t["mask_logits"].numpy() >= 0
            scores = np.diff(t["indis_logits"].numpy(),axis=1).ravel()
            s = int(scores.argmax())
            oracle = max(iou(a,gt) for a in hard)
            pred = hard[s]
            boundary = np.zeros(len(gt),bool)
            crossing = edges[gt[edges[:,0]] != gt[edges[:,1]]]
            boundary[crossing.ravel()] = True
            region = boundary | (adj @ boundary > 0)
            error = pred != gt
            corrected = pred.copy()
            corrected[region] = gt[region]
            random_iou = []
            for _ in range(100):
                pick = rng.choice(len(gt),int(region.sum()),replace=False)
                control = pred.copy()
                control[pick] = gt[pick]
                random_iou.append(iou(control,gt))
            value = iou(pred,gt)
            rows.append(dict(**bank["identity"],artifact_sha256=item["artifact_sha256"],
                selected_iou=value,oracle_iou=oracle,
                stratum="success" if value>.5 else "recoverable" if oracle>.5 else "limited",
                sp_count=len(gt),gt_count=int(gt.sum()),pred_count=int(pred.sum()),
                errors=int(error.sum()),fp=int((pred & ~gt).sum()),fn=int((~pred & gt).sum()),
                boundary_count=int(boundary.sum()),region_count=int(region.sum()),
                boundary_errors=int((error & boundary).sum()),region_errors=int((error & region).sum()),
                gt_components=components(adj,gt),pred_components=components(adj,pred),
                corrected_iou=iou(corrected,gt),random_corrected_iou=float(np.mean(random_iou)),
                random_recovery=float(np.mean(np.array(random_iou)>.5))))
        print("scene",scene,"complete",flush=True)
    assert len(rows)==284 and len(graphs)==71
    summaries = {}
    for group in ("success","recoverable","limited"):
        sub = [r for r in rows if r["stratum"]==group]
        scenes = sorted({r["scene_id"] for r in sub})
        fields = {
            "boundary_oracle_recovery":lambda r: r["corrected_iou"]>.5,
            "random_oracle_recovery":lambda r: r["random_recovery"],
            "excess_components":lambda r:r["pred_components"]>r["gt_components"],
            "region_error_fraction":lambda r:r["region_errors"]/max(r["errors"],1),
            "region_size_fraction":lambda r:r["region_count"]/r["sp_count"]}
        result = dict(banks=len(sub),scenes=len(scenes))
        counts = np.array([sum(r["scene_id"]==s for r in sub) for s in scenes])
        idx = rng.integers(len(scenes),size=(10000,len(scenes)))
        for name, fn in fields.items():
            totals = np.array([sum(fn(r) for r in sub if r["scene_id"]==s) for s in scenes])
            boot = totals[idx].sum(1)/counts[idx].sum(1)
            result[name]=dict(mean=float(totals.sum()/len(sub)),ci95=np.quantile(boot,[.025,.975]).tolist())
        summaries[group]=result
    payload=dict(status="complete",banks=len(rows),scenes=len(graphs),missing=0,
        source_sha256=sha(root/"summary.json"),worker_sha256=sha(__file__),
        graph_definition="scale50 occupied voxel majority-SP six-face contact",
        scope="Frozen mined M95; SP-IoU diagnostic,not deployable correction or point-metric efficacy",
        self_tests="PASS",summary=summaries,graphs=graphs,rows=rows)
    output.write_text(json.dumps(payload,indent=2))
    print(json.dumps(summaries,indent=2))


if __name__=="__main__":
    main()
