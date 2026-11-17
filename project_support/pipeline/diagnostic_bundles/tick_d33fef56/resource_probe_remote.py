
from pathlib import Path
import os,json,subprocess,datetime,re,time,socket
assert socket.gethostname()=='dl04-MS-7E06','pinned hostname mismatch'
def run(args):
 x=subprocess.run(args,capture_output=True,text=True,check=True);return x.stdout.strip()
g=run(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'])
assert 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c' in g,'GPU UUID mismatch'
c=run(['nvidia-smi','-i','0','--query-compute-apps=pid,used_gpu_memory','--format=csv,noheader,nounits'])
root='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
p=Path('/proc/3842306');args=[x.decode() for x in (p/'cmdline').read_bytes().split(bytes([0])) if x]
assert os.readlink(str(p/'cwd'))==root,'M205 cwd mismatch'
assert args[1:]==['tools/train.py','configs/Quard/ctf_hcg_csort_mdc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mdc.yaml','--gpu_ids','0','--num_gpus','1'],'M205 argv mismatch'
assert (p/'stat').read_text().split()[21]=='14699953','M205 starttime mismatch'
log=Path(root+'/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mdc_20261021_050739.log')
with log.open('rb') as f:
 f.seek(max(0,log.stat().st_size-1024*1024));tail=f.read().decode('utf-8',errors='replace')
tail=re.sub(r'\x1b\[[0-9;]*[A-Za-z]','',tail);rows=[]
for row in re.split(r'[\r\n]+',tail):
 m=re.search(r'Train\[(\d+)/(\d+)\].*?\s(\d+)/(\d+)\s',row)
 if m:rows.append({'epoch':int(m[1]),'epochs':int(m[2]),'step':int(m[3]),'steps':int(m[4]),'row':row[-500:]})
cp=Path('/data/songcl/Project/Cluster_project/pipeline/resume_snapshots/20261021_gpu0_resume_031718_r2/20261021_051530/last.pth')
print(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hostname':socket.gethostname(),'gpu':0,'inventory':g,'contexts':c,'idle':not(c or float(g.split(',')[2])>=1024 or float(g.split(',')[3])>=10),'m205':{'pid':3842306,'actual_args_match':True,'cwd_match':True,'starttime_match':True,'last_native_progress':rows[-2:],'log_mtime':datetime.datetime.fromtimestamp(log.stat().st_mtime,datetime.timezone.utc).isoformat(),'log_age_seconds':time.time()-log.stat().st_mtime,'log_bytes':log.stat().st_size},'m206_resume_checkpoint':{'path':str(cp),'exists':cp.exists(),'bytes':cp.stat().st_size if cp.exists() else None,'rehash_or_load_this_probe':False},'new_gpu_work':False}))
