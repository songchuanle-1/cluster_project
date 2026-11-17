"""Native metadata weighting of the preregistered support census; no CUDA."""
import json
from study import ROOT, OUT, guard, remote_code, save, tick, evidence, now

guard(300)
census = tick.load(OUT / "native_resolution_result.json")
small = [row["scene_id"] for row in census["records"] if row["exact_train_support_count"] < 256]
save("training_incidence_protocol.json", {
    "created_at": now(), "census": evidence(OUT / "native_resolution_result.json"),
    "question": "Count original native TRAIN dataset groups belonging to the already-frozen small-support scene set; do not mistake 28/562 scenes for the training sampler frequency.",
    "limits": "Metadata incidence only; no realized shuffled epoch, task effect, probability-of-harm or extra training is observed.",
})
program = """import copy,json,logging,sys
from collections import Counter
import torch,gorilla
torch.set_num_threads(1)
sys.path[:0]=['/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b','/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b/framework/lib']
from tools import train
from framework.dataset import build_dataset
cfg=gorilla.Config.fromfile('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b/configs/Quard/ctf_hcg_csort/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.yaml')
dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('resolution-incidence'))
counts=Counter(group[0]['scene_id'] for group in dataset.scene_inputs)
small=SMALL
assert len(counts)==562 and len(small)==28
assert not torch.cuda.is_initialized()
print(json.dumps({'native_dataset_groups':len(dataset.scene_inputs),'native_small_scene_groups':sum(counts[scene] for scene in small),'small_scene_group_counts':{scene:counts[scene] for scene in small},'cuda_initialized':False,'realized_training_batches':None,'mask_effect':None}))
""".replace("SMALL", repr(small))
result = remote_code(program, timeout=180, conda=True)
path = save("native_training_incidence.json", {"observed_at": now(), **result})
print(json.dumps({"evidence": evidence(path), "native_dataset_groups": result["native_dataset_groups"],
                  "native_small_scene_groups": result["native_small_scene_groups"], "cuda_initialized": False}))
