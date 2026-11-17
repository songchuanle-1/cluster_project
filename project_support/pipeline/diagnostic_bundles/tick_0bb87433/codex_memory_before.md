# Codex Research Memory

## Goal And Phase
- 最新直接用户2026-11-04授权server4物理GPU0、启动、继续，明确“可叠加在他们的任务上  显存够用”。授权pipeline/authorizations/server4_gpu0_overlay_20261104.json SHA783ffc27d48872940c2e15adcb85f6bb5f9b94492a8abd88694799f483d20e88保持；allowed_gpus=[0]/dispatch_enabled=true/allow_external_overlay=true/项目max1/原task_memory_mb=20000。
- 保留training/diagnostic/exclusive三协作锁。允许外部共享，不要求空卡、无context或低利用率，不再询问已有共享/启动许可；新GPU任务前仍核真实剩余显存。
- Phase1目标mIoU .5100，冠军M95 .5020/baseline .4894。原YAML/data/pretrain/loss/optimizer/precision/seed1999/epochs50/max_iters70/patience10、10G与原conditional15%显存规则/bans保持；不加FP32、逐参数非零或minimum-effect门，Phase2人工。
- GPU1和其他服务器禁用，M227-LFT、M206独立人工暂停保持；不驱逐、发信号、重启或迁移已有/外部任务，Pipeline-cluster_project保持Disabled，不改目标或调度。

## Champion And Baseline
- 冠军M95 .5020保持。WFC(M226)原生epoch30/noimp10自然早停，精确完整best .49711745977401733；archive ead6b5a9edf2466ea96e2587c931c865及checkpoint/精确校正保持；break先于save，不称last为epoch30，不重启。
- NEC(M228)原生epoch23/noimp10自然早停，23完整val，精确best .49454113841056824@13；archive35d448b2c70544049fa18e199081d30d，best13/noimp0，last22/noimp9。低于冠军，仅本实现本seed，不重启。
- MIC(M229)原生epoch26/noimp10自然早停，26完整val，精确best .49881425499916077@16；archive d03c21a094d54ed0b17a50cc21deeeb7，last25/noimp9。generic归档舍入.4990及校正历史保持。原guardian3033165已自然RELEASED，不重启。

## Active Hypotheses
- M230-HVD hierarchy-native-variance-decomposition-composition已真实原生检查、完整资源、独立复核、技术准入、部署与单次启动，现因运行时TypeError崩溃归档；真实祖先within/between方差分解→共享4C→C→C→原HCG单次inst_feats写回。效力/新颖性/人口瓶颈UNKNOWN。
- HVD测试源与当前主线d20eb221eff6584b67d4e9b5673559d0e1cb735b，父MIC07ef534a6e44f22bd7b2d083550ebd7823d1d3d3；原e38(parent6bc)、全部NULL母包和最终worker f91bddf7历史冻结，不补签或重跑。
- HVD receipt pipeline/admissions/M230-HVD.json SHAc92fcd22366cd5d84253c33ab37b2b72857915e239cfc5bb7741a58baa549a33。835共同init张量/两自然TRAIN批指纹一致，原loss有限backward、整core实际更新及路径通过。
- HVD实测证据tick_154767c2/hvd_actual_results/native_smoke.json、resources.json及hvd_actual_independent_review.json有效；不重跑原smoke/resources。原口径9.698045004G对9.762532428G，peak931769344B对936763392B，15%条件未触发；median35.4871对35.8742ms为共享环境观察，非独占性能。
- M231-PSC hierarchy-native-position-feature-cross-scatter-composition仍validation储备：原生叶内坐标×特征交叉散布按真祖先within/between传播，10C→C→C经原HCG单次inst_feats写回。反例仅证明信息差异，不证明效力/novelty。
- PSC同原9blob兼容源0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d，父当前d20；旧a709(parent07ef)/NULL提案保持。47本地+28独立兼容检查已通过，原54软件+22独立源审保持；完整Torch/autograd/native/resources仍NOT_RUN，无新准入/部署/队列。
- PSC兼容证据tick_12e364dc/psc_compatible_source/compatible_source_version.json及psc_compatible_source_independent_review.json。待HVD项目槽自然释放，另存受审实际当轮owner/source/runtime/root/UUID/producer执行绑定，再执行原两自然TRAIN/common-init/原loss/整core更新与同口径资源；不盲ff兄弟提交。

