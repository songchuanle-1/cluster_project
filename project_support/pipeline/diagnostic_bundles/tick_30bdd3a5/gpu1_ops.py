"""User-authorized GPU1 experiments bound to the current foreground lease."""
from datetime import datetime,timedelta,timezone
import os,json,sys,subprocess,shlex,yaml
from pathlib import Path
os.environ.update(PROJECT_ROOT='D:/project',PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import foreground_tick as tick
ROOT=Path('D:/project/cluster_project');OUT=Path(__file__).resolve().parent
TOKEN='30bdd3a5fb344e089ceab842a3b013f5';THREAD='01a04987-fdbe-7301-b2f0-f9b6ab60f74c'
UUID='GPU-7f82edb9-f620-8045-caea-a75232265cd1'
AUTH=ROOT/'pipeline/authorizations/server4_gpu1_20261019.json'
GOAL=tick.digest(ROOT/'pipeline/goal.json')
SSH=['-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10']
def guard(seconds=0):
 owner=tick.load(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
 assert owner['token']==TOKEN and owner['thread_id']==THREAD==os.environ['CODEX_THREAD_ID']
 assert (datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()>seconds
 assert tick.digest(ROOT/'pipeline/goal.json')==GOAL
 cfg=yaml.safe_load((ROOT/'SERVERS.yaml').read_text(encoding='utf-8'))['servers']['server-4']
 assert cfg['host']=='192.168.1.115' and cfg['expected_hostname']=='dl04-MS-7E06'
 assert cfg['allowed_gpus']==[0,1] and cfg['max_tasks_per_gpu']==1 and cfg['expected_gpu_uuids']['1']==UUID
 auth=tick.load(AUTH);assert auth['source_message']=='授权GPU1 可以做实验' and auth['source_role']=='human' and auth['physical_gpu']==1 and auth['expected_gpu_uuid']==UUID
 return owner,cfg
def evidence(path):
 path=Path(path);return {'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path)}
def save(name,value):
 guard();path=OUT/name;path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
def advance(cid,paths=(),**updates):
 guard();work=tick.load(ROOT/'pipeline/research_work.json');c=next(c for c in work['candidates'] if c['id']==cid)
 c.update(updates);seen={(e['path'],e['sha256']) for e in c['evidence']}
 for path in paths:
  item=evidence(path)
  if (item['path'],item['sha256']) not in seen:c['evidence'].append(item)
 guard();tick.save(ROOT/'pipeline/research_work.json',work)
def remote(program,timeout=120,conda=False):
 _,cfg=guard()
 code='import socket\nassert socket.gethostname()=='+repr(cfg['expected_hostname'])+'\n'+program
 command=shlex.join(['python' if conda else '/usr/bin/python3','-B','-c',code])
 if conda:command=shlex.join(['bash','-lc','source '+shlex.quote(cfg['conda_source'])+' && conda activate '+shlex.quote(cfg['conda_env'])+' && '+command])
 p=subprocess.run(['ssh',*SSH,cfg['user']+'@'+cfg['host'],command],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
 assert p.returncode==0,p.stderr[-7000:]
 return json.loads(p.stdout)
