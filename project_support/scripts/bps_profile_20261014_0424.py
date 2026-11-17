"""Bounded stage attribution on fixed native data, not production variants."""
import argparse
from datetime import datetime, timezone
import gc
import json
from pathlib import Path
import statistics
import sys
import time

from bps_runtime_20261014_0424 import (
    PIPE, fingerprint, get_batch, setup, sha)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    torch, gorilla, dataset, model, state, frozen, sources, full_name = setup(args.token)
    catalog = model.between_support.catalog
    no_events = []
    seen = set()
    for group, annotations in enumerate(dataset.scene_inputs):
        scene = annotations[0]["scene_id"]
        if scene in seen or len(annotations) != 4:
            continue
        if all(a["scene_id"] + "/" + str(int(a["ann_id"])) not in catalog["records"]
               for a in annotations):
            no_events.append(group)
            seen.add(scene)
        if len(no_events) == 2:
            break
    assert len(no_events) == 2
    cases = [("non_event_batch1", no_events[:1]),
             ("non_event_batch2", no_events),
             ("original_group452", [452]),
             ("worst_pair_batch2", [5743, 7787])]
    manifest_path = PIPE / ("bps_profile_" + args.token + ".manifest.json")
    with manifest_path.open("x") as stream:
        json.dump({"tick_token": args.token, "cases": cases,
                   "selection": "metadata-only first two distinct all-non-event four-expression scene groups; existing frozen active/stress cases",
                   "native_forward_started": False}, stream, indent=2)
    original_prepare = model.between_support.prepare
    loss_module = sys.modules[full_name + ".loss"]
    original_operator = loss_module.support_excess
    rows, clock = [], {}
    mode = "full"
    def timed_prepare(*values):
        torch.cuda.synchronize()
        started = time.perf_counter()
        if mode == "no_geometry":
            result = [{"costs": [], "counts": torch.empty(0, dtype=torch.float64),
                       "centers": torch.empty((0, 3), dtype=torch.float64), "pairs": [], "unknowns": []}
                      for _ in values[0]]
        else:
            result = original_prepare(*values)
        clock["geometry_ms"] = (time.perf_counter() - started) * 1000
        return result
    def operator(*values):
        if mode == "full":
            return original_operator(*values)
        masks, _, _, num_boxes, _ = values
        return sum(m.sum().double() * 0 for m in masks) / num_boxes
    model.between_support.prepare = timed_prepare
    loss_module.support_excess = operator
    progress = PIPE / ("bps_profile_" + args.token + ".progress.jsonl")
    try:
        with progress.open("x") as stream:
            for name, groups in cases:
                batch = get_batch(torch, gorilla, dataset, groups)
                for mode in ("full", "no_cost", "no_geometry"):
                    model.load_state_dict(state, strict=True)
                    model.train()
                    timings, losses = [], []
                    for repeat in range(11):
                        model.zero_grad(set_to_none=True)
                        gorilla.set_random_seed(1999)
                        clock.clear()
                        torch.cuda.synchronize()
                        started = time.perf_counter()
                        loss, parts = model(batch, mode="loss")
                        torch.cuda.synchronize()
                        forward_ms = (time.perf_counter() - started) * 1000
                        assert bool(torch.isfinite(loss).all())
                        value = float(loss.detach())
                        component = float(parts["between_support_loss"].detach())
                        started = time.perf_counter()
                        loss.backward()
                        torch.cuda.synchronize()
                        backward_ms = (time.perf_counter() - started) * 1000
                        if repeat >= 3:
                            timings.append({"forward_ms": forward_ms, "backward_ms": backward_ms,
                                            "geometry_ms": clock["geometry_ms"],
                                            "total_ms": forward_ms + backward_ms})
                            losses.append({"total": value, "component": component})
                        del loss, parts
                    metrics = {key: statistics.median(t[key] for t in timings)
                               for key in timings[0]}
                    row = {"case": name, "groups": groups, "condition": mode,
                           "input_sha256": fingerprint(batch), "metrics": metrics,
                           "measurements": timings, "losses": losses,
                           "readout": model.between_support.last_readout if mode != "no_geometry" else None}
                    rows.append(row)
                    stream.write(json.dumps(row, allow_nan=False) + "\n")
                    stream.flush()
                    print(json.dumps({"case": name, "condition": mode, "metrics": metrics}), flush=True)
                del batch
                gc.collect()
                torch.cuda.empty_cache()
    finally:
        model.between_support.prepare = original_prepare
        loss_module.support_excess = original_operator
    result = {"tick_token": args.token, "observed_at": datetime.now(timezone.utc).isoformat(),
              "script_sha256": sha(Path(__file__)), "source_manifest": sources,
              "frozen_manifest_sha256": sha(manifest_path), "rows": rows,
              "native_forward_count": len(rows) * 11, "native_backward_count": len(rows) * 11,
              "warmup": 3, "repeat": 8, "optimizer_steps": 0,
              "scope": "Instrumented stage attribution with barriers, no per-parameter finite-scan timing; not primary standardized throughput or a new model/gate."}
    output = PIPE / ("bps_profile_" + args.token + ".json")
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"result": str(output), "sha256": sha(output), "rows": len(rows)}), flush=True)


if __name__ == "__main__":
    main()
