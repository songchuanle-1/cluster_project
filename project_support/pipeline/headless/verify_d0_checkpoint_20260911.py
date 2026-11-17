"""Verify immutable audit artifacts and freeze a CPU-only provenance summary."""
import hashlib
import json
from pathlib import Path

ROOT = Path("D:/project/cluster_project")
OUT = ROOT / "pipeline/reports/d0_checkpoint_identity_20260911-0413"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    summary = {}
    cases = (
        ("baseline", "20260627_174353.log", .4894491136074066, 15),
        ("m95", "20260815_101011.log", .5024607181549072, 16),
    )
    for name, logfile, miou, epoch in cases:
        audit_path = OUT / f"d0_{name}_identity_20260911.json"
        audit = json.loads(audit_path.read_text())
        assert sha(OUT / logfile) == audit["log"]["log_sha256"]
        assert not audit["cuda_initialized"]
        assert not audit["strict_load_passed"] and audit["adapted_strict_load_passed"]
        assert audit["nonfinite_tensors"] == []
        assert audit["compatibility"]["missing"] == []
        assert audit["compatibility"]["mismatches"] == {}
        assert len(audit["legacy_buffers"]) == 2
        assert all(v["matches_runtime_buffer"] for v in audit["legacy_buffers"].values())
        best = audit["log"]["best"]
        assert (best["miou"], best["epoch"]) == (miou, epoch)
        assert audit["meta"]["epoch"] == epoch
        assert abs(float(audit["meta"]["best_miou"]) - miou) < 1e-7
        summary[name] = dict(audit_sha256=sha(audit_path),
                             checkpoint_sha256=audit["checkpoint_sha256"],
                             best=best, cpu_compatible=True, replay_verified=False)
    manifest_path = ROOT / "pipeline/reports/d0_inventory_20260911-0316/sample_manifest_v2.json"
    assert sha(manifest_path) == "84a7d60f85ecd5bec44b77b304140ff00c8c1fa00177dc12ecf7ef5ebfabb468"
    manifest = json.loads(manifest_path.read_text())
    groups = {subset: {s["physical_scene"] for s in manifest["samples"] if s["subset"] == subset}
              for subset in ("diagnostic", "reserved_evaluation")}
    assert not groups["diagnostic"] & groups["reserved_evaluation"]
    summary["manifest_unchanged"] = True
    summary["exact_gain"] = summary["m95"]["best"]["miou"] - summary["baseline"]["best"]["miou"]
    summary["exact_gap_to_target"] = .51 - summary["m95"]["best"]["miou"]
    summary["ledger_unchanged"] = (
        sha(ROOT / "pipeline/experiments.csv")
        == "87d73d8fd0b7c039b34d4191ae8df4e4f27a525b51f13589f18d1e989e602679")
    assert summary["ledger_unchanged"]
    (OUT / "verified_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
