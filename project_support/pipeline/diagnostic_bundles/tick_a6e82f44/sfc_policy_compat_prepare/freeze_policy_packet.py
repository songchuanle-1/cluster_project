"""Small static/AST-only policy validation and private freeze, no adapter entry."""
from pathlib import Path
from datetime import datetime,timezone
from types import SimpleNamespace
import ast,copy,hashlib,json
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
OLD=ROOT/'pipeline/diagnostic_bundles/tick_928313fd/sfc_operational_prepare'
NATIVE=ROOT/'pipeline/diagnostic_bundles/tick_928313fd/sfc_native_prepare'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(name,value):
 p=HERE/name;assert not p.exists(),name;p.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
assert not (HERE/'preparation.json').exists()
checks=[]
def check(name,value):assert value,name;checks.append(name)
newsource=(HERE/'adapter.py').read_text(encoding='utf-8');oldsource=(OLD/'adapter.py').read_text(encoding='utf-8')
provenance=read(HERE/'policy_port_provenance.json');rebuilt=oldsource
for change in provenance['ordered_literal_changes']:
 assert rebuilt.count(change['before'])==1;rebuilt=rebuilt.replace(change['before'],change['after'],1)
check('exact final adapter reproduced by eight reviewed policy-only literal edits',rebuilt==newsource)
def funcs(source):
 out={}
 for n in ast.parse(source).body:
  if isinstance(n,ast.FunctionDef):out[n.name]=ast.dump(n,include_attributes=False)
  elif isinstance(n,ast.ClassDef):out.update({n.name+'.'+f.name:ast.dump(f,include_attributes=False) for f in n.body if isinstance(f,ast.FunctionDef)})
 return out
of,nf=funcs(oldsource),funcs(newsource)
check('only guard and queue policy validator AST differ; all other 31 functions exact',of.keys()==nf.keys() and [k for k in of if of[k]!=nf[k]]==['Adapter.guard','Adapter._local_idle'])
check('remote_ops original bytes unchanged',sha(HERE/'remote_ops.py')=='37d7b75d853b601b177668b34349ae24dc3570402c914c2cdcadb1931db1418d')
native=read(NATIVE/'preparation.json')
check('original native173e whole prepared hash map unchanged',sha(NATIVE/'preparation.json')=='173e5f02eaabfa02c37ad71646f9f136d9655a771aa3baf9b4382c6b3a90da77' and all(sha(NATIVE/p)==h for p,h in native['prepared_file_hashes'].items()))
tree=ast.parse(newsource)
def constant(name):return ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)))
cap=constant('GPU_UUIDS');policy=constant('POLICY_GPU_UUIDS');grant=constant('RESOURCE_AUTHORIZATION');servers_sha=constant('SERVERS_POLICY_SHA256')
check('capability0 and policy0plus1 are separate immutable maps',list(cap)==[0] and list(policy)==[0,1] and cap[0]==policy[0])
check('new resource grant6529 and exact liveSERVERS19b hashes match',sha(ROOT/grant['path'])==grant['sha256']=='6529ecf4cb9bc39c698650e3116df67870a2f82e76c046296c8a1e74aa0d68c2' and sha(ROOT/'SERVERS.yaml')==servers_sha=='19b3753d13a8253263c6525f19a739795b816be141e21a9f9b3aaccddf4f8265')
check('original GPU0 grant retained byte-identical',sha(ROOT/'pipeline/authorizations/server4_gpu0_only_20261026.json')=='94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09')
runtime_tree=ast.parse((NATIVE/'native_runtime.py').read_text(encoding='utf-8'))
runtime_map=ast.literal_eval(next(n.value for n in runtime_tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='GPU_UUIDS' for t in n.targets)))
check('unchanged native accepts globalallowed0plus1 while physical0 hardguard remains',runtime_map==policy and 'assert type(PHYSICAL_GPU) is int and PHYSICAL_GPU == 0' in (NATIVE/'native_runtime.py').read_text(encoding='utf-8'))
klass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Adapter');guard=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=='guard')
start=next(i for i,n in enumerate(guard.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='allowed' for t in n.targets))
stop=next(i for i,n in enumerate(guard.body[start:],start) if isinstance(n,ast.If) and ast.unparse(n.test)=='gpu is not None')
fragment=guard.body[start:stop+1]
def require(value,message):
 if not value:raise ValueError(message)
