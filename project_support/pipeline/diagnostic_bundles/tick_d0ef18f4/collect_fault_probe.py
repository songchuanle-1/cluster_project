"""Read capped original probe artifacts; never launch or replay a process."""
from pathlib import Path
import base64
import hashlib
import json
import shlex
import subprocess

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
binding = json.loads((HERE / "nde_execution/execution_binding.json").read_bytes())
execution = json.loads((HERE / "nde_crash_probe_execution/crash_probe_execution.json").read_bytes())
assert execution["certainty"] == "terminal"
code = r'''
from pathlib import Path
from datetime import datetime,timezone
import base64,hashlib,json,socket
assert socket.gethostname()=="dl04-MS-7E06"
stage=Path(STAGE)
assert hashlib.sha256((stage/"native_manifest.json").read_bytes()).hexdigest()==MANIFEST_SHA
output={"observed_at":datetime.now(timezone.utc).isoformat(),"stage":str(stage),"files":{}}
for name in ("crash_probe_started.json","crash_probe_completed.json",
             "crash_probe_stdout.log","crash_probe_stderr.log",
             "fault_localization_markers.jsonl","resources_candidate_result.json"):
    path=stage/name
    if not path.is_file():
        output["files"][name]={"exists":False}
        continue
    size=path.stat().st_size
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk=stream.read(65536)
            if not chunk:break
            digest.update(chunk)
    with path.open("rb") as stream:
        if size>524288:stream.seek(-524288,2)
        data=stream.read(524288)
    output["files"][name]={"exists":True,"size":size,"sha256":digest.hexdigest(),
        "tail_only":size>524288,"captured_bytes":len(data),
        "base64":base64.b64encode(data).decode()}
print(json.dumps(output))
'''
code = code.replace("STAGE", repr(binding["stage"])).replace("MANIFEST_SHA", repr(binding["native_manifest_sha256"]))
command = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
           "-o", "ConnectTimeout=8", "songcl@192.168.1.115",
           "/home/songcl/.conda/envs/project_cluster/bin/python -B -c " + shlex.quote(code)]
process = subprocess.run(command, capture_output=True, timeout=40)
assert process.returncode == 0, process.stderr.decode(errors="replace")[-600:]
result = json.loads(process.stdout)
destination = HERE / "fault_probe_evidence"
destination.mkdir()
for name, item in result["files"].items():
    if not item["exists"]:
        continue
    data = base64.b64decode(item.pop("base64"))
    path = destination / (name + (".tail" if item["tail_only"] else ""))
    with path.open("xb") as stream:
        stream.write(data)
    if not item["tail_only"]:
        assert hashlib.sha256(data).hexdigest() == item["sha256"]
    item["local_evidence"] = {"path": path.relative_to(ROOT).as_posix(),
                              "sha256": hashlib.sha256(data).hexdigest()}
result.update(owner_token=binding["owner"]["token"], source_commit=binding["code_commit"],
              runtime_code_commit=binding["runtime_code_commit"], collection_read_only=True,
              native_manifest_sha256=binding["native_manifest_sha256"])
with (destination / "collection.json").open("x", encoding="utf-8") as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
markers = []
marker_path = destination / "fault_localization_markers.jsonl"
if marker_path.exists():
    for line in marker_path.read_bytes().splitlines():
        try:
            markers.append(json.loads(line))
        except ValueError:
            pass
stderr_path = destination / "crash_probe_stderr.log"
stderr = stderr_path.read_bytes() if stderr_path.exists() else b""
print(json.dumps({"status": "ORIGINAL_PROBE_ARTIFACTS_SAVED", "files":
    {name: {"exists": item["exists"], "size": item.get("size"),
            "tail_only": item.get("tail_only")} for name, item in result["files"].items()},
    "marker_count": len(markers), "last_markers": markers[-3:],
    "stderr_tail": stderr[-1600:].decode("utf-8", errors="replace")}, ensure_ascii=False))
