# M95 relation-composition diagnostic

Stable ID: `m95-relation-composition-depth`. Unlike lexical relation-word
screens, this tests a frozen graph-structure property without selecting a
word or orientation after outcomes.

Use the same 256 native TRAIN expressions and scene graphs frozen for
`m95-token-span-integrity`; source/graph/capture hashes remain unchanged.
Before inspecting outcomes, construct directed paths from node 0 using
the parser's actual `graph_edge` `sub_idx`/`obj_idx` IDs (subject to object);
separately record edges
incident to target, distinct reference nodes, and whether there is a
length-two target-rooted path with distinct physical referents. Treat
missing/non-object nodes and inconsistent IDs as unresolved, not exposed.
Primary exposure: valid target-rooted two-edge path. Negative controls:
single target-edge graphs and graphs with multiple edges that do not
form a target-rooted path. Compare failure incidence among 128 ambiguous
and 128 class-unique expressions separately, report all 256 rows and
scene-balanced same-scene discordant pairs. Selected-mask failure is
the frozen IoU <=0.5; no threshold search.

An enriched, identifiable target-rooted multi-hop cohort would motivate
a matched native compositional intervention, but generic relation fusion,
selector and two-anchor mechanisms are already closed. If the graph lacks
valid paths or errors do not distinguish path structure from controls,
reject this realization. No admission without distinct causal information
path, mechanism control, native backward, resources, independent package,
goal constraints and original-literature comparison.
