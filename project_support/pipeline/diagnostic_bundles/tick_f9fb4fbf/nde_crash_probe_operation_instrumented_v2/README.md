# Actual instrumented_v2 interface, unbound software only

Read nde_crash_probe_prepare/instrumented_v2/INTERFACE.json. Active bootstrap
must be exact4d3d8230 (sole DRAFT flag). Actual protocol8b2dd9 is owner-bound
ONE_BOUNDED_RESOURCE_PROCESS_CRASH_LOCALIZATION, max_attempts1/resources/candidate/
minimum_remaining1020. No invented fault_localization_only field is required
from that protocol. Review requires actualowner, passed=true, bootstrap_sha256
and fault_localization_only=true, exactly as bootstrap interface states.

Fresh native manifest view MUST add crash_probe_bootstrap.py AND
independent_probe_review.json before template hash -> lease -> binding -> request.
Original14 diagnostic entries and bytes remain unchanged. Root must bind view
through fresh prepare/stage; never append after binding. Preregistration protocol
may be separately x-staged as crash_probe_protocol.json and request hash-bound.
Old frozen native and both earlier unbound operation preparations stay intact.

Use render_bound_operation.py --bind-software --bootstrap <actual active4d file>
--preregistration <actual crash_probe_protocol.json> --review <actual passed review>
--output <absent sibling path>. Output remains release-absent pending operation
independent review. Then root may create exact operation_release only after
actual review. No ordinary adapter.run and no TRAIN2 are invoked. Original
priorfailed guard/1020/20k/max1/overlay/3locks/project lock remain unchanged.
The explicit operation is diagnostic only, never admission/comparable latency.
No SSH/GPU or actual diagnostic was executed by this author.
