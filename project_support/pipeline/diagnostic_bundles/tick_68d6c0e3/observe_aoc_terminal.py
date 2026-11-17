"""Exact original AOC termination/source and GPU0 availability readback."""
from pathlib import Path
from datetime import datetime, timezone
import json, re, subprocess, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE = Path(__file__).resolve().parent


def main():
    guard()
    exp = u.read(ROOT / 'pipeline/experiments/M222-AOC.json')
    assert exp['pid'] == 3437349 and exp['code_commit'] == u.SOURCE and exp['status'] == 'running'
    prior = u.read(ROOT / 'pipeline/diagnostic_bundles/tick_1179a5bb/aoc_progress_observer/aoc_training_progress_observation.json')
    logger = prior['observation']['native_logger_paths']
    assert len(logger) == 1
    source = u.read(ROOT / 'pipeline/diagnostic_bundles/tick_2ef53d6b/aoc_native_prepare/preparation.json')['source_files']
    program = '''import socket,os,json,hashlib,subprocess,fcntl
from pathlib import Path
from datetime import datetime,timezone
assert socket.gethostname()=='dl04-MS-7E06'
p=json.loads(PAYLOAD);root=Path(p['root']);proc=Path('/proc')/str(p['pid'])
assert not proc.exists()
head=subprocess.check_output(['git','--no-optional-locks','-C',str(root),'rev-parse','HEAD'],text=True).strip();assert head==p['commit']
hashes={}
for rel,want in p['hashes'].items():
 value=hashlib.sha256((root/rel).read_bytes()).hexdigest();hashes[rel]=value
 assert value==(want if rel.endswith('.py') else '77eac419317cb7d7f5d4688337597a966b27d2f920484c1e2323d279240289ea')
matches=[]
for entry in Path('/proc').iterdir():
 if not entry.name.isdigit():continue
 try:
  if entry.stat().st_uid!=os.getuid():continue
  argv=[v.decode() for v in (entry/'cmdline').read_bytes().split(b'\\0') if v]
  if p['config'] in argv and 'tools/train.py' in argv and str((entry/'cwd').resolve())==str(root):matches.append({'pid':int(entry.name),'argv':argv})
 except (OSError,UnicodeError):pass
assert matches==[]
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
row=[x.strip() for x in gpu.split(',')];assert row[:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
compute=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
locks={}
for kind in ['training','diagnostic','exclusive']:
 path=Path('/tmp/cluster_project_gpu0_'+kind+'.lock');assert path.is_file()
 with path.open('r+b') as handle:
  try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]='available'
  except BlockingIOError:locks[kind]='busy'
native=Path(p['logger']);a=native.stat();raw=native.read_bytes();b=native.stat();assert (a.st_size,a.st_mtime_ns)==(b.st_size,b.st_mtime_ns)
lines=[x.strip() for x in raw.decode('utf8',errors='replace').splitlines() if 'mIoU :' in x or 'resume start_epoch:' in x]
assert not proc.exists()
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'process':{'pid':p['pid'],'exists':False},'original_pid_absent_before_after':True,'same_config_processes':matches,'runtime_code_commit':head,'source_hashes':hashes,'GPU0':gpu,'GPU0_contexts':compute,'locks':locks,'idle':not compute and int(row[2])<1024 and int(row[3])<10,'native_logger':p['logger'],'native_logger_bytes':len(raw),'native_logger_sha256':hashlib.sha256(raw).hexdigest(),'native_metric_lines':lines,'signals_sent':False,'checkpoint_body_read':False,'GPU1_queried':False,'probe_only_transient_lock_checks':True}))
'''
    payload = dict(root='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1', pid=3437349,
                   commit=u.SOURCE, config=exp['config'], logger=logger[0], hashes=source)
    program = program.replace('PAYLOAD', repr(json.dumps(payload)))
    command = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=8',
               'songcl@192.168.1.115', '/usr/bin/python3 -B -']
    result = subprocess.run(command, input=program.encode(), capture_output=True, timeout=45)
    guard()
    assert result.returncode == 0, result.stderr.decode(errors='replace')
    raw = json.loads(result.stdout)
    meta = u.read(HERE / 'aoc_exact_terminal_archive/exact_log_evidence.json')
    log = ROOT / meta['local']['path']
    assert sha(log) == meta['local']['sha256'] == 'f44d1fd647884e83fc0232afe618c1997b4e10f40c38454dbaa91da6d701e370'
    text = log.read_text(encoding='utf-8', errors='replace')
    steps = re.findall(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?\|\s*(\d+)/(\d+)', text)
    raw['last_TRAIN_progress'] = list(map(int, steps[-1]))
    raw['explicit_early_stop_lines'] = [x.strip() for x in text.splitlines() if 'Early stopping at epoch' in x]
    raw['explicit_exception_lines'] = [x[-1000:] for x in text.splitlines() if re.search(r'Traceback|RuntimeError:|ValueError:|CUDA out of memory|Fatal Python', x)]
    sys.path.insert(0, 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    values, best, missed = mon.parse_native_lineage('\n'.join(raw['native_metric_lines']), resumed=False)
    observation = {'owner': EXPECTED, 'observed_at': datetime.now(timezone.utc).isoformat(), 'command': command,
                   'observation': raw, 'precise_native_validation': {'values': values, 'best': best, 'no_improve': missed},
                   'exact_own_log': meta['local'], 'scope': 'Exact original process/source/native logger plus current GPU0/three-lock readback. No lifecycle mutation, signal, source patch, recovery or GPU1.'}
    u.save(HERE / 'aoc_end_and_slot_observation.json', observation)
    print(json.dumps({'last_TRAIN_progress': raw['last_TRAIN_progress'], 'early_stop': raw['explicit_early_stop_lines'],
                      'exceptions': raw['explicit_exception_lines'], 'validation_count': len(values), 'best': best,
                      'no_improve': missed, 'idle': raw['idle'], 'locks': raw['locks'],
                      'evidence': u.ref(HERE / 'aoc_end_and_slot_observation.json')}))


if __name__ == '__main__':
    main()
