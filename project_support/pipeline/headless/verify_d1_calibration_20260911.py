"""Independent structural checks for the CPU score-calibration audit."""
import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def finite_or_none(value):
    return value is None or (isinstance(value, (int, float))
                             and math.isfinite(value))


def summarize(rows):
    return {
        "banks": len(rows),
        "top1_contains_oracle": sum(
            row["oracle_index"] == row["selected_index"] for row in rows),
        "top5_contains_oracle": sum(
            row["top5_contains_oracle"] for row in rows),
        "recoverable": sum(row["stratum"] == "recoverable" for row in rows),
        "bank_failure": sum(row["stratum"] == "bank_failure" for row in rows),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--calibration", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--worker-sha256", required=True)
    args = parser.parse_args()
    path = Path(args.calibration)
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["rows"]
    assert len(rows) == 568
    assert Counter(row["model"] for row in rows) == {
        "baseline": 284, "m95": 284}
    assert all(row["candidate_count"] == 128 for row in rows)
    assert all(row["selected_iou"] <= row["oracle_iou"] + 1e-12
               for row in rows)
    assert all(1 <= row["oracle_score_rank"] <= 128 for row in rows)
    assert all(1 <= row["selected_iou_rank"] <= 128 for row in rows)
    assert payload["tests"] == {
        "perfect_spearman": 1.0,
        "reverse_spearman": -1.0,
        "tie_spearman": 0.5,
        "perfect_ndcg": 1.0,
        "reverse_ndcg": 0.58688267143572,
    }
    for name, expected in payload["summary"].items():
        if name == "all":
            subset = rows
        elif name == "baseline":
            subset = [row for row in rows if row["model"] == "baseline"]
        elif name == "m95":
            subset = [row for row in rows if row["model"] == "m95"]
        else:
            model, stratum = name.split("_", 1)
            subset = [row for row in rows
                      if row["model"] == model and row["stratum"] == stratum]
        measured = summarize(subset)
        for key, value in measured.items():
            assert expected[key] == value, (name, key)
        for key, value in expected.items():
            if key in measured:
                continue
            assert finite_or_none(value), (name, key)
    output = {
        "status": "pass",
        "worker_sha256": args.worker_sha256,
        "calibration_sha256": sha256(path),
        "rows": len(rows),
        "models": {"baseline": 284, "m95": 284},
        "candidate_count": 128,
        "summary_counts_checked": True,
        "synthetic_rank_functions_checked": True,
        "cuda_required": False,
    }
    Path(args.out).write_text(
        json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
