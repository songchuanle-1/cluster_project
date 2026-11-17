"""Independent local-only stdlib identity review; never SSH/GPU/import packet."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
from types import SimpleNamespace
import ast, copy, hashlib, json, os, re, sys
ROOT=Path('D:/project/cluster_project')
CID='hierarchy-native-spatial-dirichlet-composition'
PSC='hierarchy-native-position-feature-cross-scatter-composition'
SOURCE='f6257de79148581334ee495e6e2d60ccb525457c'
PARENT='0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d'
GOAL='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
UUID='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
POLICY={'allow_external_overlay':True,'minimum_free_mib_before_launch':20000,'max_project_tasks_per_gpu':1,'cooperative_lock_kinds':['training','diagnostic','exclusive'],'external_contexts':'record_preserve_no_signals','measurement_scope':'authorized_overlay_potentially_contended_not_exclusive'}
AUTH={'path':'pipeline/authorizations/server4_gpu0_overlay_20261104.json','sha256':'783ffc27d48872940c2e15adcb85f6bb5f9b94492a8abd88694799f483d20e88'}
BASEPATH='/data/songcl/Project/Cluster_project/pipeline'
TOKEN='11111111111111111111111111111111'
STAGE=BASEPATH+'/nsd_11111111_gpu0'
PACKAGE='framework.model.Quard_model.model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()

def review(packet,output):
 checks=[]
 def ck(name,value,detail=None):checks.append({'name':name,'passed':bool(value),'detail':detail})
 def fn(tree,name):return next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name)
 def constants(tree):
  d={}
  for n in tree.body:
   if isinstance(n,ast.Assign):
    try:v=ast.literal_eval(n.value)
    except (ValueError,TypeError):continue
    for t in n.targets:
     if isinstance(t,ast.Name):d[t.id]=v
  return d
 frozen=json.loads((packet/'FROZEN.json').read_bytes());filemap=frozen.get('files',frozen.get('prepared_file_hashes',{}))
 ck('author_frozen_file_hashes',bool(filemap) and all(sha(packet/k)==v for k,v in filemap.items()),len(filemap))
 for name,digest in [('nsd_native_prepare','4ea59d171f4f4319f5f2b78c525aa70bda822cce02d50cf9acec3753d1815186'),('nsd_current_activation','d30317c8d666c8bf06c38361b0d3c8d4b9465484586c6d84a012eab0bd5e4cce')]:
  original=packet.parent/name
  old=json.loads((original/'FROZEN.json').read_bytes())
  ck('original_'+name+'_all_hashes_unchanged',sha(original/'FROZEN.json')==digest and all(sha(original/k)==v for k,v in old['files'].items()),len(old['files']))
 for p in packet.rglob('*.py'):compile(p.read_bytes(),str(p),'exec')
 ck('stdlib_compile_only_no_packet_import',True)
 ops=packet/'operational' if (packet/'operational').is_dir() else packet
 remote=(ops/'remote_ops.py').read_text();adapter=(ops/'adapter.py').read_text();rt=ast.parse(remote);at=ast.parse(adapter);rc=constants(rt);ac=constants(at)
 mother=packet.parent/'nsd_native_prepare'
 old_remote=(mother/'operational/remote_ops.py').read_bytes()
 ck('exactly_one_NSD_remote_identity_literal_fix',remote.encode()==old_remote.replace(("CANDIDATE='"+PSC+"'").encode(),("CANDIDATE='"+CID+"'").encode(),1))
 ck('adapter_and_launcher_byte_exact_to_original_mother',all((ops/name).read_bytes()==(mother/'operational'/name).read_bytes() for name in ['adapter.py','run_nsd_operation.py']))
 prep=json.loads((ops/'preparation.json').read_bytes());release=json.loads((ops/'release_template.json').read_bytes())
 ck('corrected_operational_preparation_and_release_hash_graphs',all(sha(ops/name)==digest for name,digest in prep['prepared_file_hashes'].items()) and all(sha(ops/name)==digest for name,digest in release['source_hashes'].items()))
 old_native=json.loads((mother/'native/manifest_template.json').read_bytes())
 ten=['current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit']
 ck('original_referenced_native_all_ten_fields_NULL',all(old_native[name] is None for name in ten))
 ck('external_literal_candidate_in_all_identity_modules',rc.get('CANDIDATE')==CID and ac.get('CANDIDATE')==CID,{'remote':rc.get('CANDIDATE'),'adapter':ac.get('CANDIDATE')})
 ck('external_literal_source_in_all_identity_modules',rc.get('COMMIT')==SOURCE and ac.get('COMMIT')==SOURCE)
 ck('adapter_remains_disabled',ac.get('DRAFT_EXECUTION_DISABLED') is True)
 memory={};process_calls=[]
 class VPath(PurePosixPath):
  def exists(self):return str(self) in memory or any(k.startswith(str(self)+'/') for k in memory)
  def resolve(self):return self
 def read(path):return copy.deepcopy(memory[str(path)])
 def msha(path):return hashlib.sha256(json.dumps(memory[str(path)],sort_keys=True).encode()).hexdigest()
 def fake_output(command,**kwargs):
  process_calls.append(command)
  return '0, '+UUID if '--query-gpu=index,uuid' in command else ''
 env={**rc,'Path':VPath,'PARENT':VPath(BASEPATH),'re':re,'read':read,'sha':msha,'exact_workers':lambda p:[],'process_info':lambda pid:None,'subprocess':SimpleNamespace(check_output=fake_output)}
 wanted=['check','identity','binding_stage','command_matches','result_matches','reconcile_operation']
 exec(compile(ast.Module(body=[fn(rt,n) for n in wanted],type_ignores=[]),'<actual-remote-functions-stdlib-fixtures>','exec'),env)
 binding={'project':'cluster_project','candidate_id':CID,'code_commit':SOURCE,'stage':STAGE,'owner':{'token':TOKEN},'physical_gpu':0,'gpu_uuid':UUID,'native_manifest_sha256':'3'*64,'resource_authorization':AUTH,'resource_memory_policy':POLICY}
 ck('actual_binding_stage_accepts_external_literal_NSD_fixture',str(env['binding_stage'](binding))==STAGE)
 for label,key,value in [('PSC','candidate_id',PSC),('wrong_source','code_commit',PARENT),('wrong_project','project','other'),('GPU1','physical_gpu',1),('wrong_UUID','gpu_uuid','GPU-foreign'),('foreign_stage','stage',BASEPATH+'/psc_11111111_gpu0'),('foreign_policy','resource_memory_policy',{})]:
  other=copy.deepcopy(binding);other[key]=value
  try:env['binding_stage'](other);rejected=False
  except (RuntimeError,KeyError,TypeError):rejected=True
  ck('crossbinding_refused_'+label,rejected)
 def expected_identity(request_id,operation,token=TOKEN,stage=STAGE):
  return {'project':'cluster_project','candidate_id':CID,'code_commit':SOURCE,'stage':stage,'token':token,'request_id':request_id,'operation':operation,'physical_gpu':0,'gpu_uuid':UUID,'native_manifest_sha256':'3'*64}
 external=expected_identity('fixture-request','run');ck('remote_actual_identity_equals_external_literal_NSD_dictionary',env['identity'](binding,{'request_id':'fixture-request','operation':'run'})==external)
 ag={**ac};exec(compile(ast.Module(body=[fn(at,'_identity'),fn(at,'_raw_result_identity')],type_ignores=[]),'<actual-adapter-pure-methods>','exec'),ag)
 ck('local_actual_identity_equals_external_literal_NSD_dictionary',ag['_identity'](None,binding,'fixture-request','run')==external)
 def raw(mode,target):return {'candidate_id':CID,'code_commit':SOURCE,'goal_sha256':GOAL,'mode':mode,'target':target,'model_package':PACKAGE+('_nsd' if target=='candidate' else ''),'execution_completed':True}
 for mode in ['smoke','resources']:
  for target in ['champion','candidate']:
   result=raw(mode,target);ck('remote_and_local_actual_result_paths_accept_external_'+mode+'_'+target,env['result_matches'](result,mode,target) and ag['_raw_result_identity'](None,result,binding,mode,target))
   for label,key,value in [('PSC','candidate_id',PSC),('parent','code_commit',PARENT),('foreign_goal','goal_sha256','0'*64),('mode','mode','other'),('target','target','other'),('fallback_package','model_package',PACKAGE+'_psc')]:
    other={**result,key:value};ck('both_actual_result_paths_refuse_'+mode+'_'+target+'_'+label,not env['result_matches'](other,mode,target) and not ag['_raw_result_identity'](None,other,binding,mode,target))
 memory[STAGE+'/native_manifest.json']={'fixture':'native_manifest_hash_held_in_binding_only'}
 for prefix in ['stage','smoke_champion','smoke_candidate','resources_champion','resources_candidate']:
  is_stage=prefix=='stage';mode,target=(None,None) if is_stage else prefix.split('_');request=expected_identity('fixture-'+prefix,'stage' if is_stage else 'run')
  if not is_stage:request.update(mode=mode,target=target)
  memory[STAGE+'/'+prefix+'_request.json']=request
  done={'identity':expected_identity('fixture-'+prefix,'stage' if is_stage else 'run')}
  if not is_stage:
   result=raw(mode,target);command=['python','-B',STAGE+'/worker.py','--lease',STAGE+'/execution_lease.json','--mode',mode,'--target',target];done.update(command=command,result=result,returncode=0);memory[STAGE+'/'+prefix+'_result.json']=result
  memory[STAGE+'/'+prefix+'_completed.json']=done
 observation=env['reconcile_operation']({'binding':binding});items=observation['requests'];ck('actual_reconcile_reads_exact_external_NSD_request_completed_result_paths',len(items)==5 and all(item['identity_matches'] and item['completed_identity_matches'] and (item['file']=='stage_request.json' or item['completed_command_matches'] and item['completed_result_identity_matches'] and item['result_identity_matches']) for item in items),[item['file'] for item in items])
 # Alter one current NSD request/complete/result to PSC; each actual reconciliation flag must refuse.
 for suffix,field,value,flag in [('_request.json','candidate_id',PSC,'identity_matches'),('_completed.json','identity',expected_identity('different-request','run'),'completed_identity_matches'),('_result.json','candidate_id',PSC,'result_identity_matches')]:
  key=STAGE+'/smoke_candidate'+suffix;old=copy.deepcopy(memory[key]);memory[key][field]=value
  found=env['reconcile_operation']({'binding':binding});item=next(i for i in found['requests'] if i['file']=='smoke_candidate_request.json');ck('actual_reconcile_cross_identity_refused_'+flag,item[flag] is False);memory[key]=old
 ck('mock_transport_only_no_actual_subprocess',bool(process_calls) and all(command[0]=='nvidia-smi' for command in process_calls),{'scope':'All check_output calls are an in-memory stub; zero real nvidia-smi/process/SSH/model/GPU calls.'})
 ck('no_active_execution_material_in_v2_packet',not any(p.name in ['adapter_release.json','native_manifest.json','execution_binding.json','execution_lease.json'] or p.name.endswith(('_request.json','_execution.json','_started.json','_completed.json','_result.json')) for p in packet.rglob('*') if p.is_file()))
 return {'schema_version':1,'status':'INDEPENDENT_DISABLED_OPERATIONAL_V2_SOFTWARE_REVIEW','passed':all(c['passed'] for c in checks),'recorded_at':datetime.now(timezone.utc).isoformat(),'reviewer_thread_id':os.environ['CODEX_THREAD_ID'],'candidate_id':CID,'source_commit':SOURCE,'parent_commit':PARENT,'frozen_manifest':{'path':(packet/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(packet/'FROZEN.json')},'checks':checks,'scope':'Actual AST-extracted remote/local pure identity guards and full reconciliation function with external literal NSD fixtures and in-memory path/read/process stubs. Proves software identity behavior only. No native execution/resource inference. New owner activation not created or authorized.','native':'NOT_RUN','resources':'NOT_RUN','Torch_autograd':'NOT_RUN','SSH_GPU_used':False,'shared_source_main_index_ledgers_modified':False}
if __name__=='__main__':
 packet=Path(sys.argv[1]);output=Path(sys.argv[2]);result=review(packet,output)
 with output.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
 print(json.dumps({'path':str(output),'sha256':sha(output),'passed':result['passed'],'checks':len(result['checks']),'failures':[v for v in result['checks'] if not v['passed']]},ensure_ascii=False))
