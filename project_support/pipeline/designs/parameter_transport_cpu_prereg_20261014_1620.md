# Parameter-Gradient Instrument CPU Validation

This event tick resumes the three existing scalar validation IDs. No new core,
admission, model package, scientific threshold, optimizer or GPU job is created.

Before executing, freeze the existing `parameter_transport` function from
`bps_task_2bbb4e0b9a814185a795b2ea2178483f/parameter_transport.py`.
Extract its function AST only; never execute its GPU adapter or source imports.

Run on server4 CPU, float32, one CPU thread, with CUDA hidden. Each of two
fixtures is repeated twice using the same unchanged function:

1. Identity Jacobian: two trainable coordinates, one intentionally unused
   parameter tensor, semantic gradient [1,2], task gradient [-1,1].
2. Anisotropic Jacobian diag(3,1): same output vectors. Query-space dot is +1
   but parameter-space dot is -7. Thus an output-space direction alignment
   cannot be promoted to parameter-space alignment without the actual Jacobian.

The fixture criterion is an explicitly synthetic quadratic, not the original
semantic loss. Independently calculate each masked VJP, norm, task dot and
unused-tensor count using matrix algebra. Compare six instrument conditions,
native-style identity, exact repeats, seven requests per forward, and absent
parameter `.grad`. Include a deliberately wrong identity-Jacobian readout that
must be distinguished by the anisotropic fixture.

The first four native groups and epoch4 manifest of the earlier preregistration
remain frozen and UNEXECUTED. These CPU fixtures neither measure their
parameter gradients nor resolve MAIN/REL/fractional source hypotheses,
full-forward repeat failures, finite-difference failures, task harm or efficacy.
After method validation, the remaining work is explicitly adapting and staging
that frozen native adapter for server4 before an authorized idle-slot test.
Missing deployment is executable preparation, not a fabricated GPU-only block.
