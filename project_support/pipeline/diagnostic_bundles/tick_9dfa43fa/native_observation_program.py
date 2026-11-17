
from pathlib import Path
from datetime import datetime,timezone
import os,socket,json,hashlib,re,subprocess
assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==1001
proc=Path('/proc')/str(P['pid']);alive=proc.exists() and (proc/'stat').read_text().split(')')[-1].split()[0]!='Z'
def bounded(path,limit=65536):
 size=path.stat().st_size
 with path.open('rb') as f:f.seek(max(0,size-limit));raw=f.read(limit)
 return raw,{'path':str(path),'file_bytes':size,'bytes_read':len(raw),'tail_sha256':hashlib.sha256(raw).hexdigest(),'whole_file_read':size<=limit}
raw,loginfo=bounded(Path(P['log']));text=raw.decode('utf8',errors='replace')
steps=[tuple(int(v) for v in x if v) for x in re.findall(r'Train\[(\d+)/\d+\]:[^\r\n]*?\|\s*(\d+)/\d+|Epoch:\s*\[(\d+)\]\s*\[\s*(\d+)/\d+\]',text)]
validation_steps=re.findall(r'Val\[(\d+)/\d+\]:[^\r\n]*?\|\s*(\d+)/(\d+)',text)
loggers=[]
if alive:
 assert (proc/'cwd').resolve()==Path(P['root'])
 argv=[a.decode(errors='replace') for a in (proc/'cmdline').read_bytes().split(b'\0') if a]
 assert P['config'] in argv and 'tools/train.py' in argv
 cfg=Path(P['config']).stem;prefix=P['work_dir']+'/'+cfg+'/'
 for fd in (proc/'fd').iterdir():
  try:
   target=os.readlink(fd)
   if target.startswith(prefix) and target.endswith('.log') and target not in [x['path'] for x in loggers]:
    dat,info=bounded(Path(target));s=dat.decode('utf8',errors='replace')
    info['metric_lines']=[line[-600:] for line in s.splitlines() if re.search(r'mIoU :|best_miou|epochs_no_improve|epoch:|Saving|save model',line)][-16:]
    info['exact_miou_values']=[float(v) for v in re.findall(r'mIoU : ([0-9.eE+-]+)',s)]
    loggers.append(info)
  except (OSError,RuntimeError):pass
else:argv=[]
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.free,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip();assert gpu.split(',')[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'pid':P['pid'],'alive':alive,'argv':argv,'stdout_log':loginfo,'native_train_last5':steps[-5:],'native_val_last5':validation_steps[-5:],'stdout_error_markers':{x:x in text for x in ['Traceback','CUDA out of memory','RuntimeError']},'native_loggers':loggers,'gpu0':gpu,'total_bytes_read':len(raw)+sum(x['bytes_read'] for x in loggers),'signals_sent':False,'GPU_compute_started':False}))
