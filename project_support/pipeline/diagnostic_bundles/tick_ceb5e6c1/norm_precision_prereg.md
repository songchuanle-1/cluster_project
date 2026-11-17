# Diagnostic Norm Scaling Precision Revision 1

Same stable self/nonself diagnostic,not model revision or mechanism selection.
Failure evidence:original native threshold failed;independent float64norms
of captured float32vectors show actual norm drift up to1.46370154e-6,
so this is not solely a GPU measurement artifact. Original failures remain.

Change only diagnostic donor normalization arithmetic:compute recipient
and donor L2norms,ratio and multiply in float64,then round the replacement
once back to the original float32. Keep original donor permutation,leaf
membership,zero-donor handling,tie mean,self term and original summation
residual. Model weights,forward precision,checkpoint epoch2,8TRAINscenes,
all source/identity/suffix controls and original1e-6threshold stay unchanged.
Add an independent float64 true norm error<=1e-6check,never remove the
original GPUfloat32norm<=1e-6check. No temperature or coefficient sweep.

Prediction:single-round normalization reduces actual vector norm error;
old and added strict native controls both must pass on every scene before
interpreting causal task readouts. First run CPU captured-vector and
zero/identity/tie/singleton controls;then full frozen native cohort. A
remaining failure is preserved and not fixed by widening tolerance.
The revised arithmetic is an implementation repair of a diagnostic matched
control,not a deployed model change,training restart or new innovation.
