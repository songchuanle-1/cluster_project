# Codex Research Memory

## Goal And Phase
- 最新直接用户2026-11-04授权server4物理GPU0、启动、继续，明确“可叠加在他们的任务上  显存够用”。共享授权pipeline/authorizations/server4_gpu0_overlay_20261104.json保持；allowed_gpus=[0]/dispatch_enabled=true/allow_external_overlay=true/项目max1/原task_memory_mb=20000，保留training/diagnostic/exclusive三协作锁。
- Phase1目标mIoU .5100，冠军M95 .5020/baseline .4894。原YAML/data/pretrain/loss/optimizer/precision/seed1999/epochs50/max_iters70/patience10、10G与原conditional15%显存规则/bans不变；不增FP32、逐参数非零或minimum-effect门，Phase2人工。
- GPU1和其他服务器禁用，M227-LFT、M206独立人工暂停保持；不驱逐、发信号、重启或迁移已有/外部任务，Pipeline-cluster_project保持Disabled，不改目标或调度。

## Champion And Baseline
- 冠军M95 .5020保持。WFC(M226)原生epoch30/noimp10自然早停，精确完整best .49711745977401733；归档ead6b5a9edf2466ea96e2587c931c865及精确校正保留，不重启，不称last为epoch30。
- NEC(M228)原生epoch23/noimp10自然早停，23完整val，精确best .49454113841056824@epoch13；归档35d448b2c70544049fa18e199081d30d，best checkpoint13/noimp0，last22/noimp9（break先于save）。低于冠军，仅本实现本seed结果，不重启。

## Active Hypotheses
- M229-MIC hierarchy-ancestry-mobius-interaction-composition：已完成实际原生两自然TRAIN批/common-init/有限原loss backward/整core更新及路径执行、完整原口径资源与独立复核，已技术准入并部署/入队，已在tick_fd2aae2a由canonical preflight于server4物理GPU0启动，现已自然终态complete，历史PID2881795/start152216088；精确best.49881425499916077@16，terminal26/noimp10，last25。效力跨seed/population及novelty未证。
- MIC receipt pipeline/admissions/M229-MIC.json SHA b7cb59e0b78ae81f4b3dec9dd5b40a19b1797cb4a0902e704918eb6ff7f3ff40；完整证据tick_3b2b394d/mic_native_smoke.json、mic_resource_comparison.json、mic_constraints_independence.json、mic_actual_independent_review.json，不重跑旧smoke或重制冻结包。
- MIC835共同参数tensor/155907386参数初始化一致；champion losses9.52912425994873/13.909585952758789，MIC8.9503173828125/13.903985023498535。FLOPs9.724783692G对9.762532428G；峰显存−0.645%，原15%条件未触发；median36.88871465ms对35.38573999ms，+4.247%，异时共享观察，不称独占性能。
- M230-HVD hierarchy-native-variance-decomposition-composition已真实native/resources通过、正式技术准入并部署入队，waiting受启动三锁继承验证hold。真实祖先within/between方差分解→共享4C→C→C→原HCG单次inst_feats写回；原29软件项与后续21/26禁用包软件审保持，不代表forward/Torch/autograd/效力/novelty。
- HVD在tick1138a3fc以独立index保存同九blob兼容源d20eb221eff6584b67d4e9b5673559d0e1cb735b，父当前MIC07ef；实际8Python语法/九新增路径/原字节及独立源审通过，未晋升主线、未部署、非模型修订。原e38d92db(parent6bc)和全部NULL母包/冻结worker保持。
- HVD冻结native/operational包仍在tick_c7451cf1，最终worker f91bddf7；旧绑定e38/6bc/NEC根不可执行或补签NULL。未来真实显存/槽位许可后另存受审owner/source/runtime/root/UUID/producer绑定，先原TRAIN2及完整资源实际通过再准入。

- M231-PSC hierarchy-native-position-feature-cross-scatter-composition在tick_0f3c54ec登记validation储备；原生叶内坐标×特征有符号交叉散布按真祖先within/between传播，10C→C→C经原HCG/单次inst_feats写回。54实际stdlib/AST/有理数软件项及22独立审通过；反例只证明信息路径不同，不证明人口瓶颈/收益/新颖性。
- PSC精确8model+原字节YAML另存隔离源a709fe0cf93690d0695fd9d9a6f6e0e865340a7a，父07ef；主线未晋升，旧NULL提案/FROZEN保持，Torch/autograd/native/resources NOT_RUN，无准入/队列/训练。原检查器文本query假阳性及AST纠正证据保留；后续原精度有限协方差/两自然TRAIN/资源真实检查，先HVD。

## Closed Or Failed Directions
- M206-CGCA、M227-LFT保持原waiting/user_paused/dispatch_hold/noPID/resume_authorized=false；M201、旧FCB及历史scope/numerical holds不恢复，不借空卡重开。
- 全部旧失败/negative/unknown、PCE2+extra1/RSTR2预算及已消费HAP授权保持；不借MIC/HVD改名重开禁用路线，未测结果不代签。

