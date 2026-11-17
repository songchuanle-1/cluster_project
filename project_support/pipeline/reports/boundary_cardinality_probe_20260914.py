"""Frozen GT-cardinality projection diagnostic; not deployment."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES="",OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1")
import json
from pathlib import Path
import numpy as np
import torch
from boundary_adjacency_audit_20260914 import graph,sha,iou


def main():
    torch.set_num_threads(1)
    root=Path("/tmp/cluster_semantic_projection_20260912/full")
    manifest=json.loads((root/"summary.json").read_text())
    rows=[]
    for scene in sorted({r["scene_id"] for r in manifest["rows"]}):
        raw=Path("/home/songcl/data/data/scannetv2/val")/(scene+"_refer.pth")
        xyz,_,sp,_,_=torch.load(raw,map_location="cpu",weights_only=False)
        _,mapping=np.unique(sp,return_inverse=True)
        edges,adj,_=graph(np.asarray(xyz),mapping)
        for item in [r for r in manifest["rows"] if r["scene_id"]==scene]:
            path=root/item["artifact"]
            assert sha(path)==item["artifact_sha256"]
            b=torch.load(path,map_location="cpu",weights_only=False); t=b["tensors"]
            gt=t["gt_spmask"].numpy().ravel()>.5
            q=int(np.diff(t["indis_logits"].numpy(),axis=1).ravel().argmax())
            logits=t["mask_logits"].numpy()[q];pred=logits>=0
            ids=np.unique(edges[gt[edges[:,0]]!=gt[edges[:,1]]].ravel())
            k=int(gt[ids].sum())
            fixed=pred.copy()
            if len(ids):
                fixed[ids]=False
                fixed[ids[np.argsort(-logits[ids],kind="stable")[:k]]]=True
            crossings=edges[gt[edges[:,0]]!=gt[edges[:,1]]]
            inverted=sum(logits[a]<=logits[c] if gt[a] else logits[c]<=logits[a] for a,c in crossings)
            rows.append(dict(**b["identity"],before=iou(pred,gt),after=iou(fixed,gt),
                boundary_n=len(ids),boundary_k=k,dp_states=len(ids)*min(k,len(ids)-k),
                crossing_edges=len(crossings),inverted_edges=int(inverted)))
    summary={}
    for name,rs in (("failure",[r for r in rows if r["before"]<=.5]),
                    ("success",[r for r in rows if r["before"]>.5])):
        summary[name]=dict(n=len(rs),after_success=sum(r["after"]>.5 for r in rs),
            mean_delta=float(np.mean([r["after"]-r["before"] for r in rs])),
            with_inversion=sum(r["inverted_edges"]>0 for r in rs),
            total_inverted=sum(r["inverted_edges"] for r in rs),
            total_crossings=sum(r["crossing_edges"] for r in rs))
    report=dict(summary=summary,rows=rows,source_sha256=sha(root/"summary.json"),
        worker_sha256=sha(__file__),max_n=max(r["boundary_n"] for r in rows),
        max_states=max(r["dp_states"] for r in rows),scope="GT boundary and cardinality,not deployable")
    path=Path("/tmp/boundary_cardinality_probe_20260914.json");assert not path.exists()
    path.write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!="rows"},indent=2))


if __name__=="__main__":main()
