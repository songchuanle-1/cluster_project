# cluster_project GitHub migration input audit

- Audit date: 2026-11-17. Local main: `0747f6acec1c61018ec99acf2efa5329c9b3523c`.
- Registered worktrees: 27 (main plus 26 isolated checkouts).
- Reachable history: 241 commits, 1339 unique blobs, 157,574,289 blob bytes; 1311 text blobs scanned.
- History blobs above 20 MiB: 0; above 100 MiB: 0.
- Current bounded text scan: 90,254 file paths, 12,626 unique text contents.
- High confidence credential-pattern hits: current 0, history 0.
- Candidate literal findings: current 1, history 0; only paths/types/line numbers are recorded.
- Current Git remotes: 0; embedded credential values were never emitted.

| Top-level path | Files | Bytes | Source/config files | Source/config bytes |
|---|---:|---:|---:|---:|
| `.gitignore` | 1 | 15 | 0 | 0 |
| `.pipeline.lock` | 1 | 0 | 0 | 0 |
| `Checkpoints` | 283 | 1,104,625,410 | 124 | 323,583 |
| `Cluster` | 4,275 | 626,049,793 | 3,000 | 38,540,364 |
| `SERVERS.yaml` | 1 | 3,976 | 1 | 3,976 |
| `configs` | 23 | 60,148 | 23 | 60,148 |
| `docs` | 21 | 28,559,479 | 0 | 0 |
| `framework` | 54 | 725,209 | 28 | 378,000 |
| `pipeline` | 97,415 | 13,921,775,766 | 77,607 | 991,091,135 |
| `scripts` | 1,527 | 10,671,770 | 1,071 | 6,205,086 |

Isolated source/config copies occupy 944,488,504 logical bytes across 73,213 paths, but only 1,660 unique contents (25,372,075 bytes).

The recommended export keeps one integrated main tree and separate archive refs for local and isolated versions. Git shares duplicate objects across these refs. Root-level operational scripts, framework/config overlays and pipeline source must be included independently; they are outside the Cluster repository and are not fully covered by its branches.

The JSON records all worktree HEADs, dirty/untracked paths, source divergence, root mirrors, large-file findings and credential-pattern candidates. Worktree dirty changes must be preserved before an archive ref can represent the full checkout.

Current diagnostic/checkpoint JSON, text above 2 MiB, caches and non-text binaries were excluded from current-content scanning. All reachable history blobs were classified and every decodable text blob was scanned. Neither server account references nor remote servers were accessed.

**This is not a final upload approval. The exact staged export and selected push refs need an independent scan.**

One current candidate requires contextual review: `scripts/test_bounded_collation_process_20260921.py:68` (`secret_or_token_literal`). No value is recorded.

Retain the 124 small YAML experiment configurations under `Checkpoints` when excluding runtime weights; the JSON lists every config path.
