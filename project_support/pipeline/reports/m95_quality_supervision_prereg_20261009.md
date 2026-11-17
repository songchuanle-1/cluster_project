# M95 Quality Supervision Coverage Preregistration

- Created: 2026-10-09, Asia/Shanghai, tick 498da58819f245158586bd649cd29a88.
- Stable candidate: m95-quality-supervision-coverage.
- Stage: diagnosis, not training admission.
- Hypothesis: native quality supervision excludes a task-relevant class of
  candidate masks, leaving a corrective target unavailable to the learned path.
- First discriminating test: inspect the actual champion score-loss graph and
  matching/target construction, then reproduce the target-coverage calculation
  with frozen native TRAIN outputs if the source supports this hypothesis.
- Matched control: preserve checkpoint, batch, mask predictions and native
  referent labels; compare native supervised query IDs with all query IDs having
  a defined mask-quality target. Rotated query IDs are a negative control.
- Readouts: exact source path/hash, target definition, supervised/excluded query
  counts and native score-loss gradient reachability. No optimizer or training.
- Sampling: use existing frozen TRAIN inputs only; report sample/scene counts,
  companions and exclusions. Do not select cases using validation outcomes.
- Reject this realization if all intended query targets are already covered,
  the relevant output head does not exist, or an exact matched intervention is
  a no-op. Missing tests remain pending, never rejected or PASS.
- Native numeric repeats retain the existing 1e-6 tolerance; failures are not
  relaxed. A source-only result does not certify native backward or efficacy.
- Scope: server-6 GPU7 only for native execution; local edits/static checks only.
  Keep Phase1 no-tuning, all goal constraints/bans and original schedule.
- No claim of novelty; literature, independent implementation, native backward,
  controls/resources and admission receipt remain required before any launch.
