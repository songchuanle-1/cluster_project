# GPU1 人工暂停记录

采集时间：2026-10-22 10:57:54（Asia/Shanghai）。

用户要求：GPU1可以先暂停训练了，给别人腾出来一张卡。

- M206-CGCA 原 PID732137/start21298582 及已核实原进程组以 pidfd 精确 SIGTERM；补发 SIGKILL 的进程数为 0。原进程和 GPU1 CUDA context 均已确认释放，GPU1 在确认时为空。
- GPU0 HAP PID979955/start21613920 的身份与 CUDA context 保持，队列记录逐字不变。
- 已冻结并 CPU 校验完整 checkpoint：meta.epoch=24，best_miou=0.4952535927295685，epochs_no_improve=7；model、optimizer（642 states/5 groups）、scheduler 完整存在，未初始化 CUDA。
- 原生脚本没有退出时 checkpoint handler；本次保存的是最近完整 epoch，未保存正在进行的部分 epoch。
- 新固定断点：`/data/songcl/Project/Cluster_project/pipeline/resume_snapshots/20261022_gpu1_pause_105409/20261021_232736/last.pth`；SHA256 `e9b42b2632762dae5ca49d80b3272889809b1ffe3ec30dd377690af8cb2e8e9d`。
- SERVERS.yaml 现在仅允许 server4 GPU0（每卡1任务）。M206 保留 waiting 条目但带人工暂停 hold、resume_authorized=false，移出 running 映射；不会自动恢复或迁移到GPU0。旧授权/旧运行/暂停历史保持。
- 当前运行根 HEAD `f51823bbddf0f8095a9a5813bf1f8169e3d7edb0` 和 M206 admitted commit `898ff63a2cf63d3895a9e86c0ee3d1e5b672b335` 分开记录；未来恢复必须重新核精确源/full-state/当前资源。没有 sync、checkout、goal 或调度变化。

证据：checkpoint_evidence.json、checkpoint_capture.json、stop_confirmation.json、operation_summary.json。

决策记录：pipeline/decisions/20261022-105913_manual.md。
