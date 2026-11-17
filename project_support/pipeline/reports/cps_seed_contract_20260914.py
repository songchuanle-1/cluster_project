"""Bounded native TRAIN/FPS contract audit, no model or optimizer."""
import os
os.environ.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", TOKENIZERS_PARALLELISM="false")
import sys
import json
import logging
from pathlib import Path
root = Path("/data3/songcl/Project/Cluster_project/Cluster")
sys.path[:0] = [str(root), str(root/"framework/lib")]
import numpy as np
import torch
import gorilla
from framework.dataset import build_dataset, build_dataloader
from pointnet2.pointnet2_utils import FurthestPointSampling

torch.set_num_threads(1)
torch.cuda.set_per_process_memory_fraction(.03)
gorilla.set_random_seed(1999)
name = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cps"
cfg = gorilla.Config.fromfile(str(root/f"configs/Quard/ctf_hcg_csort_cps/{name}.yaml"))
data = build_dataset(cfg.data.train, logging.getLogger("seed_contract"))
loader = build_dataloader(data, batch_size=2, num_workers=0, persistent_workers=False)
rows = []
for step, batch in enumerate(loader):
    xyz = batch["coords_float"].numpy()
    sp = batch["superpoints"].numpy()
    count = np.bincount(sp)
    centers = np.stack([np.bincount(sp,weights=xyz[:,i])/count for i in range(3)],axis=1)
    offsets = batch["batch_offsets"].tolist()
    for i,(s,e) in enumerate(zip(offsets[:-1],offsets[1:])):
        points = torch.tensor(centers[s:e],dtype=torch.float32,device="cuda").unsqueeze(0)
        seeds = FurthestPointSampling.apply(points,cfg.model.fps_num).cpu().numpy().ravel()
        row = dict(step=step,scene=batch["scan_ids"][i],superpoints=e-s,
                   fps_requested=cfg.model.fps_num,unique_seeds=len(np.unique(seeds)),
                   near_origin=int((np.sum(centers[s:e]**2,axis=1)<=1e-3).sum()))
        rows.append(row)
        if row["unique_seeds"] < len(seeds):
            torch.save(dict(batch=batch,centers=centers,scene_index=i,seeds=seeds),
                       "/tmp/cps_duplicate_native_fixture_20260914.pth")
            report = dict(status="reproduced",scope="native TRAIN/FPS;not exact crashed RNG replay",
                          rows=rows,duplicate=row,model_forward=False,optimizer_updates=0)
            Path("/tmp/cps_seed_contract_20260914.json").write_text(json.dumps(report,indent=2))
            print(json.dumps(report,indent=2))
            sys.exit(0)
    if step >= 63:
        break
Path("/tmp/cps_seed_contract_20260914.json").write_text(json.dumps(dict(status="not_reproduced_in64batches",rows=rows),indent=2))
print("No duplicate within bounded64batch sample")
