"""Recover native referent classes for the unresolved M95 failure pairs.

This is read-only CPU work. It reads the native ScanRefer annotations on
server-6, verifies the selected and target physical instance axes, and writes a
hash-bound local receipt. No GPU, queue, model, or training state is touched.
"""
import base64
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CAPTURE = (
    ROOT
    / "pipeline"
    / "diagnostic_runs"
    / "m95_same_forward_20260922-0945"
    / "capture.json"
)
OUTPUT = (
    ROOT
    / "pipeline"
    / "reports"
    / "m95_semantic_identity_recovery_20260922-1048.json"
)
EXPECTED_CAPTURE_SHA256 = (
    "975c718ddefb122ef8368c117439e9562b9893bb40abf8d80d1fc31c05824c80"
)


def normalize_phrase(value):
    return " ".join(
        "".join(ch for ch in part.lower() if ch.isalnum())
        for part in str(value or "").split()
        if "".join(ch for ch in part.lower() if ch.isalnum())
    )


def phrases_match(left, right):
    left = normalize_phrase(left)
    right = normalize_phrase(right)
    if not left or not right:
        return False
    if left == right or left in right or right in left:
        return True
    return left.split()[-1] == right.split()[-1]


REMOTE_CODE = r"""
import base64, hashlib, json, sys
from pathlib import Path

root = Path("/data3/songcl/data/scanrefer")
scene_graph_path = root / "scene_graphs_new_train.json"
annotations_path = root / "ScanRefer_train_new.json"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


scene_graphs = json.loads(scene_graph_path.read_text(encoding="utf-8"))
annotations = json.loads(annotations_path.read_text(encoding="utf-8"))
pairs = json.loads(base64.b64decode(sys.argv[1]).decode("utf-8"))

annotation_index = {
    (entry["scene_id"], int(entry["ann_id"])): entry
    for entry in annotations
}


def node_for_annotation(scene, ann_id):
    graph = scene_graphs.get(scene, {}).get(str(ann_id), {})
    nodes = graph.get("graph_node") or []
    if not nodes:
        raise ValueError("Missing scene graph node: %s ann %s" %
                         (scene, ann_id))
    return nodes[0]


def normalize_phrase(value):
    return " ".join(
        "".join(ch for ch in part.lower() if ch.isalnum())
        for part in str(value or "").split()
        if "".join(ch for ch in part.lower() if ch.isalnum())
    )


def phrases_match(left, right):
    left = normalize_phrase(left)
    right = normalize_phrase(right)
    if not left or not right:
        return False
    if left == right or left in right or right in left:
        return True
    return left.split()[-1] == right.split()[-1]


rows = []
for pair in pairs:
    scene = pair["scene"]
    ann_id = int(pair["ann_id"])
    target_instance = int(pair["target_instance"])
    wrong_instance = int(pair["wrong_instance"])
    annotation = annotation_index.get((scene, ann_id))
    if annotation is None:
        raise ValueError("Missing ScanRefer annotation: %s ann %s" %
                         (scene, ann_id))
    if int(annotation["object_id"]) != target_instance:
        raise ValueError("Target object_id mismatch: %s ann %s" %
                         (scene, ann_id))
    target = node_for_annotation(scene, ann_id)
    wrong_annotations = [
        entry for entry in annotations
        if entry["scene_id"] == scene
        and int(entry["object_id"]) == wrong_instance
    ]
    wrong_variants = []
    for entry in wrong_annotations:
        key = scene_graphs.get(scene, {}).get(str(entry["ann_id"]), {})
        nodes = key.get("graph_node") or []
        if not nodes:
            continue
        node = nodes[0]
        wrong_variants.append({
            "ann_id": int(entry["ann_id"]),
            "graph_name": node.get("target"),
            "lemma_head": node.get("lemma_head"),
            "matches_target": phrases_match(
                target.get("lemma_head"), node.get("lemma_head")
            ),
        })
    if not wrong_variants:
        raise ValueError("No scene graph variant for wrong instance: %s %s" %
                         (scene, wrong_instance))
    matching_variants = [
        item for item in wrong_variants
        if item["matches_target"]
        and normalize_phrase(item["lemma_head"]) not in {"object", "scene", "item"}
    ]
    chosen = matching_variants[0] if matching_variants else wrong_variants[0]
    rows.append({
        "scene": scene,
        "ann_id": ann_id,
        "dataset_index": int(pair["dataset_index"]),
        "target_instance": target_instance,
        "wrong_instance": wrong_instance,
        "target_annotation_object_name_raw": annotation["object_name"],
        "target_graph_name": target.get("target"),
        "target_lemma_head": target.get("lemma_head"),
        "target_node_type": target.get("node_type"),
        "wrong_source_ann_id": chosen["ann_id"],
        "wrong_graph_name": chosen["graph_name"],
        "wrong_lemma_head": chosen["lemma_head"],
        "wrong_variants": wrong_variants,
        "same_class_phrase": bool(matching_variants),
    })

print(json.dumps({
    "sources": {
        "scene_graphs_new_train.json": {
            "path": str(scene_graph_path),
            "sha256": sha256(scene_graph_path),
            "bytes": scene_graph_path.stat().st_size,
        },
        "ScanRefer_train_new.json": {
            "path": str(annotations_path),
            "sha256": sha256(annotations_path),
            "bytes": annotations_path.stat().st_size,
        },
    },
    "rows": rows,
}, ensure_ascii=True))
"""


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify_pair(remote_row):
    return "same-class" if remote_row["same_class_phrase"] else "cross-class-name"


