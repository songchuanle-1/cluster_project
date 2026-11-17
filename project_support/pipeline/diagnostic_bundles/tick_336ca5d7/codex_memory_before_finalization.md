# Codex Research Memory

## Goal And Phase
- 最新接管06a28ff5b75f44a2a8ae1be627d90aec；actual owner/target=01a159c5-29ab-7a22-ba7f-e79174757253一致；generated2026-10-25T14:03:54.140252+00:00/原deadline2026-10-25T15:03:54.140252+00:00不延长。前8878已核FINALIZED/released、lock/pending消失后begin；本轮真实finish以receipt为准，不预签。
- goal0441fecda…；ScanRefer目标.5100、M95最佳.5020/gap.0080、baseline.4894。Phase1 hierarchy→inst_feats→query/masks，supervision辅助；Phase2仍需人工确认。
- 原seed1999/epochs50/maxiters70/native YAML/data/optimizer和10G原口径、资源bs1/lang1/warm20/repeat100、显存+15%条件保持。禁调参/gate/语言路由/大QKV/pointN²/重复注入/新残差/纯缩放/旧rejected改名。
- standing experiment_first_20261021.json SHA2e892959…覆盖常规实现/实测/相关版本/安全同步/准入训练；不授旧hold重开/额外修订/受保护恢复/扩资源/改调度。
- 最新人类“server4 GPU1也可以用了”：pipeline/authorizations/server4_gpu1_20261025.json SHA90f8820a…，SERVERS d5277972…允许physical[0,1]/每卡max1，替代旧GPU1释放限制；M206暂停仍保留。其他服务器无allowed，Windows Pipeline-cluster_project Disabled。

- 2026-10-25用户询问当前创新设计：已说明BFC/CTS只改中层，fine/coarse沿用M95，按层分工的完整注意力设计尚未落地，新颖性/收益未证。此问答未改变项目目标、资源、暂停、授权或候选创建预算。

## Champion And Baseline
- M95仍.5020；M205-MDC自然earlystop26/.4872，M207-HAP授权epoch18恢复后earlystop31/.5002，M208-HRC自然earlystop31/.4901，M209-PSBR自然earlystop23/.4969，M210-PSNC自然earlystop31/.5001；均未超M95，不调参重跑，不整体否定hierarchy机制。
- HAP原19轮DataLoader AttributeError根因UNKNOWN，epoch18授权已消费非再次restart许可；原crash/snapshot/prior_runs和完整日志/archive保持。
- PSBR完整原log30,985,906B/0204be90…在tick_a4f73140；PSNC完整原log在tick_ddb531fb/psnc_native_earlystop_log_evidence.json，本远SHA一致，canonical归档与source43/receipt406e…保留。

