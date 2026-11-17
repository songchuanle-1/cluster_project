"""Fail-closed evaluator for the pre-registered PIRS terminal contract.

This script performs static validation and optional evaluation of paired native
captures. It does not launch models, modify training, or make an efficacy claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
import unittest
from collections import defaultdict
from pathlib import Path

from hierarchical_partition_contract_20260916 import (
    validate_hierarchical_partition,
    validate_hierarchical_row,
)


ROOT = Path(__file__).resolve().parents[1]
BASE_CLASS = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
PIRS_CLASS = BASE_CLASS + "_pirs"
PHYSICAL_KEYS = (
    "scene",
    "ann_id",
    "scene_occurrence",
    "dataset_index",
    "expression_slot",
    "original_superpoint_ids",
    "sample_inverse",
    "target_instances",
)


def _finite_probability(value: object) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value) and 0 <= value <= 1


def _validate_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(label + " hash is missing or invalid")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(label + " hash is missing or invalid") from exc
    return value


def validate_capture(capture: dict, expected_class: str) -> dict:
    if not capture.get("native_capture_completed"):
        raise ValueError("Native capture is incomplete")
    if capture.get("model_class") != expected_class:
        raise ValueError("Capture model class differs from the bound class")
    rows = capture.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Capture has no expression rows")
    _validate_sha256(capture.get("producer_sha256"), "Capture producer")
    _validate_sha256(capture.get("config_sha256"), "Capture config")
    checkpoint_sha256 = _validate_sha256(
        capture.get("checkpoint_sha256"), "Capture checkpoint")
    config_path = capture.get("config_path")
    if not isinstance(config_path, str) or not config_path:
        raise ValueError("Capture config path is missing")
    indexed = {}
    for row in rows:
        missing = [key for key in PHYSICAL_KEYS if key not in row]
        if missing:
            raise ValueError("Missing physical keys: " + ",".join(missing))
        key = (
            row["scene"],
            int(row["ann_id"]),
            int(row["scene_occurrence"]),
            int(row["dataset_index"]),
            int(row["expression_slot"]),
        )
        if key in indexed:
            raise ValueError("Duplicate expression observation")
        scores = row.get("scores")
        ious = row.get("ious")
        seeds = row.get("seed_inside")
        positives = row.get("native_positive")
        if not all(isinstance(values, list) for values in (scores, ious, seeds, positives)):
            raise ValueError("Missing query axes")
        if not scores or len({len(values) for values in (scores, ious, seeds, positives)}) != 1:
            raise ValueError("Query axes differ")
        if any(not _finite_probability(value) for value in scores + ious):
            raise ValueError("Invalid score or IoU")
        if any(value not in (0, 1, False, True) for value in seeds + positives):
            raise ValueError("Seed and positive axes must be binary")
        _validate_sha256(row.get("native_input_sha256"), "Native input")
        if row.get("checkpoint_sha256") != checkpoint_sha256:
            raise ValueError("Row checkpoint differs from the capture manifest")
        validate_hierarchical_row(row)
        order = sorted(range(len(scores)), key=lambda index: (-scores[index], index))
        if int(row.get("selected_query", -1)) != order[0]:
            raise ValueError("Native selected query differs from the contract")
        best_rank = next((rank for rank, index in enumerate(order, 1) if ious[index] > .5), None)
        if row.get("best_acceptable_rank") != best_rank:
            raise ValueError("Native best acceptable rank differs from the contract")
        indexed[key] = row
    return indexed


def pair_captures(baseline: dict, candidate: dict) -> list[tuple[dict, dict]]:
    left = validate_capture(baseline, BASE_CLASS)
    right = validate_capture(candidate, PIRS_CLASS)
    if left.keys() != right.keys():
        raise ValueError("Paired expression manifest differs")
    pairs = []
    for key in sorted(left):
        lhs, rhs = left[key], right[key]
        for field in PHYSICAL_KEYS:
            if lhs[field] != rhs[field]:
                raise ValueError("Physical support or target mismatch: " + field)
        if lhs["native_input_sha256"] != rhs["native_input_sha256"]:
            raise ValueError("Transformed native input mismatch")
        if lhs["hierarchical_partition_sha256"] != rhs["hierarchical_partition_sha256"]:
            raise ValueError("Hierarchical partition mismatch")
        pairs.append((lhs, rhs))
    return pairs


def selected_success(row: dict) -> bool:
    return row["ious"][row["selected_query"]] > .5


def best_acceptable_rank(row: dict) -> int | None:
    order = sorted(range(len(row["scores"])),
                   key=lambda index: (-row["scores"][index], index))
    return next((rank for rank, index in enumerate(order, 1)
                 if row["ious"][index] > .5), None)


def cell_mean(rows: list[dict], seed: bool, mask_ok: bool) -> float | None:
    values = [
        float(row["scores"][index])
        for row in rows
        for index in range(len(row["scores"]))
        if bool(row["seed_inside"][index]) == seed
        and (row["ious"][index] > .5) == mask_ok
    ]
    return sum(values) / len(values) if values else None


def scene_balanced_rate(rows: list[dict], predicate) -> float | None:
    groups = defaultdict(list)
    for row in rows:
        value = predicate(row)
        if value is not None:
            groups[row["scene"]].append(float(value))
    if not groups:
        return None
    return sum(sum(values) / len(values) for values in groups.values()) / len(groups)


def scene_selection_error(rows: list[dict]) -> float:
    groups = defaultdict(list)
    for row in rows:
        if best_acceptable_rank(row) is not None:
            groups[row["scene"]].append(float(not selected_success(row)))
    if not groups:
        raise ValueError("No expression has an acceptable query")
    return sum(sum(values) / len(values) for values in groups.values()) / len(groups)


def component_incidence(rows: list[dict]) -> dict:
    """Describe selected-query failures without changing the decision gates."""
    counts = defaultdict(int)
    counts["expressions"] = len(rows)
    for row in rows:
        index = row["selected_query"]
        selected_positive = bool(row["native_positive"][index])
        selected_acceptable = row["ious"][index] > .5
        any_acceptable = any(ious > .5 for ious in row["ious"])
        counts["selected_native_positive"] += int(selected_positive)
        counts["selected_mask_acceptable"] += int(selected_acceptable)
        counts["selected_positive_and_acceptable"] += int(
            selected_positive and selected_acceptable)
        if not selected_positive:
            counts["failure_selected_outside_native_positive"] += 1
            counts["failure_with_some_acceptable_query"] += int(any_acceptable)
            counts["failure_without_acceptable_query"] += int(not any_acceptable)
        elif not selected_acceptable:
            counts["failure_positive_with_unacceptable_mask"] += 1
    return dict(sorted(counts.items()))


def paired_component_transitions(pairs: list[tuple[dict, dict]]) -> dict:
    """Count fixed/broken pairs and the selected-positive change direction."""
    counts = defaultdict(int)
    counts["expressions"] = len(pairs)
    for baseline, candidate in pairs:
        base_success = selected_success(baseline)
        cand_success = selected_success(candidate)
        base_positive = bool(
            baseline["native_positive"][baseline["selected_query"]])
        cand_positive = bool(
            candidate["native_positive"][candidate["selected_query"]])
        counts["fixed"] += int(not base_success and cand_success)
        counts["broken"] += int(base_success and not cand_success)
        counts["fixed_with_positive_selection_gain"] += int(
            not base_success and cand_success
            and not base_positive and cand_positive)
        counts["broken_with_positive_selection_loss"] += int(
            base_success and not cand_success
            and base_positive and not cand_positive)
    return dict(sorted(counts.items()))


def scene_balanced_success(rows: list[dict]) -> float:
    groups = defaultdict(list)
    for row in rows:
        groups[row["scene"]].append(float(selected_success(row)))
    return sum(sum(values) / len(values) for values in groups.values()) / len(groups)


def scene_bootstrap_delta(pairs: list[tuple[dict, dict]], draws: int) -> list[float]:
    groups = defaultdict(list)
    for baseline, candidate in pairs:
        groups[baseline["scene"]].append(
            float(selected_success(candidate)) - float(selected_success(baseline)))
    deltas = [sum(values) / len(values) for values in groups.values()]
    rng = random.Random(1999)
    bootstrap = sorted(
        sum(rng.choices(deltas, k=len(deltas))) / len(deltas)
        for _ in range(draws))
    return [
        bootstrap[int(.025 * (draws - 1))],
        bootstrap[int(.975 * (draws - 1))],
    ]


def spearman(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        raise ValueError("Spearman inputs differ or are too short")

    def ranks(values):
        order = sorted(range(len(values)), key=lambda index: values[index])
        result = [0.0] * len(values)
        cursor = 0
        while cursor < len(order):
            end = cursor + 1
            while end < len(order) and values[order[end]] == values[order[cursor]]:
                end += 1
            rank = (cursor + end + 1) / 2
            for position in order[cursor:end]:
                result[position] = rank
            cursor = end
        return result

    rx, ry = ranks(left), ranks(right)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    numerator = sum((x - mx) * (y - my) for x, y in zip(rx, ry))
    denominator = math.sqrt(sum((x - mx) ** 2 for x in rx)
                            * sum((y - my) ** 2 for y in ry))
    if denominator == 0:
        raise ValueError("Spearman is undefined for a constant axis")
    return numerator / denominator


def evaluate_pirs(
    baseline: dict,
    candidate: dict,
    *,
    draws: int = 2000,
    baseline_peak_mib: float | None = None,
    candidate_peak_mib: float | None = None,
    candidate_goal_miou: float | None = None,
) -> dict:
    if draws < 1:
        raise ValueError("Positive bootstrap draws required")
    pairs = pair_captures(baseline, candidate)
    base_rows = [left for left, _ in pairs]
    pirs_rows = [right for _, right in pairs]

    p1_scores = {
        "baseline_seed_pos_mask_neg": cell_mean(base_rows, True, False),
        "baseline_seed_neg_mask_pos": cell_mean(base_rows, False, True),
        "pirs_seed_pos_mask_neg": cell_mean(pirs_rows, True, False),
        "pirs_seed_neg_mask_pos": cell_mean(pirs_rows, False, True),
    }
    p1_pass = (
        p1_scores["pirs_seed_pos_mask_neg"] is not None
        and p1_scores["pirs_seed_neg_mask_pos"] is not None
        and p1_scores["pirs_seed_pos_mask_neg"]
        < p1_scores["pirs_seed_neg_mask_pos"]
    )

    acceptable_ranks = [
        rank for row in pirs_rows if (rank := best_acceptable_rank(row)) is not None
    ]
    median_rank = statistics.median(acceptable_ranks)
    top5_rate = sum(rank <= 5 for rank in acceptable_ranks) / len(acceptable_ranks)
    baseline_error = scene_selection_error(base_rows)
    pirs_error = scene_selection_error(pirs_rows)
    p2_pass = median_rank <= 1 and top5_rate + 1e-12 >= .839 and pirs_error < baseline_error

    base_success = sum(selected_success(row) for row in base_rows) / len(base_rows)
    pirs_success = sum(selected_success(row) for row in pirs_rows) / len(pirs_rows)
    scene_delta = scene_balanced_success(pirs_rows) - scene_balanced_success(base_rows)
    ci = scene_bootstrap_delta(pairs, draws)
    p3_pass = scene_delta + 1e-12 >= .002

    spearman_values = [
        spearman(row["scores"], row["ious"]) for row in pirs_rows
    ]
    mask_only_collapse = (
        all(value >= .99 for value in spearman_values)
        and abs(pirs_error - baseline_error) <= 1e-12
    )

    resource_violation = None
    if (
        baseline_peak_mib is not None
        and candidate_peak_mib is not None
        and candidate_goal_miou is not None
    ):
        memory_ratio = candidate_peak_mib / baseline_peak_mib
        resource_violation = memory_ratio > 1.15 and candidate_goal_miou < .003

    rejection_reasons = []
    if not p1_pass:
        rejection_reasons.append("P1 failed: referent score did not reverse the seed-containment ordering")
    if not p2_pass and not p3_pass:
        rejection_reasons.append("P2/P3 failed: selection error did not fall and TRAIN success did not improve by .002")
    if mask_only_collapse:
        rejection_reasons.append("Referent ranking collapsed to mask-IoU ordering without selection improvement")
    if resource_violation:
        rejection_reasons.append("Peak memory rose by more than 15% with less than +.003 mIoU")

    if rejection_reasons:
        decision = "reject"
    elif p1_pass and p2_pass and p3_pass:
        decision = "pass"
    else:
        decision = "incomplete"

    return {
        "scope": "Pre-registered terminal PIRS contract on paired native captures; no goal-mIoU claim.",
        "expressions": len(pairs),
        "scenes": len({row["scene"] for row in pirs_rows}),
        "P1": {
            "scores": p1_scores,
            "passed": p1_pass,
            "predicate": "PIRS seed+/mask- mean score < seed-/mask+ mean score",
        },
        "P2": {
            "baseline_selection_error_scene_balanced": baseline_error,
            "pirs_selection_error_scene_balanced": pirs_error,
            "acceptable_expressions": len(acceptable_ranks),
            "median_acceptable_rank": median_rank,
            "top5_acceptable_rate": top5_rate,
            "passed": p2_pass,
        },
        "P3": {
            "baseline_success_pooled": base_success,
            "pirs_success_pooled": pirs_success,
            "scene_balanced_delta": scene_delta,
            "scene_bootstrap_95ci": ci,
            "passed": p3_pass,
            "threshold": .002,
        },
        "component_incidence": {
            "baseline": component_incidence(base_rows),
            "pirs": component_incidence(pirs_rows),
            "paired_transitions": paired_component_transitions(pairs),
            "role": "Descriptive failure attribution only; no decision threshold.",
        },
        "PIRS_spearman_score_ious_by_expression": spearman_values,
        "mask_only_collapse": mask_only_collapse,
        "resource_violation": resource_violation,
        "decision": decision,
        "rejection_reasons": rejection_reasons,
        "limitations": [
            "Superpoint selection is not goal mIoU.",
            "The evaluator requires exact paired support and target identity.",
            "The resource rejection is only evaluated when paired peak memory and goal mIoU are supplied.",
            "No statistical claim is made from this static contract run without native TERMINAL captures.",
        ],
    }


class ContractTests(unittest.TestCase):
    def row(self, *, scene="scene0001_00", scores=None, ious=None, seeds=None, positives=None,
            slot=0):
        scores = [.9, .2] if scores is None else scores
        ious = [.1, .8] if ious is None else ious
        seeds = [1, 0] if seeds is None else seeds
        positives = [1, 0] if positives is None else positives
        fps_positions = [[[0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0]]]
        cluster_ids = [[0, 0, 0], [0]]
        child_maps = [{"0": [0]}]
        partition_sha256 = validate_hierarchical_partition(
            len([0, 1, 2]), fps_positions, cluster_ids, child_maps)
        order = sorted(range(len(scores)), key=lambda index: (-scores[index], index))
        best_rank = next((rank for rank, index in enumerate(order, 1)
                          if ious[index] > .5), None)
        return {
            "scene": scene,
            "ann_id": 1,
            "scene_occurrence": slot,
            "dataset_index": slot,
            "expression_slot": slot,
            "original_superpoint_ids": [0, 1, 2],
            "sample_inverse": [0, 1, 2],
            "target_instances": [1],
            "scores": scores,
            "ious": ious,
            "seed_inside": seeds,
            "native_positive": positives,
            "selected_query": order[0],
            "best_acceptable_rank": best_rank,
            "native_input_sha256": "d" * 64,
            "checkpoint_sha256": "b" * 64,
            "hierarchical_fps_positions": fps_positions,
            "hierarchical_cluster_ids": cluster_ids,
            "hierarchical_child_maps": child_maps,
            "hierarchical_partition_sha256": partition_sha256,
        }

    def capture(self, model_class, rows):
        return {
            "native_capture_completed": True,
            "model_class": model_class,
            "producer_sha256": "a" * 64,
            "config_path": "configs/paired.yaml",
            "config_sha256": "c" * 64,
            "checkpoint_sha256": "b" * 64,
            "rows": rows,
        }

    def test_bound_model_classes_required(self):
        row = self.row()
        with self.assertRaises(ValueError):
            pair_captures(self.capture(BASE_CLASS, [row]),
                          self.capture(BASE_CLASS, [row]))

    def test_rank_recomputed_not_trusted(self):
        row = self.row()
        row["best_acceptable_rank"] = 1
        with self.assertRaises(ValueError):
            validate_capture(self.capture(BASE_CLASS, [row]), BASE_CLASS)

    def test_physical_pair_join(self):
        base = self.row()
        candidate = self.row(scores=[.9, .8], ious=[.7, .1], seeds=[1, 0])
        pairs = pair_captures(self.capture(BASE_CLASS, [base]),
                              self.capture(PIRS_CLASS, [candidate]))
        self.assertEqual(len(pairs), 1)

    def test_seed_ordering_reversal_passes(self):
        base0 = self.row(scores=[.9, .1], ious=[.1, .8], seeds=[1, 0], slot=0)
        base1 = self.row(scores=[.9, .1], ious=[.1, .8], seeds=[1, 0], slot=1)
        candidate0 = self.row(scores=[.9, .1], ious=[.8, .2], seeds=[0, 1], slot=0)
        candidate1 = self.row(scores=[.9, .1], ious=[.8, .2], seeds=[0, 1], slot=1)
        report = evaluate_pirs(
            self.capture(BASE_CLASS, [base0, base1]),
            self.capture(PIRS_CLASS, [candidate0, candidate1]),
            draws=20,
        )
        self.assertTrue(report["P1"]["passed"])
        self.assertEqual(report["decision"], "pass")

    def test_rejection_requires_concrete_reason(self):
        base = self.row(scores=[.9, .1], ious=[.1, .8], seeds=[1, 0])
        candidate = self.row(scores=[.9, .1], ious=[.1, .8], seeds=[1, 0])
        report = evaluate_pirs(
            self.capture(BASE_CLASS, [base]),
            self.capture(PIRS_CLASS, [candidate]),
            draws=20,
        )
        self.assertEqual(report["decision"], "reject")
        self.assertTrue(report["rejection_reasons"])

    def test_spearman_detects_monotone_ranking(self):
        self.assertAlmostEqual(spearman([1, 2, 3], [3, 2, 1]), -1)

    def test_component_incidence_separates_referent_and_mask_failures(self):
        rows = [
            self.row(scores=[.9, .2], ious=[.2, .8],
                     seeds=[0, 1], positives=[0, 1]),
            self.row(scores=[.9, .2], ious=[.7, .2],
                     seeds=[1, 0], positives=[1, 0]),
            self.row(scores=[.9, .2], ious=[.2, .3],
                     seeds=[1, 0], positives=[1, 0], slot=1),
        ]
        report = component_incidence(rows)
        self.assertEqual(report["selected_native_positive"], 2)
        self.assertEqual(report["selected_positive_and_acceptable"], 1)
        self.assertEqual(report["failure_selected_outside_native_positive"], 1)
        self.assertEqual(report["failure_with_some_acceptable_query"], 1)
        self.assertEqual(report["failure_positive_with_unacceptable_mask"], 1)

    def test_paired_component_transition_attributes_fixed_failure(self):
        baseline = self.row(scores=[.9, .2], ious=[.2, .8],
                            seeds=[0, 1], positives=[0, 1])
        candidate = self.row(scores=[.9, .2], ious=[.8, .2],
                             seeds=[0, 1], positives=[1, 0])
        report = paired_component_transitions([(baseline, candidate)])
        self.assertEqual(report["fixed"], 1)
        self.assertEqual(report["fixed_with_positive_selection_gain"], 1)
        self.assertEqual(report["broken"], 0)

    def test_native_input_identity_is_required(self):
        row = self.row()
        del row["native_input_sha256"]
        with self.assertRaisesRegex(ValueError, "Native input"):
            validate_capture(self.capture(BASE_CLASS, [row]), BASE_CLASS)

    def test_checkpoint_identity_is_bound_to_capture(self):
        row = self.row()
        row["checkpoint_sha256"] = "e" * 64
        with self.assertRaisesRegex(ValueError, "Row checkpoint"):
            validate_capture(self.capture(BASE_CLASS, [row]), BASE_CLASS)

    def test_hierarchical_partition_hash_is_revalidated(self):
        row = self.row()
        row["hierarchical_partition_sha256"] = "e" * 64
        with self.assertRaisesRegex(ValueError, "Hierarchical partition hash"):
            validate_capture(self.capture(BASE_CLASS, [row]), BASE_CLASS)

    def test_paired_native_input_identity_must_match(self):
        baseline = self.row()
        candidate = self.row()
        candidate["native_input_sha256"] = "e" * 64
        with self.assertRaisesRegex(ValueError, "Transformed native input"):
            pair_captures(
                self.capture(BASE_CLASS, [baseline]),
                self.capture(PIRS_CLASS, [candidate]),
            )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline")
    parser.add_argument("--candidate")
    parser.add_argument("--output")
    parser.add_argument("--draws", type=int, default=2000)
    parser.add_argument("--self-check-capture")
    args = parser.parse_args()

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ContractTests))
    if not result.wasSuccessful():
        raise SystemExit(1)

    self_check = None
    if args.self_check_capture:
        path = Path(args.self_check_capture)
        capture = json.loads(path.read_text(encoding="utf-8"))
        rows = validate_capture(capture, capture["model_class"])
        selected = sum(selected_success(row) for row in rows.values())
        no_acceptable = sum(best_acceptable_rank(row) is None for row in rows.values())
        if selected != capture["selected_success"]:
            raise ValueError("Self-check selected-success count differs")
        if no_acceptable != capture["no_acceptable"]:
            raise ValueError("Self-check no-acceptable count differs")
        self_check = {
            "capture": str(path.relative_to(ROOT)).replace("\\", "/"),
            "expressions": len(rows),
            "selected_success": selected,
            "no_acceptable": no_acceptable,
        }

    if bool(args.baseline) != bool(args.candidate):
        raise ValueError("Baseline and candidate must be supplied together")
    evaluation = None
    if args.baseline:
        baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
        candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
        evaluation = evaluate_pirs(baseline, candidate, draws=args.draws)

    report = {
        "scope": "Static pre-registered PIRS evaluator; no native terminal efficacy claim.",
        "tests_passed": result.testsRun,
        "self_check": self_check,
        "evaluation": evaluation,
        "next_action": "Run on paired terminal M95/PIRS captures after exact support, target, config, checkpoint, and native-input hashes pass; then persist the decision.",
        "sources": [
            {
                "path": str(Path(__file__).relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256(Path(__file__)),
            }
        ],
    }
    output = Path(args.output) if args.output else (
        ROOT / "pipeline/reports/pirs_preregistered_contract_20260917.json")
    output.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n",
                      encoding="ascii")
    print(json.dumps({
        "tests": result.testsRun,
        "self_check": self_check,
        "evaluation": None if evaluation is None else evaluation["decision"],
        "output": str(output),
    }))


if __name__ == "__main__":
    main()
