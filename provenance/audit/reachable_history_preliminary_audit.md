# Reachable history preliminary audit

All refs and all 27 registered worktree HEADs were enumerated: 241 commits, 1,339 unique blobs. Every blob was read and classified; 1,311 decodable text blobs were scanned and 28 non-text blobs were excluded from pattern scanning.

No credential-pattern candidates were found. No blob exceeds 20 MiB or 100 MiB. This supports constructing a history-preserving staged export; it is not final upload approval. The staged tree and selected push refs still require an independent audit.

No server access, credential-account file reads, Git mutations, or network actions were performed.
