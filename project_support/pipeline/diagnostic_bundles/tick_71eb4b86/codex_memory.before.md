# Codex Research Memory

## Goal And Phase
- 实际owner01a159c5-29ab-7a22-ba7f-e79174757253匹配环境/execution_mode。最新用户“先只用server4 GPU0、断开GPU1并同任务full resume入队”已完成，手动证据见manual_ops/20261021_gpu0_resume_031718_r2。前轮5e805d91 FINALIZED、lease released及lock/pending消失已核验，不重用旧token。
- 当前c50d25e2f6894facbb2b178bb5d12346 DESIGN began上海12:05:41、原deadline13:05:41；snapshot capacity1/running1/waiting1/ready1，reserve_budget0/creation0。experiment_first保持，一次真实有证据检查可收尾，不凑配额。GoalSHA0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85；目标.5100、历史M95 .5020、gap.0080、baseline.4894。hierarchy→inst_feats→query/masks主线，seed1999/50epochs/maxiters70/default10G/Phase1及bans不变。
- Standing授权pipeline/authorizations/experiment_first_20261021.json SHA2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8涵盖项目内代码/YAML/检查/版本/安全同步/入队/训练；不重复询问常规操作。旧双卡请求已被当前“先只使用GPU0”覆盖；新显式授权见pipeline/authorizations/gpu0_only_resume_20261021_gpu0_resume_031718_r2.json，暂仅server4物理GPU0一任务。无DDP转换、资源扩张、驱逐或历史重开授权。
- 最新用户收缩资源：SERVERS.server4 allowed[0]，server3 allowed[]/dispatchfalse，server6仍禁用；旧授权/资源清单保留beforeimage，不改goal/科学门槛/环境/调度。WindowsPipeline-cluster_project保持Disabled。

## Champion And Baseline
- 上海2026-10-21 12:05本轮canonical monitor：M205-MDC Best=.4768、11/50、no_improve0/10，GPU0继续。12:07日志mtime新、native tqdm第11轮3740→3741/4686步递增。M206仅waiting原生resume，完整checkpoint8 Best=.4751223027706146/no_improve0，后续从epoch9恢复，尚未启动。
- M205已测9.7331723G vs M95 9.762532428G；bs1 warmup20/repeat100 median34.374782/P9037.903044ms vs35.384447/36.352109；原idle host测量。M206在M205并行时配对9.764703308G vs9.762532428G、median88.502825/P90100.298061ms vs86.694451/99.899674。不能跨主机占用横比绝对延迟；unsupported ops保留。
- M206配对原TRAIN两步peak7421422080 vs7418908672bytes(+.0339%)，非全训练worstcase保证。其余旧测明细见tick_899d59f1及本轮codex_memory.before.md。
- M207-HAP原生数值/梯度/FLOPs/延迟/显存/准确率全UNKNOWN；静态PASS不是预算或native PASS。

