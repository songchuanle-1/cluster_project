"""Audit exact matched-control availability for the observed referent failures.

This is a CPU-only metadata and dataset-order audit. It does not load a model,
use a GPU, modify candidate state, or make an efficacy claim.
"""
import argparse
import hashlib
import json
import logging
import os
from pathlib import Path
import sys
from collections import defaultdict

FAILURE_OBSERVATIONS = [
    ("scene0493_00", 3, "4"),
    ("scene0481_00", 0, "48"),
    ("scene0481_00", 1, "48"),
    ("scene0481_00", 3, "48"),
    ("scene0288_00", 0, "38"),
    ("scene0288_00", 3, "24"),
    ("scene0289_00", 0, "17"),
    ("scene0289_00", 1, "16"),
    ("scene0289_00", 2, "16"),
    ("scene0220_00", 1, "4"),
    ("scene0076_00", 0, "10"),
    ("scene0076_00", 1, "6"),
    ("scene0421_00", 1, "59"),
    ("scene0421_00", 2, "11"),
    ("scene0223_00", 0, "19"),
    ("scene0223_00", 1, "18"),
    ("scene0319_00", 1, "3"),
    ("scene0319_00", 2, "20"),
    ("scene0192_00", 2, "4"),
    ("scene0110_00", 0, "18"),
    ("scene0110_00", 3, "18"),
    ("scene0632_00", 3, "2"),
    ("scene0420_00", 1, "40"),
    ("scene0420_00", 2, "6"),
    ("scene0416_00", 0, "26"),
    ("scene0416_00", 2, "42"),
    ("scene0320_00", 1, "31"),
    ("scene0320_00", 3, "18"),
    ("scene0452_00", 0, "23"),
    ("scene0452_00", 3, "20"),
    ("scene0588_00", 1, "30"),
    ("scene0588_00", 2, "1"),
    ("scene0588_00", 3, "20"),
]
FAILURE_KEYS = [row[:2] for row in FAILURE_OBSERVATIONS]


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalized_name(value):
    return str(value).strip().lower()


def annotation_indices(records):
    by_scene_ann = {}
    by_scene_object = {}
    by_scene = defaultdict(list)
    for record in records:
        scene = str(record["scene_id"])
        ann_id = str(record["ann_id"])
        object_id = str(record["object_id"])
        key = (scene, ann_id)
        if key in by_scene_ann:
            raise ValueError("Duplicate scene/ann_id in ScanRefer metadata")
        by_scene_ann[key] = record
        by_scene_object.setdefault((scene, object_id), []).append(record)
        by_scene[scene].append(record)
    return by_scene_ann, by_scene_object, dict(by_scene)


def target_node(graph, object_name):
    candidates = [
        node for node in graph["graph_node"]
        if node.get("node_type") == "Object"
        and normalized_name(node.get("lemma_head", node.get("target")))
        == normalized_name(object_name)
    ]
    if len(candidates) != 1:
        candidates = [
            node for node in graph["graph_node"]
            if node.get("node_type") == "Object" and int(node.get("node_id", -1)) == 0
        ]
    if len(candidates) != 1:
        raise ValueError("Expected one graph root matching the target object")
    return candidates[0]


def control_features(record, graph, scene_objects):
    object_id = str(record["object_id"])
    name = normalized_name(record["object_name"])
    same_class = [
        other for other in scene_objects
        if str(other["object_id"]) != object_id
        and normalized_name(other["object_name"]) == name
    ]
    if graph is None:
        return {
            "graph_available": False,
            "same_class_peer": bool(same_class),
            "same_class_peer_ids": sorted({
                str(row["object_id"]) for row in same_class
            }),
            "graph_same_class_peer": False,
            "target_has_relation_edge": False,
            "connected_same_class_peer": False,
            "connected_same_class_target": [],
            "target_has_attribute": False,
            "target_has_relation_span": False,
            "incident_relations": [],
        }
    target = target_node(graph, record["object_name"])
    target_idx = int(target["node_id"])
    target_name = normalized_name(target.get("lemma_head", target.get("target")))
    graph_peers = [
        node for node in graph["graph_node"]
        if node.get("node_type") == "Object"
        and int(node["node_id"]) != target_idx
        and normalized_name(node.get("lemma_head", node.get("target")))
        == target_name
    ]
    incident = [
        edge for edge in graph["graph_edge"]
        if int(edge["sub_idx"]) == target_idx or int(edge["obj_idx"]) == target_idx
    ]
    direct_indices = {
        int(edge["obj_idx"]) if int(edge["sub_idx"]) == target_idx
        else int(edge["sub_idx"])
        for edge in incident
    }
    connected_same_class = [
        node for node in graph_peers if int(node["node_id"]) in direct_indices
    ]
    return {
        "graph_available": True,
        "same_class_peer": bool(same_class),
        "same_class_peer_ids": sorted({str(row["object_id"]) for row in same_class}),
        "graph_same_class_peer": bool(graph_peers),
        "target_has_relation_edge": bool(incident),
        "connected_same_class_peer": bool(connected_same_class),
        "connected_same_class_target": [
            str(node.get("lemma_head", node.get("target")))
            for node in connected_same_class
        ],
        "target_has_attribute": bool(target.get("mod_text")),
        "target_has_relation_span": bool(target.get("rel_char_span")),
        "incident_relations": sorted({str(edge["relation"]) for edge in incident}),
    }


