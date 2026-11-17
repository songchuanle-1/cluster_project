# Role Hypothesis Admission Audit
2026-09-16 00:50 Asia/Shanghai.

## Candidate Dispositions
Independent unknown binary role:
L=-log(sigmoid(z)+sigmoid(-z))=0,zero gradient. Rejected.

Shared binary role:
L=-log(prod sigmoid(z_i)+prod sigmoid(-z_i)).
Invariant under z->-z;encourages agreement without selecting correct referent.
Same-lemma distinct-object counterexample defeats unrestricted anchoring. Rejected.

Binary graph coloring:
Different instance IDs do not imply different target-membership bits.
Two distinct anchors can both be non-target. Rejected.
21same-lemma othernodes in20expressions:13disconnected,8reachable,6direct.
Graph connectivity alone cannot recover missing coreference.

## Original Sources
EDA arXiv2209.14941,section3.3.2 explicitly weights auxiliary negative
similarity by2;section5 and AppendixC acknowledge parsing errors.
Archived original HTML:eda_original_20260916.html.
Cour, Sapp, Taskar, Learning from Partial Labels, JMLR2011:
partial_label_cour2011.pdf. Candidate-label ambiguity and disambiguation are
established research;no novelty claim for basic marginalization.
These sources do not establish that every proposed application is duplicated;
application-level novelty remains a substantive unresolved gate.

## Corrected Instance Evidence
Same-forward fixedTRAIN123 expressions:38failures,31confident wronginstances.
29/31wronginstances have target's annotation name;all31names available.
9 exact auxiliary-name matches are lexical only,not grounded anchor truth.
scene0220ann21 wronginstance4 is curtain,GT42 is another curtain.
The prior anchor-deletion rescue therefore does NOT demonstrate window confusion.
Its deletion also included target remention curtains.

## Next Requirement
An admissible proposal must explain instance-specific evidence,with explicit
relation/viewpoint/anchor uncertainty and controls against genuine other objects.
Do not repeat tag-removal steps,scale weights,or rename closed ranking/CPS families.
No model/config/receipt/commit/sync/queue entry created in this continuation.
Goal:newqualifiedvariant actuallytraining remains unachieved.
