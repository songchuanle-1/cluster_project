"""Manifest-bound M95 capture for the pre-registered identity controls.

This producer does not change training code, model code, or control semantics.
It scans native TRAIN items until exactly the frozen manifest expressions have
been observed, then persists the complete query-side evidence needed by the
pre-registered analysis.
"""
import argparse
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import sys

from capture_support_20260916 import bind_queries, plain, support_record
from frozen_capture_contract_20260916 import file_sha256, model_package_sha256
from hierarchical_partition_contract_20260916 import (
    partition_rows_from_observations,
)
from native_endpoint_capture_20260916 import EndpointDataset, enrich_row
from native_frozen_capture_20260916 import FrozenDataset
from native_partition_boundary_capture_20260925 import observe_partition
from m95_match_cause_contract_20260923 import check_row


MANIFEST_CONTRACT = "m95_preregistered_identity_controls_v1"
MANIFEST_ROWS = 256
FORBIDDEN_OUTCOME_FIELDS = {
    "score",
    "scores",
    "iou",
    "ious",
    "selected_query",
    "success",
}


def _manifest_key(scene, ann_id):
    return str(scene), int(ann_id)


class ManifestRows:
    def __init__(self, document, manifest_sha256):
        if document.get("contract") != MANIFEST_CONTRACT:
            raise ValueError("Wrong manifest contract")
        if len(str(manifest_sha256)) != 64:
            raise ValueError("Manifest SHA256 required")
        int(manifest_sha256, 16)
        rows = document.get("rows")
        if not isinstance(rows, list) or len(rows) != MANIFEST_ROWS:
            raise ValueError("Expected %d manifest rows" % MANIFEST_ROWS)
        self.document = document
        self.sha256 = manifest_sha256
        self.rows = {}
        for expected_index, raw in enumerate(rows):
            if int(raw.get("manifest_index", -1)) != expected_index:
                raise ValueError("Manifest indices are not contiguous")
            if FORBIDDEN_OUTCOME_FIELDS.intersection(raw):
                raise ValueError("Manifest contains model outcome fields")
            key = _manifest_key(raw.get("scene_id"), raw.get("ann_id"))
            if key in self.rows:
                raise ValueError("Duplicate manifest expression")
            row = dict(raw)
            row["scene_id"], row["ann_id"] = key
            self.rows[key] = row

    def get(self, scene, ann_id):
        return self.rows.get(_manifest_key(scene, ann_id))

    def require_complete(self, found):
        missing = sorted(set(self.rows) - set(found))
        if missing:
            raise ValueError(
                "Manifest capture missing %d expressions; first=%s"
                % (len(missing), missing[0])
            )
        unexpected = sorted(set(found) - set(self.rows))
        if unexpected:
            raise ValueError("Manifest capture has unexpected expressions")
        if len(found) != len(self.rows):
            raise ValueError("Manifest capture row count differs")


class ManifestSubset:
    """Restrict a capture dataset to the scenes referenced by the manifest."""

    def __init__(self, dataset, indices):
        indices = [int(index) for index in indices]
        if not indices or len(set(indices)) != len(indices):
            raise ValueError("Manifest subset requires unique dataset indices")
        if any(index < 0 or index >= len(dataset) for index in indices):
            raise ValueError("Manifest subset index is outside the native dataset")
        self.dataset = dataset
        self.indices = indices

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, index):
        return self.dataset[self.indices[index]]

    def collate_fn(self, items):
        return self.dataset.collate_fn(items)


def load_manifest(path, expected_sha256):
    path = Path(path)
    payload = path.read_bytes()
    actual_sha256 = hashlib.sha256(payload).hexdigest()
    if actual_sha256 != expected_sha256:
        raise ValueError("Manifest hash differs from the frozen contract")
    document = json.loads(payload.decode("ascii"))
    return ManifestRows(document, actual_sha256)


def manifest_dataset_indices(dataset, manifest):
    """Map every frozen expression to its outcome-independent dataset index."""
    scene_inputs = getattr(dataset, "scene_inputs", None)
    if not isinstance(scene_inputs, list):
        raise ValueError("Native dataset lacks scene_inputs")
    wanted = set(manifest.rows)
    found = {}
    for dataset_index, annotations in enumerate(scene_inputs):
        for raw in annotations:
            key = _manifest_key(raw.get("scene_id"), raw.get("ann_id"))
            if key not in wanted:
                continue
            if key in found:
                raise ValueError("Manifest expression occurs in multiple scenes")
            found[key] = dataset_index
    missing = sorted(wanted - set(found))
    if missing:
        raise ValueError("Manifest expression absent from native dataset")
    return [found[key] for key in sorted(found, key=lambda key: found[key])]


