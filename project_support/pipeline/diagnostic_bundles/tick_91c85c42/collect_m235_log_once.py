"""Read-only exact terminal log collection; no trainer, Torch or checkpoint load."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
TOKEN = '91c85c4270bd407ba432eca5dbf7d3a8'
REMOTE = '/data/songcl/Project/Cluster_project/Cluster_nsd_20261107/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_sinc_20261110_194721.log'
TARGET = 'songcl@192.168.1.115'
OPTIONS = ['-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=15', '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

owner_raw = json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text(encoding='utf8'))
owner = {k: owner_raw[k] for k in ('token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256')}
assert owner['token'] == TOKEN and owner['thread_id'] == os.environ['CODEX_THREAD_ID']
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
assert not (HERE/'m235_terminal_log_collection.actual.json').exists()
body = """import socket,os,pathlib,hashlib,json
assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001
p=pathlib.Path(%r)
s=p.stat();h=hashlib.sha256(p.read_bytes()).hexdigest()
assert not pathlib.Path('/proc/2248650').exists()
print(json.dumps(dict(hostname=socket.gethostname(),uid=os.getuid(),path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=h,pid_exists=False)))
""" % REMOTE
import shlex
query = subprocess.run(['ssh',*OPTIONS,TARGET,'python3 -B -c '+shlex.quote(body)],capture_output=True,text=True,encoding='utf8',timeout=45)
assert query.returncode == 0, query.stderr[-1000:]
proof = json.loads(query.stdout)
assert proof['bytes'] == 1938280
destination = ROOT/'Checkpoints/server_4/M235-SINC/b75c9152d7fd4ecea9af538101d777d4'/Path(REMOTE).name
destination.parent.mkdir(parents=True,exist_ok=True)
partial = destination.with_suffix('.log.partial')
assert not destination.exists() and not partial.exists()
scp = subprocess.run(['scp',*OPTIONS,TARGET+':'+REMOTE,str(partial)],capture_output=True,text=True,encoding='utf8',timeout=60)
assert scp.returncode == 0, scp.stderr[-1000:]
assert partial.stat().st_size == proof['bytes'] and sha(partial) == proof['sha256']
partial.replace(destination)
record = dict(owner=owner,recorded_at=datetime.now(timezone.utc).isoformat(),kind='TERMINAL_LOG_READ_ONLY_COLLECTION_SUPPLEMENT',archive_id='b75c9152d7fd4ecea9af538101d777d4',remote=proof,local=dict(path=destination.relative_to(ROOT).as_posix(),sha256=sha(destination),bytes=destination.stat().st_size),producer_sha256=sha(Path(__file__)),canonical_archive_log_local_was_empty=True,canonical_archive_unchanged=True,remote_mutations=False,Torch_imported=False,signals_sent=False,checkpoint_copied=False)
with (HERE/'m235_terminal_log_collection.actual.json').open('x',encoding='utf8') as f:
    json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(status='COLLECTED_HASH_VERIFIED',bytes=proof['bytes'],sha256=proof['sha256'],path=str(destination))))
