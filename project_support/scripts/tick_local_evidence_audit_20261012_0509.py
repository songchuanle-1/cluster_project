"""Verify this tick's downloaded artifacts under the current owning lease."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text())
    assert owner["token"] == args.token
    assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    audit_path = ROOT / "pipeline/reports/tick_evidence_audit_20261012_0509.json"
    remote = json.loads(audit_path.read_text())
    rows = []
    for r in remote["rows"]:
        source = ROOT / "scripts" / r["source"]
        result = ROOT / "pipeline/reports" / r["result"]
        data = json.loads(result.read_text())
        actual_source, actual_result = sha(source), sha(result)
        assert actual_source == r["source_sha256"] == data["script_sha256"]
        assert actual_result == r["result_sha256"]
        rows.append({"result": r["result"], "source": r["source"],
                     "result_sha256": actual_result, "source_sha256": actual_source,
                     "local_remote_and_declared_hashes_match": True})
    hierarchy = ROOT / ("Cluster/framework/model/Quard_model/"
                        "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/"
                        "hier_postprocess.py")
    actual = sha(hierarchy)
    for r in rows:
        data = json.loads((ROOT / "pipeline/reports" / r["result"]).read_text())
        assert data["hierarchy_sha256"] == actual
    result = {
        "local_verified_at": datetime.datetime.now().astimezone().isoformat(),
        "remote_observed_at": remote["remote_observed_at"], "thread_id": owner["thread_id"],
        "token": args.token, "rows": rows, "native_hierarchy_sha256": actual,
        "remote_audit_sha256": sha(audit_path),
        "remote_diagnostic_lock_available": remote["diagnostic_lock"]["returncode"] == 0,
        "remote_gpu7_no_compute_processes": (
            remote["gpu7_compute_processes"]["returncode"] == 0
            and remote["gpu7_compute_processes"]["stdout"] == ""),
        "limits": "Remote/local clocks are recorded independently. Not an allocation grant for a later tick or training efficacy certification."}
    output = ROOT / "pipeline/reports/tick_local_evidence_audit_20261012_0509.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
