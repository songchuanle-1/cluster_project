# LFT FF verifier maintenance note — next reviewed tool copy only

Observed at 2026-10-31T12:52:53.418245+00:00. Current helper: `lft_admission_active/fast_forward_tested_lft.py:58`, SHA 8f794828a3c96244abb1e6e9066c55a10d9356809c78d92f2bba28f752e297d1. This note does not modify it, replay the FF, signal a process or authorize any new entry.

The source-preservation check currently invokes the full `git ls-files --stage -z` read once per prior-index key:

```python
assert all(index_entries().get(k) == v for k, v in prior_index.items())
```

With 2,947 prior entries, success evaluates 2,947 full subprocess/index reads and reconstructs a 2,956-entry dictionary each time. It is finite repeated verification, not by itself evidence of a stalled merge. No completion/remaining-time estimate is justified from a single process snapshot; the existing intent/command/result remains the authority. At 12:52:17Z a local CIM snapshot limited to python.exe/git.exe showed no matching helper or ls-files command; that alone is not proof of completion.

In the next separately reviewed tool copy, capture the single post-FF snapshot once:

```python
after_index = index_entries()
assert all(after_index.get(k) == v for k, v in prior_index.items())
```

Under the intended protected fixed-index comparison this preserves the same key/value requirement while reducing full index reads from 2,947 to one. Keep prior tree, all original index entries, exact 9A/source hashes, user28/status/empty staging, WFC working-source and lifecycle/owner guards unchanged. Do not edit any frozen draft, active helper, original intent/result or baseline in place. This is a tool performance correction, with no model/protocol/scientific gate change and no reason to repeat an already successful FF.
