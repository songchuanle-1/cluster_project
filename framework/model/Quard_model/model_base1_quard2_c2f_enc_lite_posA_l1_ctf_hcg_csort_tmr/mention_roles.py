"""TRAIN-only annotation-anchored noun-role supervision."""
import json
import os
import re

import torch
from transformers import RobertaTokenizerFast


class TargetMentionRoles:
    def __init__(self, data_root):
        root = os.path.join(data_root, "scanrefer")
        with open(os.path.join(root, "ScanRefer_train_new.json")) as handle:
            annotations = json.load(handle)
        with open(os.path.join(root, "scene_graphs_new_train.json")) as handle:
            graphs = json.load(handle)
        self.tokenizer = RobertaTokenizerFast.from_pretrained(
            os.path.join(data_root, "roberta-base"), local_files_only=True)
        self.catalog = {}
        for annotation in annotations:
            scene, aid = annotation["scene_id"], int(annotation["ann_id"])
            graph = graphs[scene][str(aid)]
            caption = " ".join(graph["utterance"].replace(",", " ,").split())
            words = re.findall(r"[a-z0-9]+", annotation.get("object_name", "").lower())
            if not words:
                continue
            pattern = r"\b" + r"\s+".join(map(re.escape, words)) + r"\b"
            found = list(re.finditer(pattern, caption, re.I))
            if len(found) != 1:
                continue
            begin, end = found[0].span()
            node = next(n for n in graph["graph_node"] if n["node_id"] == 0)
            if any(max(begin, left) < min(end, right)
                   for left, right in node["target_char_span"]):
                continue
            encoded = self.tokenizer(caption)
            first = encoded.char_to_token(begin)
            last = encoded.char_to_token(end - 1)
            if first is None or last is None or last >= 256:
                continue
            objects = sorted(map(int, annotation.get(
                "object_ids", [annotation.get("object_id")])))
            self.catalog[scene, aid] = {
                "objects": objects, "tokens": tuple(range(first, last + 1)),
                "span": (begin, end),
            }

    def rebind(self, ann_ids, scan_ids, scenes_len, object_idss, dense_maps):
        scenes = [scene for scene, count in zip(scan_ids, scenes_len)
                  for _ in range(int(count))]
        if not (len(scenes) == len(ann_ids) == len(dense_maps) == len(object_idss)):
            raise ValueError("Native scene/annotation/map cardinalities disagree")
        maps, changed = list(dense_maps), []
        for b, (scene, aid) in enumerate(zip(scenes, ann_ids)):
            record = self.catalog.get((scene, int(aid)))
            if not record or sorted(map(int, object_idss[b])) != record["objects"]:
                continue
            original = dense_maps[b]
            positive = original["positive_map"].clone()
            if not record["tokens"] or max(record["tokens"]) >= positive.shape[-1]:
                continue
            positive[0].zero_()
            positive[0, list(record["tokens"])] = 1.0 / len(record["tokens"])
            if torch.equal(positive > 0, original["positive_map"] > 0):
                continue
            other = (original["other_entity_map"]
                     + original["positive_map"]).clamp(0, 1)
            other = other.masked_fill(positive > 0, 0)
            maps[b] = dict(original, positive_map=positive, other_entity_map=other)
            changed.append(b)
        return maps, changed
