"""Current-lease source contract and read-only authorized-slot observations."""
import ast
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

os.environ.update(PROJECT_ROOT="D:/project", PYTHONDONTWRITEBYTECODE="1")
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick

ROOT = Path("D:/project/cluster_project")
OUT = Path(__file__).resolve().parent
TOKEN = "d7dee0a18225465284ff88f668cfc050"
BASE = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
NAME = BASE + "_hds_canon_r1"


def guard():
    owner = tick.load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    return owner


def save(name, value):
    guard()
    tick.save(OUT / name, value)


def methods(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name: node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name in ("predict", "predict_by_feat")}


guard()
assert tick.load(OUT / "cpu_controls.json")["passed"]
base = ROOT / "Cluster/framework/model/Quard_model" / BASE / "network.py"
candidate = ROOT / "Cluster/framework/model/Quard_model" / NAME / "network.py"
left, right = methods(base), methods(candidate)
assert set(left) == set(right) == {"predict", "predict_by_feat"}
for name in left:
    assert ast.dump(left[name], include_attributes=False) == ast.dump(right[name], include_attributes=False)
returned = [node for node in ast.walk(left["predict_by_feat"])
            if isinstance(node, ast.Return) and isinstance(node.value, ast.Call)]
fields = {item.arg for item in returned[-1].value.keywords}
assert {"scan_id", "object_ids", "ann_id", "piou", "pred_pmask", "gt_pmask"} <= fields
native = ROOT / "Cluster/tools/train.py"
dataset = ROOT / "Cluster/framework/dataset/scannetv2.py"
builder = ROOT / "Cluster/framework/dataset/__init__.py"
train_tree = ast.parse(native.read_text(encoding="utf-8"))
evaluation = next(node for node in train_tree.body if isinstance(node, ast.FunctionDef) and node.name == "eval")
assert any(isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "miou" for t in node.targets)
           and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute)
           and ast.unparse(node.value.func) == "pious.mean" for node in ast.walk(evaluation))
sources = {p.relative_to(ROOT / "Cluster").as_posix(): tick.digest(p)
           for p in (base, candidate, native, dataset, builder)}
save("source_contract.json", {
    "observed_at": datetime.now(timezone.utc).isoformat(), "passed": True,
    "sources": sources, "prediction_methods_ast_identical": True,
    "prediction_fields": sorted(fields),
    "native_aggregation": "torch.stack(pious, dim=0).cpu().numpy().mean(); float32",
    "scope": "ScanRefer task_type=res; nt_labels empty, so no Multi3DRefer metadata relabeling",
    "batch_contract": "predict_by_feat uses scan_ids[0]; inference batch_size=1; training batch2 unchanged",
    "missing_metadata": "Not fabricated; optional fields remain unmeasured",
    "line_references": {"predict": left["predict"].lineno,
                        "predict_by_feat": left["predict_by_feat"].lineno,
                        "native_eval": evaluation.lineno}})

