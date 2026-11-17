"""Record this tick's frozen TRAIN data-contract screens in the durable ledger."""
import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "pipeline/research_work.json"
STAMP = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
ROUTES = (
    (
        "m95-target-label-alignment",
        "65/256 literal category/lemma mismatches, including 17 failed ambiguous rows; "
        "exact descriptions mostly contain compounds, aliases or annotation granularity. "
        "One apparent wrong parser target; zero same-scene exposure-discordant pairs. "
        "Literal mismatch cannot identify a physical referent conflict.",
        "Do not rename lexical category mismatch as referent binding or supervision repair. "
        "Revisit this ID only with independent physical-identity evidence and matched native control.",
        ("m95_target_label_alignment_prereg_20260926-2224.md",
         "m95_target_label_alignment_context_20260926-2228.json"),
        "20260926-223350_route_change.md",
    ),
    (
        "m95-utterance-provenance",
        "243/256 original/graph utterances differ only in punctuation; 13 word-token "
        "changes are contraction expansions, including two failures. No task-bearing "
        "target word was lost and no same-scene discordant exposure pair exists.",
        "Do not build graph-text repair or retokenization variant from normalization "
        "differences; native token spans were independently verified reachable.",
        ("m95_utterance_provenance_prereg_20260926-2234.md",
         "m95_utterance_provenance_20260926-2234.json"),
        "20260926-223359_route_change.md",
    ),
    (
        "m95-description-label-collision",
        "96 normalized distinct-target description collisions in full TRAIN source; "
        "only two exposed in the frozen 256-row cohort and both are successful. "
        "Zero same-scene exposure-discordant pairs.",
        "Do not relabel as same-target description consistency or positive-set repair. "
        "Only reconsider under the same ID if independent failure-linked contradictory "
        "labels and a matched causal control are obtained.",
        ("m95_description_collision_prereg_20260926-2240.md",
         "m95_description_collision_20260926-2240.json"),
        "20260926-223408_route_change.md",
    ),
    (
        "m95-target-span-lemma-contract",
        "All 256 frozen target-node head tokens occur in their valid target spans; "
        "zero primary missing-head exposures, including all 56 failures. "
        "Exact multiword lemma containment is 174/256, not a physical-ID test.",
        "Do not build span repair, retokenization or lexical-target variant from "
        "this negative contract screen.",
        ("m95_target_span_lemma_prereg_20260926-2237.md",
         "m95_target_span_lemma_20260926-2237.json"),
        "20260926-223620_route_change.md",
    ),
    (
        "m95-sample-context-support",
        "Exact target-class cue absent in 8/80 eligible frozen expressions, only "
        "one failure. Other-only graph-bound class keys: 25/58 ambiguous failures "
        "versus 26/70 controls, with mixed predeclared graph-node/length cells. "
        "Target-instance overwrite makes literal cues insufficient to infer "
        "actual final seed-supervision error.",
        "Do not rename this as lexical sample-loss correction, class-key expansion, "
        "or semantic supervision gate. Reconsider only with independent final "
        "native seed-label conflict and matched loss-path control.",
        ("m95_sample_context_support_prereg_20260926-2241.md",
         "m95_sample_context_support_20260926-2241.json",
         "m95_sample_context_role_control_prereg_20260926-2243.md",
         "m95_sample_context_role_control_20260926-2243.json"),
        "20260926-224335_route_change.md",
    ),
    (
        "m95-object-category-conflict",
        "Zero of 256 frozen targets have conflicting normalized object names "
        "across same-instance TRAIN annotations, despite 255 targets having "
        "multiple annotations. No exposed failure or label contradiction.",
        "Do not rename as multi-description label consistency or target-category "
        "supervision repair. Reconsider only with independent contradictory "
        "physical-instance labels and a matched native causal control.",
        ("m95_object_category_conflict_prereg_20260926-2248.md",
         "m95_object_category_conflict_20260926-2248.json"),
        "20260926-225025_route_change.md",
    ),
    (
        "m95-cross-role-token-overlap",
        "Actual native tokenizer positions show zero of 256 frozen target-noun "
        "versus other-object noun overlaps, though 240 rows have other-object "
        "tokens. Zero target-modifier/pronoun overlap; one relation-token "
        "overlap. No primary contradictory semantic-supervision support.",
        "Do not relabel as referent-role competition, semantic-map correction "
        "or lexical loss repair. Reconsider only with independent native "
        "same-token positive/negative conflict and matched loss-path control.",
        ("m95_cross_role_token_overlap_prereg_20260926-2253.md",
         "m95_cross_role_token_overlap_20260926-2253.json"),
        "20260926-225220_route_change.md",
    ),
)


def evidence(path):
    full = ROOT / path
    return {"path": path.as_posix(), "sha256": hashlib.sha256(full.read_bytes()).hexdigest()}


def main():
    doc = json.loads(LEDGER.read_text(encoding="utf-8"))
    existing = {candidate["id"] for candidate in doc["candidates"]}
    added = []
    for route_id, result, next_action, artifacts, decision in ROUTES:
        if route_id in existing:
            continue
        receipts = [evidence(Path("pipeline/reports") / name) for name in artifacts]
        receipts.append(evidence(Path("pipeline/decisions") / decision))
        doc["candidates"].append({
            "id": route_id, "stage": "rejected",
            "latest_progress": STAMP + ": " + result + " No admission or training.",
            "next_action": next_action,
            "evidence": receipts,
        })
        added.extend(receipts)
    doc["updated_at"] = STAMP
    doc["next_action"] = (
        "Continue independent, prediction-blind task mechanism diagnosis on "
        "server-6 GPU7 only. Seven frozen data-contract routes were rejected. "
        "Do not reopen completed numerical provenance, old selector/ranking/fusion, "
        "or lexical routes by renaming; require all six gates before admission. "
        "Strict historical full-scan comparison remains failed 26/65."
    )
    doc["design_cycle"] = {
        "timestamp": STAMP,
        "stop_reason": "tick_deadline_near",
        "deferred_reason": (
            "Seven distinct frozen TRAIN data-contract diagnostics completed and "
            "rejected; no candidate admitted. This disposition is provisional "
            "until the scheduler deadline is within 180 seconds; continue "
            "substantive research while time remains."
        ),
        "attempted_ids": [entry[0] for entry in ROUTES],
        "evidence": added,
        "resume_condition": (
            "At the next design interval, locate a genuinely distinct "
            "prediction-blind task information deficit and pre-register an "
            "outcome-independent matched native control on server-6 GPU7. "
            "Do not enqueue without diagnosis, controls, native backward, "
            "resources, independent package/config and goal constraints."
        ),
        "blocker": (
            "No defensible training mechanism emerged from the seven completed "
            "data-contract tests; capacity remains open, not externally blocked."
        ),
    }
    LEDGER.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("persisted", len(added), "evidence receipts", "SHA256",
          hashlib.sha256(LEDGER.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
