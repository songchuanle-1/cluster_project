"""One-time private authoring; never imports the adapter, Torch, or any entry point."""
from pathlib import Path
from datetime import datetime, timezone
import ast, copy, hashlib, io, json, os, shutil, tokenize

HERE=Path(__file__).resolve().parent
TICK=HERE.parent
ROOT=TICK.parents[2]
OLD=ROOT/'pipeline/diagnostic_bundles/tick_34f4e385/wfc_native_prepare'
NATIVE=TICK/'wfc_native_activation_prepare'
REFERENCE=ROOT/'pipeline/diagnostic_bundles/tick_a6e82f44/sfc_policy_compat_prepare'
CID='hierarchy-wedge-factor-incidence-composition'
COMMIT='94c4fe61b38f46f321a7ee84236fea70ade04d9b'
PARENT='18e64b8d95ed0ba5c1053ead114c0f91a4b0c324'
ACTIVE=('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def ref(p):return {'path':Path(p).resolve().relative_to(ROOT).as_posix(),'sha256':sha(p)}
def author_guard():
    a=ast.parse((TICK/'anchor.py').read_text(encoding='utf-8'));values={}
    for node in a.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('EXPECTED','CHECKS'):
            values[node.targets[0].id]=ast.literal_eval(node.value)
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert {k:owner.get(k) for k in values['EXPECTED']}==values['EXPECTED']
    mode=read(ROOT/'pipeline/execution_mode.json')
    assert mode['mode']=='foreground' and mode['target_thread_id']==owner['thread_id']
    assert os.environ.get('CODEX_THREAD_ID') and os.environ['CODEX_THREAD_ID']!=owner['thread_id']
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    for name,h in values['CHECKS'].items():assert sha(ROOT/name)==h,name
    return values['EXPECTED']
def write(p,data):
    author_guard();p=Path(p).resolve()
    assert p.is_relative_to(HERE) or p.is_relative_to(NATIVE)
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(data if isinstance(data,bytes) else data.encode('utf-8'))
def save(p,obj):write(p,json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def functions(source):
    a=ast.parse(source);return {n.name:ast.dump(n,include_attributes=False) for n in a.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
def methods(source):
    a=ast.parse(source);return {n.name:ast.dump(n,include_attributes=False) for c in a.body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef)}

owner=author_guard()
assert sha(OLD/'preparation.json')=='af6d4dd62858baaad4fb773909e2219f9e39c5c2752ebf626f20feae56790e20'
oldprep=read(OLD/'preparation.json');oldtemplate=read(OLD/'manifest_template.json')
for n,h in oldprep['prepared_file_hashes'].items():assert sha(OLD/n)==h,n
assert all(oldtemplate[k] is None for k in ACTIVE)
for n in oldtemplate['diagnostic_files']:
    if n!='native_runtime.py':write(NATIVE/n,(OLD/n).read_bytes())
oldruntime=(OLD/'native_runtime.py').read_text(encoding='utf-8')
assert oldruntime.count('DRAFT_EXECUTION_DISABLED = True')==1
runtime=oldruntime.replace('DRAFT_EXECUTION_DISABLED = True','DRAFT_EXECUTION_DISABLED = False')
assert functions(runtime)==functions(oldruntime)
write(NATIVE/'native_runtime.py',runtime)
template=copy.deepcopy(oldtemplate)
template['draft_execution_disabled']=False
template['diagnostic_files']['native_runtime.py']=sha(NATIVE/'native_runtime.py')
template['protocol']=template['protocol'].replace('DRAFTTrue/10activeNULL/nativeNOT_RUN; future reviewed activation+freshowner/idlephysical0/three locks required.','Formal activation copy/10activeNULL/nativeNOT_RUN; external reviewed release plus freshowner/idlephysical0/three locks required.')
assert template['protocol']!=oldtemplate['protocol']
save(NATIVE/'manifest_template.json',template)
save(NATIVE/'activation_provenance.json',dict(owner=owner,actual_child_thread_id=os.environ['CODEX_THREAD_ID'],root_thread_not_impersonated=True,old_preparation=ref(OLD/'preparation.json'),old_independent_review=ref(OLD.parent/'wfc_native_preparation_independent_review.json'),runtime_exact_one_flag_change=True,all_runtime_functions_AST_unchanged=True,worker_byte_identical=True,source_binding_byte_identical=True,source9_byte_identical=True,old_draft_unchanged=True,ten_active_fields_NULL=True,actual_native_resources='NOT_RUN',scope='Separate formal static capability only. Original af6d remains DRAFTTrue; inherited source-binding prose describes that historical draft. No active binding, release, remote directory, request, compute, admission, or ready claim.'))
write(NATIVE/'README.md','# WFC static native activation copy\n\nExact af6d worker, source binding, candidate8 and original YAML. Runtime differs only in DRAFT_EXECUTION_DISABLED=False; its nine function ASTs are unchanged. Template records the new runtime SHA and false draft metadata; ten execution fields remain null. The original draft is preserved. A missing manifest fails before Torch; this packet itself is not an execution lease or native/resource PASS. Source94c4 is a nine-addition child of expected runtime18e.\n')
native_validation=dict(status='STATIC_ACTIVATION_METADATA_VALIDATED_NOT_NATIVE_PASS',checks=['old20-map exact','worker byte exact','candidate8 and YAML exact','source binding exact','runtime exact one flag','runtime all9 function AST exact','template original assets/science/source metadata exact except declared draft and runtime hash','active10 null','no active manifest/lease/result/release'],actual_native_resources='NOT_RUN')
save(NATIVE/'static_validation.json',native_validation)
np=copy.deepcopy(oldprep)
np.update(recorded_at=datetime.now(timezone.utc).isoformat(),status='FORMAL_STATIC_WFC_NATIVE_CAPABILITY_PREPARED_NOT_EXECUTED',draft_execution_disabled=False,operational_ready=False,scope='Separate static activation from af6d; requires reviewed operational external anchors, real current owner and actual idle physicalGPU0. No active manifest, lease, request, native/resource result or admission.',original_draft_preparation=ref(OLD/'preparation.json'),original_draft_independent_review=ref(OLD.parent/'wfc_native_preparation_independent_review.json'),activation_provenance=ref(NATIVE/'activation_provenance.json'),manifest_template=ref(NATIVE/'manifest_template.json'),runtime=ref(NATIVE/'native_runtime.py'),worker=ref(NATIVE/'worker.py'),source_version_binding=ref(NATIVE/'source_version_binding.json'),static_validation=ref(NATIVE/'static_validation.json'),static_check_command='One-time private assemble_packet.py metadata assertions; no native or entry execution',actual_static_check_count=len(native_validation['checks']))
for k in ['launcher_plan']:np.pop(k,None)
np['prepared_file_hashes']={p.relative_to(NATIVE).as_posix():sha(p) for p in sorted(NATIVE.rglob('*')) if p.is_file()}
save(NATIVE/'preparation.json',np)

# Transform STRING tokens only. Python identifiers and dict/schema keys are not
# replaced by substring substitutions; every literal change is recorded.
literal_plan=[
 ('pipeline/diagnostic_bundles/tick_928313fd/sfc_native_prepare','pipeline/diagnostic_bundles/tick_85772373/wfc_native_activation_prepare'),
 ('173e5f02eaabfa02c37ad71646f9f136d9655a771aa3baf9b4382c6b3a90da77',sha(NATIVE/'preparation.json')),
 ('154f7ade2cc67741d02c0eb2e9b79701244c56c2f5462efa57c171dc6c0d7de9',sha(NATIVE/'manifest_template.json')),
 ('c9be548699cd66bf68badff9ae6198a03eafa142',COMMIT),
 ('d4d062ef075abfe7cde93d4b4347ce146572762f',PARENT),
 ('hierarchy-synchronous-full-neighbor-composition',CID),
 ('hierarchy-fine-coarse-complete-bipartite-composition','hierarchy-undirected-edge-state-line-graph-composition'),
 ('M224-SFC','M226-WFC'),('M223-FCB','M225-ELC'),
 ('ctf_hcg_csort_fcb','ctf_hcg_csort_elc'),('_fcb.yaml','_elc.yaml'),
 ('/M223-FCB.json','/M225-ELC.json'),
 ('sfc_remote_ops','wfc_remote_ops'),('sfc_execution','wfc_execution'),('sfc_','wfc_'),('_sfc','_wfc'),
 ('SFC','WFC'),('FCB','ELC'),('parentd4d','parent18e'),('promoted ELCd4d','promoted ELC18e')]
changes=[]
def port(source,label):
    tokens=[]
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type==tokenize.STRING:
            value=ast.literal_eval(tok.string)
            if isinstance(value,str):
                new=value
                for old,replacement in literal_plan:new=new.replace(old,replacement)
                if new!=value:
                    changes.append(dict(file=label,line=tok.start[0],old=value,new=new))
                    tok=tok._replace(string=repr(new))
        tokens.append(tok)
    return tokenize.untokenize(tokens)
for n in ['adapter.py','remote_ops.py']:
    source=(REFERENCE/n).read_text(encoding='utf-8');target=port(source,n)
    compile(target,n,'exec');write(HERE/n,target)

adapter=(HERE/'adapter.py').read_text(encoding='utf-8')
assert 'PARENT_EXPERIMENT = \'M225-ELC\'' in adapter
assert "PARENT_CANDIDATE = 'hierarchy-undirected-edge-state-line-graph-composition'" in adapter
assert "self.root/'pipeline/admissions/M225-ELC.json'" in adapter
assert "PARENT_CONFIG = 'configs/Quard/ctf_hcg_csort_elc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_elc.yaml'" in adapter
assert COMMIT in adapter and PARENT in adapter and sha(NATIVE/'preparation.json') in adapter

release=read(REFERENCE/'release_template.json')
def port_obj(x):
    if isinstance(x,str):
        for old,new in literal_plan:x=x.replace(old,new)
        return x
    if isinstance(x,list):return [port_obj(v) for v in x]
    if isinstance(x,dict):return {k:port_obj(v) for k,v in x.items()}
    return x
release=port_obj(release)
release['source_version_binding_sha256']=sha(NATIVE/'source_version_binding.json')
release['source_hashes']={n:sha(HERE/n) for n in ['adapter.py','remote_ops.py']}
save(HERE/'release_template.json',release)

launcher='''"""Default NOP. Each explicit root operation executes at most one original request."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, subprocess, sys
HERE=Path(__file__).resolve().parent
ROOT=Path('D:/project/cluster_project')
EXPECTED_RUNTIME='18e64b8d95ed0ba5c1053ead114c0f91a4b0c324'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump_x(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False)
def snapshot(owner):
    baseline=read(ROOT/'pipeline/diagnostic_bundles'/('tick_'+owner['token'][:8])/'protected_assets_before.json')
    git=['C:/Program Files (x86)/Git/cmd/git.exe','--no-optional-locks','-c','core.fsmonitor=false','-C',str(ROOT/'Cluster')]
    def query(*args):return subprocess.check_output(git+list(args),env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0'))
    assert query('rev-parse','HEAD').decode().strip()==EXPECTED_RUNTIME
    assert not query('diff','--cached','--name-only','-z')
    index=Path(query('rev-parse','--git-path','index').decode().strip())
    if not index.is_absolute():index=ROOT/'Cluster'/index
    return dict(primary=EXPECTED_RUNTIME,index=sha(index),status_hex=query('status','--porcelain=v1','--untracked-files=all','-z').hex(),user_files={n:sha(ROOT/'Cluster'/n) for n in baseline['files']},ledgers={n:sha(ROOT/'pipeline'/n) for n in baseline['protected_ledgers']},work=sha(ROOT/'pipeline/research_work.json'),memory=sha(ROOT/'pipeline/codex_memory.md'))
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute-root',action='store_true')
    p.add_argument('--operation',choices=['probe','prepare','stage','run','status','reconcile'])
    p.add_argument('--mode',choices=['smoke','resources'])
    p.add_argument('--target',choices=['champion','candidate'])
    p.add_argument('--request-id');p.add_argument('--local-only',action='store_true')
    a=p.parse_args()
    if not a.execute_root:
        print(json.dumps(dict(status='DEFAULT_NOP_NO_ENTRY_OR_TRANSPORT',candidate_id='hierarchy-wedge-factor-incidence-composition',code_commit='94c4fe61b38f46f321a7ee84236fea70ade04d9b',selected_physical_gpu=0,active_binding_created=False,native_executed=False)));return
    assert a.operation is not None and sys.dont_write_bytecode
    spec=importlib.util.spec_from_file_location('wfc_reviewed_adapter',HERE/'adapter.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    adapter=module.Adapter()
    mutation=a.operation in ('prepare','stage','run')
    remaining=1020 if a.operation=='run' else 420 if a.operation=='stage' else 360 if a.operation=='prepare' else 60
    current=adapter.guard(remaining,0,mutation=mutation)
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        current=adapter.guard(remaining,0,mutation=mutation)
        before=snapshot(current['owner']);directory=adapter._directory(current)
        if mutation:
            adapter._local_idle(0)
            if a.operation=='run':assert (a.mode,a.target) in module.PAIRS
            name=a.operation+('_'+a.mode+'_'+a.target if a.operation=='run' else '')
            journal=ROOT/'pipeline/diagnostic_bundles'/('tick_'+current['owner']['token'][:8])/('wfc_root_'+name+'_intent.json')
            assert not journal.exists(),'Original wrapper attempt exists; reconcile, never replay.'
            adapter.guard(remaining,0,mutation=True)
            dump_x(journal,dict(owner={k:current['owner'][k] for k in ('token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256')},operation=a.operation,mode=a.mode,target=a.target,protected_before=before))
        if a.operation in ('probe','prepare'):result=getattr(adapter,a.operation)(0)
        elif a.operation=='run':result=adapter.run(a.mode,a.target)
        elif a.operation=='status':result=adapter.status(remote=not a.local_only)
        elif a.operation=='reconcile':result=adapter.reconcile(a.request_id)
        else:result=adapter.stage()
        adapter.guard(0,0,mutation=False)
        assert snapshot(current['owner'])==before,'Shared/source protection changed; preserve evidence, no replay.'
        print(json.dumps(dict(operation=a.operation,result=result,protected_source_and_lifecycle_unchanged=True),indent=2,allow_nan=False))
    finally:lock.close()
if __name__=='__main__':main()
'''
compile(launcher,'run_wfc_operation.py','exec');write(HERE/'run_wfc_operation.py',launcher)
save(HERE/'literal_port_provenance.json',dict(reference_preparation=ref(REFERENCE/'preparation.json'),reference_adapter=ref(REFERENCE/'adapter.py'),reference_remote=ref(REFERENCE/'remote_ops.py'),literal_plan=literal_plan,actual_STRING_token_changes=changes,identifiers_and_schema_not_substring_replaced=True,root_owner=owner,actual_child_thread_id=os.environ['CODEX_THREAD_ID'],root_thread_not_impersonated=True))
write(HERE/'README.md','# WFC guarded operational preparation\n\nSource94c4 is an exact9 child18e. Native activation is separately frozen in sibling wfc_native_activation_prepare; original af6d draft is untouched. The original worker/science/protocol/resources remain byte/AST unchanged. PhysicalGPU0 only, live authorized[0,1]; a legal running/reserved GPU1 does not invalidate GPU0, but selectedGPU0 must have no registered or pending/uncertain claim and must be physically idle with its exact UUID and all three locks available. Never evict, reset or use fallback GPU1.\n\nNo production adapter_release.json, manifest, lease, remote stage, request or result exists in this preparation. Root must externally review/register native and this exact package, then copy release_template.json exactly to adapter_release.json. The default root launcher is NOP. Future use still needs the actual current owner/context/pending/deadline, intended runtime18e and genuine parent ELC technical receipt. A changed runtime requires separately binding a truly compatible tested version, not a blind ff.\n\nExplicit root commands use python -B run_wfc_operation.py --execute-root --operation prepare, then stage, then one run --mode smoke/resources --target champion/candidate per original four-arm request. Each run requires >1020 seconds remaining. Local/remote uncertainty preserves original IDs and requires status/reconcile; never replay a mutation. No admission/queue or formal training is generated here. Both current original jobs must remain untouched.\n')
checks=[]
def check(value,label):assert value,label;checks.append(label)
check(all(template[k] is None for k in ACTIVE),'active10NULL')
check((NATIVE/'worker.py').read_bytes()==(OLD/'worker.py').read_bytes(),'worker exact old af6d')
check((NATIVE/'source_version_binding.json').read_bytes()==(OLD/'source_version_binding.json').read_bytes(),'source binding exact')
check(functions(runtime)==functions(oldruntime),'all native runtime function AST identical')
oldworker=ast.parse((OLD/'worker.py').read_text(encoding='utf-8'));newworker=ast.parse((NATIVE/'worker.py').read_text(encoding='utf-8'))
check(ast.dump(oldworker,include_attributes=False)==ast.dump(newworker,include_attributes=False),'all worker AST including resources identical')
check(not any((HERE/n).exists() for n in ['adapter_release.json','native_manifest.json','execution_lease.json','execution_binding.json']),'no release or active artifacts')
check(not any((NATIVE/n).exists() for n in ['native_manifest.json','execution_lease.json','execution_binding.json']),'native no active artifacts')
for name,h in oldprep['source_files'].items():
    path=NATIVE/'candidate.yaml' if name.endswith('.yaml') else NATIVE/'candidate_model'/Path(name).name
    check(sha(path)==h,'source exact '+Path(name).name)
# Actual extracted queue-reservation method: legal other GPU1 accepted; selected
# GPU0/unknown/bool/uncertain reservations refused, without importing Adapter.
a=ast.parse(adapter);cls=next(n for n in a.body if isinstance(n,ast.ClassDef) and n.name=='Adapter');idle=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_local_idle')
class Refusal(Exception):pass
def require(ok,reason):
    if not ok:raise Refusal(reason)
class FakeYaml:
    @staticmethod
    def safe_load(_):return {'servers':{'server-4':{'allowed_gpus':[0,1]}}}
class FakeFile:
    def __truediv__(self,_):return self
    def read_text(self,**_):return ''
class FakeSelf:root=FakeFile()
fixture={'running':{},'tasks':[]}
def fake_read(_):
    fake_read.calls+=1
    return {'server-4':fixture['running']} if fake_read.calls%2 else {'gpu_queues':{'server-4':fixture['tasks']}}
fake_read.calls=0
ns={'read':fake_read,'require':require,'yaml':FakeYaml,'POLICY_GPU_UUIDS':{0:'g0',1:'g1'}}
exec(compile(ast.Module(body=[idle],type_ignores=[]),'actual_queue_method','exec'),ns)
for task,refuse,label in [({'status':'running','gpu':'1'},False,'legal other GPU1 running'),({'status':'running','gpu':0},True,'selectedGPU0 reserved'),({'status':'running','gpu':True},True,'bool GPU rejected'),({'status':'running','gpu':'2'},True,'unknownGPU rejected'),({'status':'waiting','gpu':0,'launch_verification':'pending_progress'},True,'selected pending claim rejected')]:
    fixture['tasks']=[task];caught=False
    try:ns['_local_idle'](FakeSelf(),0)
    except Refusal:caught=True
    check(caught==refuse,label)
# Execute only native pre-manifest AST prefix: formal False reaches missing
# manifest before Torch/CUDA/NVML/filesystem writes; no full module import.
prefix=[]
for node in ast.parse(runtime).body:
    if isinstance(node,ast.Import) and any(x.name=='os' for x in node.names):break
    prefix.append(node)
env={};exec(compile(ast.Module(body=prefix,type_ignores=[]),'native_formal_prefix','exec'),env)
check(env['DRAFT_EXECUTION_DISABLED'] is False,'formal prefix permitted only with exact known source metadata')
check('torch' not in env,'formal prefix imports no Torch')
check(all(x in adapter for x in ['self._require_parent_promotion(ref)','self._candidate_ready(ref)',"allowed==[0,1]",'POLICY_GPU_UUIDS']),'parent/current candidate/live policy wiring retained')
for n in ['adapter.py','remote_ops.py','run_wfc_operation.py']:compile((HERE/n).read_text(encoding='utf-8'),n,'exec');checks.append('compile '+n)
save(HERE/'static_validation.json',dict(status='STATIC_OPERATIONAL_METADATA_AND_BOUNDED_CONTROLS_PASSED_NOT_NATIVE_PASS',actual_check_count=len(checks),checks=checks,actual_native_resources='NOT_RUN',Torch_or_entry_import=False,remote_transport=False,root_guard_not_executed_or_impersonated=True,scope='Actual extracted queue method synthetic fixtures; exact token port/hash/AST/compile and pre-manifest prefix only. No model forward or old suite.'))
op=dict(schema_version=1,recorded_at=datetime.now(timezone.utc).isoformat(),status='STATIC_WFC_NATIVE_ACTIVATION_AND_OPERATIONAL_PREPARATION_NOT_EXECUTED',candidate_id=CID,experiment_id='M226-WFC',code_commit=COMMIT,source_commit=COMMIT,source_parent_commit=PARENT,expected_runtime_code_commit=PARENT,draft_execution_disabled=False,operational_ready=False,prepared_under_parent_owner=owner,actual_author_child_thread_id=os.environ['CODEX_THREAD_ID'],static_provenance_only_not_execution_binding=True,native_preparation=ref(NATIVE/'preparation.json'),native_manifest_template=ref(NATIVE/'manifest_template.json'),native_source_version_binding=ref(NATIVE/'source_version_binding.json'),original_draft_preparation=ref(OLD/'preparation.json'),original_draft_independent_review=ref(OLD.parent/'wfc_native_preparation_independent_review.json'),source_preparation=oldprep['source_preparation'],native_protocol=oldprep['native_protocol'],isolated_source_version=oldprep['isolated_source_version'],reference_operational_preparation=ref(REFERENCE/'preparation.json'),release_template=ref(HERE/'release_template.json'),root_launcher=ref(HERE/'run_wfc_operation.py'),literal_port_provenance=ref(HERE/'literal_port_provenance.json'),metadata_validation=ref(HERE/'static_validation.json'),selected_GPU_capability=[0],live_resource_policy=dict(allowed_gpus=[0,1],max_tasks_per_gpu=1),resource_authorization=release['resource_policy']['authorization'],conditional_parent_promotion=release['conditional_parent_promotion'],active_binding_manifest_lease='NOT_CREATED',production_static_release='NOT_CREATED; exact template copy and external review anchors required',all_actual_execution='NOT_RUN',native_TRAIN2='NOT_RUN',resources='NOT_RUN',efficacy='UNKNOWN',scientific_admission=False,independent_review='EXTERNAL_PENDING_NOT_CIRCULARLY_MAPPED')
op['prepared_file_hashes']={p.relative_to(HERE).as_posix():sha(p) for p in sorted(HERE.rglob('*')) if p.is_file()}
save(HERE/'preparation.json',op)
print(json.dumps(dict(native_preparation=ref(NATIVE/'preparation.json'),operational_preparation=ref(HERE/'preparation.json'),runtime=ref(NATIVE/'native_runtime.py'),template=ref(NATIVE/'manifest_template.json'),adapter=ref(HERE/'adapter.py'),remote=ref(HERE/'remote_ops.py'),release_template=ref(HERE/'release_template.json'),root_launcher=ref(HERE/'run_wfc_operation.py'),static_validation=ref(HERE/'static_validation.json'),checks=len(checks))))