def selected_axes(axes, manifest):
    selected = []
    for index, axis in enumerate(axes):
        row = manifest.get(axis.get("scene"), axis.get("ann_id"))
        if row is not None:
            selected.append((index, row))
    return selected


def matcher_cause_record(sampled_pos, obj_pos, labels, object_ids,
                         matcher_result, native_positive):
    nearest, members, matched, _ = matcher_result
    row = dict(
        sampled_pos=plain(sampled_pos),
        obj_pos=plain(obj_pos),
        sampled_instance_labels=plain(labels),
        object_ids=[int(value) for value in object_ids],
        nearest_query_per_gt=plain(nearest),
        member_queries_per_gt=[plain(group) for group in members],
        native_positive=plain(native_positive),
    )
    counts = check_row(row)
    expected_pairs = [
        (int(q), int(gt)) for q, gt in zip(plain(matched[0]), plain(matched[1]))
    ]
    captured_pairs = (
        [(int(q), gt) for gt, q in enumerate(row["nearest_query_per_gt"])]
        + [(int(q), gt) for gt, group in enumerate(row["member_queries_per_gt"])
           for q in group]
    )
    if expected_pairs != captured_pairs:
        raise ValueError("Native matched pair order contradicts captured causes")
    row["matched_query_gt_pairs"] = [list(pair) for pair in expected_pairs]
    return row, counts


def native_matcher_cause_record(match_inputs, match_result, native_positive):
    labels, object_ids, sampled_pos, obj_pos = match_inputs
    return matcher_cause_record(
        sampled_pos, obj_pos, labels, object_ids, match_result, native_positive
    )


def identity_query_record(query, pred, batch_index, seed_indices, fps_indices,
                          native_scores, score_head):
    import torch

    seeds = identity_query_binding(
        query.shape, pred["indis"].shape, batch_index, seed_indices,
        fps_indices, len(native_scores),
    )
    if not torch.isfinite(query).all():
        raise ValueError("Nonfinite native query state")
    if not torch.allclose(score_head(query), pred["indis"], atol=1e-5, rtol=1e-5):
        raise ValueError("Captured query state does not reproduce indicator logits")
    return {
        "query_states": query[batch_index].detach().cpu(),
        "sampled_seed_indices": [int(index) for index in seed_indices],
        "sampled_superpoint_ids": seeds,
    }


def identity_query_binding(query_shape, indicator_shape, batch_index,
                           seed_indices, fps_indices, score_count):
    if len(query_shape) != 3 or len(indicator_shape) != 3:
        raise ValueError("Native query and indicator axes must be batched")
    if tuple(query_shape[:2]) != tuple(indicator_shape[:2]):
        raise ValueError("Query state differs from native indicator axis")
    if batch_index < 0 or batch_index >= query_shape[0]:
        raise ValueError("Query batch index differs")
    count = query_shape[1]
    if len(seed_indices) != count or score_count != count:
        raise ValueError("Query state differs from sampled seed or score axis")
    if any(type(index) is not int or index < 0 or index >= len(fps_indices)
           for index in seed_indices):
        raise ValueError("Invalid sampled seed index")
    return [int(fps_indices[index]) for index in seed_indices]


