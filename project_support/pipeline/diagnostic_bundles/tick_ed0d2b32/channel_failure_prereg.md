# Preserve And Measure The Actual Null-Control Failure

Original native_channel_null_result: failed strict1e-6 at the third fixed
readout after10source forwards, saved-prefix identity0. The runner did not
persist partial per-readout magnitudes before its assertion; those values are
UNKNOWN, not0. Preserve that file, code, manifest and failure permanently.

One diagnostic-only follow-up on exactly expression0/last-valid point (the
identified original failing readout), with the SAME frozen prefix, weights,
directions, norms, flags and thresholds. No other cases, seeds, retries or new
model. Save original full-sized baseline plus three conditions and the exact
strict-null gate result, even if it fails. Do not convert a successful recording
into a scientific PASS or overwrite the original failure.

Also record centered global-weight residual after float32 direction casting,
the native actual mean shift, and its difference from exact single-point-change/N.
These distinguish rounding evidence from a source-graph error; no assertion
about cause is made before observing them. Unique kernel attribution remains
unestablished. Partial numerical control is not admission or trained harm.
