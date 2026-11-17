# CRE one-time isolated source save (root-only, not executed)

This single-purpose helper binds only M217-CRE / `hierarchy-cross-root-directed-edge-broadcast`, its eight `_cre` model files (including `root_exchange.py`) and the original `_cre.yaml`. It uses exactly `C:/Program Files (x86)/Git/cmd/git.exe`. There is no enable-copy or second execution-capability flag: default invocation performs no operation, while explicit `--execute-root` still requires the actual six-field foreground owner, original deadline/context, standing project authorization, python `-B`, `GIT_OPTIONAL_LOCKS=0`, frozen actual source/review SHA arguments and the canonical project lock.

Root may execute only after the real source bundle and independent review freeze:

```
$env:GIT_OPTIONAL_LOCKS='0'
$env:PYTHONDONTWRITEBYTECODE='1'
python -B -X utf8 prepare_isolated_cre_version.py --execute-root --source-preparation-sha256 <actual-frozen-prep-sha> --independent-review-sha256 <actual-source-peer-sha>
```

The source path is fixed to this tick's `new_candidate_prepare`; the peer path is fixed to `new_candidate_source_independent_review.json`. Missing or invented hashes do not pass. The helper requires the peer's exact candidate/experiment/null-version status, `anchors.preparation` and `source_files_exact9` to match the actual frozen preparation/manifest. It copies only the nine exact source/config paths, checks both staged and committed Git blob hashes, ordinary single-child commit parent, exact9A diff and clean isolated HEAD/index/worktree. Source metadata, model bytes, native protocol, scientific thresholds and public runtime stay untouched.

The destination is exactly `pipeline/isolated_versions/cre_65785aaf`, parent `026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563`. Root primary HEAD/index/protected28 status+bytes and all fourteen lifecycle ledgers, plus current work/memory/policy/mode/SERVERS bytes, must remain identical. The actual original BEC job remains running and no queue, admission, native/remote execution or GPU operation occurs. Only a new isolated worktree registration, its exact nine files/index and ordinary candidate-only local Git commit may be written. Durable private before/intent records precede the worktree mutation. Existing destination, intent, before/result record or empty-hooks directory refuses replay; partial failures require exact read-only reconciliation, without rollback/reset/clean/stash/force/deletion.

Compatibility is **only the current026c parent**. Existing AEF56b2 is a separate sibling on026c and is never borrowed as parent. This CRE source is not native-tested and no later fast-forward is assumed after AEF or any other main advancement. If primary moves first, preserve this source proof and freshly package the unchanged CRE nine files on the then-current compatible parent, then test that exact version. That is version compatibility, not a model revision/tuning or permission to relabel old raw results. Original frozen null-code/source declarations are never rewritten by this helper.

The author performed only stdlib compile/AST inspection and three extracted actual-main default/missing-hash checks with an execute stub. No helper execute, Git, SSH, GPU, root guard, model import or shared mutation occurred. These software checks are not source preservation success, native/FP32/gradient/resource PASS or permission beyond root's existing scope.
