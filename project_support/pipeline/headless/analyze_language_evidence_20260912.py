"""Offline candidate-evidence probe for the frozen M95 capture.

The script reads only immutable capture artifacts. It does not import the
production model, write a checkpoint, or use CUDA. Rank metrics are diagnostic:
they are not a substitute for a training-time causal test.
"""
import argparse
import json
import math
from pathlib import Path

import torch
import torch.nn.functional as F

EPS = 1e-8


def zscore(value):
    value = value.float()
    return (value - value.mean()) / value.std(unbiased=False).clamp_min(1e-6)


def rank_of(index, values):
    order = sorted(range(len(values)), key=lambda i: float(values[i]), reverse=True)
    return order.index(index)


def spearman(values, target):
    order = sorted(range(len(values)), key=lambda i: (float(values[i]), i))
    ranks = [0] * len(values)
    for rank, index in enumerate(order):
        ranks[index] = rank
    order = sorted(range(len(target)), key=lambda i: (float(target[i]), i))
    target_ranks = [0] * len(target)
    for rank, index in enumerate(order):
        target_ranks[index] = rank
    n = len(values)
    mean = (n - 1) / 2
    numerator = sum((ranks[i] - mean) * (target_ranks[i] - mean) for i in range(n))
    denominator = sum((ranks[i] - mean) ** 2 for i in range(n))
    return numerator / max(denominator, EPS)


def evidence_scores(tensors, language_override=None, point_permutation=None):
    mask = tensors["mask_logits"].float()
    query = tensors["query"].float()
    feats = tensors["inst_feats"].float()
    language = tensors["lang_feats"].float()
    valid = ~tensors["batch_mask"].bool()
    mask = mask[:, valid]
    feats = feats[valid]
    if point_permutation is not None:
        feats = feats[point_permutation]
    if language_override is not None:
        language, language_mask = language_override
        language = language.float()
        lang_valid = ~language_mask.bool()
    else:
        lang_valid = ~tensors["lang_masks"].bool()
    language = language[lang_valid]

    query = F.normalize(query, dim=-1)
    feats = F.normalize(feats, dim=-1)
    language = F.normalize(language, dim=-1)
    support = torch.sigmoid(mask).clamp(1e-4, 1.0 - 1e-4)
    support_sum = support.sum(dim=1, keepdim=True).clamp_min(EPS)

    region_query = (support @ feats) / support_sum
    region_language = (support @ feats) / support_sum
    query_region = F.cosine_similarity(query, region_query, dim=-1)
    language_region = F.cosine_similarity(
        language.mean(dim=0, keepdim=True).expand_as(region_language),
        region_language,
        dim=-1,
    )

    sim = language @ feats.T
    language_relevance = sim.max(dim=0).values
    language_prob = torch.sigmoid(language_relevance)
    language_soft = F.softmax(language_relevance / math.sqrt(feats.shape[-1]), dim=0)
    language_logit = torch.logit(language_prob.clamp(1e-4, 1.0 - 1e-4))

    support_mass = support @ language_soft
    support_mass_log = torch.log(support_mass.clamp_min(EPS))
    mean_relevance = (support @ language_soft) / support_sum.squeeze(-1)
    bernoulli = (
        support * torch.log(language_prob).unsqueeze(0)
        + (1.0 - support) * torch.log1p(-language_prob).unsqueeze(0)
    ).mean(dim=1)

    allocation = support / support.sum(dim=0, keepdim=True).clamp_min(EPS)
    allocation_sum = allocation.sum(dim=1).clamp_min(EPS)
    exclusive_mass = allocation @ language_soft
    exclusive_log = torch.log(exclusive_mass.clamp_min(EPS))
    exclusive_mean = (allocation @ language_soft) / allocation_sum
    exclusive_logodds = (allocation @ language_logit) / allocation_sum

    return {
        "query_region_cos": query_region,
        "language_region_cos": language_region,
        "language_support_mass": support_mass,
        "language_support_logmass": support_mass_log,
        "language_support_mean": mean_relevance,
        "language_bernoulli": bernoulli,
        "exclusive_language_mass": exclusive_mass,
        "exclusive_language_log": exclusive_log,
        "exclusive_language_mean": exclusive_mean,
        "exclusive_language_logodds": exclusive_logodds,
    }