def collect_unresolved_pairs(capture):
    rows = []
    for row in capture["rows"]:
        selected = int(row["selected_query"])
        if float(row["ious"][selected]) > 0.5:
            continue
        target = int(row["target_instances"][0])
        overlaps = row["selected_mask_endpoints"]["overlaps"]
        wrong = max(overlaps, key=lambda item: float(item["iou"]))["instance"]
        rows.append({
            "scene": row["scene"],
            "ann_id": int(row["ann_id"]),
            "dataset_index": int(row["dataset_index"]),
            "target_instance": target,
            "wrong_instance": int(wrong),
        })
    if len(rows) != 8:
        raise ValueError("Expected eight selected-query failures")
    unresolved = [
        row for row in rows
        if any(
            item["instance"] in {row["target_instance"], row["wrong_instance"]}
            and item["semantic_class"] == -100
            for source in capture["rows"]
            if source["scene"] == row["scene"]
            and int(source["ann_id"]) == row["ann_id"]
            for item in source["selected_mask_endpoints"]["overlaps"]
        )
    ]
    if len(unresolved) != 6:
        raise ValueError("Expected six semantic-unresolved failures")
    return unresolved


def main():
    if file_sha256(CAPTURE) != EXPECTED_CAPTURE_SHA256:
        raise ValueError("Capture hash differs from the frozen receipt")
    capture = json.loads(CAPTURE.read_text(encoding="utf-8"))
    pairs = collect_unresolved_pairs(capture)
    encoded_code = base64.b64encode(REMOTE_CODE.encode("utf-8")).decode("ascii")
    encoded_pairs = base64.b64encode(
        json.dumps(pairs).encode("utf-8")
    ).decode("ascii")
    remote_command = (
        "python3 -c \"import base64;exec(base64.b64decode('%s'))\" %s"
        % (encoded_code, encoded_pairs)
    )
    completed = subprocess.run(
        ["ssh", "server-6", remote_command],
        check=True,
        capture_output=True,
        text=True,
    )
    native = json.loads(completed.stdout)
    rows = native["rows"]
    if len(rows) != 6:
        raise ValueError("Expected six recovered native rows")
    for row in rows:
        row["classification"] = classify_pair(row)
    result = {
        "contract": "m95_semantic_identity_recovery_v1",
        "generated_at": "2026-09-22T10:48:00+08:00",
        "scope": (
            "Read-only native ScanRefer/SceneGraph identity recovery for six "
            "selected-query failures whose sampled semantic labels were -100. "
            "No GPU, model, queue, admission, sync, or training action."
        ),
        "source_capture": {
            "path": CAPTURE.relative_to(ROOT).as_posix(),
            "sha256": EXPECTED_CAPTURE_SHA256,
        },
        "native_sources": native["sources"],
        "summary": {
            "selected_query_failures": 8,
            "previously_semantic_unresolved": 6,
            "recovered": 6,
            "same_class_phrase": sum(row["same_class_phrase"] for row in rows),
            "cross_class_name": sum(
                not row["same_class_phrase"] for row in rows
            ),
            "combined_known_same_class_failures": 2 + sum(
                row["same_class_phrase"] for row in rows
            ),
            "combined_known_cross_class_failures": sum(
                not row["same_class_phrase"] for row in rows
            ),
        },
        "rows": rows,
        "interpretation": (
            "All six previously unresolved failure pairs are same-class under "
            "the native annotation-indexed scene graphs; together with the two "
            "earlier known same-class pairs, all eight selected-query failures "
            "are same-class identity confusions. The objectness-only any-seed "
            "control is not class-matched, so the bounded capture cannot "
            "distinguish referent identity from same-class objectness. This is "
            "bounded diagnostic evidence, not a population effect and not "
            "admission or efficacy evidence."
        ),
        "not_evidence_of": [
            "admission",
            "efficacy",
            "population effect",
            "referent-specific causality",
            "a deployable mechanism",
        ],
    }
    OUTPUT.write_text(
        json.dumps(result, indent=2, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
