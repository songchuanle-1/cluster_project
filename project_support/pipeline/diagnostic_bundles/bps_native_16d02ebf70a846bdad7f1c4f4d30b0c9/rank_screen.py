"""CPU-only, paired native-query cost ordering screen."""

from collections import Counter
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import json

os.environ["PROJECT_ROOT"] = "D:/project"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick

PROJECT = Path("D:/project/cluster_project")
BUNDLE = Path(__file__).resolve().parent
TOKEN = "16d02ebf70a846bdad7f1c4f4d30b0c9"
owner = tick.load(PROJECT / "pipeline/headless/.foreground.lockdir/owner.json")
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
bank = tick.load(BUNDLE / "bank_result.json")
native = tick.load(BUNDLE / "bank_native_result.json")
assert bank["status"] == "completed" and len(bank["rows"]) == 2 * len(native["rows"])
totals = Counter()
transitions = Counter()
examples = []
records = []


def order(delta, epsilon):
    if delta < -epsilon:
        return "concordant"
    if delta > epsilon:
        return "discordant"
    return "tied"


for group_index, group in enumerate(native["rows"]):
    first, second = bank["rows"][2 * group_index:2 * group_index + 2]
    assert first == second, "Require exact stored readout repeat before screening"
    for expression, row in enumerate(first["expressions"]):
        if not row["available_events"]:
            continue
        counts = Counter()
        local = Counter()
        for left in range(row["query_count"]):
            for right in range(left + 1, row["query_count"]):
                if row["ious"][left] == row["ious"][right]:
                    counts["equal_iou_pairs_excluded"] += 1
                    continue
                better, worse = (left, right) if row["ious"][left] > row["ious"][right] else (right, left)
                original_delta = row["original"][better] - row["original"][worse]
                oracle_delta = row["oracle"][better] - row["oracle"][worse]
                counts["unequal_iou_pairs"] += 1
                for label, epsilon in (("exact", 0), ("separated1e6", 1e-6)):
                    before, after = order(original_delta, epsilon), order(oracle_delta, epsilon)
                    local[label + ":" + before + "->" + after] += 1
                    counts[label + ":original_" + before] += 1
                    counts[label + ":oracle_" + after] += 1
                    if label == "separated1e6" and before == "concordant" and after == "discordant" and len(examples) < 8:
                        examples.append({
                            "scene": group["scan_ids"][expression],
                            "ann_id": group["ann_ids"][expression], "group": group["group_index"],
                            "better_query": better, "worse_query": worse,
                            "better_iou": row["ious"][better], "worse_iou": row["ious"][worse],
                            "original_better_minus_worse_cost": original_delta,
                            "oracle_better_minus_worse_cost": oracle_delta,
                        })
        records.append({
            "scene": group["scan_ids"][expression], "ann_id": group["ann_ids"][expression],
            "group": group["group_index"], "counts": dict(counts), "transitions": dict(local),
        })
        totals.update(counts)
        transitions.update(local)
result = {
    "token": TOKEN, "recorded_at": datetime.now().astimezone().isoformat(),
    "script_sha256": tick.digest(Path(__file__)),
    "bank_sha256": tick.digest(BUNDLE / "bank_result.json"),
    "native_sha256": tick.digest(BUNDLE / "bank_native_result.json"),
    "expressions": len(records), "scenes": len({row["scene"] for row in records}),
    "counts": dict(totals), "transitions": dict(transitions),
    "separated_concordant_to_discordant_examples": examples, "rows": records,
    "universal_nonworsening_claim": "disconfirmed_in_fixed_native_bank" if examples else "not_disconfirmed_by_this_screen",
    "scope": "Correlated within-bank pairs, not independent samples, causal task harm, efficacy or rejection of every teacher-supervision mechanism.",
}
tick.save(BUNDLE / "rank_result.json", result)
print(json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2))
