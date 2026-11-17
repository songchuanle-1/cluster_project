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
- M231-PSC hierarchy-native-position-feature-cross-scatter-composition已技术准入/原九文件ff/独立运行目录部署/单次原生训练，现crashed归档，禁止自动重启。真祖先叶内坐标×特征交叉散布within/between传播，10C→C→C经原HCG单次inst_feats；效力/novelty UNKNOWN。
- 实际source/main0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d，父d20eb221eff6584b67d4e9b5673559d0e1cb735b；旧a709/全部DRAFT十NULL母包保持冻结，worker530a5230021fad8d880c37a34c18973b4c556e7dc1536b6c4faaffdd6d6f93d8不变。
- PSC复用tick_0bb87433真实成对TRAIN2/835共同init/自然批指纹/原loss有限backward/coords-cross路径和整core真实更新；候选loss9.213239669799805与13.907380104064941，独立181项核对；旧owner不改签，旧资源候选1020秒门前拒绝保留。
- 本轮另存d20ca92f六字段owner/source/runtime/root/UUID/producer绑定，candidate-first及champion两个完整资源臂真实terminal/rc0；同fixture/count9.827019852G vs9.762532428G，peak932597248B vs936763392B，不触发15%；median37.6625 vs35.9142ms/p90候选81.0253ms为允许共享环境观察，非独占性能。
- mixed-normalizer197检查及独立实际148检查PASS；原始两轮provenance分别保留。canonical receipt pipeline/admissions/M231-PSC.json SHAd0122c5f4389d4966e32f04335b45642be30258ca55bdcb7f6ccd066925585c3，四technical gates通过，不是效力证明。
- M232-NSD resource blocked（resume validation）储备，原隔离源1fa7d779567b3e10119c63190d2eee16d7fda18f父d20保留；本轮同9blob兼容源f6257de79148581334ee495e6e2d60ccb525457c父当前PSC0ccc已保存独审。原fine叶坐标链特征能量→真祖先bottom-up/top-down→HCG单写回。41CPU/独立200有理数检查有效，native/Torch/autograd/resources NOT_RUN。兼容45软件检查和独立审通过；native/Torch/autograd/resources仍NOT_RUN；不盲ff兄弟，不新增凑数。

## Closed Or Failed Directions
- M230-HVD已crashed归档656485273dd0482fb5ec08cef6a68df4；2026-11-06T13:49:46Z epoch5/1449，TypeError argument of type MultiheadAttention is not iterable，train.py129枚举参数；根因UNKNOWN/implementation-inconclusive，非假设证伪，不自动重启/resume。
- HVD完整saved best/last均epoch4/best .4264346659183502/noimp0；partial5未保存，原完整log SHA810eb46d4008d60848b097b9077b15dff826688b75e35435704bc3d48ca2d57a。CPU Torch2.8方法/128次遍历未复现，缺原GPU对象历史，非修复许可，不重复无信息检查。
- M206/M227人工暂停、M201/旧FCB和全部旧scope/numerical holds保持；旧negative/unknown/PCE2+extra1/RSTR2和已消费HAP授权保留，不换名重开bans。

## Running And Queue
- PSC原日志末次写入2026-11-06T18:46:56.833353Z，异常位于epoch2/984；19:12Z实际确认已退出，DataLoader worker0 get_sp_label→Tensor.unique→torch.functional._return_output TypeError: NoneType object is not callable。原生实现/运行故障，根因UNKNOWN，非自然早停或假设证伪，不自动重启/resume。
- 2026-11-06T19:12:45Z起3次实际/proc141056不存在、无项目trainer/context、原三锁自然可用；canonical crashed archive cbed4ef333ad48aaa272ebd303e4ca13，精确原stdout SHA4a456f41cb11f9143111c04b8618b164f1bd3bf84194b88b7675c029ea4ad543和内层原生日志均已保存。
- 原stdout不含mIoU，不能将其0匹配当0验证。内层native log仅1完整验证.3035579323768616；CPU实际best/last均epoch1/best.3035579323768616/noimp0，optimizer+scheduler存在；partial2未保存。v1 numpyfloat32 JSON序列化失败保留，v2仅修记录序列化，未改训练。
- 当前无项目训练；M206/LFT仍人工暂停/noPID/no resume，不算ready。main/runtime0ccc与PSC根保留；SERVERS SHA1f1ba94e90c6f44e2e9cb0e6f1e746568e38cc1e92f398ee49efc5e8c40232bf，原28用户文件/当前index38bc7e2fb40d4ae2727e8cbfdc8bf96ede395855b39ea6c7790eb56e2a908d05保持；所有旧根/checkpoints不动。
- NSD兼容源f625尚未部署。NSD母包native/source静态审通过，但operational/remote_ops错误沿用PSC CANDIDATE，正确NSD binding会Foreign binding；母包/旧activation禁止运行。233项activation增量审未覆盖整体身份，后续负记录5ffa4193…保留旧审不覆盖。无root release/execution目录/远端stage。已另存禁用nsd_operational_prepare_v2，仅改远端CANDIDATE字面量，54实际软件+55独立审通过；FROZEN30225589…、review a6113d17…，完整v1/十NULL/原worker不变。19:31:41Z物理GPU0真实free32514MiB、无context、3locksavailable，仅为当时资源观察，新的GPU工作仍需fresh checks。

