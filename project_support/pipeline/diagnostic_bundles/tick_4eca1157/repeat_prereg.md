# Native Training-Prefix Repeatability - New Finite Diagnostic

StableID native-train-prefix-repeatability-audit. Concrete trigger:all4
train-mode backwardsmokes passed and batchhashes matched,but original/ref
pre-gather fingerprints differed for BOTHmodels. Difference magnitude was
not captured;do not infer taskgain or blame a specific backend yet.

Hypothesis:identical originalmodels,initialcheckpoints,inputbatch andseed
produce bitwise-identical pre-gather tensors and targetgradients in fresh
processes. Test ONLYoriginalconditions,2fresh repeats forM95 then2forFLE,
samefirst2TRAINgroups/batch2/seed1999/native.train/backward/clip. Nooptimizer,
newseed,schedule,VAL,modelchange or referencecondition in this test.

Before the actual gather,save tensorarguments/tokens/IDs/mask/fine_message
and hash CPUtorch/CUDAtorch/numpy/Python RNGstates. Capture rawarrays only
to this diagnosticstage. Retain originalweights/parameterflags. Report
allnonidenticalelements,maxabs/meanabs/relativeL2,loss andtargetgradient
differences,and RNG/batch/sourceequality. No tolerance calibration or gate
relaxation;bitwiseequality is the tested property,not a required efficacy
gate. Two repeats cannot estimate trainingseednoise or a confidencebound.

If RNGstates match but tensors differ,record native numerical repeatability
limits without asserting a particularatomic/kernel cause. If RNG differs,
keep stochastic-callsite causeUNKNOWN. Do not retry untilmatching. Preserve
all earlier raw results. This diagnostic is independent of the completed
finitepaddingcontract,not a newattention mechanism or fillertrainvariant.
Sourceboundstage/currentlease/liveidleGPU0/3locks required eachprocess.
