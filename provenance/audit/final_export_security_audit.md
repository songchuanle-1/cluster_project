# Final independent export audit

**PASS** for the audited precommit working tree and all 29 current branch refs. No actual credentials, weight artifacts or files above 100 MiB were found.

- Current payload: 24,222 files; all 24,222 source/record files scanned, including fallback decoding for eight extracted text records.
- Selected-ref history: 237 commits, 1,345 unique blobs, 1,317 decodable text blobs scanned; zero secret-pattern hits and zero blobs above 100 MiB.
- Integrated baseline `5413102`: all 2,954 source/config files match byte-for-byte. The uncommitted main payload is covered by the filesystem scan.
- All 27 original archived HEADs match their source identities. All 37 local working files match archive/local-working byte-for-byte; eight already had identical content in the committed base, leaving 29 content-diff paths.
- Root support source/config copies match: configs 23, framework 28, scripts 1,071, pipeline 4,394 and retained checkpoint YAML configs 124.
- Vendored canonical tooling matches all 53 selected files, excluding caches and task backups.
- One lexical candidate at `project_support/scripts/test_bounded_collation_process_20260921.py:68` is a test placeholder injected through an environment mock. No value is disclosed.
- Three Git mode-120000 link targets match the baseline exactly; Windows currently represents them as target text files.

DEST3D's 49 local source/license/readme files were scanned with zero findings and match the flattened staged copies byte-for-byte. Subsequent portable helper code changes receive a final code-delta check. The former gitlink does not establish the identity of the local DEST3D payload; migration provenance records that uncertainty.

This report records the audited precommit content and refs. Subsequent content changes must be checked against the recorded manifest before push. Audit cache files are not export inputs.

Both updated portable helper sources pass secret-pattern scanning and AST parsing. The stage verifier matches its audited source. The stage materializer still requires the audited 7,148-byte source copy, SHA-256 `789256ba6c2269067f7d4dbe8ccea4eb638632f98eb568c02d9de8ec74a9dd64`; matching that copy completes the helper delta confirmation.
