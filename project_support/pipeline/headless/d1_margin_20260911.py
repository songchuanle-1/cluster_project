"""Independent NumPy score-gradient audit using immutable source-autograd records."""
from datetime import datetime
import json
from pathlib import Path
import time
import numpy as np
from d1_candidate_bank_20260911 import sha, key
from prepare_d1_margin_20260911 import ROOT, P, OUT


def gradient(z, y, eos):
    d = z[:, 1]-z[:, 0]
    p = np.exp(-np.logaddexp(0, -d))
    w = np.where(y, 1., float(np.float32(eos)))
    g = w*(p-y)/sum(y)
    return d, p, g


def loss(z, y, eos):
    d = z[:, 1]-z[:, 0]
    w = np.where(y, 1., float(np.float32(eos)))
    return float((w*(np.logaddexp(0, d)-y*d)).sum()/sum(y))


def synthetic():
    records = []
    for ys, yh in ((0, 0), (0, 1), (1, 0), (1, 1)):
        z = np.array([[0., 1.], [0., .2], [.1, -.2]])
        y = np.array([ys, yh, 1], dtype=bool)
        d, p, g = gradient(z, y, .1)
        analytic = -2*(g[0]-g[1])
        gz = np.stack((-g, g), 1)
        eps = 1e-5
        zz = z-eps*gz
        numeric = (((zz[0, 1]-zz[0, 0])-(zz[1, 1]-zz[1, 0]))-(d[0]-d[1]))/eps
        assert abs(numeric-analytic) < 1e-8
        fd_errors = []
        for i in range(3):
            for c in range(2):
                zp, zm = z.copy(), z.copy()
                zp[i, c] += eps
                zm[i, c] -= eps
                fd = (loss(zp, y, .1)-loss(zm, y, .1))/(2*eps)
                fd_errors.append(abs(fd-gz[i, c]))
        assert max(fd_errors) < 1e-8
        assert (analytic > 0) == (ys == 1 and yh == 0)
        perm = [2, 0, 1]
        assert np.allclose(gradient(z[perm], y[perm], .1)[2], g[perm])
        records.append(dict(labels=[ys, yh], velocity=analytic,
                            direction_fd_error=abs(numeric-analytic), loss_fd_error=max(fd_errors)))
    tie = np.zeros((3, 2))
    y = np.array([1, 1, 0], bool)
    assert gradient(tie, y, .1)[2][0] == gradient(tie, y, .1)[2][1]
    z = np.array([[0., 1000.], [0., -1000.], [0., 0.]])
    assert np.isfinite(gradient(z, y, .1)[2]).all() and np.isfinite(loss(z,y,.1))
    return dict(status="passed", label_pairs=records, tie=True, permutation=True,
                saturation=True, empty_set_handled=True)


def pair(d, p, g, labels, eligible, s, m):
    ids = np.flatnonzero(eligible)
    if not len(ids):
        return None
    h = int(ids[np.argmax(d[ids])])
    margin = float(d[s]-d[h])
    assert margin >= 0
    return dict(best_index=h, eligible_count=len(ids), selected_label=bool(labels[s]),
                eligible_label=bool(labels[h]), same_candidate=h == s, margin=margin,
                selected_probability=float(p[s]), eligible_probability=float(p[h]),
                selected_g=float(g[s]), eligible_g=float(g[h]),
                margin_velocity=-2*float(g[s]-g[h]),
                normalized_correction=2*m*float(g[s]-g[h]))


def main():
    assert not (OUT / "margin.json").exists()
    start = time.monotonic()
    protocol = json.loads((OUT / "protocol.json").read_text())
    for rel, digest in protocol["source_hashes"].items():
        assert sha(ROOT / "Cluster" / rel) == digest
    sources = {"assignment": P / "reports/d1_assignment_20260911-1113/assignment.json",
               "ordering": P / "reports/d1_ordering_20260911-1210/ordering.json",
               "assignment_verification": P / "reports/d1_assignment_20260911-1113/verification.json",
               "ordering_verification": P / "reports/d1_ordering_20260911-1210/verification.json"}
    assert all(sha(path) == protocol["input_hashes"][name] for name,path in sources.items())
    a, o = [json.loads(sources[n].read_text()) for n in ("assignment", "ordering")]
    ar = {(r["model"], *key(r)):r for r in a["rows"]}
    tests, rows = synthetic(), []
    for name in ("baseline", "m95"):
        sp = P / f"reports/d1_expansion_20260911-0715/{name}/summary.json"
        assert sha(sp) == protocol["summary_hashes"][name]
        summary = {key(r): r for r in json.loads(sp.read_text())["rows"]}
        assert set(summary) == {tuple(k) for k in protocol["ids"]}
        for r in (r for r in o["rows"] if r["model"] == name):
            old = ar[(name, *key(r))]
            sr = summary[key(r)]
            assert r["bank_sha256"] == old["bank_sha256"] == sr["artifact_sha256"]
            d = np.array(r["logit_differences"], float)
            z = np.stack((np.zeros_like(d), d), 1)
            labels = np.zeros(len(d), bool)
            labels[old["positive_indices"]] = True
            assert labels.sum() > 0 and len(d) == 128
            dd, prob, g = gradient(z, labels, protocol["models"][name]["eos_coef"])
            assert np.isfinite(d).all() and np.isfinite(g).all()
            stored = np.array(old["gradients_z1"])
            assert np.allclose(g, stored, atol=protocol["source_gradient_atol"],
                               rtol=protocol["source_gradient_rtol"])
            s = int(np.argmax(d))
            assert s == r["selected_index"] == sr["selected_index"]
            good = np.array(sr["candidate_ious"]) > .5
            m = int(labels.sum())
            fields = {n: pair(d, prob, g, labels, eligible, s, m)
                      for n, eligible in (("usable",good), ("positive_usable",good & labels))}
            for field, pr in fields.items():
                rr = r[field]
                assert (pr is None) == (rr is None)
                if pr is not None:
                    assert pr["best_index"] == rr["best_index"]
                    assert abs(pr["margin"]-rr["selected_margin"]) < 1e-12
            h = fields["positive_usable"]
            if h is not None:
                assert h["margin_velocity"] <= 1e-12
            rows.append(dict(model=name, scene_id=r["scene_id"], object_id=r["object_id"],
                             ann_id=r["ann_id"], bank_sha256=r["bank_sha256"],
                             selected_index=s, selected_positive=bool(labels[s]),
                             selected_iou=sr["selected_iou"], oracle_iou=sr["oracle_iou"],
                             stratum=r["stratum"], positive_count=m,
                             source_gradient_max_error=float(np.max(abs(g-stored))),
                             **fields))
    assert len(rows) == 568
    data = dict(status="complete", created=datetime.now().isoformat(), tests=tests, rows=rows,
                protocol_sha256=sha(OUT / "protocol.json"), worker_sha256=sha(__file__),
                elapsed_seconds=time.monotonic()-start, new_inference=False,
                limit="Independent two-logit gradients on evaluation candidates; not actual training or shared-parameter updates.")
    (OUT / "margin.json").write_text(json.dumps(data, indent=2))
    print("AUDIT",len(rows),data["elapsed_seconds"])


if __name__ == "__main__":
    main()
