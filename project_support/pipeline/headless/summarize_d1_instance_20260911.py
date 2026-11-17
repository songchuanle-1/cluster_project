"""Independent arithmetic checks, scene uncertainty, and frozen casebook."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import numpy as np
from d1_candidate_bank_20260911 import key, sha
from close_tick_20260911_0707 import table

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
OUT = P / "reports/d1_instance_20260911-0810"
audit = json.loads((OUT / "instance_audit.json").read_text(encoding="utf-8"))
protocol = json.loads((OUT / "protocol.json").read_text(encoding="utf-8"))
assert audit["status"] == "complete" and not audit["cuda_initialized"]
expected = set(map(tuple, protocol["expected_ids"]))
by_model = {name: {key(r): r for r in audit["rows"] if r["model"] == name}
            for name in ("baseline", "m95")}
assert all(set(rows) == expected and len(rows) == 284 for rows in by_model.values())
for name, rows in by_model.items():
    old_path = P / f"reports/d1_expansion_20260911-0715/{name}/summary.json"
    assert sha(old_path) == audit["upstream_summary_hashes"][name]
    old = {key(r): r for r in json.loads(old_path.read_text(encoding="utf-8"))["rows"]}
    for identity, r in rows.items():
        assert r["bank_sha256"] == old[identity]["artifact_sha256"]
        for which in ("selected", "oracle"):
            s = r[which]
            tp, fp, fn = s["tp"], s["fp"], s["fn"]
            assert all(v >= 0 for v in (tp, fp, fn))
            assert tp + fn == s["target_points"] and tp + fp == s["pred_points"]
            assert abs(tp / (tp + fp + fn + 1e-6) - old[identity][which + "_iou"]) < 1e-7
            assert s["recall"] == tp / (tp + fn)
            assert s["precision"] == (tp / (tp + fp) if tp + fp else None)
            if s["pred_points"] == 0:
                label = "empty_prediction"
            elif s["iou"] > .5:
                label = "target_pass50"
            elif s["best_instance_iou"] > .5 and s["best_instance"] != int(r["object_id"]):
                a, b = s["target_semantic"], s["best_instance_semantic"]
                label = ("wrong_instance_semantic_unknown" if a is None or b is None else
                         "wrong_instance_same_semantic" if a == b else "wrong_instance_different_semantic")
            else:
                label = "no_instance_pass50"
            assert label == s["label"]
        assert r["relation_failure_label"] == "unknown_not_grounded"
        assert r["boundary_cause_label"] == "unknown_geometry_not_adjudicated"
    assert Counter(r["selected"]["label"] for r in rows.values()) == audit["aggregate"][name]["selected_labels"]
for k in expected:
    a, b = [by_model[n][k] for n in by_model]
    assert a["description"] == b["description"] and a["parser_graph"] == b["parser_graph"]
    assert a["selected"]["target_points"] == b["selected"]["target_points"]
    assert a["selected"]["target_semantic"] == b["selected"]["target_semantic"]

labels = sorted({r["selected"]["label"] for r in audit["rows"]})
scene_ids = sorted({r["scene_id"].split("_")[0] for r in audit["rows"]})
assert len(scene_ids) == 71
matrix = {n: np.zeros((71, len(labels))) for n in by_model}
for name, rows in by_model.items():
    for i, scene in enumerate(scene_ids):
        members = [r for r in rows.values() if r["scene_id"].split("_")[0] == scene]
        assert len(members) == 4
        for j, label in enumerate(labels):
            matrix[name][i, j] = sum(r["selected"]["label"] == label for r in members) / 4
delta = matrix["m95"] - matrix["baseline"]
indices = np.random.default_rng(1999).integers(71, size=(10000, 71))
samples = delta[indices].mean(axis=1)
intervals = {label: dict(mean=float(delta[:, j].mean()),
                         low=float(np.quantile(samples[:, j], .025)),
                         high=float(np.quantile(samples[:, j], .975)))
             for j, label in enumerate(labels)}
extra = {}
for name, rows in by_model.items():
    rs = list(rows.values())
    extra[name] = dict(
        same_semantic_other_class=sum(r["selected"]["label"] == "wrong_instance_same_semantic"
                                     and r["selected"]["target_semantic"] == 19 for r in rs),
        no_instance_target_best=sum(r["selected"]["label"] == "no_instance_pass50"
                                   and r["selected"]["best_instance"] == int(r["object_id"]) for r in rs),
        unknown_target_semantics=sum(r["selected"]["target_semantic"] is None for r in rs),
        parser_edge_present=sum(r["parser_has_relation_edge"] is True for r in rs))
casebook = [
    "# Fixed Instance-Diagnostic Casebook",
    "Protocol frozen before instance attribution; 12 hash-selected M95 recoverable errors.",
    "Nine unique same-scene successful controls; three missing, no replacement.",
    "Cases were selected on known M95 outcome, not an unbiased subset or causal matched study.",
    "Descriptions and parser text are source records, not verified scene relations.",
    "Semantic IDs are coarse; ID19 maps to NYU40 ID39 in the local dataset code, not an exact noun match.",
    "All boundary/relationship-cause labels remain unknown. No visual adjudication claimed.",
]
case_ids = []
for i, pair in enumerate(protocol["pairs"], 1):
    error_id = tuple(pair["error"])
    assert by_model["m95"][error_id]["selected_iou"] <= .5 < by_model["m95"][error_id]["oracle_iou"]
    case_ids.append(error_id)
    casebook += [f"\n## Case {i}: {'/'.join(error_id)}"]
    for role in ("error", "control"):
        if pair[role] is None:
            casebook += [f"\nControl missing: {pair['missing_reason']}."]
            continue
        identity = tuple(pair[role])
        if role == "control":
            assert by_model["m95"][identity]["selected_iou"] > .5
        r = by_model["m95"][identity]
        casebook += [f"\n### {role.title()}: {'/'.join(identity)}",
                     f"Source target name: {r['object_name']}.",
                     f"Source description: {r['description']}",
                     f"Parser utterance: {r['parser_graph']['utterance']}",
                     "Parsed predicates: " + json.dumps([e.get("relation") for e in r["parser_graph"].get("graph_edge", [])]),
                     table(["Model", "Selected IoU", "Oracle IoU", "Overlap label", "Best instance",
                            "Target/winner semantic", "Precision", "Recall", "FP", "FN"],
                           [(n, f"{by_model[n][identity]['selected_iou']:.6f}",
                             f"{by_model[n][identity]['oracle_iou']:.6f}",
                             by_model[n][identity]["selected"]["label"],
                             by_model[n][identity]["selected"]["best_instance"],
                             str(by_model[n][identity]["selected"]["target_semantic"]) + "/" +
                             str(by_model[n][identity]["selected"]["best_instance_semantic"]),
                             by_model[n][identity]["selected"]["precision"],
                             by_model[n][identity]["selected"]["recall"],
                             by_model[n][identity]["selected"]["fp"], by_model[n][identity]["selected"]["fn"])
                            for n in by_model]),
                     "Review status: overlap fields verified; physical boundary and language-cause attribution unknown."]
assert len(case_ids) == len(set(case_ids)) == 12
(OUT / "casebook.md").write_text("\n\n".join(casebook) + "\n", encoding="utf-8")
label_table = table(["Selected label", "Baseline /284", "M95 /284"],
                    [(label, audit["aggregate"]["baseline"]["selected_labels"].get(label, 0),
                      audit["aggregate"]["m95"]["selected_labels"].get(label, 0)) for label in labels])
recoverable = table(["Selected label among recoverable", "Baseline /90", "M95 /111"],
                    [(label, audit["aggregate"]["baseline"]["recoverable_labels"].get(label, 0),
                      audit["aggregate"]["m95"]["recoverable_labels"].get(label, 0)) for label in labels
                     if label != "target_pass50"])
ci_table = table(["Paired label prevalence delta M95-baseline", "Mean", "95% low", "95% high"],
                [(k, f"{v['mean']:.6f}", f"{v['low']:.6f}", f"{v['high']:.6f}") for k, v in intervals.items()])
report = f"""# D1 Instance-Overlap Audit

