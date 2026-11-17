"""Independent scalar ranking and semantic-gradient readback."""
import json
import math
import numpy as np
from prepare_d1_ordering_20260911 import P, OUT, sha


def key(r):
    return r["scene_id"], str(r["object_id"]), str(r["ann_id"])


def quantiles(values):
    if not values:
        return dict(n=0)
    q = np.quantile(values, [0, .25, .5, .75, 1])
    return dict(n=len(values), mean=float(np.mean(values)), minimum=float(q[0]),
                q25=float(q[1]), median=float(q[2]), q75=float(q[3]), maximum=float(q[4]))


def independent_semantic(test):
    for label, padded, alternate in (("base", 0, False), ("padded", 2, False),
                                     ("alternate_padding", 2, True)):
        v = np.eye(3)
        t = np.array([[.6, .8, 0], [0, .6, .8], [.8, 0, .6], [1., 0, 0]])
        if padded:
            extra = np.array([[0., 1, 0], [0., 0, 1]])
            t = np.concatenate((t, -extra if alternate else extra))
        s = v @ t.T / .07
        a = np.zeros_like(s)
        a[0, 0] = 1
        a[1:, 2:4] = 1
        w = np.array([1., np.float32(.1), np.float32(.1)])
        tw = np.array([1., np.float32(.1), np.float32(.1), 1.] + [np.float32(.1)] * padded)
        nq = a.sum(1).astype(np.float32) + np.float32(1e-6)
        ml = a.sum(0).astype(np.float32) + np.float32(1e-6)
        active = a.any(0)
        def softmax(x, axis):
            e = np.exp(x - x.max(axis=axis, keepdims=True))
            return e / e.sum(axis=axis, keepdims=True)
        g = (w[:, None] * (softmax(s, 1) - a / nq[:, None])
             + (tw * active)[None] * (softmax(s, 0) - a / ml[None])) / 2
        gv, gt = g @ t / .07, g.T @ v / .07
        assert np.allclose(gv, test[label]["query_grad"], atol=1e-6, rtol=1e-6)
        assert np.allclose(gt[:4], test[label]["valid_embedding_grad"], atol=1e-6, rtol=1e-6)
        assert test[label]["finite_difference_error"] < 1e-5
    assert abs(test["base"]["loss"] - test["query_permuted"]["loss"]) < 1e-6


def main():
    data = json.loads((OUT / "ordering.json").read_text())
    assert data["protocol_sha256"] == sha(OUT / "protocol.json")
    assert data["worker_sha256"] == sha(P / "headless/d1_ordering_20260911.py")
    assert not data["cuda_initialized"]
    result = dict(status="passed", ordering_sha256=sha(OUT / "ordering.json"),
                  verified_records=568, models={}, semantic={})
    by_model = {}
    for name in ("baseline", "m95"):
        rows = [r for r in data["rows"] if r["model"] == name]
        source = {key(r): r for r in json.loads((P / f"reports/d1_expansion_20260911-0715/{name}/summary.json").read_text())["rows"]}
        assert len(rows) == 284 and {key(r) for r in rows} == set(source)
        for r in rows:
            s = source[key(r)]
            assert r["bank_sha256"] == s["artifact_sha256"]
            d = r["logit_differences"]
            best = max(range(128), key=lambda i: d[i])
            assert best == r["float64_selected"]
            for field in ("usable", "positive_usable"):
                eligible = [i for i, u in enumerate(s["candidate_ious"])
                            if u > .5 and (field == "usable" or i in r["positive_indices"])]
                v = r[field]
                if not eligible:
                    assert v is None
                    continue
                q = max(eligible, key=lambda i: d[i])
                assert v["best_index"] == q and v["count"] == len(eligible)
                assert v["rank"] == 1 + sum(x > d[q] for x in d)
                assert v["tied_count"] == sum(x == d[q] for x in d)
                assert v["selected_margin"] == d[r["selected_index"]] - d[q]
                assert abs(v["best_probability"] - 1 / (1 + math.exp(-d[q]))) < 1e-12
        stats = dict(descriptions=284, missing_ids=[], score_order_disagreements=sum(
            r["selected_index"] != r["float64_selected"] for r in rows), strata={})
        for stratum in ("success", "recoverable", "bank_failure"):
            group = [r for r in rows if r["stratum"] == stratum]
            value = dict(descriptions=len(group))
            for field in ("usable", "positive_usable"):
                selected = [r[field] for r in group if r[field] is not None]
                value[field] = {metric: quantiles([v[metric] for v in selected])
                                for metric in ("rank", "selected_margin", "best_probability")}
            stats["strata"][stratum] = value
        result["models"][name] = stats
        independent_semantic(data["semantic_tests"][name])
        test = data["semantic_tests"][name]
        result["semantic"][name] = {k: test[k] for k in (
            "status", "padded_minus_base", "alternate_minus_base", "max_valid_gradient_change")}
        result["semantic"][name]["base_loss"] = test["base"]["loss"]
        result["semantic"][name]["padded_loss"] = test["padded"]["loss"]
        by_model[name] = {key(r): r for r in rows}
    # Pair only descriptions for which both fixed banks contain a usable mask.
    common = sorted(k for k in by_model["baseline"]
                    if all(by_model[n][k]["usable"] is not None for n in by_model))
    scenes = sorted({k[0] for k in common})
    scene_values = np.array([[np.mean([by_model[n][k]["usable"]["rank"]
                                      for k in common if k[0] == s])
                              for n in ("baseline", "m95")] for s in scenes])
    rng = np.random.default_rng(1999)
    draws = rng.integers(len(scenes), size=(10000, len(scenes)))
    bs = scene_values[draws].mean(1)
    result["paired_rank_bootstrap"] = dict(
        eligible_descriptions=len(common), eligible_physical_scenes=len(scenes),
        eligible_ids=common, within_scene_equal_description_mean=True,
        across_scene_equal_weight=True, seed=1999, resamples=10000,
        baseline_mean=float(scene_values[:, 0].mean()),
        m95_mean=float(scene_values[:, 1].mean()),
        difference=float(np.diff(scene_values, axis=1).mean()),
        difference_ci=np.quantile(bs[:, 1] - bs[:, 0], [.025, .975]).tolist(),
        limitation="Conditional intersection of banks with usable masks; not full dataset prevalence.")
    (OUT / "verification.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2)[:23000])


if __name__ == "__main__":
    main()
