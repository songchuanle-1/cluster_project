# Native Norm Failure Capture - Diagnostic Instrumentation 1

Same stableID fle-self-neighbor-content-separation. Original frozen runner
failed on scene2 at the unchanged norm<=1e-6assertion after2nativeforwards,
one completedscene and3suffixreplays. Original result/runner/manifest remain
unchanged. This is not FLEmodelrevision2 or a tolerance/precision change.

Copy original diagnostic files into an independent capture stage. Add only
control-attempt metadata and,after a norm failure is detected,before the
SAMEassertion,save original fine inputs,exact decomposed nonself tensors,
the original-permutation replacement and their GPUfloat32norms. Recompute
only those diagnostic quantities for capture;never use their mask outputs
as a passed causal intervention. Originalmodel/source/weights,cohort8scenes,
checkpoint epoch2,identity/source/suffix controls and1e-6stayfixed.

Prediction to test:the second fixed scene reproduces a finite norm mismatch;
raw vectors distinguish donor-scaling representation error from float32
norm-reduction measurement error. Inspect float64 norms of the saved exact
float32vectors onCPU independently;this is forensics,not permission to
change the native tolerance or call an invalid cohort PASS.

Bind new diagnostic-only manifest hashes and current-token lease;the
production assets/cohort fields must equal the original manifest exactly.
Acquire current pinned GPU0andall3lifetime locks beforeCUDA. Preserve all
original and capture failures;no training,restart,newcheckpoint choice or
model/config/schedule change. Any actual correction needs a separate
evidence-backed pre-registration and retest,not this instrumentation.
