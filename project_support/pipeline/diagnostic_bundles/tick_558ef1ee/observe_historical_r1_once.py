"""Current-owner read-only reconciliation of historical successful RVE stage."""
import ast,hashlib,json,os,shlex,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path("D:/project/cluster_project")
HERE=Path(__file__).resolve().parent
TOKEN="558ef1ee132543f98d6897c98aff9dc9"
old=ROOT/"pipeline/diagnostic_bundles/tick_b410c66a/observe_current_once_v2.py"
source=ROOT/"pipeline/diagnostic_bundles/tick_b410c66a/rvec_r1_source_prepare/source_version.json"
assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS")=="0"
owner_raw=json.loads((ROOT/"pipeline/headless/.foreground.lockdir/owner.json").read_text())
owner={k:owner_raw[k] for k in ("token","thread_id","generated_at","deadline_at","context_sha256","pending_sha256")}
assert owner["token"]==TOKEN and owner["thread_id"]==os.environ["CODEX_THREAD_ID"]
assert datetime.now(timezone.utc)<datetime.fromisoformat(owner["deadline_at"])
assert hashlib.sha256(source.read_bytes()).hexdigest()=="ff2872df24a82c761a4ff50e54e9ed2f6c52b07a877e90714ae5e59bd5ab2851"
version=json.loads(source.read_text())
program=next(ast.literal_eval(n.value) for n in ast.parse(old.read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="PROGRAM" for t in n.targets))
payload={"owner":version["owner"],"source_commit":version["source_commit"]}
result=HERE/"historical_r1_runtime_observation.json";assert not result.exists()
record={"current_owner":owner,"observed_historical_owner":version["owner"],"purpose":"READ_ONLY_RECONCILIATION_NO_OLD_EXECUTION_OR_LEASE_REPLAY","recorded_at":datetime.now(timezone.utc).isoformat(),"remote_program_sha256":hashlib.sha256(program.encode()).hexdigest(),"current_wrapper_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"certainty":"uncertain"}
process=subprocess.Popen(["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=8","songcl@192.168.1.115","PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -c "+shlex.quote(program)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding="utf-8",errors="replace")
try:
 stdout,stderr=process.communicate(json.dumps(payload),timeout=40)
 record.update(certainty="terminal",returncode=process.returncode,stderr=stderr[:3000])
 try:record["observation"]=json.loads(stdout)
 except json.JSONDecodeError:record["stdout_excerpt"]=stdout[:2000]
except subprocess.TimeoutExpired:record["reason"]="Read-only observation uncertain; no signals or retry"
with result.open("x",encoding="utf-8",newline="\n") as stream:json.dump(record,stream,ensure_ascii=False,indent=2);stream.write("\n")
assert record.get("returncode")==0 and "observation" in record
print(json.dumps({"path":str(result),"sha256":hashlib.sha256(result.read_bytes()).hexdigest(),"observation":record["observation"]}))