def manifest_artifact_entry(axis, row, features, mask_logits, masks, scores,
                           native_positive, seed_inside, instance_labels,
                           target, manifest_sha256, identity_query=None):
    support_record(axis["original_superpoint_ids"], axis["sample_inverse"])
    support_size = len(axis["original_superpoint_ids"])
    semantic_values = plain(axis["semantic_labels"])
    label_values = plain(instance_labels)
    if len(semantic_values) != support_size:
        raise ValueError("Semantic labels differ from captured support")
    if len(label_values) != support_size:
        raise ValueError("Physical labels differ from captured support")
    query_vectors = {
        "mask logits": mask_logits,
        "masks": masks,
        "scores": scores,
        "native positives": native_positive,
        "seed support": seed_inside,
    }
    query_count = len(scores)
    if query_count == 0 or any(len(value) != query_count
                               for value in query_vectors.values()):
        raise ValueError("Artifact query axes differ")
    for name in ("mask logits", "masks"):
        value = query_vectors[name]
        shape = getattr(value, "shape", None)
        if shape is not None:
            valid_width = len(shape) == 2 and int(shape[1]) == support_size
        else:
            valid_width = (
                isinstance(value, (list, tuple))
                and all(len(row) == support_size for row in value)
            )
        if not valid_width:
            raise ValueError("Artifact mask support differs")
    artifact = dict(
        manifest_index=int(row["manifest_index"]),
        manifest_sha256=manifest_sha256,
        axis=axis,
        features=features,
        query_mask_logits=mask_logits,
        query_masks=masks,
        query_scores=scores,
        native_positive=native_positive,
        fps_seed_inside_target=seed_inside,
        physical_instance_labels=instance_labels,
        semantic_labels=semantic_values,
        target_union=target,
        artifact_contract="m95_manifest_native_query_artifact_v1",
    )
    if identity_query is not None:
        artifact["identity_query"] = identity_query
    return artifact


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--model-class",
        default="model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort",
    )
    parser.add_argument("--config")
    parser.add_argument("--max-batches", type=int, default=0)
    parser.add_argument("--manifest-only", action="store_true")
    parser.add_argument("--capture-match-causes", action="store_true")
    parser.add_argument("--capture-identity-query", action="store_true")
    parser.add_argument("--capture-partition-boundary", action="store_true")
    return parser.parse_args()


