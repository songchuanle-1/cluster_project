"""Scoped helpers for the explicitly authorized M204 checkpoint resume."""
from datetime import datetime, timedelta, timezone
import hashlib,json,os,shlex,subprocess,sys
from pathlib import Path
os.environ.update(PROJECT_ROOT='D:/project',PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import foreground_tick as tick
ROOT=Path('D:/project/cluster_project')
CODE=ROOT/'Cluster'
OUT=Path(__file__).resolve().parent
TOKEN='2546d8030a97460eb9c7fca51a48a759'
THREAD='01a04987-fdbe-7301-b2f0-f9b6ab60f74c'
GOAL='42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec'
CID='coarse-semantic-point-cross-attention'
ID='M204-CPA'
OLD=ROOT/'pipeline/diagnostic_bundles/tick_92463b56'
ORIGINAL=ROOT/'pipeline/diagnostic_bundles/tick_72695a5d'
AUTH=ROOT/'pipeline/authorizations/cpa_resume_M204.json'
STAGE='/data/songcl/Project/Cluster_project/pipeline/cpa_resume_2546d803'
SSH=['-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10']
def guard(seconds=0):
 owner=tick.load(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
 assert owner['token']==TOKEN and owner['thread_id']==THREAD==os.environ['CODEX_THREAD_ID']
 assert (datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()>seconds
 assert tick.digest(ROOT/'pipeline/goal.json')==GOAL
 assert tick.load(ROOT/'pipeline/execution_mode.json')=={'mode':'foreground','target_thread_id':THREAD}
 return owner
def save(name,value):
 guard();path=OUT/name;path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
def evidence(path):
 path=Path(path)
 return {'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path)}
def advance(paths=(),**updates):
 guard();work=tick.load(ROOT/'pipeline/research_work.json')
 candidate=next(c for c in work['candidates'] if c['id']==CID);candidate.update(updates)
 known={(e['path'],e['sha256']) for e in candidate['evidence']}
 for path in paths:
  item=evidence(path)
  if (item['path'],item['sha256']) not in known:candidate['evidence'].append(item)
 guard();tick.save(ROOT/'pipeline/research_work.json',work)
def run(args,timeout=120):
 return subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
def transport(command,timeout=120):
 guard();command='test "$(hostname)" = dl04-MS-7E06 && '+command
 result=run(['ssh',*SSH,'songcl@192.168.1.115',command],timeout)
 assert result.returncode==0,result.stderr[-5000:]
 return result.stdout.strip()
def ssh(program,conda=False,timeout=120):
 program="import socket\nassert socket.gethostname()=='dl04-MS-7E06'\n"+program
 if conda:
  command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && '+shlex.join(['python','-B','-c',program])
  result=transport(shlex.join(['bash','-lc',command]),timeout)
 else:result=transport(shlex.join(['/usr/bin/python3','-B','-c',program]),timeout)
 return json.loads(result)
