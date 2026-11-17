"""Small disposable software metadata checks. No actual project guard, SSH or native run."""
import ast
import copy
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
BASE=ROOT/'pipeline/diagnostic_bundles/tick_64ac844e/bfc_operational_prepare'
checks=[]
def check(name,condition):
    if not condition:raise AssertionError(name)
    checks.append(name)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def audit(event,args):
    if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.__new__','socket.connect','socket.bind','socket.getaddrinfo'):raise AssertionError('Forbidden real action: '+event)
    if event=='import' and args and str(args[0]).split('.')[0]=='torch':raise AssertionError('Forbidden Torch import')
def funcs(path):
    out={}
    def visit(nodes,prefix=''):
        for n in nodes:
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):out[prefix+n.name]=ast.dump(n,include_attributes=False)
            elif isinstance(n,ast.ClassDef):visit(n.body,prefix+n.name+'.')
    visit(ast.parse(path.read_text('utf-8')).body);return out

def main():
    sys.addaudithook(audit)
    for name in ('adapter.py','remote_ops.py'):
        source=(HERE/name).read_text('utf-8');compile(source,str(HERE/name),'exec');check(name+'_AST_compile',True)
    spec=importlib.util.spec_from_file_location('aef_software_adapter',HERE/'adapter.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    check('only_GPU0_capability',m.GPU_UUIDS=={0:'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'})
    check('AEF_source_actual_namespace',m.CANDIDATE=='hierarchy-parent-antisymmetric-edge-flux' and m.COMMIT=='56b2a96dc48cc8a88f0f7105527ef448113b1060' and m.EXPECTED_RUNTIME_COMMIT=='026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563')
    check('actual_final_native_hashes_bound',all(isinstance(x,str) and len(x)==64 and all(c in '0123456789abcdef' for c in x) for x in (m.PREPARATION_SHA,m.TEMPLATE_SHA)))
    check('actual_final_native_preparation_and_template_SHA',sha(m.FROZEN/'preparation.json')==m.PREPARATION_SHA and sha(m.FROZEN/'manifest_template.json')==m.TEMPLATE_SHA)
    native=json.loads((m.FROZEN/'preparation.json').read_text('utf-8'));template=json.loads((m.FROZEN/'manifest_template.json').read_text('utf-8'))
    check('native_frozen_candidate_version',native['candidate_id']==m.CANDIDATE and native['source_commit']==m.COMMIT and template['candidate_id']==m.CANDIDATE and template['code_commit']==m.COMMIT)
    active=('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')
    check('actual_template_ten_active_fields_all_null',all(k in template and template[k] is None for k in active))
    class NoTransport:
        def call(self,*args,**kwargs):raise AssertionError('No fake or actual transport expected')
    with tempfile.TemporaryDirectory(prefix='aef_metadata_',dir=HERE) as tmp:
        r=Path(tmp);(r/'pipeline').mkdir();(r/'SERVERS.yaml').write_text(yaml.safe_dump({'servers':{'server-4':{'allowed_gpus':[0]}}}),encoding='utf-8')
        adapter=m.Adapter(root=r,transport=NoTransport(),origin=HERE,frozen=m.FROZEN)
        for method in ('probe','prepare'):
            for gpu in (1,False,None):
                try:getattr(adapter,method)(gpu)
                except m.Refused:check(method+'_reject_'+repr(gpu)+'_before_guard_transport',True)
                else:raise AssertionError('Invalid GPU admitted')
        good={'id':m.CANDIDATE,'experiment_id':'M216-AEF','code_commit':m.COMMIT,'goal_sha256':m.GOAL,'authorization':{'path':'software.json','sha256':'0'*64},'config':'actual_aef_config','stage':'validation'}
        adapter._frozen_details=lambda:({}, {'config':'actual_aef_config'})
        def candidate(value):
            (r/'pipeline/research_work.json').write_text(json.dumps({'candidates':[value]}),encoding='utf-8')
            adapter._candidate_ready(good['authorization'])
        candidate(good);check('AEF_metadata_eligible_without_revision',True)
        for key,value in [('revision_history',[{'revision':1}]),('implementation_revision_sha256','x'),('human_hold',True),('code_commit','9'*40),('experiment_id','M215-BEC')]:
            wrong=copy.deepcopy(good);wrong[key]=value
            try:candidate(wrong)
            except m.Refused:check('candidate_reject_'+key,True)
            else:raise AssertionError('Candidate metadata drift admitted')
        for state in ('running','claiming'):
            (r/'pipeline/running.json').write_text('{}',encoding='utf-8');(r/'pipeline/queue.json').write_text(json.dumps({'gpu_queues':{'server-4':[{'id':'M215-BEC','status':state,'gpu':'0'}]}}),encoding='utf-8')
            try:adapter._local_idle(0)
            except m.Refused:check('registered_'+state+'_refuses_before_transport',True)
            else:raise AssertionError('Registered busy accepted')
        (r/'pipeline/running.json').write_text(json.dumps({'server-4':{'0':'M215-BEC'}}),encoding='utf-8')
        try:adapter._local_idle(0)
        except m.Refused:check('running_map_busy_refuses',True)
        else:raise AssertionError('Busy map accepted')
        probe={'server_id':'server-4','hostname':'dl04-MS-7E06','root':m.REMOTE_ROOT,'physical_gpu':0,'gpu_uuid':m.GPU_UUIDS[0],'runtime_code_commit':m.EXPECTED_RUNTIME_COMMIT,'idle':True,'contexts':[],'memory_used_mib':41,'utilization_percent':0,'locks':{k:'available' for k in ('training','diagnostic','exclusive')}}
        adapter._check_probe(probe,0);check('software_schema_probe_exact_runtime',True)
        for key,value in [('runtime_code_commit','0'*40),('idle',False),('gpu_uuid','wrong')]:
            wrong=copy.deepcopy(probe);wrong[key]=value
            try:adapter._check_probe(wrong,0)
            except m.Refused:check('probe_reject_'+key,True)
            else:raise AssertionError('Bad observation accepted')
    def normalized(source):
        return source.replace('hierarchy-parent-butterfly-token-composition','hierarchy-parent-antisymmetric-edge-flux').replace('48fc302c3c02ffef0b241be3593c386b6b65a72e','56b2a96dc48cc8a88f0f7105527ef448113b1060').replace('M213-BFC','M216-AEF').replace('BFC','AEF').replace('bfc','aef')
    transport_old=ast.parse(normalized((BASE/'adapter.py').read_text('utf-8')))
    transport_old=next(x for x in transport_old.body if isinstance(x,ast.ClassDef) and x.name=='SSHTransport')
    transport_new=next(x for x in ast.parse((HERE/'adapter.py').read_text('utf-8')).body if isinstance(x,ast.ClassDef) and x.name=='SSHTransport')
    check('SSH_transport_AST_same_after_required_namespace_literal',ast.dump(transport_old)==ast.dump(transport_new))
    old_functions=funcs(BASE/'remote_ops.py');new_functions=funcs(HERE/'remote_ops.py')
    changed_remote=[name for name in old_functions if old_functions[name]!=new_functions[name]]
    check('RPC_controlflow_changed_only_namespace_GPU0_text_metadata',set(changed_remote)=={'binding_stage','probe','result_matches'})
    for name in ['run_operation','stage_operation','require_fresh','require_idle','native_verify','exact_workers','process_info','reconcile_operation','dispatch']:
        check('remote_'+name+'_entire_AST_exact',old_functions[name]==new_functions[name])
    source=(HERE/'adapter.py').read_text('utf-8');tree=ast.parse(source)
    run=next(n for c in tree.body if isinstance(c,ast.ClassDef) and c.name=='Adapter' for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='run')
    check('1020s_original_required_run_window',source.count('required_seconds=1020')==2)
    check('no_revision_or_BEC_science_inheritance','preregistration' not in source and 'M215-BEC' not in source and '5module' not in source and '12block' not in source)
    check('no_production_release_manifest_lease_or_binding',not any((HERE/n).exists() for n in ['adapter_release.json','native_manifest.json','execution_lease.json','execution_binding.json']))
    report={'status':'DISPOSABLE_METADATA_SOFTWARE_CHECKS_PASSED_NOT_NATIVE','recorded_at':datetime.now(timezone.utc).isoformat(),'logical_checks_count':len(checks),'checks':checks,'source_hashes':{n:sha(HERE/n) for n in ('adapter.py','remote_ops.py')},'scope':'Only isolated temporary metadata fixtures, production AST/compile and explicit invalid-GPU refusal methods. No actual project guard or adapter operation, no subprocess/network/Torch/Git/SSH/GPU/native/standard_PASS/receipt/queue.','actual_execution':'NOT_RUN','material_concerns':[]}
    out=HERE/'metadata_validation.json'
    with out.open('x',encoding='utf-8') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps({'checks':len(checks),'report':str(out),'sha256':sha(out),'actual_execution':'NOT_RUN'}))

if __name__=='__main__':main()
