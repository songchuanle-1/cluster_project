"""Static admission counterexamples; no native training or efficacy claims."""
import ast
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"


def method(path, name):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    nodes = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(nodes) == 1, name
    return ast.unparse(nodes[0])


def main():
    loss, dec = MODEL / "loss.py", MODEL / "dec.py"
    matcher = method(loss, "match_sampled_ins")
    masks = method(loss, "loss_masks")
    indi = method(loss, "loss_indi")
    layer = method(loss, "get_layer_loss")
    head = method(dec, "prediction_head")
    decoder = dec.read_text(encoding="utf-8")
    checks = {
        "seed_match_has_no_mask_argument": "pred_mask" not in matcher,
        "indi_positive_set_is_indices": "target_sim[src_idx] = pos_mask" in indi,
        "mask_and_indi_share_indices": (
            "self.loss_indi(pred_indis, target, indices, num_insts)" in layer
            and "self.loss_masks(pred_masks, pred_scores, target, indices, num_insts)" in layer),
        "score_regresses_matched_iou_only": (
            "score[idx_q]" in masks and "tgt_score > 0.5" in masks
            and "F.mse_loss(pred_score, tgt_score)" in masks),
        "mask_depends_on_same_query": (
            "self.out_norm(query)" in head and "torch.einsum" in head),
        "query_receives_scene_and_language": (
            "self.qia(inst_feats, query, batch_mask)" in decoder
            and "self.qla(lang_feats, query_qia, lang_masks)" in decoder),
    }
    assert all(checks.values()), checks

    # A threshold label and an IoU regression agree in rank only on the shared
    # supervised support. Off-support scores are unconstrained by that regression.
    cases = []
    for seed_positive, iou in itertools.product((False, True), (0.0, 0.25, 0.75, 1.0)):
        cases.append(dict(seed_positive=seed_positive, target_iou=iou,
                          existing_score_supervised=seed_positive and iou > 0.5,
                          proposed_positive=iou > 0.5))
    support_mismatch = sum(not x["existing_score_supervised"] and x["proposed_positive"]
                           for x in cases)
    assert support_mismatch == 2
    # Raw query can encode a mask direction even without a mask-pooling input.
    scene = ((1, 0), (0, 1))
    queries = ((1, -1), (-1, 1))
    decoded = [[sum(a * b for a, b in zip(q, f)) > 0 for f in scene] for q in queries]
    assert decoded == [[True, False], [False, True]]

    ownership_path = ROOT / "pipeline/reports/ownership_path_contract_20260916.json"
    ownership = json.loads(ownership_path.read_text(encoding="utf-8"))
    connected = [r for r in ownership["rows"] if r["distance_to_target"] is not None]
    assert len(connected) == 7
    provenance = []
    for row in connected:
        provenance.append({
            "scene": row["scene"], "ann_id": row["ann_id"], "node_id": row["node_id"],
            "distance_to_target": row["distance_to_target"],
            "available_axis": ["scene", "ann_id", "node_id"],
            "missing_from_this_archive": [
                "native_batch_occurrence", "sample_inverse", "original_superpoint_ids",
                "paired_2d_3d_row_vectors", "cache_producer_identity"],
        })
    # Endpoint ownership can change the ranking without a new information source.
    # This tests a reference factor model, not the network or novelty.
    factor = [[3, 1], [0, 2]]
    unary = [1, 2]
    owned = [sum(factor[i][j] * unary[j] for j in range(2)) for i in range(2)]
    relocated = [sum(factor[j][i] * unary[j] for j in range(2)) for i in range(2)]
    disabled = [sum(unary)] * 2
    assert owned == [5, 4] and relocated == [3, 5] and disabled == [3, 3]
    paths = [Path(__file__), loss, dec, ownership_path,
             ROOT / "pipeline/reports/modality_index_contract_20260916.json"]
    report = {
        "scope": "Static source checks and finite counterexamples only; no native data execution.",
        "source_checks": checks, "label_support_cases": cases,
        "positive_support_mismatches": support_mismatch,
        "query_extent_counterexample": decoded,
        "connected_case_provenance": provenance,
        "ownership_control_counterexample": {
            "owned": owned, "endpoint_relocated": relocated, "predicate_disabled": disabled},
        "conclusions": [
            "Absence of explicit mask pooling does not establish absence of extent information.",
            "Seed matching is verified, but supervision as the root cause is not identified.",
            "Mask-label supervision overlaps score quality learning, but is not identical: support differs.",
            "Changing referent positives changes the referent assignment even if the mask matcher is untouched.",
            "23 unsuccessful fixed readouts cannot prove representation-wide absence of information.",
            "A relation mentioned in text need not identify a unique physically observable referent.",
            "Seven connected text cases lack physical axes in the inspected ownership archive.",
            "Endpoint-sensitive factor inference is a control, not a newly established contribution.",
        ],
        "limitations": [
            "No neural learning, native imitation test, FLOPs, latency, memory or generalization measurement.",
            "No claim that missing fields in this archive are absent from native data.",
            "No new prior-art conclusion; literature search returned no usable result this tick.",
        ],
        "sources": {str(p.relative_to(ROOT)).replace("\\", "/"):
                    hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    }
    out = ROOT / "pipeline/reports/referent_supervision_contract_20260916.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checks": len(checks), "label_cases": len(cases),
                      "connected_cases": len(provenance), "result": "PASS"}))


if __name__ == "__main__":
    main()
