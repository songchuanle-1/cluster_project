"""Exact native fixed-anchor partition control and frozen TRAIN geometry."""
import json
from ops import ROOT, OUT, CID, guard, remote, save, evidence, tick, now

guard(600)
program = r'''
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
import ast,copy,hashlib,importlib.util,json,logging,sys
from pathlib import Path
import torch,gorilla
from torch_scatter import scatter_mean
torch.set_num_threads(1)
root=Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b')
sys.path[:0]=[str(root),str(root/'framework/lib')]
from tools import train
from framework.dataset import build_dataset
name='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
hier=root/'framework/model/Quard_model'/name/'hier_postprocess.py'
dataset_source=root/'framework/dataset/scannetv2.py'
config=root/'configs/Quard/ctf_hcg_csort'/(name+'.yaml')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert sha(hier)=='7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f'
assert sha(dataset_source)=='2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d'
assert sha(config)=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a'
spec=importlib.util.find_spec('pointnet2')
package=Path(list(spec.submodule_search_locations)[0])
wrapper=package/'pointnet2_utils.py'
text=wrapper.read_text()
tree=ast.parse(text)
fps=next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=='FurthestPointSampling')
forward=next(node for node in fps.body if isinstance(node,ast.FunctionDef) and node.name=='forward')
native_sources=[str(path) for path in package.rglob('*') if path.is_file() and path.suffix in ('.cu','.cpp') and 'sampl' in path.name]
hier_tree=ast.parse(hier.read_text())
partitioner=next(node for node in hier_tree.body if isinstance(node,ast.ClassDef) and node.name=='PointCloudPartitioner')
method=next(node for node in partitioner.body if isinstance(node,ast.FunctionDef) and node.name=='partition_points')
namespace={'torch':torch}
exec(compile(ast.Module(body=[method],type_ignores=[]),str(hier),'exec'),namespace)
partition=namespace['partition_points']
cfg=gorilla.Config.fromfile(str(config))
assert cfg.train.seed==1999 and cfg.model.dec.cluster_layer_nums==[256,64,8]
dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('relabel-native-cpu'))
first={}
for index,group in enumerate(dataset.scene_inputs):first.setdefault(group[0]['scene_id'],index)
scenes=['scene0000_00','scene0001_00','scene0002_00','scene0003_00']
gorilla.set_random_seed(1999)
rows=[]
def labels(groups,n):
 result=torch.empty(n,dtype=torch.long)
 for label,indices in enumerate(groups):result[indices]=label
 return result
for scene in scenes:
 index=first[scene]
 item=dataset[index]
 assert item[1]==scene
 coords_float=item[3]
 superpoints=item[5].long()
 assert not coords_float.is_cuda and not superpoints.is_cuda
 coords=scatter_mean(coords_float,superpoints,dim=0).float().contiguous()
 n=len(coords)
 assert n>=256 and coords.shape==(n,3)
 permutation=torch.arange(n-1,-1,-1,dtype=torch.long)
 inverse=torch.argsort(permutation)
 assert torch.equal(coords[permutation][inverse],coords)
 anchors=coords[:256].clone()
 original=labels(partition(None,coords,anchors),n)
 identity=labels(partition(None,coords.clone(),anchors.clone()),n)
 relabeled=labels(partition(None,coords[permutation],anchors),n)[inverse]
 rows.append({'scene_id':scene,'group_index':index,'valid_superpoints':n,'coordinates':coords.tolist(),
  'coordinate_sha256':hashlib.sha256(coords.numpy().tobytes()).hexdigest(),
  'exact_inverse_permutation':True,'native_fixed_anchor_identity_equal':torch.equal(original,identity),
  'native_fixed_anchor_relabel_equal':torch.equal(original,relabeled),
  'changed_fixed_anchor_assignments':int((original!=relabeled).sum()),
  'anchor_scope':'First256physicalrows,NOTnativeFPS-selectedanchors;conditionalassignmentcontrolonly.'})
assert not torch.cuda.is_initialized()
print(json.dumps({'execution_completed':True,'cuda_initialized':False,'cohort':rows,
 'source_hashes':{'hierarchy':sha(hier),'dataset':sha(dataset_source),'config':sha(config)},
 'native_partition_method_ast':ast.unparse(method),
 'fps_wrapper':str(wrapper),'fps_wrapper_sha256':sha(wrapper),'fps_forward_ast':ast.unparse(forward),
 'installed_sampling_sources':native_sources,'first_physical_seed_rule':None,
 'seed_rule_status':'UNKNOWN unless exposed in exact installed wrapper/source;binary delegation is not seed evidence.',
 'scope':'Exact native CPU fixed-anchor assignment and native TRAIN geometry;no FPSkernel/hierarchy/mask/backward/effectivenessPASS.'}))
'''
result = remote(program, timeout=240, conda=True)
path = save("native_cpu_probe.json", {"observed_at": now(), **result})
payload = save("native_geometry.json", {"cohort": [{key: row[key] for key in ("scene_id", "group_index", "valid_superpoints", "coordinates", "coordinate_sha256")} for row in result["cohort"]],
                                      "cpu_probe": evidence(path), "source_hashes": result["source_hashes"]})
work = tick.load(ROOT / "pipeline/research_work.json")
candidate = next(row for row in work["candidates"] if row["id"] == CID)
candidate.update(stage="validation", updated_at=now(),
    gate_result="Actual native TRAIN geometry captured and exact native fixed-anchor assignment controls executed. This is not native FPS/recomputed hierarchy or task benefit;compiled seed rule remains unknown unless source exposed.",
    next_action="Freeze/run exact original GPU FPS and composed hierarchy under lossless physical row reversal, with native identity and inverse-permutation controls;compare label-invariant co-membership,not cluster label numbers.")
candidate["evidence"].extend([evidence(path), evidence(payload)])
guard()
tick.save(ROOT / "pipeline/research_work.json", work)
print(json.dumps({'scenes':[{key:value for key,value in row.items() if key!='coordinates'} for row in result['cohort']],
                  'fps_forward_ast':result['fps_forward_ast'],'installed_sampling_sources':result['installed_sampling_sources'],
                  'cuda_initialized':result['cuda_initialized'],'evidence':evidence(path)},indent=2))
