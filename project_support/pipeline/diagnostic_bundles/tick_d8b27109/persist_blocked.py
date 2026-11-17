"""Record actual foreign occupation and honest candidate dispositions."""
from datetime import datetime, timedelta, timezone
import json
import shlex
import shutil
from ops import (guard, save, run, ssh, advance, evidence, tick, OUT, PREV,
                 ROOT, CID, SSH)

guard(180)
remote = '''import fcntl,hashlib,json,os,subprocess
from pathlib import Path
from datetime import datetime,timezone
m=json.loads(Path('/data/songcl/Project/Cluster_project/pipeline/native_channel_d8b27109/channel_failure/native_manifest.json').read_text())
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for chunk in iter(lambda:stream.read(8*1024*1024),b''):h.update(chunk)
 return h.hexdigest()
assets=m['assets'];base=Path(m['root'])
checks={name:digest(base/'framework/model/Quard_model'/m['name']/name)==value for name,value in assets['source_hashes'].items()}
for name,path in [('config',assets['config_path']),('checkpoint',assets['checkpoint']),('annotation',assets['annotation_path'])]:
 checks[name]=digest(path)==assets[name+'_sha256']
checks['dataset']=digest(base/'framework/dataset/scannetv2.py')==assets['dataset_source_sha256']
checks['prefix']=digest(m['prefix_source']['path'])==m['prefix_source']['sha256']
assert all(checks.values()),checks
locks={}
for kind in ('training','diagnostic','exclusive'):
 path=Path('/tmp/cluster_project_gpu0_'+kind+'.lock')
 if not path.exists():locks[kind]='absent_not_created';continue
 with path.open('r+b') as handle:
  try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]='available_released_on_close'
  except BlockingIOError:locks[kind]='held_by_other_owner_not_modified'
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert [p.strip() for p in gpu.split(',')][:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
apps=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader,nounits'],text=True).strip()
print(json.dumps({'server':'server-4','hostname':socket.gethostname(),'observed_at':datetime.now(timezone.utc).isoformat(),'gpu':gpu,'contexts':apps,'immutable_assets':checks,'locks':locks,'cuda_calls':0}))
'''
server4 = ssh(remote, 120)
program = '''import socket,subprocess,json
from datetime import datetime,timezone
assert socket.gethostname()=='sysu311-MS-7C59'
gpu=subprocess.check_output(['nvidia-smi','-i','1','--query-gpu=index,uuid,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'],universal_newlines=True).strip()
assert [p.strip() for p in gpu.split(',')][:2]==['1','GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0']
apps=subprocess.check_output(['nvidia-smi','-i','1','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader,nounits'],universal_newlines=True).strip()
print(json.dumps({'server':'server-3','hostname':socket.gethostname(),'observed_at':datetime.now(timezone.utc).isoformat(),'gpu':gpu,'contexts':apps,'cuda_calls':0}))
'''
result = run(['ssh', *SSH, 'songcl@192.168.1.120',
              shlex.join(['/usr/bin/python3', '-B', '-c', program])])
assert result.returncode == 0, result.stderr
server3 = json.loads(result.stdout)
save('final_environment.json', {'server4': server4, 'server3': server3})
assert server4['contexts'] and server3['contexts'], 'A slot opened; continue instead of declaring a block'
cpu = tick.load(OUT / 'cpu_channel_roundoff/cpu_channel_roundoff_result.json')
native = tick.load(OUT / 'channel_failure/native_channel_failure_result.json')
assert native['source_interface_forwards'] == 0
assert native['error'] == 'Occupied authorized GPU;no sharing or eviction'
assert cpu['cpu_source_formula_forwards'] == 12 and cpu['cuda_initialized'] is False
summary = {'observed_at': datetime.now(timezone.utc).isoformat(),
           'candidate_id': CID, 'scientific_status': 'inconclusive_pending_native_failure_measurement',
           'native_test_attempt': 'stopped before acquisition/forwards by actual foreign GPU occupation',
           'original_native_failure_exact_amplitude': 'UNKNOWN',
           'cpu_arithmetic_reference': cpu,
           'actual_this_tick': {'native_forwards': 0, 'native_backwards': 0,
                                'native_source_interface_forwards': 0,
                                'cpu_source_formula_forwards': 12,
                                'new_training': 0, 'new_VAL': 0, 'new_models': 0,
                                'admissions': 0, 'optimizer_steps': 0, 'scheduler_steps': 0},
           'all_authorized_slots_foreign_occupied': True,
           'server4_GPU1_authorized': False,
           'not_claimed': ['original GPU failure cause', 'whole-network bottleneck',
                           'trained efficacy', 'novelty', 'scientific admission'],
           'next_test': 'ONE original frozen expression0/lastvalid native failure measurement after fresh idle lease'}