program = r'''
import csv,datetime,fcntl,hashlib,json,pathlib,socket,subprocess,time
assert socket.gethostname()==HOSTNAME
root=pathlib.Path(ROOT_PATH)
def query(args):
    return subprocess.check_output(args,universal_newlines=True,timeout=15).strip()
def sample():
    row=query(['nvidia-smi','-i',str(GPU),'--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'])
    cells=[cell.strip() for cell in next(csv.reader([row]))]
    assert cells[:2]==[str(GPU),UUID]
    contexts=query(['nvidia-smi','-i',str(GPU),'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'])
    processes=[{'pid':int(c[0]),'used_mib':int(c[1])} for c in csv.reader(contexts.splitlines()) if c]
    locks={}
    for name in LOCKS:
        path=pathlib.Path(name)
        if not path.exists():
            locks[name]='absent (no deletion or acquisition)';continue
        with path.open('rb') as handle:
            try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:locks[name]='held by another owner'
            else:
                locks[name]='available; probe released immediately'
                fcntl.flock(handle,fcntl.LOCK_UN)
    progress=[]
    lock_fds=[]
    alive=None
    scalars=[]
    if LOG:
        import re
        proc=pathlib.Path('/proc')/str(PID)
        alive=proc.exists() and b'tools/train.py' in proc.joinpath('cmdline').read_bytes().split(b'\0')
        with pathlib.Path(LOG).open('rb') as h:
            h.seek(max(0,pathlib.Path(LOG).stat().st_size-131072))
            text=h.read().decode('utf-8',errors='replace')
        progress=re.findall(r'(Train|Val)\[(\d+)/(\d+)\]:[^\r\n]*?\|\s*(\d+)/(\d+)',text)[-3:]
        if proc.exists():
            for fd in (proc/'fd').iterdir():
                try:target=str(fd.resolve(strict=True))
                except OSError:continue
                if target in LOCKS:lock_fds.append(target)
                if target.startswith(WORK+'/') and target.endswith('.log'):
                    values=pathlib.Path(target).read_text(errors='replace')
                    scalars.append({'path':target,'miou':[float(x) for x in re.findall(r'(?<![A-Za-z])mIoU\s*:\s*([0-9.eE+-]+)',values)],
                                    'expressions':[int(x) for x in re.findall(r'Evaluate referring segmentation:\s*(\d+)',values)]})
        markers=[word for word in ('Traceback','CUDA out of memory','TypeError:','RuntimeError:') if word in text]
    else:markers=[]
    return {'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'gpu':{'index':GPU,'uuid':UUID,'total_mib':int(cells[2]),'used_mib':int(cells[3]),'free_mib':int(cells[4]),'util_percent':int(cells[5])},
        'compute_processes':processes,'lock_observation':locks,'training_alive':alive,
        'native_steps':progress,'training_lock_fds':sorted(set(lock_fds)),
        'current_scalar_logs':scalars,'tail_crash_markers':markers}
first=sample()
if LOG:time.sleep(7)
second=sample() if LOG else first
paths=[root/name for name in FILES]
hashes={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
print(json.dumps({'hostname':socket.gethostname(),'samples':[first,second] if LOG else [first],
    'source_hashes':hashes,'source_hashes_match':hashes==FILES,
    'no_gpu_computation':True,'no_process_signal':True,'no_lock_deletion':True}))
'''

import yaml
servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
experiment = tick.load(ROOT / "pipeline/experiments/M202-HDS.json")
frozen = tick.load(ROOT / "pipeline/diagnostic_bundles/m202_recovery_fded20f5/failure_snapshot.json")
data = {}
for server, gpu in (("server-3", 1), ("server-4", 0)):
    config = servers[server]
    assert config["allowed_gpus"] == [gpu] and config["dispatch_enabled"]
    locks = ["/tmp/cluster_project_gpu1_" + x + ".lock" for x in
             ("m201_migration", "exclusive", "parameter_transport")] if gpu == 1 else [
             "/tmp/cluster_project_gpu0_" + x + ".lock" for x in ("training", "diagnostic", "exclusive")]
    files = {p.relative_to(ROOT / "Cluster").as_posix(): tick.digest(p)
             for p in (base, dataset, builder)} if gpu == 1 else frozen["source_hashes"]
    constants = {"HOSTNAME": config["expected_hostname"], "ROOT_PATH": config["remote_code_root"],
                 "GPU": gpu, "UUID": config["expected_gpu_uuid"], "LOCKS": locks, "FILES": files,
                 "LOG": experiment["log"] if gpu == 0 else None,
                 "PID": experiment["pid"] if gpu == 0 else None, "WORK": config["work_dir"]}
    payload = "\n".join(name + "=" + repr(value) for name, value in constants.items()) + "\n" + program
    command = shlex.join(["env", "PYTHONDONTWRITEBYTECODE=1", "/usr/bin/python3", "-B", "-c", payload])
    response = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
                               "-o", "ConnectTimeout=10", config["user"] + "@" + config["host"], command],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
    assert response.returncode == 0, response.stderr
    data[server] = json.loads(response.stdout)
save("resources_d7dee0a1.json", data)
print(json.dumps({server: {"sample": value["samples"][-1], "source_hashes_match": value["source_hashes_match"]}
                  for server, value in data.items()}, indent=2))
