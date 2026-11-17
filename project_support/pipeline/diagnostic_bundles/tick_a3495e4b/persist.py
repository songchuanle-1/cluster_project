"""Archive the final authorized PCE failure without changing scientific gates."""
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import repair

c = repair.c
ROOT, OUT = repair.ROOT, repair.OUT


def main():
    c.guard(300)
    original_save = c.save
    def save_once(name, value):
        path = OUT / name
        if path.exists():
            # Resume only this tick's immutable partial archival outputs.
            assert name in ('diagnostic_release.json', 'analysis.json', 'independent_route_review.json')
            assert isinstance(c.tick.load(path), dict)
            return path
        return original_save(name, value)
    c.save = save_once
    candidate_result = c.tick.load(OUT / 'combined_candidate_result.json')
    baseline = c.tick.load(OUT / 'm95_reference/resources_champion_result.json')
    assert candidate_result['execution_completed'] and baseline['execution_completed']
    assert candidate_result['input_sha256'] == baseline['input_sha256']
    assert candidate_result['profile']['profiler_file_sha256'] == baseline['profile']['profiler_file_sha256']
    assert not candidate_result['all_full_source_controls_passed']
    assert candidate_result['control_tolerance'] == 1e-6
    static = c.tick.load(OUT / 'static_review.json')
    package = ROOT / 'Cluster/framework/model/Quard_model' / (c.NAME + '_pce')
    assert {path.name: c.tick.digest(path) for path in package.glob('*.py')} == static['candidate_source_hashes']
    release_code = '''
import fcntl,json,subprocess
from datetime import datetime,timezone
row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert row.split(',')[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
locks={}
for kind in ('training','diagnostic','exclusive'):
 handle=open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b')
 try:
  fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
  locks[kind]='available'
 except BlockingIOError:locks[kind]='busy'
 finally:handle.close()
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'gpu':row,'contexts':contexts,'locks':locks}))
'''
    release = OUT / 'diagnostic_release.json'
    if not release.exists():
        release = c.save('diagnostic_release.json', c.remote(release_code))
    release_observation = c.tick.load(release)
    assert release_observation['returncode'] == 0
    assert not release_observation['data']['contexts']
    assert set(release_observation['data']['locks'].values()) == {'available'}
    old = c.tick.load(ROOT / 'pipeline/diagnostic_bundles/tick_3259705f/combined_candidate_result.json')
    analysis = c.save('analysis.json', {
        'observed_at': c.now(), 'candidate_id': c.CID, 'revision': 3,
        'outcome': 'failed', 'failure_scope': 'implementation', 'scientific_admission': False,
        'human_authorization': c.evidence(OUT / 'human_authorization.json'),
        'archival_repair': c.evidence(OUT / 'archival_classification.json'),
        'same_resource_input_sha256': baseline['input_sha256'],
        'resource_table': [{key: result.get(key) for key in ('target','parameters','median_ms','p90_ms',
            'peak_allocated_bytes','peak_reserved_bytes')} | {'flops_g': result['profile']['flops_g']}
            for result in (baseline, candidate_result)],
        'latency_ratio_vs_fresh_M95': candidate_result['median_ms'] / baseline['median_ms'],
        'latency_reduction_fraction_vs_R2': 1 - candidate_result['median_ms'] / old['median_ms'],
        'peak_allocated_ratio_vs_M95': candidate_result['peak_allocated_bytes'] / baseline['peak_allocated_bytes'],
        'graph_controls': candidate_result['graph_controls'],
        'graph_exact': candidate_result['graph_controls_passed'],
        'operator_maximum_error': candidate_result['maximum_operator_error'],
        'operator_equivalence_passed': candidate_result['operator_equivalence_passed'],
        'full_source_controls': candidate_result['controls'],
        'maximum_full_source_error': candidate_result['maximum_full_source_control_error'],
        'frozen_tolerance': 1e-6,
        'native_backward': {'loss_forwards': candidate_result['native_loss_forwards'],
            'criterion_backwards': candidate_result['native_criterion_backwards'],
            'finite_parameter_gradient_tensors': candidate_result['gradient_tensor_count'],
            'all_observed_gradients_finite': candidate_result['all_observed_gradients_finite'],
            'inst_feats_change_vs_deleted': candidate_result['native_feature_path_change_vs_deleted']},
        'interpretation': 'Fixed pooling removes observed identity-repeat mismatch, but row and deleted-parent controls still fail. Language permutation error occurs before the bank in unchanged LIA; no attribution proof or numerical waiver. A passing local operator and finite gradients are not full-source admission or trained efficacy.',
        'flops_caveat': 'Original FVCore handlers unchanged. Unsupported new elementwise/sum/softmax and CSR operations are omitted; equal9.7625G does not establish zero added computation or lightweight Pareto pass.',
        'baseline_harness_failure_preserved': c.evidence(OUT / 'resources_champion_result.json'),
        'baseline_harness_repair': c.evidence(OUT / 'm95_reference/harness_repair.json'),
        'implementation_limitations': ['Coincident physical centers are explicitly rejected; broader input coverage unverified',
            'Full optimizer-state peak and original no-cluster resource delta unmeasured',
            'Same2TRAINscenes/8expressions; population efficacy, harm, novelty and noise floor remain unknown'],
        'additional_revisions_remaining': 0, 'new_training': 0, 'optimizer_steps': 0,
        'commits': 0, 'production_deployment': False,
        'next_action': 'Park failed realization. No unchanged rerun or automatic fourth revision. A separate prediction-blind mainline diagnosis remains permitted but requires its own concrete independent evidence; no global exhaustion claim.'})
    review = c.save('independent_route_review.json', {
        'observed_at': c.now(), 'scope': 'Bounded read-only review of existing PCE mainline evidence; not an executed independent candidate test',
        'reviewed_evidence': [c.evidence(ROOT / 'pipeline/diagnostic_bundles/tick_658721c0' / name)
            for name in ('analysis.json', 'native_contact_result.json', 'source_distinction.json')],
        'finding': 'Existing2scene/8expression readouts are mixed and co-label edges include background. These do not yet establish an independent feature deficit for a new structural mechanism. Do not rename PCE or reopen M203/M204 to fill the spare slot.',
        'missing': 'Independent prediction-blind point-feature diagnosis with a discriminating native matched intervention',
        'all_routes_exhausted': False, 'new_candidate_created': False,
        'not_an_early_stop_certificate': True})
    # Use the canonical decision helper before changing the candidate disposition.
    bash = Path('C:/Program Files (x86)/Git/bin/bash.exe')
    decision = subprocess.run([str(bash), str(repair.SKILL / 'log_decision.sh'), 'cluster_project', 'other',
        'PCE额外一次局部修订完成但完整数值控制仍失败',
        '保留R1/R2/R3全部失败；R3停止追加修改，未准入未训练。归档分类与既有授权已登记。',
        'identity重复误差0；row与deleted控制仍2.861e-6>1e-6；465.45ms对33.58ms且642梯度有限不能替代科学准入。',
        str(analysis)], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
    decision_path = c.save('decision_helper.json', {'returncode': decision.returncode, 'stdout': decision.stdout, 'stderr': decision.stderr})
    assert decision.returncode == 0
    work = c.tick.load(ROOT / 'pipeline/research_work.json')
    candidate = next(item for item in work['candidates'] if item['id'] == c.CID)
    before = copy.deepcopy(candidate)
    revision = candidate['revision_history'][-1]
    assert revision['revision'] == 3 and revision['result'] == 'pending'
    results = [c.evidence(OUT / 'combined_candidate_result.json'), c.evidence(analysis), c.evidence(OUT / 'static_review.json')]
    for entry in results:
        if entry not in revision['evidence']:
            revision['evidence'].append(entry)
    revision['result_evidence'] = results
    revision['result'] = 'failed'
    for path in (analysis, release, review, decision_path, Path(__file__)):
        entry = c.evidence(path)
        if entry not in candidate['evidence']:
            candidate['evidence'].append(entry)
    candidate.update(stage='blocked', failure_scope='implementation', blocker_kind='numerical_control_failure',
        blocker='Final authorized PCE R3 fails unchanged full-source1e-6 row/deleted-parent controls at2.861e-6. Three revisions consumed (default2+explicit1); no automatic extra change. Latency13.86x matched M95 remains unresolved.',
        retry_after=(datetime.now(timezone.utc) + timedelta(hours=4)).isoformat(),
        unblock_condition='Materially new control-preserving evidence on the SAME stable ID; any additional implementation revision needs new explicitly scoped human authorization. A timer/free GPU/gradient result is not scientific admission.',
        next_action='Preserve all failures; do not rerun unchanged tests, alter attention/precision/thresholds or add R4. Continue only a separately evidenced independent point-feature diagnosis under existing project scope.',
        scientific_admission=False, actual_executed_test_result='failed',
        result_archival_status='Resolved: R2/R3 failed results classified without rewriting inputs or timestamps')
    repair.closure.validate_revisions(ROOT, candidate, before)
    # Retire the old, now false "R3 authorization pending" cycle without inventing
    # a global no-gain/independent-route exhaustion certificate.
    previous_cycle = work.pop('design_cycle', None)
    if previous_cycle is not None:
        work.setdefault('design_cycle_history', []).append(previous_cycle)
    c.tick.save(ROOT / 'pipeline/research_work.json', work)
    print(json.dumps({'analysis': c.evidence(analysis), 'r3_result': 'failed', 'gpu_released': True,
        'latency_ratio': candidate_result['median_ms'] / baseline['median_ms']}))


if __name__ == '__main__':
    main()
