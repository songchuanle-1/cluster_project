"""Join frozen native peer-query leakage to deployed mask outcome."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

from m95_native_positive_union_20260927 import CAPTURE_SHA, sha

PEER_SHA = "d400c26f9037ed1107e32113e27fec1de6cafaf6bafb183ba807b9f0ad651eaa"


def analyze(capture_path, peer_path):
    if sha(capture_path) != CAPTURE_SHA or sha(peer_path) != PEER_SHA:
        raise ValueError("Frozen input differs")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    peer = json.loads(peer_path.read_text(encoding="utf-8"))
    if (len(capture["rows"]) != 256 or peer["capture_sha256"] != CAPTURE_SHA
            or peer["contract"] != "m95_fragment_peer_query_origin_v1"
            or len(peer["rows"]) != 26):
        raise ValueError("Frozen cohort differs")
    source = {int(r["manifest_index"]): r for r in capture["rows"]}
    strata = defaultdict(list)
    rows = []
    for item in peer["rows"]:
        native = source[item["manifest_index"]]
        if native["scene"] != item["scene"]:
            raise ValueError("Scene differs")
        selected = float(native["ious"][int(native["selected_query"])])
        maximum = max(float(value) for value in native["ious"])
        positive_peer = sum(p["any_positive"] for p in item["peers"])
        best_peer = sum(p["best_positive"] for p in item["peers"])
        row = {
            "manifest_index": item["manifest_index"], "scene": item["scene"],
            "group": item["group"], "selected_iou": selected,
            "max_iou": maximum, "deployed_failure": selected <= .5,
            "mask_limited": maximum <= .5,
            "peer_superpoints": sum(p["total"] for p in item["peers"]),
            "positive_peer_superpoints": positive_peer,
            "best_positive_peer_superpoints": best_peer,
            "positive_peer_leak": positive_peer > 0,
            "best_positive_peer_leak": best_peer > 0,
        }
        rows.append(row)
        strata["failure" if row["deployed_failure"] else "success"].append(row)
        strata["mask_limited" if row["mask_limited"] else "mask_capable"].append(row)
        strata[row["group"]].append(row)
    if len({r["manifest_index"] for r in rows}) != 26:
        raise ValueError("Duplicate native row")
    def tally(part):
        return {
            "expressions": len(part), "scenes": len({r["scene"] for r in part}),
            "deployed_failures": sum(r["deployed_failure"] for r in part),
            "mask_limited": sum(r["mask_limited"] for r in part),
            "positive_peer_leak": sum(r["positive_peer_leak"] for r in part),
            "best_positive_peer_leak": sum(r["best_positive_peer_leak"] for r in part),
            "peer_superpoints": sum(r["peer_superpoints"] for r in part),
            "positive_peer_superpoints": sum(r["positive_peer_superpoints"] for r in part),
            "best_positive_peer_superpoints":
                sum(r["best_positive_peer_superpoints"] for r in part),
        }
    return {
        "contract": "m95_peer_leak_failure_link_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "peer_sha256": PEER_SHA,
        "strata": {name: tally(part) for name, part in strata.items()},
        "rows": sorted(rows, key=lambda r: r["manifest_index"]),
        "limits": "Retrospective TRAIN outcome association, not causal intervention or admission.",
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "peer", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    result = analyze(args.capture, args.peer)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps(result["strata"]))


if __name__ == "__main__":
    main()
