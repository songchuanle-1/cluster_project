# Motivation Review - Anchor Identification
2026-09-16 05:17 Asia/Shanghai. Continuation of design0439, not a new variant.

## 1. Goal
Authoritative pipeline/goal.json unchanged: target .51, exact champion
.5024607181549072; 14constraints/11bans. No admission waiver or new annotations.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Existing attention responds to parser spans | measured |107interventions|not identity|
| Relation result responds to actual anchor node | measured |10of11edges|not correctness|
| Shared parameters guarantee target-to-anchor transfer | disproven as guarantee |static counterexample|native behavior unknown|
| Class/geometry pseudo-anchor supervision is new | not new |CoT3DRef methodology|distinct mechanism absent|

## 3. Experiment Assessment
Baseline .4894491136;M95 .5024607182;M196 stillrunning at05:07.
No new experimental accuracy. Do not convert synthetic countermodels to
native failure or target-only learning impossibility.

## 4. Gap Analysis
CoT3DRef archived original2310.06214 methodology:
parser/SBERT class matching, single candidate match, relation-based FIND,
random same-class fallback when unresolved; parallel/sequential anchor supervision.
This directly overlaps a proposed class/geometry pseudo-anchor pipeline.
NS3D2303.13483v1 sec3.4: object-category CE plus final-target CE, category
pretraining then joint training. Shared modular grounding without manual
anchor labels is therefore also not sufficient novelty.
Sources read in full for these sections, not inferred from abstracts.

## 5. Design Rationale
Static shared model p=softmax(u+r*v), target contexts r=0, anchor contexts r=1.
Two v settings have identical target probabilities and zero target-loss gradient
in v, but opposite anchor choices. Existing-target supervision alone does not
guarantee transfer across contextual roles. A labeled-anchor synthetic control
distinguishes them; this does NOT request or authorize added labels.
Counterexample limits a guarantee; it is not proof native embeddings encode r.
Do not reject all trainable transfer mechanisms based on this example.
Need a concrete computation tied to observable instance evidence and a difference
from these originals; bare CE, pseudolabel matching, or orderedmass not sufficient.

## 6. Next Batch
No admitted candidate. Continue same-forward-coverage-diagnosis toward a
distinct core mechanism; no repeated attention, relation or role-mixture audits.
Concurrent0512 audit applies to old107generic replacements; later10edge
anchor_relation_response result already targets actual relation-node IDs,
including pillow at scene0416_00/74. Missing raw signedattention means no
posthoc vector analysis, not absence of the directly measured scalar response.
Static axis check: dec.get_batches preserves contiguous SP order;
LIA source=inst_feats/query=language; neither encoder FFN nor cluster residual
reorders SPs. Query sampling does not subsample LIA support.
