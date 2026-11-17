"""Frozen M95 native-positive query-mask union, diagnostic only."""
import argparse
import hashlib
import json
from pathlib import Path

CAPTURE_SHA = "68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a"
MANIFEST_SHA = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
PRODUCER_SHA = "206c594d8c5219c6e249d89f7cb91815467bd443a030bc8bbd76d457de0b485a"
CHECKPOINT_SHA = "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
FRAGMENT_SHA = "dc9ce208a764bc2406f6093a089cdc65263f69b4ce23706d615a952194b2ea53"
POPULATION_SHA = "71159f4e74fcc19a72bdf13dd478d6ffe2a30b80823efeb41d6f59b3597800ea"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def metrics(mask, target):
    tp = int((mask & target).sum())
    fp = int((mask & ~target).sum())
    return {"tp": tp, "fp": fp, "recall": tp / int(target.sum()),
            "precision": tp / max(1, tp + fp)}


def evaluate(artifact, source):
    import torch

    idx = source["manifest_index"]
    if (artifact["artifact_contract"] != "m95_manifest_native_query_artifact_v1"
            or artifact["manifest_sha256"] != MANIFEST_SHA
            or int(artifact["manifest_index"]) != idx
            or artifact["axis"]["scene"] != source["scene"]
            or int(artifact["axis"]["ann_id"]) != source["ann_id"]):
        raise ValueError(f"Artifact identity differs: {idx}")
    masks = artifact["query_masks"].bool()
    target = artifact["target_union"].bool()
    if masks.ndim != 2 or masks.shape != (128, target.numel()) or not target.any():
        raise ValueError(f"Native mask axis differs: {idx}")
    positive = [i for i, yes in enumerate(source["native_positive"]) if yes]
    if (not positive or len(artifact["native_positive"]) != 128
            or any(bool(artifact["native_positive"][i]) != (i in positive)
                   for i in range(128))):
        raise ValueError(f"Matcher positive set differs: {idx}")
    negative = [i for i in range(128) if i not in positive][:len(positive)]
    if len(negative) != len(positive):
        raise ValueError(f"Insufficient negative controls: {idx}")
    best = min(positive, key=lambda i: (
        -int((masks[i] & target).sum()), int((masks[i] & ~target).sum()), i))
    union = masks[positive].any(dim=0)
    all_union = masks.any(dim=0)
    negative_union = masks[negative].any(dim=0)
    out = {"manifest_index": idx, "scene": source["scene"],
           "ann_id": source["ann_id"], "positive_count": len(positive),
           "best_positive": best, "best": metrics(masks[best], target),
           "positive_union": metrics(union, target),
           "all_union": metrics(all_union, target),
           "negative_union": metrics(negative_union, target),
           "target_size": int(target.sum())}
    out["positive_extra_recall"] = out["positive_union"]["recall"] - out["best"]["recall"]
    out["all_extra_recall"] = out["all_union"]["recall"] - out["best"]["recall"]
    return out


def analyze(capture_path, artifact_root, fragment_path, population_path):
    import torch

    for path, expected in ((capture_path, CAPTURE_SHA), (fragment_path, FRAGMENT_SHA),
                           (population_path, POPULATION_SHA)):
        if sha(path) != expected:
            raise ValueError(f"Frozen source differs: {path}")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    fragment = json.loads(fragment_path.read_text(encoding="utf-8"))
    population = json.loads(population_path.read_text(encoding="utf-8"))
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or len(capture["rows"]) != 256
            or fragment["capture_sha256"] != CAPTURE_SHA
            or population["capture_sha256"] != CAPTURE_SHA):
        raise ValueError("Frozen capture provenance differs")
    limited = {r["manifest_index"] for r in population["limited_rows"]}
    controls = {r["manifest_index"] for r in population["control_rows"]}
    fragmented = {r["manifest_index"] for r in fragment["groups"]["limited"]["rows"]
                  if r["extra_recall"] > 0}
    if len(limited) != 16 or len(controls) != 16 or len(fragmented) != 4:
        raise ValueError("Frozen cohort differs")
    pending = limited | controls
    source = {r["manifest_index"]: r for r in capture["rows"]}
    results = {}
    for entry in capture["feature_artifacts"]:
        if not pending:
            break
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError(f"Frozen artifact differs: {path}")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            idx = int(artifact["manifest_index"])
            if idx in pending:
                results[idx] = evaluate(artifact, source[idx])
                pending.remove(idx)
    if pending:
        raise ValueError(f"Missing frozen rows: {sorted(pending)}")
    groups = {}
    for name, indices in (("fragmented", fragmented),
                          ("other_limited", limited - fragmented),
                          ("covered_controls", controls)):
        rows = [results[i] for i in sorted(indices)]
        groups[name] = {
            "expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
            "positive_extra": sum(r["positive_extra_recall"] > 0 for r in rows),
            "all_extra": sum(r["all_extra_recall"] > 0 for r in rows),
            "mean_positive_extra_recall": sum(r["positive_extra_recall"] for r in rows) / len(rows),
            "mean_positive_precision": sum(r["positive_union"]["precision"] for r in rows) / len(rows),
            "mean_all_precision": sum(r["all_union"]["precision"] for r in rows) / len(rows),
            "rows": rows,
        }
    return {"contract": "m95_native_positive_union_v1", "admission": False,
            "capture_sha256": CAPTURE_SHA, "fragment_sha256": FRAGMENT_SHA,
            "population_sha256": POPULATION_SHA, "groups": groups,
            "limits": "TRAIN GT-localized existing matcher only; no deployable rule, new-model backward, efficacy, or admission."}


def main():
    p = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "fragment", "population", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    result = analyze(args.capture, args.artifact_root, args.fragment, args.population)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps({name: {k: v for k, v in group.items() if k != "rows"}
                      for name, group in result["groups"].items()}))


if __name__ == "__main__":
    main()
