"""Default NOP. Root-only one-shot transport for frozen NSD collect/render."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import base64
import hashlib
import json
import os
import shlex
import subprocess
import sys
import yaml

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TICK = HERE.parent
PACKET = TICK / "nsd_path_production_prepare"
PRODUCER = "/data/songcl/Project/Cluster_project/pipeline/runtime/nsd_path_prepare_f74f3603"
PRODUCTION = "/data/songcl/Project/Cluster_project/pipeline/runtime/nsd_path_prod_f74f3603"
TOKEN = "f74f3603193a426097a8dc288fd05fde"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
KEYS = ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")
FILES = ("production_controller.py", "lock_core.py", "entry_factory.py")
FROZEN_SHA = "e7c6a8c55730dfdcf1cb5d3fd35f041f2ebbc445c76a0bee97b01691bfa2549d"
REVIEW_SHA = None
DRAFT_EXECUTION_DISABLED = True
EXPECTED_OWNER = {'token': 'f74f3603193a426097a8dc288fd05fde', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-11-07T03:08:55.256706+00:00', 'deadline_at': '2026-11-07T04:08:55.256706+00:00', 'context_sha256': '936753f928fb1a7c6400844ae2157b5379e3df7c2b4c510b6ddc8ecec3b361d0', 'pending_sha256': '94021c1be1944131acb86d0901f32b91ab8a844a7783af73062946ebf3b966c4'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save(path, value):
    with Path(path).open("x", encoding="utf8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def guard():
    assert not DRAFT_EXECUTION_DISABLED and isinstance(REVIEW_SHA, str), "Disabled prospective transport; fresh independent review/root activation required"
    assert HERE == ROOT / "pipeline/diagnostic_bundles/tick_f74f3603/nsd_path_production_transport"
    assert sys.dont_write_bytecode and os.environ.get("CODEX_THREAD_ID") == THREAD
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == THREAD
    assert {key: owner[key] for key in KEYS} == EXPECTED_OWNER
    assert (datetime.fromisoformat(owner["deadline_at"]) - datetime.now(timezone.utc)).total_seconds() > 180
    mode = read(ROOT / "pipeline/execution_mode.json")
    assert mode["mode"] == "foreground" and mode["target_thread_id"] == THREAD
    for name, key in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
        assert sha(ROOT / "pipeline/headless" / name) == owner[key]
    assert sha(ROOT / "SERVERS.yaml") == "1f1ba94e90c6f44e2e9cb0e6f1e746568e38cc1e92f398ee49efc5e8c40232bf"
    server = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf8"))["servers"]["server-4"]
    assert server["host"] == "192.168.1.115" and server["user"] == "songcl" and server["expected_hostname"] == "dl04-MS-7E06"
    assert server["allowed_gpus"] == [0] and server["expected_gpu_uuids"]["0"] == "GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"
    assert server["max_tasks_per_gpu"] == 1 and server["task_memory_mb"] == 20000 and server["allow_external_overlay"] is True
    assert server["remote_code_root"] == "/data/songcl/Project/Cluster_project/Cluster_psc_20261106"
    assert sha(ROOT / "pipeline/goal.json") == "0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85"
    assert sha(PACKET / "FROZEN.json") == FROZEN_SHA
    assert all(sha(PACKET / name) == digest for name, digest in read(PACKET / "FROZEN.json")["files"].items())
    review = TICK / "nsd_path_production_independent_review.json"
    assert sha(review) == REVIEW_SHA and read(review)["passed"] is True
    return {key: owner[key] for key in KEYS}


REMOTE = r'''
from pathlib import Path
from datetime import datetime,timezone
import base64,hashlib,json,os,socket,stat,subprocess,sys
assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001
packet=json.load(sys.stdin)
stage=Path('/data/songcl/Project/Cluster_project/pipeline/runtime/nsd_path_prepare_f74f3603')
assert packet['stage']==str(stage)
owner=packet['owner']
assert owner=={'token': 'f74f3603193a426097a8dc288fd05fde', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-11-07T03:08:55.256706+00:00', 'deadline_at': '2026-11-07T04:08:55.256706+00:00', 'context_sha256': '936753f928fb1a7c6400844ae2157b5379e3df7c2b4c510b6ddc8ecec3b361d0', 'pending_sha256': '94021c1be1944131acb86d0901f32b91ab8a844a7783af73062946ebf3b966c4'}
assert owner['token']=='f74f3603193a426097a8dc288fd05fde' and owner['thread_id']=='01a159c5-29ab-7a22-ba7f-e79174757253'
assert owner['deadline_at']=='2026-11-07T04:08:55.256706+00:00'
assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
assert packet['training_launch_authorized'] is False
action=packet['action'];assert action in ('stage','collect','render')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def regular(path):
 s=os.lstat(path);assert stat.S_ISREG(s.st_mode) and s.st_uid==1001 and s.st_nlink==1
 assert not stat.S_ISLNK(s.st_mode)
if action=='stage':
 assert not stage.exists(),'Existing stage: preserve and reconcile, never replay'
 parent=os.lstat(stage.parent);assert stat.S_ISDIR(parent.st_mode) and parent.st_uid==1001
 assert set(packet['files'])=={'production_controller.py','lock_core.py','entry_factory.py'}
 for name,item in packet['files'].items():
  raw=base64.b64decode(item['bytes_base64'],validate=True)
  assert hashlib.sha256(raw).hexdigest()==item['sha256'];compile(raw,name,'exec')
 stage.mkdir(mode=0o700)
 for name,item in packet['files'].items():
  with (stage/name).open('xb') as stream:stream.write(base64.b64decode(item['bytes_base64'],validate=True))
  (stage/name).chmod(0o600);regular(stage/name);assert sha(stage/name)==item['sha256']
 print(json.dumps({'certainty':'terminal','action':'stage','owner':owner,'stage':str(stage),
  'files':{name:sha(stage/name) for name in packet['files']},'training_launch_or_GPU_use':False}));sys.exit(0)
assert stage.is_dir() and stage.resolve()==stage
s=os.lstat(stage);assert s.st_uid==1001 and stat.S_IMODE(s.st_mode)==0o700
for name,expected in packet['files'].items():regular(stage/name);assert sha(stage/name)==expected
request_raw=base64.b64decode(packet['request_bytes_base64'],validate=True)
assert hashlib.sha256(request_raw).hexdigest()==packet['request_sha256']
request=json.loads(request_raw);assert request['owner']==owner and request['action']==action
assert request['execution_authorized'] is True and request['training_launch_authorized'] is False
request_path=stage/(action+'_request.json')
assert not request_path.exists(),'Existing request: preserve and reconcile, never replay'
if action=='render':
 regular(stage/'actual_observation.json')
 assert sha(stage/'actual_observation.json')==request['actual_observation_sha256']
 assert not Path('/data/songcl/Project/Cluster_project/pipeline/runtime/nsd_path_prod_f74f3603').exists()
else:assert not (stage/'actual_observation.json').exists()
with request_path.open('xb') as stream:stream.write(request_raw)
request_path.chmod(0o600)
command=['/usr/bin/python3','-I','-B',str(stage/'production_controller.py'),action,'--request',str(request_path),'--request-sha256',packet['request_sha256']]
environment=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=environment)
try:
 stdout,stderr=process.communicate(timeout=240)
except subprocess.TimeoutExpired:
 print(json.dumps({'certainty':'uncertain','pid':process.pid,'action':action,'owner':owner,'stage':str(stage),
  'reason':'CPU controller timeout; no signal or replay','training_launch_or_GPU_use':False}));sys.exit(0)
name='actual_observation.json' if action=='collect' else 'production_render_result.json'
result_path=stage/name;result=None;result_sha=None;result_bytes=None
if result_path.exists():
 regular(result_path);result_sha=sha(result_path);raw=result_path.read_bytes()
 result=json.loads(raw);result_bytes=base64.b64encode(raw).decode()
print(json.dumps({'certainty':'terminal','returncode':process.returncode,'pid':process.pid,'action':action,
 'owner':owner,'stage':str(stage),'command':command,'stdout':stdout,'stderr':stderr,
 'result':result,'remote_result_sha256':result_sha,'remote_result_bytes_base64':result_bytes,'training_launch_or_GPU_use':False}))
'''


def embedded(path):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path),
            "bytes_base64": base64.b64encode(path.read_bytes()).decode()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-root", action="store_true")
    parser.add_argument("--action", choices=("stage", "collect", "render"))
    parser.add_argument("--admission")
    parser.add_argument("--activation")
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({"status": "DEFAULT_NOP_NO_SSH_OR_MUTATION", "training_launch_authorized": False}))
        return
    assert args.action is not None
    owner = guard()
    intent = HERE / (args.action + "_intent.json")
    result_path = HERE / (args.action + "_actual.json")
    assert not intent.exists() and not result_path.exists(), "Existing attempt must reconcile; never replay"
    packet = {"action": args.action, "stage": PRODUCER, "owner": owner, "training_launch_authorized": False}
    hashes = {name: sha(PACKET / name) for name in FILES}
    if args.action == "stage":
        packet["files"] = {name: {"sha256": hashes[name], "bytes_base64":
                                  base64.b64encode((PACKET / name).read_bytes()).decode()} for name in FILES}
        request_ref = None
    else:
        assert (HERE / "stage_actual.json").is_file()
        staged = read(HERE / "stage_actual.json")
        assert staged["observation"]["certainty"] == "terminal" and staged["observation"]["files"] == hashes
        assert staged["owner"] == owner
        request = read(PACKET / (args.action + "_request.draft.json"))
        request.update(owner=owner, execution_authorized=True)
        if args.action == "render":
            assert args.admission and args.activation
            collected = read(HERE / "collect_actual.json")
            assert collected["owner"] == owner and collected["observation"]["returncode"] == 0
            assert collected["observation"]["certainty"] == "terminal"
            request["actual_observation_sha256"] = collected["observation"]["remote_result_sha256"]
            request["admission_receipt"] = embedded(args.admission)
            request["activation_receipt"] = embedded(args.activation)
            activation = read(args.activation)
            assert activation["decision"] == "ALLOW_PRODUCTION_PATH_RENDER" and activation["owner"] == owner
            assert activation["actual_observation_sha256"] == request["actual_observation_sha256"]
            assert activation["admission_receipt_sha256"] == request["admission_receipt"]["sha256"]
            assert activation["training_launch_authorized"] is False and not activation.get("draft_not_an_actual_receipt")
            admission = read(args.admission)
            assert admission["id"] == "M232-NSD" and admission["code_commit"] == "f6257de79148581334ee495e6e2d60ccb525457c"
            assert admission["config"] == "configs/Quard/ctf_hcg_csort_nsd/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nsd.yaml"
            assert admission["goal_sha256"] == "0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85"
            assert all(admission["gates"][name]["passed"] is True for name in ("native_backward", "resources", "independence", "constraints"))
        local_request = HERE / (args.action + "_request.json")
        assert not local_request.exists()
        save(local_request, request)
        packet.update(files=hashes, request_bytes_base64=base64.b64encode(local_request.read_bytes()).decode(),
                      request_sha256=sha(local_request))
        request_ref = {"path": local_request.relative_to(ROOT).as_posix(), "sha256": sha(local_request)}
    guard()
    save(intent, {"recorded_at": datetime.now(timezone.utc).isoformat(), "action": args.action,
                  "owner": owner, "request": request_ref, "source_FROZEN_sha256": FROZEN_SHA,
                  "controller_review_sha256": REVIEW_SHA, "no_replay": True})
    command = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=8",
               "songcl@192.168.1.115", "/usr/bin/python3 -I -B -c " + shlex.quote(REMOTE)]
    record = {"recorded_at": datetime.now(timezone.utc).isoformat(), "owner": owner, "action": args.action,
              "intent_sha256": sha(intent), "certainty": "uncertain", "training_launch_or_GPU_use": False}
    try:
        process = subprocess.run(command, input=json.dumps(packet), capture_output=True, text=True, encoding="utf8", timeout=270)
        record.update(ssh_returncode=process.returncode, stdout=process.stdout, stderr=process.stderr)
        if process.returncode == 0:
            record["observation"] = json.loads(process.stdout)
            assert record["observation"]["owner"] == owner and record["observation"]["stage"] == PRODUCER
            if args.action != "stage" and record["observation"].get("remote_result_bytes_base64"):
                raw = base64.b64decode(record["observation"]["remote_result_bytes_base64"], validate=True)
                assert hashlib.sha256(raw).hexdigest() == record["observation"]["remote_result_sha256"]
                assert json.loads(raw) == record["observation"]["result"]
            record["certainty"] = record["observation"]["certainty"]
    except Exception as error:
        record.update(error_type=type(error).__name__, error=str(error))
        save(result_path, record)
        raise
    save(result_path, record)
    assert record["certainty"] == "terminal" and record["ssh_returncode"] == 0, "Preserve uncertain attempt; no replay"
    if args.action != "stage":
        assert record["observation"]["returncode"] == 0 and record["observation"]["result"] is not None
    assert guard() == owner
    print(json.dumps({"action": args.action, "certainty": record["certainty"],
                      "path": str(result_path), "sha256": sha(result_path), "training_launch_or_GPU_use": False}))


if __name__ == "__main__":
    main()
