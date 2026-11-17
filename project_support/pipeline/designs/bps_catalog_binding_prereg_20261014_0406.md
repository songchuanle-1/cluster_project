# Production Metadata Binding Regression

- Original V1 package/config copied verbatim to
  pipeline/reports/bps_package_v1_1d59938f077948578e91e2cf34fc9d53;
  remote V1 staging and all bound test results remain untouched.
- Same stable ID, loss/geometry/inference calculations and all numerical
  hyperparameters unchanged. V2 binds the exact generated TRAIN catalog hash
  and defers loading until first loss-time access, not model construction.
- Repeat the original full native batch1/batch2 protocol on V2, not assuming V1
  results certify modified code. Check matching hash acceptance and deliberate
  changed-byte rejection. Prediction from a fresh catalog object pointing at
  a nonexistent path must succeed with zero prepare calls/no payload loaded.
- Full/empty catalog prediction controls remain within the same actual model,
  not original champion numerical identity. Original ordered reductions/sparse
  index support and historical whole-forward FAILs remain documented.
- No scientific new variant, no loss scaling, no new labels, optimizer or commit.
