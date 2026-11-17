"""Outcome-blind audit of frozen native-31 lexical context controls."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "pipeline/reports/m95_multiword_capture_manifest_20260928.json"
SOURCE = ROOT / (
    "Cluster/framework/dataset/scannetv2.py"
)
OUTPUT = ROOT / "pipeline/reports/m95_native31_lexical_pair_20260928.json"
EXPECTED_MANIFEST = "85e108e8c86d65bcdbdc25061987e0a973fa45b35b00030d0721d359da720040"
EXPECTED_SOURCE = "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def class_keys(source):
    tree = ast.parse(source.read_text(encoding="utf-8"))
    assignments = [
        node.value
        for cls in tree.body if isinstance(cls, ast.ClassDef)
        for method in cls.body if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))
        for node in ast.walk(method) if isinstance(node, ast.Assign)
        if any(isinstance(t, ast.Attribute) and t.attr == "type2class" for t in node.targets)
    ]
    if len(assignments) != 1:
        raise ValueError("Expected one literal type2class assignment")
    mapping = ast.literal_eval(assignments[0])
    return set(mapping) - {"others"}


def audit(manifest, keys):
    rows = {(r["scene"], r["ann_id"]): r for r in manifest["records"]}
    if len(rows) != 31 or len(manifest["pairs"]) != 11:
        raise ValueError("Frozen cohort size differs")

    def present(row):
        return sorted(keys.intersection(row["text"].split()))

    edges = []
    for pair in manifest["pairs"]:
        key = pair["scene"], pair["ann_id"]
        exposed = rows[key]
        if exposed["arm"] != "phrase":
            raise ValueError("Exposed arm changed")
        for control in pair["all_controls"]:
            other = rows[pair["scene"], control["ann_id"]]
            if other["arm"] != "phrase_absent" or other["target_instances"] != exposed["target_instances"]:
                raise ValueError("Control arm or physical target changed")
            edges.append({
                "scene": pair["scene"], "exposed": pair["ann_id"],
                "control": control["ann_id"],
                "exposed_keys": present(exposed), "control_keys": present(other),
                "same_keys": present(exposed) == present(other),
            })
    if len(edges) != 30:
        raise ValueError("Frozen pair count differs")
    arm_keys = {
        arm: Counter(
            "curtain" in present(row) for row in rows.values() if row["arm"] == arm
        ) for arm in ("phrase", "phrase_absent")
    }
    return {
        "contract": "m95_native31_lexical_pair_v1",
        "admission": False,
        "manifest_sha256": EXPECTED_MANIFEST, "source_sha256": EXPECTED_SOURCE,
        "exposed_count": 11, "unique_control_count": 20,
        "edge_count": len(edges),
        "same_key_edges": sum(edge["same_keys"] for edge in edges),
        "curtain_key_by_arm": {
            arm: {"present": count[True], "absent": count[False]}
            for arm, count in arm_keys.items()
        },
        "edges": edges,
        "limits": "Source token sets only; repeated controls and text confounding; no native outcome or causal claim.",
    }


if __name__ == "__main__":
    if digest(MANIFEST) != EXPECTED_MANIFEST or digest(SOURCE) != EXPECTED_SOURCE:
        raise ValueError("Frozen input hashes differ")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    result = audit(data, class_keys(SOURCE))
    if OUTPUT.exists():
        raise ValueError("Refusing to replace existing evidence")
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("edge_count", "same_key_edges", "curtain_key_by_arm")}))