def wrong_instance_features(target_record, wrong_object_id, graph, scene_objects):
    wrong_records = [
        row for row in scene_objects
        if str(row["object_id"]) == str(wrong_object_id)
    ]
    if not wrong_records:
        raise ValueError("Observed wrong instance absent from scene annotations")
    wrong_record = wrong_records[0]
    same_class = (
        normalized_name(wrong_record["object_name"])
        == normalized_name(target_record["object_name"])
    )
    graph_connected = False
    if graph is not None:
        target = target_node(graph, target_record["object_name"])
        target_idx = int(target["node_id"])
        peer = [
            node for node in graph["graph_node"]
            if node.get("node_type") == "Object"
            and int(node["node_id"]) != target_idx
            and normalized_name(node.get("lemma_head", node.get("target")))
            == normalized_name(wrong_record["object_name"])
        ]
        incident_indices = set()
        for edge in graph["graph_edge"]:
            if int(edge["sub_idx"]) == target_idx:
                incident_indices.add(int(edge["obj_idx"]))
            if int(edge["obj_idx"]) == target_idx:
                incident_indices.add(int(edge["sub_idx"]))
        graph_connected = any(
            int(node["node_id"]) in incident_indices for node in peer
        )
    return {
        "wrong_object_id": str(wrong_object_id),
        "wrong_object_name": str(wrong_record["object_name"]),
        "wrong_is_same_class": same_class,
        "wrong_graph_connected": graph_connected,
    }


