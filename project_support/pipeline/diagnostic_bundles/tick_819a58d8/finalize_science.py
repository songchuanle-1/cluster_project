"""Persist finite diagnostic findings without inventing a capacity-gap stop."""
from datetime import datetime, timezone
import json
import shutil
import statistics
from ops import guard, save, ssh, advance, evidence, tick, ROOT, OUT, CID, TOKEN

owner = guard(100)
files = {
    'failure': OUT / 'channel_failure/native_channel_failure_result.json',
    'single': OUT / 'task_suffix/native_task_suffix_result.json',
    'coherent': OUT / 'coherent_channel/native_coherent_channel_result.json',
    'paired': OUT / 'paired_field/native_paired_field_result.json',
    'matched': OUT / 'matched_pair/native_matched_pair_result.json',
    'factorial': OUT / 'factorial_scope/native_matched_pair_result.json'}
results = {name: tick.load(path) for name, path in files.items()}
assert results['failure']['strict_null_gate_passed'] is False
assert results['failure']['records'][0]['conditions']['remote_null']['message_max_absolute_change'] == 1.430511474609375e-6
for name, value in results.items():
    if name != 'failure':
        assert value['execution_completed'] and value['controls_passed']
        assert max(value['controls'].values()) <= 1e-6
for name in ('matched', 'factorial'):
    assert results[name]['identity_matching_identical']
    assert all(condition['mask_matching_identical'] for record in results[name]['records']
               for condition in record['conditions'].values())
counts = {key: sum(value.get(key, 0) for value in results.values()) for key in
          ('native_forwards', 'native_backwards', 'source_interface_forwards',
           'suffix_replays', 'criterion_replays', 'optimizer_steps', 'scheduler_steps')}
assert counts == {'native_forwards': 5, 'native_backwards': 5,
                  'source_interface_forwards': 729, 'suffix_replays': 730,
                  'criterion_replays': 730, 'optimizer_steps': 0, 'scheduler_steps': 0}, counts
factorial = results['factorial']
worst_identity = max(value.get('controls', {}).get('identity_criterion_loss', 0)
                     for value in results.values())
aggregate = {}
for key in factorial['records'][0]['conditions']:
    rows = [record['conditions'][key] for record in factorial['records']]
    fields = {}
    for field in ('message_max_absolute_change', 'mask_logits_max_change',
                  'native_loss_delta', 'native_cotangent_linear_surrogate'):
        values = [row[field] for row in rows]
        fields[field] = {'min': min(values), 'median': statistics.median(values),
                         'max': max(values), 'nonzero': sum(v != 0 for v in values)}
    fields['loss_abs_above_observed_identity_delta'] = sum(
        abs(row['native_loss_delta']) > worst_identity for row in rows)
    fields['strict_null_failures'] = sum(row.get('original_strict_1e_minus6_message_gate') is False for row in rows)
    aggregate[key] = fields
