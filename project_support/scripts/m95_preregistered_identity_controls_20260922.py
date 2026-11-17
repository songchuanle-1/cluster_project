"""Pre-register the larger M95 referent-identity control cohort.

The cohort is selected only from native ScanRefer metadata and frozen before
any model outcome is observed. This script performs a read-only remote metadata
query, writes a local manifest, and emits a hash-bound receipt. It does not run
the model, mutate the queue, admit a mechanism, or touch GPU state.
"""
import argparse
import base64
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_DIR = (
    ROOT / "pipeline" / "diagnostic_runs" / "m95_identity_controls_20260922"
)
MANIFEST_PATH = MANIFEST_DIR / "manifest.json"
REPORT_PATH = (
    ROOT / "pipeline" / "reports" / "m95_preregistered_manifest_20260922-1320.json"
)
CONTRACT = "m95_preregistered_identity_controls_v1"
SELECTION_SALT = "m95_identity_controls_v1"
SELECTION_SEED = 1999
EXPRESSIONS_PER_STRATUM = 128
MAX_EXPRESSIONS_PER_SCENE_PER_STRATUM = 1
MAX_EXPRESSIONS_PER_CLASS_PER_STRATUM = 4
EXPECTED_SOURCE_SHA256 = {
    "scene_graphs_new_train.json": (
        "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08"
    ),
    "ScanRefer_train_new.json": (
        "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d"
    ),
}


REMOTE_CODE = r"""
import hashlib, json
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


def normalize_class(value):
    return "".join(
        character
        for character in str(value or "").strip().lower()
        if character.isalnum()
    )


annotations = json.loads(annotations_path.read_text(encoding="utf-8"))
by_scene = {}
for entry in annotations:
    scene = str(entry["scene_id"])
    object_id = str(entry["object_id"])
    class_name = normalize_class(entry["object_name"])
    if not class_name:
        raise ValueError("Empty ScanRefer object class")
    by_scene.setdefault(scene, {})[object_id] = class_name

records = []
for entry in annotations:
    scene = str(entry["scene_id"])
    object_id = str(entry["object_id"])
    class_name = normalize_class(entry["object_name"])
    peers = sorted(
        peer
        for peer, peer_class in by_scene[scene].items()
        if peer != object_id and peer_class == class_name
    )
    description = str(entry["description"])
    records.append({
        "scene_id": scene,
        "ann_id": int(entry["ann_id"]),
        "target_object_id": object_id,
        "target_class": class_name,
        "same_class_peer_object_ids": peers,
        "same_class_peer_count": len(peers),
        "scene_object_count": len(by_scene[scene]),
        "description_sha256": hashlib.sha256(
            description.encode("utf-8")
        ).hexdigest(),
        "description_tokens": len(description.split()),
        "stratum": "ambiguous" if peers else "class_unique",
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
    "records": records,
}, ensure_ascii=True))
"""


CONTROL_CONTRACT = {
    "acceptable_query": {
        "metric": "target_union_iou",
        "operator": ">",
        "threshold": 0.5,
    },
    "deployed": "score argmax over all queries; lowest index wins ties",
    "target_positive": (
        "score argmax over queries whose mask is a native training positive; "
        "null and no fallback when the pool is empty"
    ),
    "target_objectness": (
        "score argmax over queries whose FPS seed lies in the target instance "
        "union; null and no fallback when the pool is empty"
    ),
    "class_matched_selector": (
        "score argmax over queries whose dominant-overlap physical instance has "
        "the target class; target and non-target instances are both allowed; "
        "null and no fallback when the pool is empty"
    ),
    "class_matched_non_target": (
        "score argmax over queries whose dominant-overlap physical instance is "
        "a declared same-class peer of the target; null and no fallback when "
        "the pool is empty"
    ),
    "dominant_overlap": {
        "instance": (
            "argmax overlap count between the query mask and physical instance "
            "labels; lowest instance ID wins ties"
        ),
        "minimum_overlap_points": 1,
        "unknown_class": "exclude query from class-matched pools",
    },
    "score_matched_pair": {
        "positive_pool": "target_positive query",
        "negative_pool": "class_matched_non_target query",
        "max_absolute_score_difference": 0.1,
        "tie_break": (
            "minimum absolute score difference, then SHA256 of contract and "
            "query pair, then positive index, then negative index"
        ),
        "unavailable_policy": "row excluded from paired estimand; no fallback",
    },
    "unknown_semantics": (
        "use the frozen manifest object_id-to-class map; sampled semantic label "
        "-100 never substitutes for native annotation class"
    ),
}


