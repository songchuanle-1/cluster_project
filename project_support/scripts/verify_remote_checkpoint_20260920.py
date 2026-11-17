"""Hash the explicitly cited M95 checkpoint, without loading model weights."""
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
PATH = "/data3/songcl/Project/Cluster_project/pipeline/scm_admission_20260914/best.pth"
OUTPUT = ROOT / "pipeline/reports/remote_checkpoint_inventory_20260920-0215.json"
CODE = r'''
import datetime,hashlib,json,pathlib
p=pathlib.Path(PATH)
before=p.stat()
h=hashlib.sha256()
with p.open("rb") as f:
    for chunk in iter(lambda:f.read(1048576),b""):
        h.update(chunk)
after=p.stat()
print(json.dumps(dict(path=str(p),sha256=h.hexdigest(),bytes=after.st_size,
    observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    stable=(before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns))))
'''


def main():
    if OUTPUT.exists():
        raise ValueError("Checkpoint inventory exists")
    prior = json.loads((ROOT / "pipeline/reports/positive_membership_intervention_20260916.json").read_text())
    expected = prior["sources"][PATH]
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "songcl@100.64.3.28",
         "/data3/songcl/miniconda3/envs/project_cluster/bin/python -B -"],
        input=CODE.replace("PATH", repr(PATH), 1), text=True, capture_output=True,
        timeout=120, check=True)
    observed = json.loads(result.stdout)
    report = dict(observed=observed, expected_sha256=expected,
                  matches=observed["sha256"] == expected and observed["stable"],
                  source="pipeline/reports/positive_membership_intervention_20260916.json",
                  weights_loaded=False, gpu_allocated=False)
    with OUTPUT.open("x", encoding="ascii") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
