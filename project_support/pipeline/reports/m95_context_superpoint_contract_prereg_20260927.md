# Native context-superpoint target contract

Stable ID `m95-sample-context-support`, diagnosis only. Freeze the first
64 lexicographically sorted distinct ScanRefer TRAIN scenes and **all**
annotations in those scenes. The native dataset writes target point mask 1,
exact class-key context point mask 0.5, and other points 0, then averages by
superpoint; binary GT superpoint target is target point fraction >0.5.
Test whether the soft context target could contradict this target/negative
partition on physical input; compare each annotation's target-bearing rows to
same-scene non-target rows and report unique scene/instance denominators
separately from repeated annotation-superpoint counts.

Primary screen: count superpoints with native binary target GT=1 but
soft context mask <0.5, and binary GT=0 but soft context mask >=0.5.
Separately count fractional support 0<mask<1 and target minority rows;
these are *not* equivalent to contradictions. The native training loss
may override matched seed targets and applies a factor 0.5, so this input
check alone cannot establish a loss defect. Fail-closed on noncontiguous
superpoint IDs, unknown class mapping, or changed data schema. This is a
prediction-blind CPU diagnostic; no new model, GPU, admission or training.
