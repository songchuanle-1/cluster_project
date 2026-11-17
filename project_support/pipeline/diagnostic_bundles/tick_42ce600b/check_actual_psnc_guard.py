"""Exercise the real current project adapter guard with transport prohibited."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
PACKAGE=HERE/'psnc_operational_prepare';TOKEN='42ce600bac914e84bceee707167a669b'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    names=['queue.json','running.json','research_work.json','experiments/M208-HRC.json','experiments/M209-PSBR.json',
        'experiments/M206-CGCA.json','experiments/M207-HAP.json','admissions/M208-HRC.json','admissions/M209-PSBR.json']
    before={name:sha(ROOT/'pipeline'/name) for name in names}
    source_before={str(p):sha(p) for p in [PACKAGE/'adapter.py',PACKAGE/'remote_ops.py',PACKAGE/'adapter_release.json']}
    execution=HERE/'psnc_execution';assert not execution.exists()
    dangerous_events=[]
    def audit(event,args):
        if event=='socket.connect':
            dangerous_events.append(event);raise AssertionError('No real network permitted in local guard test')
        if event=='subprocess.Popen':
            executable=Path(str(args[0])).name.lower()
            if executable in ('ssh','ssh.exe','scp','scp.exe','sftp','sftp.exe','nvidia-smi','nvidia-smi.exe'):
                dangerous_events.append(executable);raise AssertionError('No remote/GPU process permitted in local guard test')
    sys.addaudithook(audit)
    spec=importlib.util.spec_from_file_location('psnc_actual_guard_adapter',PACKAGE/'adapter.py')
    adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
    class NoTransport:
        def __init__(self):self.calls=[]
        def call(self,*args,**kwargs):
            self.calls.append(str(args[0]) if args else 'unknown')
            raise AssertionError('Current occupied GPU must be refused before any transport')
    transport=NoTransport()
    instance=adapter.Adapter(transport=transport)
    caught=None
    try:instance.prepare(0)
    except adapter.Refused as error:caught={'type':type(error).__name__,'reason':str(error)}
    assert caught is not None and caught['reason']=='Selected GPU has registered running task',caught
    assert transport.calls==[] and dangerous_events==[] and 'torch' not in sys.modules
    assert not execution.exists()
    assert {name:sha(ROOT/'pipeline'/name) for name in names}==before
    assert {name:sha(Path(name)) for name in source_before}==source_before
    assert read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')==owner
    result={'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,
        'candidate_id':'hierarchy-parent-spectral-nonlinear-token-coupling','code_commit':adapter.COMMIT,
        'operation':'Adapter(transport=NoTransport).prepare(0) against actual current project',
        'status':'ACTUAL_CURRENT_REGISTERED_BUSY_GUARD_REFUSED_BEFORE_TRANSPORT','caught':caught,
        'transport_calls':transport.calls,'remote_or_GPU_process_events':dangerous_events,'torch_imported':False,
        'production_native_execution_dir_created':False,'production_manifest_lease_binding_created':False,
        'protected_project_records_unchanged':{name:sha(ROOT/'pipeline'/name)==expected for name,expected in before.items()},
        'module_and_static_release_hashes_unchanged':source_before,'actual_owner_unchanged':True,
        'scope':'Actual local project guard only; not real remote/native/resource execution, not an admission or idle proof.'}
    path=HERE/'psnc_actual_guard_integration.json'
    with path.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'path':str(path),'sha256':sha(path),'status':result['status'],'native':'NOT_RUN'},ensure_ascii=False))

if __name__=='__main__':main()
