# Experiment Result Analysis - M194-CTF-HCG-CSORT-SCM
## 1. Basic Info
Config: configs/Quard/ctf_hcg_csort_scm/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_scm.yaml.
Server4 GPU1; launched September14 14:07:51; monitor finalized September15 16:16:47.
Registry stopped_unknown; native log explicitly shows normal earlystop.
Log: /data/songcl/Project/Cluster_project/Cluster/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_scm_20260914_140751.log.
## 2. Best Metrics
|Metric|Value|Epoch|
|---|---|---|
|mIoU monitor|.4920|unverified|
|mIoU native footer|.4924 rounded|20 inferred, not checkpoint verified|
|Acc50 at best|unknown|unknown|
|spmIoU at best|unknown|unknown|
Final VAL30 .479/Acc50 .532/spmIoU .441 are not peak metrics.
## 3. Convergence Summary
Native footer: `Early stopping at epoch 30: no improvement for 10 epochs (best=0.4924)`.
Plateau confirmed. Initial line-based tail overexpanded CR progress;
byte-bounded normalized final tail confirmed the footer.
## 4. Comparison
Rounded native peak vs baseline .4894491: +.00295; vs M95 .5024607: -.01006.
Target .51 remains unmet; exact SCM checkpoint best remains unverified.
## 5. Conclusion
Failed to improve champion. Do not restart or tune SCM to fill queue.
Registry reconciliation pending; preserve native evidence without unsafe queue mutation.
This does not reject all spatial supervision.
## 6. Crash Info
No demonstrated crash. Three process absences caused stopped_unknown classification;
native footer indicates normal earlystop. No repair/retry performed.
