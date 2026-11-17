# M208-HRC implementation preparation

Stable ID: `hierarchy-bottom-up-refined-token-composition`.
This is a registration draft for root review, not an admission receipt. No native/GPU/SSH/sync/queue/Git commit ran. Both authorized server4 cards were occupied by HAP/CGCA at the root's current observation. Efficacy, measured peak memory and runtime remain UNKNOWN.

## Source graph

Control M95 builds raw means `mu0 -> mu1 -> mu2`, then independently computes `hl = mul + Fl(LNl(mul))` for all three scales. HRC leaves those original raw banks intact, then changes only the FFN input chain:

```
h0 = mu0 + F0(LN0(mu0))
u1 = mean_ids1(h0)
h1 = u1 + F1(LN1(u1))
u2 = mean_ids2(h1)
h2 = u2 + F2(LN2(u2))
message = original_HCG(h0, h1, h2)
```

Each existing FFN executes exactly once. Existing parameter names, LayerNorms, FFN definitions, dropout, geometric IDs/FPS, raw CSORT inputs/loss, original HCG level gate/readback/projection and the single final inst_feats update are unchanged. No parameter is added (the existing three FFN+LN blocks have 1,578,240 parameters at C=256). Extra arithmetic is two fixed-child mean reductions, O((Kfine+Kmid)*C); resource cost has not been measured.

`refined_parent_mean` uses each batch's `ids[lvl].numel()` child prefix and the original padded parent width. It cannot pool batch padding. Parent IDs, including gaps, retain their original integer slots; `dim_size` is the original parent-bank padded width. The original raw parent pooling equally counts every child slot. HRC therefore also retains internal empty child slots: their raw value is zero, but FFN bias can become nonzero and propagate upwards. No occupancy filtering, point-count weighting or new gate was added. Empty-parent output is zero before its existing FFN. Padding rows can acquire existing FFN bias but are excluded by the next IDs prefix and never indexed by valid point IDs.

## Limited historical countercheck

Read-only checks covered the closest sources rather than all history. CCP adds refined parent values to children (top-down). REAG_CASC performs two point readbacks with point-feature reaggregation between them. lite_agg learns per-point aggregation weights. MFP retains independent scale FFNs. These are not the HRC chain above. pce_audit and mdc_review reported no explicit same-graph or direct-ban conflict in that bounded check. This does not establish literature novelty or benefit. All old holds/rejections remain in force.

## Static evidence

Eight independent model sources and one native YAML were added only under the new `_hrc` paths. Six copied sources are byte-identical to M95; only `hier_postprocess.py` plus the new helper differ. All eight sources compile via builtin `compile`/AST without executing/importing model code. The CTF constructor and the original partitioner, SharedClusterBank, HCG and CSORT classes have identical ASTs. Native YAML is byte- and semantic-identical to M95, including seed1999, 50epochs, scheduler max_iters70 and pretrain. Static checks do not prove native behavior. `preparation.json` binds all nine SHA256s and original control hashes; `validate_static.py` reproduces read-only checks.

## Future native worker adaptation (not executed)

1. Bind a fresh foreground token/deadline, exact tested source commit and all nine hashes; assert resolved Network.__module__ is the exact HRC package (the native resolver catches ImportError/AttributeError and otherwise can silently fall back to the default package); independently observe an authorized idle physical card/UUID and acquire existing diagnostic locks before torch setup. Do not use the current occupied cards or reuse an old lease. Preserve the original native train.train/pretrain/loader, the original two TRAIN batches, loss, backward, optimizer steps and paired native resource protocol; use no synthetic batch or trained-M95 initialization.
2. Replace the HAP-specific affine/pinv observer with wrappers around this package's `refined_parent_mean` (two calls per forward) and `_cluster_to_points` (one call receiving h0,h1,h2). Preserve inputs/outputs rather than recomputing model operators. Record per-batch child lengths, parent widths, ID minima/maxima/unique/empty-slot counts, raw-bank and ID fingerprints, tensor finite status, and padding exclusion. Verify the two means reproduce a separately accumulated fixed-child sum/count reference on those real native values; do not silently drop internal empty rows.
3. Hook existing three FFNs/norms: once each per forward, correct order, finite input/output/feature gradients, finite nonzero original FFN weight gradients, and parameter hashes change after each of the two optimizer steps. Confirm fine output is the M95 fine residual FFN for the same input and that raw bank/CSORT fingerprints are unchanged. Do not expect candidate losses to equal M95 losses.
4. A source-specific dependency audit should capture h2 before original HCG and use a predeclared nonconstant fixed probe of its valid tokens. `autograd.grad(probe(h2), F0.weight/F1.weight, retain_graph=True, allow_unused=True)` is structurally unused in control M95 and should generally be finite/nonzero in HRC. Use autograd.grad rather than accumulating probe gradients into native .grad, keep native loss/backward unchanged, and restore wrappers in finally. The expected new paths are F0 -> mean1 -> F1 -> mean2 -> F2 and F1 -> mean2 -> F2. This is a graph/mechanism check, not an efficacy claim; exact observed zero must be investigated rather than waived.
5. Confirm original HCG and last inst_feats update remain on the native mask/loss graph; record mask/total losses, full native gradient summaries, optimizer updates, both real batch fingerprints and paired max allocated/reserved/NVML/time. Only fresh complete evidence may satisfy native/resource admission. Current statuses are NOT_RUN/resource_blocked; no gate is marked PASS.
