# Codex Research Memory

## Goal And Phase
- 当前60d21b3324c94445b26d2ecb24a3ba65，actual/target01a159c5-29ab-7a22-ba7f-e79174757253一致；generated2026-10-26T16:09:41.027895+00:00/deadline17:09:41.027895+00:00原值保持。
- goal0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85；ScanRefer目标.5100，M95最佳.5020/baseline.4894/gap.0080。Phase1层级分工→inst_feats→query/masks，监督辅助，Phase2需人工确认。
- seed1999/epochs50/max_iters70/原YAML/data/pretrain/optimizer/precision不变；原10G/原fvcore handlers/fullunsupported、bs1/lang1/warm20/repeat100 median/P90。峰值显存+15%需≥+.003mIoU；禁调参、gate/cag/cfe/layerscale、语言路由、大QKV/N²attention、重复inst注入、旧rejected改名/无图改变微调。
- standing authorizations/experiment_first_20261021.json SHA2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8覆盖项目普通实验操作，不授旧hold重开/额外修订/受保护恢复/扩大资源/改调度。
- 最新人类不用gpu1：SERVERS SHA2583ddf1a21511368e98bfaed99d1a2c5e6bd7f223e577d565279a3628352fc1仅server4 physical[0]/max1；授权server4_gpu0_only_20261026.json SHA94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09。旧GPU1实测仅历史依据；未来禁用GPU1，其他allowed[]/调度Disabled保持。

## Champion And Baseline
- M95仍.5020；M205-MDC26/.4872、M207-HAP31/.5002、M208-HRC31/.4901、M209-PSBR23/.4969、M210-PSNC31/.5001、M211-BTC31/.4914、M212-BCR27/.4995均自然早停未超M95。不调参重跑或整体否定层级方向。
- HAP原DataLoader异常根因UNKNOWN、epoch18恢复授权已消费；BTC/BCR原版本/归档/完整日志保持，不再启动。BCR archive5d060afca23d43deb4ae63525c00ff3d/完整log f14c962f…。

## Active Hypotheses
- M215-BEC R1现已真实训练，primary/runtime/source026c0c4cda5332bbcce0faa33b3cbdb3d3c5b563（父4e8），精确9A ff，不新造commit。admission113a72afb83c57401d00072b1a723a5cc3094a76a1e2d9acfe75b465f10238dc，唯一canonical dispatch/native Popen1次，原GPU0 PID1558071/start64444390，原YAML/seed1999/epochs50/maxiters70/data/optimizer不变。
- BEC双跨层joint child+parent→2C/GELU split u/v，v按true child等权上行，经原coarse LN/FFN再两2C→C/GELU回传middle/fine；六原model/rawmean/FPS/IDs/CSORT/HCG/单inst保持。原9b两smoke成功/JIT bool index_fill资源失败f8fac959仍保留历史，非假设否定，不重标为026c结果。
- 唯一implementation R1原注册3fa782b8… immutable字段保持；仅True→1 CPU兼容修复，CPU390ac50a先前bool/int1 eager相同、bool JIT失败/int1 trace+fvcore通过，原2ef/617源与原声明不改。现真实四臂独审后R1.result=passed、追加本轮actual result_evidence并用canonical revision_digest绑定收据，无新修订。
- 历史94f真实R1四臂全terminal/rc0；原checker报告89099675a78da788f8186968102de364901859110f68ad8cd7bb45065ee798e0，独审46c47d4983a31205d710be5889e7e9e812bd4d3649865edef60c5f046b4c0a36。TRAIN2 loss9.3905391693/13.9133872986、真实两batch/common839张量/156432954参数/hash768c65…配对；5module/12原W块每步原loss有限grad+实际更新，fine边2048/middle512、上下行/私mean/原coarse/HCG/inst-mask路径观察通过。
- BEC R1原资源9.720589388G vsM959.762532428G，params157220922 vs157484090（−263168）；同GPU0 median36.89109697 vs35.94086046ms（慢2.6439%），P9038.59042175 vs38.09330325ms（慢1.3050%）；预测allocated−.11237%，observer-smoke allocated−.03420%，+15%条件未触。保原handlers/fullunsupported，pureTRAIN峰值/效果/新颖性未知，不称全面更快。
- 原R1 op9a81/nativeedd/worker7e/releaseee75、四结果checker57752/071202/98def均原字节；94f仅fresh绑定/原deadline/GPU0 staging执行，未原地改旧2d/null或322c原23文件/null/DRAFTTrue、旧9b op420/8e/b551。
- M214-CTS已canonical stopped_unknown，archivea966d7e40d26454598863ac4a87fc4a9/14of50/best记录.4890；原PID3505065不见，ownlog停14:1843无尾部异常/正常结束标记。原因UNKNOWN，不说正常完成/模型失败，不自动恢复。原source4e8/receipt5416/launch/检查点未动。
- CTS唯一完整log已root精确读取并本远SHA/size一致：17693952B，05dce0486051bf0cf8d4af30de61a6a756200efb47b32033b6355f5e7df12da4；tick_94f8ddb8/cts_exact_archive/archive_evidence.json，root补log_local与辅助training_status两field，原archive/status/best/epochs/receipt不改。
- M216-AEF现已保存真实隔离source56b2a96dc48cc8a88f0f7105527ef448113b1060，唯一父026c，恰9A/9blob全等原9d6冻结源码，隔离HEAD/index/worktree clean；版本证明427ee808…/实际Git独审4d1e98e0…。主线/运行源仍026c，未promotion/sync/native/FP32/资源/准入。
- 原150c AEF prep9d6a03/candidate3898be内code/source=null、reference4e8维持原字节，21集成+46独立stdlib结果仍只覆盖旧原源码软件性质；新实际parent026c由本轮新source_version单独记录，不回填或重标旧证据，不增加模型修订。
- AEF只middle原父组detached几何MST上的双向共享GELU/W反对称q和signedincidence，原LN/skip/fine/coarse/rawmean/CSORT/HCG/单inst不变；只实数unweighted sum，不保RSTR πpointmean/非Markov，不授旧RSTR恢复/R3。理论参数−394240，实际资源/梯度/准确率未知。
- AEF当前native工具尚未完成：下一步按真实56b2源版本/原YAML协议准备native worker；实际M95/AEF TRAIN2与原资源只在BEC自然释放唯一GPU0且fresh UUID/三锁/currentowner/原deadline通过后执行。不得复用B E C common839或CTS843计数代实际派生，不原地改源码/抽样/阈值，不现在promote运行主线。
- M213-BFC原TRAIN20/50 step3832/4686共享DataLoader scatter overlap RuntimeError，crashed archiveb91b3ba11671451bb28f39dc3cc3f2c7；source48fc/receipt812454/launch/完整log daf14d06…保持，根因UNKNOWN，不否定机制、不自动恢复。
- BFC last.pth SHA24b3424f0cdc3a6f004bf20ff49b1799e75b92382214b2590d90486192883777，epoch19/best.4992169439792633/noimprove4/1151CPUtensor finite/640optstates/5groups/maxstep89034/scheduler19；证据9b957f10…/计划8379534d…已存。RNG/sampler/失败输入未复现，不能称续3833；需具体兼容源计划与BFC专属人类授权，不借HAP/M206grant。

