"""Static PIRS admission audit. No native execution or efficacy claims."""
import ast
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
import unittest
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "Cluster/framework/model/Quard_model"
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def bce(s, target):
    return max(s, 0) + math.log1p(math.exp(-abs(s))) - target * s


def soft_iou(probabilities, target):
    inter = sum(p * t for p, t in zip(probabilities, target))
    return inter / (sum(probabilities) + sum(target) - inter)


def hard_iou(probabilities, target):
    return soft_iou([float(p > .5) for p in probabilities], target)


class Contracts(unittest.TestCase):
    def test_soft_overlap_does_not_mean_object_overlap(self):
        p = [sigmoid(-10), sigmoid(10)]
        self.assertEqual(hard_iou(p, [1, 0]), 0)
        self.assertGreater(soft_iou(p, [1, 0]), 0)

    def test_all_finite_grid_queries_get_full_weight(self):
        for a in (-20, -10, -1, 0, 1, 10, 20):
            for b in (-20, -10, -1, 0, 1, 10, 20):
                self.assertGreater(soft_iou([sigmoid(a), sigmoid(b)], [1, 0]), 0)

    def test_soft_quality_can_reverse_deployed_mask_quality(self):
        good, bad = [.51, .49], [.49, .01]
        self.assertGreater(hard_iou(good, [1, 0]), hard_iou(bad, [1, 0]))
        self.assertLess(soft_iou(good, [1, 0]), soft_iou(bad, [1, 0]))

    def test_coupled_target_can_decrease_quality(self):
        # d BCE(s,t)/dt = -s. For s<0, gradient descent decreases t.
        eps = 1e-6
        derivative = (bce(-2, .7 + eps) - bce(-2, .7 - eps)) / (2 * eps)
        self.assertAlmostEqual(derivative, 2, places=7)
        self.assertLess(bce(-2, .69), bce(-2, .7))

    def test_two_class_logit_contract(self):
        a, b, t = 3.2, -.7, .8
        normalizer = max(a, b) + math.log(math.exp(a-max(a,b)) + math.exp(b-max(a,b)))
        ce = -(1-t)*(a-normalizer) - t*(b-normalizer)
        self.assertAlmostEqual(ce, bce(b-a, t), places=12)
        self.assertNotAlmostEqual(ce, bce(b, t), places=3)

    def test_quality_objective_not_threshold_success(self):
        # Maximizing expected IoU and P(IoU>.5) need not select the same query.
        qa, qb = [.49, 1], [.51, .51]
        self.assertGreater(sum(qa)/2, sum(qb)/2)
        self.assertLess(sum(q > .5 for q in qa), sum(q > .5 for q in qb))

    def test_target_detach_is_present(self):
        code = (PACKAGE / (NAME + "_pirs") / "loss.py").read_text(encoding="utf-8")
        tree = ast.parse(code)
        fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "loss_indi")
        text = ast.unparse(fn)
        self.assertIn("pred_masks[b].sigmoid().detach()", text)
        self.assertIn("soft > 0", text)
        self.assertIn("pred_indis.log_softmax(-1)", text)


def main():
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contracts))
    if not result.wasSuccessful():
        raise SystemExit(1)
    literature = []
    sources = [
        ("gfl", "https://arxiv.org/abs/2006.04388"),
        ("mask_scoring", "https://openaccess.thecvf.com/content_CVPR_2019/html/Huang_Mask_Scoring_R-CNN_CVPR_2019_paper.html"),
    ]
    for name, url in sources:
        try:
            with urllib.request.urlopen(url, timeout=35) as response:
                content = response.read()
            path = ROOT / f"pipeline/reports/pirs_{name}_original_20260916.html"
            path.write_bytes(content)
            literature.append({"url": url, "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                               "sha256": hashlib.sha256(content).hexdigest(),
                               "scope": "Original abstract page only; full method equivalence not verified."})
        except Exception as exc:
            literature.append({"url": url, "error": str(exc)})
    paths = [Path(__file__), PACKAGE / (NAME + "_pirs") / "loss.py",
             ROOT / f"Cluster/configs/Quard/pirs/{NAME}_pirs.yaml",
             ROOT / "pipeline/designs/exp_design_20260916-1150.md",
             ROOT / "pipeline/reviews/motivation_review_20260916-1150.md"]
    report = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "scope": "Static scalar counterexamples, AST inspection and original abstract retrieval only.",
        "tests_passed": result.testsRun,
        "findings": [
            "The existing candidate is detached soft-IoU weighted two-class CE, not differentiable-target BCE as the design claims.",
            "soft>0 grants full eos weight to all 49 finite-grid queries, including a zero hard-IoU mask. Underflow can produce exceptions; this is not a native frequency measurement.",
            "Soft-IoU reverses hard-IoU ranking in a two-point counterexample; the TRAIN hard-mask oracle does not validate this target.",
            "Removing detach is not a fix: dBCE/dtarget=-logit permits reducing mask quality when the referent logit is negative.",
            "BCE must act on positive-minus-negative logits to preserve the existing two-class deployment contract.",
            "Candidate YAML uses the backbone pretrain, while the design specifies an M95 warm start; matched initialization and total updates are unspecified.",
            "GFL original abstract explicitly combines quality and class prediction with continuous labels. Mask Scoring original abstract learns mask IoU. Provenance terminology alone does not establish a whole-mechanism increment.",
            "Neither original abstract establishes exact equivalence to PIRS; novelty gate remains unverified, not a universal prior-art rejection.",
            "The positive-set oracle tests GT-restricted selection, not relabelling or learned deployment; scope B remains valid but is not evidence PIRS will work.",
        ],
        "counterexamples": {
            "zero_hard_overlap_soft_iou": soft_iou([sigmoid(-10), sigmoid(10)], [1, 0]),
            "hard_good_soft": soft_iou([.51, .49], [1, 0]),
            "hard_bad_soft": soft_iou([.49, .01], [1, 0]),
            "coupled_bce_target_derivative_at_logit_minus2": 2,
        },
        "decision": "Do not admit the current PIRS artifact. Keep referent-supervision-axis in design; preserve existing uncommitted files.",
        "next_action": "Specify hard versus soft quality, detached gradient contract, support weighting and matched initialization; verify full GFL/Mask Scoring methods and a whole-mechanism increment before amending the existing review/design. No threshold/weight sweep or renamed variant.",
        "literature": literature,
        "sources": [{"path": str(p.relative_to(ROOT)).replace("\\", "/"),
                     "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],
        "limitations": ["No native backward, resource measurement, efficacy, receipt, enqueue, sync or launch.",
                        "This audit does not resolve physical endpoint or modality support provenance in other due records."],
    }
    out = ROOT / "pipeline/reports/pirs_admission_audit_20260916.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(json.dumps({"tests_passed": result.testsRun, "report": str(out)}))


if __name__ == "__main__":
    main()
