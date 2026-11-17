"""Descriptive follow-up only: explain pair velocities, never select a new loss."""
import argparse
import json
from pathlib import Path

import torch

from source_head_interference_20260913 import flat_grad, logits
from d1_assignment_20260911 import sha


def main():
    parser = argparse.ArgumentParser()
    for name in ("protocol", "result", "capture", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    output = Path(args.output)
    assert not output.exists()
    protocol = json.loads(Path(args.protocol).read_text())
    result = json.loads(Path(args.result).read_text())
    assert result["protocol_sha256"] == sha(args.protocol)
    assert sha(protocol["checkpoint"]) == protocol["checkpoint_sha256"]
    state = torch.load(protocol["checkpoint"], map_location="cpu", weights_only=False)["model"]
    names = ["0.weight", "0.bias", "2.weight", "2.bias", "3.weight", "3.bias"]
    params = [state["dec.decoder_layers.5.indi_embedding." + n].double().clone().requires_grad_(True)
              for n in names]
    del state
    rows = []
    for r in result["rows"]:
        if r.get("pair_status") != "informative":
            continue
        artifact = Path(args.capture) / f"{r['scene_id']}_{r['object_id']}_{r['ann_id']}.pth"
        assert sha(artifact) == r["artifact_sha256"]
        bank = torch.load(artifact, map_location="cpu", weights_only=False)["tensors"]
        q = bank["query"].double()
        z = logits(q, params)
        d = z[:, 1] - z[:, 0]
        s, h = r["selected_index"], r["positive_index"]
        js, jh = flat_grad(d[s], params), flat_grad(d[h], params)
        kss, khh, ksh = float(js.dot(js)), float(jh.dot(jh)), float(js.dot(jh))
        y = torch.zeros(len(q), dtype=torch.bool)
        y[r["positive_indices"]] = True
        weights = torch.where(y, 1., protocol["eos_coef"]).float().double()
        c = (weights * (d.sigmoid() - y.double()) / int(y.sum())).detach()
        selected_component = -float(c[s]) * (kss - ksh)
        positive_component = -float(c[h]) * (ksh - khh)
        assert abs(selected_component + positive_component - r["v_pair"]) < 1e-8
        grouped = []
        offset = 0
        for name, p in zip(names, params):
            n = p.numel()
            a = js[offset:offset+n] - jh[offset:offset+n]
            gp = c[s] * js[offset:offset+n] + c[h] * jh[offset:offset+n]
            grouped.append(dict(parameter=name, v_pair=-float(a.dot(gp))))
            offset += n
        gt = bank["gt_spmask"].bool().flatten()
        masks = bank["mask_logits"].float().sigmoid() >= .5
        membership = set(r["positive_indices"])
        rows.append(dict(scene_id=r["scene_id"], object_id=r["object_id"], ann_id=r["ann_id"],
            recoverable=r["recoverable"], selected_positive=s in membership,
            positive_positive=s in membership and h in membership,
            selected_iou=r["selected_iou"], positive_iou=float(
                (masks[h] & gt).sum() / ((masks[h] | gt).sum().float() + 1e-6)),
            selected_probability=float(d[s].sigmoid().detach()),
            positive_probability=float(d[h].sigmoid().detach()),
            kss=kss, khh=khh, ksh=ksh,
            selected_self_minus_cross=kss-ksh, positive_cross_minus_self=ksh-khh,
            selected_component=selected_component, positive_component=positive_component,
            v_pair=r["v_pair"], v_head=r["v_head"], parameter_contributions=grouped))
    assert not torch.cuda.is_initialized()
    output.write_text(json.dumps(dict(result_sha256=sha(args.result), worker_sha256=sha(__file__),
        rows=rows, status="complete", limit="Post-result descriptive decomposition, not preregistered discovery or training causality."), indent=2))
    print(json.dumps([r for r in rows if r["recoverable"] and r["v_head"] > 0], indent=2))


if __name__ == "__main__":
    main()
