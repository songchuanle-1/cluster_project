"""Current research lease and bounded cluster-only evidence operations."""
from datetime import datetime,timedelta,timezone
import json,os,shlex,subprocess,sys,yaml
from pathlib import Path
os.environ.update(PROJECT_ROOT='D:/project',PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import foreground_tick as tick
import pipeline_monitor as monitor
ROOT=Path('D:/project/cluster_project');CODE=ROOT/'Cluster';OUT=Path(__file__).resolve().parent
TOKEN='28fc3749e22e4c968fcadf9b6a2907a6';THREAD='01a04987-fdbe-7301-b2f0-f9b6ab60f74c'
CID='m95-scale-specific-boundary-responsibility'
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
SSH=['-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10']
SERVERS=yaml.safe_load((ROOT/'SERVERS.yaml').read_text(encoding='utf-8'))['servers']
def guard(seconds=0):
 owner=tick.load(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
 assert owner['token']==TOKEN and owner['thread_id']==THREAD==os.environ['CODEX_THREAD_ID']
 assert (datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()>seconds
 assert tick.digest(ROOT/'pipeline/goal.json')=='42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec'
 assert tick.load(ROOT/'pipeline/execution_mode.json')=={'mode':'foreground','target_thread_id':THREAD}
 return owner
def save(name,value):
 guard();path=OUT/name;path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
def evidence(path):
 path=Path(path);return {'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path)}
def advance(paths=(),**updates):
 guard();work=tick.load(ROOT/'pipeline/research_work.json');candidate=next(c for c in work['candidates'] if c['id']==CID)
 candidate.update(updates);known={(e['path'],e['sha256']) for e in candidate['evidence']}
 for path in paths:
  item=evidence(path)
  if (item['path'],item['sha256']) not in known:candidate['evidence'].append(item)
 guard();tick.save(ROOT/'pipeline/research_work.json',work)
def run(args,timeout=120):return subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
def remote(server,program,conda=False,timeout=120):
 guard();cfg=SERVERS[server]
 assert server in ('server-3','server-4')
 program='import socket\nassert socket.gethostname()=='+repr(cfg['expected_hostname'])+'\n'+program
 command=shlex.join(['python' if conda else '/usr/bin/python3','-B','-c',program])
 if conda:command=shlex.join(['bash','-lc','source '+shlex.quote(cfg['conda_source'])+' && conda activate '+shlex.quote(cfg['conda_env'])+' && '+command])
 result=run(['ssh',*SSH,cfg['user']+'@'+cfg['host'],command],timeout)
 assert result.returncode==0,result.stderr[-5000:]
 return json.loads(result.stdout)