- PSC禁用native/operational软件包已在tick_2e51495f完成45/27实际CPU检查；DRAFT=True/10NULL，无active release/binding/manifest/lease/request/远端stage；完整Torch/autograd/native/resources仍NOT_RUN。复用冻结包，独立软件包审查以该目录审查文件为准。
- 新M232-NSD hierarchy-native-spatial-dirichlet-composition已登记implementation：原fine叶坐标链成对特征差能量→真祖先共享bottom-up analysis/top-down synthesis→原HCG单次inst_feats。41实际stdlib检查及独立200组有理数/源审通过；反例均值/方差/PSC scatter相同而能量8/7与24/7，仅证明信息差异。
- NSD隔离源1fa7d779567b3e10119c63190d2eee16d7fda18f父d20，精确9文件，主线/index/用户文件保持；Torch/autograd/native/resources NOT_RUN，无准入/队列/部署。PSC优先；后续父版本变化须兼容保存同9字节，不盲ff兄弟提交。坐标链非一般旋转不变，效果/novelty UNKNOWN。

## Closed Or Failed Directions
- M206-CGCA、M227-LFT保留waiting/user_paused/dispatch_hold/noPID/resume_authorized=false；M201、旧FCB及历史scope/numerical holds不恢复，不借空卡重开。
- 全部旧失败/negative/unknown、PCE2+extra1/RSTR2预算及已消费HAP授权保持；不借后继改名重开禁用路线，不给未测项代签。

## Running And Queue
- HVD于2026-11-06T13:49:46Z（上海21:49）在epoch5/1449退出，原日志TypeError: argument of type 'MultiheadAttention' is not iterable；根因UNKNOWN，不是自然早停或假设证伪。三次新鲜/proc死亡核验后canonical finalize_task已crashed归档656485273dd0482fb5ec08cef6a68df4，未调用dispatch/crashfix或重启。
- CPU CUDA_VISIBLE_DEVICES=''、map_location=cpu实际核saved best/last均epoch4/best0.4264346659183502/noimp0，未保存partial5；完整原日志已精确拉取。此best为中断训练已保存结果，非完整效力结论。
- 原guardian3024669/start158549879已RELEASED，/proc/locks三锁空；无项目训练在跑。M206/LFT仍人工暂停/noPID/no resume，不算ready。
- 当前main/runtime仍d20、live根Cluster_hvd_20261106、SERVERS SHA6a87d428190d77955500b34d58bff0310eecb13c8b233c7b3e4fd7ef253787a7；旧MIC/NEC/WFC/4457及用户/index保持。PSC最近可原生检查，但本轮剩余时间不足原1020秒run margin，不启动诊断；下轮重新核资源/三锁/UUID与实际当前owner绑定。

## Open Questions And Risks
- HVD实际启动未继承三锁：Bash python()函数不能覆盖closure.safe_launch直接subprocess.Popen(["python",...])的PATH执行。旧Linux CPU proof只证明Bash路径，不能称实际prelaunch锁成功。
- 已完成的是启动后CPU守护修复，postlaunch_correction=true/prelaunch_lock_check_proven=false。既有conda_source shim保留缺陷证据；任何后续新训练启动前须真实可执行PATH包装或FD继承的实际入口证明与独立审查，不能沿用Bash-only证明放行。不自动重启或resume已崩溃HVD。
- 原12e guardian文件CRLF的实际SHA175523fb…与LF绑定83cda708…不一致；其远端启动先在过期deadline拒绝，旧stage实测不存在，无guardian Popen。新20c守护LF字节SHA83cda70864923f77da6ac0d3a69f303dbd257a2396ff2680a0b3f22749851cc4已经实际核验，旧文件与失败证据保留。
- 首次v2 schema拒绝无EXEC/SSH/Popen，v3仅一次实际训练Popen；随后canonical进度核验曾因kill -0拒绝而未确认，已用只读/proc核真并canonical reconcile。未知启动先reconcile，不盲重放。
- 新guardian的当前owner/deadline仅约束其启动，授权生命周期为精确trainer自然退出；后续只读观察，不续写旧lease/binding，不再次Popen。
- SSH仅key/StrictHostKeyChecking，固定dl04-MS-7E06/192.168.1.115/GPU0UUID958e；不读密码文件、不连旧.137、不假设sudo。共享运行计时如实标竞争。

## Last Tick
- 前轮20c已FINALIZED/PASS/context_committed/released，启动后锁修复证据保持；更早12e INCOMPLETE保留，不重放旧owner/binding/NULL。
- 本轮2e51495f07244023946fc53eec6e6d98 generated13:10:54Z/deadline14:10:54Z：完成PSC缺失软件producer/operations及NSD1个预算内独立源准备；0新准入/0训练或GPU检查启动。HVD故障与guardian释放真实记录并canonical归档，非科学拒绝，不自动恢复。
- 审计目录pipeline/diagnostic_bundles/tick_2e51495f，含HVD原生退出/CPU检查点/归档/诊断、PSC双冻结包、NSD原源/独立审/隔离版本与persist_result。report/finish及释放以本轮实际tick_receipts收据为准，不预称成功。
- 下一轮先核故障证据和当前资源，再优先PSC实际原生四臂缺项；不借软件PASS准入。HVD只做CPU根因调查，原last/best及所有人工暂停/bans/原seed协议保持。
