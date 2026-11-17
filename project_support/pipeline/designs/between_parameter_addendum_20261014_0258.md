# Original Parameter Reachability and Generic Shape Control

- Support-excess path was active on4of8frozen native groups;6resolved GT
  self-excesses0, two events unavailable. Center path stillzero. Keep all raw
  outputs and no-op/unknown cases, no scene/tolerance/weight changes.
- On the same8native groups, differentiate the standalone component with
  respect to all ORIGINAL trainable parameters, twice on the same capture.
  Record finite, reached, nonzero and1e-6max-repeat results. Unused original
  semantic heads are not a new-parameter failure. This is NOT full candidate
  repeated forward/backward or a replacement for historical strict failures.
- Generic shape control uses native GT center and its point-count-weighted
  spatial variance, not physical reference roles:
  relu(E_pred[||x-C_GT||^2]/V_GT-E_GT[||x-C_GT||^2]/V_GT).
  Zero GT variance remains unavailable, no fitted epsilon or loss scale.
  Same expressions, matches, num_boxes and native masks as the relational
  component; compare actual mask-gradient norm/cosine/max difference.
- A different gradient is only control separation, not causal benefit,
  independent novelty or training admission. No optimizer/parameter update.
