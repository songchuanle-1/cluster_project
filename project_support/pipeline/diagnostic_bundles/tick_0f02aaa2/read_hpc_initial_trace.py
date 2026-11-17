"""Exact failed HPC request stderr readback only; no native replay."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent
guard()
script="""import socket
assert socket.gethostname()=='dl04-MS-7E06'
from pathlib import Path
import hashlib,json
p=Path('/data/songcl/Project/Cluster_project/pipeline/hpc_0f02aaa2_gpu0/smoke_champion_stderr.log');b=p.read_bytes();h=hashlib.sha256(b).hexdigest()
assert h=='41b232a399da105a159e67250540ba4b516baf08abdb2b6474f5d70c5850ad10'
print(json.dumps({'path':str(p),'bytes':len(b),'sha256':h,'stderr':b.decode('utf8',errors='replace')}))
"""
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -'],input=script,capture_output=True,text=True,encoding='utf8',timeout=30)
assert r.returncode==0,r.stderr[-2000:]
out={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,'request_id':'cb0abedec37c4d5586814d8d45965f7f','observation':json.loads(r.stdout),'scope':'Exact original HPC failed request stderr; no signal, model or GPU computation.'}
guard()
with (HERE/'hpc_initial_smoke_trace.json').open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(out['observation']['stderr'][-9000:]);print('SAVED_SHA256',sha(HERE/'hpc_initial_smoke_trace.json'))
