"""ELC private policy-only port of the reviewed SFC compatibility logic. No entries."""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,json
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
OLD=ROOT/'pipeline/diagnostic_bundles/tick_692b4575/elc_operational_prepare'
NATIVE=ROOT/'pipeline/diagnostic_bundles/tick_692b4575/elc_native_prepare'
SFC=HERE.parent/'sfc_policy_compat_prepare'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(name,value):
 p=HERE/name;assert not p.exists(),name;p.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
assert not (HERE/'adapter.py').exists()
assert sha(OLD/'preparation.json')=='3ef93f05824b7b2833de569c0f5d09d9097806a0d2bdf5d63bb802dfe05b5ade'
assert sha(SFC/'preparation.json')=='3c76c1eb7329df2f6206eaafc4ca376b012d934ef8b99c712a709c1a02a0a058'
assert sha(SFC/'policy_static_validation.json')=='803f25c088e6f30227e3f5812cecd4a8069838545c4d5c0b911d7066b2435ae2'
peer=HERE.parent/'sfc_policy_compat_independent_review.json'
assert sha(peer)=='8ce8d9555758206d4789cc270cfce98e20b3be6909a54cd159903b02366d0abf'
assert read(peer)['material_concerns']==[]
old=read(OLD/'preparation.json');base_source=(OLD/'adapter.py').read_text(encoding='utf-8');source=base_source
plan=read(SFC/'policy_port_provenance.json')['ordered_literal_changes'];changes=[]
for item in plan:
 before=item['before'].replace('This SFC packet','This ELC packet')
 after=item['after'].replace('This SFC policy copy','This ELC policy copy')
 assert source.count(before)==1,before
 source=source.replace(before,after,1);changes.append({'before':before,'after':after})
compile(source,'private ELC policy adapter','exec');(HERE/'adapter.py').write_text(source,encoding='utf-8',newline='\n')
(HERE/'remote_ops.py').write_bytes((OLD/'remote_ops.py').read_bytes())
checks=[]
def check(name,ok):assert ok,name;checks.append(name)
def functions(s):
 out={}
 for n in ast.parse(s).body:
  if isinstance(n,ast.FunctionDef):out[n.name]=n
  elif isinstance(n,ast.ClassDef):out.update({n.name+'.'+f.name:f for f in n.body if isinstance(f,ast.FunctionDef)})
 return out
def dump(n):return ast.dump(n,include_attributes=False)
of,nf=functions(base_source),functions(source)
check('only original ELC guard and other-card reservation validator AST differ',of.keys()==nf.keys() and [k for k in of if dump(of[k])!=dump(nf[k])]==['Adapter.guard','Adapter._local_idle'])
sf=functions((SFC/'adapter.py').read_text(encoding='utf-8'))
class DiagnosticIdentity(ast.NodeTransformer):
 def visit_Constant(self,node):
  if isinstance(node.value,str):node.value=node.value.replace('ELC','SFC')
  return node
