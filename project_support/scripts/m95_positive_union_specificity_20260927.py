"""Check fixed threshold crossing of native-positive union on frozen cohorts."""
import argparse
import hashlib
import json
from pathlib import Path

UNION_SHA = "44cc861714a5fe49ded3d6e02afec8893d8d139860422babdd4049a0ad8f9aa2"
POPULATION_SHA = "71159f4e74fcc19a72bdf13dd478d6ffe2a30b80823efeb41d6f59b3597800ea"
FRAGMENT_SHA = "dc9ce208a764bc2406f6093a089cdc65263f69b4ce23706d615a952194b2ea53"
POSITIVE_SHA = "a81b30f58c039cf52bc26c00e345408113c96a935fd0290a7502e799f5a0c7ce"


def read(path, expected):
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != expected:
        raise ValueError(f"Frozen report differs: {path}")
    return json.loads(content)


def iou(arm, target_size):
    denominator = target_size + arm["fp"]
    return arm["tp"] / denominator


def analyze(union, population, fragment, positive):
    if not (union["capture_sha256"] == population["capture_sha256"]
            == fragment["capture_sha256"] == positive["capture_sha256"]):
        raise ValueError("Captures differ")
    native = {r["manifest_index"]: r
              for key in ("limited_rows", "control_rows")
              for r in population[key]}
    limited = {r["manifest_index"] for r in population["limited_rows"]}
    fragmented = {r["manifest_index"] for r in fragment["groups"]["limited"]["rows"]
                  if r["extra_recall"] > 0}
    positive_rows = {r["manifest_index"]: r for r in positive["rows"]}
    if len(native) != 32 or len(limited) != 16 or len(fragmented) != 4:
        raise ValueError("Cohorts differ")
    groups = {}
    seen = set()
    for name in ("fragmented", "other_limited", "covered_controls"):
        source_rows = union["groups"][name]["rows"]
        rows = []
        for r in source_rows:
            idx = r["manifest_index"]
            n = native[idx]
            if (idx in seen or r["scene"] != n["scene"]
                    or (idx in fragmented) != (name == "fragmented")
                    or (idx in limited) != (name != "covered_controls")):
                raise ValueError(f"Frozen positive identity differs: {idx}")
            seen.add(idx)
            values = {key: iou(r[key], r["target_size"])
                      for key in ("best", "positive_union", "all_union", "negative_union")}
            if idx in limited:
                p = positive_rows[idx]
                if (r["best_positive"] != p["best_positive_query"]
                        or abs(values["best"] - p["selected_iou"]) > 1e-5):
                    raise ValueError(f"Frozen best-positive IoU differs: {idx}")
            elif values["best"] > n["max_iou"] + 1e-5:
                raise ValueError(f"Best-positive exceeds native maximum: {idx}")
            rows.append({"manifest_index": idx, "scene": r["scene"],
                         "positive_count": r["positive_count"], **values})
        groups[name] = {
            "expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
            "positive_union_fixed": sum(r["best"] <= .5 < r["positive_union"] for r in rows),
            "positive_union_broken": sum(r["best"] > .5 >= r["positive_union"] for r in rows),
            "positive_union_harmed": sum(r["positive_union"] < r["best"] for r in rows),
            "all_union_fixed": sum(r["best"] <= .5 < r["all_union"] for r in rows),
            "all_union_broken": sum(r["best"] > .5 >= r["all_union"] for r in rows),
            "rows": rows,
        }
    if seen != set(native):
        raise ValueError("Incomplete frozen population")
    return {"contract": "m95_positive_union_specificity_v1", "admission": False,
            "union_sha256": UNION_SHA, "population_sha256": POPULATION_SHA,
            "fragment_sha256": FRAGMENT_SHA, "positive_sha256": POSITIVE_SHA,
            "groups": groups,
            "limits": "TRAIN oracle-matcher-positive union only; not deployable, new-model backward or efficacy."}


def main():
    parser = argparse.ArgumentParser()
    for name in ("union", "population", "fragment", "positive", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    result = analyze(
        read(args.union, UNION_SHA), read(args.population, POPULATION_SHA),
        read(args.fragment, FRAGMENT_SHA), read(args.positive, POSITIVE_SHA))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps({key: {k: v for k, v in g.items() if k != "rows"}
                      for key, g in result["groups"].items()}))


if __name__ == "__main__":
    main()
