# Target-Blind Candidate Neighborhood Diagnostic

Stable ID `m95-explicit-group-topology`. Use frozen lower/upper
physical cohorts SHA256
`ecf6d9fe21f254e512b4fc490bc8a843a256a0a8c9e8ae5cab79c86bbf894edc`
and `e86746aac35cae5e3a47e6cf277bdc67fbd4dc14efb4ddc9811f68d499bbbe85`,
graph binding SHA256
`4cd1e5e9e3739fbaa892c91c9fd786a292a72d68b381d4898e14470fbd9c1031`,
and local-vs-global SHA256 `d29e4cd8cb85ef37681738e8cf9c4ea24ee91ef255e1e50e9a97c31e9cdb4e8d`.

For all rows whose cue is bound to node-0 modifier and which have a
same-name peer, compute a neighborhood on all physical scene instances
except the target: nearest horizontal centroid, with numeric instance
ID tie-break. Keep the exact scene-file hash guard. Compare desired
z sign of the target against that neighbor, the frozen same-name nearest
neighbor, and reverse sign; deduplicate scene-target pairs. No threshold,
GT class filtering, or target outcome enters neighborhood selection.

This is a retrospective target-bound probe only. A deployable model
would have to form neighborhoods for *every* predicted proposal, bind
the phrase to an estimated group, and demonstrate true/shuffled native
contrast and finite gradients within resources. A collapse of cue
alignment when removing GT object names shows class identity must be
learned, not that the method is impossible. Never sign receipt from
this physical oracle alone.
