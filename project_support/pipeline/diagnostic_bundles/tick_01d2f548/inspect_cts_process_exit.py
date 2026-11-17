"""Readonly bounded original CTS terminal/process evidence; GPU0 only."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess
from anchor_bfc_packet import guard
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
REMOTE=r'''
import socket
assert socket.gethostname()=='dl04-MS-7E06'
import pathlib,subprocess,json,re,datetime,os
root=pathlib.Path('/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1')
assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()=='4e80006047d5cb3dcdfb9c1102e02c33f354a07d'
p=pathlib.Path('/proc/3505065/stat');present=p.exists()
log=pathlib.Path(TASK['log']);assert log.is_file() and str(log).startswith(str(root)+'/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cts_')
with log.open('rb') as f:f.seek(max(0,log.stat().st_size-300000));tail=f.read().decode(errors='replace')
lines=tail.replace('\r','\n').splitlines();special=[(i,s) for i,s in enumerate(lines) if any(x.lower() in s.lower() for x in ['Traceback','Error','Exception','Early stopping','Best mIoU','best_miou','mIoU:','mIoU =','Training finished','training complete'])]
matches=list(re.finditer(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[',tail))
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip();assert [s.strip() for s in gpu.split(',')][:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
print(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hostname':socket.gethostname(),'original_PID_present':present,'original_PID':3505065,'own_log':str(log),'log_bytes':log.stat().st_size,'last_train_progress':[int(matches[-1][i]) for i in (1,2,3,4)] if matches else None,'significant_lines':special[-35:],'last_lines':lines[-90:],'GPU0_inventory':gpu,'GPU0_contexts':contexts,'GPU1_queried':False,'read_only':True,'signals_sent':False}))
'''
def main():
 o=guard();q=json.loads((ROOT/'pipeline/queue.json').read_text('utf8'));t=next(x for x in q['gpu_queues']['server-4'] if x['id']=='M214-CTS');assert t['pid']==3505065
 target=HERE/'cts_exit_readonly_evidence.json';assert not target.exists()
 r=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -'],input='TASK='+repr({'log':t['log']})+'\n'+REMOTE,capture_output=True,text=True,encoding='utf8',timeout=40)
 result={'owner_token':o['token'],'command_scope':'Original CTS own log tail<=300000B, original PID existence, exact runtime HEAD and only GPU0 inventory/contexts','original_observer_error':'FileNotFoundError /proc/3505065/stat after hostname and runtime HEAD checks','returncode':r.returncode,'observation':json.loads(r.stdout) if r.returncode==0 else None,'stderr':r.stderr}
 guard()
 with target.open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
 assert r.returncode==0,r.stderr
 v=result['observation'];print(json.dumps({'path':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'original_PID_present':v['original_PID_present'],'last_train_progress':v['last_train_progress'],'significant_lines':v['significant_lines'],'last_lines':v['last_lines'][-22:],'GPU0_inventory':v['GPU0_inventory'],'GPU0_contexts':v['GPU0_contexts']},ensure_ascii=False))
if __name__=='__main__':main()
