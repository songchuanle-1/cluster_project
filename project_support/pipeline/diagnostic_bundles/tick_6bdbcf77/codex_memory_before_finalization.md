# Codex Research Memory

## Goal And Phase
- 最新接管336ca5d7348b4018b7fd8b9e41f6eee3；actual owner/target=01a159c5-29ab-7a22-ba7f-e79174757253一致；generated2026-10-25T16:10:36.841364+00:00/原deadline2026-10-25T17:10:36.841364+00:00不延长。前06a2 FINALIZED/released且lock/pending消失后begin；本轮finish以真实receipt为准，不预签。
- goal0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85；ScanRefer目标.5100，M95最佳.5020/gap.0080，baseline.4894。Phase1 hierarchy→inst_feats→query/masks；supervision辅助，Phase2仍需人工确认。
- 原seed1999/epochs50/max_iters70/native YAML/data/pretrain/optimizer保持。原10G资源口径、bs1/lang1/warm20/repeat100 median/P90/fullunsupported，峰值显存+15%需≥+.003mIoU条件保持；禁止调参、gate/cag/cfe/layerscale、语言路由、大QKV/新N²、3/4/6重复inst注入、旧rejected改名和无图改变微调。
- standing pipeline/authorizations/experiment_first_20261021.json SHA2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8覆盖普通实现/测试/相关版本/安全同步/准入训练，不授旧hold重开/额外修订/受保护恢复/扩大资源/改调度。
- 最新资源人类“server4 GPU1也可以用了”：pipeline/authorizations/server4_gpu1_20261025.json SHA90f8820a60ef4d4e277904815b025658f7b8b457b0711a4d0ef5f7395fdd23f8；SERVERS d5277972e80b6fe184a3e07f0fff34f7e1e7950b558d60905416ced302b206a2允许server4 physical[0,1]/每卡max1；其他server allowed[]。M206暂停仍有效，Windows Pipeline-cluster_project Disabled。
- 用户2026-10-25问当前创新设计，已说明BFC/CTS只替换middle，fine/coarse沿用M95，按层分工完整attention尚未落地，新颖性/收益未证；问答未改变目标/资源/权限/预算。

## Champion And Baseline
- M95仍.5020；M205-MDC earlystop26/.4872、M207-HAP授权epoch18恢复后earlystop31/.5002、M208-HRC earlystop31/.4901、M209-PSBR earlystop23/.4969、M210-PSNC earlystop31/.5001；均未超M95，不调参重跑或整体否定hierarchy。
- 新终态M211-BTC原source00e2b18c6b8d568a64edb496e6979d766440883c自然earlystop31/50，native终态best.4914（4dp），末次Val.479分开；原PID2784474/start47557208退出，0信号/重启。完整42038211B原log本远SHA2b4032d0b705ae7f5e8ebdba81f14d5ed7eb55da491b4b9fec2ba78342aba38c保留，canonical archive_id73e3038e744b4f6a9bffb68a7b43e8f8/receipt93756329…/source/launch proof保持。
- BTC真实终态/全log/仅本ID finalize_task归档见tick_336ca5d7/btc_terminal_archive.json SHA2fef3232e42c97c550f20df9f42982f72c7cf7e3e9d4191a74b0f41e90c20962及独审0d06cc39…；未重复monitor/preflight或deathwatch，未手写queue/running清理。M95/目标差距不变。
- HAP原epoch19 DataLoader AttributeError根因UNKNOWN，epoch18恢复授权已消费，非再次restart许可。原crash/snapshot/prior_runs保留；PSBR完整log0204be90…在a4f73140，PSNC完整log在ddb531fb；其他旧版本/失败/归档不重写。

