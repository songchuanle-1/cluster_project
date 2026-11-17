"""Contact interventions; distinguish false islands from missing target components."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES="", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
import json
from pathlib import Path
import numpy as np
import torch
from scipy.sparse.csgraph import connected_components
from boundary_adjacency_audit_20260914 import graph, sha, iou


def main():
    torch.set_num_threads(1)
    root = Path("/tmp/cluster_semantic_projection_20260912/full")
    manifest = json.loads((root/"summary.json").read_text())
    out = Path("/tmp/contact_intervention_20260914.json")
    assert not out.exists()
    rows = []
    for scene in sorted({r["scene_id"] for r in manifest["rows"]}):
        raw = Path("/home/songcl/data/data/scannetv2/val")/(scene+"_refer.pth")
        xyz, _, sp, _, _ = torch.load(raw,map_location="cpu",weights_only=False)
        _, mapping = np.unique(sp,return_inverse=True)
        _, adj, _ = graph(np.asarray(xyz),mapping)
        for item in [r for r in manifest["rows"] if r["scene_id"]==scene]:
            path = root/item["artifact"]
            assert sha(path)==item["artifact_sha256"]
            bank = torch.load(path,map_location="cpu",weights_only=False)
            t = bank["tensors"]
            assert np.array_equal(mapping,t["superpoints"].numpy().ravel())
            gt = t["gt_spmask"].numpy().ravel()>.5
            q = int(np.diff(t["indis_logits"].numpy(),axis=1).ravel().argmax())
            pred = t["mask_logits"].numpy()[q]>=0
            seed = int(t["seed_indices"].numpy().ravel()[t["sample_indices"].numpy().ravel()[q]])
            ids = np.flatnonzero(pred)
            labels = connected_components(adj[pred][:,pred],directed=False)[1] if len(ids) else np.array([],int)
            rooted = np.zeros(len(gt),bool)
            if pred[seed]:
                rooted[ids[labels==labels[np.flatnonzero(ids==seed)[0]]]]=True
            # GT oracle removes only wholly false-positive connected components.
            prune = pred.copy()
            for label in np.unique(labels):
                comp = ids[labels==label]
                if not gt[comp].any():
                    prune[comp]=False
            # GT oracle completes only target components already touched by prediction.
            gt_ids = np.flatnonzero(gt)
            gt_labels = connected_components(adj[gt][:,gt],directed=False)[1]
            completion = pred.copy()
            for label in np.unique(gt_labels):
                comp = gt_ids[gt_labels==label]
                if pred[comp].any():
                    completion[comp]=True
            rows.append(dict(**bank["identity"],before=iou(pred,gt),
                seed_in_gt=bool(gt[seed]),seed_in_pred=bool(pred[seed]),
                root_component_iou=iou(rooted,gt),false_island_oracle_iou=iou(prune,gt),
                touched_target_completion_iou=iou(completion,gt),
                root_removed_true=int((pred & ~rooted & gt).sum()),
                pure_false_removed=int((pred & ~prune).sum()),
                target_added=int((completion & ~pred).sum())))
    assert len(rows)==284
    result={}
    for name, subset in (("failures",[r for r in rows if r["before"]<=.5]),
                         ("success",[r for r in rows if r["before"]>.5])):
        result[name]=dict(n=len(subset),scenes=len({r["scene_id"] for r in subset}),
            seed_outside_gt=sum(not r["seed_in_gt"] for r in subset),
            seed_outside_pred=sum(not r["seed_in_pred"] for r in subset))
        for method in ("root_component_iou","false_island_oracle_iou","touched_target_completion_iou"):
            result[name][method]=dict(success=sum(r[method]>.5 for r in subset),
                worse=sum(r[method]<r["before"] for r in subset),
                mean_delta=float(np.mean([r[method]-r["before"] for r in subset])))
    out.write_text(json.dumps(dict(summary=result,rows=rows,source_sha256=sha(root/"summary.json"),
        worker_sha256=sha(__file__),scope="Frozen mined M95 SP-IoU. Two GT oracles,one no-GT root intervention;not training or new method."),indent=2))
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
