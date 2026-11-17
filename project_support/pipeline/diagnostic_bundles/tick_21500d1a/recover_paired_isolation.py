"""Resume only the unrun condition in a fresh process; preserve reference/failure."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shlex
import subprocess
from audit_terminal import guard, save, remote, ROOT, OUT, tick

owner = guard()
assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 1400
attempt = tick.load(OUT/"paired_execution_attempt.json")
assert attempt["returncode"] == 1 and "already registered" in attempt["combined_output"]
markers = [line for line in attempt["combined_output"].splitlines() if line.startswith("PAIRED_NATIVE_CONDITION=")]
assert len(markers) == 1
reference = json.loads(markers[0].split("=",1)[1])
assert reference["expressions"] == 9508 and reference["unique_scenes"] == 141
stage = "/data/songcl/Project/Cluster_project/pipeline/evidence_producer_21500d1a"
response = subprocess.run(["scp","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10",
                           "songcl@192.168.1.115:"+stage+"/reference_m95_epoch16.json",str(OUT/"reference_m95_epoch16.json")],
                          capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=45)
assert response.returncode == 0, response.stderr
assert tick.digest(OUT/"reference_m95_epoch16.json") == reference["sha256"]
source = (OUT/"paired_validation.py").read_text(encoding="utf-8")
changes = [
    ('STAGE / "paired_manifest.json"','STAGE / "paired_manifest_isolated.json"'),
    ('for condition in ("reference_m95_epoch16", "candidate_hds_epoch19"):', 'for condition in ("candidate_hds_epoch19",):'),
    ('    val_config = None\n','    val_config = copy.deepcopy(gorilla.Config.fromfile(str(ROOT / manifest["conditions"]["reference_m95_epoch16"]["config"])).data.val)\n    val_config.data_root = "/home/songcl/data/data/"\n'),
    ('STAGE / "paired_capture_index.json"','STAGE / "paired_candidate_capture_index.json"')]
for old,new in changes:
    assert source.count(old) == 1,old
    source = source.replace(old,new)
runner = OUT/"paired_validation_isolated.py"
runner.write_text(source,encoding="utf-8",newline="\n")
compile(source,runner.name,"exec")
manifest = tick.load(OUT/"paired_manifest.json")
manifest["producer_hashes"] = {name:tick.digest(OUT/name) for name in ("paired_validation.py",runner.name,"aligned_evidence.py")}
save("paired_manifest_isolated.json",manifest)
save("paired_registry_failure_review.json",{
    "observed_at":datetime.now(timezone.utc).isoformat(),
    "failure":"Fresh import of second model in SAME process collides on gorilla losses registry Criterion; no candidate forward executed.",
    "first_condition_preserved":reference,"failed_execution_artifact":"paired_execution_attempt.json",
    "repair":"Fresh process for unrun candidate only. Do not clear/force shared registry or change model source.",
    "transport_only_changes":[{"old":old,"new":new} for old,new in changes],
    "original_script_sha256":tick.digest(OUT/"paired_validation.py"),"isolated_script_sha256":tick.digest(runner),
    "weights_config_seed_data_controls_unchanged":True,"model_revision":False})
for filename in (runner.name,"paired_manifest_isolated.json"):
    response = subprocess.run(["scp","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10",
                               str(OUT/filename),"songcl@192.168.1.115:"+stage+"/"],capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=45)
    assert response.returncode == 0,response.stderr
guard()
command = "source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh; conda activate project_cluster; " + shlex.join([
    "env","PYTHONDONTWRITEBYTECODE=1","python","-B",stage+"/"+runner.name])
args = ["ssh","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10",
        "-o","ServerAliveInterval=10","-o","ServerAliveCountMax=3","songcl@192.168.1.115",shlex.join(["bash","-lc",command])]
lines=[]
with subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",bufsize=1) as process:
    for line in process.stdout:
        lines.append(line)
        if line.startswith("PAIRED_NATIVE_"):print(line.rstrip(),flush=True)
    rc=process.wait(timeout=20)
save("paired_isolated_execution_attempt.json",{"observed_at":datetime.now(timezone.utc).isoformat(),"returncode":rc,"combined_output":"".join(lines)})
assert rc==0,"".join(lines)[-4000:]
for filename in ("candidate_hds_epoch19.json","paired_candidate_capture_index.json"):
    response=subprocess.run(["scp","-o","BatchMode=yes","-o","StrictHostKeyChecking=yes","-o","ConnectTimeout=10",
                             "songcl@192.168.1.115:"+stage+"/"+filename,str(OUT/filename)],capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=60)
    assert response.returncode==0,response.stderr
candidate_index=tick.load(OUT/"paired_candidate_capture_index.json")
assert candidate_index["passed"] and set(candidate_index["conditions"])=={"candidate_hds_epoch19"}
candidate=candidate_index["conditions"]["candidate_hds_epoch19"]
assert tick.digest(OUT/"candidate_hds_epoch19.json")==candidate["sha256"]
save("paired_capture_index.json",{"passed":True,"observed_at":datetime.now(timezone.utc).isoformat(),
    "conditions":{"reference_m95_epoch16":reference,"candidate_hds_epoch19":candidate},
    "execution_processes":"One fresh process per condition; original duplicate-registry failure preserved.",
    "optimizer_steps":0,"reference_and_candidate_files_hash_verified":True,
    "scope":manifest["scope"]})
print("PAIRED_CAPTURE_PULLED_AND_HASH_VERIFIED",flush=True)
