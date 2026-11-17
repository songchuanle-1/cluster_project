"""D3 CPU-only geometry of wrong-instance selection on the frozen candidate banks.

Question: when a wrong candidate is selected, what is its spatial relation to the
correct instance's mask - sub-part, super-set/merge, or a disjoint other object?

This decides the shape of any admissible mechanism: part-vs-whole comparisons,
merge suppression, or cross-object instance discrimination, respectively.

Reads only the 568 frozen .pth banks. No model load, no inference, no CUDA,
no dataset sample, no queue or trainer change. Run on a CPU-only remote env.
"""
import argparse
import glob
import json
import math
from collections import Counter
from pathlib import Path

import torch


def ratios(a, b):
    inter = int((a & b).sum())
    denom = int(b.sum())
    return inter, denom


def classify(sel, orc):
    """Coarse relation of the selected mask to the oracle mask."""
    inter = int((sel & orc).sum())
    if inter == 0:
        return "disjoint"
    cov_orc = inter / max(1, int(orc.sum()))
    cov_sel = inter / max(1, int(sel.sum()))
    if cov_orc >= 0.9 and cov_sel >= 0.9:
        return "near_duplicate"
    if cov_orc >= 0.9 and cov_sel < 0.6:
        return "strict_subpart"
    if cov_sel >= 0.9 and cov_orc < 0.6:
        return "superset_or_merge"
    if cov_orc >= 0.5 or cov_sel >= 0.5:
        return "partial_overlap"
    return "small_overlap"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--banks", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for path in sorted(glob.glob(str(Path(args.banks) / "*" / "*.pth"))):
        model = Path(path).parent.name
        bank = torch.load(path, map_location="cpu", weights_only=False)
        m = bank["metrics"]
        sel, orc = int(m["selected_index"]), int(m["oracle_index"])
        logits = bank["mask_logits"]
        sel_m = logits[sel] >= 0.0
        orc_m = logits[orc] >= 0.0
        gt = bank["gt_spmask"] > 0.5
        ident = bank["identity"]
        rec = {
            "model": model,
            "scene_id": ident["scene_id"], "object_id": ident["object_id"],
            "ann_id": ident["ann_id"],
            "selected_iou": float(m["selected_iou"]),
            "oracle_iou": float(m["oracle_iou"]),
            "stratum": ("success" if float(m["oracle_iou"]) > 0.5
                        and float(m["selected_iou"]) > 0.5 else
                        "recoverable" if float(m["oracle_iou"]) > 0.5 else
                        "bank_failure"),
            "sel_size": int(sel_m.sum()), "orc_size": int(orc_m.sum()),
            "gt_size": int(gt.sum()),
            "sel_orc_inter": int((sel_m & orc_m).sum()),
            "sel_minus_orc": int((sel_m & ~orc_m).sum()),
            "orc_minus_sel": int((~sel_m & orc_m).sum()),
            "sel_in_gt": int((sel_m & gt).sum()),
            "orc_in_gt": int((orc_m & gt).sum()),
            "relation": classify(sel_m, orc_m),
        }
        if rec["stratum"] == "recoverable" and sel != orc:
            rec["sel_precision_in_gt"] = rec["sel_in_gt"] / max(1, rec["sel_size"])
            rec["sel_orc_containment"] = rec["sel_orc_inter"] / max(1, rec["orc_size"])
            rec["orc_sel_containment"] = rec["sel_orc_inter"] / max(1, rec["sel_size"])
            rec["wrong_is_outside_gt"] = 1.0 - rec["sel_precision_in_gt"]
        rows.append(rec)
        del bank, logits

    summary = {}
    for model in sorted({r["model"] for r in rows}):
        for stratum in ("recoverable", "success", "bank_failure"):
            g = [r for r in rows if r["model"] == model and r["stratum"] == stratum]
            if not g:
                continue
            rel = Counter(r["relation"] for r in g)
            entry = {"banks": len(g),
                     "relation_counts": dict(rel),
                     "relation_fractions": {k: round(v / len(g), 4)
                                            for k, v in rel.items()}}
            if stratum == "recoverable":
                prec = sorted(r["sel_precision_in_gt"] for r in g
                              if "sel_precision_in_gt" in r)
                cont = sorted(r["sel_orc_containment"] for r in g
                              if "sel_orc_containment" in r)
                if prec:
                    entry.update(
                        n_with_distinct_oracle=len(prec),
                        sel_precision_in_gt_median=round(prec[len(prec) // 2], 4),
                        sel_precision_in_gt_mean=round(sum(prec) / len(prec), 4),
                        wrong_mask_mostly_outside_gt=round(
                            sum(1 for p in prec if p < 0.5) / len(prec), 4),
                        sel_orc_containment_median=round(cont[len(cont) // 2], 4),
                    )
            summary.setdefault(model, {})[stratum] = entry

    payload = {"banks_root": args.banks, "n_banks": len(rows),
               "summary": summary, "rows": rows}
    (out / "mask_overlap.json").write_text(json.dumps(payload, indent=2))
    print(json.dumps(summary, indent=2))
    print("wrote", out / "mask_overlap.json")


if __name__ == "__main__":
    main()
