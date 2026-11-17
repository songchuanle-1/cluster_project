# Physical-target size-normalized seed coverage

On server-6 GPU7, replay unchanged M95 checkpoint and the same frozen
32-scene/128-expression TRAIN population at transform seed 1999. For
each physical target instance, count its superpoints in the native
criterion label axis and valid FPS positions selected from it. Also
count all valid scene superpoints and FPS seeds, and report the
target-seed fraction normalized to the target's superpoint fraction.
Verify the 128 input fingerprints and selected-seed indices against
the previous native target-seed census. Within mixed-outcome scenes
compare mean normalized coverage of deployed failures and successes.
Zero-target/zero-FPS denominators must be explicit. This cannot
establish a new selector or training benefit.
