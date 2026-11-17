"""Bounded native TRAIN graph/interface coverage, without model forward."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES="",OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1")
import importlib.util
import json
import logging
from pathlib import Path
import sys
import time
root=Path("/data3/songcl/Project/Cluster_project/Cluster")
work=Path("/tmp/bca_admission_20260914")
sys.path[:0]=[str(root),str(root/"framework/lib")]
import torch
import gorilla
from framework.dataset import build_dataset,build_dataloader
spec=importlib.util.spec_from_file_location("helper",work/"model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bca/boundary_assignment.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
torch.set_num_threads(1)
gorilla.set_random_seed(1999)
cfg=gorilla.Config.fromfile(str(work/"model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bca.yaml"))
cfg.data.train.data_root="/data3/songcl/data/data_cluster/"
dataset=build_dataset(cfg.data.train,logging.getLogger("bca_coverage"))
loader=build_dataloader(dataset,batch_size=2,num_workers=0,persistent_workers=False)
rows=[]
times=[]
for step,batch in enumerate(loader):
    start=time.perf_counter()
    graphs=m.scene_contacts(batch["voxel_coords"],batch["p2v_map"],batch["superpoints"],batch["batch_offsets"])
    times.append(time.perf_counter()-start)
    offset=0
    for scene,(edges,length) in enumerate(zip(graphs,batch["scenes_len"].tolist())):
        edge=torch.tensor(edges)
        for b in range(offset,offset+length):
            gt=batch["gt_spmasks"][b].flatten().bool()
            boundary=torch.unique(edge[gt[edge[:,0]]!=gt[edge[:,1]]])
            k=int(gt[boundary].sum())
            rows.append(dict(step=step,scene=batch["scan_ids"][scene],
                objects=batch["object_idss"][b],boundary_n=len(boundary),boundary_k=k,
                dp_states=len(boundary)*min(k,len(boundary)-k)))
        offset+=length
    if step==15:break
report=dict(batches=len(times),expressions=len(rows),rows=rows,
    valid=sum(r["boundary_n"]>0 for r in rows),
    max_n=max(r["boundary_n"] for r in rows),max_dp_states=max(r["dp_states"] for r in rows),
    graph_seconds_mean=sum(times)/len(times),graph_seconds_max=max(times),
    scope="16native TRAIN batches,seed1999,workers0;not full-epoch coverage")
out=work/"train_coverage.json";assert not out.exists()
out.write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!="rows"},indent=2))