## Active Hypotheses
- 4694轮已推进既有CTS而非新增候选：禁用native包 pipeline/diagnostic_bundles/tick_4694ba96/cts_native_prepare/preparation.json SHAff7fb7a65999369f277744828598822883a222a10ce1ef02732aafeb561fb2cf；独审 pipeline/diagnostic_bundles/tick_4694ba96/cts_native_preparation_independent_review_v2.json SHA7edea74d7aefa2b09ff5e6695992b1f702518c0d47715840d9e890062389bcbf。实际本地syntax/observer/拒绝入口检查已完成；DRAFT=True、10active与code/parent仍null，资源函数沿用原口径，非Torch/native/效能证明。原bfab9源与7036协议不变；无adapter/实际binding/版本/receipt/queue。
- 新准备M214-CTS stable hierarchy-parent-cyclic-triadic-state-composition，tick_3824d9c9/new_candidate_prepare/preparation.json bfab01a3…14map/8独立模型+原字节YAML9源；code_commit/source_commit/futureparent均null，不造Git/version。参考base11a不是未来父提交，实际native-ready时按兼容current main选父并验证同9blob，避免与BFC48fc兄弟提交ff分叉；现stageimplementation/source-tested储备。
- CTS按原true-support父组detached xyz+ID成环，每round同步旧own/+3^r/−3^r经共享3C→C+原GELU，最小3^k≥n轮，重叠receiver而非BFC disjointpair双输出。−邻与+邻同realID则−slot私有0，不复制token；n1W[x,0,0]，n0unsupported/pad delta0，原LN/cfskip/finecoarse/FPS/rawmean/IDs/CSORT/HCG/单inst不变。明确dense3tap dilated circular Conv1D家族，非novelty/newfullparentcoverage/单因素收益；MDC一跳6方向depthwise+pointwise旧结果不重开。
- CTS实际首轮264384作者stdlib断言/136完整oracle cases+14非法拒绝；独立生产plan+forward controlflow列表替身n0..128/25特殊/16非法/多batch及37类别集成，3de1e79f…；PCE21项集成成本审dcb3f3d7…；没有Torch/tensor/GELU实际数值/原生/资源证明。额外ring/circular/stencil/conv1d等有限metadata搜索无同声明，不是全史或论文查重。原cap64未改，n65..128仅testcap128。
- CTS196864参数替525568(−328704)，DP64任意分组最多256receiverrows/4round、linear50,331,648 vs33,554,432/Δ16,777,216 MAC均仅源上界，非fullFLOPs/10G PASS。未来原TRAIN2需实际3distinct/multiround/r≥1 dilation，3个W input块每step原loss有限非零grad+实际更新；alias/n1/pad计数未行使则NOT_EXERCISED，percall零合法，不换样本/seed/precision/阈值。全部native/资源/效能UNKNOWN；4694已备禁用worker，实际lease/receipt/queue仍无。
- 3824仅重绑BFC checker/admit/history至本tick目录，prep d16808a8…，reviewer/history原字节，admit仅TICK常量、全部函数AST不变，13有界检查+缺输入真实拒绝，不重跑42/61。sourceff/dispatch V1 82d11e…发现2个未执行lifecycle guard宽点，原稿/224477ac…保留；V2 957d9b00…8map及独审91618948…修成strict旧GPU/source/receipt/PID/running-map与explicit done_complete/earlystop，11逻辑+43定向拒绝仅stub，三锁holder AST原样。仍总开关False、4实际reviewrefs None，无actual4或操作；未来须真实结果+fresh owner明确物化，不借准备时间授权。
- 3824轮BFC原NoTransport guard在真实3824 owner/context下再核两registered忙卡和14非法入口，0transport/process/network/torch/activebinding。另真实只读Adapter probe0于08:11:54UTC：UUID0原BTC context19726MiB/idleFalse，3locks available不等于空卡，公共HEAD11a，无BFC执行目录或lease。BFC源码/8512/48fc/8839和协议完全不变，当前优先等真实空卡再原生验证，CTS第二储备先保留源9而不造版本。
- 64ac完成BFC完整静态catalog：bfc_operational_prepare outerd7880522…31map/native0c50b957…14map/template4d9caaab…12diag、adapter56235653…/remotef3a360b2…/release95a2e8bc…；worker883925原字节，runtime原13203仅DRAFTTrue→False成f7cdf6e7，原727b包不改。10active仍null，外锚/root release同reviewed template，源/模型/协议无变，非资源许可或native PASS。
- BFC最终61离线suite run2 0e94d8d7…PASS、0真实process/network/torch；原run1 61PASS及code/fixture preimages保留，不重标成当前新code证据。公开prepare/probe强化None/bool/str/非0,1早拒绝；probe额外遵守live whitelist，旧status/reconcile只读语义保留。独审6a55ae95…62本地项，仅静态。
- 当前真实owner/context/外锚guard通过，NoTransport prepare0/1均因registered任务在probe/dir/manifest/lease前拒绝，14非法入口和原deadline负例通过；proof bfc_actual_local_guard_integration.json，0transport/process/network/torch或活动binding。只证明真实本地guard，不代签实际assets/硬件idle/native；late双run原生增长表明工具就绪后仍无空槽。
- BFC结果review/admit/history草稿prep c42f8c19…13map，checker cb245895…/admit442b75f6…/history17c44a96…；10组件/静态和42负例通过，旧harness failure及modeguard改前文件保留，独审f38292d4…。实际4raw缺失即拒绝，默认只读，需真实来源/原6owner/独审/原资源及canonical预算才可--execute-root。允许某旧job自然归档后准入，同时保存现存BTC/BCR行、exp/receipt及M206 pause；无actualreport/标准PASS。未来owner需显式重绑草稿，旧deadline不延长。
- 已备M213-BFC stable hierarchy-parent-butterfly-token-composition，原sourceprep tick_ab7e46d4/new_candidate_prepare/preparation.json 8512a69d…16map/9sourceconfig、原code_commitnull保持；真实isolated_versions/bfc_ab7e46d4版本48fc302c3c02ffef0b241be3593c386b6b65a72e单亲11a，仅9新增。source版本proof78a56a70…/独审6c366938…，primary/runtime11a、28status+bytes/index及11账前后不变。
- BFC仅原middleFFN改为同父true-support几何排序、共享2C→2C+原GELU的bit-up/down互不重叠双输出交互，每stage同步读旧state并保留n个C状态、原ID逆散。非2幂只用真实行、不造pad叶；n1同W[x,0]取前C，n0/unsupported/pad delta0。原LN/cfskip/fine-coarse/rawCSORT/FPS/HCG/单inst保留。nC存储不是可逆/无损或self-exclusive保证。
- BFC实际197963作者stdlib断言/152validplan/13非法拒绝，以及独立productionplan+原forward函数体列表替身n0..128/22特殊/16非法和集成核，非Torch或训练实验；topologyda6a6811…/integration4ac572c5…。首作者checker误用get_cluster_center方法名，保留失败/快照，改实际cluster_layer，仅harness改正不计模型revision。抽象n65..128显式cap128，原nativecap64未改。
- BFC参数262656替525568(−262912)、每middle最多11round/352mixrows/linear+58.720M MAC均源推断，未测native总量；示例9.821253G仅估计，绝非≤10G PASS。图异于PSNC一次basis conjugation、BTC压摘要/补集、BCR/PSBR累计链；属近邻图备选，不重开旧负结果、不宣称独立novelty或训练上涨。
- BFC disabled native包 bfc_native_prepare/prep727b89a2…14map/12diag/source48fc，worker88392519…/runtime13203cf2…/templatedef851ba…/binding717f48b9…；DRAFTTrue/10active null/无活动lease或adapter。作者14本地检查+7包核与独审43fe525f…46项仅静态；原resources函数及7guard AST保留。草稿额外同call双half非零门按冻结d05d协议移除且旧版留档，未改模型；逐call零合法，四W quadrant每step原loss有限非零梯度及更新仍必须真测。
- M213现stagevalidation/实际准备储备1、非历史parkedhold；source48fc/8512/原9blob及原727b禁用包保持，native_execution_code_commitnull，无M213raw/receipt/queue/experiment。64ac完成受审静态编排catalog与审核草稿后，下一步仅等真实空卡并fresh guard/lease/assets，通过原M95/BFC TRAIN2和资源配对后再准入；缺coverage INCONCLUSIVE，不换样本/seed/precision/阈值，不动BTC0/BCR1/M206。
- 当前M212-BCR stable hierarchy-parent-bidirectional-complement-recurrence，tested/admitted/training/source11a811618179ab1ddc0cee299194667413b7fdb9单父00e；原17map prep tick_41eb62fa/new_candidate_prepare/preparation.json faf3494d…原code_commitnull保持，1334断言62labels/22生产plan与24独立stdlib调用均属历史本地检查，不是训练实验。
- BCR仅middleFFN换strict-exclusive双向共享scan和own/L/R线性读出，原LN/cfskip/fine-coarse/raw-CSORT/HCG/单inst保留；真point-support、原parent、detached xyz+ID排序、Ws恰2(n−1)，Wf每父1调用/n行。PSBR/BTC近邻因子化新信息流，不宣称独立新颖或PSBR单因素因果，不resume旧PSBR。
- 前7526轮GPU1 origincc8b4b16…(disabled)/operational e748a619…outer33/native f5724e27…17/diag12、worker a3b10169…原字节、runtime008e536e…，staticrelease40ee3b47…；静态独审2e4dcbad…44项。52离线run2 abf1ed52…PASS，run1原1fail/1error65d508…及两fixture更正保留，不算候选模型修订。
- 实际owner7526/ctxa524/pending782与原deadline、UUID1/idle/assets/三锁后stage bcr_gpu1_7526f819；native manifest be07748d…/lease7b5a9ab2…/bindingbd01b6b1…，诊断source11a与当时公共runtime00e明确区分。原未执行包/准备历史不回写造PASS。
- 实际原M95/BCR TRAIN2：BCR loss9.521808624267578/13.909966468811035，两原loss/backward/optimizer各2；共同843张量/156958522参数/hash04231c23…及两原batch指纹配对。每forward64真n>=3父组、896scan/64readout、768 depth>=2，最大深度9/12；实际非零priorstate、五Ws token/state/Wf own/L/R原loss梯度和权重更新、cfskip/HCG→inst→mask均核实。
- 实际原资源BCR9.756240972G vsM959.762532428G，157286714 vs157484090参数(−197376)；GPU1 median87.026832014 vs84.860082512ms(+2.5533%)、P90108.935047296 vs99.932504783(+9.0086%)；预测allocated935975424 vs936763392(−0.0841%)、reserved1189085184 vs1191182336，15%条件未触发；完整unsupported保留。
- 四原请求terminal/rc0且逐请求只读reconcile完整对象/LF hash一致，workers[]/GPU1contexts空；history15b18429…/status4640b05a…。V2实际语义c2c36812…、独审ab9644ea…104项；receipt pipeline/admissions/M212-BCR.json b8532405…。是技术准入，非准确率收益。
- 当前M211-BTC stable hierarchy-parent-binary-tree-complement-composition，tested/admitted/科学source00e2b18c6b8d568a64edb496e6979d766440883c、receipt93756329…保持；公共runtime后推进11a仅BCR9新增，BTC8源/已部署YAML/common/原进程未改。原几何父组平衡tree inside/outside、原cfskip/LN/fine-coarse/raw-CSORT/HCG/单inst保留。
- BTC原真TRAIN2 loss9.507390976/13.910472870，common843/hash04231c…；64真n>=3组、inside384/outside896/leaf512/rootinside0，三map更新；原资源9.758338124G vs9.762532428G，157352506参数，旧GPU0 median+13.3134%/P90+19.3694%明确更慢。原ddb四raw/独审dc03…/receipt9375保持，不拿其结果代签BCR。

