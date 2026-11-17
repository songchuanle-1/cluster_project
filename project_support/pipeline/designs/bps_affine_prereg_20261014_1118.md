# BPS Native Affine Geometry Diagnostic

- Stable candidate: m95-native-between-pair-support; supplemental robustness
  diagnosis only. M201-BPS continues unchanged. No new training variant.
- Question: does the native TRAIN jitter/flip/rotation matrix change the
  Euclidean normalized reference-pair support fields or pair availability,
  although the existing 52 tests only cover similarity transformations?
- Source: framework/dataset/scannetv2.py SHA256
  2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d.
  Native transform_train uses data_aug(xyz, True, True, True) for
  coords_float. Elastic changes voxel coordinates separately, so it is not
  the variable in this test.
- Freeze before outcomes: use every unique scene/ann_id in the prior
  bps_native_current_c9de23ffb1804f1eaa81cf54b94b9d6a.json readouts.
  Sorted scene order; seed1999; one exact native data_aug matrix per scene.
  Load original TRAIN raw points/labels, native get_sp_label/get_ref_mask
  methods, and unchanged committed BPS prepare. No sampled new outcomes.
- Matched branches: original coordinates; native matrix; the same matrix's
  polar orthogonal factor times its RMS singular value (similarity control).
  The reference catalog, physical IDs, SP memberships and GT masks do not
  change. Check identity re-execution and input restoration.
- Primary uses native float32 coordinates. An explicitly auxiliary float64
  coordinate branch separates rounding from metric dependence; this is not
  a change to model precision or a new native-forward PASS.
- Report denominators, inactive cases, source/raw-file hashes, matrices,
  matched/added/removed physical-pair columns, absolute field drift and
  GT expectation drift. Keep the existing absolute1e-6 check for controls.
  Do not turn a failed control into PASS by changing tolerance.
- Prediction: nonconformal native matrices can change reference projection
  fields or availability; a conformal control should not change geometry
  apart from measured roundoff. Zero effects disconfirm only this scoped
  geometry premise. No task-level effect-size gate.
- CPU-only on authorized server-6, two CPU threads, CUDA hidden for the
  diagnostic process only, hard600-second bound. Preserve training and
  foreign jobs; no optimizer, model forward, new dataset, seed sweep,
  package/config mutation or admission.
- A positive result is geometry sensitivity, not wrong labels, task harm,
  trained efficacy or a novel independent mechanism. Investigate exact
  frozen native augmented-input/task controls before any proposed repair.
