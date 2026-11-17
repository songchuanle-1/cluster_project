# M95 Group-Cue Parser Binding Audit

Stable ID: `m95-explicit-group-topology`. Lower TRAIN cohort SHA256
`ecf6d9fe21f254e512b4fc490bc8a843a256a0a8c9e8ae5cab79c86bbf894edc`;
upper opposing cohort SHA256
`e86746aac35cae5e3a47e6cf277bdc67fbd4dc14efb4ddc9811f68d499bbbe85`.
Native parsed scene-graph source:
`/data3/songcl/data/scanrefer/scene_graphs_new_train.json`,
SHA256 `e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08`.

For each exact scene/ann expression in both cohorts, save all graph nodes
(node_id, target, node_type, mod_text) and graph edges (object, subject,
relation, obj_idx), bound without target outcomes. Count exact `bottom`/
`lower` or `top`/`upper` words in node-0 modifier text separately from
any other node or edge. The parser's node-0 binding is a conservative
observable, not semantic truth. Report rows, unique scene-targets, and
missing graph entries; do not silently drop an expression.

If target-bound modifiers are sparse or edges describe only the target's
own subparts or other anchors, nearest-peer vertical agreement cannot
support an independently grounded local-group mechanism. Regardless of
this parser outcome, causal native true/shuffled intervention and all
remaining gates would still be required for admission.
