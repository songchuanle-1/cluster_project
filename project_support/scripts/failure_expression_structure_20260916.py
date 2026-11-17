"""What expression structure is available in the recoverable selection failures?

Joins the fixed-forward coverage outcome per expression with the audited entity /
relation annotations, to test whether relation or attribute evidence even exists
for the cases a candidate mechanism would have to fix. Local analysis only.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path("D:/project/cluster_project")
COVERAGE = ROOT / "pipeline/reports/coverage_stage_20260916.json"
BINDING = ROOT / "pipeline/reports/entity_binding_20260916.json"
PURITY = ROOT / "pipeline/reports/cluster_instance_purity_20260916.json"
OUT = ROOT / "pipeline/reports/failure_expression_structure_20260916.json"

RELATION_STOP = {"is", "of", "with", "in", "on", "at", "the", "a", "an", "it",
                 "that", "this", "and", "to", "by", "from", "for", "its"}


def main():
    coverage = json.loads(COVERAGE.read_text())["rows"]
    binding = {(r["scene"], r["ann_id"]): r
               for r in json.loads(BINDING.read_text())["rows"]}
    purity = {(r["scene"], r["expression_slot"]): r
              for r in json.loads(PURITY.read_text())["rows"]}

    rows = []
    for c in coverage:
        last = c["layers"][-1]
        if last["selected"] > .5:
            outcome = "success"
        elif last["best"] > .5:
            outcome = "recoverable"
        else:
            outcome = "mask_limited"
        b = binding.get((c["scene"], c["ann_id"]))
        if b is None:
            continue
        edges = b.get("edges", [])
        entities = b.get("entities", [])
        non_target = b.get("non_target_entities", [])
        nt_attr = b.get("non_target_with_attributes", [])
        nouns = []
        for e in entities:
            spans = e.get("spans", {})
            txt = spans.get("target_char_span") or []
            for s in txt:
                if s.get("valid") and s.get("text"):
                    nouns.append(s["text"].lower())
        content_edges = [e for e in edges
                         if e.get("relation", "").strip().lower() not in RELATION_STOP]
        rows.append(dict(
            scene=c["scene"], ann_id=c["ann_id"], outcome=outcome,
            caption=b["caption"], n_edges=len(edges),
            n_content_edges=len(content_edges),
            content_relations=[e["relation"] for e in content_edges],
            n_entities=len(entities),
            non_target_entities=non_target,
            non_target_with_attributes=nt_attr,
            n_unique_nouns=len(set(nouns)),
            has_relation=bool(content_edges),
            has_other_entity=bool(non_target),
            has_attribute_contrast=bool(nt_attr),
            best_iou=last["best"], selected_iou=last["selected"]))

    groups = {}
    for outcome in ("success", "recoverable", "mask_limited"):
        group = [r for r in rows if r["outcome"] == outcome]
        n = len(group)
        groups[outcome] = dict(
            n=n,
            with_content_relation=sum(r["has_relation"] for r in group),
            with_other_entity=sum(r["has_other_entity"] for r in group),
            with_other_entity_attributes=sum(r["has_attribute_contrast"] for r in group),
            with_any_signal=sum(r["has_relation"] or r["has_other_entity"]
                                or r["has_attribute_contrast"] for r in group),
            with_no_signal=sum(not (r["has_relation"] or r["has_other_entity"]
                                    or r["has_attribute_contrast"]) for r in group),
            mean_content_edges=(sum(r["n_content_edges"] for r in group) / n
                                if n else None),
            unique_nouns=dict(Counter(r["n_unique_nouns"] for r in group)))

    # same-name distractor presence among the recoverable failures
    rec = [r for r in rows if r["outcome"] == "recoverable"]
    same_name = 0
    for r in rec:
        p = purity.get((r["scene"], r["ann_id"]))
        if p is None:
            continue
        if p.get("winner_is_wrong"):
            same_name += 1

    result = dict(
        groups=groups,
        recoverable_with_wrong_instance=same_name,
        rows=rows,
        scope="Local join of the fixed-forward coverage outcome with the audited "
              "entity/relation annotations. 'Content relation' excludes copular and "
              "purely syntactic relations. 'Other entity' means an annotated non-target "
              "entity exists in the expression. This measures whether the evidence a "
              "candidate mechanism would exploit is even present, not whether the "
              "current model uses it. No model or admission claim.",
        sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (COVERAGE, BINDING, PURITY, Path(__file__))})
    OUT.write_text(json.dumps(result, indent=2))
    print(json.dumps(groups, indent=2))
    print("recoverable with identified wrong instance:", same_name, "of", len(rec))
    print("\nrecoverable with no usable signal:")
    for r in rec:
        if not (r["has_relation"] or r["has_other_entity"]
                or r["has_attribute_contrast"]):
            print(" ", r["scene"], r["ann_id"], "|", r["caption"][:110])


if __name__ == "__main__":
    main()
