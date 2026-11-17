# Experiment Result Analysis - cluster_project
Experiment: M195-CTF-HCG-CSORT-CPS | Observed state: crashed

## 1. Basic Info
- Config: configs/Quard/ctf_hcg_csort_cps/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cps.yaml
- Server: server-6 | GPU: 7
- Started: 2026-09-14 19:43:14 Asia/Shanghai; failure observed at 20:07 tick.
- Exact finish time unknown; remote clock differs. Train progress elapsed 01:07.
- Runtime crash confirmed by traceback; scheduler still running, deathwatch 1/3.

## 2. Best Metrics
| Metric | Value | Epoch |
|---|---|---|
| mIoU | unavailable, no completed validation in inspected tail | none |
| Acc@50 | unavailable | none |
| spmIoU | unavailable | none |

## 3. Convergence Summary
- Epoch 1/50, last progress 18/4686 steps; no convergence conclusion.

## 4. Comparison
- Baseline .4894491136074066 and M95 .5024607181549072 cannot be compared with this incomplete run.

## 5. Conclusion
- Operational failure, not evidence for or against CPS efficacy.
- Duplicate physical seeds violate the implementation's uniqueness assertion.
- Root cause and scientifically valid duplicate handling remain unverified.
- Do not silently skip pairs, change loss semantics, or retry unchanged.
- Preserve scheduler deathwatch reconciliation; next event must diagnose the seed contract.

## 6. Crash Info
- Error: ValueError: Duplicate physical seeds in one expression.
- Stack: tools/train.py:109 -> CPS network.py:128 -> loss.py:628 -> paired_switch.py:44.
- Evidence: one SSH tail of /data3/songcl/Project/Cluster_project/Cluster/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cps_20260914_194314.log.
- Auto-fix attempt: N; zero retries this tick; unresolved.
- Scheduler state was not mutated and monitor was not rerun.
