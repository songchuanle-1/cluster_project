# Boundary And Adjacency Verification
## Scope
Completed284 frozen M95 banks/71scenes,missing0;bank hashes and raw SP
alignment verified. All identities/raw hashes in boundary_adjacency_audit_20260914.json.
CPU only. Graph:existing scale50,majoritySP occupied voxel,six-face contact.
536314/7975431 voxels have multiple SP labels;minority contacts may be lost.
GT boundary endpoints plus one graph hop define the correction region.
Strict SP-IoU>.5 success;not substituted for original point-level metrics.

## Results
|Subset|Banks|Scenes|Boundary oracle recovery|Equal-size random recovery|Excess components|
|---|---|---|---|---|---|
|recoverable|109|58|38/109|6.84%|28/109|
|limited|30|24|17/30|3.70%|15/30|
|all failures|139|62|55/139 (39.57%)|6.17%|43/139|
Random100regions/bank,seed1999. Paired recovery advantage33.403percentage
points;10000scene-bootstrap95%[25.140,42.014]pp.
Recoverable mean region covers10.50%SPs/48.03%errors;
limited8.38%SPs/58.02%errors. Success excess-components20/145.
Fragmentation is neither necessary nor sufficient for failure.
GT corrections are diagnostic upper bounds,not deployable results.
Scene bootstrap does not remove failure-mining selection bias.

## Original Literature
Original PMLR Kervadec2019 Boundary loss for highly unbalanced segmentation,
local boundary_kervadec2019.pdf/text,section2 Eq4/5 verified.
Eq4 integral phi_G*(s-g) matches proposal1101 up to count/diagonal scaling;
Eq5 drops constant GT term. Gradient same up to scaling.
Reject unchanged signed-distance proposal as a new core mechanism.
It can be an attributed control for a genuinely distinct later mechanism.
Search/open tools returned empty results;publisher original PDF fetched/read.
Adjacency exact-operator originality remains unverified;no exhaustive claim.

## Disposition
Boundary-specific diagnostic gap is now filled with controlled positive evidence
in this frozen corpus. Trainability and a distinct mechanism remain open.
Adjacency has a43-bank excess-component subset;need component/contact
interventions and original-source comparison before admission.
No new model/config/queue change. Decision20260914-200939_next_batch.md.
Concurrent scheduler recorded M195 runtime duplicate-seed crash20:07;
that separate operational issue does not change this frozen-M95 diagnostic.
