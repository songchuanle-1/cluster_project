# Experiment Result Analysis - cluster_project
Experiment: M204-CPA | State: stopped_unknown（主机重启中断，不是训练完成）
采集时间：2026-10-19 14:18 上海时间；CPU 检查点核验 14:26-14:36。

## 1. Basic Info
- ID: M204-CPA；稳定候选 coarse-semantic-point-cross-attention，CPA-R1。
- Config: configs/Quard/ctf_hcg_csort_cpa_r1/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cpa_r1.yaml。
- Server: server-4，物理 GPU0；原 PID141278 已不在，两次探针均无精确配置的训练进程。
- Started: 2026-10-19 09:29:58；最后原生训练行 12:16:58，第6/50轮1580/4686步；stdout最后1587步。
- 主机本次启动 12:17:42，晚于原启动。精确退出时间、退出码及重启原因未知；14:39:42只是对账时间。
- 原授权只允许一次探索性启动且禁止自动重试。本轮没有重启、迁移、调参或新增变体。

## 2. Best Metrics
| Metric | Value | @ Epoch |
|---|---|---|
| mIoU（未完成训练的原生VAL） | 0.43399661779403687 | 5 |
| Acc@50 | 未单独核验，未知 | 未知 |
| spmIOU | 未单独核验，未知 | 未知 |
| epochs_no_improve | 0 | 5 |

## 3. Convergence Summary
- 已完成5次验证：0.3420785069、0.3853775263、0.4117324054、0.4224834144、0.4339966178。
- 第5轮验证12:07:32完成，last.pth于12:07:39写毕，meta.epoch=5；原生恢复从第6轮开始。
- 第6轮未保存部分不能从该检查点回接。未见原生日志的早停、Traceback或OOM终态。
- 尚不能判断最终收敛、机制成立或机制失败。

## 4. Comparison
- 缓存历史baseline0.4894、M95champion0.5020、目标0.5100；champion仍差0.0080。
- 当前部分best数值差为-0.0554、-0.0680，不是相同训练预算的终态比较，不判定设计无效。
- 可用M95epoch16权重尚未验证为历史champion权重。

## 5. Conclusion
- 操作层中断，科学状态inconclusive；没有新的提升或否定核心假设证据。
- CPA-R1只改变粗层消息：Q=点特征、K=原始粗层bank、V=CTF更新粗token；细/中层、融合、query和原损失不变。
- diagnosis/semantic-controls未通过，revision1仍inconclusive；不把中断写成科学拒绝或资源PASS替代准入。
- 两份检查点CPU可读、SHA256已留档；last中模型1165张量、优化器1926张量均有限，含AdamW、PolyLR(last_epoch5/max_iters70/power4)、best和早停计数。
- 已核对train.py/gorilla.resume加载优化器和调度器，但没有执行实际恢复训练，不宣称续训成功。
- 无RNG状态，不能保证与未中断训练逐步相同；第6轮未保存工作需重做。
- 只在所属会话明确授权后恢复同一M204-CPA，server4GPU0、seed1999/batch2/workers4/总50轮不变；先重新核验源文件、身份、占用及独占租约，再核实恢复状态和步数增长。

## 6. Interruption Info
- 故障：重启后原进程消失；模型异常、原生退出码及主机重启原因未知。
- Auto-fix/retry：未执行；原授权明确不允许自动重启。
- 精确日志保存在pipeline/diagnostic_bundles/tick_92463b56/native_training.log，远端SHA256一致；检查点未改且留在原服务器。
- 证据同目录：original_run_before/after.json、original_run_reconciliation.json、checkpoint_cpu.json、resume_contract_cpu.json、lifecycle_reconciled.json、resume_request.json。
