"""Known CreateProcess/WinError2 no-child recovery, using discovered Git Bash."""
from pathlib import Path
import json,os,subprocess
from anchor_bfc_packet import guard
HERE=Path(__file__).resolve().parent
def main():
 o=guard();intent=json.loads((HERE/'decision_log_intent.json').read_text('utf8'));old=intent['command'];assert intent['owner_token']==o['token']
 assert not Path(old[0]).exists() and not (HERE/'decision_log_result.json').exists()
 result=HERE/'decision_log_recovery_result.json';assert not result.exists()
 exe=Path('C:/Program Files (x86)/Git/bin/bash.exe');assert exe.is_file()
 cmd=[str(exe),*old[1:]]
 with (HERE/'decision_log_recovery_intent.json').open('x',encoding='utf8') as f:json.dump({'owner_token':o['token'],'reason':'Original CreateProcess raised WinError2 before any child or canonical logger execution; discovered installed Git Bash corrects executable path only.','original_no_child':True,'command':cmd},f,ensure_ascii=False,indent=2)
 r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',env=dict(os.environ,PROJECT_ROOT='D:/project',PYTHONDONTWRITEBYTECODE='1'),timeout=30)
 with result.open('x',encoding='utf8') as f:json.dump({'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'owner_token':o['token']},f,ensure_ascii=False,indent=2)
 assert r.returncode==0,r.stderr
 print(r.stdout.strip())
if __name__=='__main__':main()
