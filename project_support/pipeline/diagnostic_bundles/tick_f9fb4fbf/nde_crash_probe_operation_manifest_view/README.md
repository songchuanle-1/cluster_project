# Manifest-view crash probe software, unbound and default denied

Supersedes only the additional-file staging contract of the preserved unbound
nde_crash_probe_operation package. No SSH/GPU or file staging was executed.
Actual bootstrap/prereg/review hashes remain NULL and release remains absent.

Root must first create and independently review a fresh native manifest view
that preserves the original14 diagnostic-file entries and all original worker,
runtime and model bytes, and adds the separately active bootstrap plus its
independent review hash entries. Both bootstrap and review are required by the
actual bootstrap validate_request contract. Bind the new view through the
normal fresh prepare/stage chain; old manifest/lease and old package stay intact.

The remote extension accepts preinstalled extra assets only when current fresh
manifest entries and actual hashes agree. Missing extra files use x-create,
then bootstrap+review manifest enrollment and full original native_verify must
pass. New root/request/started/completed journal uniqueness remains strict;
existing requests never cause launch/retry. Current guard1020, priorfailure,
project lock, original20k/max1/overlay/3locks remain unchanged. No adapter.run.

Use render_bound_operation.py with --bind-software and actual --bootstrap,
--preregistration, --review, --output to produce another software-only bound
packet. Actual independent review must precede byte-exact operation_release.
All results are non-admitting fault localization; instrumented latency is not
comparable. Stdout/stderr collection remains capped separately by root.
