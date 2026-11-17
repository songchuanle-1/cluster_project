"""Minimal current metadata/AST/refusal checks; never import operational modules."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import ast
import copy
import hashlib
import json
import re

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
OLD = ROOT / 'pipeline/diagnostic_bundles/tick_7e492595'
PARENT = '56b2a96dc48cc8a88f0f7105527ef448113b1060'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):
    return json.loads(Path(p).read_text('utf-8'))


def functions(p):
    result = {}
    tree = ast.parse(Path(p).read_text('utf-8'))
    def visit(body, prefix=''):
        for n in body:
            if isinstance(n, ast.FunctionDef):
                result[prefix + n.name] = copy.deepcopy(n)
            elif isinstance(n, ast.ClassDef):
                visit(n.body, prefix + n.name + '.')
    visit(tree.body)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    assert output.is_relative_to(HERE) and not output.exists()
    checks = []
    def check(value, label):
        assert value, label
        checks.append(label)
    native = HERE / 'native'
    prep = read(native / 'preparation.json')
    template = read(native / 'manifest_template.json')
    binding = read(native / 'source_version_binding.json')
    old_native = read(OLD / 'cre_native_prepare/preparation.json')
    old_op = read(OLD / 'cre_operational_prepare/preparation.json')
    for folder, p in [(OLD / 'cre_native_prepare', old_native), (OLD / 'cre_operational_prepare', old_op), (native, prep)]:
        check(all((folder / n).resolve().is_relative_to(folder.resolve()) and sha(folder / n) == h for n, h in p['prepared_file_hashes'].items()), 'complete hash map: ' + str(folder.relative_to(ROOT)))
    commit = prep['code_commit']
    proof_path = ROOT / binding['isolated_source_version']['path']
    proof = read(proof_path)
    check(sha(proof_path) == binding['isolated_source_version']['sha256'], 'real source version external hash')
    check(commit == binding['code_commit'] == template['code_commit'] == proof['code_commit'] and re.fullmatch('[0-9a-f]{40}', commit), 'exact new source commit chain')
    check(proof['parent_commit'] == binding['parent_commit'] == prep['source_parent_commit'] == template['source_parent_commit'] == PARENT, 'exact actual56b2 parent chain')
    check(binding['runtime_expected_commit'] == prep['runtime_expected_commit'] == template['runtime_expected_commit'] == PARENT, 'current56b2 runtime separated from candidate')
    check(proof['frozen_source_files'] == proof['committed_blob_sha256'] == prep['source_files'] == old_native['source_files'] and len(prep['source_files']) == 9, 'original exact nine source/YAML blobs')
    check(sha(native / 'worker.py') == sha(OLD / 'cre_native_prepare/worker.py') == 'bcc611437b7487f8ede6968827c693290da8a9e6badd5450c8c4bb34041c429b', 'entire worker including setup/TRAIN2/resources unchanged')
    check(all(sha(native / name) == h for name, h in template['diagnostic_files'].items()) and len(template['diagnostic_files']) == 12, 'twelve complete diagnostic assets')
    check(sha(native / 'source_version_binding.json') == template['source_version_binding_sha256'], 'binding to manifest hash')
    check(set(prep['manifest_execution_fields']) == {'current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit'} and all(v is None and template[k] is None for k,v in prep['manifest_execution_fields'].items()), 'all ten active execution fields null')
    check(template['draft_execution_disabled'] is False and prep['draft_execution_disabled'] is False and prep['native'] == prep['resources'] == 'NOT_RUN', 'original capability semantics with no actual native result')
    for rel in ['native_manifest.json','execution_lease.json','execution_binding.json','adapter_release.json']:
        check(not (HERE / rel).exists() and not (native / rel).exists(), 'no active or production release: ' + rel)
    old_runtime = functions(OLD / 'cre_native_prepare/native_runtime.py')
    new_runtime = functions(native / 'native_runtime.py')
    check(len(old_runtime) == 9 and {k:ast.dump(v,include_attributes=False) for k,v in old_runtime.items()} == {k:ast.dump(v,include_attributes=False) for k,v in new_runtime.items()}, 'all nine runtime safety function ASTs unchanged')
    for name in ['adapter.py','remote_ops.py']:
        old = functions(OLD / 'cre_operational_prepare' / name)
        new = functions(HERE / name)
        check(set(old) == set(new), name + ' function inventory unchanged')
        if name == 'adapter.py':
            class Normalize(ast.NodeTransformer):
                def visit_Constant(self,node):
                    if node.value == 'Runtime HEAD is not exact expected56b2':
                        node.value = 'Runtime HEAD is not exact expected026c'
                    return node
            new = {k:Normalize().visit(v) for k,v in new.items()}
        check({k:ast.dump(v,include_attributes=False) for k,v in old.items()} == {k:ast.dump(v,include_attributes=False) for k,v in new.items()}, name + ' all function ASTs unchanged except declared diagnostic message')
    release = read(HERE / 'release_template.json')
    check(release['code_commit'] == commit and release['native_preparation_sha256'] == sha(native / 'preparation.json') and release['manifest_template_sha256'] == sha(native / 'manifest_template.json') and release['source_version_binding_sha256'] == sha(native / 'source_version_binding.json'), 'release template complete new hash chain')
    check(release['source_hashes'] == {n:sha(HERE / n) for n in ['adapter.py','remote_ops.py']} and release['explicit_selected_physical_GPU_capability'] == [0], 'release module hashes and physical0 only')
    for p in [HERE/'adapter.py', HERE/'remote_ops.py', native/'worker.py', native/'native_runtime.py']:
        compile(p.read_text('utf-8'), str(p), 'exec')
    check(True, 'four new module source compile without import or execution')
    # Execute only the extracted stdlib early-version predicate, never the runtime module.
    pred = copy.deepcopy(new_runtime['require_promoted_version'])
    ns = {'re':re,'DRAFT_EXECUTION_DISABLED':False,'SOURCE_PARENT_COMMIT':PARENT,'CANDIDATE_COMMIT':commit,'SOURCE_PREPARATION_SHA256':prep['source_preparation_sha256']}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[pred],type_ignores=[])), '<extracted_version_predicate>', 'exec'), ns)
    ns['require_promoted_version']()
    check(True, 'actual extracted promoted predicate accepts exact source declaration only')
    for field,value in [('DRAFT_EXECUTION_DISABLED',True),('SOURCE_PARENT_COMMIT',None),('CANDIDATE_COMMIT',None),('SOURCE_PREPARATION_SHA256',None)]:
        before=ns[field];ns[field]=value
        try:
            ns['require_promoted_version']()
        except RuntimeError:
            check(True, 'extracted early version refusal: ' + field)
        else:
            raise AssertionError('missing fail-closed version refusal')
        finally:
            ns[field]=before
    old_binding = read(OLD / 'cre_native_prepare/source_version_binding.json')
    check(binding['historical_isolated_source_version'] == old_binding['isolated_source_version'] and binding['historical_isolated_source_version_independent_review'] == old_binding['isolated_source_version_independent_review'], 'old7ed source and peer kept as historical refs only')
    check(read(ROOT / prep['source_preparation']['path'])['code_commit'] is None, 'original frozen null source declaration not backfilled')
    report = {'status':'SOFTWARE_ONLY_COMPATIBLE_CRE_METADATA_AST_REFUSALS_PASSED_NOT_NATIVE_PASS','recorded_at':datetime.now(timezone.utc).isoformat(),'candidate_id':prep['candidate_id'],'code_commit':commit,'source_parent_commit':PARENT,'check_count':len(checks),'checks':checks,'material_concerns':[],'operational_modules_imported':False,'Torch_GPU_SSH_Git_transport_or_root_entries_executed':False,'native_resources_actual':'NOT_RUN','old38_19_46_suites_rerun':False}
    with output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(report,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({'check_count':len(checks),'report':str(output),'sha256':sha(output),'native_resources':'NOT_RUN'}))


if __name__ == '__main__':
    main()
