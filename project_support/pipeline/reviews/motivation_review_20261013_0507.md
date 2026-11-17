# Motivation Review - cluster_project

## 1. Goal
- Source: pipeline/goal.json; SHA256
  d7296cbb4cfc0742e92ccccc65a17b36513dcd8940c98c90e38801e79f14b21b.
- Task: diagnose specific ScanRefer referent errors and develop falsifiable
  lightweight structural mechanisms, not variants of pooling/selector/writeback.
- Target mIoU.5100; champion.5020; baseline.4894; gap.0080.
- All18constraints/11bans unchanged; original Phase1 seed1999/50epochs/70max_iters.
- Only server-6 GPU7/two slots; these native diagnostics ran CPU-only there.
- No additional labels/data/seeds, validation selection, admission relaxation,
  scheduler changes, other projects, new tasks, or background restoration.

## 2. Story Status
| Hypothesis | State | Evidence | Gap |
|---|---|---|---|
| Root mention-role mismatch exists | diagnosis retained | original admitted TMR evidence | one trial did not exceed champion |
| Stored nested relation spans are dropped | premise rejected | full TRAIN36665/562,60866nonrootObject nodes,0nonroot spans | parser completeness not tested |
| Spatial padding contaminates mask-loss boundary | direct contamination rejected | native8/32,16paddedexpressions,3132slots,gradient0/lossdelta0 | strict repeat failed; model/score path untested |

## 3. Experiment Assessment
| Experiment | mIoU | Relation to motivation | Interpretation |
|---|---|---|---|
| M95 champion | .5020 | established cluster context | remains champion |
| M200-TMR | .4952795207500458@13 | parsed target-to-reference role transfer | native early stop23/50; below champion, above rounded baseline |
- TMR best Acc@50.549/spmIOU.459 are rounded logger values, not exact metrics.
- PID absence alone was insufficient: exact native log,23 aligned validation
  records,patience10 and remote/local SHA match establish the terminal.
- No restart or tuning; previous launch/control failures and user dirty files kept.

## 4. Gap Analysis
- Nested relation premise concerns stored spans, not graph semantic completeness.
  Actual original nested/root-only/already-covered controls separate; no real
  nonroot stored spans means no factual positive cohort for a loss intervention.
- Spatial loss test uses actual native augmented getter/collation and original
  Criterion.get_layer_loss but deterministic decoder-shaped tensors and injected
  assignments. It is not a native full model/FPS/backward/resource test.
- Four pairs contain actual padding; broken filtering yields gradients between
  .000057160457799909636 and .00018248241394758224.
- V1 exact valid-gradient assertion and V2 exact trial-record assertion FAIL.
  V3 preserves all readouts: first-pair7.275957614183426e-12 appears also on an
  unchanged-input repeat; exact_repeat=false. No tolerance was changed, no strict
  gate was passed. Direct padded gradients and padding-only lossdelta are0 in
  both trials. Native score loss is0, language alignment disabled, so neither
  active-score-path behavior nor text padding is certified.
- Results reject only those direct premises; decoder attention, general graph
  parsing, nested scene relations, robustness and trained efficacy remain open.

## 5. Design Rationale
- First stable diagnosis registered before broad review, then actual original
  mapper scan. Independent second hypothesis is geometric loss isolation, not
  a renamed main-token overlap or short-group input-transport candidate.
- Existing explicit filtering defeats the proposed direct spatial repair; absent
  stored nonroot spans defeats the proposed stored-span union repair. Neither
  justifies a new admitted core, placeholder, parser-pooling variant or tuning.
- Native terminal reconciliation is additional real information, not a new
  structural experiment or proof of scientific novelty.
- Scoped no_information_gain after these two tested premises only; no assertion
  that all research is exhausted or that GPUs block work. No active unfinished
  candidate is abandoned, and no new variant is admitted.

## 6. Next Batch
- Retry2026-10-13T07:00:00+08:00, within four hours; actual schedule unknown.
- Resume sooner on independent native mechanism-deficit evidence: e.g. parser
  replay establishing omitted edge relations, direct nonzero spatial padding
  dependence in a reached model/score path, or newly observed frozen-error
  evidence distinct from the completed TMR realization.
- Do not rerun zero-incidence stored-span tests, tune TMR, treat tiny CPU repeat
  differences as a new localization mechanism, or expand budget from the old
  preflight snapshot. Candidate/queue terminal evidence is already durable.
- Relevant hashes are bound by the candidate records and design_cycle; no
  exhaustive novelty or scene-level efficacy certificate is asserted.