## Active Hypotheses
- M205-MDC（hierarchy-middle-directional-token-convolution）GPU0正式训练，commit59013e132241322054f1906e771aa78b81c48da6。middle自身+六方向近邻depthwise/pointwise替代middleFFN；fine/coarse FFNs、CSORT raw bank/HCG/末尾inst_feats路径保持。原生两步/资源/准入/启动已核验，收益待测。
- M206-CGCA（hierarchy-coarse-conditioned-fine-channel-attention）按用户指令从GPU1暂停；同commit898ff63a2cf63d3895a9e86c0ee3d1e5b672b335/admission不变，stage=deployment、training_status=paused_waiting_resume，队列同ID waiting/GPU0，无dispatch_hold。CPU核完整model/optimizer642states/5groups/scheduler/meta，固定副本epoch8，resume从9；不是新seed/冷启动。旧GPU1 PID/log/launch proof保留paused_run/history，新launch_verified=false待重新核验。
- M207-HAP（hierarchy-affine-coarse-to-fine-prolongation）validation/native_status=pending_resource，本地f51823bbddf0f8095a9a5813bf1f8169e3d7edb0未推送。8独立源+1原YAML值不变；原三FFNs先执行，coarse→middle→fine：D=occupied child centers−组均值；A=pinv(D.TD,hermitian=True)@(D.T@原refined child)；新child=已更新parent+DA。算子返回fine/mid，coarse外部保持。无新gate/residual/QKV/seed/扫参。
- HAP真实occupied沿原ids从point向上传播，排除空ID/padding；原FPS/featurepool/CSORT保持。几何FP32 detached，特征RHS/斜率/detail在autograd。原AST/compile/import/YAML等值/基线hash检查通过，无本地torch/model/合成/原生行为运行。
- 前轮tick_a5a8c4f2准备hap_native_worker.py、hap_smoke_function.py，Python3.10 AST/compile及独立只读复核无阻断问题，PREPARED_UNEXECUTED。检查三输入/两输出backward、三FFN weight梯度/独立hash更新、原train.train+loader两步/numel1有限loss、真实G/pinv观测。resources AST与已执行CGCA相同，不安装spy。
- spy仅smoke原pinv调用一次、透传args/kwargs、返回原Tensor、finally恢复；额外matrix_rank不是pinv内部保留秩。旧worker原pinv抛错前G未留存/谱异常不单列的缺口保留于旧证据，当前新v2已改善异常留档，不自动否定HAP。
- 前轮tick_5c5688ff已补齐fresh native_runtime/manifest/lease/原worker/8HAP源/YAML共13文件并远端私有stage静态编译/hash验证；NAME原M95，candidate_name_hap，GPU0/UUID0/query/locks/env一致，经独立只读复核。实际acquire-only probe在busy首查拒绝，torch/gorilla/worker/setup均未进入，0forward/0optimizer/持有锁0，无自身CUDA context。native数据/backward/资源仍未执行。

- 前轮tick_73e1f420/worker_v2.py（SHAffb2e09a53f3e860b398b435674ca0800b9641f5e48391d1af0d3098b8698a73）在全新文件修复pinv前G留档、原异常保留及observer异常延后独立检查；原训练调用/setup/resources/main AST不变，模型f51823bb/YAML未改。独立只读源审无阻断，服务器5个纯Python非tensor哨兵控制测试通过（异常/单次调用/原返回对象），0torch/model/data/GPU。未staging此v2、未执行原生数值/backward/resource。后续fresh stage须采用此worker并重绑hash。
- observer_readout_complete只表示字段完整且无异常，不保证额外谱值全finite。G/Gplus真实finite门保留，JSON非finite转null不可当0/PASS；worker私有diagnostic_observer异常归档ledger时映射implementation，当前candidate scope/修订预算未变。

## Closed Or Failed Directions
- 8旧held及负证据/修订限制保持，RSTR/PCE/FLE/HDS/CPA/M201未重开。RSTR明确授权9文件本地commit36b59daa保留，2修订耗尽、R2 mean1.027033878e-6>1e-6 FAIL；早先PASS/独立重算9.536743e-7不清hold。PCE额外修订已用，不自动R4。
- 旧M205 harness序列化/0D loss错误保留，原Criterion单元素shape[1]合法；当前numel1+finite。CGCA baseline一次0forward/0GPU前置资源拒绝非模型失败。
- 有限历史CCP(child+parent)、GEO(centroid/radius→Linear残差)与HAP未见完全等价/明确ban，非全面新颖性证明。HAP不是child+parent+DA，没有RSTR点质量守恒宣称。
- 前轮2个complete历史SERVERS证据仅冻结到同SHA60cba26a的tick_899d59f1/SERVERS.before.yaml；原结果/修订不变，不是科研进展，未改验证器/门槛。

- 前轮旧8blocked到期做一次有界只读复核，见tick_3e3adfa3/due_hold_readonly_review.json：4辅助监督scope hold、2数值测量实现hold、PCE/RSTR修订耗尽均无新解锁授权/修复证据，未重开/改旧记录。2测量同输入float32差1.907e-6>1e-6不冒充机制反证；通用experiment_first或timer不授权历史重开。