## Protocol And Denominators
All284 fixed descriptions on71physicalscenes, two models,568bank records.
Original banks/pointfiles/source/graphs verified bySHA, rawpoint instanceGT exact,
np.unique superpoint reindexing exact to eachsavedbank. No missing joins.
Only selected and oracle masks expanded onCPU; no newinference, GPU use,
reservedscene analysis, externalannotation or training. Protocol.json contains
prespecified labelrules and12error9control case selection, threecontrols missing.
8synthetic attributiontests pass locally andremote; all568localarithmetic checks pass.

## Measured Labels
{label_table}

{recoverable}

Labels partition selectedoutputs, not causes. Same_semantic means homogeneous
nonnegative coarse semantic ID equality, not identical fine category.
Targetsemantic unavailable for71/284 inbothmodels; retain unknown.
Same-semantic wronginstance counts include coarse semantic ID19 (NYU40 ID39):
baseline{extra['baseline']['same_semantic_other_class']},M95{extra['m95']['same_semantic_other_class']}.
No-instance-pass masks whose best-overlap instance is stilltarget:
baseline{extra['baseline']['no_instance_target_best']},M95{extra['m95']['no_instance_target_best']}.
Do not call all these masks wrongobject, absentproposal or boundaryfailure.

## Formula And Identification Limits
TP=|P intersect G|,FP=|P minus G|,FN=|G minus P|.
IoU=TP/(TP+FP+FN+1e-6), precision=TP/(TP+FP) (empty=>null),
recall=TP/(TP+FN). Both FP/|G| and FN/|G| are stored.
These derive overlap accounting only, not a newmodel contribution.
Best labelledinstance uses pointIoU; >.5 determines overlapmatch; emptyseparate.
Unknown semantic labels and unlabelledpredictedpoints are explicit, not majority-imputed.
All568relationcause and boundarycause fields unknown. Textgraph edges are parser
outputs, not objectgroundings or geometric truth; no annotatoragreement claim.