## Running And Queue
- 2026-11-06 03:07:31北京时间在tick_fd2aae2a由canonical preflight真实启动原waiting的M229-MIC，PID2881795/start152216088；原生日志logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_mic_20261106_030700.log，verified training_progress。M206/LFT暂停保持，无重复/未知启动。
- 当前本地主线Cluster实际HEADd20eb221eff6584b67d4e9b5673559d0e1cb735b，live SERVERS根/data/songcl/Project/Cluster_project/Cluster_hvd_20261106；SERVERS SHA84730b8f91db3022d2e1819362d803b20293ea6224cfa9d607b8d4e45e8f43c0。用户原文件及完整index保持，本轮实际20个dirty-path哈希与0f3/1138证据一致。
- 已验证部署证据tick_3b2b394d/mic_runtime_deployment.json SHA6f526352e2d9c356d3a3142398705813208bbcf1cb3cb8a99550bfa15e076ff8；旧NEC6bc、WFC94及4457目录/源均保留，不全局替换历史版本。
- 2026-11-06T07:14:56.367090+00:00（北京时间11月06日15:14）同PID2881795/start152216088/cwd/argv/stdout/source07ef核真；原生TRAIN epoch25步数3272→3276/4686，未见fatal标记，guardian3033165/start152434416仍持三把内核锁。GPU0context2881795/19752MiB，训练后余12802MiB；不是启动前显存证明。
- 本轮preflight报告epoch25/50，最近阶段验证舍入值0.4953/0.4950/0.4901/0.4880/0.4867，阶段best0.4988/noimp8；不是终态精确best，不作效力/novelty结论。
- 原生canonical入口未持三锁，19:20/19:22观察缺锁；已在启动后补CPU guardian3033165/start152434416，真实/proc/locks证实training/diagnostic/exclusive三FLOCK归guardian持有。精确trainer自然退出后pidfd释放锁，无GPU/信号/重启/调度。启动前锁检查未证实，禁止倒签。

## Open Questions And Risks
- MIC已自然完成且原guardian已RELEASED；HVD已准入部署，当前启动保护缺项见Last Tick。无须再问共享或启动许可。canonical在fd2启动前数值显存未留原始快照，按既有20GB选卡条件执行，不能补造数字。
- MIC完整技术准入不证明效力/新颖性；HVD兼容源保存不证明原生训练或资源通过，主线现HVDd20。储备源变更前先兼容复核同9字节，不盲ff兄弟提交。
- 旧3b2 dispatch v1/v2为schema/depth本地拒绝，v3在过期owner前拒绝；无request/无Popen，保留负证据，不用过期token重放。未知启动须先reconcile。
- SSH只用key/StrictHostKeyChecking及固定dl04-MS-7E06/192.168.1.115/GPU0UUID958e；不读密码文件、不连旧.137、不假设sudo。授权内SERVERS_after_sha为历史指纹，不要求回退。
- guardian的fd2 owner/deadline仅用于当时启动检查；其授权生命周期是精确trainer自然退出。后续仅只读观察既有守护，不更新旧lease、binding或再次Popen。

## Last Tick
- 当前owner154767c278664ba4a7b666c69f12abaa generated2026-11-06T09:12:59.944792+00:00/deadline2026-11-06T10:12:59.944792+00:00；据实际report/finish收据核验，不预称成功。前轮ee0a已FINALIZED/PASS/released。
- MIC已canonical三次死亡确认自然早停，archive d03c21a094d54ed0b17a50cc21deeeb7；26次完整val、best.49881425499916077@16/noimp10，last checkpoint25/noimp9；低于M95.5020，不重启。CPUcheckpoint与原生日志证据mic_native_terminal_metrics.json；保留generic归档.4990及校正历史，未虚构log_local。
- HVD原两自然TRAIN/835共同init张量/批指纹/有限原loss backward/整core更新、四臂完整资源已执行；54标准化+86独立复核通过。9.698045004G，peak931769344B对936763392B，median35.4871对35.8742ms；共享许可计时，原15%条件未触发，非效力/novelty证明。
- 收据pipeline/admissions/M230-HVD.json；已ff-only07ef→d20、独立Cluster_hvd_20261106部署及SERVERS唯一root切换，旧MIC07ef/NEC6bc/WFC94/4457源保持，用户20文件/旧index条目保持。证据hvd_runtime_deployment.json；SERVERS当前SHAade9c6da789a74fd9bf9b450e0e86a05a7ef38862ed9012c3f814efe8966ecfa。
- HVD已waiting入队，dispatch_hold为原三锁必须由训练进程从启动继承的Linux实测尚缺；仅新shim草案bash语法通过，CPU继承锁proof NOT_RUN，root剩余时间预检查在SSH/Popen前拒绝，无未知启动。证据hvd_launch_protection_pending.json。不是缺用户共享或启动许可。
- 下轮优先复用完整实测，另存当轮执行绑定并审查/运行CPU proof、精确HVD argv路由/受限conda_source切换，再核实时GPU0显存>=20000/max1/UUID/三锁，解除hold后canonical派发并核验原生步数。旧owner/lease/manifest不能重放，禁止再跑完整native/resources。
- PSCa709仍父07ef、原源/证据保持，未来检查前须按实际d20父兼容保存同9字节并复核，不盲ff兄弟提交。本轮无新候选/0训练启动/1技术准入；M206/LFT暂停及全部bans/原seed协议/目标/调度保持。
