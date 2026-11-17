"""Private stdlib-only packet assembly; no import of operational modules or Git.

Requires an already-created real compatible source proof and its exact SHA.
Writes only fresh files beneath this private packet directory.
"""
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
OLD_NATIVE = OLD / 'cre_native_prepare'
OLD_OP = OLD / 'cre_operational_prepare'
PARENT = '56b2a96dc48cc8a88f0f7105527ef448113b1060'
OLD_SOURCE = '7ed9373db335d44c884133da3eced3fca03ad29a'
OLD_PARENT = '026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563'
CID = 'hierarchy-cross-root-directed-edge-broadcast'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def ref(path):
    return {'path': Path(path).relative_to(ROOT).as_posix(), 'sha256': sha(path)}


def write(path, value):
    data = value if isinstance(value, bytes) else (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open('xb') as stream:
        stream.write(data)


def replace_exact(text, old, new, count=1):
    assert text.count(old) == count, (old, text.count(old), count)
    return text.replace(old, new)


def functions(path):
    tree = ast.parse(Path(path).read_text('utf-8'))
    return {n.name: ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, ast.FunctionDef)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-proof', required=True)
    parser.add_argument('--source-proof-sha256', required=True)
    args = parser.parse_args()
    proof_path = Path(args.source_proof).resolve()
    assert proof_path.is_relative_to(HERE.parent)
    assert re.fullmatch(r'[0-9a-f]{64}', args.source_proof_sha256) and sha(proof_path) == args.source_proof_sha256
    proof = read(proof_path)
    commit = proof['code_commit']
    assert re.fullmatch(r'[0-9a-f]{40}', commit) and commit not in (OLD_SOURCE, PARENT)
    assert proof['candidate_id'] == CID and proof['experiment_id'] == 'M217-CRE'
    assert proof['parent_commit'] == PARENT and proof['diff_exact9A'] and proof['isolated_worktree_and_index_clean']
    assert proof.get('material_concerns') == []
    assert not (HERE / 'native').exists(), 'Do not replay or overwrite a partial assembly'
    original_native = read(OLD_NATIVE / 'preparation.json')
    original_op = read(OLD_OP / 'preparation.json')
    assert sha(OLD_NATIVE / 'preparation.json') == '1b669c0d0d5fe2c3364f8167a88a58189e3ace8424214fddaefe19711d6b0502'
    assert sha(OLD_OP / 'preparation.json') == '54c199622d965858de862ffae056915bf94d7f8ac86db9bd4ffc716b9d36fc4a'
    for directory, prepared in [(OLD_NATIVE, original_native), (OLD_OP, original_op)]:
        for name, expected in prepared['prepared_file_hashes'].items():
            assert sha(directory / name) == expected
    assert proof['frozen_source_files'] == proof['committed_blob_sha256'] == original_native['source_files']
    native = HERE / 'native'
    for name in ['worker.py', 'candidate.yaml'] + ['candidate_model/' + n for n in read(OLD_NATIVE / 'source_version_binding.json')['candidate_source_hashes']]:
        write(native / name, (OLD_NATIVE / name).read_bytes())
    runtime = (OLD_NATIVE / 'native_runtime.py').read_text('utf-8')
    runtime = replace_exact(runtime, "CANDIDATE_COMMIT = '" + OLD_SOURCE + "'", "CANDIDATE_COMMIT = '" + commit + "'")
    runtime = replace_exact(runtime, "SOURCE_PARENT_COMMIT = '" + OLD_PARENT + "'", "SOURCE_PARENT_COMMIT = '" + PARENT + "'")
    runtime = replace_exact(runtime, "RUNTIME_EXPECTED_COMMIT = '" + OLD_PARENT + "'", "RUNTIME_EXPECTED_COMMIT = '" + PARENT + "'")
    write(native / 'native_runtime.py', runtime.encode())
    assert functions(native / 'native_runtime.py') == functions(OLD_NATIVE / 'native_runtime.py')
    binding = read(OLD_NATIVE / 'source_version_binding.json')
    historical_version_proof = copy.deepcopy(binding['isolated_source_version'])
    binding.update(code_commit=commit, parent_commit=PARENT, base_reference_commit=PARENT, future_version_parent=PARENT, runtime_expected_commit=PARENT, isolated_source_version=ref(proof_path),
                   verification_scope='Actual compatible CRE source is single-child56b2 with exactly the original c760 nine blobs. Original7ed/026c sibling and all null preparation metadata remain immutable history; no native results are inherited.')
    binding['historical_source_version_binding'] = ref(OLD_NATIVE / 'source_version_binding.json')
    binding['historical_isolated_source_version'] = historical_version_proof
    binding['historical_isolated_source_version_independent_review'] = binding.pop('isolated_source_version_independent_review')
    binding['historical_original_compatible_reference'] = OLD_PARENT
    write(native / 'source_version_binding.json', binding)
    template = read(OLD_NATIVE / 'manifest_template.json')
    template.update(code_commit=commit, source_version_commit=commit, base_reference_commit=PARENT, source_parent_commit=PARENT, future_version_parent=PARENT, runtime_expected_commit=PARENT,
                    source_version_binding_sha256=sha(native / 'source_version_binding.json'))
    template['diagnostic_files'] = {name: sha(native / name) for name in template['diagnostic_files']}
    write(native / 'manifest_template.json', template)
    write(native / 'README.md', b'Version-only compatible copy. Worker/model/YAML/scientific protocol are unchanged. Runtime guards and all nine function bodies are unchanged; only candidate/parent/runtime literals differ. DRAFT False is capability only. Ten execution fields are null. Native/resources/common pairing remain NOT_RUN. Future operations require independent external anchors, static release, fresh real root owner/deadline/currentGPU0 grant/idle/UUID/three locks/assets/lease. No old result or lease is inherited.\n')
    owner_node = next(n for n in ast.parse((HERE.parent / 'anchor.py').read_text('utf-8')).body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'EXPECTED' for t in n.targets))
    owner = ast.literal_eval(owner_node.value)
    prepared = copy.deepcopy(original_native)
    prepared.update(recorded_at=datetime.now(timezone.utc).isoformat(), code_commit=commit, source_commit=commit, source_parent_commit=PARENT, runtime_expected_commit=PARENT, isolated_source_version=ref(proof_path),
                    source_version_binding=ref(native / 'source_version_binding.json'), manifest_template=ref(native / 'manifest_template.json'), prepared_under_parent=owner,
                    prepared_file_hashes={p.relative_to(native).as_posix(): sha(p) for p in native.rglob('*') if p.is_file()},
                    reference_native_preparation=ref(OLD_NATIVE / 'preparation.json'), compatibility_scope='New metadata binding for identical source9/worker on actual56b2 parent/runtime. Existing AEF run and old CRE7ed artifacts unchanged.',
                    static_check_command='See current outer validate_packet.py; original38 software proof is historical only, not rerun.', actual_static_check_count=0,
                    software_scope='Current literal/byte/AST/file-map checks are recorded in the new outer packet; no inherited software result relabeled as current.', AEF_sibling_boundary='This compatible CRE source is a child of56b2; no ff/native/admission claim. Future main changes still require compatible packaging and actual execution.')
    for field in ['isolated_source_version_independent_review', 'static_validation']:
        prepared['historical_' + field] = prepared.pop(field)
    write(native / 'preparation.json', prepared)
    adapter = (OLD_OP / 'adapter.py').read_text('utf-8')
    substitutions = [
        ("FROZEN = PROJECT_ROOT/'pipeline/diagnostic_bundles/tick_7e492595/cre_native_prepare'", "FROZEN = PROJECT_ROOT/'" + native.relative_to(ROOT).as_posix() + "'"),
        ("PREPARATION_SHA = '" + ref(OLD_NATIVE / 'preparation.json')['sha256'] + "'", "PREPARATION_SHA = '" + sha(native / 'preparation.json') + "'"),
        ("TEMPLATE_SHA = '" + ref(OLD_NATIVE / 'manifest_template.json')['sha256'] + "'", "TEMPLATE_SHA = '" + sha(native / 'manifest_template.json') + "'"),
        ("COMMIT = '" + OLD_SOURCE + "'", "COMMIT = '" + commit + "'"),
        ("EXPECTED_RUNTIME_COMMIT = '" + OLD_PARENT + "'", "EXPECTED_RUNTIME_COMMIT = '" + PARENT + "'"),
        ('Runtime HEAD is not exact expected026c', 'Runtime HEAD is not exact expected56b2'),
    ]
    for old, new in substitutions:
        adapter = replace_exact(adapter, old, new)
    write(HERE / 'adapter.py', adapter.encode())
    remote = replace_exact((OLD_OP / 'remote_ops.py').read_text('utf-8'), "COMMIT='" + OLD_SOURCE + "'", "COMMIT='" + commit + "'")
    write(HERE / 'remote_ops.py', remote.encode())
    release = read(OLD_OP / 'release_template.json')
    release.update(code_commit=commit, native_preparation_sha256=sha(native / 'preparation.json'), manifest_template_sha256=sha(native / 'manifest_template.json'), source_version_binding_sha256=sha(native / 'source_version_binding.json'), source_hashes={n: sha(HERE / n) for n in ['adapter.py', 'remote_ops.py']})
    write(HERE / 'release_template.json', release)
    write(HERE / 'port_provenance.json', {'status':'COMPATIBLE_SOURCE_METADATA_COPY_ONLY_NOT_NATIVE_PASS', 'candidate_id':CID, 'code_commit':commit, 'parent_and_runtime':PARENT, 'source_version':ref(proof_path), 'original_native_preparation':ref(OLD_NATIVE / 'preparation.json'), 'original_operational_preparation':ref(OLD_OP / 'preparation.json'), 'runtime_changes':'Only three top-level exact candidate/parent/runtime declaration literals; all nine function ASTs identical.', 'adapter_changes': [{'old':a,'new':b} for a,b in substitutions], 'remote_changes':'Only top-level COMMIT literal.', 'worker_model_yaml_protocol_changed':False, 'active_fields_null':True, 'native_resources_actual':'NOT_RUN', 'old_packets_modified':False})
    print(json.dumps({'native_preparation':ref(native / 'preparation.json'),'template':ref(native / 'manifest_template.json'),'release_template':ref(HERE / 'release_template.json'),'code_commit':commit,'source_version':ref(proof_path)},indent=2))


if __name__ == '__main__':
    main()
