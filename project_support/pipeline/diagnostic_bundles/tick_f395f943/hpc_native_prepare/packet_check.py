"""Final small stdlib metadata/guard/source-byte validation; no worker import."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import copy
import hashlib
import json
import re

HERE=Path(__file__).resolve().parent
ROOT=Path('D:/project/cluster_project')
OLD=ROOT/'pipeline/diagnostic_bundles/tick_7e492595/cre_native_prepare'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf-8'))
def funcs(p):return {n.name:n for n in ast.parse(Path(p).read_text('utf-8')).body if isinstance(n,ast.FunctionDef)}
checks=[]
def check(value,label):
    assert value,label
    checks.append(label)
template=read(HERE/'manifest_template.json');binding=read(HERE/'source_version_binding.json')
check(template['candidate_id']==binding['candidate_id']=='hierarchy-tree-resolvent-nonlinear-composition','exact HPC stable identity')
check(template['code_commit']==binding['code_commit']=='2f7eff19ca59cc4586e13ca81a547a18ea7e313d','exact actual source2f7')
check(template['source_parent_commit']==binding['parent_commit']==template['runtime_expected_commit']=='56b2a96dc48cc8a88f0f7105527ef448113b1060','parent/current runtime56 independent from candidate')
check(sha(ROOT/binding['isolated_source_version']['path'])==binding['isolated_source_version']['sha256'] and sha(ROOT/binding['isolated_source_version_independent_review']['path'])==binding['isolated_source_version_independent_review']['sha256'],'actual source version and independent peer hash anchors')
check(read(ROOT/binding['source_preparation']['path'])['code_commit'] is None and binding['original_source_preparation_sha256']=='c94f9c289dbf92019d01d3674907a4765368fa3849160ff8268f7788f921a70c','original frozen c94 null source declaration retained')
check(sha(ROOT/binding['native_protocol']['path'])=='348e8d759df4b547561b59b96f11145b8e08e8ed83186f65ce58c6ece8b6d1a6','exact original348e scientific protocol')
check(len(binding['source_files'])==9 and len(template['candidate_source_hashes'])==8 and len(template['diagnostic_files'])==12,'exact9 source/8model/12diagnostic inventory')
check(all(sha(HERE/n)==h for n,h in template['diagnostic_files'].items()),'all current diagnostic file hashes exact')
check(sha(HERE/'source_version_binding.json')==template['source_version_binding_sha256'],'source binding manifest hash')
check(all(sha(HERE/'candidate_model'/n)==h for n,h in template['candidate_source_hashes'].items()) and sha(HERE/'candidate.yaml')==template['candidate_config_sha256'],'exact frozen model8 and original YAML bytes')
ten=['current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit']
check(all(template[k] is None for k in ten),'all ten active execution fields null')
check(template['draft_execution_disabled'] is False and template['scientific_admission'] is False,'version capability only, no scientific admission')
check(not any((HERE/n).exists() for n in ['native_manifest.json','execution_lease.json','execution_binding.json','adapter_release.json']),'no actual manifest lease binding or release')
original=funcs(OLD/'native_runtime.py');current=funcs(HERE/'native_runtime.py')
check(set(original)==set(current) and len(current)==9,'all nine original safety function names retained')
for name in current:
    new=copy.deepcopy(current[name])
    if name=='require_promoted_version':
        for node in ast.walk(new):
            if isinstance(node,ast.Constant) and isinstance(node.value,str):node.value=node.value.replace('HPC native preparation','CRE native preparation')
    check(ast.dump(new,include_attributes=False)==ast.dump(original[name],include_attributes=False),'original safety function AST: '+name)
for p in [HERE/'worker.py',HERE/'native_runtime.py']:
    compile(p.read_text('utf-8'),str(p),'exec')
check(True,'worker/runtime compilation only, not module import')
runtime_tree=ast.parse((HERE/'native_runtime.py').read_text('utf-8'))
assignments={n.targets[0].id:ast.literal_eval(n.value) for n in runtime_tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['DRAFT_EXECUTION_DISABLED','CANDIDATE_COMMIT','SOURCE_PARENT_COMMIT','SOURCE_PREPARATION_SHA256','RUNTIME_EXPECTED_COMMIT']}
pred=copy.deepcopy(current['require_promoted_version']);env={'re':re,**assignments}
exec(compile(ast.fix_missing_locations(ast.Module(body=[pred],type_ignores=[])),'<only_extracted_pure_version_predicate>','exec'),env)
env['require_promoted_version']();check(True,'extracted version predicate accepts actual declaration without executing runtime')
for key,value in [('DRAFT_EXECUTION_DISABLED',True),('CANDIDATE_COMMIT',None),('SOURCE_PARENT_COMMIT',None),('SOURCE_PREPARATION_SHA256',None)]:
    before=env[key];env[key]=value
    try:env['require_promoted_version']()
    except RuntimeError:check(True,'extracted early version refusal: '+key)
    else:raise AssertionError('fail-closed version predicate did not refuse')
    finally:env[key]=before
software=read(HERE/'static_validation.json')
check(software['worker_sha256']==sha(HERE/'worker.py') and software['Torch_native_FP32_autograd_gradient_optimizer_data_or_resource_tested'] is False,'new observer software proof exact worker and honest scope')
report={'status':'HPC_NATIVE_PACKET_METADATA_GUARD_AST_VALIDATED_NOT_NATIVE_PASS','recorded_at':datetime.now(timezone.utc).isoformat(),'check_count':len(checks),'checks':checks,'candidate_id':template['candidate_id'],'code_commit':template['code_commit'],'actual_worker_runtime_entry_import_or_execution':False,'Torch_GPU_SSH_Git_transport_root_or_shared_operation':False,'native_TRAIN2_resources_actual':'NOT_RUN','material_concerns':[]}
with (HERE/'packet_validation.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
print(json.dumps({'check_count':len(checks),'sha256':sha(HERE/'packet_validation.json'),'native_resources':'NOT_RUN'}))
