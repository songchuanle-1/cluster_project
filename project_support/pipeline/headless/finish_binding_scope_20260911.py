"""Verify and synchronize the completed bounded audit; preserve active deployment."""
from datetime import datetime
import json
import subprocess
from pathlib import Path
import yaml
from audit_binding_scope_20260911 import P, ROOT, OUT, READINGS, sha, tests
from close_tick_20260911_0707 import EXPECTED, table


def run(args):
    return subprocess.run(args, check=True, capture_output=True, timeout=60).stdout


def main():
    assert not (OUT / "verification.json").exists()
    audit = json.loads((OUT / "scope_audit.json").read_text(encoding="utf-8"))
    protocol = json.loads((OUT / "protocol.json").read_text(encoding="utf-8"))
    formal = json.loads((OUT / "formal_tests.json").read_text(encoding="utf-8"))
    assert formal["tests"] == tests() and len(formal["tests"]) == 13
    assert len(audit["rows"]) == 21
    for row in audit["rows"]:
        assert all(s in row["description"] for s in row["spans"])
        assert row["physical_relation_truth"] == row["cause"] == "unknown"
    counts = {}
    for role in ("error", "control"):
        rs = [r for r in audit["rows"] if r["role"] == role]
        counts[role] = dict(n=len(rs), confirmed=sum(r["same_pair_shared_witness_confirmed"] for r in rs),
                            rows_with_empty_exact_domain=sum(bool(r["no_exact_lexical_match"]) for r in rs))
    rendered = "# Fixed Description Scope Notes\n\n"
    rendered += protocol["scope"] + "\n\n" + protocol["rules"] + "\n\n"
    for role in ("error", "control"):
        rendered += "## " + role.title() + "s\n\n"
        for r in [r for r in audit["rows"] if r["role"] == role]:
            rendered += f"### {r['scene_id']}/{r['object_id']}/{r['ann_id']}\n"
            rendered += r["description"] + "\n\n"
            rendered += f"Scope: {r['scope']}. {r['note']}\n\n"
            rendered += table(["Mention", "Exact-label non-target object candidates"],
                              [(k, v or "missing_exact_label_match") for k, v in r["anchor_mentions"].items()]) + "\n\n"
            rendered += "Geometry truth and cause: unknown. Narrow shared-pair eligibility: not confirmed.\n\n"
    (OUT / "case_scope.md").write_text(rendered, encoding="utf-8")
    sources = json.loads((OUT / "sources.json").read_text(encoding="utf-8"))
    assert all(sha(OUT / (s["name"] + ".html")) == s["sha256"] for s in sources)
    assert {k: sha(P / k) for k in EXPECTED} == EXPECTED
    inv = json.loads((P / "reports/research_inventory_20260910-1324.json").read_text(encoding="utf-8"))
    assert all(sha(ROOT / r["path"]) == r["sha256"] for r in inv["analyses"])
    assert not run(["git", "-C", str(ROOT / "Cluster"), "status", "--porcelain"])
    deployment = {}
    servers = yaml.safe_load((ROOT / "SERVERS.yaml").read_text(encoding="utf-8"))["servers"]
    remote = "/tmp/cluster_binding_scope_20260911_1012"
    files = [P / "headless/audit_binding_scope_20260911.py",
             OUT / "protocol.json", OUT / "scope_audit.json", OUT / "formal_tests.json",
             OUT / "mechanism_audit.md", OUT / "case_scope.md", OUT / "sources.json"]
    for name in ("server-4", "server-6"):
        s = servers[name]
        host = f"{s['user']}@{s['host']}"
        ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host]
        before = run(ssh + [f"git -C {s['remote_code_root']} diff --binary HEAD"])
        run(ssh + [f"mkdir {remote}"])
        deployment[name] = {}
        for path in files:
            run(["scp", "-q", str(path), f"{host}:{remote}/{path.name}"])
            digest = run(ssh + [f"sha256sum {remote}/{path.name}"]).decode().split()[0]
            assert digest == sha(path)
            deployment[name][path.name] = digest
        assert before == run(ssh + [f"git -C {s['remote_code_root']} diff --binary HEAD"])
    verification = dict(status="passed", verified_at=datetime.now().isoformat(), counts=counts,
                        formal_tests=13, historical_analyses_verified=len(inv["analyses"]),
                        state_hashes=EXPECTED, deployments=deployment,
                        mechanism_admitted=False, new_training=0, crashes=0,
                        scope_sha256=sha(OUT / "scope_audit.json"), formal_sha256=sha(OUT / "formal_tests.json"))
    (OUT / "verification.json").write_text(json.dumps(verification, indent=2), encoding="utf-8")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
