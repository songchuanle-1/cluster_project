# Experiment Result Analysis - cluster_project

## 1. Basic Info
- ID: M200-TMR; state: done_earlystop.
- Config: configs/Quard/ctf_hcg_csort_tmr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_tmr.yaml.
- Server-6 / GPU7 / original seed1999 / unchanged50epochs and70max_iters.
- Native PID3639592 absent; original native log explicitly records patience10
  early stop at epoch23, not a crash or monitor-imposed restart.
- Local verification:2026-10-13T05:17:26.187218+08:00.
- Remote observation:2026-10-13T05:20:52+08:00; remote terminal logger
 2026-10-12 21:09:34 UTC. These clocks differ; no inferred exact duration.
- Native archived log SHA256:e30903154dd4ccab5eb3357c6d08cf91266071f697ea119810815e34808550c4.
- Facts: pipeline/reports/m200_terminal_facts_20261013_0507.json.
- Previous experiment/ledger state preserved in
  pipeline/reports/m200_terminal_before_20261013_0507.json.

## 2. Best Metrics
| Metric | Value | Epoch | Precision |
|---|---|---|---|
| mIoU | 0.4952795207500458 | 13 | original logger float |
| Acc@50 | 0.549 | 13 | native logger rounds to 3 decimals |
| spmIOU | 0.459 | 13 | native logger rounds to 3 decimals |

## 3. Convergence Summary
- Exactly23 validation records; best at13, followed by10 without a new best.
- Last epoch23: mIoU0.4805612862110138, Acc@50.534, spmIOU.443.
- Native patience termination observed. No fabricated five-window convergence
  calculation, population harm interval or multi-seed stability statement.

## 4. Comparison
- Versus stored baseline0.4894:+0.005879520750045775.
- Versus stored champion0.5020:-0.006720479249954225.
- Goal0.5100 remains unmet; no champion replacement.
- Baseline/champion values are stored rounded comparators; these are descriptive
  deltas, not uncertainty-qualified causal estimates.

## 5. Conclusion
- The single registered training screen did not improve the champion.
- Preserve the successful execution controls and actual wrong-root diagnosis;
  trained failure does not erase those observations or prove every parser-related
  mechanism ineffective.
- No automatic restart, weight scan, renamed successor or new seed.
- Frozen overall/subgroup evaluation uncertainty is not quantified by this log.

## 6. Crash Info
- Not a crash: original log has an explicit early-stop record.
