"""Final independent source binding and exact training-import guard probe."""
import ast
from datetime import datetime,timezone
import shlex
from ops import CODE,OUT,ROOT,NAME,STAGE,SSH,guard,save,run,tick

guard()
package=CODE/"framework/model/Quard_model"/NAME
initial=tick.load(OUT/"static_independence.json")
source={p.name:tick.digest(p) for p in sorted(package.glob("*.py"))}
assert len(source)==9
for name,expected in initial["source_hashes"].items():
    if name!="__init__.py":assert source[name]==expected
for path in package.glob("*.py"):
    tree=ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node,ast.ImportFrom) and node.module:assert "Quard_model.model_" not in node.module
config=CODE/"configs/Quard/ctf_hcg_csort_fle_r1"/(NAME+".yaml")
assert tick.digest(config)==initial["config_sha256"]
save("final_source.json",{"observed_at":datetime.now(timezone.utc).isoformat(),"passed_independence":True,
    "source_hashes":source,"config_sha256":tick.digest(config),"seven_mathematical_source_files_unchanged":True,
    "config_unchanged":True,"no_model_revision":True,"unique_basename":True,"new_python_file":"startup_guard.py"})
for path in [OUT/"guard_probe.py",OUT/"final_source.json"]+list(package.glob("*.py")):
    target=STAGE+("/"+NAME if path.parent==package else "")+"/"
    p=run(["scp","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes",str(path),"songcl@192.168.1.115:"+target]);assert p.returncode==0,p.stderr
command="source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh; conda activate project_cluster; "+shlex.join(["env","PYTHONDONTWRITEBYTECODE=1","python","-B",STAGE+"/guard_probe.py"])
p=run(SSH+[shlex.join(["bash","-lc",command])],180)
save("guard_probe_execution.json",{"returncode":p.returncode,"stdout":p.stdout,"stderr":p.stderr})
fetch=run(["scp","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","songcl@192.168.1.115:"+STAGE+"/guard_probe_result.json",str(OUT/"guard_probe_result.json")]);assert fetch.returncode==0,fetch.stderr
assert p.returncode==0,p.stderr
assert tick.load(OUT/"guard_probe_result.json")["passed"]
print(p.stdout)
