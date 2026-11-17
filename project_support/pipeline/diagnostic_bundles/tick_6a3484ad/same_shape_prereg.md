# Remove The GEMM-Shape Confound Without Changing The Production Mean

The naturalbatch2 test found729vs1185validpoints:4rows have456masked
positions whose native feature magnitudes reach8.16. Native reconstruction
controls0, cropped-valid gather changes.057to.126, but nonpadded rows also
show1.24e-5roundoff from different GEMM shapes. Preserve this limitation.

Run ONE more samefrozen naturalbatch2 forward and all original controls.
Then retain EXACT(B,N,C),tokens,IDs,fine messages,weights,validpointfeatures
and masks. Change ONLY features at already-masked positions in2predeclared
ways:zero;thatrow's valid-feature mean. Invoke unchanged production gather,
message_norm and fixed-prefix suffix. This is an input-invariance diagnostic,
NOT a replacement mean operator or deployable candidate.

Require valid features bitwise unchanged, all-zero-scale null<=1e-6 and
nonpadded-row output null<=1e-6. Native identity reconstruction<=1e-6.
Report valid message/mask logit effects, not multi-scenepointIoU or efficacy.
If same-shape masked-only changes still affect valid masks, attribution to
masked context is supported without the cropping GEMM-shape confound.
No model/baseline fix, training, norm-helper revision, VAL or admission.
