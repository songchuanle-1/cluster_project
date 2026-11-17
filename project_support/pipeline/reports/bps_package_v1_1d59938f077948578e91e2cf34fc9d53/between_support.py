"""Coherent-pair support excess; class candidates are not witness labels."""
import itertools
import json
from pathlib import Path

import numpy as np
import torch


def support_excess(masks, targets, indices, num_boxes, supports, fragmented=False):
    total = sum(mask.sum().double() * 0 for mask in masks)
    if len(supports) != len(masks):
        raise ValueError("Relation geometry must align with native expressions")
    for mask, target, (src, tgt), support in zip(masks, targets, indices, supports):
        if not support["costs"] or not len(src):
            continue
        counts = support["counts"].to(device=mask.device, dtype=torch.float64)
        if mask.shape[-1] != len(counts):
            raise ValueError("Native support/mask size mismatch")
        prediction = mask[src].sigmoid().double() * counts
        prediction = prediction / prediction.sum(-1, keepdim=True).clamp_min(1e-12)
        teacher = target["masks"][tgt].double() * counts
        if not bool((teacher.sum(-1) > 0).all()):
            raise ValueError("Resolved event requires a nonempty original GT mask")
        teacher = teacher / teacher.sum(-1, keepdim=True)
        events = []
        for cost in support["costs"]:
            cost = cost.to(device=mask.device, dtype=torch.float64)
            if fragmented:
                cost = cost.min(-1).values
                events.append(torch.relu(prediction @ cost - teacher @ cost))
            else:
                events.append(torch.relu(prediction @ cost - teacher @ cost).min(-1).values)
        total = total + torch.stack(events, dim=-1).mean(-1).sum()
    return total / num_boxes


class BetweenSupportCatalog:
    def __init__(self, path):
        self.catalog = {"schema_version": 1, "records": {}, "instances": {}}
        if path:
            self.catalog = json.loads(Path(path).read_text(encoding="utf-8"))
            if self.catalog["schema_version"] != 1:
                raise ValueError("Unsupported BETWEEN catalog")
        self.last_readout = []
        self.prepare_calls = 0

    def prepare(self, ann_ids, scan_ids, scenes_len, object_idss, superpoints,
                coords_float, batch_offsets, sp_ins_labels):
        self.prepare_calls += 1
        sp = superpoints.detach().cpu().numpy().astype(np.int64)
        xyz = coords_float.detach().cpu().numpy().astype(np.float64)
        offsets = batch_offsets.detach().cpu().tolist()
        result, readout = [], []
        expression = 0
        for scene_index, (scene, length) in enumerate(zip(scan_ids, scenes_len)):
            scene = str(scene)
            start, end = map(int, offsets[scene_index:scene_index + 2])
            selected = (sp >= start) & (sp < end)
            local_sp, points = sp[selected] - start, xyz[selected]
            labels = sp_ins_labels[scene_index].detach().cpu().numpy().astype(np.int64)
            if len(labels) != end - start:
                raise ValueError("Native scene instance/support mismatch")
            counts = np.bincount(local_sp, minlength=len(labels))
            if not bool((counts > 0).all()):
                raise ValueError("Native scene contains empty supports")
            centers = np.stack([np.bincount(local_sp, weights=points[:, d],
                                           minlength=len(labels)) for d in range(3)], -1)
            centers = centers / counts[:, None]
            ownership = labels[local_sp]
            geometry = {int(oid): points[ownership == oid]
                        for oid in np.unique(labels) if oid >= 0 and oid != 199}
            categories = self.catalog["instances"].get(scene, {})
            for _ in range(int(length)):
                aid = int(ann_ids[expression])
                objects = sorted(map(int, object_idss[expression]))
                record = self.catalog["records"].get(scene + "/" + str(aid))
                support = {"counts": torch.as_tensor(counts, dtype=torch.float64),
                           "centers": torch.as_tensor(centers, dtype=torch.float64),
                           "costs": [], "pairs": [], "unknowns": []}
                status = "no_event_bypass"
                if record and objects == record["target_ids"]:
                    status = "event_geometry"
                    for event in record["events"]:
                        fields, pairs = [], []
                        refs = event["references"]
                        candidates = [[int(oid) for oid, cls in categories.items()
                                       if cls == ref["category"] and ref["category"] is not None
                                       and int(oid) not in objects]
                                      for ref in refs]
                        unavailable = []
                        for left, right in itertools.combinations(range(len(refs)), 2):
                            for a, b in itertools.product(candidates[left], candidates[right]):
                                if a == b:
                                    unavailable.append("duplicate_witness")
                                    continue
                                if a not in geometry or b not in geometry:
                                    unavailable.append("native_support_missing")
                                    continue
                                pa, pb = geometry[a], geometry[b]
                                delta = pb.mean(0) - pa.mean(0)
                                norm = float(np.linalg.norm(delta))
                                if norm == 0:
                                    unavailable.append("zero_center_distance")
                                    continue
                                axis = delta / norm
                                lower, upper = float((pa @ axis).max()), float((pb @ axis).min())
                                if lower >= upper:
                                    unavailable.append("overlap_gap")
                                    continue
                                projection = centers @ axis
                                field = ((np.maximum(lower - projection, 0) +
                                          np.maximum(projection - upper, 0)) / (upper - lower)) ** 2
                                if not bool(np.isfinite(field).all()):
                                    raise ValueError("Nonfinite native pair cost")
                                fields.append(field)
                                pairs.append({"left_node": refs[left]["node_id"],
                                              "right_node": refs[right]["node_id"],
                                              "a": a, "b": b, "axis": axis.tolist(),
                                              "lower": lower, "upper": upper})
                        if fields:
                            support["costs"].append(torch.as_tensor(
                                np.stack(fields, -1), dtype=torch.float64))
                            support["pairs"].append(pairs)
                        else:
                            support["unknowns"].append({
                                "positions": event["positions"],
                                "reason": "no_valid_distinct_pair",
                                "reference_nodes": len(refs), "unavailable": unavailable})
                elif record:
                    status = "target_identity_mismatch_bypass"
                result.append(support)
                readout.append({"scene": scene, "ann_id": aid, "status": status,
                                "available_events": len(support["costs"]),
                                "valid_pair_counts": [len(p) for p in support["pairs"]],
                                "unknowns": support["unknowns"]})
                expression += 1
        if expression != len(ann_ids):
            raise ValueError("Native scene/expression grouping mismatch")
        self.last_readout = readout
        return result
