"""Read-only reconciliation of the original CPA process after a connectivity loss."""
from ops import *
import pipeline_monitor as monitor
import time

guard()
experiment=monitor.load_experiment(str(ROOT),'M204-CPA')
assert experiment['automatic_restart'] is False and experiment['scientific_admission'] is False
program=r'''import json,os,re,subprocess,hashlib
from pathlib import Path
from datetime import datetime,timezone
pid=ORIGINAL_PID
cfg=CONFIG
stage=Path('/data/songcl/Project/Cluster_project/pipeline/cpa_explore_72695a5d')
manifest=json.loads((stage/'runtime_manifest.json').read_text()) if (stage/'runtime_manifest.json').exists() else None
root=Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b')
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for block in iter(lambda:stream.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()
matches=[]
for path in Path('/proc').glob('[0-9]*/cmdline'):
 try:parts=path.read_bytes().split(b'\0')
 except OSError:continue
 if b'tools/train.py' in parts and cfg.encode() in parts:matches.append(int(path.parent.name))
process=Path('/proc')/str(pid)
original_parts=process.joinpath('cmdline').read_bytes().split(b'\0') if process.exists() else []
original_owned=b'tools/train.py' in original_parts and cfg.encode() in original_parts
stdout_path=Path(STDOUT)
stdout=''
stdout_size=None
if stdout_path.exists():
 with stdout_path.open('rb') as stream:
  stream.seek(0,2);stdout_size=stream.tell();stream.seek(max(0,stdout_size-60000))
  stdout=stream.read().decode('utf-8','replace')
steps=[(int(a),int(b)) for a,b in re.findall(r'Train\[(\d+)/\d+\]:[^\r\n]*?\|\s*(\d+)/\d+',stdout)]
boot_seconds=next(int(line.split()[1]) for line in Path('/proc/stat').read_text().splitlines() if line.startswith('btime '))
launched=datetime.fromisoformat(LAUNCHED)
native_base=Path('/data/songcl/Project/Cluster_project/Cluster_checkpoints')/Path(cfg).stem
native_paths=sorted(native_base.glob('*/*.log'),key=lambda item:item.stat().st_mtime) if native_base.exists() else []
native=None
if native_paths:
 path=native_paths[-1]
 metrics=[];epoch=None;last_train=None;terminal=[]
 with path.open(encoding='utf-8',errors='replace') as stream:
  for line in stream:
   match=re.search(r'Epoch\s*\[(\d+)/50\]\s*\[\s*(\d+)/(\d+)\]',line)
   if match:epoch=int(match.group(1));last_train=line.strip()
   metric=re.search(r'\bmIoU\s*:\s*([0-9.eE+-]+)',line)
   if metric:metrics.append({'epoch':epoch,'mIoU':float(metric.group(1)),'source_line':line.strip()})
   if any(word in line for word in ('Early stopping','Traceback','CUDA out of memory','RuntimeError:')):terminal.append(line.strip())
 checkpoints={}
 for name in ('last.pth','best.pth'):
  checkpoint=path.parent/name
  if checkpoint.exists():
   stat=checkpoint.stat()
   checkpoints[name]={'path':str(checkpoint),'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns,'modified_at':datetime.fromtimestamp(stat.st_mtime,timezone.utc).isoformat()}
 native={'path':str(path),'bytes':path.stat().st_size,'validation_history':metrics,'best':max(metrics,key=lambda item:item['mIoU']) if metrics else None,'last_training_row':last_train,'terminal_lines':terminal[-8:],'checkpoints':checkpoints}
runtime={path:sha(root/path)==digest if (root/path).is_file() else None for path,digest in manifest['runtime_files'].items()} if manifest else None
gpu_query=subprocess.run(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,capture_output=True,timeout=15)
gpu=gpu_query.stdout.strip() if gpu_query.returncode==0 else None
if gpu:assert [value.strip() for value in gpu.split(',')][:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
contexts_query=subprocess.run(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,capture_output=True,timeout=15)
contexts=contexts_query.stdout.strip() if contexts_query.returncode==0 else None
exit_path=stage/'native_exit.json'
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'boot_at':datetime.fromtimestamp(boot_seconds,timezone.utc).isoformat(),'boot_after_original_launch':boot_seconds>launched.timestamp(),'uptime_seconds':float(Path('/proc/uptime').read_text().split()[0]),'original_pid_exists':process.exists(),'original_process_owned':original_owned,'exact_config_process_ids':matches,'last_stdout_steps':steps[-6:],'stdout_log_bytes':stdout_size,'stdout_error_lines':[line for line in stdout.splitlines() if any(word in line for word in ('Traceback','CUDA out of memory','RuntimeError:','Killed'))][-8:],'native_log':native,'runtime_files_unchanged':runtime,'gpu':gpu,'gpu_error':gpu_query.stderr.strip() if gpu_query.returncode else None,'contexts':contexts,'native_exit':json.loads(exit_path.read_text()) if exit_path.exists() else None}))
'''
program=program.replace('ORIGINAL_PID',str(experiment['pid'])).replace('CONFIG',repr(experiment['config'])).replace('STDOUT',repr(experiment['log'])).replace('LAUNCHED',repr(experiment['launched']))
before=ssh(program,timeout=90)
save('original_run_before.json',before)
time.sleep(3)
after=ssh(program,timeout=90)
save('original_run_after.json',after)
result={'recorded_at':datetime.now(timezone.utc).isoformat(),'experiment_id':'M204-CPA','connection_restored':True,
 'original_process_live':after['original_process_owned'],'matching_processes':after['exact_config_process_ids'],
 'original_run_absent_in_two_fresh_probes':not before['original_process_owned'] and not after['original_process_owned'] and not before['exact_config_process_ids'] and not after['exact_config_process_ids'],
 'boot_after_original_launch':after['boot_after_original_launch'],'boot_at':after['boot_at'],
 'native_best':after['native_log']['best'] if after['native_log'] else None,
 'validation_count':len(after['native_log']['validation_history']) if after['native_log'] else None,
 'checkpoints':after['native_log']['checkpoints'] if after['native_log'] else None,
 'scientific_admission':False,'scientific_state':'inconclusive;operational interruption is not mechanism falsification',
 'restarts':0,'migrations':0,'cuda_tests':0,'evidence':[evidence(OUT/'original_run_before.json'),evidence(OUT/'original_run_after.json')]}
save('original_run_reconciliation.json',result)
advance([OUT/'original_run_before.json',OUT/'original_run_after.json',OUT/'original_run_reconciliation.json',OUT/'inspect_original_run.py'],
 next_action='Reconcile original CPA process and available full-state checkpoint;no automatic restart or migration under the one-launch authorization;keep scientific gates unresolved')
print(json.dumps(result,ensure_ascii=False,indent=2))
