# Native Main Target Token Omission

Tick3d7b538083db43b2932216472dedaa8c; unchanged deadline04:09:28+08.
Independent hypothesis: a TRAIN expression with a physical referent has an
entirely empty native main positive_map after char-to-token mapping, removing
its main mention from semantic alignment. This omission is distinct from
the simultaneous main/other-role intersection hypothesis: neither implies
the other. No wrong-root rebinding or caption rewrite is proposed.

Freeze original36665 TRAIN annotations and native seven-role mapping.
Record empty main map, root target spans, modifier/pronoun/relation support,
and graph-node counts. Do not call an empty main map zero whole-model loss:
other roles, mask loss and selector supervision may remain.
Controls: same original method, valid nonempty target span versus an empty
target-span list; all other graph fields/tokenizer fixed. Positive real cases
require first per scene, max8groups, prediction-blind original getter capture
and native semantic-loss intervention before attributing lost gradients.
Zero real cases rejects only main token omission, not parser semantic accuracy.
Full model backward/resources/independence and trained efficacy remain pending.