## Closed Or Failed Directions
- 旧8hold在8878轮到期仅一次有界canonical全记录digest、655声明path/hash pair签名及14授权目录path-size-mtime核，与3824/4a08基准一致；held_boundary_check.json SHA75bb2f2dac86ffdcb93ae974492fcb522dd95f612fd8b1a7900098c7617674f6。0个655正文read/hash/exists/stat及0旧grantbodyread/hash，new_action/user_decision均false；M206queue/exp完整digest同，无新scope/修订/恢复许可。
- 4supervision scope、2measurement implementation/inconclusive及PCE/RSTR限度保持；PCE默认2+额外1已尽/2.861e-6与13.86x；RSTR默认2已尽/R2mean1.027033878e-6>1e-6。禁PCE_R4/RSTR_R3/M201自动恢复；RSTR旧9文件localcommit授权不是新修订许可。
- 所有原HRC/PSBR/HAP/PSNC负结果、版本/日志/收据/archive保留，不整体否定hierarchy或借完成诊断重选样本/seed。

## Running And Queue
- M212-BCR GPU1原PID1215422/start51717921，截至2026-10-25T22:04:39.830832+08:00上海，原argv/cwd/fd1/UUID/model8/YAML/公共HEAD11a保持，Train12/50 3613→3620/4686；本轮proof pipeline/diagnostic_bundles/tick_06a28ff5/bcr_progress_observation.json SHAefdccbe9eb59e9bb52a092ddb63a8063ca46d6a27e8676e6b2c0089bf00498f8。科学source11a811618179ab1ddc0cee299194667413b7fdb9与原receipt保持，无信号或重启。
- M211-BTC GPU0原PID2784474/start47557208，截至2026-10-25T22:05:45.058847+08:00上海，原argv/cwd/fd1/UUID/model8/YAML/公共HEAD11a保持，Train30/50 95→100/4686；本轮proof pipeline/diagnostic_bundles/tick_06a28ff5/btc_progress_after_boundary_observation.json SHA710f237dc350c6f990afda83098817f4fcb673f9c0f7228f30be95864e8924aa。科学source00e2b18c6b8d568a64edb496e6979d766440883c与原receipt保持，无信号或重启。
- primary仅00e→11a已测9新增ff-only，原28dirty/untracked status+bytes及index空保持，不新commit/force/stash/reset/clean。canonical safe_sync远端同样ff-only且前后实际source验证；候选YAML仅既定路径适配。
- 前7526轮一次_process_queue/一次真实Popen，wrapper只查GPU1并在3flock覆盖UUID/idle至Popen返回，后释放不冒称全程训练锁；actual launch/progress41a14e95…，最终独审12c6967d412aa502…，M206与BTC原row/exp/receipt保持。
- pinned songcl@192.168.1.115/dl04-MS-7E06；UUID0 GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c，UUID1 GPU-7f82edb9-f620-8045-caea-a75232265cd1；root /data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1，conda project_cluster/runtime server4_conda_4ca73fba.sh，data /home/songcl/data/data/；keys/strict hostkey，不用旧.137/密码/sudo，python -B。
- M206-CGCA仍waiting但paused_by_user/dispatch_hold/resume_authorizedfalse，无PID，不计ready、不自动恢复/迁卡。完整snapshot meta24/best.4952535927295685/noimprove7，last.pth e9b42b26…，admitted898ff63与公共runtime11a有别，GPU1可用不授M206恢复。

