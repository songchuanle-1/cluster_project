# Native Role-Gradient Audit
2026-09-16 00:30;diagnostic only,not admitted variant.

## Evidence
Fixed16 augmented TRAIN batches,123expressions32scenes,M95eval checkpoint.
Existing parser has same main lemma in other-object nodes for20expressions16scenes:
10recoverable,9success,1mask-limited. This is lexical incidence,not coreference.
All six native semantic loss calls per batch audited;firstcall is final layer.
Original loss AST reused with independently exposed similarity logits;
scalar equality checked against native function on every call.

## Result
Final layer20expressions205matched query-token positions:
205positive gradients,0negative. Gradient descent on independent logits lowers
similarity to these repeated-head words. Source other-entity term doubles
their logits in the query-to-token partition function.
Summed originalgradient.0023176615000011225;
same-forward removal of other tag .000022457786478469188.
Gradient remains positive;not a full parameter-space optimizer result.
For scene0220ann21,9query-token positions:
originalsum.00032670790096744895,withoutother.000002946988388430327.

## Interpretation
The curtain case includes apparent target remention as an other entity,so the
preceding deletion was NOT a pure anchor-removal intervention.
Other fixed examples explicitly refer to another trash can,gray table,another
pillow,and different pictures. Do not classify all20 as annotation errors.
Lexical matching cannot safely turn these words into target-positive labels.
No new annotation,training,schedule change or production loss modification.
No core-novelty claim for masking,role cleanup,partial labels or marginalization.
Original-source retrieval this turn gave no usable literature evidence.

## Next Gate
Derive a mechanism that represents unresolved role identity without falsely
merging distinct objects;compare original prior art and closed project routes.
Use explicit distinct-object negative controls and native full-loss parameter
interventions before resource/independence/admission checks.
The user's requested new qualified variant actually training remains incomplete.

## Provenance
role_gradient_20260916.json SHA256
307e1723452344437dd9e8ac464f8e15b4a3f8a572915cf99fdc49f6c96fe4b3.
anchor_identity_20260916.json SHA256
4218cafcf571fba43e8265c098d96ab1c898cecd04862daae6552ae5e3525ed7.
role_graphs_20260916.json SHA256
a99e0c90b5d969d516ba475c9c0dab3649c90c81ab95f26a371662e6c20ea06b.