## Scene Uncertainty
{ci_table}

10000 pairedphysicalscene bootstrap draws,seed1999,percentile95.
Exploratory conditional intervals, no multiplicity-adjusted test or untouchedtest
claim. Equal-scene sample, historicallyminedvalidation, not datasetprevalence.

## Fixed Case Interpretation
See casebook.md for12hash-selectederrors/9same-scene successcontrols.
scene0046_00 target26 ann27 fails, target26 ann34 succeeds withinbothmodels;
same target/scene but differenttext, not a controlled paraphrase experiment.
scene0146_00 target16 ann8 has target asbestinstance butIoU<=.5,
so its label is no_instance_pass50, not demonstrated different-object selection.
Other examples contain relations, but co-occurrence doesnot establish causality.
Cases selected by M95 outcome, no bias-free causal effect inference.

## Conclusion And Next Work
Wrong-instance overlap is observed in many recoverableerrors. However bothmodels
have63recoverable same-semantic substitutions: M95's extra21recoverableerrors
are not an increase in that count (unknownsemantic+12,no-instance-pass+9).
Do not claim more same-class confusion from thiscomparison.
Next: audit exactobjectidentities and geometric/text evidence on frozen cases,
especially unknownsemantic and coarse ID19, with explicit labeling rules
and missingness. Boundary/relationshipmechanisms remain unproven.
N1 primarypaper comparison, singlecoremechanism derivation/gradients/degeneracies/
complexity and matchedfalsificationcontrols are prerequisites, not completedwork.
No newtrainingadmission, selectorfamily/refill, or championledgerchange.

## Resources And Provenance
Workerelapsed{audit['elapsed_seconds']:.3f}s,peakRSS{audit['peak_rss_mib']:.3f}MiB,
CUDAinitialized=false,threads1; CPUonly, not a fullmodel efficiencybenchmark.
WorkerSHA{audit['worker_sha256']}; auditSHA{sha(OUT / 'instance_audit.json')}.
Hashsynced standalonehelpers tobothservers; no trainingpackage/deploymentmutation.
Sourcecode get_ref_mask/transform_test supplies local implementation semantics.
No novelty or external-paper facts asserted by this diagnostic.
"""
(OUT / "diagnostic_report.md").write_text(report, encoding="utf-8")
result = dict(status="passed", rows_checked=568, physical_scenes=71,
              protocol_sha256=sha(OUT / "protocol.json"), audit_sha256=sha(OUT / "instance_audit.json"),
              casebook_sha256=sha(OUT / "casebook.md"), case_count=12, control_count=9, missing_controls=3,
              label_delta_scene_bootstrap95=intervals, additional_counts=extra)
(OUT / "verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(label_table)
print(recoverable)
print(json.dumps(extra, indent=2))
