# Codex Research Memory

## Goal And Phase
- 仅cluster_project；最新授权仅server4物理GPU0/UUIDGPU-958e741a-e5cf-127e-ffe8-9b984e1f404c，可与外部任务共享。max_tasks_per_gpu1/启动free>=20000MiB/三协作锁保持，不要求空卡或低利用率。GPU1/其他服务器禁用，M206/M227独立人工暂停，不自动恢复。
- 原目标.5100，M95冠军.5020/baseline.4894；原YAML/data/seed1999/epochs50/max_iters70/patience10/loss/optimizer/precision/10G及条件15%显存规则保持。全部bans/Phase1禁调参/Phase2人工保持，不驱逐、信号、重启、迁移已有或外部任务，不改调度。
- Pipeline-cluster_project Disabled；owner thread01a159c5-29ab-7a22-ba7f-e79174757253；canonical前台/python -B/PROJECT_ROOT=D:/project/PYTHONDONTWRITEBYTECODE=1。

## Champion And Baseline
- M95 .5020保持。WFC原生epoch30/noimp10早停，exactbest.49711745977401733/archiveead6b5a9edf2466ea96e2587c931c865；last非epoch30，不重启。
- NEC原生epoch23/noimp10早停，best.49454113841056824@13/last22/archive35d448b2c70544049fa18e199081d30d，不重启。
- MIC原生epoch26/noimp10早停，best.49881425499916077@16/last25/archived03c21a094d54ed0b17a50cc21deeeb7；旧.4990舍入修正保留，不重启。

## Active Hypotheses
- M234-RVE稳定ID fine-leaf-receiver-conditioned-vector-exchange，当前source d21477b0、已canonical准入/原owner真实同步保留；本轮另存新owner ee6f5eda只读验证和CPU生产render通过。部署/启动状态见Running And Queue；效力/novelty UNKNOWN。
- 新路径在原fine-leaf边上先做receiver-relative-donor向量GELU再mean；K32/H8/原tie fallback、中粗层/HCG/CSORT/singleinst/全部训练数值保持。独立排重和源码复核通过，效力/novelty UNKNOWN。
- RVE原CPU8cases保持有效。r0 common841/252值不同失败保留。本轮r1构造对照5初值完全不变/调用方RNG恢复；common841实际全部相等，原两自然TRAIN/loss/backward/AdamW及5core两步更新通过。资源9.66779702G/median86.844/P9091.400ms；效力/novelty UNKNOWN。
- M233-NDE稳定ID hierarchy-native-distribution-embedding-composition，complete/crashed；精确source0747f6acec1c61018ec99acf2efa5329c9b3523c。效力/novelty/长期稳定性UNKNOWN。
- 原46版本10.036472908G>10G失败完整保留。revision1于2026-11-08 01:23:19Z预注册，仅distribution_embedding首analysis affine按唯一parent分解，保持参数/state_dict/RNG/childwise GELU/second Linear/private mean/raw bank/HCG/writeback，不是新机制或调参。
- revision1已passed且immutable，digest3edbff4aa35f05a36da799b23cb54e154e6387faa30b1953a659b47267ccf9e2；canonical receipt52bf897dc89729063ffb429035b1cd07f14d3ea8d3e690812a4e3adfb48ed266。不得再改最终revision的evidence/result_evidence；新证据只加candidate外层。
- 原71champ+f653candidate TRAIN2/common835/有限backward/整core更新、5287champ+ec资源及801d修复core EQ/430归一化和独审复用原owner/hash，未重复测/补签。candidate9.930828876G/peak932033536B过原门；median196.958ms慢于champ70.427ms但外部context不同，不作因果解释。full optimizer训练峰值/no-cluster增量UNKNOWN。
- 构造core EQ52正比较/2错误parent负对照/原YAML AdamW/RNG恢复通过，仅core，不证明full task-loss等价或效力。