## Open Questions And Risks
- BTC/BCR最终训练准确率UNKNOWN；本轮22:03上海preflight监控Best BTC0.4914(29/50/noimprove7/10)、BCR0.4848(12/50/noimprove2/10)属采集时训练中记录。BTC后续已自然Train30，首Val29完成游标不当best。M95仍.5020，目标.5100/gap.0080；常规增长无新完成结论，不改seed/schedule/阈值或test集选机制。
- BCR当前同GPU1资源pair时延比M95更慢；不与BTC旧GPU0 timing做因果比较。原fvcore完整unsupported披露，CPU/Python工作未全计；pureTRAIN峰值UNKNOWN，smoke含observer/topology开销。
- 配对仅共同named参数与两原batch，full buffer/RNG未逐值配对；raw/map跨目标digest差异保留、不立新相等门或作因果归因；empty/pad/singleton覆盖0属未行使，offdiag/fullFP32控制NOT_RUN。
- BCR candidate早期/proc argv=[]是瞬时未观测，仅construct command/directPopen.wait/原request/result链证明本次诊断，不用于后续信号身份；正式train另有真PID/start/argv/cwd/fd1/progress双样本。
- 任何未知launch仅原request/PID/log只读reconcile，不盲重启/kill/删锁；后续GPU检查须fresh owner/assets/实际占用/三锁，旧lease与静态catalog不授未来资源。

