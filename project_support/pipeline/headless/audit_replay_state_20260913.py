"""Read-only checkpoint replay prerequisites and current trainer snapshot."""
from datetime import datetime
import json
from pathlib import Path
import re
import shlex
import yaml

from close_m185_20260912 import parse_log
from verify_control_archives_20260912 import remote, sha

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
OUT = P / "reports/replay_state_20260913-2010"


def main():
    OUT.mkdir(exist_ok=False)
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    srv = servers["server-4"]
    prior = json.loads((P / "reports/source_head_interference_20260913-1938/live.json").read_text())
    previous = next(x for x in prior["live"] if x["id"].startswith("M193"))
    processes = remote(srv, "ps -eo pid,args").decode()
    text = remote(srv, "cat " + shlex.quote(previous["remote_log"])).decode()
    log = OUT / "M193_live.log"
    log.write_text(text, encoding="utf-8")
    metrics = parse_log(text)
    best = max(metrics, key=lambda x: x["miou"])
    live = dict(id=previous["id"], config=previous["config"], remote_log=previous["remote_log"],
                best=best, completed=len(metrics), epoch=int(re.findall(r"Epoch \[(\d+)/50\]", text)[-1]),
                no_improve=metrics[-1]["epoch"]-best["epoch"],
                early_stop="Early stopping at epoch" in text,
                trainer_present=any(Path(previous["config"]).stem in line and "tools/train.py" in line
                                    for line in processes.splitlines()), log_sha256=sha(log))
    gpu = {}
    for name in ("server-4", "server-6"):
        ids = ",".join(map(str, servers[name]["allowed_gpus"]))
        gpu[name] = remote(servers[name], f"nvidia-smi -i {ids} --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits").decode().strip()
    checkpoint = srv["work_dir"] + "/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/20260815_101011/best.pth"
    worker = r'''
import hashlib, inspect, json, os
from pathlib import Path
import torch
import gorilla
torch.set_num_threads(1)
p = Path(CHECKPOINT)
def digest():
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""): h.update(block)
    return h.hexdigest()
before = digest()
assert before == "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
c = torch.load(p, map_location="cpu", weights_only=False)
o = c.get("optimizer", {})
states = o.get("state", {})
steps = [float(s["step"]) for s in states.values() if "step" in s]
result = dict(checkpoint=str(p), sha256=before, keys=list(c),
    meta=c.get("meta"), optimizer_keys=list(o), optimizer_state_count=len(states),
    optimizer_state_fields=sorted({k for s in states.values() for k in s}),
    optimizer_steps_min=min(steps) if steps else None,
    optimizer_steps_max=max(steps) if steps else None,
    param_groups=[{k:v for k,v in g.items() if k != "params"} for g in o.get("param_groups", [])],
    scheduler=c.get("lr_scheduler", c.get("scheduler")),
    save_source=inspect.getsource(gorilla.save_checkpoint),
    load_source=inspect.getsource(gorilla.load_checkpoint),
    cuda_initialized=torch.cuda.is_initialized(),
    run_files=sorted(x.name for x in p.parent.iterdir() if x.is_file()))
assert digest() == before
print(json.dumps(result, default=str))
'''.replace("CHECKPOINT", repr(checkpoint))
    command = ("source " + shlex.quote(srv["conda_source"]) + " && conda activate " +
               shlex.quote(srv["conda_env"]) + " && CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 python - <<'PY'\n" +
               worker + "\nPY")
    output = remote(srv, "bash -lc " + shlex.quote(command)).decode()
    checkpoint_state = json.loads(output.strip().splitlines()[-1])
    train = ROOT / "Cluster/tools/train.py"
    result = dict(at=datetime.now().isoformat(), live=live, gpu=gpu,
                  local_train_sha256=sha(train), checkpoint=checkpoint_state)
    (OUT / "audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
