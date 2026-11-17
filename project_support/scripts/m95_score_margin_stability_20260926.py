"""Read-only rank-margin audit of the two frozen M95 query analyses."""
import argparse
import hashlib
import json
import math
from pathlib import Path


EXPECTED = {
    "reference": "c7b6e78c64e29144d3abfea5007e5ec0843142b3e7aa6294c600e8eb114d4abb",
    "candidate": "f8456b4e5c2099af4162c00d2e81445e902290e7b3d4948201032a37eab8ea2a",
}


def load(path, expected):
    data = Path(path).read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise ValueError("Frozen analysis SHA256 differs")
    return json.loads(data)


def audit(reference, candidate):
    left = {int(row["manifest_index"]): row for row in reference["rows"]}
    right = {int(row["manifest_index"]): row for row in candidate["rows"]}
    if len(left) != 256 or set(left) != set(right) or set(left) != set(range(256)):
        raise ValueError("Manifest coverage differs")
    rows = []
    for index in range(256):
        a, b = left[index], right[index]
        old, new = a["scores"], b["scores"]
        if len(old) != len(new) or len(old) < 2:
            raise ValueError("Query axis differs")
        if not all(math.isfinite(float(v)) for v in old + new):
            raise ValueError("Nonfinite score")
        top = max(range(len(old)), key=lambda i: old[i])
        top_new = max(range(len(new)), key=lambda i: new[i])
        if top != int(a["deployed_query"]) or top_new != int(b["deployed_query"]):
            raise ValueError("Native selector differs from score argmax")
        runner = max((i for i in range(len(old)) if i != top), key=lambda i: old[i])
        drift = max(abs(float(x) - float(y)) for x, y in zip(old, new))
        margin = float(old[top]) - float(old[runner])
        rows.append({
            "manifest_index": index,
            "scene_id": a["scene_id"],
            "query_count": len(old),
            "selected_changed": top != top_new,
            "reference_margin": margin,
            "max_score_drift": drift,
            "pairwise_bound_exposed": margin <= 2 * drift,
        })
    exposed = [row for row in rows if row["pairwise_bound_exposed"]]
    return {
        "contract": "m95_frozen_rank_margin_audit_v1",
        "inputs_sha256": EXPECTED,
        "rows": 256,
        "scenes": len({row["scene_id"] for row in rows}),
        "selected_changes": sum(row["selected_changed"] for row in rows),
        "pairwise_bound_exposed": len(exposed),
        "exposed_scenes": len({row["scene_id"] for row in exposed}),
        "minimum_margin": min(row["reference_margin"] for row in rows),
        "maximum_score_drift": max(row["max_score_drift"] for row in rows),
        "exposed_rows": exposed,
        "scope": "Observed per-row drift bound only; not a future-run or efficacy guarantee",
        "strict_reproducibility_status": "fail",
        "admission": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reference")
    parser.add_argument("candidate")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise ValueError("Output already exists")
    result = audit(load(args.reference, EXPECTED["reference"]),
                   load(args.candidate, EXPECTED["candidate"]))
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                      encoding="ascii")
    print(json.dumps({k: result[k] for k in (
        "rows", "scenes", "selected_changes", "pairwise_bound_exposed",
        "exposed_scenes", "minimum_margin", "maximum_score_drift"
    )}))


if __name__ == "__main__":
    main()
