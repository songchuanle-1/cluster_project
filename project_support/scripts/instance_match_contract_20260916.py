"""Capture exact native target/seed identity conflicts before all-instance loss."""
import copy
import hashlib
import json
from pathlib import Path
import types

base = Path(__file__).with_name("coverage_stage_capture_20260916.py")
ns = {"__file__": str(base)}
exec(compile(base.read_text().split(
    "model.criterion.register_forward_pre_hook(capture)")[0], str(base), "exec"), ns)
torch, model = ns["torch"], ns["model"]
original = model.criterion.match_sampled_ins
records, state = [], {}


def wrapped(self, labels, object_ids, positions, centers):
    result = original(labels, object_ids, positions, centers)
    index = state["calls"]
    state["calls"] += 1
    # Native forward calls once on FPS support then once on selected queries.
    b = index // 2
    assert b < len(state["identities"])
    top, _, matched, _ = result
    conflicts = []
    for query, target in zip(matched[0].tolist(), matched[1].tolist()):
        owner, wanted = int(labels[query]), int(object_ids[target])
        if owner != wanted:
            conflicts.append(dict(query=query, seed_instance=owner, target=wanted,
                valid_other_instance=owner >= 0 and owner != 199,
                is_nearest_fallback=query in top.tolist(),
                distance=float(torch.linalg.vector_norm(positions[query]-centers[target]))))
    records.append(dict(**state["identities"][b],
        stage="fps" if index % 2 == 0 else "selected",
        matched=len(matched[0]), conflicts=conflicts))
    return result


model.criterion.match_sampled_ins = types.MethodType(wrapped, model.criterion)
with torch.no_grad():
    for step, batch in enumerate(ns["batches"]):
        scenes = [s for s, n in zip(batch["scan_ids"], batch["scenes_len"])
                  for _ in range(int(n))]
        state.update(calls=0, identities=[
            dict(scene=s, ann_id=int(a), batch=step)
            for s, a in zip(scenes, batch["ann_ids"])])
        ns["gorilla"].set_random_seed(1999)
        loss, _ = model(copy.deepcopy(batch), mode="loss")
        assert torch.isfinite(loss).all()
        assert state["calls"] == 2 * len(state["identities"])
        print(json.dumps(dict(batch=step, calls=state["calls"])), flush=True)
summary = {}
for stage in ("fps", "selected"):
    rows = [r for r in records if r["stage"] == stage]
    summary[stage] = dict(expressions=len(rows), matched=sum(r["matched"] for r in rows),
        conflict_expressions=sum(bool(r["conflicts"]) for r in rows),
        conflicts=sum(len(r["conflicts"]) for r in rows),
        valid_other=sum(c["valid_other_instance"] for r in rows for c in r["conflicts"]))
out = ns["ROOT"].parent / "pipeline/instance_match_contract_20260916"
out.mkdir(exist_ok=True)
(out / "result.json").write_text(json.dumps(dict(summary=summary, records=records,
    scope="Original native matching return values, no replacement or optimizer step. "
          "Mismatch is intentional nearest-center fallback,not automatically a bug. "
          "Naive all-instance seed-mask supervision can conflict with target labels.",
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), base, ns["checkpoint"])}), indent=2))
print(json.dumps(summary), flush=True)
