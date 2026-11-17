# Frozen 2D feature indexing contract

Stable diagnosis ID `m95-sample-context-support`. This tests a distinct
data-provenance failure, not the failed local modality-disagreement mechanism.
The training dataset samples points, remaps retained original superpoint IDs
to dense IDs, and indexes scene CLIP features by `unique`. If the remap is
not order-preserving with the indexed CLIP rows, a prediction-blind physical
feature correspondence error could affect all downstream losses.

Before running: inspect the exact native dataset and decoder source. Test the
indexing contract with noncontiguous original IDs, permutation, duplicate
sampled points and full retention. The invariant is that each retained point's
dense superpoint ID selects the CLIP row indexed by its original superpoint ID.
Also verify that the decoder receives the selected features and does not
reindex them against the original sparse IDs. A counterexample in the actual
native source path would justify a bound native check; passing synthetic
contract cases only rejects this narrow indexing-bug hypothesis, not a
native-data correspondence defect. No model change, admission or training
follows from this audit.
