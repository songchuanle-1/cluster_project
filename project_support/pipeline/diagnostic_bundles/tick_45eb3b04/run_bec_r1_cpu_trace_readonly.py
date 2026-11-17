"""Preregistered tiny CPU compatibility test only; no original model is imported."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess

ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
def main():
    owner=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text())
    assert owner['token']=='45eb3b045c6243518d56eade38d5cd17' and datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    prereg=HERE/'bec_revision1_preregistration.json'
    assert hashlib.sha256(prereg.read_bytes()).hexdigest()=='3fa782b8970de909a219cc090e2188983e1afeab1ac99cac43df07b4f1e5b527'
    registered=json.loads(prereg.read_text())['preregistration']['preregistered_at']
    assert datetime.now(timezone.utc)>datetime.fromisoformat(registered)
    payload=r'''import socket,os,pathlib,hashlib,json,traceback,warnings,importlib
from datetime import datetime,timezone
assert socket.gethostname()=='dl04-MS-7E06'
os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['OMP_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
import torch
torch.set_num_threads(1)
import fvcore
from fvcore.nn import FlopCountAnalysis
handlers={n:hashlib.sha256(pathlib.Path(importlib.import_module('fvcore.nn.'+n).__file__).read_bytes()).hexdigest() for n in ['flop_count','jit_analysis','jit_handles']}
assert handlers=={'flop_count':'b5a02604a883bcda75deb918d68639d207c433938cf27e7034dd6de26a2956ba','jit_analysis':'110f30463ba9f20a86dc1f7a447bed29fe6d55dfedff4a30e05e955e47cacb31','jit_handles':'ef3a1d20ccad504bfdab7d2a127bce9483de1125d170d915d22f4addbc36c129'}
class ExactMaskLine(torch.nn.Module):
 def __init__(self,value):super().__init__();self.value=value
 def forward(self,coarse,ids):
  mask=torch.zeros(coarse.shape[:2],dtype=torch.bool,device=coarse.device)
  for b in range(coarse.shape[0]):
   mask[b]=mask[b].index_fill(0,ids,self.value)
  return mask
cases=[]
for name,values in [('empty',[]),('nonempty',[0,3,7]),('repeated',[2,2,5])]:
 coarse=torch.zeros((2,8,256),dtype=torch.float32);ids=torch.tensor(values,dtype=torch.long)
 old=ExactMaskLine(True).eval();new=ExactMaskLine(1).eval()
 with torch.no_grad():
  eager_old=old(coarse,ids);eager_new=new(coarse,ids)
 assert eager_old.dtype==eager_new.dtype==torch.bool and eager_old.shape==eager_new.shape and torch.equal(eager_old,eager_new)
 result={'case':name,'ids':values,'input_shape':list(coarse.shape),'mask_shape':list(eager_old.shape),'mask_dtype':str(eager_old.dtype),'eager_bool_int_exact':True,'mask_true_count':int(eager_old.sum().item()),'branches':{}}
 for label,model in [('original_bool',old),('integer_one',new)]:
  branch={}
  try:
   with warnings.catch_warnings(record=True) as caught,torch.no_grad():
    traced=torch.jit.trace(model,(coarse,ids))
    traced_mask=traced(coarse,ids)
   graph=str(traced.inlined_graph)
   branch['JIT']={'succeeded':True,'eager_mask_exact':bool(torch.equal(traced_mask,eager_old)),'graph_sha256':hashlib.sha256(graph.encode()).hexdigest(),'aten_index_fill_count':graph.count('aten::index_fill('),'warnings':[str(w.message) for w in caught]}
  except Exception as error:branch['JIT']={'succeeded':False,'error_type':type(error).__name__,'error':str(error)}
  try:
   with warnings.catch_warnings(record=True) as caught,torch.no_grad():
    analysis=FlopCountAnalysis(model,(coarse,ids));analysis.unsupported_ops_warnings(False);analysis.uncalled_modules_warnings(False);total=analysis.total()
   branch['original_fvcore']={'succeeded':True,'flops':float(total),'by_operator':{k:float(v) for k,v in analysis.by_operator().items()},'unsupported_ops':dict(analysis.unsupported_ops()),'warnings':[str(w.message) for w in caught]}
  except Exception as error:branch['original_fvcore']={'succeeded':False,'error_type':type(error).__name__,'error':str(error)}
  result['branches'][label]=branch
 cases.append(result)
def original_expected_fail(c):
 return all(not c['branches']['original_bool'][k]['succeeded'] and 'aten::index_fill' in c['branches']['original_bool'][k]['error'] and 'alias_analysis.cpp' in c['branches']['original_bool'][k]['error'] for k in ['JIT','original_fvcore'])
def new_expected_pass(c):
 return c['branches']['integer_one']['JIT']['succeeded'] and c['branches']['integer_one']['JIT']['eager_mask_exact'] and c['branches']['integer_one']['JIT']['aten_index_fill_count']==2 and c['branches']['integer_one']['original_fvcore']['succeeded']
matched=all(c['eager_bool_int_exact'] and original_expected_fail(c) and new_expected_pass(c) for c in cases)
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'torch_version':str(torch.__version__),'fvcore_version':fvcore.__version__,'profiler_file_sha256':handlers,'cases':cases,'registered_prediction_supported_by_CPU_test':matched,'actual_native_model_TRAIN_resource_gate':'NOT_RUN_BY_THIS_TEST','original_model_imported':False,'CUDA_or_torch_cuda_API_used':False,'GPU_queried':False,'forward_scope':'Only tiny explicitly defined CPU mask-line module, not original model','backward_optimizer_or_training':False,'remote_source_or_file_modified':False,'no_custom_or_ignored_handlers':True}))
'''
    args=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/home/songcl/.conda/envs/project_cluster/bin/python -B -']
    run=subprocess.run(args,input=payload,capture_output=True,text=True,encoding='utf8',timeout=90)
    q={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner_token':owner['token'],'preregistration':{'path':prereg.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(prereg.read_bytes()).hexdigest()},'preregistered_at':registered,'transport':'SSH_KEY_BATCHMODE_STRICT_KNOWN_HOST','returncode':run.returncode,'stderr':run.stderr,'result':json.loads(run.stdout) if run.returncode==0 else None,'failed_stdout':run.stdout if run.returncode else None,'source_changed':False,'native_resource_or_TRAIN_pass_claimed':False}
    path=HERE/'bec_r1_cpu_trace_evidence.json'
    with path.open('x',encoding='utf8') as f:json.dump(q,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
    print(json.dumps({'returncode':run.returncode,'evidence_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'registered_prediction_supported':q['result']['registered_prediction_supported_by_CPU_test'] if q['result'] else None,'stderr':run.stderr if run.returncode else None}))
if __name__=='__main__':main()