## Open Questions And Risks
- HVD旧Bash python()函数未覆盖directPopen的缺陷证据保留；PSC使用原已Linux真实CPU证明的PATH可执行core/factory字节，实际生产source/YAML/interpreter/UID/原3dev+inode/完整图已另存并独审，原proof未重做。
- PSC生产图result SHA8b9743cd6db9432a0dd584edc0288dc6f35a54ea994a2dd9bbca1adca5f8cd41，independent b1c1412d89d46dc591919ff7cc2a0e720cfa9ea9ba87394e9d876628eba13a8a。当轮启动前free32509MiB及实际trainer持3FD/kernelFLOCK证明历史有效；本轮精确trainer已退出，锁自然释放。
- 保留旧CRLF mismatch、过期owner、未加锁负证据与所有partial；新owner不续写旧lease/不补签NULL。生产shim d20ca92f的18:08Z deadline已过期，不得重用或续签；NSD新诊断须另外审绑定原始baseconda源6c80…并明确diagnostic-only，不经旧shim、不修改SERVERS来假装续期。
- SSH key/StrictHostKeyChecking，固定songcl@192.168.1.115、dl04-MS-7E06、GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c；不读密码/连旧.137/假设sudo。不将共享计时或技术准入当效力。

## Last Tick
- 当前0fe5b17c391841008a5bf1193377d60a generated2026-11-06T23:18:30.392471Z/deadline2026-11-07T00:18:30.392471Z，原1020秒run余量不改。前eb827823已实际核验FINALIZED/PASS/context_committed/released，无旧lease。
- 本轮23:19:39Z固定server4/GPU0 UUID/runtime0ccc实际free530MiB，外部PID1471059占用31976MiB；无本项目trainer，原training/diagnostic/exclusive三锁available。仅低于原20000MiB预算阻塞，外部共享仍授权，context/util不独立阻塞，不发信号/改资源。
- NSD继续resource blocked/resume validation，retry2026-11-07T00:19:39Z；fresh free>=20000、项目max1/原三锁及原1020秒run余量满足后，再另存受审实际新owner/source/runtime/root/UUID/producer/baseconda执行绑定。不续旧lease/不补旧NULL/不盲重放。
- 本轮直接复用旧已审sourcef625/原cd1cbworker/correctedv2。eb activation FROZENe83ecaff…/review db5bac5c…275软件审；禁用生产包236fe5ee…/9b9e2a67…及review0ffaf58c…61；normalizer1242bf3d…/reviewbbe39b42…44+49，均仅软件准备。无新release/prepare intent/manifest/lease/request/stage，native/resources/真实四臂结果仍NOT_RUN，不重制冻结包。
- 旧M220-DCE重复路线筛查不重做；未出现新的实际诊断或可辩护独立机制，不为储备额度新增candidate或M233占位。HVD原128CPU无信息诊断不重复；PSC/HVD已归档不重启，M206/LFT人工暂停与全部holds/bans不变。
- 独立代理只读核对本轮资源owner与旧activation27/normalizer6文件锚保持，未重跑旧套件/SSH/GPU；当前无可执行新GPU检查。normalizer旧eb owner不可直接消费未来结果，须另存受审新tick元数据。
- 本轮实核主线0ccc、28用户文件/当前index/WFC/LFT源与SERVERS/goal等固定配置保持；protected_assets.json明确旧baseline适用范围。报告/finish及context提交/lease释放等待本轮实际收据，不预称成功；释放后不改共享记录。
