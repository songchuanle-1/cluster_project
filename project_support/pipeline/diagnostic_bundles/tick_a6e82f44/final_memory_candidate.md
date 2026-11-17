# Codex Research Memory

## Goal And Phase
- 当前 owner a6e82f44da954be096beeaef0a3755bc，generated 2026-10-30T08:07:36.868186Z，原 deadline 2026-10-30T09:07:36.868186Z；实际 root thread 01a159c5-29ab-7a22-ba7f-e79174757253。本文件仅未应用草稿，不表示 report/finish 完成。
- 目标 .5100，冠军 M95 .5020，gap .0080；Phase1 为 pointfeature→inst_feats→masks，Phase2 人工。原 YAML/data/pretrain/loss/optimizer/precision/seed1999/50epochs/maxiters70/patience10、10G 与 bans 保持。
- 人类已恢复 server4 GPU1 使用；当前允许 GPU0/1、每卡1任务，SERVERS 19b375、resourcegrant 6529。旧 GPU0-only 授权保留历史。Pipeline-cluster_project 仍 Disabled，不改调度。

## Champion And Baseline
- 冠军仍 M95 .5020，baseline .4894。原 M222-AOC 正常 earlystop30/noimprove10，精确 best .5000720620155334，archive b132ffc47c5941119d9272c5e6aa35ef；原 receipt/source0314/完整日志保留，不恢复。
- 原 M223-FCB 的技术四臂通过不代表长期效果；唯一 formal PID3190302 在首个已观测 TRAIN 前消失，内部日志证明 pretrain 已返回和 Trainbatch2，退出根因/验证 best UNKNOWN。canonical stopped_unknown/archive be33748f0b67482cba00213bed99eb7a，receipt189f/sourceD4/完整日志保留，不盲重派。
- 前 68d6c0e3 tick 已 INCOMPLETE、context 未 commit、lease released。本轮只接管其真实持久结果，不补旧 finish、不重算其归档/FCB 启动或旧 D4 九源 FF。

## Active Hypotheses
- M224-SFC 来源 c9be548699cd66bf68badff9ae6198a03eafa142，唯一父 D4；原型963dc/协议c651/native173e/worker edbe/生产九源保持。真实三层森林节点 OLDstate 全邻居等权均值→共享 cell/GELU，同步恰组件直径 D 轮，hD 直接经原三 skip/HCG/CSORT/单次 inst；普通 GNN 家族，效力/新颖性未知。
- 本轮 SFC 原 GPU0 诊断四臂均单次 terminal rc0，两个自然 TRAIN batch/common 动态 names-shapes-count-hash 实配；candidate losses 9.176466941833496/13.905925750732422。真实 D4/R4 路径与 wholecore 原 loss 聚合梯度和真实整体更新通过；未遇到的 D2 提前完成边界仅 NOT_EXERCISED。
- SFC 同原资源口径双方 FLOPs 9.762532428G；candidate/control median 35.16075097/33.95235795ms（+3.5591%），P90 39.68409386/36.81934724ms（+7.7805%），allocated 930981888/936763392（−0.6172%），原15%条件 false。不能写全面加速或纯 TRAIN 峰值。
- SFC 已真实 exact9A D4→C9 主线提升、技术准入和 canonical 单次 GPU1 启动；原 PID3696093/start96568246 严格原生步增 [1,359]→[1,366]（08:35:15→18Z），source/runtime C9。已知增长证明不等于训练完成或准确率收益；不重派。
- M225-ELC 来源 18e64b8d95ed0ba5c1053ead114c0f91a4b0c324，唯一父 SFC C9；原型 c777/协议7add/native28ec/worker614a 不改。无向原边持久状态：initialize/GELU 一次，OTHER-incident OLDedge 等权均值与共享 cell 同步恰 treeD−1 轮，再最终 incident mean→原 skip/HCG/单 inst。不是物理自信息去除，效力/新颖性未知。
- ELC 本轮四臂已单次 terminal rc0；candidate losses 9.152840614318848/13.906514167785645。实际 E2560/N2624、initialize1/R3/cell3/GELU4/OTHERmean3/incident1/三 scatter，持久状态 hash 链和 whole initialize+cell 原 loss 聚合更新通过；mixed lineD1/D3 未遇到，不增覆盖门。
- ELC/control FLOPs 9.758338124/9.762532428G；median 47.42672452/41.91025399ms（+13.1626%），P90 67.46532313/60.75894034ms（+11.0377%），allocated 931507200/936763392（−0.5611%），原15%条件 false。ELC 准入、formal 启动与严格步增仍待 root 真实事实，不能预签。

