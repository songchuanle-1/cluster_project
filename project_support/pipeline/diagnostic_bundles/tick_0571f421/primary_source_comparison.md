# Primary-source mechanism comparison

Observed 2026-10-17, current foreground tick. This compares actual operator roles; it is not a completeness certificate or novelty PASS.

## Point Transformer

- Verified source: Hengshuang Zhao et al., Point Transformer, ICCV2021, arXiv2012.09164v2 PDF, pp3-4, equations1-4. PDF text was directly retrieved this tick.
- The paper distinguishes scalar dot-product attention from its local vector-attention layer. Its proposed layer uses learned feature transformations, relative-position encoding and channel-wise weights over neighbors; it also uses hierarchical point processing. Recipient-specific local aggregation is therefore prior work, not this project's invention.
- Current FLE uses unprojected per-head scalar dot products within existing geometric fine leaves. Position defines the neighbor support, not a learned relative-position term. Middle/coarse M95 tokens, their FFNs, original level fusion and the inst_feats-to-mask path are retained. These are implementation differences, not proof of a materially new scientific contribution.

## RefMask3D

- Verified source: Junran Wu et al., RefMask3D: Language-Guided Transformer for3DReferring Segmentation, ACM MM2024, arXiv2407.18244v1 HTML, sections3.1-3.4/equations1-5. Full HTML was directly retrieved this tick.
- It couples hierarchical point-language fusion, language-aware point aggregation and object queries with point-mask decoding. Thus both language-guided hierarchical features and generating masks from query/point features already have explicit precedent.
- Current FLE does not introduce its language-aware pooling or object-query objective. It replaces M95's fine shared-token readback with per-recipient same-leaf point exchange while keeping the existing decoder and native losses. The tested question is whether that information unit helps this frozen project protocol, not whether local attention or query-point mask decoding is new.

## Project-specific controls And Verdict

- Source comparison and current native tests distinguish recipient-specific point exchange from banned attnpool's one learned pooled token. No cross-variant import, new gate, learned scalar, language routing, large projection, new loss or repeated injection was added. This is not authorization to reopen old families.
- Four fixed TRAIN scenes/sixteen expressions passed native forward/backward and same-prefix candidate-versus-uniform controls. Those tests establish graph activity and mask influence, not trained improvement, population causality or paper-level novelty.
- Whole-mechanism material novelty is NOT established. Treat this candidate as a structural hypothesis test using known operators; do not advertise it as a confirmed core innovation. Original HDS negative training, previous fine tie failure and uncertainty remain in force. Efficiency and full post-training comparison remain separate requirements.
