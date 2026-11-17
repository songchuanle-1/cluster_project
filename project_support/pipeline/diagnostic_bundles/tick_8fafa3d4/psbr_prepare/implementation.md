# M209-PSBR implementation (static preparation only)

Status: **PREPARED_STATIC_ONLY_UNEXECUTED**. Stable ID:
`hierarchy-parent-segmented-bidirectional-token-state`.
The parent selected this implementation under the current tick. The original
proposal is frozen at SHA256
`7a82845976c83accb74f730fef4500046c6f7e004c5dff84b2ea02c2f0c79650`.
The bounded history review is `../variant_boundary_review.json`; no claim of
literature novelty, exhaustive historical exclusion, or task benefit is made.

## Source scope and actual change

Only eight new independent Python files under
`Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_psbr/`
and one new native YAML under `Cluster/configs/Quard/ctf_hcg_csort_psbr/`
were added. The new YAML is byte-identical to M95, including cluster_mode
`ctf_hcg_csort`, seed 1999, 50 epochs, max_iters 70, GELU setting, all paths,
all loss/optimizer/data values, and one final encoder hierarchy injection.
Native resolution must select the new package by the complete `_psbr` config
basename; a future worker must explicitly reject fallback to the M95 package.

`__init__.py`, `backbone.py`, `loss.py`, `network.py`, and `sample_model.py`
are byte-identical standalone copies. Only `hier_postprocess.py`, `dec.py`,
and the new `middle_recurrence.py` implement the change. No shared resolver,
registry, model, ledger, queue, notes, memory, scheduling, or existing bundle
was edited. All 28 preexisting dirty/untracked file hashes were captured before
writing and independently rechecked by the static checker.

The native CTF constructor prefix is preserved: all three FFNs and LNs are
constructed in their original order. `cluster_ffn[1]` is replaced by
parameter-free `nn.Identity`, removing its registered 525568 parameters rather
than leaving an unused trainable middle FFN. Fine/coarse FFN keys and all three
original pre-norms remain. One `middle_recurrence` module is registered.

Before, for each scale l:

    h_l = raw_l + FFN_l(LN_l(raw_l))

After:

    h_0 = raw_0 + FFN_0(LN_0(raw_0))
    h_1 = PSBR(LN_1(raw_1), current_middle_centers, ids_2, true_support)
    h_2 = raw_2 + FFN_2(LN_2(raw_2))

The original HCG, message normalization, existing level gate/point gate,
single original `inst_feats += gate * message`, ILA, decoder, and mask head
remain. No middle skip, new gate, new residual, Q/K/V, softmax routing,
learned scale/decay/temperature, or additional point injection is introduced.
Original raw banks remain the inputs to the completely unchanged CSORT class.

## Geometry, support, state domain and shape contract

The unchanged native partitioner computes:

    coords_0 = actual per-batch sp_pos
    coords_1 = native mean(coords_0, ids_0)
    coords_2 = native mean(coords_1, ids_1)
    coords_3 = native mean(coords_2, ids_2)

The exact existing `per_layer_coords[2]` tensors are detached and retained in
side cache after the original FPS/aggregation/child-map loop. They are not
recomputed from another scatter; fine-row weighting, empty-ID convention and
all original cluster IDs/maps remain unchanged. This centroid is the native
mean of fine centroids, not a newly introduced point-count-weighted centroid.
The partitioner clears geometry at entry. The bank clears geometry/support
before partition, verifies the original current parent-ID list identity and
lengths, then exposes that forward's side cache. Encoder forwards the cache
and its exact ID-list binding immediately before the unchanged attention API.
Missing, stale-ID, malformed shape, nonfinite geometry, device mismatch or
negative parent IDs fail closed; geometry is never silently reused or clamped.

For batch b, `Kmid = max(ids1_b)+1 = ids2_b.numel()`, including internal gaps;
centers have shape `[Kmid,3]`. Actual support is exactly:

    point_to_mid = ids1_b[ids0_b]
    supported_mid = bincount(point_to_mid, minlength=Kmid) > 0

Internal middle IDs with no real point support do not enter the recurrence and
receive zero output at their original rows. Batch tail padding is separately
excluded and receives zero. A supported centroid at (0,0,0) is valid; no
feature/coordinate-nonzero occupancy heuristic is used. Original raw pooling
still includes its original child slots; this support mask defines only the
new recurrence domain. Unsupported slots have no direct native HCG point
recipient; they cannot become phantom bridges through sibling state.

Supported ORIGINAL middle IDs are partitioned by ORIGINAL `ids2_b[j]` coarse
parent, then sorted by detached `(center_x, center_y, center_z, original_ID)`.
Outputs are inverse-written with `index_copy` to ORIGINAL middle IDs, without
renumbering IDs/maps. Zero boundary state is created separately for every
parent, batch and direction. No hidden state survives a forward. Empty groups
are skipped; a singleton uses the same two zero-boundary self transforms.