PRIMARY_ESTIMAND = {
    "name": "scene_balanced_paired_target_iou_uplift",
    "unit": "selected-query target-union IoU",
    "contrast": "target_positive minus score_matched_non_target",
    "aggregation": (
        "compute the paired mean within each scene, then average scene means"
    ),
    "bootstrap": {
        "unit": "scene",
        "draws": 10000,
        "seed": SELECTION_SEED,
        "interval": 0.95,
    },
    "minimum_complete_pairs": 64,
    "minimum_independent_scenes": 64,
    "minimum_point_estimate": 0.05,
    "minimum_ci_lower": 0.0,
}


REJECTION_CRITERIA = [
    "reject identity-specific causal support when complete pairs are below 64",
    "reject identity-specific causal support when independent scenes are below 64",
    "reject identity-specific causal support when the paired point estimate is below 0.05",
    "reject identity-specific causal support when the scene bootstrap lower bound is not above zero",
    "report secondary controls as descriptive when class_matched_selector or target_objectness is unavailable",
    "never treat this diagnostic as admission, efficacy, population, novelty, or deployable evidence",
]


def normalize_class(value):
    return "".join(
        character
        for character in str(value or "").strip().lower()
        if character.isalnum()
    )


def stable_key(scene_id, ann_id):
    payload = "%s|%s|%s" % (SELECTION_SALT, scene_id, int(ann_id))
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def select_stratum(records, limit):
    selected = []
    scene_counts = Counter()
    class_counts = Counter()
    ordered = sorted(
        records,
        key=lambda record: (
            stable_key(record["scene_id"], record["ann_id"]),
            record["scene_id"],
            int(record["ann_id"]),
        ),
    )
    for record in ordered:
        scene_id = str(record["scene_id"])
        class_name = str(record["target_class"])
        if (
            scene_counts[scene_id] >= MAX_EXPRESSIONS_PER_SCENE_PER_STRATUM
            or class_counts[class_name]
            >= MAX_EXPRESSIONS_PER_CLASS_PER_STRATUM
        ):
            continue
        selected.append(record)
        scene_counts[scene_id] += 1
        class_counts[class_name] += 1
        if len(selected) == limit:
            break
    if len(selected) != limit:
        raise ValueError("Insufficient metadata for one cohort stratum")
    return selected


def build_manifest(records, source_hashes, generated_at, per_stratum=128):
    if source_hashes != EXPECTED_SOURCE_SHA256:
        raise ValueError("Native source hash differs from the frozen contract")
    if not records:
        raise ValueError("No native expression metadata")
    by_stratum = defaultdict(list)
    seen = set()
    for raw in records:
        record = dict(raw)
        key = (str(record["scene_id"]), int(record["ann_id"]))
        if key in seen:
            raise ValueError("Duplicate native expression")
        seen.add(key)
        class_name = normalize_class(record["target_class"])
        peers = sorted(str(value) for value in record["same_class_peer_object_ids"])
        if str(record["target_object_id"]) in peers:
            raise ValueError("Target appears in its same-class peer list")
        expected_stratum = "ambiguous" if peers else "class_unique"
        if record["stratum"] != expected_stratum:
            raise ValueError("Incorrect static stratum")
        record["target_class"] = class_name
        record["same_class_peer_object_ids"] = peers
        record["same_class_peer_count"] = len(peers)
        by_stratum[expected_stratum].append(record)
    ambiguous = select_stratum(by_stratum["ambiguous"], per_stratum)
    class_unique = select_stratum(by_stratum["class_unique"], per_stratum)
    rows = sorted(
        ambiguous + class_unique,
        key=lambda row: (
            row["stratum"],
            stable_key(row["scene_id"], row["ann_id"]),
            row["scene_id"],
            int(row["ann_id"]),
        ),
    )
    for index, row in enumerate(rows):
        row["manifest_index"] = index
    return {
        "schema_version": 1,
        "contract": CONTRACT,
        "generated_at": generated_at,
        "selection": {
            "seed": SELECTION_SEED,
            "salt": SELECTION_SALT,
            "outcome_independent": True,
            "expression_order": (
                "SHA256(salt|scene_id|ann_id), then scene_id, then ann_id"
            ),
            "expressions_per_stratum": per_stratum,
            "max_expressions_per_scene_per_stratum": (
                MAX_EXPRESSIONS_PER_SCENE_PER_STRATUM
            ),
            "max_expressions_per_class_per_stratum": (
                MAX_EXPRESSIONS_PER_CLASS_PER_STRATUM
            ),
            "strata": {
                "ambiguous": (
                    "target has at least one same-class non-target object_id "
                    "in the scene"
                ),
                "class_unique": (
                    "target is the only object_id with that ScanRefer "
                    "object_name in the scene"
                ),
            },
        },
        "native_sources": source_hashes,
        "controls": CONTROL_CONTRACT,
        "primary_estimand": PRIMARY_ESTIMAND,
        "rejection_criteria": REJECTION_CRITERIA,
        "summary": {
            "source_expressions": len(records),
            "eligible_ambiguous": len(by_stratum["ambiguous"]),
            "eligible_class_unique": len(by_stratum["class_unique"]),
            "selected_expressions": len(rows),
            "selected_ambiguous": len(ambiguous),
            "selected_class_unique": len(class_unique),
            "selected_scenes": len({row["scene_id"] for row in rows}),
            "selected_classes": len({row["target_class"] for row in rows}),
        },
        "rows": rows,
    }


