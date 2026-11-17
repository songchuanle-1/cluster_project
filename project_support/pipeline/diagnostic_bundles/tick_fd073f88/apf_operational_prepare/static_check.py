"""Bounded stdlib metadata-port validation, no adapter entry/import/transport."""
from pathlib import Path
from types import SimpleNamespace
import ast,copy,hashlib,json,re
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
NATIVE=HERE.parent/'apf_native_prepare'
checks=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(n,v):
    assert v,n
    checks.append({'name':n,'passed':True})
def fn(tree,name):return next(x for x in ast.walk(tree) if isinstance(x,ast.FunctionDef) and x.name==name)
def refuse(c,message):
    if not c:raise RuntimeError(message)
port=json.loads((HERE/'port_provenance.json').read_text());trees={}
for n,details in port['ports'].items():
    original=ROOT/details['reference']['path'];check('original_hash_'+n,sha(original)==details['reference']['sha256'])
    text=original.read_text()
    for item in details['literal_changes']:
        check('literal_count_'+n+'_'+str(len(checks)),text.count(item['old'])==item['replacements']);text=text.replace(item['old'],item['new'])
    current=(HERE/n).read_text();check('exact_allowed_transform_'+n,current==text)
    compile(current,str(HERE/n),'exec');trees[n]=ast.parse(current)
    expected=ast.parse(text);check('all_function_AST_'+n,[ast.dump(x,include_attributes=False) for x in ast.walk(trees[n]) if isinstance(x,ast.FunctionDef)]==[ast.dump(x,include_attributes=False) for x in ast.walk(expected) if isinstance(x,ast.FunctionDef)])
release=json.loads((HERE/'release_template.json').read_text());native=json.loads((NATIVE/'preparation.json').read_text());template=json.loads((NATIVE/'manifest_template.json').read_text())
check('native_prep_ref',sha(NATIVE/'preparation.json')==release['native_preparation_sha256'])
check('template_ref',sha(NATIVE/'manifest_template.json')==release['manifest_template_sha256'])
check('binding_ref',sha(NATIVE/'source_version_binding.json')==release['source_version_binding_sha256'])
for n,h in release['source_hashes'].items():check('module_hash_'+n,sha(HERE/n)==h)
check('ten_active_null',all(v is None for v in native['manifest_execution_fields'].values()) and len(native['manifest_execution_fields'])==10)
check('no_production_release_or_active',not any((HERE/n).exists() for n in ('adapter_release.json','execution_binding.json','native_manifest.json','execution_lease.json')))
# Extract actual metadata predicate, not complete operational module or entry.
ns={'require':refuse,'GPU_UUIDS':{0:'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'},'REMOTE_ROOT':template['root'],'EXPECTED_RUNTIME_COMMIT':native['runtime_expected_commit']}
exec(compile(ast.Module(body=[fn(trees['adapter.py'],'_check_probe')],type_ignores=[]),'actual_probe_metadata','exec'),ns)
obs={'server_id':'server-4','hostname':'dl04-MS-7E06','root':template['root'],'physical_gpu':0,'gpu_uuid':ns['GPU_UUIDS'][0],'runtime_code_commit':native['runtime_expected_commit'],'idle':True,'contexts':[],'memory_used_mib':41,'utilization_percent':0,'locks':{k:'available' for k in ('training','diagnostic','exclusive')}}
ns['_check_probe'](None,obs,0);check('actual_probe_metadata_positive',True)
for name,key,value in [('wrong_runtime','runtime_code_commit','56b2a96dc48cc8a88f0f7105527ef448113b1060'),('busy','idle',False),('context','contexts',[{'pid':1}]),('wrong_uuid','gpu_uuid','UNKNOWN'),('busy_lock','locks',{'training':'busy','diagnostic':'available','exclusive':'available'})]:
    bad=copy.deepcopy(obs);bad[key]=value
    try:ns['_check_probe'](None,bad,0)
    except RuntimeError:check(name+'_refused',True)
    else:raise AssertionError(name)
class NoProcess:
    def check_output(self,*a,**k):raise AssertionError('No actual inventory/process call permitted')
remote={'check':refuse,'GPU_UUIDS':ns['GPU_UUIDS'],'subprocess':NoProcess()}
exec(compile(ast.Module(body=[fn(trees['remote_ops.py'],'probe')],type_ignores=[]),'actual_remote_invalid_prefix','exec'),remote)
for gpu in (1,True,'0',2,None):
    try:remote['probe'](gpu)
    except RuntimeError:check('remote_early_refuse_'+repr(gpu),True)
    else:raise AssertionError('Invalid physicalGPU accepted')
result={'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'CURRENT_METADATA_LITERAL_PORT_SOFTWARE_CHECKS_PASSED_NOT_NATIVE','count':len(checks),'checks':checks,'source_hashes':{n:sha(HERE/n) for n in ['adapter.py','remote_ops.py','release_template.json']},'actual_adapter_or_remote_entry_imported':False,'actual_transport_network_GPU_Torch_Git_shared_operations':False,'native':'NOT_RUN','resources':'NOT_RUN'}
(HERE/'static_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps({'count':len(checks),'status':result['status']}))