def summarize(rows):
    recoverable = [row for row in rows if row["oracle_iou"] > 0.5 and row["indis_iou"] <= 0.5]
    success = [row for row in rows if row["oracle_iou"] > 0.5 and row["indis_iou"] > 0.5]
    return {
        "banks": len(rows),
        "oracle_recoverable": len(recoverable),
        "oracle_success": len(success),
        "mean_selected_iou": sum(row["selected_iou"] for row in rows) / len(rows),
        "selected_acc50": sum(row["selected_iou"] > 0.5 for row in rows) / len(rows),
        "recoverable_rescued": sum(row["selected_iou"] > 0.5 for row in recoverable),
        "success_harmed": sum(row["selected_iou"] <= 0.5 for row in success),
        "mean_oracle_rank": sum(row["oracle_rank"] for row in rows) / len(rows),
        "oracle_top5": sum(row["oracle_rank"] < 5 for row in rows) / len(rows),
    }


def evaluate(rows, name_to_score):
    metrics = {}
    for name, score in name_to_score.items():
        selected = int(score.argmax())
        row = rows[selected]
        metrics[name] = {
            "selected_index": selected,
            "selected_iou": row["oracle_iou"] if selected == row["oracle_index"] else row["candidate_ious"][selected],
            "oracle_rank": rank_of(row["oracle_index"], score.tolist()),
        }
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    capture = Path(args.capture)
    output = Path(args.out)
    summary = json.loads((capture / "summary.json").read_text(encoding="utf-8"))
    rows = summary["rows"]
    all_output = {}
    aggregate = {}
    controls = {}

    shuffled_language = {}
    for index, row in enumerate(rows):
        other = rows[(index + 1) % len(rows)]
        other_tensors = torch.load(
            capture / other["artifact"], map_location="cpu", weights_only=False
        )["tensors"]
        shuffled_language[row["artifact"]] = (
            other_tensors["lang_feats"],
            other_tensors["lang_masks"],
        )

    names = None
    for index, row in enumerate(rows):
        artifact = torch.load(capture / row["artifact"], map_location="cpu", weights_only=False)
        tensors = artifact["tensors"]
        candidate_ious = [
            float(((tensors["mask_logits"][candidate].float() > 0.0) &
                   tensors["gt_spmask"].bool()).sum())
            / max(float(((tensors["mask_logits"][candidate].float() > 0.0) |
                         tensors["gt_spmask"].bool()).sum()), 1.0)
            for candidate in range(tensors["mask_logits"].shape[0])
        ]
        row["candidate_ious"] = candidate_ious
        indis = tensors["indis_logits"].float()[:, 1]
        quality = tensors["quality_scores"].float()
        evidence = evidence_scores(tensors)
        shuffled = evidence_scores(tensors, language_override=shuffled_language[row["artifact"]])
        scores = {
            "indis": indis,
            "quality": quality,
            **{f"e_{name}": value for name, value in evidence.items()},
            **{f"shuffle_{name}": value for name, value in shuffled.items()},
        }
        if names is None:
            names = sorted(scores)
        bank = {}
        for name in names:
            score = scores[name]
            selected = int(score.argmax())
            bank[name] = {
                "selected_index": selected,
                "selected_iou": candidate_ious[selected],
                "oracle_rank": rank_of(int(row["oracle_index"]), score.tolist()),
            }
        all_output[f'{row["scene_id"]}/{row["object_id"]}/{row["ann_id"]}'] = {
            **{key: row[key] for key in (
                "scene_id", "object_id", "ann_id", "oracle_index", "oracle_iou",
                "indis_iou", "quality_iou",
            )},
            "methods": bank,
        }
        if (index + 1) % 25 == 0:
            print(f"ANALYZED {index + 1} of {len(rows)}", flush=True)

    for name in names:
        metrics = []
        for row in rows:
            record = all_output[f'{row["scene_id"]}/{row["object_id"]}/{row["ann_id"]}']
            metrics.append({
                "oracle_iou": row["oracle_iou"],
                "indis_iou": row["indis_iou"],
                **record["methods"][name],
            })
        aggregate[name] = summarize(metrics)

    output.write_text(json.dumps({
        "capture": str(capture),
        "capture_summary_sha256": __import__("hashlib").sha256(
            (capture / "summary.json").read_bytes()
        ).hexdigest(),
        "methods": aggregate,
        "banks": all_output,
        "limitation": (
            "Exploratory offline reranking of frozen banks. It neither trains "
            "nor establishes mechanism novelty or generalization."
        ),
    }, indent=2), encoding="utf-8")
    print(json.dumps(aggregate, indent=2), flush=True)


if __name__ == "__main__":
    main()
