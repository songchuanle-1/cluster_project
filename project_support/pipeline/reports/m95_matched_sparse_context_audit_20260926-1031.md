# M95 Matched Sparse Context Audit

2026-09-26 10:31 Asia/Shanghai. Candidate: `m95-repro-drift-boundary`.
On authorized server-6 GPU7, a frozen row83 batch was run twice cold and
twice after one frozen row174 forward, resetting seed 1999 before each
forward. The diagnostic made no optimizer step and did not edit model code.
The checkpoint, model package, row83 and row174 batches, and completed
full-order row83 result were hash-checked before execution.

All four row83 runs agreed byte-for-byte at sparse input-conv input
(`909040b7`), first sparse output (`808e1af8`), and output-layer result
(`b1e0f9fb`); their corresponding sparse indices were also identical.
Each comparison against the first cold run had zero changed elements and
zero maximum absolute difference at these measured feature stages. All
four selected query 2 with IoU 0. The output-layer hash did not equal
the recovered original-order result (`ef0b1b70`), nor the earlier
fixed-batch repeat's sparse hash (`e466a41e`); this cross-process
difference is not explained by a single row174 warm-up and cannot be
attributed to any one sparse operator. The historical reference has
no comparable upstream stage hashes.

This is a bounded negative context control. It does not reproduce the
original 3137-step model/RNG context, and a hash difference alone
does not indicate task benefit. The unchanged strict comparator fails
26/65 paired rows. No structural candidate passed diagnosis or matched
behavioral controls; native backward, resource and independent-variant
gates therefore remain untested. Admission is false; queue stays empty.

Next bounded evidence: when a full authorized GPU7 window is available,
collect matching input-conv input, coordinates and first sparse stage
features in one original-order row83/step3137 run, and compare them
numerically against a frozen-batch run from the same process with
explicit ordering/context receipts. Stop at the first measured
divergence. Do not retune tolerances or infer the original reference's
unobserved upstream state.

Receipt: `pipeline/reports/m95_matched_sparse_context_20260926-1029.json`,
SHA256 `5cae28f15d9104a07f49e3f42e42adb83df3c158f780f8ad55a23b64358665d5`.
Script: `scripts/m95_matched_sparse_context_20260926.py`, SHA256
`81650bac24ea34655c585b8c4f2bc7fc80f36ff989ff2dd686e5a5df272d6ed5`.
Two local comparator tests passed.
