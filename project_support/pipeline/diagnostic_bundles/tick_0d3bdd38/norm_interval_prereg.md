# Diagnostic Arithmetic Revision2 - Before Execution

Stable ID:fle-self-neighbor-content-separation. This is the final bounded
diagnostic arithmetic revision,not a production FLE/model change. Preserve
original/precisionrevision1 failures and unchanged1e-6native norm assertion.

Defect:one-round true-norm scaling controls exact-real radius,but the cast
vector's original float32 reduction can cross more than1e-6from the recipient's
float32 norm. Native versus high-precision error must both be bounded;neither
measurement is silently substituted for the other.

For a nonzero donor d and recipient R,only scalar radius r may change:
q(r)=float32(d_float64 * r / norm64(d)). The original spatial donor map,
recipient self term,zero-donor fallback and exact-coordinate tie policy stay.
Require BOTH abs(norm32(q)-norm32(R))<=1e-6 and
abs(norm64(q)-norm64(R))<=1e-6. Identity returns the original tensor exactly.

First try r=norm64(R),which preserves revision1 output where valid. Otherwise
bisect r in[0,2*max(norm32(R),norm64(R))+1e-6]. Positive rounding and sums of
squares are monotone in radius;classify below/above using BOTH constraints.
If both constraints disagree,or64fixed bisections exhaust without a feasible
cast vector,record infeasible and FAIL.64is a finite numerical solver bound
beyond float64mantissa resolution,not a model hyperparameter. No label/loss/
mask/IoU/VAL feedback or candidate selection is allowed. Record adjusted-row
counts and iterations. No new parameters or donor-direction mixing.

Before native use:run both saved failure captures(4expressions each),all
original CPU contract groups against the new helper,and finite-gradient
controls. Original float64 fixture tolerance1e-12 remains. Do not replace
the original native1e-6assertion with a relative or true-norm-only check.
Then use the same original8TRAINscenes32expressions/time-selected epoch2
checkpoint,source/data hashes,seed1999 and sameprefix/suffix/native controls.
Keep failure capture and compare masks only after matched controls pass.
Any failure is diagnostic implementation/inconclusive;no third arithmetic
revision,model restart,trainingadmission or all-family rejection follows.
