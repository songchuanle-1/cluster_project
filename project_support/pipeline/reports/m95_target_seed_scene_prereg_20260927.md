# Scene-paired target-seed count screen

Freeze `m95_target_seed_direction_native_20260927.json`. Within each
of the 32 scenes, compare the average physical target-instance FPS seed
count between deployed failures (IoU <= 0.5) and successes (> 0.5),
only where both outcomes exist. Report scenes, count differences, ties
and zero-seed denominators. This is descriptive and confounded by
target instance size; a subsequent native size-normalized audit would
be required to establish a genuine coverage gap. No selector redesign,
new loss, admission or training from this count.
