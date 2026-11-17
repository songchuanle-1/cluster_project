"""Final local hashes/AST checks; no production operation, model or transport."""
import argparse
import ast
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent.parent
ROOT=Path('D:/project/cluster_project')
OLD=ROOT/'pipeline/diagnostic_bundles/tick_4694ba96/cts_native_prepare'
BFC=ROOT/'pipeline/diagnostic_bundles/tick_64ac844e/bfc_operational_prepare'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
checks=[]
def check(name,value):
    checks.append({'name':name,'passed':bool(value)})
    assert value,name
def dump(node):return ast.dump(node,include_attributes=False)
def functions(p):return {n.name:dump(n) for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
out=HERE/'offline_tests'/args.output
assert out.parent==HERE/'offline_tests' and not out.exists()
assert 'torch' not in sys.modules
for p in HERE.rglob('*.py'):compile(p.read_text(encoding='utf-8'),str(p),'exec')
check('all_current_python_sources_compile_without_import_execution',True)
check('worker03329_original_bytes',sha(HERE/'native/worker.py')==sha(OLD/'worker.py')=='03329ec50fba63d67330342052ec34262f772aee6cc16d3d8d2978d58628c27c')
check('whole_resource_function_AST_original',functions(HERE/'native/worker.py')['resources']==functions(OLD/'worker.py')['resources']==functions(BFC/'native/worker.py')['resources'])
check('all_original_runtime_function_AST_retained',functions(HERE/'native/native_runtime.py')==functions(OLD/'native_runtime.py'))
check('original_ff7_preparation_sha_unchanged',sha(OLD/'preparation.json')=='ff7fb7a65999369f277744828598822883a222a10ce1ef02732aafeb561fb2cf')
for name,h in read(OLD/'preparation.json')['prepared_file_hashes'].items():check('original_ff7_file_'+name,sha(OLD/name)==h)
for where in ['native/preparation.json','native/manifest_template.json']:
    p=read(HERE/where);mapping=p['prepared_file_hashes'] if 'prepared_file_hashes' in p else p['diagnostic_files']
    for name,h in mapping.items():check(where+'_'+name,sha(HERE/'native'/name)==h)
manifest=read(HERE/'native/manifest_template.json');prep=read(HERE/'native/preparation.json')
check('ten_active_fields_null',all(v is None for v in prep['manifest_execution_fields'].values()) and len(prep['manifest_execution_fields'])==10 and all(manifest[k] is None for k in prep['manifest_execution_fields']))
check('explicit_candidate4e8_parent_runtime48fc',manifest['code_commit']==manifest['source_version_commit']=='4e80006047d5cb3dcdfb9c1102e02c33f354a07d' and manifest['source_parent_commit']==manifest['runtime_expected_commit']=='48fc302c3c02ffef0b241be3593c386b6b65a72e')
check('static_catalog_not_production_release',not (HERE/'adapter_release.json').exists())
check('no_active_manifest_lease_binding_requests',not any(p.name in ('native_manifest.json','execution_lease.json','execution_binding.json') or p.name.endswith('_request.json') for p in HERE.rglob('*.json') if 'offline_tests' not in p.parts))
suite=read(HERE/'offline_tests/full_offline_run2.json')
check('final61_actual_mock_cases_passed',suite['successful'] and suite['tests_run']==61 and not suite['failures'] and not suite['errors'] and suite['source_unchanged_during_run'])
for name,h in suite['source_hashes'].items():check('final_suite_source_'+name,sha(HERE/name)==h)
entry=read(HERE/'offline_tests/entry_refusal_final.json')
check('seven_actual_CLI_refusals_no_process_network_torch',entry['case_count']==7 and entry['process_network_torch_events']==[] and entry['source_sha256']==sha(HERE/'adapter.py'))
check('all_results_only_offline_no_native',suite['native_execution']=='NOT_RUN' and suite['gpu_execution']=='NOT_RUN' and suite['transport_execution']=='MOCK_ONLY' and entry['native_resources_transport']=='NOT_RUN')
check('Torch_not_imported', 'torch' not in sys.modules)
payload={'schema_version':1,'checked_at':datetime.now(timezone.utc).isoformat(),'scope':'ACTUAL_LOCAL_HASH_AST_COMPILE_AND_RECORDED_OFFLINE_RESULT_CHECKS_ONLY','checks':checks,'check_count':len(checks),'failed_checks':[],
 'native':'NOT_RUN','resources':'NOT_RUN','Git':'NOT_RUN','SSH_GPU':'NOT_RUN','torch_imported':False,
 'source_hashes':{n:sha(HERE/n) for n in ['adapter.py','remote_ops.py','native/native_runtime.py','native/worker.py','native/preparation.json','native/manifest_template.json','release_template.json']},
 'limits':'These checks read original frozen sources and actual local mocked/refusal proof only. They do not validate hardware availability, execute native Tensor behavior or create standard PASS/admission.'}
with out.open('x',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'check_count':len(checks),'sha256':sha(out),'failed_checks':[]}))