def run_fragment(nodes,ns):exec(compile(ast.fix_missing_locations(ast.Module(body=copy.deepcopy(nodes),type_ignores=[])),'actual_policy_predicates_AST','exec'),ns)
def policy_case(allowed,gpu,uuids=None):
 ns={'server':{'allowed_gpus':allowed,'expected_gpu_uuids':uuids or policy},'gpu':gpu,'mutation':True,'GPU_UUIDS':cap,'POLICY_GPU_UUIDS':policy,'require':require}
 try:run_fragment(fragment,ns);return True
 except ValueError:return False
check('actual policy predicates permit exact0plus1 and select0',policy_case([0,1],0))
check('actual policy predicates reject changed malformed or partial whitelists',all(not policy_case(a,0) for a in ([0],[1,0],[0,0],[0,True],['0',1],[0,2],[])))
check('actual selected-card predicate still rejectsGPU1 bool string float',all(not policy_case([0,1],g) for g in (1,True,'0',0.0,2)))
check('actual policy UUID predicate refuses wrong other-card UUID',not policy_case([0,1],0,{0:policy[0],1:'GPU-foreign'}))
idle=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=='_local_idle');loop=next(n for n in idle.body if isinstance(n,ast.For))
def queue_case(task):
 ns={'tasks':[task],'gpu':0,'allowed':[0,1],'GPU_UUIDS':cap,'POLICY_GPU_UUIDS':policy,'require':require}
 try:run_fragment([loop],ns);return True
 except ValueError:return False
check('actual queue validator recognizes other-policyGPU1 int or string reservation',all(queue_case({'status':'running','gpu':g}) for g in (1,'1')))
check('actual queue validator refuses selected0 active or pendinguncertain',all(not queue_case(t) for t in ({'status':'running','gpu':0},{'status':'claiming','gpu':'0'},{'status':'waiting','gpu':'0','launch_verification':'pending_progress'})))
check('actual queue validator still refuses malformed or unknown reservation',all(not queue_case({'status':'running','gpu':g}) for g in (True,'2',2,None)) and not queue_case({'status':'running'}))
for p in HERE.glob('*.py'):compile(p.read_bytes(),str(p),'exec')
check('all current source compiles without importing adapter/native entries',True)
release=read(HERE/'release_template.json')
check('fresh staticrelease binds exact newcore and untouched native refs',all(release['source_hashes'][n]==sha(HERE/n) for n in ('adapter.py','remote_ops.py')) and release['native_preparation_sha256']==sha(NATIVE/'preparation.json') and release['explicit_selected_physical_GPU_capability']==[0])
check('no productionrelease currentbinding manifest lease request or execution created',not any((HERE/n).exists() for n in ('adapter_release.json','execution_binding.json','native_manifest.json','execution_lease.json','sfc_execution','prepare_request.json')))
native_template=read(NATIVE/'manifest_template.json');active=['current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit']
check('original native template active ten fields remain NULL',all(native_template[k] is None for k in active))
validation={'schema_version':1,'status':'PASS_STATIC_RESOURCE_POLICY_COMPATIBILITY_ONLY_NOT_NATIVE','recorded_at':datetime.now(timezone.utc).isoformat(),'check_count':len(checks),'checks':checks,
 'actual_AST_predicate_cases_only':True,'Torch':False,'adapter_or_native_entry_executed':False,'transport_process_GPU_Git_shared_operations':0,'native':'NOT_RUN','resources':'NOT_RUN'}
