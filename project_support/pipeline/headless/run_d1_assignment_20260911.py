"""Freeze provenance, isolate uploads, and run a bounded CPU assignment audit."""
from datetime import datetime
import json
from pathlib import Path
import subprocess
import yaml
from d1_candidate_bank_20260911 import sha, key, MANIFEST_SHA

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
OUT = P / "reports/d1_assignment_20260911-1113"
REMOTE = "/tmp/cluster_d1_assignment_20260911_1113"


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, timeout=60)
    if r.returncode:
        raise RuntimeError((r.stdout + r.stderr).decode(errors="replace"))
    return r.stdout


def main():
    assert not OUT.exists()
    goal = json.loads((P / "goal.json").read_text(encoding="utf-8"))
    review = (P / "reviews/motivation_review_20260911-111300.md").read_text(encoding="utf-8")
    quoted = json.loads(review.split("```json\n")[1].split("```")[0])
    assert quoted == goal
    OUT.mkdir()
    protocol = dict(created=datetime.now().isoformat(), manifest_sha256=MANIFEST_SHA,
                    source_hashes={}, summary_hashes={}, models={}, ids=[],
                    goal_sha256=sha(P / "goal.json"), constraints=goal["constraints"],
                    banned=goal["banned"], evaluation_replay_only=True,
                    design_sha256=sha(P / "designs/exp_design_20260911-111300.md"))
    protocol["source_hashes"]["framework/dataset/scannetv2.py"] = sha(ROOT / "Cluster/framework/dataset/scannetv2.py")
    for name in ("baseline", "m95"):
        a = json.loads((P / f"reports/d0_checkpoint_identity_20260911-0413/d0_{name}_identity_20260911.json").read_text())
        package = a["explicit_module"].replace(".", "/")
        for filename in ("loss.py", "network.py"):
            rel = f"{package}/{filename}"
            assert sha(ROOT / "Cluster" / rel) == a["package_sha256"][filename]
            protocol["source_hashes"][rel] = sha(ROOT / "Cluster" / rel)
        config = a["saved_config"]["model"]["criterion"]
        protocol["models"][name] = dict(loss_path=package + "/loss.py",
                                        eos_coef=config.get("eos_coef", .1),
                                        loss_weight=config["loss_weight"],
                                        checkpoint_sha256=a["checkpoint_sha256"])
        summary = P / f"reports/d1_expansion_20260911-0715/{name}/summary.json"
        protocol["summary_hashes"][name] = sha(summary)
        ids = sorted(key(r) for r in json.loads(summary.read_text())["rows"])
        if protocol["ids"]:
            assert ids == protocol["ids"]
        protocol["ids"] = ids
    (OUT / "protocol.json").write_text(json.dumps(protocol, indent=2, ensure_ascii=False), encoding="utf-8")
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    evidence = dict(started=datetime.now().isoformat(), deployments={})
    worker = P / "headless/d1_assignment_20260911.py"
    for name in ("server-4", "server-6"):
        s = servers[name]
        host = f"{s['user']}@{s['host']}"
        ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host]
        before = run(ssh + [f"git -C {s['remote_code_root']} diff --binary HEAD"])
        run(ssh + [f"mkdir {REMOTE}"])
        evidence["deployments"][name] = {}
        for file in (worker, OUT / "protocol.json",
                     P / "reviews/motivation_review_20260911-111300.md",
                     P / "designs/exp_design_20260911-111300.md"):
            run(["scp", "-q", str(file), f"{host}:{REMOTE}/{file.name}"])
            digest = run(ssh + [f"sha256sum {REMOTE}/{file.name}"]).decode().split()[0]
            assert digest == sha(file)
            evidence["deployments"][name][file.name] = digest
        assert before == run(ssh + [f"git -C {s['remote_code_root']} diff --binary HEAD"])
    s = servers["server-4"]
    host = f"{s['user']}@{s['host']}"
    command = (f"set -e\nsource {s['conda_source']}\nconda activate {s['conda_env']}\n"
               "export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1\n"
               f"timeout 600s python -u {REMOTE}/{worker.name} --protocol {REMOTE}/protocol.json "
               f"--code-root {s['remote_code_root']} --data-root {s['data_root']} "
               f"--banks /tmp/cluster_d1_expansion_20260911_0715 --out {REMOTE}/result\n")
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", host, "bash -s"],
                       input=command.encode(), capture_output=True, timeout=640)
    (OUT / "worker.log").write_bytes(r.stdout + r.stderr)
    evidence.update(returncode=r.returncode, finished=datetime.now().isoformat())
    (OUT / "execution.json").write_text(json.dumps(evidence, indent=2))
    print((r.stdout + r.stderr).decode(errors="replace")[-5000:])
    r.check_returncode()
    run(["scp", "-q", f"{host}:{REMOTE}/result/assignment.json", str(OUT)])
    assert sha(OUT / "assignment.json") == run(["ssh", host, f"sha256sum {REMOTE}/result/assignment.json"]).decode().split()[0]
    print("DOWNLOADED", sha(OUT / "assignment.json"))


if __name__ == "__main__":
    main()