## Closed Or Failed Directions
- PES 在 TRAIN5/529 的 clip_grad_norm 参数枚举出现 ValueError，根因 UNKNOWN；原归档和 partial best 保留，不当 SFC/ELC 修复。APF/HPC/CTS/BFC 等既存 negative/unknown 不重开、不改名借结果。
- 旧10 holds、已尽 PCE2+extra1/RSTR2、已消费 HAP 旧 grant 与 M206 用户 pause/noPID/dispatch_hold 保持。新增 GPU1 授权不允许自动恢复旧任务、FCB 重启或改变数据/门/参数。

## Running And Queue
- 已确认的 formal 运行证据是原 SFC 在 GPU1 的上述 PID/start/sourceC9 严步增；ELC 四臂是 GPU0 原生诊断，尚无已绑定的 ELC formal 运行证据。本草稿不声明“两项 running”，不声明 ELC 已入队或已启动。
- 已知主线/远端 C9；ELC C9→18e 的新增九源 FF 尚待 root 完成事实。若后续全局 checkout 成为18e，只是新增 ELC 独立九文件，SFC 历史来源/回执仍为C9，原 PID/start/SFC 源与部署 YAML 字节须保持；新观察器需区分运行来源与全局 HEAD。
- SFC 在 GPU1 运行不构成 ELC GPU0 的 exclusive_gpu_slot；ELC 后续仍须真实技术证据/当前兼容源、fresh owner/原 deadline、授权 UUID、实际占用/资产和三锁。所有 ledger/队列/派发仍由 root 唯一写。

## Open Questions And Risks
- SFC/ELC 准确率、收益、新颖性、长程稳定性及纯 TRAIN 峰值 UNKNOWN。两步有限 loss、参数减少或符合计数 FLOPs 不证明任务瓶颈、效力或全面资源收益。
- 保原 wholecore 原 loss finite/nonzero 聚合梯度与真实整体权重/module 更新门；单 map/node/edge/round/列/bias 零合法，不加 FP32 守恒、Jacobian、收敛或强制边界覆盖门。完整 unsupported 和原100 timing 口径保留。
- ELC 端点 incident readout 有实数代数容量耦合风险，不是 RSTR 修复或 FP32 gate。保持原3LN/3rawskip/rawmean/FPS/IDs/CSORT/HCG/单 inst。

## Last Tick
- 本轮0新 candidate、0模型 revision、151记录；共8个真实原生诊断臂（SFC四臂+ELC四臂），不是8次正式训练。新 policy 兼容 op：SFC3c76/release0ce3/peer8ce8 与 ELCd770/release71ce/peercec3；仅资源 guard/合法其他卡预约校验变化，原来源包/native/worker/科学协议不动。
- 已有 SFC 九源 FF 与启动后 C9/空 index/原28用户/32生命周期基线；原未执行 postlaunch 文书草稿未用于覆盖 ELC 已运行事实。除本轮真实目标记录外，其他149候选、M206、旧授权/receipt/archive、源与用户文件保持。
- ELC receipt、exact9A FF、formal launch/strictgrowth，以及最终 running 数/report/finish 必须由 root 按后续实际结果补齐后再应用本草稿。当前不能预签 finish 或延长 09:07:36 原截止。