## Active Hypotheses
- M213-BFC现正式training，tested/admitted/runtime/main均48fc302c3c02ffef0b241be3593c386b6b65a72e，singleparent11a。源8512a69d…/原YAMLa18f2c6f…/worker88392519…保持；只改middle同父true-supported token按detached几何排序的bit-up/down稀疏配对，共享2C→2C/GELU同时更新双方，保留n份C状态与原ID散回；原LN/cfskip/finecoarse/rawmeans/FPS/CSORT/HCG/单inst保持。非可逆/无损/独立novelty或训练收益声明。
- 本轮真实fresh owner336绑定GPU0/原deadline，四臂原M95/BFC TRAIN2与资源均terminal/rc0；manifest5324b975…、binding3d4715b6…、lease67f0b80c…；诊断时公共runtime11a与staged候选48fc分开。两候选loss9.5372838974/13.9084777832，原criterion backward/optimizer各2；共同843张量/156958522参数/hash04231c23…及两原TRAIN batch fingerprints配对。
- BFC每forward64个n>=3、多stage父组，nonpower56/60，56round/0singleton；四W quadrant每step原loss非零有限梯度与slice实际更新，原skip/HCG/inst→mask路径核实。逐call/row/half零合法，不加新门；singleton/unsupported/pad实际0属NOT_EXERCISED。首raw/id/map跨target摘要不同，不推断原因/幅度/收益；fullbuffers/RNG/offdiagonal/FP32未测。
- 真资源BFC9.775377484G vsM959.762532428G，params157221178 vs157484090（−262912）；同GPU0 median42.218151968 vs42.311575031ms（−.2208%），P9062.910521450 vs60.952819872ms（+3.2118%更慢）；预测allocated935713280 vs936763392（−.1121%）、reserved1189085184 vs1191182336；含observer smoke allocated+.00214%，15%条件未触发。完整unsupported原样保留；纯TRAIN峰值/准确率未知。
- 实际checker报告tick_336ca5d7/bfc_execution_review_prepare/actual_four_result_review.json SHAb8fa916c6c746e86d03fc3aa4fc3325382e11266c6662de85ece09a35934ae4b；全面真实独审43afc27994befe726f987d3e029e19307b421de1ff43e1c4ef7135fd7970248a、独立交叉审419fd14b…；4原request逐一只读reconcile/fullobjects/LinuxSHA相同，history01cd9bea…/statusf2e1a349…记录诊断结束workers/context空，非未来idle许可。
- M213 receipt pipeline/admissions/M213-BFC.json SHA812454a819702e8f4d53080c1b479617d605f2175bf44a3422905688253ca01c。仅真实已测9A ff-only推进primary11a→48fc，保护28status+bytes/index空；canonical safe_sync同样11a→48fc，仅候选YAML既定路径适配。未新造BFC commit/force/reset/stash/clean，未改BCR8/YAML/原进程或BTC归档。
- 本轮dispatch首版在任何intent/transport前因canonical load_servers不保留expected_gpu_uuids而KeyError；原失败/zero-intent proof保留。新execute_v2仅从SHA绑定raw SERVERS读全UUID map并精确核对，独审60f40e7e…；原owner/三锁/once/源/receipt/FIFO门不松，非模型revision。实际只一次_process_queue/一次native Popen，结果9e453fb4…，最终独审069833d3ff3fa18a403b2ae37a749c754563947efe0dc09bb0d58a6725dac20c。
- 原BFC历史静态包727b(DRAFTTrue)/operational d788/native0c50/release95a2与61离线run2/42旧负例及所有失败快照保持；未重跑或重标新实验。实际执行336独立绑定，旧prepare token/deadline/空字段不改。当前源码/时延与容量不证明新颖性或训练涨点。
- M214-CTS现validation，已实保存隔离source4e80006047d5cb3dcdfb9c1102e02c33f354a07d，唯一parent为当轮已测且实际primary48fc；worktree pipeline/isolated_versions/cts_336ca5d7，仅原bfab九个独立model8+原YAML9A，primary/runtime48fc及28/index/13账前后未变。source_version证据tick_336ca5d7/cts_version_execute/isolated_source_version.json SHA6b666a8c8e9d0f5bed8422fa02e6e2ea17192b1114c6eda5ecf28affb409c2d0及本轮独审；不是主线/运行源推进或native PASS。
- CTS原sourceprep tick_3824d9c9/new_candidate_prepare/preparation.json bfab01a3…/protocol70363d43…仍原metadata code/parent null、base_reference11a仅历史来源；真实新父48fc与新commit单独记录，不回写冻结准备。原264384作者stdlib/136oracle+14拒绝、3de1e79f拓扑/dcb3f3d7集成均静态，未重复测试或混作训练。
- CTS同父原几何cycle同步old own/±3^r经共享3C→C+原GELU，最小3^k>=n轮，重叠receiver；重复负邻slot私有0，n1同W[x,0,0]，无支持/pad delta0。原LN/cfskip/finecoarse/rawmean/FPS/IDs/CSORT/HCG/单inst保留。明确dense3tap dilated circular Conv1D家族近邻整体图替代，非新覆盖、单因素因果、新颖性或旧MDC重开。
- CTS禁用native包tick_4694ba96/cts_native_prepare/preparation.json ff7fb7a6…/独审7edea74d…+2ee2f7db…仍DRAFTTrue且code/parent/10active null。新4e8源版本不会自动使旧包可执行；须新建受审版本绑定operational copy/lease/adapter再用真实空卡原M95/CTS TRAIN2与资源。三W input列块原loss有限非零grad/更新，实际3distinct/multiround/r>=1覆盖；缺覆盖INCONCLUSIVE，不换样本/seed/precision/阈值，逐call零合法。全部native/资源/效能未测，无M214receipt/queue/launch。
- M212-BCR科学tested/admitted source11a811618179ab1ddc0cee299194667413b7fdb9、receiptb8532405…，原strict-exclusive双向scan/own-L-R读出保留；现公共runtime48fc仅增加BFC9文件，BCR独立8源/映射YAML77e/原PID/start均核实保持。前7526真实TRAIN2/资源/独审/准入/启动证据沿用，不代签BFC/CTS。

