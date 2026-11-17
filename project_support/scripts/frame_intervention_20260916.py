"""Decoder-coordinate transport diagnostic with unchanged voxel features."""
import copy
import hashlib
import json
from pathlib import Path

base = Path(__file__).with_name("coverage_stage_capture_20260916.py")
env = {"__file__": str(base)}
exec(compile(base.read_text().split(
    "model.criterion.register_forward_pre_hook(capture)")[0], str(base), "exec"), env)
torch, model, batches = env["torch"], env["model"], env["batches"]
root = env["ROOT"].parent / "pipeline"
exposure_path = root / "frame_exposure_20260916/result.json"
exposure = json.loads(exposure_path.read_text())
state, output = {}, []


def change_coords(module, args):
    if state["branch"] in ("base", "repeat"):
        return
    args = list(args)
    coordinates, offsets = args[5].clone(), args[2]
    assert coordinates.ndim == 2 and coordinates.shape[1] == 3
    matrices = state["matrices"]
    if state["branch"] == "mismatch":
        matrices = matrices[::-1]
    expanded = [m for m, count in zip(matrices, state["batch"]["scenes_len"])
                for _ in range(int(count))]
    assert len(expanded) == len(offsets)-1
    for i, matrix in enumerate(expanded):
        lo, hi = int(offsets[i]), int(offsets[i+1])
        inv = torch.linalg.inv(torch.tensor(matrix, device=coordinates.device,
                                            dtype=coordinates.dtype))
        coordinates[lo:hi] = coordinates[lo:hi] @ inv
    args[5] = coordinates
    return tuple(args)


def collect(module, args):
    env["capture"](module, args)
    state["seeds"] = args[7].gather(1, args[0]["sample_inds"].long()).cpu().tolist()


model.dec.register_forward_pre_hook(change_coords)
model.criterion.register_forward_pre_hook(collect)
out = root / "frame_intervention_20260916"
out.mkdir(parents=True, exist_ok=True)
with torch.no_grad():
    for step, batch in enumerate(batches):
        scenes = exposure["scenes"][2*step:2*step+2]
        assert [s["scene"] for s in scenes] == list(batch["scan_ids"])
        expected = [(r["scene"], r["ann_id"]) for r in exposure["expressions"] if r["batch"] == step]
        actual_scenes = [s for s, n in zip(batch["scan_ids"], batch["scenes_len"]) for _ in range(int(n))]
        assert expected == list(zip(actual_scenes, map(int, batch["ann_ids"])))
        state.update(batch=batch, matrices=[s["matrix"] for s in scenes])
        env["current"].update(step=step, batch=batch)
        branches = {}
        for branch in ("base", "repeat", "inverse", "mismatch"):
            state["branch"] = branch
            env["rows"].clear()
            env["gorilla"].set_random_seed(1999)
            loss, _ = model(copy.deepcopy(batch), mode="loss")
            assert torch.isfinite(loss).all()
            branches[branch] = dict(rows=copy.deepcopy(env["rows"]), seeds=state["seeds"])
        output.append(dict(batch=step, branches=branches))
        (out / "partial.json").write_text(json.dumps(output, indent=2))
        print(json.dumps(dict(batch=step, complete=True)), flush=True)
report = dict(batches=output, sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
    for p in (Path(__file__), base, exposure_path, env["checkpoint"])},
    scope="M95eval nativeTRAIN16 batches. Only decoder coords inverse transported;voxel features,"
          "2Dfeatures,FPS generation unchanged. Sampling can change downstream. No viewpoint "
          "truth,training efficacy,new architecture or resource admission.")
(out / "result.json").write_text(json.dumps(report, indent=2))
