"""Check availability, never infer boundary components from mask components."""
import hashlib
import json
from pathlib import Path


def audit(source):
    rows = source["rows"]
    identities = [(r["scene_id"], r["object_id"], r["ann_id"]) for r in rows]
    scenes = sorted({r["scene_id"] for r in rows})
    needed = ("boundary_component_membership", "boundary_component_sizes",
              "boundary_component_positive_counts")
    missing = {
        field: [list(key) for key, row in zip(identities, rows) if field not in row]
        for field in needed
    }
    assert len(rows) == source["banks"]
    assert len(scenes) == source["scenes"]
    assert len(set(identities)) == len(rows)
    assert all(scene in source["graphs"] for scene in scenes)
    return {
        "coverage_checks": "PASS",
        "banks": len(rows),
        "scenes": scenes,
        "source_reported_missing": source["missing"],
        "missing_required_fields": {k: len(v) for k, v in missing.items()},
        "missing_bank_identities": missing,
        "whole_mask_component_rows": sum(
            "gt_components" in r and "pred_components" in r for r in rows),
        "boundary_component_incidence": None,
        "availability": "INCOMPLETE" if any(missing.values()) else "AVAILABLE",
        "interpretation": "Schema availability only; no incidence or efficacy estimate.",
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    path = root / "reports/boundary_adjacency_audit_20260914.json"
    data = path.read_bytes()
    result = audit(json.loads(data))
    result["source"] = str(path)
    result["source_sha256"] = hashlib.sha256(data).hexdigest()
    # Negative control: whole-mask components cannot satisfy the boundary contract.
    mock = {"rows": [{"scene_id": "s", "object_id": "o", "ann_id": "a",
                     "gt_components": 2, "pred_components": 3}],
            "banks": 1, "scenes": 1, "graphs": {"s": {}}, "missing": 0}
    assert audit(mock)["availability"] == "INCOMPLETE"
    for key in result["missing_required_fields"]:
        mock["rows"][0][key] = []
    assert audit(mock)["availability"] == "AVAILABLE"
    result["schema_negative_positive_controls"] = "PASS"
    out = root / "reports/component_evidence_availability_20260915-1509.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ("missing_bank_identities", "scenes")}, indent=2))