## Closed Or Failed Directions
- 本轮336旧8hold完整canonical digest/655声明path-hash签名/14授权目录元数据与8878/3824基准一致；held_boundary_check.json SHA8f5a970b3ed9f228f7fc9ce584450239cb8a0eabfeabe7cabe04a4e39ca1fad2。0个655正文read/hash/stat/exists、0旧grantbody读/hash、0checkpoint body；new_action/user_decision false。旧scope/失败/修订上限不变，不因GPU空或到期而重开。
- 4supervision scope保持辅助；PCE默认2+额外1已尽/2.861e-6与13.86x，RSTR默认2已尽/R2mean1.027033878e-6>1e-6。禁PCE_R4/RSTR_R3/M201自动恢复；旧RSTR9文件localcommit授权不授新修订。原所有负证据与准入史保持。

## Running And Queue
- 截至2026-10-26T00:36:47.869059+08:00上海，M213-BFC GPU0原新PID219369/start56265957 Train1/50 133→141/4686；M212-BCR GPU1原PID1215422/start51717921 Train15/50 3724→3729/4686。actual唯一argv/cwd/fd1/各8source/部署YAML77e/UUID双样本保持，公共HEAD48fc，BCR科学source11a分开。proof tick_336ca5d7/active_runs_progress_observation.json SHAcd5eca4e362d581cc7564f6d9ec24ab70d544e572f1aabb1500990bbdebb8824。
- 当前2running/0ready，M206-CGCA waiting但paused_by_user/dispatch_hold/resume_authorizedfalse/noPID，不计ready、不恢复或迁卡。完整checkpoint历史meta24/best.4952535927295685/noimprove7，last.pth e9b42b2632762dae5ca49d80b3272889809b1ffe3ec30dd377690af8cb2e8e9d保持，未读body。GPU1资源可用不授M206恢复。
- pinned songcl@192.168.1.115 / dl04-MS-7E06；GPU0 UUID GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c、GPU1 GPU-7f82edb9-f620-8045-caea-a75232265cd1；root /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1，conda project_cluster/runtime server4_conda_4ca73fba.sh，data /home/songcl/data/data/，ckpts /data/songcl/Project/Cluster_project/Cluster_checkpoints。keys/strict hostkey，先hostname后操作，不用旧.137/密码/sudo，python -B/PYTHONDONTWRITEBYTECODE=1。
- BFC launch的三flock覆盖idle/UUID至Popen返回，未冒称整个训练全程持有诊断锁；未知claim/request/PID只读原请求reconcile，不盲重启/kill/删锁。任何新GPU计算均要fresh owner/deadline/assets/实际idle/三锁，旧lease或原诊断context空非未来许可。

## Open Questions And Risks
- BFC/BCR最终准确率与新颖性UNKNOWN，M95.5020/目标.5100不变；本轮preflight BCR15/50 Best.4929/noimprove1/10仅当时训练中数据。BTC终态best.4914未超M95，不整体证伪hierarchy或调参重跑。
- BFC P90实际较M95慢3.2118%，不夸称全面效率提升；median微差非因果收益。BCR前GPU1 pair median87.0268 vs84.8601/P90108.9350 vs99.9325也更慢，不与本轮GPU0 timing直接比较。完整unsupported/CPU-Python开销局限保持，预测/observer-smoke峰值不等于纯TRAIN峰值。
- common配对只覆盖843 named parameters和两原TRAIN批次；fullbuffers/RNG/FP32/offdiagonal依赖/未行使零边界未测，首bank跨target digest不同无幅度或原因结论。native早期/proc argv偶空只作未观测，原Popen/terminal/result链成立，不用于未来发信号身份。
- CTS源版本4e8仅本地完整性，尚需新版本绑定原生包与真实资源检查，不得把原ff7 null字段原地填满冒充已审版本；新parent48fc有实际BFC receipt/四臂证据，不是从历史11a猜测。

## Last Tick
- 本轮336初始snapshot2running(BTC/BCR)/0ready、admission_budget2/reserve2/creation0，11due含旧9；实际发现BTC已自然退出，canonical仅本ID归档后空GPU0继续BFC。未二次preflight、未扩资源或动既有运行。
- 实际M95/BFC原TRAIN2+原资源4arms全terminal/rc0，真4reconcile/status匹配；native语义与独立/交叉审通过→精确9A ff-only primary/safe runtime sync→receipt812454→一次canonical verified launch。预派发normalized UUID KeyError是已证明零请求的本地接口失败，原证据保留，新raw-map副本审后才发唯一真实Popen。
- 0新候选，1新真实准入/queue/launch（≤预算2），两active恢复BFC0+BCR1；BTC31/.4914归档。CTS作为既有候选保存隔离4e8/parent48fc九blob源版本，未推主线/运行源，未native/准入/训练。源码主线只推进已测BFC48fc，28保护status+bytes/index与13账源保存前后保持。
- 完整本轮记录位于tick_336ca5d7，canonical queue_push决策由真实admit生成；旧9有界复查无新权限/修订/M201或M206恢复，目标/资源/禁项/数据seed/schedule/YAML/调度不变。新结果不证明涨点或新颖。
- 七段memory与notes后canonical六段report、原token真实finish核FINALIZED/released与lock/pending消失；未发生前不预签，释放后不回写。实质BTC完成+BFC启动+CTS源版本准备，选择NOTIFY。