## Exact recurrent graph and CPU RNG clarification

Within one sorted supported parent group:

    u_i = Wx z_i + bx
    sf_0 = 0; sf_i = tanh(u_i + Wh sf_(i-1))
    sb_(n+1) = 0; sb_i = tanh(u_i + Wh sb_(i+1))
    h1_i = Wo concat(sf_i, sb_i) + bo

Wx and Wh are each registered once, shared across both directions. Wx is
computed once per group and reused by the two scans. Wh has no bias. There
is one fixed concat/Wo output and no middle residual. Linear and tanh are
explicit operations, not an opaque fused RNN or profiler override.

`design_clarification.json` separately records the root-approved pairing
control: only the new module constructor runs inside
`torch.random.fork_rng(devices=[])`. Original constructor prefix and default
`nn.Linear` initialization are retained; there is no manual_seed, new
initializer, seed/YAML change, CUDA RNG operation, or initialization search.
The intended effect is to restore the original downstream CPU RNG position.
The new parameter random subsequence can be reused by subsequent common
initialization, creating declared correlations. Common parameter equality,
actual loader batch pairing and any training benefit are **NOT VERIFIED**.

## Static checks actually executed

From `D:/project`:

    python -B -X utf8 D:/project/cluster_project/pipeline/diagnostic_bundles/tick_8fafa3d4/psbr_prepare/static_check.py --write

50 checks passed. These include all eight AST parses and builtin compiles
without importing torch; all nine inventory hashes; YAML byte/field equality;
28 preexisting dirty-file hashes; five identical standalone source copies;
complete original HCG/CSORT class AST equality; original FPS/assignment,
aggregation/bank-build AST equality; original constructor prefix; original
fine/coarse branch; complete decoder unchanged except four geometry-transfer
statements; exact shared recurrent registrations; no added gate/QKV/seed calls;
and state/support/inverse-write structure. These are syntax/source checks,
not tensor execution, dynamic parameter inventory, derivative measurement,
resource admission, or evidence that trained efficacy improves.

Static middle arithmetic at C=256: new 262656, removed old 525568, delta
-262912 parameters. For 64 supported middle tokens, new linear MAC estimate
is `5*K*C*C = 20971520`, versus old FFN `8*K*C*C = 33554432`.
This does not sign total-model <=10G FLOPs. Python scans/small kernels/CPU
sorting may increase latency despite fewer MACs. Tanh saturation or recurring
products may weaken/amplify gradients; replacing the middle skip may lose
self detail; parent segmentation misses cross-parent interactions; axis
ordering introduces coordinate-frame and exact-tie ID sensitivity.

## Remaining real native and resource work

All are **NOT_RUN**, and `admission_ready` is false. The parent observed both
server4 GPUs occupied by the existing HAP and CGCA runs. This child performed
no SSH, GPU import/use, stage, lease, sync, native run or Git mutation.

A new exact-PSBR worker/controller must bind the finally committed nine-file
source/version and this preparation; the HRC worker cannot be renamed or
reused as a result. Run only after fresh actual-owner/deadline, resource,
physical GPU/UUID, independent locks, source/assets and current authorization
checks. Preserve both active trainings and use original native train/pretrain,
loader/loss/backward/optimizer/scheduler/YAML entry points.

The minimum future native protocol is two real original TRAIN batches for
champion and candidate with complete input fingerprints actually compared.
Record native loss/backward/optimizer steps, finite Wx/Wh/Wo gradients and
updates, fine/coarse FFN execution and unchanged rawbank/CSORT/ID/map hashes.
Record true-support/internal-empty/padding counts, exact parent groups/order/
inverse, all state boundaries and at least one supported nonsingleton parent
in both actual batches to establish that Wh's history path was exercised.
Verify runtime parameter inventory removes old middle FFN and contains only
one Wx/Wh/Wo set; the candidate resolver must equal its `_psbr.network.Network`.

Any mechanism autograd probes must preserve native .grad identities/versions/
values, optimizer/scheduler and RNG, with an entry guard on every observer;
never substitute probe.backward for native criterion backward. The expected
structural distinction is a cross-token middle derivative inside a parent,
and no cross-parent recurrence derivative. Existence/nonzero magnitude must
be measured honestly under a fixed predeclared readout, not selected after
failure. Zero-state-per-token edge-cut is a diagnostic matched control, not
a new tuning experiment or queued architecture.

Standard resource pair remains the existing fvcore handlers, batch 1/language
1, 20 warmups and 100 repeats with same actual input and median/P90. No custom
operator handler or omitted scan work may manufacture a <=10G claim. Resource
mode installs no observers/probes. A two-step smoke peak with probes includes
diagnostic overhead and must not be called pure native TRAIN memory; no new
pure-TRAIN-memory requirement is silently added. Native efficacy, total FLOPs,
latency, memory, pairing and admission remain unknown until real execution.
