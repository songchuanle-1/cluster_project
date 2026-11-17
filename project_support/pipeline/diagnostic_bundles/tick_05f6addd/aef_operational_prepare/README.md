# AEF operational preparation; native execution NOT_RUN

This package ports the reviewed BFC adapter/RPC driver to the existing M216-AEF source `56b2a96dc48cc8a88f0f7105527ef448113b1060`, with exact current runtime parent `026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563`. Native files remain in the sibling `aef_native_prepare` folder and are verified through its exact preparation/template hashes and full native file map. This package does not copy or change that worker or any model.

Only physical server4 GPU0 is supported; it becomes logical CUDA0 inside the existing worker. GPU1 is rejected before transport by direct `probe`/`prepare`, by current-policy validation, and by remote capability validation. Current explicit resource authorization is `server4_gpu0_only_20261026.json` (94075ebd...). Live SERVERS must still allow exactly `[0]`, and fresh context/owner, original deadline, assets, pinned hostname/key, exact expected runtime026c, local registered-idle state, actual idle GPU0 UUID and the three original locks remain mandatory. The 1020-second minimum run window and original uncertain-request/no-replay behavior remain unchanged. An existing BEC task is never stopped or evicted.

The release template is only a static code/version catalog. Root may materialize its exact bytes as `adapter_release.json` only after independent review and external candidate anchors. There is no production release, active manifest, lease, binding, execution directory or native result in this prepared package. Static provenance token/time is historical, not execution authority. Every real `prepare` needs a new actual root owner/context and a currently idle authorized GPU0. Old bindings are read-only; status/reconcile never renew an old lease or permit re-execution.

The adapter creates no standard native smoke, PASS, decision, admission receipt or queue entry. `execution_completed` in a future raw result is not full semantic review, paired-input proof or admission. Future root must independently review the four real raw results, original two TRAIN loss/backward/optimizer and AEF-specific path/gradient controls, real paired inputs/common initialization, original resource protocol/full unsupported lists and all remaining unknowns before separate standard summaries/admission. No BEC R1 branch, BEC five-module/twelve-block control, or old BEC/BFC result signs AEF.

Future root CLI order (do not execute against the busy current card):

```
python -B -X utf8 adapter.py probe --gpu 0
python -B -X utf8 adapter.py prepare --gpu 0
python -B -X utf8 adapter.py stage
python -B -X utf8 adapter.py run --mode smoke --target champion
python -B -X utf8 adapter.py run --mode smoke --target candidate
python -B -X utf8 adapter.py run --mode resources --target champion
python -B -X utf8 adapter.py run --mode resources --target candidate
python -B -X utf8 adapter.py status
python -B -X utf8 adapter.py reconcile --request-id <original-id>
```

`run_pair`/`pair` also use these original four arms, but any busy refusal, failed/uncertain request or timeout must be reconciled against its original request ID; it is never blindly rerun. Each fresh tick has exactly one local `aef_execution` directory and stage `aef_<token8>_gpu0`. There is no fallback to another card. A previous tick can be inspected via `--execution-dir`, under current actual read-only authorization, without mutating the previous lease.

Only a small disposable software metadata/AST check is prepared here; it is not a rerun of the old61/98 suites, native/autograd/FP32 tests, or hardware observation. Its isolated temporary candidate/busy fixtures do not impersonate a root environment against the actual project. No SSH, Git, GPU, Torch, scheduling or shared mutation is performed while preparing or testing this package.