## Running And Queue
- server4 pinned192.168.1.115/dl04-MS-7E06，当前仅GPU0 UUID958e741a/allowed[0]/max1card可用；GPU1 UUID7f82edb9仅库存，已停止项目M206、不再授权实验/诊断。root=/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1仍HEAD898ff，未sync/修改其源码。
- M206旧PID3873690及GPU1 context已确认消失，暂停事务完整保留。当前12:07 GPU0 M205 PID3842306继续，约20438MiB；另有CUDA context PID1210171约1790MiB，归属未核验，不干预，也不据低util/锁文件可用当空卡。
- 三账一致：queue M205 running GPU0，M206 waiting resume GPU0；running.json仅server4[0]=M205；experiment M206 waiting+paused_run/history+固定resume proofs，无旧PID冒充当前launch。GPU0空闲后优先排队M206，不新开HAP抢占。
- HAP仅等待server4GPU0，M206已准入的same-experiment resume排队优先。GPU1释放并不解锁HAP；下轮新lease/stage/guard必须按allowed[0]生成，使用reviewed worker_v2/精确f51823bb/YAML/assets，实际native两步+配对资源PASS才准入。不能复用旧assert[0,1]的控制helper或旧lease。
- server3旧GPU1历史授权保留记录但当前allowed[]/dispatchfalse，不作当前容量；server3外部任务未触碰、server6仍禁用。旧root dirty YAML/diff保持，无reset/clean/stash/force/sudo/密码操作。

- 原普通launcher不消费resume_from存在冷启动风险，现canonical cluster_resume.py+closure.safe_launch+monitor已作Cluster-only严格resume支持。16项专门测试root实跑PASS、132项整体离线回归PASS；双hash artifact/人类授权/固定CPU完整state/path+SHA/旧exact remoteHEAD+source integrity、GPU0约束，启动前重hash并唯一追加--resume。resume不sync、不改YAML，不依赖localHEAD=f518与898不同；其余fresh路径不变。partial-proof缺path会拒绝，不回退冷启动。

- M206固定checkpoint副本/data/songcl/Project/Cluster_project/pipeline/resume_snapshots/20261021_gpu0_resume_031718_r2/20261021_051530/last.pth，SHA2e11ea38ba81b657301a34efc11483455fb1f9eeb83a5f4d52fbc40ffb4669d7；epoch8/best.4751223027706146/no_improve0，原optimizer/scheduler完整。最新完整proof见manual_ops/.../checkpoint_evidence_final.json与resume_queue_validation.json，实际绝对路径由queue artifact引用为准；不把stat存在等同新hash核验。

## Open Questions And Risks
- HAP正规方程平方条件数，FP32退化/default pinv cutoff须实测，禁止加ridge/改精度/调阈值绕过失败。rank(D)<=min(3,nchild−1)，单child/零D给parent-only；≤4仿射独立时detail=Hchild−mean，不能声称每组独特几何过滤。
- fine/mid末层constant bias梯度可为0，须观测非恒定child及parent路径。组token均值=parent非pointmass守恒；可能抹高阶语义/粗截距伤小目标。小3x3不免费，native数值/资源/收益待测。
- MDC固定轴旋转、跨coarse parent及fine-ID空洞边界保持；CGCA模糊/场景偏置未知。不能按首轮验证扫参、换seed或宣称最终有效。

## Last Tick
- 本轮bundle pipeline/diagnostic_bundles/tick_c50d25e2：resume_resource_check/native_progress_rows/report_notes/tick_result。优先已有M206续训队列，双proof/原admission有效、checkpoint存在，但唯一GPU0仍有M205训练及其他context。M205实际native步数递增，无新的异常或用户事项。
- tick_attempt绑定当前generated_at2026-10-21T04:05:41.178730Z、M206部署候选、resource_check/blocked及新资源证据，不复用旧检查。0新候选/0native诊断/0新准入/0队列新增/0启动；reserve/creation预算0，不新准备或复测HAP。
- 后续只使用server4GPU0，GPU0真正全空闲后优先同M206 native full resume epoch9并重新核验新PID/log/progress；不使用释放的GPU1。HAP继续等待，旧hold不重开、调度不变；当前健康运行与同一资源等待按约定静默。
- memory/中文notes于finish前留档，收尾以tick_receipts/c50d25e2f6894facbb2b178bb5d12346.json及实际命令为准，不预写PASS。必须核验FINALIZED、lease released及owned lock/pending消失，释放后不写项目。