check('new guard and queue predicates exactly match independently reviewed SFC policy logic',all(dump(DiagnosticIdentity().visit(copy.deepcopy(nf[k])))==dump(sf[k]) for k in ('Adapter.guard','Adapter._local_idle')))
check('remote module byte-identical, still physical0-only',sha(HERE/'remote_ops.py')==sha(OLD/'remote_ops.py')=='0d5c76c0bb639791e31450be3fc3155432e0b31a02e9270a898d9df42f441859')
check('entire original native28ec hash map unchanged',sha(NATIVE/'preparation.json')=='28ec7b290cae00e50e30f28d9cef3d9d4ccc75cc3c4936cb15db1014a5d7cec9' and all(sha(NATIVE/n)==h for n,h in read(NATIVE/'preparation.json')['prepared_file_hashes'].items()))
newtree=ast.parse(source)
def constant(name):return ast.literal_eval(next(n.value for n in newtree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)))
grant=constant('RESOURCE_AUTHORIZATION');policy=constant('POLICY_GPU_UUIDS');cap=constant('GPU_UUIDS');servers_sha=constant('SERVERS_POLICY_SHA256')
check('new exact resourcepolicy grant/SERVERS hashes match',sha(ROOT/grant['path'])==grant['sha256']=='6529ecf4cb9bc39c698650e3116df67870a2f82e76c046296c8a1e74aa0d68c2' and sha(ROOT/'SERVERS.yaml')==servers_sha=='19b3753d13a8253263c6525f19a739795b816be141e21a9f9b3aaccddf4f8265')
check('global policy0plus1 remains separate from compute capability0',list(policy)==[0,1] and list(cap)==[0] and cap[0]==policy[0])
check('original SFCtechnicalreceipt and actualmainc9 mutation-only mother gate unchanged',old['conditional_parent_promotion']=={'expected_primary_HEAD':'c9be548699cd66bf68badff9ae6198a03eafa142','required_technical_receipt':'pipeline/admissions/M224-SFC.json','profile':'experiment_first','training_completion_or_effect_requirement':False,'applies_to_mutations_only':True} and all(dump(nf[k])==dump(of[k]) for k in ('validate_parent_technical_receipt','Adapter._require_parent_promotion','Adapter._candidate_ready')))
native_template=read(NATIVE/'manifest_template.json');active=['current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit']
check('unchanged native10activefields NULL, no actual binding',all(native_template[k] is None for k in active) and not any((HERE/n).exists() for n in ('adapter_release.json','native_manifest.json','execution_lease.json','execution_binding.json','elc_execution')))
runtime=(NATIVE/'native_runtime.py').read_text(encoding='utf-8');rt=ast.parse(runtime)
native_map=ast.literal_eval(next(n.value for n in rt.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='GPU_UUIDS' for t in n.targets)))
check('original native permits allowed0plus1 metadata but physical0 hardguard',native_map==policy and 'assert type(PHYSICAL_GPU) is int and PHYSICAL_GPU == 0' in runtime)
check('original GPU0 grant retained without rewriting',sha(ROOT/'pipeline/authorizations/server4_gpu0_only_20261026.json')=='94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09')
release=read(OLD/'release_template.json');release['source_hashes']={n:sha(HERE/n) for n in ('adapter.py','remote_ops.py')}
release['selection_scope']='Current live exact policy[0,1]/max_tasks_per_gpu1; this ELC packet can only select physicalGPU0, with future genuine SFC technicalreceipt and actual main/runtimec9. No GPU1 compute/fallback/replay/eviction or parent training completion/efficacy requirement.'
release['resource_policy']={'SERVERS_sha256':servers_sha,'authorization':grant,'live_allowed_gpus':[0,1],'selected_GPU_capability':[0],'max_tasks_per_gpu':1}
save('release_template.json',release)
check('new release binds exact new core and original native/source identity',release['code_commit']==old['code_commit']=='18e64b8d95ed0ba5c1053ead114c0f91a4b0c324' and release['native_preparation_sha256']==sha(NATIVE/'preparation.json') and release['explicit_selected_physical_GPU_capability']==[0])
for p in HERE.glob('*.py'):compile(p.read_bytes(),str(p),'exec')
check('private programs compile, no adapter/native entry imports',True)
provenance={'recorded_at':datetime.now(timezone.utc).isoformat(),'reference_operational_preparation':ref(OLD/'preparation.json'),
 'reference_module_hashes':{n:sha(OLD/n) for n in ('adapter.py','remote_ops.py')},'reference_reviewed_policy_preparation':ref(SFC/'preparation.json'),
 'reference_reviewed_policy_static_validation':ref(SFC/'policy_static_validation.json'),'reference_policy_independent_review':ref(peer),
 'ordered_literal_changes':changes,'actual_changed_function_ASTs':['Adapter.guard','Adapter._local_idle'],'all_other_adapter_function_ASTs_exact':True,
 'policy_function_AST_equal_to_reviewed_SFC_except_ELC_diagnostic_identity':True,'remote_ops_byte_identical':True,'native_preparation':ref(NATIVE/'preparation.json'),
 'scope':'Existing ELC source18e childSFCc9/worker614a/protocol7add and all native bytes unchanged. Only new static operational policy compatibility. Parent technicalreceipt/HEAD c9 remains necessary, not established by this packet; no computation or activation.'}
save('policy_port_provenance.json',provenance)
validation={'schema_version':1,'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'PASS_STATIC_ELC_RESOURCE_POLICY_COMPATIBILITY_ONLY_NOT_NATIVE','check_count':len(checks),'checks':checks,
 'scope':'Only new byte/hash/AST/parent-guard binding checks; policy predicate logic exactly matches reviewed SFC copy. No repeat of19 fixtures or prior ELC33/25/27/151 suites.','Torch':False,'adapter_or_native_entry_executed':False,'transport_process_GPU_Git_shared_operations':0,'native':'NOT_RUN','resources':'NOT_RUN'}
