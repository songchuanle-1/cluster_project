"""Read-only canonical source integrity check; no authorization or launch is manufactured."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import yaml

BASE=Path(__file__).resolve().parent
PROJECT=BASE.parents[2]
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
sys.path.insert(0,str(SKILL))
import source_integrity

def main():
    server=yaml.safe_load((PROJECT/'SERVERS.yaml').read_text(encoding='utf-8'))['servers']['server-4']
    assert server['host']=='192.168.1.115' and server['expected_hostname']=='dl04-MS-7E06'
    assert server['allowed_gpus']==[0] and server['max_tasks_per_gpu']==1
    policy=json.loads((PROJECT/'pipeline/closure_policy.json').read_text(encoding='utf-8'))
    mappings=[(x['source'],server[x['server_key']].rstrip('/')) for x in policy['path_mappings']]
    probes=[]
    def ssh(host,user,command):
        assert (host,user)==('192.168.1.115','songcl')
        args=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',user+'@'+host,command]
        r=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',timeout=75)
        probes.append(dict(command=args,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
        assert r.returncode==0,r.stderr
        return r.stdout
    passed=False;error=None
    try:
        source_integrity.verify_git(server,'f51823bbddf0f8095a9a5813bf1f8169e3d7edb0',mappings,ssh)
        passed=True
    except Exception as exc:error=type(exc).__name__+': '+str(exc)
    result=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),passed=passed,error=error,
        source_integrity_file=str(SKILL/'source_integrity.py'),
        source_integrity_sha256=hashlib.sha256((SKILL/'source_integrity.py').read_bytes()).hexdigest(),
        tested_commit='f51823bbddf0f8095a9a5813bf1f8169e3d7edb0',mappings=mappings,probes=probes,
        read_only=True,source_synced=False,source_modified=False,GPU_computation=False,
        resume_authorization_created=False,resume_started=False)
    target=BASE/'hap_source_integrity.json'
    with target.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(dict(path=str(target),passed=passed,error=error,sha256=hashlib.sha256(target.read_bytes()).hexdigest()),ensure_ascii=False))
    if not passed:raise SystemExit(1)

if __name__=='__main__':main()