## Last Tick
- 本轮06a2 begin一次monitor/goal/已有合格派发；design/candidate_budget2/reserve2/creation0，2running/0ready/0新终态/0operationalissue；due仅BFC/CTS，旧9notdue不重查，沿用8878有界metadata记录。
- 首BTC在Train29 4686/4686和Val29 363/363交界，3秒窗TRAIN增长false已保留d4d16f…且非训练故障；一次同原PID/start/源/UUID/唯一log复核后Train30 95→100，710f237d…。BCR原Train12 3613→3620，efdccbe9…。两卡原NVML context忙，0信号/重启/共享overlay。
- 实际BFC availability resource_check blocked f5b8ce…；current owner/context/原deadline本地busy guard在probe/dir/manifest/lease前拒绝，0transport。无GPU诊断计算/新候选/版本/准入/queue/launch，保留BFC先原生与CTS后续封装顺序，不重跑52/61/42静态套件或凑额度。
- 仅BFC资源证据追加，CTS、两训练candidate及其他全部candidate canonical digest保持；M206 pause/resumefalse/noPID及queue/running/原exp/receipt、primary11a/28status/index空保持。旧scope/失败/修订/资源边界/目标/调度/data-seed-schedule/YAML/禁项不变。
- 无新增研究决策文件或实质状态变化、失败、需用户处理事项；完整六段notes/report和七段memory留档。finish真实核FINALIZED/released与lock/pending消失后不回写；例行健康/等待资源选择DONT_NOTIFY。