## Closed Or Failed Directions
- 旧10本轮未due，不读655正文/旧grant/checkpoint体、不重开/重测。最近bounded metadata tick_3d001030/held_boundary_check.json SHAed313bb0…是原时间证据，无新增恢复/修订许可。
- PCE默认2+额外1已尽/2.861e-6/13.86x，RSTR默认2已尽/R2mean1.027033878e-6>1e-6；禁PCE_R4/RSTR_R3/M201自动恢复。旧RSTR9文件localcommit授权不授额外修订，负证据全保留。
- 原2d06 prep/null、native322c原23文件/null/DRAFTTrue、旧9b op420/8e/b551均原字节；新R1工具是新包，不填旧null或原地启用。BFC P90+3.2118%/BCR原GPU1较慢，不夸全面效率；预测/observer不等pureTRAIN峰值。

## Running And Queue
- 当前1个确认训练：M215-BEC source026c，server4GPU0 原PID1558071/start64444390；采集2026-10-26T16:13:54.410568+00:00→2026-10-26T16:13:57.772397+00:00，TRAIN2/50 3963→3972/4686；本轮4974189d…观测/0eb7c9eb…独审。原source8/YAML/queue/experiment/receipt/revision_digest及唯一selected0 mapping核实，不声称持续独占。
- CTS已unknown终态归档并释放登记槽位，无自动resume；M206waiting但paused/dispatch_hold/resume_authorized=false不计ready，GPU1禁用。当前0ready，AEF只准备未入队；BFC不恢复。
- AEF本轮实际resource_check05916568…引用本轮root硬件实观和当前登记，唯一GPU0被原BEC占用；检查本身0transport/Popen/network/Torch/新硬件查询，无AEF adapter/PASS或工具可用性声明。源码版本保存不等于准入或可运行待跑。
- pinned songcl@192.168.1.115，先验证dl04-MS-7E06；GPU0 UUID GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c；root /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1；conda project_cluster/server4_conda_4ca73fba.sh，data /home/songcl/data/data/，ckpts /data/songcl/Project/Cluster_project/Cluster_checkpoints。keys/strict hostkey，不用旧IP/密码/sudo。
- 未知claim/request/PID只读reconcile，不盲重启/kill/删锁；白名单/旧lease不是未来空卡许可。真实GPU计算前核当前资源/UUID/三锁/原deadline；python -B与PYTHONDONTWRITEBYTECODE=1。

## Open Questions And Risks
- CTS停止原因UNKNOWN；仅日志无尾标，未读新checkpoint或构造恢复计划/授权，不推断外部kill/OOM/模型崩溃，不借HAP等grant。
- 当前BEC仅确认原生+资源与训练步数增长，准确率仍待测；目标.5100/M95.5020/gap.0080。原buffer/RNG/offdiagonal/未行使零边界/pureTRAIN峰值未知；单row/call零合法，不新加数值门。

- AEF只有兼容源版本与原软件性质，Torch/原生forward/backward/实际grad、浮点Σδ、同口径资源与效果均未测；不能拿Git/CPU/符号性质代签。最新BEC验证指标本轮未提取，完整训练效果待评估。

## Last Tick
- 新begin完成一次canonical进展/派发；当前BEC原训练继续，无新终态/运维故障，M206暂停不计ready。AEF是唯一due可推进项，creation/reserve预算1但未新增候选，只接续已有source版本。
- 实际本地隔离worktree+单父026c普通commit56b2，仅新增原9d6九文件；保存helper478075/93e243与源审fb9b0598，root执行新副本仅启用单flag，actual Git独审4d1e98e0确认9blob/单父/clean与primary28/index/14账+19保护文件在该操作前后全同。无主线ff/remote/模型执行。
- 本轮真实tick_attempt为AEF resource_check/blocked，原BEC source/progress双样本证明原GPU0占用；实际0新candidate/0模型revision/1隔离local source commit/0新准入/入队/训练启动。不重跑原136/46软件套件，不读旧655/grant/ckpt。
- 收尾仅work中AEF实际source/current resource与BEC当前进度、七段memory/notes改变；其他140候选、全部14生命周期账、主线026c/28status+bytes/index不变。六段report后canonical finish，以实际receipt/释放为准，释放后不回写。

