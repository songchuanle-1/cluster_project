# Minimal-pair switch audit correction

The preregistered minimal-pair checker counted a class-token insertion
as a context switch without checking whether the class token also appeared
elsewhere in the shorter expression. Its sole reported pair, scene0035_00
ann21/31, has `desk` in both utterances and the native support probe found
identical context values on all 509 superpoints. This is a diagnostic bug,
not a positive mechanism result.

Correct the checker to require exclusive class-key membership between
the two utterances for the candidate physical instance. Rerun the
unchanged frozen 64-scene cohort to a new output path; preserve the
original report with its hash as superseded evidence. Count only actual
context-label switches, and retain one-token insertion pairs separately.
No admission or training follows.
