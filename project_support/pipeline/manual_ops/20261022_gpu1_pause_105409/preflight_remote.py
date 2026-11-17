import socket
assert socket.gethostname() == 'dl04-MS-7E06'
import datetime as dt
import json
import os
from pathlib import Path
import re
import signal
import subprocess

ROOT = '/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
CFG = 'configs/Quard/ctf_hcg_csort_cgca/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca.yaml'
LOG = Path(ROOT) / 'logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca_20261021_232722.log'
RESUME = '/data/songcl/Project/Cluster_project/pipeline/resume_snapshots/20261021_gpu0_resume_031718_r2/20261021_051530/last.pth'


def proc(pid):
    p = Path('/proc') / str(pid)
    tail = (p / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, state=tail[0], ppid=int(tail[1]), pgid=int(tail[2]), sid=int(tail[3]),
        starttime=tail[19], cwd=os.readlink(p / 'cwd'), uid=p.stat().st_uid,
        args=[x.decode() for x in (p / 'cmdline').read_bytes().split(b'\0') if x])


target, protected = proc(732137), proc(979955)
assert target['starttime'] == '21298582' and protected['starttime'] == '21613920'
assert target['args'] == ['python', 'tools/train.py', CFG, '--gpu_ids', '1', '--num_gpus', '1', '--resume', RESUME]
assert protected['args'] == ['python', 'tools/train.py', 'configs/Quard/ctf_hcg_csort_hap/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hap.yaml', '--gpu_ids', '0', '--num_gpus', '1']
assert target['cwd'] == protected['cwd'] == ROOT and target['uid'] == protected['uid'] == os.getuid()
assert target['pgid'] == target['sid'] == target['pid'] and protected['pgid'] != target['pgid']
assert hasattr(os, 'pidfd_open') and hasattr(signal, 'pidfd_send_signal')
inventory = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,memory.used,utilization.gpu', '--format=csv,noheader,nounits'], text=True).strip()
for line in inventory.splitlines():
    index, uuid, *_ = [x.strip() for x in line.split(',')]
    assert uuid == {'0': 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c', '1': 'GPU-7f82edb9-f620-8045-caea-a75232265cd1'}[index]
contexts = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid,used_memory', '--format=csv,noheader,nounits'], text=True).strip()
assert any(row.split(',')[1].strip() == '732137' and row.startswith('GPU-7f82edb9-f620-8045-caea-a75232265cd1') for row in contexts.splitlines())
with LOG.open('rb') as stream:
    stream.seek(max(0, LOG.stat().st_size - 5000000))
    text = stream.read().decode('utf-8', errors='replace')
saved = re.findall(r'save last pth to ([^\r\n]+)', text)
assert saved, 'No current-run last checkpoint path observed; no process stopped'
checkpoint = Path(saved[-1].strip()).resolve()
base = Path('/data/songcl/Project/Cluster_project/Cluster_checkpoints') / Path(CFG).stem
assert checkpoint.is_relative_to(base.resolve()) and checkpoint.name == 'last.pth' and checkpoint.is_file()
progress = list(re.finditer(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[', text))
print(json.dumps(dict(observed_at=dt.datetime.now(dt.timezone.utc).isoformat(), hostname=socket.gethostname(),
    target=target, protected=protected, inventory=inventory, contexts=contexts, source_checkpoint=str(checkpoint),
    checkpoint_bytes=checkpoint.stat().st_size, log=str(LOG), log_bytes=LOG.stat().st_size,
    native_progress=[dict(epoch=int(m[1]), epochs=int(m[2]), step=int(m[3]), steps=int(m[4])) for m in progress[-2:]],
    runtime_HEAD=subprocess.check_output(['git', '-C', ROOT, 'rev-parse', 'HEAD'], text=True).strip(),
    admitted_M206_commit='898ff63a2cf63d3895a9e86c0ee3d1e5b672b335', pidfd_supported=True, read_only=True)))
