"""CPU-only score/IoU calibration audit over already saved candidate banks.

This worker reads the immutable expansion artifacts. It does not load a model,
run a forward pass, modify a checkpoint, or access ScanRefer samples.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ranks(values):
    order = sorted(range(len(values)), key=lambda index: values[index])
    result = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        average = (start + end - 1) / 2.0 + 1.0
        for index in order[start:end]:
            result[index] = average
        start = end
    return result


def pearson(left, right):
    if len(left) != len(right) or not left:
        return None
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    numerator = sum((a - left_mean) * (b - right_mean)
                    for a, b in zip(left, right))
    left_ss = sum((a - left_mean) ** 2 for a in left)
    right_ss = sum((b - right_mean) ** 2 for b in right)
    denominator = math.sqrt(left_ss * right_ss)
    return numerator / denominator if denominator else None


def spearman(left, right):
    return pearson(ranks(left), ranks(right))


def kendall_tau_b(left, right):
    concordant = discordant = left_ties = right_ties = 0
    for i in range(len(left)):
        for j in range(i + 1, len(left)):
            dl = left[i] - left[j]
            dr = right[i] - right[j]
            if dl == 0 and dr == 0:
                left_ties += 1
                right_ties += 1
            elif dl == 0:
                left_ties += 1
            elif dr == 0:
                right_ties += 1
            elif dl * dr > 0:
                concordant += 1
            else:
                discordant += 1
    denominator = math.sqrt(
        (concordant + discordant + left_ties)
        * (concordant + discordant + right_ties))
    return (concordant - discordant) / denominator if denominator else None


def ndcg(relevance, ranking):
    def dcg(order):
        total = 0.0
        for position, index in enumerate(order):
            gain = (2.0 ** relevance[index]) - 1.0
            total += gain / math.log2(position + 2.0)
        return total
    predicted = dcg(ranking)
    ideal_order = sorted(range(len(relevance)),
                         key=lambda index: relevance[index], reverse=True)
    ideal = dcg(ideal_order)
    return predicted / ideal if ideal else None


def finite(value):
    return value is not None and math.isfinite(value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--source-sha256", required=True)
    args = parser.parse_args()
    root = Path(args.root)
    output = Path(args.out)
    if output.exists():
        raise SystemExit(f"refusing to overwrite {output}")
    actual_source_sha256 = sha256(__file__)
    expected_source_sha256 = args.source_sha256.strip()
    if actual_source_sha256 != expected_source_sha256:
        raise SystemExit(
            f"source hash mismatch: file={__file__} "
            f"actual={actual_source_sha256} "
            f"expected={expected_source_sha256!r} "
            f"len={len(expected_source_sha256)}")

    import torch

    rows = []
    for model in ("baseline", "m95"):
        model_dir = root / model
        banks = sorted(model_dir.glob("*.pth"))
        if len(banks) != 284:
            raise SystemExit(f"{model}: expected 284 banks, got {len(banks)}")
        for bank_path in banks:
            bank = torch.load(bank_path, map_location="cpu",
                              weights_only=False)
            ious = [float(value) for value in bank["metrics"]["candidate_ious"]]
            score_logits = bank["score_logits"].float()
            mask_probabilities = torch.sigmoid(bank["mask_logits"].float())
            if score_logits.ndim != 2 or score_logits.shape[1] != 2:
                raise SystemExit(f"bad score shape in {bank_path}")
            probabilities = torch.softmax(score_logits, dim=-1)[:, 1].tolist()
            soft_area = mask_probabilities.mean(dim=-1).tolist()
            binary_area = (mask_probabilities >= 0.5).float().mean(dim=-1).tolist()
            if len(ious) != len(probabilities) or not ious:
                raise SystemExit(f"candidate mismatch in {bank_path}")
            selected = int(bank["metrics"]["selected_index"])
            oracle = int(bank["metrics"]["oracle_index"])
            score_order = sorted(range(len(probabilities)),
                                 key=lambda index: probabilities[index],
                                 reverse=True)
            soft_area_order = sorted(range(len(soft_area)),
                                     key=lambda index: soft_area[index],
                                     reverse=True)
            binary_area_order = sorted(range(len(binary_area)),
                                       key=lambda index: binary_area[index],
                                       reverse=True)
            score_rank = ranks(probabilities)
            area_rank = ranks(binary_area)
            fused_rank = [
                score_rank[index] + area_rank[index]
                for index in range(len(ious))
            ]
            fused_order = sorted(range(len(ious)),
                                 key=lambda index: fused_rank[index])
            iou_order = sorted(range(len(ious)),
                               key=lambda index: ious[index], reverse=True)
            top5 = score_order[:5]
            top1 = score_order[0]
            if top1 != selected:
                raise SystemExit(f"selected mismatch in {bank_path}")
            selected_iou = ious[selected]
            oracle_iou = ious[oracle]
            if oracle_iou > 0.5 and selected_iou <= 0.5:
                stratum = "recoverable"
            elif oracle_iou <= 0.5:
                stratum = "bank_failure"
            else:
                stratum = "success"
            positive_scores = [probabilities[index] for index in range(len(ious))
                               if ious[index] > 0.5]
            rows.append({
                "model": model,
                "identity": bank["identity"],
                "artifact": bank_path.name,
                "artifact_sha256": sha256(bank_path),
                "stratum": stratum,
                "candidate_count": len(ious),
                "selected_index": selected,
                "oracle_index": oracle,
                "selected_iou": selected_iou,
                "oracle_iou": oracle_iou,
                "score_of_selected": probabilities[selected],
                "score_of_oracle": probabilities[oracle],
                "oracle_score_rank": score_order.index(oracle) + 1,
                "selected_iou_rank": iou_order.index(selected) + 1,
                "top5_contains_oracle": oracle in top5,
                "top5_oracle_count": sum(1 for index in top5 if ious[index] > 0.5),
                "points_iou_positive": sum(1 for value in ious if value > 0.5),
                "positive_score_max": max(positive_scores) if positive_scores else None,
                "spearman": spearman(probabilities, ious),
                "kendall_tau_b": kendall_tau_b(probabilities, ious),
                "ndcg_continuous": ndcg(ious, score_order),
                "ndcg_binary": ndcg([1.0 if value > 0.5 else 0.0 for value in ious],
                                    score_order),
                "soft_area_spearman": spearman(soft_area, ious),
                "soft_area_top5_contains_oracle": oracle in soft_area_order[:5],
                "binary_area_spearman": spearman(binary_area, ious),
                "binary_area_top5_contains_oracle": oracle in binary_area_order[:5],
                "rank_fused_top5_contains_oracle": oracle in fused_order[:5],
            })

    def summarize(selection):
        values = [row for row in rows if selection(row)]
        numeric = [
            "spearman", "kendall_tau_b", "ndcg_continuous", "ndcg_binary",
            "soft_area_spearman", "binary_area_spearman",
        ]
        summary = {
            "banks": len(values),
            "top1_contains_oracle": sum(
                row["oracle_index"] == row["selected_index"] for row in values),
            "top5_contains_oracle": sum(
                row["top5_contains_oracle"] for row in values),
            "soft_area_top5_contains_oracle": sum(
                row["soft_area_top5_contains_oracle"] for row in values),
            "binary_area_top5_contains_oracle": sum(
                row["binary_area_top5_contains_oracle"] for row in values),
            "rank_fused_top5_contains_oracle": sum(
                row["rank_fused_top5_contains_oracle"] for row in values),
            "recoverable": sum(row["stratum"] == "recoverable"
                               for row in values),
            "bank_failure": sum(row["stratum"] == "bank_failure"
                                for row in values),
        }
        for name in numeric:
            usable = [row[name] for row in values if finite(row[name])]
            summary[name] = (
                sum(usable) / len(usable) if usable else None)
        return summary

    summary = {
        "all": summarize(lambda row: True),
        "baseline": summarize(lambda row: row["model"] == "baseline"),
        "m95": summarize(lambda row: row["model"] == "m95"),
        "baseline_recoverable": summarize(
            lambda row: row["model"] == "baseline"
            and row["stratum"] == "recoverable"),
        "m95_recoverable": summarize(
            lambda row: row["model"] == "m95"
            and row["stratum"] == "recoverable"),
        "baseline_success": summarize(
            lambda row: row["model"] == "baseline"
            and row["stratum"] == "success"),
        "m95_success": summarize(
            lambda row: row["model"] == "m95"
            and row["stratum"] == "success"),
    }
    tests = {
        "perfect_spearman": spearman([0.0, 1.0, 2.0], [0.0, 1.0, 2.0]),
        "reverse_spearman": spearman([0.0, 1.0, 2.0], [2.0, 1.0, 0.0]),
        "tie_spearman": spearman([0.0, 0.0, 1.0], [0.0, 1.0, 1.0]),
        "perfect_ndcg": ndcg([0.0, 1.0, 2.0], [2, 1, 0]),
        "reverse_ndcg": ndcg([0.0, 1.0, 2.0], [0, 1, 2]),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "source_sha256": args.source_sha256,
        "root": str(root),
        "summary": summary,
        "tests": tests,
        "rows": rows,
    }, indent=2), encoding="utf-8")
    print(json.dumps({"summary": summary, "tests": tests}, indent=2))


if __name__ == "__main__":
    main()
