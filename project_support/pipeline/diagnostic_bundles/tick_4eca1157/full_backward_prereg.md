# Frozen Native Training-Mode Backward Smoke Test, No Optimizer Updates

Continue SAMEpaddingID and unchanged diagnosticreference1. Both originalflag
nativeinterface probes passed at1e-6;allfalse flags reproduce baselineerror,
restoredflags reproduce exactnative outputs. Initialfailures stayimmutable.
Module-only resource results do NOT cover fulltrainingsteps.

Run four independent fresh processes/checkpoint loads in fixedorder:
M95original,M95reference,FLEoriginal,FLEreference. Each uses the FIRST TWO
frozenTRAIN scene groups/originalbatch2/config/seed1999. Diagnostic loader0
workers only;trainingconfigworkers4 unchanged. model.train(),native loss
forward,model.zero_grad(),loss.backward(),originalconfigured gradientclip.
No optimizer object/step,schedulerstep,epoch advancement,checkpointwrite,
validation or trainingloop. In-processBNbuffers may change as native.train
requires;the source checkpoint and productionfiles remain unchanged.

Reference condition temporarily binds the exactsource reference gather
method ONLY. Originalcondition calls actual originalbound method. Restore
methods in finally,alloriginalparameterflags preserved. Set RNG1999just
before nativeforward for bothcounterparts. Saveinput and pre-gather prefix
fingerprints for transparency;differentprefixes forbid claiming matched
taskgain and are NOT retried until equal. Loss/parameters differ between
M95/FLE,so neverinterpret crossmodeldelta as an architectureestimate.

Require finite loss,finite existing trainablegradients,and nonzero gradients
on actual cluster level_gate/point_out_proj weights. Record missinggradient
denominators,pointfeaturegradient(masked andvalid) and bothclip norms. The
wholefeature has OTHER downstream paths:nonzero maskedgradient there does
not contradict the separately isolated gathercontract and is not hidden.

Record allocated/reserved peaks and timing for THIS SINGLE fixed-batch
forward/backward/clip,not an all-training peak or a warmup/repeatbenchmark.
Interface resources already usebs1/20warmup/100repeats;keep scopes separate.
No efficacy/novelty/admission claim follows from backward smokePASS. The
single-op reference remains a nonnovel correctnesscontract,not a Phase1
structuralvariant or permission to restart stoppedFLE.

Fresh currentlease/deadline/server4identity/GPU0UUID/liveidle/no foreign
contexts/3lifetimeflocks beforeEVERY process. Bound alarm;save partialresult
and exactfailures;do not lower gates,evict jobs or retry blindly onOOM.