write('policy_static_validation.json',validation)
readme='''# SFC resource-policy compatibility copy

Only this new private operational origin changes. Original SFC native173e, worker edbe, source9/protocolc651, runtime1d635 and prior op packet remain byte-identical. Selected compute capability is still physicalGPU0. Global live whitelist is now exact[0,1], currentSERVERS19b and new human resourcegrant6529; old GPU0 grant940 remains immutable history.

The adapter distinguishes POLICY_GPU_UUIDS0+1 from compute GPU_UUIDS0. It validates both live policy UUIDs and exact[0,1]/max_tasks_per_gpu1, but every probe/prepare/binding/remote selected-card predicate still permits only0. Original native runtime already knows UUID0+1 and separately hardasserts physical0, so unchanged prepare/binding places liveallowed[0,1] into manifest/lease/server_binding. No native modification or artificial diagnostic-subset rewrite occurs.

The only changed method ASTs are Adapter.guard (new resourcegrant/SERVERS hash and exact live policy) and Adapter._local_idle (recognize a legitimate active GPU1 assignment without treating it as selectedGPU0 occupancy; unknown/bool/malformed assignments still refuse). All other adapter functions and entire remote_ops bytes remain unchanged: original owner/thread/context/deadline, exact source/native assets, genuine FCB parent technical receipt, UUID+idle checks, three locks, four arms, durable requests, no blind replay and readonly reconciliation remain intact. No FCB training completion/accuracy gate exists.

release_template is a new static source catalogue, not a lease/grant. adapter_release is not created; root must independently review and externally anchor the new preparation/release before any entry can transport. Current actual raw/native/resources are NOT_RUN. No active directory/binding/lease/request or GPU/remote/Git/shared action was created. Initial private guard-only WIP/source/release/provenance bytes are retained before the necessary other-card reservation parsing addition; original frozen files were never edited.

Static validation uses only AST/hash/compile and isolated actual policy predicate/queue-loop fragments with local dictionaries. It does not import/call Adapter/native entries, Torch, old software suites or remote code. Original native fullhashmap is checked for byte preservation; no model/protocol/function body is rewritten.
'''
(HERE/'README.md').write_text(readme,encoding='utf-8')
old=read(OLD/'preparation.json');owner_ast=ast.parse((HERE.parent/'anchor.py').read_text(encoding='utf-8'))
owner=next(ast.literal_eval(n.value) for n in owner_ast.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('EXPECTED','OWNER') for t in n.targets))
prepared={p.relative_to(HERE).as_posix():sha(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='preparation.json'}
prep={k:old[k] for k in ('candidate_id','experiment_id','code_commit','source_commit','source_parent_commit','expected_runtime_code_commit','native_preparation','native_manifest_template','native_source_version_binding','source_preparation','native_protocol','isolated_source_version','isolated_source_version_independent_review','conditional_parent_promotion')}
prep.update(schema_version=1,recorded_at=datetime.now(timezone.utc).isoformat(),status='STATIC_SFC_GPU0_CAPABILITY_GLOBAL_GPU01_POLICY_COMPATIBILITY_NOT_NATIVE_PASS',
 prepared_under_parent_owner=owner,static_provenance_only_not_an_execution_binding=True,draft_execution_disabled=False,
 reference_operational_preparation=ref(OLD/'preparation.json'),release_template=ref(HERE/'release_template.json'),policy_port_provenance=ref(HERE/'policy_port_provenance.json'),
 metadata_validation=ref(HERE/'policy_static_validation.json'),actual_metadata_check_count=len(checks),static_check_command='python -B pipeline/diagnostic_bundles/tick_a6e82f44/sfc_policy_compat_prepare/freeze_policy_packet.py (one-time private freeze; do not replay frozen outputs)',
 selected_GPU_capability=[0],live_resource_policy={'SERVERS_sha256':servers_sha,'allowed_gpus':[0,1],'max_tasks_per_gpu':1},resource_authorization=grant,
 previous_resource_authorization_preserved={'path':'pipeline/authorizations/server4_gpu0_only_20261026.json','sha256':'94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09'},
 native_manifest_allowed_gpus_scope='Actual fresh live whitelist[0,1]; unchanged original native accepts both UUIDs but physicalGPU hardguard0. No current active manifest.',
 all_actual_execution='NOT_RUN',native_TRAIN2='NOT_RUN',resources='NOT_RUN',efficacy='UNKNOWN',production_static_release='NOT_CREATED; root exact template copy/external anchors after independent review',
 active_binding_manifest_lease='NOT_CREATED',independent_review='EXTERNAL_PENDING_NOT_CIRCULARLY_MAPPED',prepared_file_hashes=prepared)
write('preparation.json',prep)
print(json.dumps({'preparation':ref(HERE/'preparation.json'),'adapter':sha(HERE/'adapter.py'),'remote':sha(HERE/'remote_ops.py'),'release_template':sha(HERE/'release_template.json'),'map_count':len(prepared),'checks':len(checks)}))
