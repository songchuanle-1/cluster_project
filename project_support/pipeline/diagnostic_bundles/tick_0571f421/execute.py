"""Stage new independent diagnostics, execute synchronously, preserve all results."""
import argparse
from datetime import datetime, timezone
import shlex
from ops import CODE, OUT, ROOT, NAME, STAGE, SSH, guard, save, run, tick

parser=argparse.ArgumentParser()
parser.add_argument("mode",choices=["contracts","native","native_m95","native_loader","native_fresh","resource"])
parser.add_argument("--target",choices=["candidate","champion","baseline"])
parser.add_argument("--attempt",default="")
args=parser.parse_args()
owner=guard()
remaining=(datetime.fromisoformat(owner["deadline_at"])-datetime.now(timezone.utc)).total_seconds()
timeout=min(1250,int(remaining)-180)
assert timeout>120
label=args.mode+("_"+args.target if args.target else "")
if args.attempt:label+="_"+args.attempt
worker="measure_resources.py" if args.mode=="resource" else args.mode+".py"
assert not (OUT/(label+"_execution.json")).exists()
check=run(SSH+[shlex.join(["mkdir","-p",STAGE,STAGE+"/"+NAME])]);assert check.returncode==0,check.stderr
names=["manifest.json","integration_prereg.md","runtime.py",worker]
if args.mode=="resource":
    program="from pathlib import Path; p=Path("+repr(STAGE)+"); old=p/'resource.py'; target=p/'failed_resource_attempt1.py'; assert old.parent.resolve()==p.resolve() and target.parent.resolve()==p.resolve(); assert not target.exists() or not old.exists(); old.rename(target) if old.exists() else None"
    fixed=run(SSH+[shlex.join(["/usr/bin/python3","-B","-c",program])]);assert fixed.returncode==0,fixed.stderr
if args.mode=="contracts":
    prior=ROOT/"pipeline/diagnostic_bundles/tick_99e0a813"
    for name in ("fine_exchange_operator.py","fine_exchange_operator_v1.py"):
        r=run(["scp","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes",str(prior/name),"songcl@192.168.1.115:"+STAGE+"/"])
        assert r.returncode==0,r.stderr
for path in [OUT/n for n in names]+[CODE/"configs/Quard/ctf_hcg_csort_fle_r1"/(NAME+".yaml")]:
    guard();r=run(["scp","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes",str(path),"songcl@192.168.1.115:"+STAGE+"/"])
    assert r.returncode==0,r.stderr
for path in sorted((CODE/"framework/model/Quard_model"/NAME).glob("*.py")):
    guard();r=run(["scp","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes",str(path),"songcl@192.168.1.115:"+STAGE+"/"+NAME+"/"])
    assert r.returncode==0,r.stderr
guard()
command="source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh; conda activate project_cluster; "+shlex.join(["env","PYTHONDONTWRITEBYTECODE=1","python","-B",STAGE+"/"+worker]+(["--target",args.target,"--label",label] if args.target else []))
execution=run(SSH+[shlex.join(["bash","-lc",command])],timeout)
save(label+"_execution.json",{"observed_at":datetime.now(timezone.utc).isoformat(),"returncode":execution.returncode,"stdout":execution.stdout,"stderr":execution.stderr,"runtime_sha256":tick.digest(OUT/"runtime.py"),"worker_sha256":tick.digest(OUT/worker)})
fetch=run(["scp","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","songcl@192.168.1.115:"+STAGE+"/"+label+"_result.json",str(OUT/(label+"_result.json"))])
save(label+"_fetch.json",{"returncode":fetch.returncode,"stderr":fetch.stderr})
print(execution.stdout[-2500:]);print(execution.stderr[-2500:])
assert execution.returncode==0, "Diagnostic failed; evidence preserved"
assert fetch.returncode==0, fetch.stderr
print("FETCHED="+label)