def summarize(rows):
    count = len(rows)
    keys = (
        "graph_available",
        "same_class_peer",
        "graph_same_class_peer",
        "target_has_relation_edge",
        "connected_same_class_peer",
        "target_has_attribute",
        "target_has_relation_span",
        "same_target_repeated",
    )
    summary = {"expressions": count}
    for key in keys:
        passed = sum(bool(row.get(key, False)) for row in rows)
        summary[key] = {
            "count": passed,
            "rate": passed / count if count else None,
        }
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--train-annotations", required=True)
    parser.add_argument("--val-annotations", required=True)
    parser.add_argument("--train-graphs", required=True)
    parser.add_argument("--val-graphs", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--batches", type=int, default=16)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    os.environ.update(
        CUDA_VISIBLE_DEVICES="",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        TOKENIZERS_PARALLELISM="false",
    )
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import gorilla
    from framework.dataset import build_dataset, build_dataloader

    train_records = json.loads(Path(args.train_annotations).read_text())
    val_records = json.loads(Path(args.val_annotations).read_text())
    train_graphs = json.loads(Path(args.train_graphs).read_text())
    val_graphs = json.loads(Path(args.val_graphs).read_text())
    train_by_ann, train_by_object, train_by_scene = annotation_indices(train_records)
    val_by_ann, val_by_object, val_by_scene = annotation_indices(val_records)

    config = root / (
        "configs/Quard/ctf_hcg_csort/"
        "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.yaml"
    )
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("control-audit"))
    loader = build_dataloader(
        dataset,
        batch_size=2,
        num_workers=0,
        persistent_workers=False,
    )

    sample_rows = []
    for step, batch in enumerate(loader):
        scenes = [
            scene
            for scene, count in zip(batch["scan_ids"], batch["scenes_len"])
            for _ in range(int(count))
        ]
        slots = [
            slot
            for count in batch["scenes_len"]
            for slot in range(int(count))
        ]
        ann_ids = [str(value) for value in batch["ann_ids"]]
        if not (len(scenes) == len(slots) == len(ann_ids)):
            raise ValueError("Dataset expression axes differ")
        for scene, slot, ann_id in zip(scenes, slots, ann_ids):
            record = train_by_ann[(str(scene), ann_id)]
            scene_objects = train_by_scene[str(scene)]
            graph = train_graphs.get(str(scene), {}).get(str(record["object_id"]))
            features = control_features(record, graph, scene_objects)
            repeats = train_by_object[(str(scene), str(record["object_id"]))]
            sample_rows.append({
                "step": step,
                "scene": str(scene),
                "expression_slot": int(slot),
                "ann_id": ann_id,
                "object_id": str(record["object_id"]),
                "object_name": str(record["object_name"]),
                "same_target_repeated": len(repeats) > 1,
                "same_target_descriptions": len(repeats),
                **features,
            })
        if step + 1 >= args.batches:
            break

    sample_by_key = {
        (row["scene"], row["expression_slot"]): row for row in sample_rows
    }
    missing = [key for key in FAILURE_KEYS if key not in sample_by_key]
    if missing:
        raise ValueError("Observed failures absent from reproduced sample: %r" % missing)
    failure_rows = [sample_by_key[key] for key in FAILURE_KEYS]
    for row, (_, _, wrong_object_id) in zip(failure_rows, FAILURE_OBSERVATIONS):
        row.update(wrong_instance_features(
            train_by_ann[(row["scene"], row["ann_id"])],
            wrong_object_id,
            train_graphs.get(row["scene"], {}).get(row["object_id"]),
            train_by_scene[row["scene"]],
        ))
    wrong_same_class = sum(row["wrong_is_same_class"] for row in failure_rows)
    wrong_connected = sum(row["wrong_graph_connected"] for row in failure_rows)
    failure_rows_summary = summarize(failure_rows)
    failure_rows_summary["wrong_is_same_class"] = {
        "count": wrong_same_class,
        "rate": wrong_same_class / len(failure_rows),
    }
    failure_rows_summary["wrong_graph_connected"] = {
        "count": wrong_connected,
        "rate": wrong_connected / len(failure_rows),
    }

    def coverage(by_ann, by_object, by_scene, graph_source):
        rows = []
        for (scene, ann_id), record in by_ann.items():
            scene_objects = by_scene[scene]
            graph = graph_source.get(scene, {}).get(str(record["object_id"]))
            features = control_features(record, graph, scene_objects)
            repeats = by_object[(scene, str(record["object_id"]))]
            rows.append({
                "scene": scene,
                "ann_id": ann_id,
                "same_target_repeated": len(repeats) > 1,
                **features,
            })
        return rows

    train_rows = coverage(
        train_by_ann,
        train_by_object,
        train_by_scene,
        train_graphs,
    )
    val_rows = coverage(
        val_by_ann,
        val_by_object,
        val_by_scene,
        val_graphs,
    )

    report = {
        "scope": (
            "CPU-only ScanRefer metadata audit of exact same-class and "
            "relation-connected control availability; no model forward, GPU "
            "execution, admission, or efficacy claim"
        ),
        "producer_sha256": file_sha256(__file__),
        "source_sha256": {
            str(Path(args.train_annotations)): file_sha256(args.train_annotations),
            str(Path(args.val_annotations)): file_sha256(args.val_annotations),
            str(Path(args.train_graphs)): file_sha256(args.train_graphs),
            str(Path(args.val_graphs)): file_sha256(args.val_graphs),
            str(config): file_sha256(config),
        },
        "sample": {
            "batches": min(args.batches, step + 1),
            "expressions": len(sample_rows),
            "failure_keys_matched": len(failure_rows),
            "failure_key_match_rate": len(failure_rows) / len(FAILURE_KEYS),
        },
        "observed_failure_coverage": {
            "summary": failure_rows_summary,
            "rows": failure_rows,
        },
        "train_metadata_coverage": summarize(train_rows),
        "val_metadata_coverage": summarize(val_rows),
        "design_consequence": {
            "admissible_unpaired": [
                "same-class wrong-object controls when same_class_peer is true",
                "same-target repeated-description controls when same_target_repeated is true",
            ],
            "admissible_connected": [
                "same-class wrong-object controls sharing a direct target relation"
            ],
            "not_established": [
                "physical mask quality or native feature identity",
                "causal effect of relation context on referent selection",
                "that a metadata-connected peer is a model-confusable hard negative",
            ],
        },
        "limitations": [
            "ScanRefer object names and scene-graph edges are language annotations, "
            "not native 3D instance geometry.",
            "The reproduced first-16-batch order is fixed by the archived seed and "
            "configuration; it is a diagnostic sample, not the full training set.",
            "Same-class peer availability does not establish that the peer is present "
            "in the model's candidate query set or is geometrically confusable.",
            "The audit produces a matched-control registry only; it does not reopen a "
            "closed mechanism family or admit a training candidate.",
        ],
    }
    Path(args.output).write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="ascii",
    )
    print(json.dumps({
        "expressions": len(sample_rows),
        "failure_expressions": len(failure_rows),
        "failure_summary": report["observed_failure_coverage"]["summary"],
        "train_summary": report["train_metadata_coverage"],
        "val_summary": report["val_metadata_coverage"],
    }, indent=2))


if __name__ == "__main__":
    main()
