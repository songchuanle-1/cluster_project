# Fixture disclosure before execution

- Two fixed40recipient single-leaf geometries,not a search:seed1999 Gaussian coordinates;and the first40 integer points from[-2,2]^3 ordered by(squared radius,x,y,z),to exercise cutoff ties.
- Each uses deterministic seed1999 float64 C256/H8 probe features;they are not trained/captured point features. Also evaluate float32 on the same inputs,without selecting probe scale or changing model precision.
- Every preregistered transform is evaluated on both geometries. Exact source replay and singleton/zero controls are required. Non-isometric x-compression is the disclosed sensitivity control only,not an isometry failure.
- Native PointCloudPartitioner uses FurthestPointSampling.apply,a CUDA extension;CPU cannot silently replace it. Do not label a CPU FPS surrogate as native membership. First perform these cheapest operator tests;actual TRAIN geometry preparation may proceed on CPU,while exact native fine-membership tests require a genuinely free authorized card.
- If a representation-sensitive cutoff counterexample is observed,save it and independently confirm the distance/ranking/fallback explanation. A real source counterexample is not a claim of trained-mask harm or permission to alter M203.
