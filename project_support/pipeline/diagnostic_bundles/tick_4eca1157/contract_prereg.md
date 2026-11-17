# Uniform Padding Reference Contract - Diagnostic Revision1

StableID hierarchical-padding-context-invariance-audit;continuation of the
already frozen follow-up protocol. NOT a productionmodel revision,not
normhelperrevision3,not a new attention mechanism or training admission.
Preserve the original32TRAIN QF failure/replication and sharedpadding facts.

## Exact Reference And Scope
Parse each bound M95/FLE _cluster_to_points function from actual source.
Compile an unchanged original and one diagnostic copy differing ONLY in the
global_mean assignment. Define count=(~mask).sum,mu=masked_fill(mask,0).sum/
count.clamp_min(1). Use native original mean on rows with count==N to retain
bitwise no-padding behavior;otherwise mu. Allmaskedrows get zero context
and original output masking. No params,temperature,labels or learned change.
All other source statements are AST-identical. Source/config/checkpoints
and all production files stay unchanged. Use finite inputs;nonfinite padding
robustness is outside this initial native contract and not silently claimed.

## CPU Before Native
Both EXACT existing checkpoint gate/projection weights,seed1999,float64CPU,
B1,N6,C256,threelevels(2,1,1tokens),cases:general4valid2masked;no-padding6;
allmasked0valid;zero-scale4valid. Reconstructed source functions share weights.
Require no-padding original/reference output+gradient equality at1e-12;
masked-gradient0 and allmasked/zero-scale output-gradient nulls at1e-12.
Changing masked finitevalues and appending3maskedpositions preservesvalid
reference outputs at1e-12. Keep valid gradients nonzero on general/no-pad.
Central directional difference has ONE frozen step1e-5 and bound
abs(error)<=1e-8+1e-5*abs(autogradderivative). Noepsilon/threshold sweep.
These are synthetic trainedweight/source fixtures,NOT nativebackward.

## Native Interface And Frozen Data
Use exact availableM95epoch16(not verifiedhistoricalchampionweights) and
uniqueFLEterminalbest13. FIRST TWO previously frozenTRAIN scene groups,
originalbatch2/seed1999/config/cohort unchanged. One fullnative lossforward
per model in eval/no_grad captures actual gather arguments,cluster message,
ILA and finaldecoderprefix. Reconstruct source/gather/message/suffix<=1e-6.
Disable parametergradients only in diagnostic replay;parametersunchanged.
Differentiate valid squared gather output w.r.t.actual captured pointfeatures
under original and reference,keeping token/fine paths detached to isolate
the context interface. Reference maskedgrad must be0,validgrad finite/nonzero;
zero-scale gradnull and no-padding-row equality retain1e-6. Record native
interfacebackward separately from fullmodeltrainingbackward(0). Fixed-shape
maskedvalue0/1 and masked-validmean cases must preserve reference output<=1e-6.
Replay reference message through same suffix;report masklogit differences,
not incorrect shared-index multi-scenePiou or claimedtraininggain.

## Resource Protocol And Limits
Actual captured firstrow,bs1,20warmup/100repeats,CUDAevents,median/P90,
allocated/reserved peaks and incremental allocated memory,for BOTH original
and reference per model. Scope is gather-interface latency/memory,NOT full
model/wholetraining resources or FLOPs/admissionPASS. No performance selection.
Fresh server4identity/physicalGPU0UUID,idleness/no foreigncontexts and all3
lifetime training/diagnostic/exclusiveflocks before EVERY CUDA run. Original
localtoken/deadline;bounded alarm;save partial results;nooptimizer,VAL,queue,
productionpatch,newseed,newdata/schedule or bannedroute reopening.
