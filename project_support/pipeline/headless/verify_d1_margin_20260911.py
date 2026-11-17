"""Scalar readback and scene-level uncertainty for fixed score-gradient diagnostics."""
from datetime import datetime
import json
import math
import numpy as np
from prepare_d1_margin_20260911 import P, OUT
from d1_candidate_bank_20260911 import key, sha


def stats(values):
    if not values:
        return dict(n=0)
    return dict(n=len(values), mean=float(np.mean(values)), median=float(np.median(values)),
                q25=float(np.quantile(values,.25)), q75=float(np.quantile(values,.75)),
                minimum=float(min(values)), maximum=float(max(values)))


def main():
    protocol = json.loads((OUT / "protocol.json").read_text())
    data = json.loads((OUT / "margin.json").read_text())
    assert data["status"] == "complete" and len(data["rows"]) == 568
    assert data["protocol_sha256"] == sha(OUT / "protocol.json")
    assert data["worker_sha256"] == sha(P / "headless/d1_margin_20260911.py")
    ordering = json.loads((P / "reports/d1_ordering_20260911-1210/ordering.json").read_text())
    prior = {(r["model"], *key(r)): r for r in ordering["rows"]}
    verification = dict(status="passed", created=datetime.now().isoformat(),
                        margin_sha256=sha(OUT / "margin.json"), records=568,
                        source_gradient_max_error=max(r["source_gradient_max_error"] for r in data["rows"]),
                        models={})
    by_model = {}
    for name in ("baseline", "m95"):
        rr = [r for r in data["rows"] if r["model"] == name]
        by_model[name] = {key(r): r for r in rr}
        assert len(rr) == 284 and len(by_model[name]) == 284
        assert set(by_model[name]) == {tuple(k) for k in protocol["ids"]}
        for r in rr:
            o = prior[(name, *key(r))]
            d = o["logit_differences"]
            s = r["selected_index"]
            for field in ("usable", "positive_usable"):
                pr = r[field]
                if pr is None:
                    assert o[field] is None
                    continue
                h = pr["best_index"]
                ps, ph = [1/(1+math.exp(-d[i])) for i in (s,h)]
                ws, wh = [1 if v else float(np.float32(.1)) for v in (
                    pr["selected_label"],pr["eligible_label"])]
                gs = ws*(ps-int(pr["selected_label"]))/r["positive_count"]
                gh = wh*(ph-int(pr["eligible_label"]))/r["positive_count"]
                assert abs(pr["selected_g"]-gs) < 1e-12
                assert abs(pr["eligible_g"]-gh) < 1e-12
                assert abs(pr["margin_velocity"]+2*(gs-gh)) < 1e-12
                assert abs(pr["normalized_correction"]-2*r["positive_count"]*(gs-gh)) < 1e-12
                assert pr["margin"] == d[s]-d[h]
                assert pr["same_candidate"] == (s == h)
        model = dict(descriptions=284, physical_scenes=len({r["scene_id"] for r in rr}), strata={})
        for stratum in ("all", "success", "recoverable", "bank_failure"):
            group = [r for r in rr if stratum == "all" or r["stratum"] == stratum]
            record = dict(descriptions=len(group), selected_positive=sum(r["selected_positive"] for r in group))
            for field in ("usable", "positive_usable"):
                vv = [r[field] for r in group if r[field] is not None]
                record[field] = dict(
                    eligible=len(vv), missing=len(group)-len(vv),
                    same_candidate=sum(v["same_candidate"] for v in vv),
                    decreasing=sum(v["margin_velocity"] < -1e-12 for v in vv),
                    increasing=sum(v["margin_velocity"] > 1e-12 for v in vv),
                    zero_within_1e12=sum(abs(v["margin_velocity"]) <= 1e-12 for v in vv),
                    selected_negative_eligible_positive=sum(not v["selected_label"] and v["eligible_label"] for v in vv),
                    selected_positive_eligible_negative=sum(v["selected_label"] and not v["eligible_label"] for v in vv),
                    **{f:stats([v[f] for v in vv]) for f in (
                        "margin","margin_velocity","normalized_correction","selected_probability","eligible_probability")})
            model["strata"][stratum] = record
        verification["models"][name] = model
    names = ("baseline","m95")
    common = sorted(k for k in by_model["baseline"]
                    if all(by_model[n][k]["positive_usable"] is not None for n in names))
    scenes = sorted({k[0] for k in common})
    values = np.array([[np.mean([by_model[n][k]["positive_usable"]["margin"]
                                for k in common if k[0] == s]) for n in names] for s in scenes])
    rng = np.random.default_rng(protocol["bootstrap_seed"])
    draws = rng.integers(len(scenes),size=(protocol["bootstrap_resamples"],len(scenes)))
    delta = values[:,1]-values[:,0]
    verification["paired_H_margin"] = dict(
        ids=common, descriptions=len(common), scenes=len(scenes),
        baseline=float(values[:,0].mean()), m95=float(values[:,1].mean()),
        delta=float(delta.mean()), ci=np.quantile(delta[draws].mean(1),[.025,.975]).tolist(),
        weighting="Equal eligible descriptions within scene then equal scenes; paired scene resampling",
        seed=1999,resamples=10000,
        limitation="Conditional on usable positive in both banks; not prevalence or causal inference.")
    all_ids = sorted(by_model["baseline"])
    all_scenes = sorted({k[0] for k in all_ids})
    verification["paired_rates"] = {}
    predicates = {
        "recoverable_H_selected_negative": lambda r: r["stratum"] == "recoverable" and
        r["positive_usable"] is not None and not r["selected_positive"],
        "usable_but_no_H": lambda r: r["usable"] is not None and r["positive_usable"] is None,
    }
    for label, pred in predicates.items():
        vals = np.array([[np.mean([pred(by_model[n][k]) for k in all_ids if k[0] == s])
                          for n in names] for s in all_scenes])
        draws = rng.integers(len(all_scenes),size=(10000,len(all_scenes)))
        delta = vals[:,1]-vals[:,0]
        verification["paired_rates"][label] = dict(
            descriptions=284, scenes=len(all_scenes),
            baseline_count=sum(pred(r) for r in by_model["baseline"].values()),
            m95_count=sum(pred(r) for r in by_model["m95"].values()),
            baseline=float(vals[:,0].mean()),m95=float(vals[:,1].mean()),
            delta=float(delta.mean()),ci=np.quantile(delta[draws].mean(1),[.025,.975]).tolist(),
            seed=1999,resamples=10000,weighting="Equal four descriptions per scene, equal71scenes")
    (OUT / "verification.json").write_text(json.dumps(verification, indent=2))
    print(json.dumps({n:r["strata"]["recoverable"] for n,r in verification["models"].items()}, indent=2))
    print("PAIRED",json.dumps({k:v for k,v in verification["paired_H_margin"].items() if k != "ids"}))
    print("RATES",json.dumps(verification["paired_rates"]))


if __name__ == "__main__":
    main()
