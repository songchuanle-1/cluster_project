"""Check actual owner/ledger guards locally; transport is explicitly disabled."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
ORIGIN = HERE/'hrc_execution_adapter_head74f'
TOKEN = '37695e94da4a485c8979d474d3f33b39'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def verify_ref(item):
    path = (ROOT/item['path']).resolve()
    assert path.is_relative_to(ROOT.resolve()) and sha(path) == item['sha256']


class DisabledTransport:
    def __init__(self):
        self.calls = []

    def call(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        raise AssertionError('No remote operation is allowed in this local actual-guard check')


def main():
    candidate = next(c for c in read(ROOT/'pipeline/research_work.json')['candidates']
                     if c['id'] == 'hierarchy-bottom-up-refined-token-composition')
    assert candidate['code_commit'] == '74fcd21df0af9a971792038ffe251af1ffea2604'
    assert candidate['stage'] == 'blocked' and candidate['blocker_kind'] == 'exclusive_gpu_slot'
    anchors = []
    for section, keys in [('worker_preparation', ('preparation', 'worker', 'runtime', 'manifest_template')),
                          ('execution_adapter', ('preparation', 'release', 'adapter', 'remote_ops', 'root_review', 'independent_tests'))]:
        for key in keys:
            item = candidate[section][key]
            verify_ref(item)
            anchors.append(item)
    protected = ['research_work.json', 'queue.json', 'running.json', 'experiments/M207-HAP.json',
                 'experiments/M206-CGCA.json', 'execution_mode.json', 'goal.json',
                 'headless/.tick_context.json', 'headless/.tick_context_state.next.json']
    before = {rel: sha(ROOT/'pipeline'/rel) for rel in protected}
    execution_dir = HERE/'hrc_execution'
    assert not execution_dir.exists(), 'No preexisting execution directory expected for this tick'
    assert read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')['token'] == TOKEN
    spec = importlib.util.spec_from_file_location('hrc_actual_guards_head74f', ORIGIN/'adapter.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    transport = DisabledTransport()
    adapter = module.Adapter(transport=transport)
    actual = adapter.guard(360, gpu=0, mutation=True)
    assert actual['owner']['token'] == TOKEN
    results = {'GPU0_current_owner_candidate_policy_whitelist_guard': 'PASS_LOCAL_ONLY'}
    for gpu, expected in [(0, 'Selected GPU has registered running task'),
                          (1, 'Selected GPU is not currently allowed')]:
        try:
            adapter.prepare(gpu)
        except module.Refused as error:
            message = str(error)
            assert message == expected, message
            results['prepare_GPU'+str(gpu)] = {'refused': True, 'reason': message}
        else:
            raise AssertionError('Unexpected prepare success for GPU'+str(gpu))
    assert not transport.calls
    assert not execution_dir.exists()
    after = {rel: sha(ROOT/'pipeline'/rel) for rel in protected}
    assert before == after
    result = {
        'schema_version': 1, 'recorded_at': datetime.now(timezone.utc).isoformat(),
        'token': TOKEN, 'actual_thread_id': os.environ.get('CODEX_THREAD_ID'),
        'guard_inputs': 'Actual current owner/context/pending/goal/resource policy and HRC74f candidate; no fixture policy substituted.',
        'external_anchors_verified_before_adapter_import': anchors,
        'results': results, 'remote_transport_calls': len(transport.calls),
        'production_execution_directory_binding_manifest_lease_created': False,
        'protected_shared_files_hash_identical': {rel: before[rel] == after[rel] for rel in protected},
        'actual_remaining_seconds_at_guard': actual['remaining_seconds'],
        'native_smoke': 'NOT_RUN', 'resources': 'NOT_RUN', 'actual_pairing': 'NOT_RUN',
        'SSH': False, 'torch_import': False, 'GPU_computation': False,
        'HAP_process_or_remote_source_modified': False,
        'conclusion': 'New74f bundle passes actual local identity/eligibility guards, refuses occupied projectGPU0 and unauthorizedGPU1 before transport. This is not idle proof, native execution or scientific admission.'
    }
    path = HERE/'hrc_forward_actual_guard_integration.json'
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'result': 'PASS_LOCAL_GUARDS_ONLY', 'transport_calls': 0,
                      'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
