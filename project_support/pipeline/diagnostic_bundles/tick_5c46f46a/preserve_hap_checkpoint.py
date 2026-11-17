"""Copy a stable full HAP checkpoint and inspect on CPU; never resumes training."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

BASE=Path(__file__).resolve().parent
def main():
    params=dict(source_checkpoint='/data/songcl/Project/Cluster_project/Cluster_checkpoints/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hap/20261022_002007/last.pth',
                operation_id='20261022_hap_crash_5c46f46a')
    # Reuse only the audited CPU snapshot helper, never the old stop/action wrapper.
    helper=Path('D:/project/cluster_project/pipeline/manual_ops/20261022_gpu1_pause_105409/checkpoint_remote.py')
    assert hashlib.sha256(helper.read_bytes()).hexdigest()=='949db0f195d433dc9a7e22644d879f32b80be70fd4795cef59804daf00c33d30'
    payload='PARAMS='+repr(params)+'\n'+helper.read_text(encoding='utf-8')
    command=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
             'songcl@192.168.1.115','/home/songcl/.conda/envs/project_cluster/bin/python -B -']
    r=subprocess.run(command,input=payload,capture_output=True,text=True,encoding='utf-8',timeout=180)
    result=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),command=command,
        helper_path=str(helper),helper_sha256=hashlib.sha256(helper.read_bytes()).hexdigest(),
        payload_sha256=hashlib.sha256(payload.encode()).hexdigest(),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr)
    if r.returncode==0:result['data']=json.loads(r.stdout)
    target=BASE/'hap_checkpoint_evidence.json'
    with target.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(dict(path=str(target),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),**result.get('data',{})),ensure_ascii=False))
    if r.returncode:raise SystemExit(r.returncode)

if __name__=='__main__':main()
