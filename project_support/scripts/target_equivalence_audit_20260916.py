"""Static physical-target equivalence audit of an existing fixed TRAIN capture."""
from collections import defaultdict
import hashlib
import itertools
import json
from pathlib import Path


def audit(rows):
    groups = defaultdict(list)
    seen = set()
    for row in rows:
        key = (row["scene"], row["ann_id"])
        if key in seen:
            raise ValueError("Duplicate scene/annotation identity")
        seen.add(key)
        targets = tuple(sorted(row["target_ids"]))
        if len(targets) != 1:
            raise ValueError("Audit requires single-target expressions")
        groups[(row["scene"], targets)].append(row)
    pairs = []
    for (scene, targets), group in sorted(groups.items()):
        for a, b in itertools.combinations(sorted(group, key=lambda x: x["ann_id"]), 2):
            observable = all(r["winner_id"] is not None and r["winner_overlap"] > .5
                             for r in (a, b))
            pairs.append(dict(scene=scene, target_ids=list(targets),
                ann_ids=[a["ann_id"], b["ann_id"]],
                utterances=[a["utterance"], b["utterance"]],
                winner_ids=[a["winner_id"], b["winner_id"]],
                winner_observable=observable,
                same_winner=a["winner_id"] == b["winner_id"] if observable else None,
                both_correct_identity=all(r["winner_id"] in targets for r in (a, b))
                                      if observable else None,
                ious=[a["before"], b["before"]],
                success_disagreement=(a["before"] > .5) != (b["before"] > .5),
                iou_difference=abs(a["before"] - b["before"])))
    return dict(summary=dict(expressions=len(rows), scenes=len({r["scene"] for r in rows}),
        paired_groups=sum(len(g) > 1 for g in groups.values()),
        pairs=len(pairs), observable_pairs=sum(p["winner_observable"] for p in pairs),
        different_winner_pairs=sum(p["same_winner"] is False for p in pairs),
        both_correct_identity_pairs=sum(p["both_correct_identity"] is True for p in pairs),
        success_disagreements=sum(p["success_disagreement"] for p in pairs)),
        pairs=pairs, limitations=[
            "Fixed123TRAIN capture;five paired objects cannot establish population invariance.",
            "Physical instance IDs only;no cross-forward query-index joins.",
            "Instance equality does not imply equal mask boundaries or identical logits.",
            "Strict IoU>.5 is the inherited diagnostic convention,not an exact native metric proof.",
            "No unsupported consistency mechanism admitted;broader hypothesis remains untested."])


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    source = root / "pipeline/reports/anchor_instance_names_20260916.json"
    result = audit(json.loads(source.read_text(encoding="utf-8"))["rows"])
    result["evidence"] = [dict(path=str(p.relative_to(root)),
        sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in (source, Path(__file__))]
    output = root / "pipeline/reports/target_equivalence_20260916.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"]))
