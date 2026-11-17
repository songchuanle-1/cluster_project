"""Resource-only AST adaptation; old frozen scientific scripts remain intact."""
from gpu1_ops import *
import ast,copy,shutil
guard(300)
program=r'''import json,subprocess,fcntl,shutil
from datetime import datetime,timezone
rows={}
for gpu in (0,1):
 row=subprocess.check_output(['nvidia-smi','-i',str(gpu),'--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
 contexts=subprocess.check_output(['nvidia-smi','-i',str(gpu),'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
 fields=[s.strip() for s in row.split(',')];expected='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c' if gpu==0 else 'GPU-7f82edb9-f620-8045-caea-a75232265cd1'
 assert fields[:2]==[str(gpu),expected]
 locks={};held=[]
 for kind in ('training','diagnostic','exclusive'):
  handle=open('/tmp/cluster_project_gpu'+str(gpu)+'_'+kind+'.lock','a+b')
  try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]=True;held.append(handle)
  except BlockingIOError:locks[kind]=False;handle.close()
 for handle in reversed(held):handle.close()
 rows[str(gpu)]={'gpu':row,'contexts':contexts,'locks_available':locks,'idle':not contexts and int(fields[2])<1024 and int(fields[3])<10 and all(locks.values())}
assert rows['1']['idle'],'AuthorizedGPU1isnotactuallyidle;do notshare/evict'
assert shutil.disk_usage('/data/songcl/Project/Cluster_project').free>5*1024**3
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'cards':rows,'disk_free_bytes':shutil.disk_usage('/data/songcl/Project/Cluster_project').free,'probe_locks_released':True,'cuda_initialized':False}))
'''
observed=remote(program,conda=True);save('fresh_gpu1_availability.json',observed)
config_receipt={'recorded_at':datetime.now(timezone.utc).isoformat(),'source':'ExplicitcurrenthumanGPU1authorization,notheartbeatinference','authorization':evidence(AUTH),'SERVERS':evidence(ROOT/'SERVERS.yaml'),'new_goal':evidence(ROOT/'pipeline/goal.json'),'old_goal_sha256':tick.load(AUTH)['prior_goal_sha256'],'begin_snapshot_kept_unchanged':True,'note':'ExplicitresourceadditionoccurredAFTERbeginunderthislease. Preflighttablesremainoldallocation;currentnewserver4allowed[0,1],server3GPU1retained,totalcapacity3. No secondpreflight,science/target/bans/scheduleunchanged.'}
save('resource_authorization_receipt.json',config_receipt)
old_uuid='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
class Adapt(ast.NodeTransformer):
 def __init__(self):self.counts={'uuid':0,'index_string':0,'lock':0}
 def visit_Constant(self,node):
  if node.value==old_uuid:self.counts['uuid']+=1;return ast.copy_location(ast.Constant(UUID),node)
  if node.value=='0':self.counts['index_string']+=1;return ast.copy_location(ast.Constant('1'),node)
  if isinstance(node.value,str) and '/tmp/cluster_project_gpu0_' in node.value:
   self.counts['lock']+=1;return ast.copy_location(ast.Constant(node.value.replace('/tmp/cluster_project_gpu0_','/tmp/cluster_project_gpu1_')),node)
  return node
for label,oldfolder,entry,metrics,cid in (
 ('scale','tick_28fc3749','native_scale_task.py','scale_metrics.py','m95-scale-specific-boundary-responsibility'),
 ('expression','tick_87d50f0c','native_expression_task.py','expression_metrics.py','m95-expression-specific-point-message')):
 old=ROOT/'pipeline/diagnostic_bundles'/oldfolder;folder=OUT/label;folder.mkdir()
 previous=tick.load(old/'native_manifest.json')
 for name in (entry,metrics):
  assert tick.digest(old/name)==previous['diagnostic_files'][name]
  shutil.copy2(old/name,folder/name)
 original=ast.parse((old/'native_runtime.py').read_text(encoding='utf-8'));adapter=Adapt();tree=adapter.visit(copy.deepcopy(original));ast.fix_missing_locations(tree)
 assert adapter.counts=={'uuid':2,'index_string':3,'lock':1},adapter.counts
 (folder/'native_runtime.py').write_text(ast.unparse(tree)+'\n',encoding='utf-8')
 for name in (entry,metrics,'native_runtime.py'):ast.parse((folder/name).read_text(encoding='utf-8'))
 assert tick.digest(folder/entry)==previous['diagnostic_files'][entry]
 assert tick.digest(folder/metrics)==previous['diagnostic_files'][metrics]
 manifest=copy.deepcopy(previous)
 manifest.update(stage='/data/songcl/Project/Cluster_project/pipeline/gpu1_30bdd3a5/'+label,
  diagnostic_files={name:tick.digest(folder/name) for name in (entry,metrics,'native_runtime.py')},
  physical_gpu=1,gpu_uuid=UUID,gpu_authorization=evidence(AUTH),resource_adaptation='Onlynative_runtimeASTstringconstantsforphysicalGPUindex/UUID/lock. CUDAlogicaldevice0unchanged;source/config/checkpoint/cohort/query/target/toleranceunchanged.')
 tick.save(folder/'native_manifest.json',manifest)
 save(label+'_resource_adaptation.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'candidate_id':cid,'original_manifest':evidence(old/'native_manifest.json'),'new_manifest':evidence(folder/'native_manifest.json'),'runtime_AST_replacements':adapter.counts,'scientific_entry_byte_identical':True,'metric_file_byte_identical':True,'asset_dict_unchanged':manifest['assets']==previous['assets'],'cohort_unchanged':manifest['cohort']==previous['cohort'],'tolerance_unchanged':manifest['tolerance']==previous['tolerance']==1e-6,'model_or_config_changes':0,'new_training':0})
 advance(cid,[AUTH,ROOT/'SERVERS.yaml',ROOT/'pipeline/goal.json',OUT/'fresh_gpu1_availability.json',OUT/'resource_authorization_receipt.json',OUT/(label+'_resource_adaptation.json'),folder/'native_manifest.json'],stage='validation',last_resource_resolution='ExplicithumanGPU1additionplusfreshverifiedGPU1idlenessandlockavailability. OldGPU0busy/server3faultevidencepreserved;no longerblockthisnative task.',next_action='ExecuteSAMEfrozennativepair0onnewlyauthorizedserver4GPU1withfreshcurrentlease/manifest/exclusiveflocks. Preservealloriginalstrictcontrols;noM204restart/scientificgatewaiver.')
print(json.dumps({'GPU1_verified_idle':True,'prepared_diagnostics':['scale','expression'],'science_entry_files_unchanged':True,'new_goal_sha256':GOAL,'new_training':0},ensure_ascii=True,indent=2))
