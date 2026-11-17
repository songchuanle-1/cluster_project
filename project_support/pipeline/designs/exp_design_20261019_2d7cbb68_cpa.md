# Experiment Design - cluster_project
## 1. Motivation
Literal goal:hierarchical information interaction must genuinely update point/superpoint inst_feats
used with query for masks. This candidate tests coarse-global semantics while retaining fine/middle paths.
## 2. Current Best Results
| ID | State | Best mIoU | Role |
|---|---|---|---|
| M95 | Historical cached | .5020 | Comparator;availableepoch16provenance caveat |
| M203-FLE | Stopped cached | .4885315597 | No restart |
## 3. Analysis & Direction
Variables:x_i are current point features;C are raw8coarse means;V=C+FFN(LN(C)).
For each existing head,A=softmax(xC^T/sqrt(d_head));new coarse message=AV.
Fine and middle messages,existing scale fusion/output projection/message norm/outer encoder path stay unchanged.
Revision1 moves ONLY keys from V to C,no temperature/heads/scale/gate/QKV tuning.
Gradient:remote values receive A-weighted task gradient;native actual A gradient and all coarseFFN/norm gradients
are finite/nonzero both fromM95checkpoint and newNetwork+originalbackbone. No new trainable parameters.
Degeneracies:identical keys or zero queries give mean values;coarse nonempty bank required.
Complexity:O(B*N*Kcoarse*C),Kcoarse8,notN2;attention bufferO(B*heads*N*8).
## 4. Experiment Plan
| StableID | Current phase | Actual result | Next |
|---|---|---|---|
| coarse-semantic-point-cross-attention | validation | Computational path/resources pass;semantic diagnosis unpassed | Frozen error-point readout |
Original prototype,raw-key repair,uniform and cyclic mismatch all retained. Query/criterion inputs/matching
are fixed within each capture;different process prefixes are NOT claimed exactly paired.
## 5. GPU Allocation Plan
Only server4physicalGPU0 used with pinned hostname/UUID and3lifetimeflocks.
server3physicalGPU1 foreign-busy at06:13Shanghai,laterUNKNOWN. server4GPU1 NOTauthorized.
## 6. Implementation Checklist
- Independent8sourcefile package+same-numerical-config:done,no foreign variant imports.
- Full original criterion backward,workers0/4,cold backbone initialization:done.
- Same-handler resources bs1warmup20repeat100,matched input hashes:done.
- Task deficit and semantic controls:NOTpassed;new error-point readout unrun due guarded budget.
- Commit/safeFFsync/admission/queue/launch:NOTperformed;no trainingoptimizer/schedulersteps.
## 7. Risk Assessment
Near-uniform attention and inconsistent semantic controls remain material risks.
Do not infer benefit/harm from small pretrained loss changes or use residual diagnostic as successor.
Resource9.769168428G versusM959.762532428G;median35.9614vs35.3617ms;
inference memory+1.2878%,matched train activation peaks+0.3289%to+0.7063%.
Full optimizer peak and original no-cluster resource delta UNKNOWN;all default budgets unchanged.
## 8. Smell Check And Prior Art
New coarse-point information edges,not numeric-only tuning;no new learned gate/scalar/projection.
Attnpool/qcond/agg/multi,TrueRoute,FLE,relation2Dtransport checked at implementation level.
Ordinary cross-attention and latent output-query reading are prior art(PerceiverIO,arXiv2107.14795).
Material novelty UNKNOWN;this is an unadmitted structural hypothesis,not a novel attention primitive.
## 9. Post-Training Plan
Only after real admission:unchangedScanReferVAL mIoU,baseline/champion comparators,seed1999/
epochs50/max_iters70 and lightweightPareto;scene clustering,predefined relation/same-class groups.
Evaluation noise floor unquantified;no test/VALmechanism selection,no extra datasets/seeds.
Status:VALIDATION,notAPPROVEDfortraining.
