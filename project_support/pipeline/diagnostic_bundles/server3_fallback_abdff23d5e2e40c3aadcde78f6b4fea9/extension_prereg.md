# Runtime Extension Preparation

The first CPU model preparation failed before CUDA initialization because the
frozen Git bundle does not contain the ignored pointgroup_ops_ext binary.
Keep native_capture_server3_prepare_attempt.json unchanged as negative evidence.
The target already has CUDA11.3, gcc7 and torch1.12+cu113. Compile the unchanged
exact-commit extension sources in the new isolated checkout only, with the
original compile flags and RTX3090 architecture8.6. Compare every source hash
before/after. No package installation, shared environment edit, driver change,
CUDA allocation or model calculation change. A successful build is environment
readiness only, not native execution, model admission or trained efficacy.

The first build wrapper failed before compilation because Ninja is absent.
Keep its source and attempt unchanged. Use setuptools BuildExtension with
use_ninja=False and the same CUDAExtension sources/macros/flags, matching the
original setup.py construction. This reuses existing tools, with no package
installation and no change to model/source calculations.
