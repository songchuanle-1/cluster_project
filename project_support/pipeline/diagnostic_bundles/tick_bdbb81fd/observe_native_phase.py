"""Read original native iterator markers while TRAIN is between epochs."""
from pathlib import Path
from datetime import datetime,timezone
import json,shlex,subprocess
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent
def main():
    guard();prior=json.loads((HERE/'cre_training_progress_observation.json').read_text('utf8'))
    assert prior['owner']==EXPECTED and prior['returncode']==0
    identity=prior['observation']['identity_after'];assert identity['pid']==118189
    exp=json.loads((ROOT/'pipeline/experiments/M217-CRE.json').read_text('utf8'))
    payload={'identity':identity,'log':exp['log']}
    script='''import socket,json,os,time,re,hashlib
from pathlib import Path
from datetime import datetime,timezone
assert socket.gethostname()=='dl04-MS-7E06'
p=json.loads(PAYLOAD);want=p['identity'];proc=Path('/proc')/str(want['pid'])
def identity():
 assert proc.exists() and proc.stat().st_uid==os.getuid()
 argv=(proc/'cmdline').read_bytes().replace(b'\\0',b' ').decode();cwd=str((proc/'cwd').resolve())
 start=(proc/'stat').read_text().rsplit(') ',1)[1].split()[19]
 assert (argv,cwd,start)==(want['argv'],want['cwd'],want['start_ticks'])
 return {'pid':want['pid'],'argv':argv,'cwd':cwd,'start_ticks':start}
before=identity();path=Path(p['log']);assert path.stat().st_uid==os.getuid()
def sample():
 size=path.stat().st_size
 with path.open('rb') as f:f.seek(max(0,size-16000));raw=f.read()
 text=raw.decode('utf8',errors='replace').replace('\\r','\\n')
 markers=[{'phase':a,'epoch':int(b),'epochs':int(c),'step':int(d),'steps':int(e)} for a,b,c,d,e in re.findall(r'([A-Za-z]+)\\[(\\d+)/(\\d+)\\]:[^\\n]*?\\|\\s*(\\d+)/(\\d+)',text)]
 return {'observed_at':datetime.now(timezone.utc).isoformat(),'log_size':size,'tail_sha256':hashlib.sha256(raw).hexdigest(),'last_native_markers':markers[-3:],'exception_seen':any(x in text for x in ['Traceback','CUDA out of memory','RuntimeError']),'last_600_characters':text[-600:]}
a=sample();time.sleep(3);b=sample();after=identity();assert before==after
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'identity_before':before,'identity_after':after,'samples':[a,b],'signals_sent':False,'GPU_computation_or_query':False}))
'''.replace('PAYLOAD',repr(json.dumps(payload)))
    args=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','export PYTHONDONTWRITEBYTECODE=1 && /usr/bin/python3 -B -c '+shlex.quote(script)]
    guard();r=subprocess.run(args,capture_output=True,text=True,timeout=30)
    record={'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'command':args,'returncode':r.returncode,'stderr':r.stderr,
            'prior_physical_source_observation':{'path':(HERE/'cre_training_progress_observation.json').relative_to(ROOT).as_posix(),'sha256':sha(HERE/'cre_training_progress_observation.json')}}
    if r.returncode==0:record['observation']=json.loads(r.stdout)
    guard()
    with (HERE/'cre_native_phase_observation.json').open('x',encoding='utf8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
    assert r.returncode==0,r.stderr
    print(json.dumps({'samples':[{k:s[k] for k in ('observed_at','log_size','last_native_markers','exception_seen')} for s in record['observation']['samples']],
                      'sha256':sha(HERE/'cre_native_phase_observation.json')}))
if __name__=='__main__':main()
