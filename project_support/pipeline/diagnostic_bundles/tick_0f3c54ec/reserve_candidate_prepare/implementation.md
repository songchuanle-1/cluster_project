# PSC private source preparation

Each fine node receives a centered native position-feature cross moment J0(3C).
Private parent coordinates and features both use equal true-supported children.
W1=mean_children(J0); B1=cov(child_coordinate_center,child_feature_center).
W2=mean_children(W1+B1); B2 is the analogous middle-to-coarse cross moment.
Rows are fine=[z0,J0,B1(parent),B2(grandparent)],
middle=[z1,W1,B1,B2(parent)], coarse=[z2,W2,B2,zero], each 10C.
One shared10C→C→C nonlinear factor supplies original raw-bank refinement deltas.
Original CSORT/HCG/single inst_feats output, supervision and native YAML remain.

No arbitrary temperature/normalization/gate/scalar or new Q/K/V/O projection.
The new information edge passes the existing native coordinates to this core.
The generic covariance mechanism is not claimed novel, useful or a bottleneck.
The identity example separates information from HVD/HAP but does not prove gain.

Only dec coordinate forwarding, CTF constructor/forward, CSORT argument passing
and the new position_scatter.py differ from the original native package.
The extra module uses fork_rng after original initialization draws; real paired
common initialization still must be checked natively and is NOT_RUN.
