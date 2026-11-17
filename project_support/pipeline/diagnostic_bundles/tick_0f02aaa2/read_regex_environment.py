"""Read stdlib provenance and bounded regex behavior; no dependency/environment mutation."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess
from anchor import ROOT,EXPECTED,guard,sha
HERE=Path(__file__).resolve().parent
guard()
script="""import socket
assert socket.gethostname()=='dl04-MS-7E06'
import sys,builtins,hashlib,json,re,sre_compile,inspect,traceback
from pathlib import Path
p=Path(sre_compile.__file__);s=p.read_text();lines=s.splitlines()
result={'python':sys.executable,'builtin_len_type':str(type(builtins.len)),'builtin_len_repr':repr(builtins.len),'sre_compile_path':str(p),'sre_compile_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'compile_function_lines':lines[70:115],'failure_site_lines':lines[211:236],'module_len_binding':repr(sre_compile.__dict__.get('len','ABSENT'))}
try:
 re.compile(r'(aa|bb|cc)+[1-3]');result['fresh_regex_compile']='PASS'
except BaseException as e:result.update(fresh_regex_compile='FAIL',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc())
print(json.dumps(result))
"""
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/home/songcl/.conda/envs/project_cluster/bin/python -B -'],input=script,capture_output=True,text=True,encoding='utf8',timeout=30)
assert r.returncode==0,r.stderr[-2000:]
out={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,'observation':json.loads(r.stdout),'scope':'Only read stdlib file and compile one fixed CPU regex in same interpreter; no site-package write, model import, native/GPU work or replay.'}
guard()
with (HERE/'regex_environment_readback.json').open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(out['observation'],ensure_ascii=False));print('SAVED_SHA256',sha(HERE/'regex_environment_readback.json'))