save('analysis_summary.json', {
    'observed_at': datetime.now(timezone.utc).isoformat(), 'candidate_id': CID,
    'scientific_status': 'finite_conditional_channel_audit_complete;task_bottleneck_and_efficacy_unproven',
    'original_strict_gate_failed': True, 'failure_amplitude': 1.430511474609375e-6,
    'actual_this_tick': {**counts, 'new_training': 0, 'new_VAL': 0,
                        'new_models': 0, 'admissions': 0, 'new_candidates': 0},
    'worst_identity_loss_delta_observed': worst_identity,
    'factorial_aggregate': aggregate, 'actual_matching_identical': True,
    'independent_scenes': 2, 'expressions': 8, 'fixed_readouts': 24,
    'physical_scene_coarse_regions': len({(row['expression'] // 4, row['coarse_cluster']) for row in factorial['records']}),
    'factorial_conditions': sum(len(row['conditions']) for row in factorial['records']),
    'population_uncertainty': 'UNKNOWN;not288independent samples',
    'conclusion': 'Rank2 global-mean channels are task-active;single-point response also depends on sender dilution and receiver scope. No causal task deficit or new mechanism benefit established.',
    'not_claimed': ['unique numerical cause', 'whole-network bottleneck', 'novel attention',
                    'trained benefit/harm', 'all independent routes exhausted']})
manifest = OUT / 'factorial_scope/native_manifest.json'
remote = '''import fcntl,hashlib,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
m=json.loads(Path('/data/songcl/Project/Cluster_project/pipeline/native_channel_819a58d8/factorial_scope/native_manifest.json').read_text())
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for data in iter(lambda:stream.read(8*1024*1024),b''):h.update(data)
 return h.hexdigest()
a=m['assets'];base=Path(m['root'])
checks={name:digest(base/'framework/model/Quard_model'/m['name']/name)==value for name,value in a['source_hashes'].items()}
for name,path in [('config',a['config_path']),('checkpoint',a['checkpoint']),('annotation',a['annotation_path'])]:checks[name]=digest(path)==a[name+'_sha256']
checks['dataset']=digest(base/'framework/dataset/scannetv2.py')==a['dataset_source_sha256']
checks['prefix']=digest(m['prefix_source']['path'])==m['prefix_source']['sha256']
assert all(checks.values()),checks
locks={}
for kind in ('training','diagnostic','exclusive'):
 path=Path('/tmp/cluster_project_gpu0_'+kind+'.lock')
 if not path.exists():locks[kind]='absent_not_created';continue
 with path.open('r+b') as handle:
  try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]='available_released_on_close'
  except BlockingIOError:locks[kind]='held_by_other_not_modified'
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert [v.strip() for v in gpu.split(',')][:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
apps=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader,nounits'],text=True).strip()
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'gpu':gpu,'contexts':apps,'assets_unchanged':checks,'locks':locks,'cuda_calls':0}))
'''
environment = ssh(remote, 90)
save('final_environment.json', environment)
shutil.copyfile(ROOT / 'pipeline/goal.json', OUT / 'goal_frozen.json')
shutil.copyfile(ROOT / 'pipeline/codex_memory.md', OUT / 'memory_before.md')
save('original_source_review.json', {
    'paper': 'SPFormer: Superpoint Transformer for 3D Instance Segmentation',
    'primary_source': 'https://arxiv.org/html/2211.15766',
    'verified_sections': ['3.2SuperpointQueryDecoder', '3.3InstanceMaskPrediction'],
    'verified_scope': 'Superpoint cross-attention updates queries;the mask module uses query-generated kernels and superpoint features. These general components are prior art,not this project innovation.',
    'limitations': 'One bounded original-paper check,not exhaustive novelty verification for any future architecture. 3D instance segmentation is not identical to language-grounded ScanRefer evaluation.'})
paths = [*files.values(), OUT / 'analysis_summary.json', OUT / 'final_environment.json',
         OUT / 'goal_frozen.json', OUT / 'original_source_review.json',
         ROOT / 'pipeline/reviews/motivation_review_20261019_819a58d8_channel.md',
         ROOT / 'pipeline/designs/exp_design_20261019_819a58d8_channel.md']
advance(paths, stage='complete', failure_scope='inconclusive',
        blocker=None, blocker_kind=None, retry_after=None, unblock_condition=None,
        gate_result='Finite conditional rank/scope/task audit COMPLETE,not architecture admission. Original null1e-6 gate FAILED. Actual matching fixed in final controls;rank2 task channels active,not a proven accuracy bottleneck.',
        next_action='Do not repeat finite rank/numerical probes or derive a new gate from rank2 alone. Any next structural candidate needs a separate target-blind point-feature task deficit and matched intervention while preserving all bans/failures.')
work = tick.load(ROOT / 'pipeline/research_work.json')
remaining = (datetime.fromisoformat(owner['deadline_at']) - datetime.now(timezone.utc)).total_seconds()
work['design_cycle'] = {
    'status': 'finite_diagnostic_complete_no_global_exhaustion_claim',
    'attempted_ids': [CID], 'evidence': [evidence(path) for path in paths],
    'resume_condition': 'A concrete independent,legal point-feature mechanism deficit with matched task evidence;not generic rank2,extra variants,timers or reopened rejected families.',
    'remaining_seconds_at_record': remaining,
    'no_admission_reason': 'The native null gate remains failed and no task-accuracy deficit/new structural mechanism has been established. No artificial resource/phase hold or two-ID exhaustion invented.'}
if remaining <= 180:
    work['design_cycle']['stop_reason'] = 'tick_deadline_near'
guard()
tick.save(ROOT / 'pipeline/research_work.json', work)
print(json.dumps({'counts': counts, 'finite_candidate_stage': 'complete',
                  'scientific_admission': False, 'remaining_seconds': remaining,
                  'environment': environment}, ensure_ascii=False))
