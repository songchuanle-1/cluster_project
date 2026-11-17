# Codex Research Memory

## Goal And Phase
- 最新直接用户2026-11-04授权server4物理GPU0启动/继续及外部共享；authorizations/server4_gpu0_overlay_20261104.json SHA783ffc27d48872940c2e15adcb85f6bb5f9b94492a8abd88694799f483d20e88。allowed_gpus=[0]/dispatch_enabled=true/allow_external_overlay=true/max_tasks_per_gpu=1/原task_memory_mb=20000；真实剩余显存须满足原预算，不要求空卡或低利用率，不重复询问许可。
- 保留training/diagnostic/exclusive三协作锁。GPU1/其他服务器禁用，M206-CGCA/M227-LFT人工暂停/noPID/resume_authorized=false；不驱逐、发信号、重启/迁移已有或外部任务，不改调度/目标/bans。Pipeline-cluster_project保持Disabled。
- Phase1目标.5100，冠军M95 .5020，baseline .4894；原YAML/data/pretrain/loss/optimizer/precision/seed1999/epochs50/max_iters70/patience10/10G和conditional15%显存规则不改。不加FP32/逐参数非零/minimum-effect门，Phase2人工。

## Champion And Baseline
- M95 .5020保持；WFC(M226)原生epoch30/patience10自然早停，精确best .49711745977401733，archive ead6b5a9edf2466ea96e2587c931c865；last不称epoch30，不重启。
- NEC(M228)原生epoch23/noimp10自然早停，best .49454113841056824@13；archive35d448b2c70544049fa18e199081d30d，last22；不重启。
- MIC(M229)原生epoch26/noimp10自然早停，best .49881425499916077@16，last25；archived03c21a094d54ed0b17a50cc21deeeb7；原generic .4990舍入校正保留。不重启。

## Active Hypotheses
- M231-PSC hierarchy-native-position-feature-cross-scatter-composition本轮已技术准入/原九文件ff/独立运行目录部署/单次原生训练启动。真祖先叶内坐标×特征交叉散布within/between传播，10C→C→C经原HCG单次inst_feats；效力/novelty UNKNOWN。
- 实际source/main0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d，父d20eb221eff6584b67d4e9b5673559d0e1cb735b；旧a709/全部DRAFT十NULL母包保持冻结，worker530a5230021fad8d880c37a34c18973b4c556e7dc1536b6c4faaffdd6d6f93d8不变。
- PSC复用tick_0bb87433真实成对TRAIN2/835共同init/自然批指纹/原loss有限backward/coords-cross路径和整core真实更新；候选loss9.213239669799805与13.907380104064941，独立181项核对；旧owner不改签，旧资源候选1020秒门前拒绝保留。
- 本轮另存d20ca92f六字段owner/source/runtime/root/UUID/producer绑定，candidate-first及champion两个完整资源臂真实terminal/rc0；同fixture/count9.827019852G vs9.762532428G，peak932597248B vs936763392B，不触发15%；median37.6625 vs35.9142ms/p90候选81.0253ms为允许共享环境观察，非独占性能。
- mixed-normalizer197检查及独立实际148检查PASS；原始两轮provenance分别保留。canonical receipt pipeline/admissions/M231-PSC.json SHAd0122c5f4389d4966e32f04335b45642be30258ca55bdcb7f6ccd066925585c3，四technical gates通过，不是效力证明。
- M232-NSD implementation储备，隔离源1fa7d779567b3e10119c63190d2eee16d7fda18f父d20；原fine叶坐标链特征能量→真祖先bottom-up/top-down→HCG单写回。41CPU/独立200有理数检查有效，native/Torch/autograd/resources NOT_RUN。main已0ccc，未来先兼容保存并独审原9字节；不盲ff兄弟，不新增凑数。

## Closed Or Failed Directions
- M230-HVD已crashed归档656485273dd0482fb5ec08cef6a68df4；2026-11-06T13:49:46Z epoch5/1449，TypeError argument of type MultiheadAttention is not iterable，train.py129枚举参数；根因UNKNOWN/implementation-inconclusive，非假设证伪，不自动重启/resume。
- HVD完整saved best/last均epoch4/best .4264346659183502/noimp0；partial5未保存，原完整log SHA810eb46d4008d60848b097b9077b15dff826688b75e35435704bc3d48ca2d57a。CPU Torch2.8方法/128次遍历未复现，缺原GPU对象历史，非修复许可，不重复无信息检查。
- M206/M227人工暂停、M201/旧FCB和全部旧scope/numerical holds保持；旧negative/unknown/PCE2+extra1/RSTR2和已消费HAP授权保留，不换名重开bans。

## Running And Queue
- M231-PSC实际server4物理GPU0/PID141056/start160474755，root/data/songcl/Project/Cluster_project/Cluster_psc_20261106/source0ccc；log logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_psc_20261107_020327.log。
- 2026-11-06T18:05:08.700504+00:00核原生TRAIN [1, 107]→[1, 115]，canonical launch_verified=true；同trainer实际三原inode FD继承和kernelFLOCK均核实。精确PID/source/marker保持，不重放。
- SERVERS现仅server4 code-root和受审真实PATH conda_source切换；SHA1f1ba94e90c6f44e2e9cb0e6f1e746568e38cc1e92f398ee49efc5e8c40232bf，其他配置/资源/调度不改。原28用户文件和既有index entries保持，ff只新增原PSC9文件。
- HVD/MIC/NEC/WFC94/旧4457运行目录/源码/checkpoints保持。HVD旧guardian已随退出自然RELEASED；M206/LFT仍暂停，不算ready。

## Open Questions And Risks
- HVD旧Bash python()函数未覆盖directPopen的缺陷证据保留；PSC使用原已Linux真实CPU证明的PATH可执行core/factory字节，实际生产source/YAML/interpreter/UID/原3dev+inode/完整图已另存并独审，原proof未重做。
- PSC生产图result SHA8b9743cd6db9432a0dd584edc0288dc6f35a54ea994a2dd9bbca1adca5f8cd41，independent b1c1412d89d46dc591919ff7cc2a0e720cfa9ea9ba87394e9d876628eba13a8a。实际启动前free32509MiB、max1/UUID/三锁，实际trainer持锁证明见psc_postlaunch_observation.json。
- 保留旧CRLF mismatch、过期owner、未加锁负证据与所有partial；新owner不续写旧lease/不补签NULL。生产shim当前deadline仅允许本轮新启动，已运行trainer持锁到自然退出；以后不得重用过期shim启动新任务。
- SSH key/StrictHostKeyChecking，固定songcl@192.168.1.115、dl04-MS-7E06、GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c；不读密码/连旧.137/假设sudo。不将共享计时或技术准入当效力。

## Last Tick
- 当前d20ca92f1b654e24ba9cf29f634307b7 generated17:08:14Z/deadline18:08:14Z，未延期；前0bb已FINALIZED/PASS/context_committed/released。
- 本轮0新候选、1技术准入/入队/真实训练启动；PSC资源双臂/独立审/实际PATH生产部署与3FD-FLOCK/原生步数已通过。所有证据在tick_d20ca92f，旧NULL包与旧owner完整保留。
- 下一轮先观察同一PSC训练/验证/终态，不重复启动；项目max1期间仅预算内非GPU准备。NSD需实际父0ccc兼容后再补真实缺项。HVD不重启，所有holds/bans不改。
- report/finish及lease释放以当前真实tick_receipts收据为准，不预称成功；释放后不改报告/记忆。
