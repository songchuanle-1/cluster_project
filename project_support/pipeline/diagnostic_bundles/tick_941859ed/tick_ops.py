"""Bounded cluster-only evidence operations bound to this foreground lease."""
from datetime import datetime,timedelta,timezone
import os,json,sys,shlex,subprocess,yaml
from pathlib import Path
os.environ.update(PROJECT_ROOT='D:/project',PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import foreground_tick as tick
ROOT=Path('D:/project/cluster_project');OUT=Path(__file__).resolve().parent
TOKEN='941859edec734e62b88712a7f1660136';THREAD='01a04987-fdbe-7301-b2f0-f9b6ab60f74c'
GOAL='42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec'
SERVERS=yaml.safe_load((ROOT/'SERVERS.yaml').read_text(encoding='utf-8'))['servers']
PRIMARY=['m95-scale-specific-boundary-responsibility','m95-expression-specific-point-message']
AUX=['m95-native-relation-other-sign-conflict','m95-native-main-role-weight-precedence','m95-native-secondary-positive-mass','m95-native-between-pair-support']
def guard(seconds=0):
 owner=tick.load(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
 assert owner['token']==TOKEN and owner['thread_id']==THREAD==os.environ['CODEX_THREAD_ID']
 assert (datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()>seconds
 assert tick.digest(ROOT/'pipeline/goal.json')==GOAL
 assert tick.load(ROOT/'pipeline/execution_mode.json')=={'mode':'foreground','target_thread_id':THREAD}
 return owner
def evidence(path):
 path=Path(path);return {'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path)}
def save(name,data):
 guard();path=OUT/name
 with path.open('x',encoding='utf-8') as stream:json.dump(data,stream,ensure_ascii=False,indent=2,allow_nan=False)
def remote(server,program,timeout=90):
 guard();assert server in ('server-3','server-4');cfg=SERVERS[server]
 code='import socket\nassert socket.gethostname()=='+repr(cfg['expected_hostname'])+'\n'+program
 process=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10',cfg['user']+'@'+cfg['host'],shlex.join(['/usr/bin/python3','-B','-c',code])],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
 assert process.returncode==0,process.stderr[-3000:]
 return json.loads(process.stdout)
