
import socket,subprocess,os,json,datetime,hashlib
from pathlib import Path
assert socket.gethostname()=='dl04-MS-7E06'
def run(a):return subprocess.run(a,capture_output=True,text=True,check=True).stdout.strip()
inv=run(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'])
expected={'0':'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c','1':'GPU-7f82edb9-f620-8045-caea-a75232265cd1'}
for line in inv.splitlines():
 parts=[x.strip() for x in line.split(',')]
 if parts[0] in expected:assert parts[1]==expected[parts[0]],'GPU UUID mismatch'
gpu1=[x.strip() for x in next(x for x in inv.splitlines() if x.startswith('1,')).split(',')]
contexts1=run(['nvidia-smi','-i','1','--query-compute-apps=pid,used_gpu_memory','--format=csv,noheader,nounits'])
assert not contexts1 and int(gpu1[2])<1024 and int(gpu1[3])<10,'GPU1 not idle'
p=Path('/proc/3842306');args=[x.decode() for x in (p/'cmdline').read_bytes().split(bytes([0])) if x]
root='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
assert os.readlink(str(p/'cwd'))==root and (p/'stat').read_text().split()[21]=='14699953'
assert args[1:]==['tools/train.py','configs/Quard/ctf_hcg_csort_mdc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mdc.yaml','--gpu_ids','0','--num_gpus','1']
cp=Path('/data/songcl/Project/Cluster_project/pipeline/resume_snapshots/20261021_gpu0_resume_031718_r2/20261021_051530/last.pth');sha=hashlib.sha256()
with cp.open('rb') as f:
 for z in iter(lambda:f.read(1024*1024),b''):sha.update(z)
assert sha.hexdigest()=='2e11ea38ba81b657301a34efc11483455fb1f9eeb83a5f4d52fbc40ffb4669d7'
print(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hostname':socket.gethostname(),'inventory':inv,'gpu1_contexts':contexts1,'gpu1_idle':True,'m205_pid':3842306,'m205_exact_process_preserved':True,'m205_starttime':'14699953','checkpoint':str(cp),'checkpoint_sha256':sha.hexdigest(),'checkpoint_bytes':cp.stat().st_size,'new_cuda_work':False}))
