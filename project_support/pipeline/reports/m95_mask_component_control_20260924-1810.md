# M95 Mask-Component Control Boundary

2026-09-24 18:10 Asia/Shanghai. This is a source-bound diagnostic
specification, not a native measurement or a candidate admission.

The frozen M95 criterion expands GT masks according to each GT's matched
query count, but `loss_masks` indexes the expanded mask tensor with the
unexpanded GT indices. A repeated match for an earlier GT can therefore
address another GT's mask. The source-bound synthetic contract illustrates
this case; its incidence among the frozen 256 TRAIN expressions is unknown.

The affected computational paths are mask BCE, mask Dice, and the score
target computed by `get_iou(pred_mask, tgt_mask)` when its >0.5 filter
admits the pair. The indicator-label path uses matched query indices and
does not read `tgt['masks']`; it must not be counted as a direct mask-binding
effect. Token maps are repeated from the first expression row, not
instance-specific maps, so the capture does not establish their causal role.

Native control sequence after GPU7 clearance:
1. Verify authorized GPU7 occupancy and memory, SSH, code/root/runtime/data,
   M95 checkpoint hash, frozen manifest hash, and nine-file producer hash.
2. Run one ordered, opt-in 256-row TRAIN capture with matcher causes and
   query states; check all-row GT binding, collision intersections, six
   exclusion rows, and four preregistered same-ID scenes.
3. On the same captured forward, compare original versus correctly
   GT-indexed masks while holding matched queries, indicator labels,
   predictions and other losses fixed. Report affected-pair and scene
   denominators, BCE/Dice/score-target changes, and whether the score
   filter crosses 0.5. Separately compare a label-only control and the
   coupled intervention. These are controls, not independent variants.
4. Reject a mask-binding explanation for exclusion failures if no affected
   target pairs occur in those six rows; do not attribute co-occurrence as
   causal improvement. A new supervision unit still requires its own
   expression-level mechanism, prior-art comparison, native backward,
   resource and independence gates.

At 18:07:48, read-only SSH showed external PID 3694608 using 41,996 MiB
on GPU7 (42,023 MiB used, 39,057 MiB free). No native diagnostic,
training, sync or queue operation was attempted. The three due IDs remain
blocked; retry after 18:30 Asia/Shanghai or when occupancy clears.

Source identities (SHA256):
- `Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/loss.py`: `c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5`
- `scripts/native_manifest_capture_20260922.py`: `d172f98c88ee82f627f935f152296ffdd7804c095326dfde1463ab87e6c7e5ab`
- `scripts/m95_repeated_gt_mask_contract_20260924.py`: `d1bf42ed9cfe0b9f0caa72965da314104c891438028e8e8fa69e41effab57851`
- `scripts/m95_exclusion_cause_audit_20260924.py`: `77420392d47631bb586a2e399b261144b7555f5ada878c017f5cb6624831c4f1`

24 focused exclusion-audit synthetic tests passed. Their fixtures do not
measure native incidence, backward behavior, resource cost or efficacy.
