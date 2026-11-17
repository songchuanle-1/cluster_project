"""Paired native TRAIN lexical-context intervention with independent phrase primitive."""
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import random
import socket
import sys

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
DATA = Path("/data3/songcl/data/data_cluster")
TOKEN = "5d01839a3f8642658868200f877656f3"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def phrase_classes(text, mapping):
    words = text.split()
    found = set()
    for name, value in mapping.items():
        if name == "others":
            continue
        pattern = name.split()
        if any(words[i:i + len(pattern)] == pattern
               for i in range(len(words) - len(pattern) + 1)):
            found.add(value)
    return found


def object_ids(annotation):
    if "object_ids" in annotation:
        return list(map(int, annotation["object_ids"]))
    return [int(annotation["object_id"])]


def main():
    assert socket.gethostname() == "das" and os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    import numpy as np
    import torch
    import gorilla
    import spacy
    from spacy.matcher import PhraseMatcher
    from spacy.tokens import Doc
    from spacy.vocab import Vocab
    from framework.dataset import build_dataset
    import framework.dataset.scannetv2 as native
    torch.set_num_threads(1)
    source = ROOT / "framework/dataset/scannetv2.py"
    annotations = DATA / "scanrefer/ScanRefer_train_new.json"
    graphs_path = DATA / "scanrefer/scene_graphs_new_train.json"
    config = PIPE / "majority_erasure_original_config_20261012_0910.yaml"
    assert sha(source) == "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d"
    assert sha(annotations) == "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d"
    assert sha(graphs_path) == "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08"
    assert sha(config) == "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a"
    cfg = gorilla.Config.fromfile(str(config))
    cfg.data.train.data_root = str(DATA) + "/"
    assert cfg.train.seed == 1999 and cfg.data.train.lang_num_max == 4
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("context-phrase"))
    mapping = dataset.type2class
    cls = next(n for n in ast.parse(source.read_text()).body
               if isinstance(n, ast.ClassDef) and n.name == "ScanNetDataset_sample_graph_edge")
    getter = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "__getitem__")
    word_loop = next(n for n in ast.walk(getter) if isinstance(n, ast.For)
                     and isinstance(n.target, ast.Name) and n.target.id == "word")
    lexical = ast.FunctionDef(
        name="original_classes", args=ast.arguments(
            posonlyargs=[], args=[ast.arg(arg="self"), ast.arg(arg="lang_utterance")],
            kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=[ast.Assign(targets=[ast.Name(id="context_label", ctx=ast.Store())],
                         value=ast.Call(func=ast.Name(id="set", ctx=ast.Load()), args=[], keywords=[])),
              copy.deepcopy(word_loop),
              ast.Return(value=ast.Name(id="context_label", ctx=ast.Load()))],
        decorator_list=[])
    original_namespace = {}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[lexical], type_ignores=[])),
                 str(source), "exec"), original_namespace)
    original_classes = original_namespace["original_classes"]
    vocab = Vocab()
    matcher = PhraseMatcher(vocab, attr="ORTH")
    for name in mapping:
        if name != "others":
            matcher.add(name, [Doc(vocab, words=name.split())])

    def library_classes(text):
        return {mapping[vocab.strings[mid]] for mid, _, _ in matcher(Doc(vocab, words=text.split()))}

    controls = {}
    for name, text in (("single", "a chair"), ("multi", "a shower curtain"),
                       ("unrelated", "a purple unknown"), ("single_curtain", "a curtain")):
        old = original_classes(dataset, text)
        new = phrase_classes(text, mapping)
        assert new == library_classes(text)
        controls[name] = {"old": sorted(old), "new": sorted(new)}
    assert controls["single"]["old"] == controls["single"]["new"]
    assert controls["unrelated"]["old"] == controls["unrelated"]["new"] == []
    assert mapping["shower curtain"] not in controls["multi"]["old"]
    assert mapping["shower curtain"] in controls["multi"]["new"]

    anns = json.loads(annotations.read_text())
    graphs = json.loads(graphs_path.read_text())
    changed, equivalence_errors = [], []
    for ann in anns:
        scene, aid = ann["scene_id"], str(ann["ann_id"])
        text = " ".join(graphs[scene][aid]["utterance"].replace(",", " ,").split()) + " . not mentioned"
        old = original_classes(dataset, text)
        new = phrase_classes(text, mapping)
        reference = library_classes(text)
        if new != reference:
            equivalence_errors.append({"scene": scene, "ann_id": aid})
        if old != new:
            changed.append({"scene": scene, "ann_id": int(aid),
                            "original_classes": sorted(old), "phrase_classes": sorted(new)})
    assert len(anns) == 36665 and not equivalence_errors
    groups = {}
    for idx, group in enumerate(dataset.scene_inputs):
        for ann in group:
            groups[(ann["scene_id"], int(ann["ann_id"]))] = idx
    selected, used_scenes = [], set()
    for row in sorted(changed, key=lambda x: (x["scene"], x["ann_id"])):
        if row["scene"] in used_scenes:
            continue
        idx = groups[(row["scene"], row["ann_id"])]
        selected.append({"scene": row["scene"], "native_group": idx,
                         "trigger_ann_id": row["ann_id"],
                         "annotations": [{"ann_id": int(a["ann_id"]),
                                          "object_ids": object_ids(a)
                                         } for a in dataset.scene_inputs[idx]]})
        used_scenes.add(row["scene"])
        if len(selected) == 8:
            break
    manifest_path = PIPE / "context_phrase_manifest_20261012_1908.json"
    assert not manifest_path.exists()
    manifest_path.write_text(json.dumps({
        "selection": "sorted first affected annotation per scene, at most eight; prediction blind",
        "tick_token": TOKEN, "groups": selected}, indent=2) + "\n")

    identity_tree = copy.deepcopy(getter)
    namespace = dict(native.__dict__)
    namespace["phrase_classes"] = phrase_classes
    exec(compile(ast.fix_missing_locations(ast.Module(body=[identity_tree], type_ignores=[])),
                 str(source), "exec"), namespace)
    identity_getter = namespace["__getitem__"]
    candidate_tree = copy.deepcopy(getter)
    replacement = ast.parse("context_label = phrase_classes(lang_utterance, self.type2class)").body[0]

    class ReplaceLoop(ast.NodeTransformer):
        def visit_For(self, node):
            if isinstance(node.target, ast.Name) and node.target.id == "word":
                return copy.deepcopy(replacement)
            return self.generic_visit(node)

    candidate_tree = ReplaceLoop().visit(candidate_tree)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[candidate_tree], type_ignores=[])),
                 str(source), "exec"), namespace)
    candidate_getter = namespace["__getitem__"]

    def digest(value):
        h = hashlib.sha256()

        def consume(item):
            if torch.is_tensor(item):
                consume(("tensor", str(item.dtype), tuple(item.shape)))
                h.update(item.detach().cpu().contiguous().numpy().tobytes())
            elif isinstance(item, np.ndarray):
                consume(("array", str(item.dtype), item.shape))
                h.update(item.tobytes())
            elif isinstance(item, dict):
                for key in sorted(item):
                    consume(key)
                    consume(item[key])
            elif isinstance(item, (list, tuple)):
                h.update(b"[")
                for part in item:
                    consume(part)
                h.update(b"]")
            else:
                h.update(repr(item).encode("utf-8"))
                h.update(b";")
        consume(value)
        return h.hexdigest()

    def rng_state():
        return random.getstate(), np.random.get_state(), torch.get_rng_state()

    def restore(state):
        random.setstate(state[0])
        np.random.set_state(state[1])
        torch.set_rng_state(state[2])

    trials = []
    for trial in range(2):
        gorilla.set_random_seed(1999)
        rows = []
        for group in selected:
            index = group["native_group"]
            before = rng_state()
            old = dataset[index]
            after = rng_state()
            restore(before)
            identity = identity_getter(dataset, index)
            assert digest(identity) == digest(old)
            restore(before)
            new = candidate_getter(dataset, index)
            restore(after)
            assert old[1] == new[1] == group["scene"]
            old_rest = [x for i, x in enumerate(old) if i != 9]
            new_rest = [x for i, x in enumerate(new) if i != 9]
            assert digest(old_rest) == digest(new_rest)
            for aid, original_mask, candidate_mask in zip(old[0], old[9], new[9]):
                delta = candidate_mask - original_mask
                rows.append({"scene": group["scene"], "ann_id": int(aid),
                             "native_group": index,
                             "changed_context_supports": int((delta != 0).sum()),
                             "max_context_delta": float(delta.abs().max()),
                             "original_context_sha256": digest(original_mask),
                             "candidate_context_sha256": digest(candidate_mask),
                             "all_noncontext_fields_exact": True})
            print(json.dumps({"trial": trial, "groups_done": len(rows) // 4,
                              "expressions": len(rows)}), flush=True)
        trials.append(rows)
    assert trials[0] == trials[1]
    result = {
        "contract": "native_context_phrase_transport_v1", "tick_token": TOKEN,
        "observed_at": datetime.now(timezone.utc).isoformat(), "cpu_only": True,
        "hostname": socket.gethostname(), "seed": 1999, "expressions": len(anns),
        "lexically_changed_expressions": len(changed),
        "lexically_changed_scenes": len({r["scene"] for r in changed}),
        "phrase_library_mismatches": len(equivalence_errors), "spacy_version": spacy.__version__,
        "spacy_matcher_binary_sha256": sha(Path(sys.modules["spacy.matcher.phrasematcher"].__file__)),
        "native_groups": len(selected), "native_expressions": len(trials[0]),
        "native_changed_expressions": sum(r["changed_context_supports"] > 0 for r in trials[0]),
        "native_changed_supports": sum(r["changed_context_supports"] for r in trials[0]),
        "native_repeat_exact": True, "controls": controls, "lexical_rows": changed,
        "native_rows": trials[0], "manifest_sha256": sha(manifest_path),
        "dataset_sha256": sha(source), "annotations_sha256": sha(annotations),
        "graphs_sha256": sha(graphs_path), "config_sha256": sha(config),
        "script_sha256": sha(Path(__file__)),
        "scope": "Literal recognition and native TRAIN context-target transport only; no whole-model loss/backward/resource/efficacy certification.",
    }
    output = PIPE / "context_phrase_audit_20261012_1908.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in (
        "expressions", "lexically_changed_expressions", "lexically_changed_scenes",
        "phrase_library_mismatches", "spacy_version", "native_groups", "native_expressions",
        "native_changed_expressions", "native_changed_supports", "native_repeat_exact")}), flush=True)
    print(json.dumps({"output_sha256": sha(output)}), flush=True)


if __name__ == "__main__":
    main()
