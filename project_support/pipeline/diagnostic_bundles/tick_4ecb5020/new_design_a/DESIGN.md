# CSO: fine-leaf full covariance shape composition

Stable ID: fine-leaf-full-covariance-shape-composition. Source parent is clean
admitted d214, retaining0747 compatibility. No original M234 experiment is
reopened. Root assigns a new experiment ID.

Hypothesis: cross-channel coactivation inside native fine leaves may provide
useful mask context beyond the raw point mean or a diagonal dispersion bank.
The native256-channel features are normalized and linearly projected to eight
channels. The existing fine incidence determines projected means and full8x8
centered population covariance. A fixed six-step trace-scaled Newton-Schulz
approximation to the covariance square root couples its entries after pooling.
Symmetric vectorization weights off-diagonals by sqrt(2), concatenates the
eight projected means, and maps44->128->256. Original fine incidence broadcasts
the learned descriptor. The inherited middle/coarse FFNs, HCG, raw-bank CSORT,
single encoder cluster slot and inst_feats-to-query/mask path remain.

This replaces the old fine FFN/norm rather than adding an extra residual,
gate, routing layer, attention pool, large QKVO, extra injection or new loss.
The new core has41,856 parameters at256 channels; the inherited fine FFN is
removed. Actual whole-model FLOPs/latency/memory are NOT MEASURED.

Distinctions: HVD keeps diagonal within/between dispersion; CSO explicitly
retains cross-channel covariance and applies a coupled matrix function. NPC
keeps spatial-feature crossscatter; CSO has no position-feature statistic.
NDE learns pointwise conditional embeddings before means; CSO aggregates a
fixed full second-order statistic and applies nonseparable matrix processing
after aggregation. RVE learns receiver-relative donor messages on spatial
neighbors; CSO has no donor edges and produces one leaf descriptor. These are
architectural differences, not verified novelty, task deficit or efficacy.

Falsifiable control: projected populations {(1,1),(-1,-1)} and
{(1,-1),(-1,1)} have the same mean/diagonal variance but opposite covariance.
Full square-root descriptors must distinguish them; a diagonal-only control
must erase this distinction. Test actual/default versus literal leaf-loop
reference outputs/input+all parameter gradients. Check padding, scene isolation,
joint point permutation, fine-ID relabeling, singleton/empty-slot support and
finite gradients. Six steps are a fixed polynomial approximation, not a claim
of exact matrix square root; record approximation error on known matrices.

Native harness: reuse tick_b410c66a native worker/YAML/train protocol, changing
candidate package/mode and core observation only. Core prefix is
dec.cluster_att.fine_covariance.; trainable groups are input_norm.*, project.weight,
readout.0.*, readout.2.*, readout.3.*. Hook the whole module and inspect
last_observation; no RVE donor/neighbor hooks apply. Explicit controls are
forward_reference and forward_diagonal_only. All new parameters must receive
finite nonzero native task gradients; compare same common initialization using
the inherited torch.random.fork_rng(devices=[]) protection.

YAML is copied from the admitted native protocol with only cluster_mode changed
to cso_csort. Data, batch2, four persistent workers, augmentation/elastic, seed1999,
50epochs, max_iters70, pretrain/loss/optimizer/scheduler and CSORT weight remain.
Five unrelated inherited source files are copied byte-for-byte so the existing
baseline loss alias and common-state checks remain valid.

Native two-step loss/backward, resource budget, independent source review and
admission are pending. Local AST/static checks do not satisfy native gates.
No SSH/GPU/data execution, main writes or shared ledger mutation occurred.