def main():
    args = _parse_args()
    if args.max_batches < 0:
        raise ValueError("Maximum batch count must be nonnegative")
    if args.capture_identity_query and not args.capture_match_causes:
        raise ValueError("Identity query capture requires native matcher coordinates")
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "7":
        raise ValueError("Authorized physical GPU7 required")
    manifest = load_manifest(args.manifest, args.expected_manifest_sha256)
    import torch

    root = Path(args.root).resolve()
    out = Path(args.output).resolve()
    manifest_path = Path(args.manifest).resolve()
    if not out.is_relative_to(root.parent / "pipeline") or out.exists():
        raise ValueError("Require a new project-local output directory")
    os.environ.update(
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        TOKENIZERS_PARALLELISM="false",
    )
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import gorilla
    from framework.dataset import build_dataset, build_dataloader

    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.15)
    name = args.model_class
    if name != "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort":
        raise ValueError("Only the exact M95 model class is bound")
    if args.config:
        config = Path(args.config)
        if not config.is_absolute():
            config = root / config
    else:
        config = (
            root
            / "configs/Quard/ctf_hcg_csort"
            / (name + ".yaml")
        )
    config = config.resolve()
    if not config.is_relative_to(root) or not config.is_file():
        raise ValueError("Config must be a project-local file")

    producer_files = [
        Path(__file__).resolve(),
        Path(__file__).with_name("m95_match_cause_contract_20260923.py"),
        Path(__file__).with_name("native_frozen_capture_20260916.py"),
        Path(__file__).with_name("frozen_capture_contract_20260916.py"),
        Path(__file__).with_name("hierarchical_partition_contract_20260916.py"),
        Path(__file__).with_name("native_endpoint_capture_20260916.py"),
        Path(__file__).with_name("native_support_capture_v2_20260916.py"),
        Path(__file__).with_name("capture_support_20260916.py"),
        Path(__file__).with_name("physical_mask_endpoints_20260916.py"),
    ]
    if args.capture_partition_boundary:
        producer_files.extend([
            Path(__file__).with_name("native_partition_boundary_capture_20260925.py"),
            Path(__file__).with_name("m95_partition_boundary_probe_20260925.py"),
        ])
    producer_sha256 = hashlib.sha256(
        b"".join(path.read_bytes() for path in producer_files)
    ).hexdigest()
    checkpoint_sha256 = file_sha256(args.checkpoint)
    model_source_sha256 = model_package_sha256(root, name)

    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = (
        "/data3/songcl/data/data_cluster/"
    )
    gorilla.set_random_seed(1999)
    FrozenDataset.checkpoint_sha256 = checkpoint_sha256
    source_dataset = build_dataset(
        cfg.data.train, logging.getLogger("manifest_capture")
    )
    dataset = FrozenDataset(
        source_dataset,
        out.name,
        producer_sha256,
    )
    if args.manifest_only:
        dataset = ManifestSubset(
            dataset, manifest_dataset_indices(source_dataset, manifest)
        )
    loader = build_dataloader(
        dataset,
        batch_size=2,
        num_workers=0,
        persistent_workers=False,
    )
    model = importlib.import_module(
        "framework.model.Quard_model." + name
    ).Network(**cfg.model)
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=False)[
        "model"
    ]
    for key in (
        "text_encoder.embeddings.position_ids",
        "text_encoder.embeddings.token_type_ids",
    ):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    del state
    model.cuda().eval()

    held, calls, handles, cause_calls = {}, [], [], []
    hierarchy_positions, hierarchy_outputs = [], []
    boundary_rows, batch_axes = {}, []

    def projection(tag):
        def hook(module, inputs, output):
            held["raw_" + tag] = inputs[0].detach()
            held["projected_" + tag] = output.detach()

        return hook

    handles.append(model.dec.input_proj.register_forward_hook(projection("3d")))
    handles.append(
        model.dec.input_proj_2d.register_forward_hook(projection("2d"))
    )
    handles.append(
        model.dec.sum_norm.register_forward_hook(
            lambda module, inputs, output: held.update(fused=output.detach())
        )
    )
    handles.append(
        model.dec.encoder_layers[-1].register_forward_hook(
            lambda module, inputs, output: held.update(final=output[1].detach())
        )
    )
    if args.capture_identity_query:
        handles.append(
            model.dec.decoder_layers[-1].register_forward_hook(
                lambda module, inputs, output: held.update(
                    identity_query=output[0].detach()
                )
            )
        )

    def criterion(module, inputs):
        held.update(
            pred=inputs[0],
            gt=inputs[1],
            objects=inputs[3],
            labels=inputs[4],
            fps=inputs[7],
            offsets=inputs[9],
        )

    handles.append(model.criterion.register_forward_pre_hook(criterion))
    partitioner = model.dec.cluster_bank.partitioner
    original_partition_points = partitioner.partition_points

    def partition_points(points_pos, fps_pos):
        call_index = len(hierarchy_positions)
        levels = len(model.dec.cluster_bank.cluster_layer_nums)
        batch_index, level = divmod(call_index, levels)
        selected = False
        if args.capture_partition_boundary and level == 0:
            if batch_index >= len(batch_axes):
                raise ValueError("Partition batch exceeds native expression axis")
            axis = batch_axes[batch_index]
            entry = manifest.get(axis["scene"], axis["ann_id"])
            selected = entry is not None and int(entry["manifest_index"]) in (83, 174)
        if selected:
            subsets, observation = observe_partition(
                torch, original_partition_points, points_pos, fps_pos, 344
            )
            boundary_rows[batch_index] = observation
        else:
            subsets = original_partition_points(points_pos, fps_pos)
        hierarchy_positions.append(fps_pos.detach().cpu().tolist())
        return subsets

    partitioner.partition_points = partition_points
    handles.append(
        partitioner.register_forward_hook(
            lambda module, inputs, output: hierarchy_outputs.append(output)
        )
    )
    native_match = model.criterion.match_sampled_ins

    def match(*inputs, **kwargs):
        result = native_match(*inputs, **kwargs)
        calls.append(result[2][0].detach())
        if args.capture_match_causes:
            cause_calls.append((inputs, result))
        return result

    model.criterion.match_sampled_ins = match

    out.mkdir(parents=True)
    rows, artifacts, found = [], [], {}
    try:
        with torch.no_grad():
            for step, (batch, axes) in enumerate(loader):
                batch_axes = axes
                held.clear()
                calls.clear()
                cause_calls.clear()
                hierarchy_positions.clear()
                hierarchy_outputs.clear()
                boundary_rows.clear()
                gorilla.set_random_seed(1999)
                loss, _ = model(batch, mode="loss")
                if not bool(torch.isfinite(loss).all()):
                    raise ValueError("Nonfinite native loss")
                pred = held["pred"]
                if len(axes) != len(pred["masks"]):
                    raise ValueError("Expression output axis differs")
                nonempty = [
                    b for b, ids in enumerate(held["objects"]) if len(ids)
                ]
                if len(calls) != 2 * len(nonempty):
                    raise ValueError("Unexpected native matcher call structure")
                if args.capture_match_causes and len(cause_calls) != len(calls):
                    raise ValueError("Incomplete native matcher-cause capture")
                if len(hierarchy_outputs) != 1:
                    raise ValueError("Unexpected hierarchical partition structure")
                if len(hierarchy_positions) != (
                    len(axes) * len(model.dec.cluster_bank.cluster_layer_nums)
                ):
                    raise ValueError("Partition call count differs from batch axis")
                raw_cluster_ids, raw_child_maps = hierarchy_outputs[0]
                cluster_ids = [
                    [value.detach().cpu().tolist() for value in level]
                    for level in raw_cluster_ids
                ]
                child_maps = [[value for value in level] for level in raw_child_maps]
                hierarchy_rows = partition_rows_from_observations(
                    hierarchy_positions,
                    cluster_ids,
                    child_maps,
                    [len(axis["original_superpoint_ids"]) for axis in axes],
                    len(model.dec.cluster_bank.cluster_layer_nums),
                )
                positive_ids = {
                    b: calls[2 * i + 1] for i, b in enumerate(nonempty)
                }
                features = {}
                for tag in (
                    "raw_3d",
                    "raw_2d",
                    "projected_3d",
                    "projected_2d",
                    "fused",
                ):
                    features[tag] = model.dec.get_batches(
                        held[tag], held["offsets"]
                    )[0]
                features["final"] = held["final"]
                artifact_entries = []
                for b, axis in enumerate(axes):
                    manifest_row = manifest.get(axis["scene"], axis["ann_id"])
                    if manifest_row is None:
                        continue
                    key = _manifest_key(axis["scene"], axis["ann_id"])
                    if key in found:
                        raise ValueError("Duplicate native expression in capture")
                    labels = held["labels"][b].long().reshape(-1)
                    target = held["gt"][b].reshape(-1).bool()
                    n = len(axis["original_superpoint_ids"])
                    if len(labels) != n or len(target) != n:
                        raise ValueError("Native target/instance support differs")
                    if int((~pred["batch_mask"][b]).sum()) != n:
                        raise ValueError("Native valid mask differs from support")
                    mask_logits = pred["masks"][b, :, :n]
                    masks = mask_logits > 0
                    ious = (
                        (masks & target).sum(-1).float()
                        / (masks | target).sum(-1).clamp_min(1)
                    )
                    scores = pred["indis"][b].softmax(-1)[:, 1]
                    positive = torch.zeros_like(scores, dtype=torch.bool)
                    if b in positive_ids:
                        positive[positive_ids[b]] = True
                    seeds = held["fps"][b][pred["sample_inds"][b]].long()
                    seed_inside = target[seeds]
                    row = bind_queries(
                        axis,
                        scores.cpu(),
                        ious.cpu(),
                        seed_inside.cpu(),
                        positive.cpu(),
                        labels.cpu(),
                    )
                    if row["selected_query"] != int(scores.argmax()):
                        raise ValueError("Static/native argmax tie mismatch")
                    row.update(
                        step=step,
                        target_instances=[
                            int(value) for value in held["objects"][b]
                        ],
                        target_superpoints=int(target.sum()),
                        fps_superpoints=held["fps"][b].cpu().tolist(),
                        sampled_seed_indices=pred["sample_inds"][b]
                        .cpu()
                        .tolist(),
                        manifest_index=int(manifest_row["manifest_index"]),
                        manifest_sha256=manifest.sha256,
                        stratum=manifest_row["stratum"],
                        target_object_id=str(
                            manifest_row["target_object_id"]
                        ),
                        target_class=manifest_row["target_class"],
                        same_class_peer_object_ids=list(
                            manifest_row["same_class_peer_object_ids"]
                        ),
                        description_sha256=manifest_row["description_sha256"],
                        query_mask_contract=(
                            "boolean pred.masks > 0 before selected-query "
                            "endpoint truncation"
                        ),
                    )
                    row.update(hierarchy_rows[b])
                    if b in boundary_rows:
                        if int(row["hierarchical_cluster_ids"][0][344]) != (
                            boundary_rows[b]["recorded_assignment"]
                        ):
                            raise ValueError("Boundary and hierarchy assignment differ")
                        row["partition_boundary_point344"] = boundary_rows[b]
                    elif args.capture_partition_boundary and (
                        int(row["manifest_index"]) in (83, 174)
                    ):
                        raise ValueError("Missing native partition boundary")
                    if args.capture_match_causes and b not in positive_ids:
                        raise ValueError("Manifest expression lacks native matcher call")
                    if args.capture_match_causes:
                        i = nonempty.index(b)
                        match_inputs, match_result = cause_calls[2 * i + 1]
                        cause, counts = native_matcher_cause_record(
                            match_inputs, match_result, positive
                        )
                        row["native_match_cause"] = cause
                        row["native_match_cause_counts"] = counts
                    identity_query = None
                    if args.capture_identity_query:
                        identity_query = identity_query_record(
                            held["identity_query"], pred, b,
                            row["sampled_seed_indices"],
                            row["fps_superpoints"], scores,
                            model.dec.decoder_layers[-1].indi_embedding,
                        )
                        if identity_query["sampled_superpoint_ids"] != [
                            int(value) for value in seeds.cpu().tolist()
                        ]:
                            raise ValueError("Native physical seed binding differs")
                        if len(cause["sampled_pos"]) != len(
                            identity_query["query_states"]
                        ):
                            raise ValueError("Identity and criterion query axes differ")
                    enrich_row(row, masks[row["selected_query"]].cpu().tolist())
                    vectors = {
                        tag: value[b, :n].cpu()
                        for tag, value in features.items()
                    }
                    support_record(
                        row["original_superpoint_ids"], row["sample_inverse"]
                    )
                    artifact_entries.append(
                        manifest_artifact_entry(
                            axis,
                            manifest_row,
                            vectors,
                            mask_logits.cpu(),
                            masks.cpu(),
                            scores.cpu(),
                            positive.cpu(),
                            seed_inside.cpu(),
                            labels.cpu(),
                            target.cpu(),
                            manifest.sha256,
                            identity_query,
                        )
                    )
                    found[key] = int(manifest_row["manifest_index"])
                    rows.append(row)
                if artifact_entries:
                    artifact = out / ("manifest_selected_%03d.pt" % step)
                    torch.save(artifact_entries, artifact)
                    artifacts.append(
                        dict(
                            path=artifact.name,
                            sha256=hashlib.sha256(
                                artifact.read_bytes()
                            ).hexdigest(),
                            rows=len(artifact_entries),
                            step=step,
                        )
                    )
                print(
                    json.dumps(
                        dict(
                            step=step,
                            expressions=len(rows),
                            matching_expressions=len(artifact_entries),
                            loss=float(loss),
                        )
                    ),
                    flush=True,
                )
                if len(found) == len(manifest.rows):
                    break
                if args.max_batches and step + 1 >= args.max_batches:
                    break
        manifest.require_complete(found)
        if not rows:
            raise ValueError("No captured expressions")
        if args.capture_match_causes and any(
            "native_match_cause" not in row for row in rows
        ):
            raise ValueError("Incomplete manifest matcher-cause axes")
        report = dict(
            scope=(
                "Native manifest-bound "
                + name
                + " TRAIN diagnostic; no mechanism, efficacy, or admission claim"
            ),
            artifact_contract="m95_manifest_native_query_artifact_v1",
            producer_sha256=producer_sha256,
            batches=step + 1,
            rows=rows,
            manifest=dict(
                path=manifest_path.relative_to(root).as_posix()
                if manifest_path.is_relative_to(root)
                else str(manifest_path),
                sha256=manifest.sha256,
                rows=len(manifest.rows),
                contract=manifest.document["contract"],
            ),
            model_class=name,
            model_source_sha256=model_source_sha256,
            config_path=config.relative_to(root).as_posix(),
            config_sha256=file_sha256(config),
            checkpoint_sha256=checkpoint_sha256,
            feature_artifacts=artifacts,
            native_capture_completed=True,
            native_match_cause_completed=args.capture_match_causes,
            identity_query_completed=args.capture_identity_query,
            partition_boundary_completed=(
                args.capture_partition_boundary
                and all(
                    any(
                        int(row["manifest_index"]) == index
                        and "partition_boundary_point344" in row
                        for row in rows
                    )
                    for index in (83, 174)
                )
            ),
            partition_boundary_scope=(
                "Changed-producer diagnostic only; no strict reproducibility pass"
                if args.capture_partition_boundary else None
            ),
            capture_mode=(
                "manifest_subset" if args.manifest_only else "full_train_scan"
            ),
            selected_expressions=len(rows),
            selected_success=sum(
                row["ious"][row["selected_query"]] > 0.5 for row in rows
            ),
            no_acceptable=sum(
                row["best_acceptable_rank"] is None for row in rows
            ),
        )
        (out / "capture.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=True) + "\n",
            encoding="ascii",
        )
    finally:
        model.criterion.match_sampled_ins = native_match
        if "partition_points" in partitioner.__dict__:
            del partitioner.partition_points
        for handle in handles:
            handle.remove()


if __name__ == "__main__":
    main()
