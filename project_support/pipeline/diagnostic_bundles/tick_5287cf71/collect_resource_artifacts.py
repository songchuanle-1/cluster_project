"""Collect capped original resource files over read-only, pinned SSH."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import base64
import hashlib
import json
import subprocess

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TOKEN = "5287cf71a0424b018f3d0c77db4950ff"


def read(path):
    return json.loads(path.read_bytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=["champion", "candidate"])
    args = parser.parse_args()
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    binding = read(HERE / "nde_execution/execution_binding.json")
    execution = read(HERE / "nde_execution" / ("resources_" + args.target + "_execution.json"))
    assert binding["owner"]["token"] == TOKEN
    assert execution["certainty"] == "terminal"
    prefix = "resources_" + args.target
    names = [prefix + suffix for suffix in (
        "_request.json", "_started.json", "_completed.json",
        "_stdout.log", "_stderr.log", "_result.json")]
    code = r'''
from pathlib import Path
from datetime import datetime,timezone
import base64,hashlib,json,socket
assert socket.gethostname()=="dl04-MS-7E06"
stage=Path(STAGE)
assert stage==Path("/data/songcl/Project/Cluster_project/pipeline/nde_5287cf71_gpu0")
assert hashlib.sha256((stage/"native_manifest.json").read_bytes()).hexdigest()==MANIFEST_SHA
output={"observed_at":datetime.now(timezone.utc).isoformat(),"stage":str(stage),"files":{}}
for name in NAMES:
    assert Path(name).name==name
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
    code = code.replace("STAGE", repr(binding["stage"])).replace(
        "MANIFEST_SHA", repr(binding["native_manifest_sha256"])).replace("NAMES", repr(names))
    process = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
         "-o", "ConnectTimeout=8", "songcl@192.168.1.115", "python3 -B -"],
        input=code.encode(), capture_output=True, timeout=40)
    assert process.returncode == 0, process.stderr[-600:].decode(errors="replace")
    result = json.loads(process.stdout)
    destination = HERE / ("resource_evidence_" + args.target)
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
        item["local_evidence"] = {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(data).hexdigest()}
    for suffix, key in (("_stdout.log", "stdout_sha256"),
                        ("_stderr.log", "stderr_sha256"),
                        ("_result.json", "result_sha256")):
        item = result["files"][prefix + suffix]
        if execution.get(key) is not None:
            assert item["exists"] and item["sha256"] == execution[key]
    result.update(owner_token=TOKEN, collection_read_only=True,
                  source_commit=binding["code_commit"],
                  runtime_code_commit=binding["runtime_code_commit"],
                  native_manifest_sha256=binding["native_manifest_sha256"])
    with (destination / "collection.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps({"status": "ORIGINAL_RESOURCE_ARTIFACTS_SAVED", "target": args.target,
        "files": {name: {key: item.get(key) for key in ("exists", "size", "tail_only")}
                  for name, item in result["files"].items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