## Closed Or Failed Directions
- NSD M232 archive4c26231600b04e3ca7126aa32d869e02，partial epoch1/1961 of4686、完整epoch/验证0、无pth、bestUNKNOWN；自然退出，不重启。原self.cuda/Module._apply Torch异常根因UNKNOWN，不是机制证伪。
- HVD M230 archive656485273dd0482fb5ec08cef6a68df4，partial5/1449，完整saved4/best.4264346659183502；PSC M231 archivecbed4ef333ad48aaa272ebd303e4ca13，partial2/984，完整saved1/best.3035579323768616；均不重启，Torch根因未修复。
- 全部旧scope/numerical holds、M201/旧FCB、PCE2+extra1/RSTR2及已消费HAP授权保持；不得改名重开bans。M206/M227人工暂停保持。

## Running And Queue
- M234 queue实际status=waiting；dispatch_hold=Tested r1 technical admission; dispatch held for detached d214 source resolver, canonical safe sync and fresh production activation/shim/source-runtime validation. No training launch until those production prerequisites are verified; this is not a physical GPU resource hold.；launch_verified=False。
- 截至本草稿时间，canonical dispatch记录不存在；不声称训练已启动。
- runtime根/data/songcl/Project/Cluster_project/Cluster_nsd_20261107，实际HEAD d21477b0；main0747/index/user28/r0九文件保持。558旧sync22fb0e59保留原owner，不重放；ee6当前验证951e2e93是只读复核。
- SERVERS实际conda_source=/data/songcl/Project/Cluster_project/pipeline/runtime/nde_path_prod_8a3431fa/conda_source.sh，SHA=62e4595edb002ed4c1340372ef2afc3d5dc9ba75a2a40f74b6752db61cbad9b3；只以真实switch结果/当前bytes为准。M206/M227独立人工暂停授权保持。
- 新生产stage /data/songcl/Project/Cluster_project/pipeline/runtime/rvec_path_prod_ee6f5eda；CPU render时marker未消费/未启动训练。之后是否消费仅以实际marker/PID proof为准。
- 实际observer增长=False；早期步数不证明完整epoch/验证、最终效力或长期稳定性。

## Open Questions And Risks
- M233完整训练结果、验证指标、泛化、novelty、长期稳定性未测；早期步数只证明启动和进度，不证明效果。
- 历史NSD/HVD/PSC的Torch失败未解释，不用CPU provenance或当前短期健康冒充修复。保留原46超10G、f653 SIGSEGV、旧EQ harness失败、非复现、旧shim过期和所有失败独审。
- 前轮派发前YAML检查先误要求提前adapt，独审真实拒绝原packet。新独立包仅允许精确原commit YAML或已认证canonical preview，最终生产入口仍强制适配SHA，原safe_launch负责实际适配。非模型revision2。
- SSH仅key/StrictHostKeyChecking，pinned songcl@192.168.1.115/dl04-MS-7E06；不读密码/连旧.137/假设sudo。旧NSD消费shim及所有过期lease/intent禁止重放。

- 本轮read-only验证复用旧sync，不是新sync；CPU stage/collect/render及identity-only UUID不能冒充GPU occupancy/resource PASS、长训练或步数增长。所有新声明必须取实际dispatch/proof/observer artifact。

## Last Tick
- ee6f5eda，快照2026-11-09T07:10:46.030397Z，原deadline08:10:46.030397Z；本草稿as-of 2026-11-09T07:57:31.621749+00:00，仅tick-local，shared memory/work未由作者修改。
- 当前只读source验证951e2e93通过，kind CURRENT_READONLY_VERIFICATION_REUSE_OLD_SYNC_NOT_NEW_SYNC，保留旧sync22fb0e59原owner。
- 新stage c7a13282 / CPU collect0250ea6a、resultf6b321a3、独审39bef064通过；root activation4906c93a仅授权render，training_launch_authorized=false。
- 实际render38519c30/result735fd2e8通过，固定bindingb9a56ca3、entrybc455767、corec0857d0b；真实PATH/conda CPU验证，render本身未训练/未消费marker。实际生产独审/切换/hold-clear/dispatch若稍后执行，必须刷新本草稿，不预写成功。
- 已passed RVE revision1 canonical digest daaf3041ebd3a9beacf487c60346d214374fd81a9a9411379801232e4450377f保持；新证据仅加candidate外层，不改revision evidence/result_evidence。native841 exact/common 与历史835不同scope；不重测有效门槛。
- 下一步：Require actual rendered-production peer PASS, conda_source-only switch, clear only M234 setup hold, canonical one-shot dispatch and factual PID/marker/lock/native step growth before any training claim.
