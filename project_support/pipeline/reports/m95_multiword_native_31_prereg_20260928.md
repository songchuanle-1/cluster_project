# M95 native outcome capture for the frozen 31-expression cohort

Use `m95_multiword_capture_manifest_v1` SHA256
`85e108e8c86d65bcdbdc25061987e0a973fa45b35b00030d0721d359da720040`
without replacing the historical 256-row identity manifest. Capture original
TRAIN scene inputs for the two manifest scenes with native dataset transforms,
M95 checkpoint SHA256
`fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e`,
seed 1999, native model loss and unchanged labels. Before forward, require
all 31 scene/annotation IDs, target IDs and normalized utterances to match
the frozen manifest. Retain only the 31 specified expression outcomes.

For each expression record selected-query mask IoU to native superpoint GT,
selected query, physical seed superpoint and whether the native sampled seed
is in the physical target instance. Compare phrase-present and phrase-absent
descriptions only as text-confounded diagnostics; aggregate by scene and
scene-target, not as 31 independent physical samples. No post-hoc selection,
source patch or claim of training efficacy. A later same-forward fixed-text
context-support intervention requires a separate preregistered control.

Run only on authorized server-6 GPU7 after checking live GPU idleness and
acquiring the project's exclusive native-diagnostic lease. Output must be
fresh and project-local; zero outcome is not inferred from this plan.
