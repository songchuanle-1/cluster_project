# One bounded resource crash localization operation, unbound/default denied

No SSH/GPU/diagnostic executed. Actual bootstrap, preregistration and independent
review hashes are intentionally NULL; packet binding_complete=false. Default
launcher and renderer are NOP; operation_release.json is absent. The operation
uses the unchanged reviewed Adapter guard/binding/local idle/project lock/prior
failure no-further-run check and 1020-second launch margin. The original native
worker/acquire retains20k/freeGPU0/max1/overlay/all3 locks. Ordinary adapter.run
is never called or modified. Old stage/failed history remain untouched.

Root may render a new bound software copy using render_bound_operation.py
--bind-software --bootstrap <separately reviewed active bootstrap> --preregistration
<actual JSON> --review <actual JSON> --output <absent sibling directory>. Review
requires owner=current exact six fields, passed=true, bootstrap_sha256=actual
active bootstrap, fault_localization_only=true. Prereg requires same owner and
fault_localization_only=true. No original fourteen-file manifest, worker or
lease is modified: extras are written with x and bound by independent request
SHA256. Bootstrap must accept the separate hash extension contract; the observed
initial draft incorrectly required bootstrap/review in original manifest.

Only after actual interface review may root write byte-exact operation_release
from release_template and call --execute-root. Unique local/root intent and
remote request/startPID+start_ticks/stdout/stderr/completion prevent replay.
Any known/unknown attempt reconciles read-only; no cleanup/signals/restarts.
A failed diagnostic is preserved terminal, never reinterpreted as resource PASS.
Only original candidate/resources entry executes through the unchanged bootstrap
with -B -X faulthandler -u; diagnostic timing is never comparable or admission.
Stdout/stderr are recorded remotely and only hashes returned. Root can retrieve
bounded512KiB per file separately with full byte count/SHA; do not dump logs.
