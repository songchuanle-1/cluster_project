"""Frozen M95 TRAIN role-marker intervention, diagnostic only."""
import argparse
import hashlib
import json
from pathlib import Path


IDENTITIES = {("scene0110_00", 7), ("scene0416_00", 74),
              ("scene0452_00", 59)}
FEASIBILITY_SHA = "f3e5af583537207b90f1b3f5faf29c9ab3a00c2dcb6ce121c57e891995808223"
ENTITY_SHA = "344921f3ca7285312238225ce5ee8d529a3e7c38f023f0e0864efbf4548533a8"
CHECKPOINT_SHA = "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def noun_control(tokenizer, text, entity, original, marker_positions, vocabulary):
    spans = entity["spans"]["target_char_span"]
    if not spans or not all(s["valid"] for s in spans):
        return None
    start, end = min(int(s["span"][0]) for s in spans), max(
        int(s["span"][1]) for s in spans)
    noun_tokens = {original.char_to_token(c) for c in range(start, end)} - {None}
    old = original["input_ids"][0]
    for word in vocabulary:
        if word.lower() == text[start:end].lower() or word in text.split():
            continue
        candidate = tokenizer(text[:start] + word + text[end:],
                              return_tensors="pt")["input_ids"][0]
        if candidate.shape != old.shape:
            continue
        changed = set((candidate != old).nonzero().flatten().tolist())
        if changed and changed <= noun_tokens and not changed & set(marker_positions):
            return word, candidate, sorted(changed)
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--feasibility", type=Path, required=True)
    p.add_argument("--entity", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("New output directory required")
    if digest(a.feasibility) != FEASIBILITY_SHA or digest(a.entity) != ENTITY_SHA:
        raise ValueError("Frozen inputs changed")

    # Reuse the exact fixed 16-batch native loader and M95 attention hooks.
    parent = Path(__file__).with_name("anchor_attention_probe_20260916.py")
    scope = {"__file__": str(parent)}
    exec(compile(parent.read_text().split("\nreference_path=")[0],
                 str(parent), "exec"), scope)
    torch, model, ns = scope["torch"], scope["model"], scope["ns"]
    root = ns["ROOT"].parent / "pipeline"
    if digest(root / "scm_admission_20260914/best.pth") != CHECKPOINT_SHA:
        raise ValueError("Checkpoint changed")
    if digest(root / "entity_binding_20260916/result.json") != ENTITY_SHA:
        raise ValueError("Remote entity binding changed")
    binding = scope["binding"]
    if set(binding) & IDENTITIES != IDENTITIES:
        raise ValueError("Missing TRAIN identity")
    feasibility = json.loads(a.feasibility.read_text(encoding="utf-8"))
    mentions = {}
    for r in feasibility["rows"]:
        key = r["scene"], int(r["ann_id"])
        mentions.setdefault(key, []).append(r)
    if set(mentions) != IDENTITIES or sum(map(len, mentions.values())) != 4:
        raise ValueError("Frozen mention identity mismatch")
    tokenizer = ns["dataset"].tokenizer
    vocabulary = sorted({
        span["text"] for record in binding.values()
        for entity in record["entities"]
        for span in entity["spans"]["target_char_span"]
        if span["valid"] and span["text"].isalpha()
    })

    current = scope["current"]
    captured = {}

    def collect(module, args):
        pred, gt = args[:2]
        captured["masks"] = pred["masks"].detach().cpu()
        captured["scores"] = pred["indis"].detach().cpu().softmax(-1)[..., 1]
        captured["targets"] = [x.detach().cpu().flatten().bool() for x in gt]
        captured["sample_inds"] = pred["sample_inds"].detach().cpu()

    handle = model.criterion.register_forward_pre_hook(collect)
    outputs, artifacts = [], {}
    try:
        for step, batch in enumerate(ns["batches"]):
            scenes = [s for s, n in zip(batch["scan_ids"], batch["scenes_len"])
                      for _ in range(int(n))]
            for b, scene in enumerate(scenes):
                key = scene, int(batch["ann_ids"][b])
                if key not in IDENTITIES:
                    continue
                record = binding[key]
                text = record["caption"] + " . not mentioned"
                encoded = tokenizer(text, return_tensors="pt")
                length = int(batch["lang_masks"][b].sum())
                old = encoded["input_ids"][0]
                if old.tolist() != batch["lang_tokenss"][b, :length].tolist():
                    raise ValueError("Native tokenizer axis differs")
                for mention in mentions[key]:
                    position = mention["token_positions"]
                    if len(position) != 1:
                        raise ValueError("Only single-token marker supported")
                    replacement = text[:mention["char_span"][0]] + "the" + text[mention["char_span"][1]:]
                    marker = tokenizer(replacement, return_tensors="pt")["input_ids"][0]
                    if marker.shape != old.shape or set(
                        (marker != old).nonzero().flatten().tolist()) != set(position):
                        raise ValueError("Marker changed unexpected tokens")
                    entity = next(e for e in record["entities"]
                                  if int(e["node_id"]) == int(mention["node_id"]))
                    noun = noun_control(tokenizer, text, entity, encoded, position,
                                        vocabulary)
                    if noun is None:
                        outputs.append({"scene": scene, "ann_id": key[1],
                                        "node_id": mention["node_id"],
                                        "status": "noun_control_missing"})
                        continue
                    noun_word, noun_ids, noun_tokens = noun
                    row_branches = {}
                    for branch, ids in (("original", old), ("marker", marker),
                                        ("repeat", old), ("noun", noun_ids)):
                        changed = dict(batch)
                        changed["lang_tokenss"] = batch["lang_tokenss"].clone()
                        changed["lang_tokenss"][b, :length] = ids
                        current["attention"] = {}
                        ns["gorilla"].set_random_seed(1999)
                        with torch.no_grad():
                            loss, _ = model(changed, mode="loss")
                        if not bool(torch.isfinite(loss).all()):
                            raise ValueError("Nonfinite native loss")
                        scores = captured["scores"][b].clone()
                        logits = captured["masks"][b].clone()
                        target = captured["targets"][b]
                        n = len(target)
                        masks = logits[:, :n] > 0
                        iou = ((masks & target).sum(-1).float() /
                               (masks | target).sum(-1).clamp_min(1))
                        attention = [current["attention"][layer][b, position, :n]
                                     .mean(0).detach().cpu().clone()
                                     for layer in range(6)]
                        row_branches[branch] = {
                            "score": scores, "logits": logits, "iou": iou,
                            "attention": attention, "sample_inds":
                            captured["sample_inds"][b].clone(),
                            "target": target.clone(),
                        }
                    original = row_branches["original"]
                    repeat = row_branches["repeat"]
                    if not torch.equal(original["target"], repeat["target"]):
                        raise ValueError("Physical support changed")
                    if not torch.equal(original["sample_inds"], repeat["sample_inds"]):
                        raise ValueError("Repeat query axis changed")
                    measurements = []
                    for layer in range(6):
                        ref = original["attention"][layer]
                        tv = lambda branch: float(
                            (row_branches[branch]["attention"][layer] - ref)
                            .abs().sum() / 2)
                        measurements.append({"layer": layer, "marker_tv": tv("marker"),
                                             "noun_tv": tv("noun"),
                                             "repeat_tv": tv("repeat")})
                    def selected(branch):
                        o = row_branches[branch]
                        q = int(o["score"].argmax())
                        return {"query": q, "iou": float(o["iou"][q]),
                                "score": float(o["score"][q])}
                    artifact_id = f"{scene}_{key[1]}_node{mention['node_id']}"
                    artifacts[artifact_id] = row_branches
                    outputs.append({
                        "scene": scene, "ann_id": key[1], "node_id": mention["node_id"],
                        "marker": mention["marker"], "marker_token": position,
                        "noun_replacement": noun_word, "noun_tokens": noun_tokens,
                        "step": step, "branch": {name: selected(name) for name in row_branches},
                        "layers": measurements, "status": "complete",
                    })
                    print(json.dumps({"completed": artifact_id}), flush=True)
    finally:
        handle.remove()
    if len(outputs) != 4:
        raise ValueError("Incomplete frozen mentions")
    a.output.mkdir(parents=True)
    torch.save(artifacts, a.output / "branches.pt")
    result = {
        "contract": "m95_reference_role_native_v1",
        "admission": False, "checkpoint_sha256": CHECKPOINT_SHA,
        "entity_sha256": ENTITY_SHA, "feasibility_sha256": FEASIBILITY_SHA,
        "artifact_sha256": digest(a.output / "branches.pt"),
        "rows": outputs, "complete": sum(x["status"] == "complete" for x in outputs),
        "limitations": "Three selected TRAIN scenes; semantic sensitivity and attention are not physical reference assignment or six-gate admission.",
    }
    (a.output / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps({"complete": result["complete"]}), flush=True)


if __name__ == "__main__":
    main()
