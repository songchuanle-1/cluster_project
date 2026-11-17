"""CPU-only native TRAIN incidence, not learned feature or GPU execution."""
import json
import subprocess
from audit_feature_path import BUNDLE, MODEL, TOKEN, guard, tick

PROGRAM=r'''
import datetime,hashlib,json,logging,os,pathlib,subprocess,sys
os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='1')
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
root=pathlib.Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b')
checkpoint=root.parent/'Cluster_checkpoints'/MODEL/'20260815_101011/best.pth'
def sha(p):
    h=hashlib.sha256()
    with pathlib.Path(p).open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()
checkpoint_sha=sha(checkpoint)
sys.path[:0]=[str(root),str(root/'framework/lib')]
import torch,gorilla
torch.set_num_threads(1)
assert not torch.cuda.is_initialized()
saved=torch.load(checkpoint,map_location='cpu',weights_only=False,mmap=True)
meta=saved.get('meta',{})
checkpoint_record={'path':str(checkpoint),'sha256':checkpoint_sha,'expected_frozen_sha256':'fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e',
                   'matches_expected_frozen':checkpoint_sha=='fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e',
                   'meta':{k:meta.get(k) for k in ('epoch','best_res','best_epoch','epochs_no_improve')},'model_state_present':'model' in saved}
del saved
from framework.dataset import build_dataset
config=root/'configs/Quard/ctf_hcg_csort'/(MODEL+'.yaml')
cfg=gorilla.Config.fromfile(str(config))
assert cfg.train.seed==1999 and cfg.train.epochs==50 and cfg.lr_scheduler.max_iters==70
cfg.data.train.data_root='/home/songcl/data/data/'
dataset=build_dataset(cfg.data.train,logging.getLogger('point-feature-native-input'))
groups=[0,60,101,124]
def fingerprint(value):
    h=hashlib.sha256()
    def visit(x):
        if torch.is_tensor(x):
            y=x.detach().cpu().contiguous();h.update(str((y.dtype,tuple(y.shape))).encode());h.update(y.numpy().tobytes())
        elif isinstance(x,dict):
            for key in sorted(x):h.update(str(key).encode());visit(x[key])
        elif isinstance(x,(tuple,list)):
            for part in x:visit(part)
        else:h.update(repr(x).encode())
    visit(value)
    return h.hexdigest()
trials=[]
for trial in range(2):
    gorilla.set_random_seed(1999)
    rows=[]
    for group in groups:
        item=dataset[group]
        sp=item[5]
        rows.append({'group':group,'scene':item[1],'ann_ids':item[0],'expressions':len(item[0]),'points':len(sp),
                     'superpoint_extent':int(sp.max())+1,'unique_superpoints':int(sp.unique().numel()),'native_item_sha256':fingerprint(item)})
        del item
    trials.append(rows)
assert trials[0]==trials[1],'Original native inputs must repeat at unchanged seed1999'
pairs=[]
for a,b in ((0,1),(2,3)):
    left,right=trials[0][a],trials[0][b]
    maximum=max(left['superpoint_extent'],right['superpoint_extent'])
    pairs.append({'groups':[left['group'],right['group']],
                  'extent':[left['superpoint_extent'],right['superpoint_extent']],
                  'padding_trigger':left['superpoint_extent']!=right['superpoint_extent'],
                  'inferred_valid_fraction':[left['superpoint_extent']/maximum,right['superpoint_extent']/maximum]})
assert not torch.cuda.is_initialized()
print(json.dumps({'observed_at':datetime.datetime.now().astimezone().isoformat(),'checkpoint':checkpoint_record,
 'config_sha256':sha(config),'dataset_source_sha256':sha(root/'framework/dataset/scannetv2.py'),
 'group_count':len(groups),'expression_count':sum(row['expressions'] for row in trials[0]),'repeat_exact':True,'trials':trials,'preregistered_pairs':pairs,
 'scope':'Actual original TRAIN __getitem__ only. Padding extents inferred from unchanged collate/expand/get_batches source, NOT learned feature or native network capture.',
 'cuda_initialized':False,'network_forwards':0,'optimizer_steps':0,'training':False},default=lambda x:x.item()))
'''

guard()
result=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=12','server-4','/home/songcl/.conda/envs/project_cluster/bin/python','-B','-'],input='MODEL='+repr(MODEL)+'\n'+PROGRAM,text=True,encoding='utf-8',capture_output=True,timeout=220)
guard()
tick.save(BUNDLE/'native_input_attempt.json',{'token':TOKEN,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
if result.returncode:
    print(result.stderr[-5000:])
    raise SystemExit(result.returncode)
data=json.loads(result.stdout)
tick.save(BUNDLE/'native_input_incidence.json',{'token':TOKEN,**data})
print(json.dumps(data,indent=2))
