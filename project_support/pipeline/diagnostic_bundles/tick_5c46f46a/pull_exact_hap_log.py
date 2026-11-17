"""Pull only the original HAP run log and verify its previously observed remote SHA."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess

BASE=Path(__file__).resolve().parent
PROJECT=BASE.parents[2]
def main():
    observation=json.loads((BASE/'hap_crash_remote_inspection.json').read_text(encoding='utf-8'))['data']
    assert observation['hap_pid_absent'] and observation['hostname']=='dl04-MS-7E06'
    remote=observation['log']['path']
    assert remote.endswith('/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hap_20261022_001959.log')
    dest=PROJECT/'Checkpoints/server_4/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hap/20261022_002007'/Path(remote).name
    dest.parent.mkdir(parents=True,exist_ok=True)
    assert not dest.exists()
    command=['scp','-q','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
             'songcl@192.168.1.115:'+remote,str(dest)]
    r=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',timeout=80)
    assert r.returncode==0,r.stderr
    digest=hashlib.sha256(dest.read_bytes()).hexdigest()
    assert digest==observation['log']['sha256']
    text=dest.read_text(encoding='utf-8',errors='replace')
    assert 'AttributeError: Caught AttributeError in DataLoader worker process 1.' in text
    assert "AttributeError: 'Tensor' object has no attribute 'has_torch_function_unary'" in text
    progress=[tuple(map(int,m)) for m in re.findall(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[',text)]
    metrics=re.findall(r'(?<!sp)mIOU:\s*([0-9.]+)',text)
    result=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),command=command,
        returncode=r.returncode,stderr=r.stderr,remote_log=remote,log_local=str(dest),sha256=digest,
        bytes=dest.stat().st_size,remote_sha256_match=True,original_native_log=True,
        last_train_progress=progress[-1],rounded_validation_miou=metrics,
        exact_best_source='hap_checkpoint_evidence.json cpu_inspection.meta.best_miou',
        completed_epoch_checkpoint=18,interrupted_epoch=19,failure_scope='implementation',
        mechanism_falsified=False,resume_started=False)
    target=BASE/'hap_original_log_evidence.json'
    with target.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
