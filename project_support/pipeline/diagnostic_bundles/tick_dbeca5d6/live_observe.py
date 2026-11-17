"""Read-only authorized-card occupation, source and native log progress."""
import json
import sys
from ops import guard,ssh,save,NAME,REMOTE_ROOT

guard()
suffix='_final' if '--final' in sys.argv else ''
for name,host,gpu,hostname,uuid in (
    ('server4','192.168.1.115',0,'dl04-MS-7E06','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'),
    ('server3','192.168.1.120',1,'sysu311-MS-7C59','GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0')):
    program='''import os,json,socket,subprocess,re
from pathlib import Path
from datetime import datetime,timezone
assert socket.gethostname()==%r
def output(args):return subprocess.check_output(args,universal_newlines=True,timeout=10).strip()
gpu=output(['nvidia-smi','-i',%r,'--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'])
assert gpu.split(',')[1].strip()==%r
contexts=output(['nvidia-smi','-i',%r,'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'])
record={'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'gpu':gpu,'contexts':contexts,'occupied':bool(contexts),'cuda_allocations':0}
if %r=='server4':
 pid=1995443
 record['training_pid_alive']=Path('/proc/'+str(pid)).exists()
 record['training_command']=Path('/proc/'+str(pid)+'/cmdline').read_bytes().replace(b'\\0',b' ').decode()
 log=Path(%r)/'logs'/('train_'+%r+'_20261017_230107.log')
 text=log.read_text(errors='replace')
 record['log_path']=str(log);record['log_mtime_ns']=log.stat().st_mtime_ns
 record['validation_miou']=[float(v) for v in re.findall(r'mIoU\\s*:\\s*([0-9.]+)',text)]
 steps=re.findall(r'Train[^\\n]*?epoch:\\s*(\\d+)/(\\d+)[^\\n]*?iter:\\s*(\\d+)/(\\d+)',text,re.I)
 if not steps:steps=re.findall(r'Train[^\\n]*?(\\d+)/(50)[^\\n]*?(\\d+)/(\\d+)',text)
 record['last_step_matches']=steps[-4:]
 record['last_train_lines']=[line for line in text.splitlines() if 'Train' in line][-2:]
 record['log_bytes']=log.stat().st_size
 record['native_log_fd_targets']=[os.readlink(str(p)) for p in Path('/proc/'+str(pid)+'/fd').iterdir() if p.is_symlink() and ('Cluster_checkpoints' in os.readlink(str(p)))]
 logger=next(Path(p) for p in record['native_log_fd_targets'] if p.endswith('.log'))
 native=logger.read_text(errors='replace')
 record['native_validation_miou']=[float(v) for v in re.findall(r'mIoU\s*:\s*([0-9.]+)',native)]
 record['last_native_epoch_step']=re.findall(r'Epoch \[(\d+)/(\d+)\]\[(\d+)/(\d+)\]',native)[-1:]
 record['native_log_path']=str(logger)
 locks=Path('/proc/locks').read_text().splitlines();held={}
 for kind in ('training','diagnostic','exclusive'):
  p=Path('/tmp/cluster_project_gpu0_'+kind+'.lock')
  held[kind]=[int(line.split()[4]) for line in locks if line.split()[5].split(':')[-1]==str(p.stat().st_ino)] if p.exists() else []
 record['lock_owner_pids']=held
print(json.dumps(record))
'''%(hostname,str(gpu),uuid,str(gpu),name,REMOTE_ROOT,NAME)
    value=ssh(program,host=host)
    save(name+'_live'+suffix+'.json',value)
    print(json.dumps({'server':name,'observed_at':value['observed_at'],'occupied':value['occupied'],
        'native_epoch_step':value.get('last_native_epoch_step'),'validation_miou':value.get('native_validation_miou')}))
