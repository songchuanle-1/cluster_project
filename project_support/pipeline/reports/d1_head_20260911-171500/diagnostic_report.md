# D1 Head Ownership And Synthetic Coupling Audit

Completed 2026-09-11T17:23:43.034244 Asia/Shanghai. This is a CPU-only
implementation audit. It performed no real-data forward pass, no training, no
checkpoint write, and no GPU allocation.

## Contract

The baseline checkpoint resolves all six decoder-layer `indi_embedding`
attributes to one module object:

    unique module objects       = 1
    unique parameter objects    = 6
    total parameter references  = 36
    state head keys             = 36
    duplicate checkpoint groups = 6
    all duplicate values equal  = True

The M95 checkpoint resolves to six independent module objects:

    unique module objects       = 6
    unique parameter objects    = 36
    total parameter references  = 36
    state head keys             = 36
    duplicate checkpoint groups = 0

Thus the earlier source-text difference is confirmed at the object, storage,
state-dict, and checkpoint levels. The baseline truly ties its layer heads; M95
does not.

## Synthetic Gradient Check

For tied heads, the exact chain-rule decomposition is:

    dm_1/dt = local_margin_velocity + cross_layer_coupling
            = 178.2748994052913 + 178.2748994052913
            = 356.5497988105826

The centered finite-difference value is 356.5497997229938, error
9.124111670644197e-7. For the independent control, the cross-layer term is
exactly zero and the finite-difference error is 1.1405705890865647e-7.
The minimum absolute ReLU preactivation is 2.4493639190169967, so no ReLU
crossing contaminated this synthetic check.

The M95 synthetic tied control gives 60.275037792112315 versus finite difference
60.27503783002374, error 3.7911426886694244e-8. Its independent control gives
30.137518896056157 and is consistent with finite difference to 4.8e-9.

## Interpretation

This confirms an implementation difference, not an error cause. A tied head has
a standard cross-layer gradient path; independent heads do not. The real losses,
real inputs, optimizer state, dropout, augmentation, and full decoder graph
remain outside the audit. Parameter tying and the chain rule are not novel.

The result also does not make a shared head an admissible replacement. The
baseline already has tied heads and is below M95 in this frozen diagnostic
sample. The next research step cannot be "adopt sharing" or any successor
selector/readback variant.

## Decision

Record the exact ownership contract and keep the shared-head question as a
diagnostic fact. Do not admit a mechanism and do not enqueue training. Any real
head-input capture must wait for a separately justified protocol and free
resource allocation. The next admissible work remains the search for one
evidence-selected mechanism with a non-standard forward/loss graph, explicit
gradient derivation, primary-source comparison, matched control, and
preregistered rejection condition.

## Provenance

- Initial protocol: `cf7c884848fdd11f46101d80f0db239a8a05d6cc9f0997231c936b0bae76c8d5`
- Retry protocol: `12591b51b6651c056ab2e70384259ed8a4e4350de461addbaee725a1617f361e`
- Baseline result: `56bad53097707612df8b73024b71baaf0b36a102b7e066bffce6ee9cddf69a98`
- M95 result: `5b3bc1baabcd475692a0074d3432c90528eb8297d42d6e159c7bf4ee2c080bfb`
- Worker: `0b60fc7611f549c13f8e8f5998cb0a37a969e2799e10016b37a6c40f7ce945e7`
- Runner: `e9fa204a06e9061fc84f313325fbb2ae1ad9dd062f3725f3fef07e77f4faae57`

The first two helper failures and the finite-difference sign repair are
preserved in `baseline_attempt1.log`, `m95_attempt1.log`, and
`execution_attempt1.json`.
