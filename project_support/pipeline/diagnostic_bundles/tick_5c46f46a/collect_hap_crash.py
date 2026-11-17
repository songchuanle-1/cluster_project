"""Pinned, bounded read-only crash inspection; CPU-only checkpoint preservation separately."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

BASE = Path(__file__).resolve().parent
REMOTE_PAYLOAD = r'''
import socket
assert socket.gethostname() == 'dl04-MS-7E06'
import datetime as dt, hashlib, json, os, pwd, subprocess
from pathlib import Path
root = Path('/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1')
log = root / 'logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hap_20261022_001959.log'
checkpoint = Path('/data/songcl/Project/Cluster_project/Cluster_checkpoints/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hap/20261022_002007/last.pth')
def run(args):
    r = subprocess.run(args, capture_output=True, text=True, timeout=20)
    return dict(returncode=r.returncode, stdout=r.stdout.strip(), stderr=r.stderr.strip())
def file_info(p):
    s=p.stat()
    return dict(path=str(p),size=s.st_size,inode=s.st_ino,mtime_ns=s.st_mtime_ns)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()
process={'pid':128551,'exists':Path('/proc/128551').exists()}
if process['exists']:
    p=Path('/proc/128551')
    try:
        s=(p/'stat').read_text().rsplit(')',1)[1].split()
        argv=[x.decode() for x in (p/'cmdline').read_bytes().split(b'\0') if x]
        cwd=os.readlink(p/'cwd')
        process.update(uid=p.stat().st_uid,username=pwd.getpwuid(p.stat().st_uid).pw_name,
            starttime=s[19],state=s[0],executable=os.path.basename(argv[0]) if argv else '',
            cwd_in_current_project=cwd.startswith('/data/songcl/Project/Cluster_project/'),
            exact_hap_config_in_argv=any('ctf_hcg_csort_hap' in x for x in argv),
            ownership='FOREIGN_OR_UNREGISTERED_DO_NOT_TOUCH')
    except OSError as e:process['read_error']=str(e)
tensor=Path('/home/songcl/.conda/envs/project_cluster/lib/python3.10/site-packages/torch/_tensor.py')
tensor_lines=tensor.read_text().splitlines()
dataset=root/'framework/dataset/scannetv2.py'
out=dict(observed_at=dt.datetime.now(dt.timezone.utc).isoformat(),hostname=socket.gethostname(),
    hap_pid_absent=not Path('/proc/979955').exists(),other_gpu0_process=process,
    gpu0_inventory=run(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits']),
    gpu0_contexts=run(['nvidia-smi','-i','0','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits']),
    GPU1='NOT_QUERIED_RELEASED_TO_OTHERS',log={**file_info(log),'sha256':sha(log)},
    last_checkpoint=file_info(checkpoint),runtime_head=run(['git','-C',str(root),'rev-parse','HEAD']),
    dataset={**file_info(dataset),'sha256':sha(dataset)},
    tensor_source={**file_info(tensor),'sha256':sha(tensor),
        'lines_1215_to_1230':tensor_lines[1214:1230]},
    gpu_computation_started=False,signals_sent=False,source_or_environment_modified=False)
print(json.dumps(out))
'''

def main():
    command=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
             'songcl@192.168.1.115','/usr/bin/python3 -B -']
    r=subprocess.run(command,input=REMOTE_PAYLOAD,capture_output=True,text=True,encoding='utf-8',timeout=70)
    result=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),command=command,
        payload_sha256=hashlib.sha256(REMOTE_PAYLOAD.encode()).hexdigest(),returncode=r.returncode,
        stdout=r.stdout,stderr=r.stderr)
    if r.returncode==0:result['data']=json.loads(r.stdout)
    target=BASE/'hap_crash_remote_inspection.json'
    with target.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(dict(path=str(target),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),**result.get('data',{})),ensure_ascii=False))
    if r.returncode:raise SystemExit(r.returncode)

if __name__=='__main__':main()
