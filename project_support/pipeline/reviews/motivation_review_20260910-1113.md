# Motivation Review - cluster_project
2026-09-10 11:13 Asia/Shanghai.

## 1. Goal
Authoritative complete goal.json is reproduced in goal_snapshot_20260910-1113.json
alongside this review, byte-for-byte; constraint/banned checks below refer to every
entry, not historical prose. Target .5100; M95 .5020; gap .0080; Phase1 NOT YET.
No active reservation in goal constraints or last10 decision originals.
Question075552 explicitly says no global hold; admission portion was resolved.

## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|------------|--------|----------|-----|
| Multiscale context helps | Supported within original comparisons | A1 .5012 vs .4894 | Generalization across seeds |
| Explicit routing helps | Rejected | A3 .4468 vs shuffle .4941 | Do not reopen |
| Recurrent object-mask context improves champion | Unsupported | M175 .49675/M176 .49356/M177 .49628/M178 .49304 | Recurrence versus retrieval confounded |
| Terminal-only context avoids feedback interference | Open | M184-M186 early training, M187/M188 waiting | No mature result yet |
| CSORT robustness | Weak | M95 .5020; controls .490-.494 | No causal/robustness claim |

## 3. Experiment Assessment
Full local analysis inventory and ledger assessment are generated in
reports/research_inventory_20260910-1113.json and
reports/research_assessment_20260910-1113.md. All221 analysis documents are read,
hash recorded, and their conclusion sections retained; the ledger is parsed
without overwriting scores. Duplicate/old analyses are not independent runs.
The following load-bearing results use latest exact paired analyses.

| Experiment | mIoU | Acc50 | spmIOU | Motivation contribution |
|------------|------|-------|--------|-------------------------|
| M95 | .5020 | .557 | .465 | Context platform; single-seed comparison only |
| M169 | .5000 | .554 | .462 | Fine-branch clue; compromised patience |
| M175 | .49675262 | .546 | .461 | Flow recurrence below champion, >10G |
| M176 | .49356174 | .541 | .456 | Sibling recurrence below champion, >10G |
| M177 | .49627879 | .548 | .459 | Bottleneck recurrence below champion, >10G |
| M178 | .49304044 | .546 | .455 | Top-down recurrence below champion, >10G |

All four recent terminal parents have ten real post-best validations. Their score
branches stay closed: no coefficients, temperatures, surrogate-gradient changes,
or alternative score variants. The proposed intervention removes feedback edges
while preserving each formula. It tests recurrence necessity, not a claim that
failed scores are promising. No automatic resume or repeated numerical trial.

## 4. Gap Analysis
Q1: Existing MQ parents entangle hierarchy retrieval with recursive modification
of future masks. M169 provides limited support for coherent hierarchy context;
M175-M178 do not establish a superior recurrent mechanism. The revised readout
graph is untested for sibling, bottleneck and top-down retrieval.
The primary risk is that all retrieval variants simply fail; early M184-M186
scores cannot justify a performance forecast or a combination with HQI.
Waiting2 versus configured capacity4 requires reserve5, deficit3.

The mechanism hypothesis is derived from the local graph and results, not an
external literature claim. Attempted primary-source lookup returned no usable
content this tick, so no unverified paper is used as supporting evidence.
No denoising masks, loss weights, new data or schedule are introduced.

## 5. Design Rationale
Q2: M189 copies M177 and removes intermediate context calls; M190 does the same
to M178; M191 to M176. Keep one fixed final readout because it cannot alter later
context-selection masks. No index/depth sweep, all six decoder outputs retained.
M190 also receives the already-established per-scene padding correctness fix.
Q3: Success above .5020 supports further confirmation, not a causal claim across
hardware/runs; reaching .5100 triggers Phase0/ablation transition. Failure closes
each terminal version with no numerical rescue. Improvements<.002 and plateau
follow existing branch-stop constraints; patience10 unchanged.
M175 flow terminal extension is deferred: it adds a contrastive signed context
path with weaker efficiency and interpretability, unnecessary for reserve3.

## 6. Next Batch
See designs/exp_design_20260910-1113.md. M189/M190/M191 may enter the queue only
after physically independent packages, byte-identical parent numerical configs,
CUDA oracles/gradients/boundary checks, matched measured<=10G admission, safe sync
to both allowed servers, and logged locked enqueue. No held placeholders count.