save('policy_static_validation.json',validation)
(HERE/'README.md').write_text('''# ELC conditional resource-policy compatibility

Only a new private operational origin is prepared. Original ELC3ef93/native28ec/worker614a/runtimef9f5/source18e(parentSFCc9)/protocol7add/source prototypec777 remain byte-identical. Current SERVERS19b/new grant6529 has live allowed[0,1]/one task per card, but this packet compute capability and entire unchanged remote module remain physicalGPU0 only. The separate policy UUID map0+1 permits live policy validation and recognition of legitimate other-GPU1 reservations; selectedGPU0 active/pending/uncertain occupancy and all malformed/unknown reservations still refuse.

Only Adapter.guard and Adapter._local_idle change. All other31 functions, original owner/context/original-deadline, assets, true SFCtechnicalreceipt/actual mainruntimec9, three locks, RPC and durable-request/no-blind-replay/readonly reconcile rules remain exact. These two policy function ASTs equal the already independently reviewed SFC policy-copy ASTs after ELC diagnostic-name normalization. No repeated fixture matrix is needed. The original native runtime already knows both UUIDs and separately hardasserts physical0; unchanged prepare/binding therefore places live allowed[0,1] into manifest/lease/server_binding without enabling nativeGPU1.

The genuine M224-SFC technical receipt and actual local/remote parentc9 prerequisite are NOT established by this packet. No SFC training completion, accuracy or gain requirement is added. No direct cumulative branch promotion is allowed. Actual ELC native/resources remain NOT_RUN and effect unknown. If main does not follow SFCc9, preserve this packet and make/test genuinely compatible source packaging.

release_template is only a new exact module/version catalogue. There is no adapter_release, binding, manifest, lease, request, execution directory or native result. Root must independently review and externally anchor any later static release before a fresh owner can run anything. No adapter/runtime/model import, Torch, SSH/GPU, Git, source/shared ledger or scheduling action occurred. Original GPU0 grant is preserved; new human GPU1 grant is explicitly pinned. This policy preparation does not activate ELC.
''',encoding='utf-8')
anchor=ast.parse((HERE.parent/'anchor.py').read_text(encoding='utf-8'));owner=next(ast.literal_eval(n.value) for n in anchor.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('EXPECTED','OWNER') for t in n.targets))
prepared={p.relative_to(HERE).as_posix():sha(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='preparation.json'}
prep={k:old[k] for k in ('candidate_id','experiment_id','code_commit','source_commit','source_parent_commit','expected_runtime_code_commit','native_preparation','native_manifest_template','native_source_version_binding','source_preparation','native_protocol','isolated_source_version','isolated_source_version_independent_review','conditional_parent_promotion')}
prep.update(schema_version=1,recorded_at=datetime.now(timezone.utc).isoformat(),status='STATIC_CONDITIONAL_ELC_GPU0_CAPABILITY_GLOBAL_GPU01_POLICY_COMPATIBILITY_NOT_NATIVE_PASS',prepared_under_parent_owner=owner,
 static_provenance_only_not_an_execution_binding=True,draft_execution_disabled=False,reference_operational_preparation=ref(OLD/'preparation.json'),reference_reviewed_policy_preparation=ref(SFC/'preparation.json'),
 release_template=ref(HERE/'release_template.json'),policy_port_provenance=ref(HERE/'policy_port_provenance.json'),metadata_validation=ref(HERE/'policy_static_validation.json'),actual_metadata_check_count=len(checks),
 static_check_command='python -B pipeline/diagnostic_bundles/tick_a6e82f44/elc_policy_compat_prepare/prepare_policy_packet.py (one-time private author/freeze; do not replay frozen outputs)',selected_GPU_capability=[0],
 live_resource_policy={'SERVERS_sha256':servers_sha,'allowed_gpus':[0,1],'max_tasks_per_gpu':1},resource_authorization=grant,
 previous_resource_authorization_preserved={'path':'pipeline/authorizations/server4_gpu0_only_20261026.json','sha256':'94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09'},
 native_manifest_allowed_gpus_scope='Future fresh live whitelist[0,1] in metadata; original native accepts both UUIDs but physicalGPU hardguard0. No active manifest/lease.',
 all_actual_execution='NOT_RUN',native_TRAIN2='NOT_RUN',resources='NOT_RUN',efficacy='UNKNOWN',production_static_release='NOT_CREATED; future root exact template copy/external anchors after independent review',
 active_binding_manifest_lease='NOT_CREATED',parent_technical_readiness='NOT_ESTABLISHED_BY_THIS_PACKET',independent_review='EXTERNAL_PENDING_NOT_CIRCULARLY_MAPPED',prepared_file_hashes=prepared)
save('preparation.json',prep)
print(json.dumps({'preparation':ref(HERE/'preparation.json'),'adapter':sha(HERE/'adapter.py'),'remote':sha(HERE/'remote_ops.py'),'release_template':sha(HERE/'release_template.json'),'checks':len(checks),'map_count':len(prepared)}))
