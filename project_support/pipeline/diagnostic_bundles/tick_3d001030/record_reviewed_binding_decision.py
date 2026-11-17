"""Record one actual current research decision through the canonical logger."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess
from anchor_bfc_packet import guard
HERE=Path(__file__).resolve().parent
ROOT=Path('D:/project/cluster_project')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 o=guard();intent=HERE/'decision_log_intent.json';result=HERE/'decision_log_result.json'
 assert not intent.exists() and not result.exists()
 a=json.loads((HERE/'bec_r1_static_anchor_result.json').read_text('utf8'));g=json.loads((HERE/'bec_r1_actual_local_guard.json').read_text('utf8'))
 assert a['owner']['token']==g['owner']['token']==o['token'] and g['native']==g['resources']=='NOT_RUN' and g['transport_calls']==0
 cmd=['C:/Program Files/Git/bin/bash.exe','C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh','cluster_project','other','BEC R1已审026c工具是否可作待测准备','接受同一R1的静态版本绑定；等待唯一GPU0原CTS释放后按原协议实测','当前实际guard已到达GPU0登记CTS忙及GPU1授权拒绝；零transport，不是native通过。R1仍pending，原9b失败与所有暂停保留。','pipeline/diagnostic_bundles/tick_3d001030/bec_r1_static_anchor_result.json SHA'+sha(HERE/'bec_r1_static_anchor_result.json')+'; pipeline/diagnostic_bundles/tick_3d001030/bec_r1_actual_local_guard.json SHA'+sha(HERE/'bec_r1_actual_local_guard.json')]
 with intent.open('x',encoding='utf8') as f:json.dump({'owner_token':o['token'],'recorded_at':datetime.now(timezone.utc).isoformat(),'command':cmd},f,ensure_ascii=False,indent=2)
 env=dict(os.environ,PROJECT_ROOT='D:/project',PYTHONDONTWRITEBYTECODE='1')
 r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',env=env,timeout=30)
 with result.open('x',encoding='utf8') as f:json.dump({'owner_token':o['token'],'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},f,ensure_ascii=False,indent=2)
 assert r.returncode==0,r.stderr
 print(r.stdout.strip())
if __name__=='__main__':main()
