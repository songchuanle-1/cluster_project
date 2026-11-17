"""Small stdlib AST/hash/refusal checks; no production driver import/entry/transport."""
import ast, copy, hashlib, json, re
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OLD=ROOT/'pipeline/diagnostic_bundles/tick_d08825b5/cre_compatible_tooling'
NATIVE=HERE.parent/'hpc_native_prepare'
CHECKS=[]
def need(v,label):
    if not v:raise AssertionError(label)
    CHECKS.append(label)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def globals_of(tree):
    out={}
    for n in tree.body:
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
            try:out[n.targets[0].id]=ast.literal_eval(n.value)
            except (ValueError,TypeError):pass
    return out
def port(s):
    return s.replace('hierarchy-cross-root-directed-edge-broadcast','hierarchy-tree-resolvent-nonlinear-composition').replace('M217-CRE','M218-HPC').replace('CRE','HPC').replace('cre_','hpc_').replace('_cre','_hpc')
def funcs(t):return [(n.name,ast.dump(n,include_attributes=False)) for n in ast.walk(t) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
a=(HERE/'adapter.py').read_text(encoding='utf-8');r=(HERE/'remote_ops.py').read_text(encoding='utf-8');at=ast.parse(a);rt=ast.parse(r);g=globals_of(at);rg=globals_of(rt)
need(g['CANDIDATE']==rg['CANDIDATE']=='hierarchy-tree-resolvent-nonlinear-composition','HPC_exact_CID_both_drivers')
need(g['COMMIT']==rg['COMMIT']=='2f7eff19ca59cc4586e13ca81a547a18ea7e313d','actual_root_source_commit_both_drivers')
need(g['EXPECTED_RUNTIME_COMMIT']=='56b2a96dc48cc8a88f0f7105527ef448113b1060','actual_parent_runtime56_separate')
need(g['GPU_UUIDS']==rg['GPU_UUIDS']=={0:'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'},'physical0_only_UUID_no_GPU1')
need(g['RESOURCE_AUTHORIZATION']['sha256']=='94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09','GPU0_only_explicit_grant_unchanged')
for name,text in [('adapter.py',a),('remote_ops.py',r)]:
    old=(OLD/name).read_text(encoding='utf-8');need(funcs(ast.parse(text))==funcs(ast.parse(port(old))),name+'_all_function_AST_exact_after_declared_identity_namespace_labels')
    compile(text,str(HERE/name),'exec')
need(True,'both_driver_compile_without_import_or_execution')
# The final frozen native bundle is checked by metadata and hashes only.
p=read(NATIVE/'preparation.json');m=read(NATIVE/'manifest_template.json')
need(sha(NATIVE/'preparation.json')==g['PREPARATION_SHA'] and sha(NATIVE/'manifest_template.json')==g['TEMPLATE_SHA'],'real_native_and_template_hash_constants_bound')
need(p['candidate_id']==g['CANDIDATE'] and p['source_commit']==g['COMMIT'] and m['code_commit']==g['COMMIT'],'native_candidate_source_exact')
for n,h in p['prepared_file_hashes'].items():
    f=(NATIVE/n).resolve();need(f.is_relative_to(NATIVE.resolve()) and sha(f)==h,'native_map_'+n)
active=['current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit']
need(all(k in m and m[k] is None for k in active),'all_ten_execution_fields_null_not_an_active_binding')
need(m['candidate_config_sha256']=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a','original_native_YAML_hash')
need(m['source_parent_commit']==m['runtime_expected_commit']==g['EXPECTED_RUNTIME_COMMIT'],'native_parent_runtime_matches_driver56')
oldw=ast.parse((OLD/'native/worker.py').read_text(encoding='utf-8'));neww=ast.parse((NATIVE/'worker.py').read_text(encoding='utf-8'))
resource=lambda t:ast.dump(next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='resources'),include_attributes=False)
need(resource(oldw)==resource(neww),'entire_original_resource_function_AST_exact')
need(not (HERE/'adapter_release.json').exists(),'no_production_release_created')
need(not (HERE.parent/'hpc_execution').exists(),'no_execution_directory_created')
need(all(not (NATIVE/n).exists() for n in ['native_manifest.json','execution_lease.json','execution_binding.json']),'no_active_native_manifest_binding_or_lease_created')
# Actual stdlib refusal of extracted frozen metadata guard, NOT an Adapter import/operation.
refused=type('Refused',(RuntimeError,),{})
def require(c,m):
    if not c:raise refused(m)
method=next(n for c in at.body if isinstance(c,ast.ClassDef) and c.name=='Adapter' for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='_frozen_details')
namespace={'COMMIT':None,'re':re,'require':require}
exec(compile(ast.Module(body=[method],type_ignores=[]),'extracted_frozen_guard','exec'),namespace)
for v in [None,False,'','unbound','0'*39]:
    namespace['COMMIT']=v
    try:namespace['_frozen_details'](object())
    except refused as e:need(str(e)=='Exact promoted source commit is required','stdlib_refusal_invalid_source_'+repr(v))
    else:raise AssertionError('invalid source accepted')
# Complete release catalogue cannot authorize execution; it contains no active owner/grant fields.
release=read(HERE/'release_template.json')
need(release['candidate_id']==g['CANDIDATE'] and release['code_commit']==g['COMMIT'] and release['native_preparation_sha256']==g['PREPARATION_SHA'],'release_static_identity_and_native_hash')
need(release['source_hashes']=={n:sha(HERE/n) for n in ['adapter.py','remote_ops.py']},'release_two_source_hashes_exact')
need(not any(k in release for k in active+['token','owner','lease','expires_at']),'release_has_no_execution_owner_token_lease_grant')
report={'status':'MINIMAL_METADATA_AST_AND_STDLIB_REFUSALS_PASSED_NOT_NATIVE','checks_count':len(CHECKS),'checks':CHECKS,'source_hashes':{n:sha(HERE/n) for n in ['adapter.py','remote_ops.py']},'native_preparation_sha256':g['PREPARATION_SHA'],'manifest_template_sha256':g['TEMPLATE_SHA'],'production_entry_imported_or_called':False,'transport_network_process_Torch_GPU_or_Git_operations':0,'native_TRAIN2':'NOT_RUN','resources':'NOT_RUN','old_suite_rerun':False,'scope':'Only actual local source/hash/metadata inspection, compile without import, and five invalid source-value refusals of an AST-extracted guard. Original 32/41/61/98 suites not run.'}
(HERE/'software_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
