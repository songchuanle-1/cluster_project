"""Independent scalar readback, scene uncertainty, and diagnostic summary."""
from collections import Counter
import json
import math
import numpy as np
from run_d1_assignment_20260911 import P, OUT, sha, key


def main():
    a = json.loads((OUT / "assignment.json").read_text())
    protocol = json.loads((OUT / "protocol.json").read_text(encoding="utf-8"))
    assert a["protocol_sha256"] == sha(OUT / "protocol.json")
    assert a["worker_sha256"] == sha(P / "headless/d1_assignment_20260911.py")
    assert not a["cuda_initialized"]
    models, scene_arrays = {}, {}
    scene_names = sorted({r["scene_id"] for r in a["rows"]})
    assert len(scene_names) == 71 and len({s.split("_")[0] for s in scene_names}) == 71
    fields = ["any_usable_negative", "no_usable_positive", "recoverable",
              "recoverable_with_positive_usable", "recoverable_without_positive_usable",
              "selected_positive", "positive_oracle", "negative_oracle"]
    for name in ("baseline", "m95"):
        rows = [r for r in a["rows"] if r["model"] == name]
        summary = json.loads((P / f"reports/d1_expansion_20260911-0715/{name}/summary.json").read_text())
        source = {key(r): r for r in summary["rows"]}
        assert {key(r) for r in rows} == set(source) and len(rows) == 284
        missing = [key(r) for r in rows if r["status"] != "complete"]
        assert not missing, missing
        counters = Counter()
        scores = {}
        for r in rows:
            s = source[key(r)]
            assert r["bank_sha256"] == s["artifact_sha256"]
            pos = set(r["positive_indices"])
            assert len(pos) == len(r["positive_indices"])
            expected = {i for i, c in enumerate(r["query_instance_labels"]) if c == int(r["object_id"])}
            expected.add(r["nearest"])
            assert pos == expected
            u = s["candidate_ious"]
            good = {i for i, value in enumerate(u) if value > .5}
            assert r["positive_usable"] == len(pos & good)
            assert r["negative_usable"] == len(good - pos)
            assert r["positive_unusable"] == len(pos - good)
            assert r["negative_unusable"] == 128 - len(pos | good)
            assert r["positive_oracle"] == max(u[i] for i in pos)
            assert r["negative_oracle"] == max(u[i] for i in range(128) if i not in pos)
            assert r["selected_positive"] == (s["selected_index"] in pos)
            assert r["oracle_positive"] == (s["oracle_index"] in pos)
            assert r["recoverable"] == (s["selected_iou"] <= .5 < s["oracle_iou"])
            assert r["no_usable_positive"] == bool(good and not (pos & good))
            for i, g in enumerate(r["gradients_z1"]):
                assert math.isfinite(g)
                assert g <= 0 if i in pos else g >= 0
            for f in ("positive_usable", "negative_usable", "positive_unusable", "negative_unusable"):
                counters[f] += r[f]
            flags = dict(
                any_usable_negative=bool(good - pos), no_usable_positive=r["no_usable_positive"],
                recoverable=r["recoverable"],
                recoverable_with_positive_usable=r["recoverable"] and bool(pos & good),
                recoverable_without_positive_usable=r["recoverable"] and not bool(pos & good),
                selected_positive=r["selected_positive"],
                positive_oracle=r["positive_oracle"], negative_oracle=r["negative_oracle"])
            for f in fields[:6]:
                counters[f] += int(flags[f])
            counters["selected_positive_failure"] += int(r["selected_positive"] and s["selected_iou"] <= .5)
            counters["selected_negative_success"] += int(not r["selected_positive"] and s["selected_iou"] > .5)
            counters["recoverable_selected_positive"] += int(r["recoverable"] and r["selected_positive"])
            counters["nearest_outside_target"] += int(not r["nearest_in_target"])
            counters["nearest_float64_disagreement"] += int(not r["nearest_float64_agrees"])
            counters["nearest_ties"] += int(r["nearest_tie_count"] > 1)
            counters["all_oracles_negative"] += int(r["all_usable_oracles_negative"])
            scores[key(r)] = flags
        scene_arrays[name] = np.array([
            [np.mean([v[f] for k, v in scores.items() if k[0] == scene]) for f in fields]
            for scene in scene_names])
        assert all(sum(k[0] == s for k in scores) == 4 for s in scene_names)
        models[name] = dict(descriptions=284, candidates=284 * 128, missing_ids=missing,
                            counts=dict(counters), max_gradient_error=max(r["gradient_error"] for r in rows),
                            scene_mean=dict(zip(fields, scene_arrays[name].mean(0).tolist())))
    rng = np.random.default_rng(1999)
    draws = rng.integers(0, 71, (10000, 71))
    bootstrap = {}
    for name, values in {**scene_arrays, "m95_minus_baseline": scene_arrays["m95"] - scene_arrays["baseline"]}.items():
        samples = values[draws].mean(1)
        lo, hi = np.quantile(samples, [.025, .975], axis=0)
        bootstrap[name] = {f: dict(mean=float(values[:, i].mean()), low=float(lo[i]), high=float(hi[i]))
                           for i, f in enumerate(fields)}
    result = dict(status="passed", assignment_sha256=sha(OUT / "assignment.json"),
                  models=models, bootstrap=bootstrap, physical_scenes=71,
                  verified_records=568, synthetic_tests=a["tests"],
                  limits="Conditional equal-scene sample; descriptive scene bootstrap, no population or causal claims.")
    (OUT / "verification.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(models, indent=2))


if __name__ == "__main__":
    main()
