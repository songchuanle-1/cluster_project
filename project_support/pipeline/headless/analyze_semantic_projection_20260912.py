"""Offline diagnostic for the discarded semantic-alignment projection.

The frozen M95 checkpoint trains ``proj_query`` and ``proj_token`` through
``loss_sem_align``.  Inference currently ignores both tensors.  This script
tests whether they contain new candidate-selection evidence on the same frozen
diagnostic banks.  It is evaluation-only and does not establish a mechanism,
novelty, or permission to train.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import torch
import torch.nn.functional as F


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rank_of(index, values):
    order = sorted(range(len(values)), key=lambda i: float(values[i]), reverse=True)
    return order.index(index)


def bank_iou(mask_logits, gt_spmask):
    support = mask_logits.float() > 0.0
    gt = gt_spmask.bool()
    intersection = (support & gt.unsqueeze(0)).sum(dim=1).float()
    union = (support | gt.unsqueeze(0)).sum(dim=1).float().clamp_min(1.0)
    return intersection / union


def valid_tokens(lang_masks, proj_token):
    valid = ~lang_masks.bool()
    if valid.ndim == 2:
        valid = valid[0]
    token = proj_token.float()
    if not valid.any():
        raise ValueError("No valid language tokens")
    return token[valid], valid


def semantic_scores(proj_query, proj_token, lang_masks):
    query = F.normalize(proj_query.float(), dim=-1)
    token, _ = valid_tokens(lang_masks, proj_token)
    token = F.normalize(token, dim=-1)
    cosine = query @ token.T
    count = cosine.shape[1]
    train_temperature = 0.07

    max_cos = cosine.max(dim=1).values
    mean_cos = cosine.mean(dim=1)
    lse_cos = torch.logsumexp(cosine, dim=1) - math.log(count)
    lse_train = (
        torch.logsumexp(cosine / train_temperature, dim=1)
        - math.log(count)
    )
    top2 = cosine.topk(k=min(2, count), dim=1).values
    margin_top2 = top2[:, 0] - top2[:, 1] if count >= 2 else torch.zeros_like(top2[:, 0])

    # Average candidate-normalized log likelihood for each text token.
    token_logits = cosine / train_temperature
    token_contrast = (
        token_logits - torch.logsumexp(token_logits, dim=0, keepdim=True)
    ).mean(dim=1)

    return {
        "sem_max_cos": max_cos,
        "sem_mean_cos": mean_cos,
        "sem_lse_cos": lse_cos,
        "sem_lse_train_tau": lse_train,
        "sem_margin_top2": margin_top2,
        "sem_token_contrast_train_tau": token_contrast,
    }


def score_bundle(tensors, language_override=None):
    scores = {}
    indis_softmax = F.softmax(tensors["indis_logits"].float(), dim=-1)
    scores["indis_softmax"] = indis_softmax[:, 1]
    scores["indis_logit_margin"] = (
        tensors["indis_logits"].float()[:, 1] - tensors["indis_logits"].float()[:, 0]
    )
    scores["quality"] = tensors["quality_scores"].float()

    if language_override is None:
        proj_token = tensors["proj_token"]
        lang_masks = tensors["lang_masks"]
    else:
        proj_token, lang_masks = language_override
    scores.update(
        semantic_scores(tensors["proj_query"], proj_token, lang_masks)
    )
    return scores


def summarize(rows, method_values, method_rows, base_indices):
    result = {}
    for method, values in method_values.items():
        row_indices = method_rows[method]
        subset = [rows[index] for index in row_indices]
        recoverable = [
            row
            for row in subset
            if row["oracle_iou"] > 0.5 and row["indis_iou"] <= 0.5
        ]
        success = [
            row
            for row in subset
            if row["oracle_iou"] > 0.5 and row["indis_iou"] > 0.5
        ]
        selected_iou = [value["selected_iou"] for value in values]
        result[method] = {
            "banks": len(subset),
            "oracle_recoverable": len(recoverable),
            "oracle_success": len(success),
            "mean_selected_iou": sum(selected_iou) / len(selected_iou),
            "selected_acc50": sum(value > 0.5 for value in selected_iou) / len(selected_iou),
            "recoverable_rescued": sum(
                value > 0.5
                for row, value in zip(subset, selected_iou)
                if row["oracle_iou"] > 0.5 and row["indis_iou"] <= 0.5
            ),
            "success_harmed": sum(
                value <= 0.5
                for row, value in zip(subset, selected_iou)
                if row["oracle_iou"] > 0.5 and row["indis_iou"] > 0.5
            ),
            "mean_oracle_rank": sum(value["oracle_rank"] for value in values) / len(values),
            "oracle_top5": sum(value["oracle_rank"] < 5 for value in values) / len(values),
            "changed_from_indis": sum(
                value["selected_index"] != base_indices[row_index]
                for row_index, value in zip(row_indices, values)
            ),
        }
    return result


def category_map(source_path):
    records = json.loads(Path(source_path).read_text(encoding="utf-8"))
    result = {}
    for record in records:
        key = (
            record["scene_id"],
            str(record["object_id"]),
            str(record["ann_id"]),
        )
        result[key] = record["object_name"]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True)
    parser.add_argument("--source", default="")
    parser.add_argument("--out", default="-")
    args = parser.parse_args()

    capture = Path(args.capture)
    summary = json.loads((capture / "summary.json").read_text(encoding="utf-8"))
    rows = summary["rows"]
    if len(rows) != 284:
        raise ValueError(f"Expected 284 frozen banks, found {len(rows)}")

    categories = category_map(args.source) if args.source else {}
    category_to_indices = {}
    for index, row in enumerate(rows):
        key = (row["scene_id"], str(row["object_id"]), str(row["ann_id"]))
        category = categories.get(key)
        if category:
            category_to_indices.setdefault(category, []).append(index)

    per_bank = {}
    method_values = {}
    method_rows = {}
    base_indices = []
    for index, row in enumerate(rows):
        artifact = torch.load(
            capture / row["artifact"], map_location="cpu", weights_only=False
        )
        tensors = artifact["tensors"]
        candidate_ious = bank_iou(tensors["mask_logits"], tensors["gt_spmask"]).tolist()
        oracle_index = int(max(range(len(candidate_ious)), key=candidate_ious.__getitem__))
        indis_scores = F.softmax(tensors["indis_logits"].float(), dim=-1)[:, 1]
        indis_index = int(indis_scores.argmax())
        base_indices.append(indis_index)

        next_row = rows[(index + 1) % len(rows)]
        next_tensors = torch.load(
            capture / next_row["artifact"], map_location="cpu", weights_only=False
        )["tensors"]
        shuffled = (next_tensors["proj_token"], next_tensors["lang_masks"])

        same_category = None
        key = (row["scene_id"], str(row["object_id"]), str(row["ann_id"]))
        category = categories.get(key)
        if category:
            peers = category_to_indices.get(category, [])
            peer_indices = [peer for peer in peers if peer != index]
            if peer_indices:
                peer = peer_indices[index % len(peer_indices)]
                peer_tensors = torch.load(
                    capture / rows[peer]["artifact"],
                    map_location="cpu",
                    weights_only=False,
                )["tensors"]
                same_category = (
                    peer_tensors["proj_token"],
                    peer_tensors["lang_masks"],
                )

        methods = {}
        method_scores = {
            "base": score_bundle(tensors),
            "shuffle_language": score_bundle(tensors, language_override=shuffled),
        }
        if same_category is not None:
            method_scores["shuffle_same_category"] = score_bundle(
                tensors, language_override=same_category
            )
        for prefix, scores in method_scores.items():
            for name, values in scores.items():
                method_name = name if prefix == "base" else f"{prefix}_{name}"
                selected = int(values.argmax())
                methods[method_name] = {
                    "selected_index": selected,
                    "selected_iou": candidate_ious[selected],
                    "oracle_rank": rank_of(oracle_index, values.tolist()),
                }

        if oracle_index != int(row["oracle_index"]):
            raise ValueError(f"Oracle index mismatch at {row['artifact']}")
        per_bank[f'{row["scene_id"]}/{row["object_id"]}/{row["ann_id"]}'] = {
            "artifact": row["artifact"],
            "category": category,
            "candidate_ious": candidate_ious,
            "oracle_index": oracle_index,
            "indis_index": indis_index,
            "methods": methods,
        }
        for name, value in methods.items():
            method_values.setdefault(name, []).append(value)
            method_rows.setdefault(name, []).append(index)
        if (index + 1) % 25 == 0:
            print(f"ANALYZED {index + 1} of {len(rows)}", file=sys.stderr, flush=True)

    result = {
        "capture": str(capture),
        "capture_summary_sha256": sha256(capture / "summary.json"),
        "worker_sha256": summary.get("worker_sha256"),
        "source": args.source,
        "source_sha256": sha256(args.source) if args.source else None,
        "methods": summarize(rows, method_values, method_rows, base_indices),
        "banks": per_bank,
        "limitation": (
            "Exploratory offline reranking of frozen candidate banks. The "
            "semantic projection is already trained. No training-time "
            "causality, novelty, or deployable gain is established."
        ),
    }
    text = json.dumps(result, indent=2)
    if args.out == "-":
        print(text)
    else:
        Path(args.out).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
