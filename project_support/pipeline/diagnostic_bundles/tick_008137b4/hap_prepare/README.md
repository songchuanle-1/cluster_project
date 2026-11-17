# HAP 当前轮静态准备材料

本目录仅准备材料；尚未 SSH、远端 staging、GPU 运算、原生两步训练或资源测量，不构成 admission PASS。

- 绑定 token：008137b428f54f20a65fe71e999f13dc。
- 原始截止：2026-10-21T17:03:27.572736+00:00；执行入口不会延长或刷新。
- 唯一执行会话：01a159c5-29ab-7a22-ba7f-e79174757253。controller 校验真实 CODEX_THREAD_ID；不要覆盖环境伪装会话。
- 唯一物理卡：server4 GPU0 / GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c；probe/query/三种 flock/CUDA_VISIBLE_DEVICES 均指此卡。
- 当前 [0,1] 白名单仅用于核验配置未漂移；本 controller 不查询或占用 GPU1。
- 独立 stage：/data/songcl/Project/Cluster_project/pipeline/hap_008137b4；不修改、同步或清理 active code root。
- 模型：f51823bbddf0f8095a9a5813bf1f8169e3d7edb0 中精确 8 个独立 HAP 源文件及原 YAML 字节；本地工作副本亦逐字节一致。
- worker_v2.py 与既有独立审阅件逐字节相同，SHA256 ffb2e09a53f3e860b398b435674ca0800b9641f5e48391d1af0d3098b8698a73。

主会话先确认 M205 终态已按原流程收尾、GPU0 当前闲置及 prepared_file_hashes。审核后分步执行：

    python -B "D:/project/cluster_project/pipeline/diagnostic_bundles/tick_008137b4/hap_prepare/controller.py" status
    python -B "D:/project/cluster_project/pipeline/diagnostic_bundles/tick_008137b4/hap_prepare/controller.py" probe
    python -B "D:/project/cluster_project/pipeline/diagnostic_bundles/tick_008137b4/hap_prepare/controller.py" stage
    python -B "D:/project/cluster_project/pipeline/diagnostic_bundles/tick_008137b4/hap_prepare/controller.py" smoke --target candidate
    python -B "D:/project/cluster_project/pipeline/diagnostic_bundles/tick_008137b4/hap_prepare/controller.py" resources --target champion
    python -B "D:/project/cluster_project/pipeline/diagnostic_bundles/tick_008137b4/hap_prepare/controller.py" resources --target candidate

stage 使用 SSH stdin 传输，避开 Windows 命令行长度限制；上传后仅导入 native_runtime 的 CPU 哈希验证，不进入 acquire/setup。所有远端 hash、source、config、annotation、pretrain、native train.py 和冻结 lineage checkpoint 必须真实通过。可按需重复只读 verify-assets；每项 smoke/resources 的 request 使用独占创建，重复执行会拒绝，SSH 不确定时先对账。

GPU 使用由 worker 的 acquire 在任何 torch/model import 前核验 hostname、GPU0 UUID/占用、training/diagnostic/exclusive 三锁、当前 lease/manifest/原 deadline 与完整资产 SHA，然后才设置 CUDA_VISIBLE_DEVICES。若 GPU0 繁忙、资源或资产漂移、时间不足，则失败并保留证据，不共享/抢占/删锁、不自动迁移到 GPU1。

协议保持：native train.train 的前两批原 loader（seed1999/epochs50/max_iters70/bs2/workers4），真实 loss/backward/optimizer step，HAP 两输出及 fine/middle 非恒定路径和 coarse 截距梯度、各层 FFN 权重更新；仅 smoke observer 包装原 pinv 一次并返回原 Tensor，不设置额外 rtol/atol。资源模式没有此包装，沿用原 fvcore handlers、同一输入、bs1/warmup20/repeat100/median/P90/显存/总 FLOPs≤10G。需比较 paired input_sha256/handler SHA 及候选相对 M95 增量，尚无 baseline 无 cluster 增量。

prepare 不能证明 native smoke 或 resource PASS。若 observer 失败，保留原异常和 diagnostic_observer 归因，不能据此伪称 pinv/model 被证伪。结果中的其他 spectrum 字段出现 null 也不能当成有限值 PASS。科学效果与 mIoU 均未测。

controller 仅写本目录请求/观测/结果，不写 research_work、memory、队列、模型或配置；正式 admission/部署/训练由主会话按完整结果决定。
