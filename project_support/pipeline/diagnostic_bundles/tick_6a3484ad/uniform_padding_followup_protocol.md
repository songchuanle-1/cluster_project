# Uniform Padding Contract: Follow-Up, Not An Attention Variant

Same stable padding diagnosis ID. Unexecuted steps below are PENDING,not
PASS,resources,training or novelty. Preserve all original negatives.

## Evidence And Boundary
Actual FLE and existing availableM95epoch16 same-shape batch2 tests show
masked-only feature changes affect valid hierarchy outputs and finalmasks.
Identity/zero-scale/nonpaddednulls0. Different trainedweights prevent using
effectsize differences as a causal architecture comparison. A sharedbugfix
must apply uniformly;do not change onebaseline or relabel oldchampionmetrics.

## Contract And Derivation
With valid indicator v and n=sum(v),context should be mu=sum(v_i*x_i)/n
for n>0. Existing g=sum(x_i)/N includesmaskedfeatures. Levelweights are
softmax(Wp*x_i+Wg*g+b);maskedinput changesvalidweights via Wg/N. Different
scale messages transfer this to validoutput;zero-scalecontrol removes it.
An allmaskedrow must remain outputzero with an explicit safe denominator.
The sourceCPUgradient fixture confirms this path,not trainedefficacy.

## Next Test Before Any Production Change
Freeze a separate diagnostic revision under a fresh lease. Start exactsource
CPUtests for no-padding identity,allmasked,zero-scale and masked-gradient0
with retained validgradients. Then run matched native forward/backward
interface tests on BOTH original frozenmodels using identicaltensors and
declared precision/finite-difference bounds. No optimizer or epsilon sweep.
Report gradientpaths,peakmemory,latency,failures and sourcehashesbefore/after.
Current masked-validmean inputfilling is only an invarianceprobe of the OLD
operator,not a productionreplacement,Phase1variant or architectureclaim.

## Interpretation And Resources
Correctness doesnotprove trainedgain,generalization,newattention or admission.
Any uniformbugfix needs separate review,then genuinely structural research
still needs diagnosis,derivation,originalpapers,matchedcontrols,efficiency,
independence andnativeadmission. No VALselection or automaticretraining.
Localorchestration/static only. Nativework must freshlycheck authorized
server4physicalGPU0 orserver3physicalGPU1,occupation,lifetimeleases and
realdeadline. PriorGPU0release doesnotgrant futurecapacity. NootherGPU,
foreignjobeviction,lockdeletion,M201recovery or schedulerchange.
