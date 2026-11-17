"""Current-lease native ILA diagnostic staging and execution."""
import ast
import base64
import copy
import hashlib
import json
from pathlib import Path
import register

c=register.c
ROOT,BASE=register.ROOT,register.OUT
c.CID='m95-final-ila-expression-source-dependence'
c.OUT=BASE/'ila_runtime';c.STAGE+='/ila_runtime'


def main():
    owner,_=c.guard(1200);c.OUT.mkdir(exist_ok=False)
    worker=(BASE/'language_worker.py').read_bytes();ast.parse(worker.decode('utf-8'))
    runtime=(ROOT/'pipeline/diagnostic_bundles/tick_658721c0/native_runtime.py').read_text(encoding='utf-8').replace('658721c071ae487ea47224e55d51abde',c.TOKEN).replace('01a04987-fdbe-7301-b2f0-f9b6ab60f74c',c.THREAD)
    payload={'native_runtime.py':runtime.encode('utf-8'),'worker.py':worker}
    manifest=copy.deepcopy(c.tick.load(BASE/'native_manifest.json'))
    manifest.update(stage=c.STAGE,candidate_id=c.CID,protocol=c.evidence(BASE/'ila_source_preregistration.json'))
    manifest['diagnostic_files']={name:hashlib.sha256(value).hexdigest() for name,value in payload.items()}
    c.save('native_manifest.json',manifest);payload['native_manifest.json']=(c.OUT/'native_manifest.json').read_bytes()
    c.save('execution_lease.json',{'token':c.TOKEN,'thread_id':c.THREAD,'project':'cluster_project',
        'deadline_at':owner['deadline_at'],'native_manifest_sha256':c.tick.digest(c.OUT/'native_manifest.json')})
    payload['execution_lease.json']=(c.OUT/'execution_lease.json').read_bytes()
    encoded={name:base64.b64encode(value).decode('ascii') for name,value in payload.items()}
    hashes={name:hashlib.sha256(value).hexdigest() for name,value in payload.items()}
    code='''
import base64,hashlib,json
from pathlib import Path
stage=Path(STAGE);stage.mkdir(exist_ok=False)
for name,value in PAYLOAD.items():
 path=stage/name
 assert path.resolve().is_relative_to(stage.resolve())
 with path.open('xb') as stream:stream.write(base64.b64decode(value))
 assert hashlib.sha256(path.read_bytes()).hexdigest()==HASHES[name]
print(json.dumps({'staged':str(stage),'files':len(PAYLOAD)}))
'''
    staged=c.save('staging.json',c.remote('STAGE='+repr(c.STAGE)+'\nPAYLOAD='+repr(encoded)+'\nHASHES='+repr(hashes)+'\n'+code))
    assert c.tick.load(staged)['returncode']==0
    c.advance([c.OUT/'native_manifest.json',BASE/'language_worker.py',staged,Path(__file__)],
        'Execute actual final ILA source pairing diagnostic; receiving point query and native final query remain fixed.')
    code='''
import json,subprocess,sys
from pathlib import Path
stage=Path(STAGE)
p=subprocess.run([sys.executable,'-B',str(stage/'worker.py'),'--lease',str(stage/'execution_lease.json')],capture_output=True,text=True,timeout=580)
r={'returncode':p.returncode,'stdout':p.stdout[-8000:],'stderr':p.stderr[-14000:]}
path=stage/'native_ila_result.json'
if path.exists():r['result']=json.loads(path.read_text())
print(json.dumps(r))
'''
    observation=c.remote('STAGE='+repr(c.STAGE)+'\n'+code,timeout=620,conda=True)
    execution=c.save('native_execution.json',observation);assert observation['returncode']==0
    result=observation['data'].get('result',{});path=c.save('native_ila_result.json',result)
    c.advance([execution,path],'Interpret actual final ILA sensitivity and all scene directions without promoting a language-routing architecture or trained benefit.')
    print(json.dumps({'returncode':observation['data']['returncode'],'execution_completed':result.get('execution_completed'),
        'error':result.get('error'),'summary':result.get('summary')}))


if __name__=='__main__':main()
