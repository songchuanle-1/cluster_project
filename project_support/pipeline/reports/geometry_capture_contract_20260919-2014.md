# Versioned Geometry Nuisance Capture

## Scope

Continuation of the seven due candidates' shared diagnostic dependency.
This is a CPU-tested adapter for observed criterion inputs, not a new mechanism,
native execution, completed objectness control, or seven candidate validations.
No frozen producer, model package, configuration or queue is changed.

## Contract

`criterion_geometry_nuisance_v1` consumes criterion input4 instance labels,
input7 FPS indices, input8 concatenated transformed superpoint coordinates,
input9 expanded expression offsets, and pred.sample_inds. Coordinates are
sliced with offsets before composing local FPS[sample_inds]. Native source
inspection confirms network.py expands coordinates and offsets per expression
and calls criterion with these positions; loss.py slices the same offsets.

Each row binds capture/scene/occurrence/dataset/annotation/expression identity,
original superpoint IDs, sampled-point inverse, native-input identity,
producer/config/model/checkpoint hashes and a fingerprint of the observed
criterion geometry inputs. The payload has its own hash. Validation checks
the expected source binding, reconstructs rows, and recomputes geometry.
Mutable input lists are deep-copied; serialized payloads round-trip.

Physical instance labels come from EndpointDataset.semantic_binding, checked
against exact criterion labels. Native majority voting uses sentinel199 for
unresolved superpoints. Such support maps to physical -1 and is excluded,
whereas a physically bound real instance199 is retained. Raw native labels
remain in the artifact; the physical map is never inferred from label199 alone.

The geometry is squared distance from the instance centroid divided by mean
squared instance radius, then minimum cost over that object's selected seeds.
It remains annotation-assisted and conditionally target-blind on a fixed
support/label/query axis. It is not objectness, quality, or a probability.
All-background input fails closed; degenerate/uncovered objects remain missing.
Evaluation retains requested, valid, missing and tied denominators plus raw
minimum pairwise gaps. Near ties are flagged at rel_tol1e-9/abs_tol1e-12 as a
numerical diagnostic only, never as a tunable performance threshold.

## Tests And Limitations

Tests cover multi-expression coordinate slicing, local FPS composition,
target/text swaps, source/physical identity changes, tampered payloads and
rehashed stale costs, native sentinel disambiguation, missing/zero-radius
support, exact and near ties, query-selection sensitivity, NumPy axes,
deep-copy isolation and JSON serialization.

An initial exact-tie fixture used translated noninteger centroids and differed
by floating-point roundoff. It was replaced with exactly representable symmetric
coordinates; a separate near-tie test retains the floating-point distinction.
Final executed test counts and hashes are in the companion JSON report.

The observation hash identifies native dtype/shape/bytes when supplied actual
tensors; reconstruction from serialized lists cannot independently attest
those native bytes. Hashes are provenance checks, not proof of truthful input.
No GPU hook or runtime integration was executed. Next implement a separately
versioned runtime wrapper/source manifest without editing the frozen seven-file
producer, then validate actual tensor layout and physical bindings on GPU7
when capacity permits. Independent objectness remains unresolved. The geometry
diagnostic cannot satisfy that gate or promote failure-selected pairs to a
population effect. Native tie/missingness frequencies are unknown.
