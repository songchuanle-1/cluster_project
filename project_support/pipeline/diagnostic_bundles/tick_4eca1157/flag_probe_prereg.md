# One Diagnostic Execution-Adapter Probe - No Arithmetic Repair

Preserve BOTH initial failures:all gather/gradient/null controls0 but native
suffixmasks differ by1.90735e-5(M95)/2.67029e-5(FLE),above frozen1e-6.
Do NOT claim overallPASS or use reference masks from those invalid runs.

Hypothesis:unnecessarily changing modelparameter requires_grad flags or the
order of autograd before suffixreplay changes runtimeexecution. No source
evidence of such a branch was found in project customattention;causeunknown.
This is a one-time paired probe,not retry-until-success or normrevision3.
Keep referencefunction1,originalweights/data/precision/tolerances unchanged.

For each counterpart,one same frozenbatch2 nativeforward. BEFORE autograd,
replay the exact original suffix with initialparameterflags,then allfalse,
then restoredinitialflags. Save all errors. Next differentiate original/
reference/zero-scale gather with flags UNCHANGED. autograd.grad targets only
the input tensor and must not accumulate any parameter.grad. Replay suffix
again and record all errors. All source/gather/null/normal-originalflag
checks retain1e-6. Frozenflag probe is a nonnative execution-context contrast,
not an excuse to discard an originalflag failure. If originalflag checks
still fail,this adapter hypothesis is unsupported;do not makeanotherblind
revision. Capture controls before assertion,including on failure.

Resource benchmark proceeds only after all originalflag gates pass. Same
20warmup/100repeats,bs1,gather-only scope. No productionpatch,optimizer,
training,VAL,admission,sourcearithmetic/tolerancechange or newcheckpoint.