def validate_manifest(document):
    if document.get("contract") != CONTRACT:
        raise ValueError("Wrong manifest contract")
    rows = document.get("rows")
    if not isinstance(rows, list):
        raise ValueError("Manifest rows must be a list")
    expected = 2 * EXPRESSIONS_PER_STRATUM
    if len(rows) != expected:
        raise ValueError("Expected %d manifest rows" % expected)
    keys = [
        (row["stratum"], row["scene_id"], int(row["ann_id"]))
        for row in rows
    ]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate manifest expression")
    if [row["manifest_index"] for row in rows] != list(range(len(rows))):
        raise ValueError("Manifest indices are not contiguous")
    if Counter(row["stratum"] for row in rows) != {
        "ambiguous": EXPRESSIONS_PER_STRATUM,
        "class_unique": EXPRESSIONS_PER_STRATUM,
    }:
        raise ValueError("Manifest strata are not balanced")
    forbidden = {"score", "scores", "iou", "ious", "selected_query", "success"}
    for row in rows:
        overlap = forbidden.intersection(row)
        if overlap:
            raise ValueError(
                "Manifest contains outcome fields: " + ",".join(sorted(overlap))
            )
    return True


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_remote_records():
    encoded = base64.b64encode(REMOTE_CODE.encode("utf-8")).decode("ascii")
    remote_command = (
        "python3 -c \"import base64;exec(base64.b64decode('%s'))\"" % encoded
    )
    completed = subprocess.run(
        ["ssh", "server-6", remote_command],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    generated_at = args.generated_at or datetime.now().astimezone().isoformat()
    native = collect_remote_records()
    source_hashes = {
        name: source["sha256"]
        for name, source in native["sources"].items()
    }
    document = build_manifest(
        native["records"], source_hashes, generated_at, EXPRESSIONS_PER_STRATUM
    )
    document["native_sources"] = native["sources"]
    validate_manifest(document)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(document, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="ascii",
    )
    manifest_sha256 = file_sha256(MANIFEST_PATH)
    report = {
        "schema_version": 1,
        "contract": "m95_preregistered_manifest_receipt_v1",
        "generated_at": generated_at,
        "scope": (
            "Outcome-independent native ScanRefer metadata cohort and control "
            "contract. No model forward, GPU work, queue mutation, admission, "
            "sync, or training action."
        ),
        "manifest": {
            "path": MANIFEST_PATH.relative_to(ROOT).as_posix(),
            "sha256": manifest_sha256,
            "rows": len(document["rows"]),
            "contract": document["contract"],
        },
        "native_sources": native["sources"],
        "summary": document["summary"],
        "execution_state": {
            "capture_ready": True,
            "capture_executed": False,
            "blocker": (
                "server-6 GPU7 is occupied by a foreign 100%-utilization "
                "process; do not evict it"
            ),
            "next_action": (
                "when GPU7 has a safe project slot, adapt the frozen capture "
                "producer to select exactly this manifest and emit raw query "
                "masks, query scores, native-positive flags, FPS-seed support, "
                "physical instance labels, and the manifest hash"
            ),
        },
        "not_evidence_of": [
            "admission",
            "deployable efficacy",
            "population effect",
            "novelty",
            "referent-specific causality",
            "a deployable mechanism",
        ],
    }
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="ascii",
    )
    print(json.dumps(report["summary"], sort_keys=True))
    print("manifest_sha256=" + manifest_sha256)


if __name__ == "__main__":
    main()
