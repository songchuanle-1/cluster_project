# Default-disabled current-owner rebind only

This is the reviewed e2e3 preparation546046/source1ca378/guard10d079 and independent
review910044 with exactly two literal assignments changed: OWNER6 to the new3d
owner and CURRENT_BASELINE to fresh5656. Every other source byte is identical after
reversing those two assignments, and the complete normalized AST is equal.
The NoTransport source is byte-identical. The old6file package remains untouched.
No old25/35/98 suite, helper module/main, Git, SSH, GPU, Torch or shared write ran.

PCE0e357 and all OP9a81/checker57752/peer98def/source026c/prereg/CPU/history refs stay
unchanged. The new baseline is current primary4e8/indexempty/28files/12ledgers/
141candidate digests. Currentroot token3d001030 has its original11:05:37Z deadline;
this is a new authorized owner, not an extension/replay of olde2e3 orfacc leases.

ENABLE_ROOT_EXECUTION=False remains the single disabled flag. After independent
rebind review, root may copy both .py files into same-tick sibling
bec_r1_anchor_execute and change only this flag False->True in the anchor file,
recording exactold/new SHA/diff. Explicit --execute-root is still required:
python -B -X utf8 <execute>/anchor_bec_r1_static.py --execute-root
python -B -X utf8 <execute>/check_bec_r1_current_guard.py --execute-root

Outputs move automatically to currenttick3d: once-intent/before/staticanchorresult/
NoTransportcurrentguard. All existing protected12 ledger/source28/index and other
140candidate rules, completeold9b history, R1nativeNone/NOTRUN/pending and only0
remain unchanged. Any partial intent/staticrelease/temp requires readonly
reconciliation; no overwrite/adoption/blindrerun. No source promotion or queue/
process/GPU operation is in these helpers. Root final memory/CTS aux audit is
separate and must follow anchor+guard while their protectedbaseline still matches.