save('analysis_summary.json', summary)
now = datetime.now(timezone.utc)
paths = [OUT / 'analysis_summary.json', OUT / 'final_environment.json',
         OUT / 'channel_failure/native_manifest.json',
         OUT / 'channel_failure/native_channel_failure_result.json',
         OUT / 'cpu_channel_roundoff/cpu_channel_roundoff_result.json',
         OUT / 'cpu_channel_roundoff_prereg.md']
advance(paths, stage='blocked', failure_scope='inconclusive',
        blocker_kind='exclusive_gpu_slot', required_server='server-4',
        blocker='Both authorized physical slots are occupied by foreign compute processes. '
                'The native diagnostic stopped before CUDA/forwards; CPU-only fixed-readout references completed. '
                'Original native failure and unknown exact amplitude remain unchanged.',
        retry_after=(now + timedelta(hours=1)).isoformat(),
        unblock_condition='Freshly idle authorized server4 physicalGPU0 with pinned hostname/UUID and '
                          'all3 lifetime flocks; alternatively authorized server3 physicalGPU1 idle '
                          'after exact frozen asset/source/runtime parity preparation. Fresh owning lease '
                          'with sufficient unchanged deadline is mandatory; no sharing/eviction.',
        wake_paths=['SERVERS.yaml', 'pipeline/goal.json'],
        next_action='After genuine resource release execute exactly the frozen native failed readout '
                    'once under a new current lease; save strict1e-6 outcome and arithmetic residuals. '
                    'Do not rerun to obtain PASS or infer efficacy from CPU references.',
        gate_result='CPU float32 remote-null=9.5367431640625e-7, float64ideal=1.7763568394002505e-15; '
                    'active controls nonzero. NOT native gate PASS. Original GPU amplitude UNKNOWN; '
                    'native follow-up unrun because both authorized slots occupied.')
work = tick.load(ROOT / 'pipeline/research_work.json')
auxiliary = tick.load(OUT / 'auxiliary_scope_recheck.json')
auxids = {c['id'] for c in auxiliary['candidates']}
for candidate in work['candidates']:
    if candidate['id'] in auxids:
        assert candidate['stage'] == 'blocked' and candidate['blocker_kind'] == 'human_authorization'
        candidate['retry_after'] = (now + timedelta(hours=4)).isoformat()
        candidate['evidence'].append(evidence(OUT / 'auxiliary_scope_recheck.json'))
work['design_cycle'] = {
    'stop_reason': 'external_resource_blocked', 'attempted_ids': [CID],
    'evidence': [evidence(path) for path in paths],
    'resume_condition': 'An authorized physical slot is genuinely idle; preserve native guards and exact preregistered test. '
                        'Auxiliary human scope holds do not receive priority from timers or idle GPUs.',
    'retry_after': (now + timedelta(hours=1)).isoformat(),
    'recorded_at': now.isoformat()}
guard()
tick.save(ROOT / 'pipeline/research_work.json', work)
shutil.copyfile(ROOT / 'pipeline/codex_memory.md', OUT / 'memory_before.md')
decision = run(['C:/Program Files (x86)/Git/bin/bash.exe',
                'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh',
                'cluster_project', 'other', 'Native rank/null diagnostic resource stop',
                'Preserve strict failed native gate; no GPU sharing or scope expansion',
                'Both authorized slots have live foreign contexts;12CPU reference forwards completed,0native/VAL/training',
                'pipeline/diagnostic_bundles/tick_d8b27109/analysis_summary.json'])
save('decision_execution.json', {'returncode': decision.returncode,
                                 'stdout': decision.stdout, 'stderr': decision.stderr})
assert decision.returncode == 0, decision.stderr
print(json.dumps({'server4': server4, 'server3': server3,
                  'candidate_stage': 'blocked', 'retry_after': work['design_cycle']['retry_after'],
                  'actual_this_tick': summary['actual_this_tick'],
                  'decision': decision.stdout}, ensure_ascii=False))
