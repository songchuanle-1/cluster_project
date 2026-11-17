# Codex Research Memory

## Goal And Phase
- 实际owner01a159c5-29ab-7a22-ba7f-e79174757253已核验。最新人类“gpu1可以使用”恢复server4GPU1授权，覆盖此前GPU0-only对GPU1的限制；server3/server6仍禁用。前轮f8150790 FINALIZED/released，无旧lease。手动事务manual_ops/20261021_gpu1_reenable_152505已在.pipeline.lock下完成授权/白名单/同M206GPU1双proof/队列重绑。
- 当前为手动资源恢复，尚未begin新tick/未启动；GPU1实时idle及原checkpointSHA、精确远端898ff源码PASS，M205原PID/cwd/argv/starttime保持。准备完成后立即canonical begin派发，不把ready写成已恢复。goalSHA0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85及科学目标/数据/seed/schedule/bans不变。
- Standing experiment_first_20261021.json SHA2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8继续。最新GPU1授权pipeline/authorizations/server4_gpu1_reenabled_20261021_gpu1_reenable_152505.json SHA30f17c5bcb66782a255d7eed4bb00277e807bfea4e64a48a499ab749fadd2fa7，允许server4[0,1]每卡1任务。复用原full-resume授权，新增GPU1绑定双proof，禁止冷启动/驱逐/扩大到其他服务器或历史重开。
- 最新SERVERS.server4 allowed[0,1]/max1card，GPU0 M205保留、GPU1优先原M206full resume；server3 allowed[]/dispatchfalse、server6仍禁用。旧授权/资源清单beforeimage保留，goal/科学门槛/环境/调度不变，WindowsPipeline-cluster_project保持Disabled。

## Champion And Baseline
- 上海2026-10-21 22:05 canonical monitor：M205-MDC Best=.4872、23/50、no_improve6/10，尚未触发原patience10。22:05:51同PID/argv/cwd/starttime，第23轮3414→3415/4686递增、log age0.32秒。M206仅waiting native resume，epoch8 Best=.4751223027706146/no_improve0，尚未从9恢复。
- M205已测9.7331723G vs M95 9.762532428G；bs1 warmup20/repeat100 median34.374782/P9037.903044ms vs35.384447/36.352109；原idle host测量。M206在M205并行时配对9.764703308G vs9.762532428G、median88.502825/P90100.298061ms vs86.694451/99.899674。不能跨主机占用横比绝对延迟；unsupported ops保留。
- M206配对原TRAIN两步peak7421422080 vs7418908672bytes(+.0339%)，非全训练worstcase保证。其余旧测明细见tick_899d59f1及本轮codex_memory.before.md。
- M207-HAP原生数值/梯度/FLOPs/延迟/显存/准确率全UNKNOWN；静态PASS不是预算或native PASS。

## Active Hypotheses
- M205-MDC（hierarchy-middle-directional-token-convolution）GPU0正式训练，commit59013e132241322054f1906e771aa78b81c48da6。middle自身+六方向近邻depthwise/pointwise替代middleFFN；fine/coarse FFNs、CSORT raw bank/HCG/末尾inst_feats路径保持。原生两步/资源/准入/启动已核验，收益待测。
- M206-CGCA（hierarchy-coarse-conditioned-fine-channel-attention）原GPU1暂停历史完整保留；最新GPU1再次授权，同898ff/admission/nativeYAML/epoch8完整checkpoint不变，现same-ID waiting/GPU1 ready，无dispatch_hold，stage=deployment、training_status=paused_waiting_resume、launch_verified=false。重核精确源码与固定SHA，预期native从9恢复优化器/调度器/best/patience，尚未新启动。
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

- 8旧hold于本轮22:05快照再次due，有界独立只读复核见tick_f8150790/due_hold_readonly_review.json对照tick_d33fef56：4辅助scope/2数值测量实现hold/PCE3次与RSTR2次耗尽均无实质变化、新解锁授权或保门修复，指定wake文件仍不存在。未重开/改记录；同输入FP32差1.907e-6>1e-6不是机制反证，timer不授权。

## Running And Queue
- server4 pinned192.168.1.115/dl04-MS-7E06，当前allowed[0,1]/每卡1任务；GPU0 UUID958e741a、GPU1 UUID7f82edb9，均精确核验。root=/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1仍精确HEAD898ff，无源码sync/YAML改动。
- M206旧PID3873690及GPU1 context暂停证明保留；当前22:05 GPU0约18645MiB/util27%，唯一可见CUDA context为同M205 PID3842306约18590MiB。GPU0未空闲，不按低util/旧context PID/锁文件可用推断空卡。
- 三账一致：queue M205 running/GPU0，M206 waiting/full-resume/GPU1；running暂仅GPU0=M205，无GPU1假running；M206experiment新gpu1双proof/人类授权/history一致，无旧PID冒充当前launch。立即canonical dispatch并核验新进度。
- HAP原GPU0 prepared计划继续等待实际空槽；新GPU1授权已解除旧GPU0-only禁令，但M206已准入resume优先。后续fresh lease/stage必须使用reviewed worker_v2/精确f51823bb/YAML/assets，按选定授权卡同步UUID/query/locks/env，真实native两步+配对资源PASS才准入。
- server3旧GPU1历史授权保留记录但当前allowed[]/dispatchfalse，不作当前容量；server3外部任务未触碰、server6仍禁用。旧root dirty YAML/diff保持，无reset/clean/stash/force/sudo/密码操作。

- canonical cluster_resume.py现最小支持server4GPU0/1，必须当前白名单/任务gpu/双hash proof精确一致；human/fullstate/source/checkpoint/no-cold-fallback全部保留。相关116离线回归PASS，独立22专门测试PASS及只读复核无阻断；closure/monitor不改。resume不sync、不改YAML，Popen前重hash唯一--resume，实际启动仍待核验。

- M206固定checkpoint副本/data/songcl/Project/Cluster_project/pipeline/resume_snapshots/20261021_gpu0_resume_031718_r2/20261021_051530/last.pth，SHA2e11ea38ba81b657301a34efc11483455fb1f9eeb83a5f4d52fbc40ffb4669d7；epoch8/best.4751223027706146/no_improve0，原optimizer/scheduler完整。最新完整proof见manual_ops/.../checkpoint_evidence_final.json与resume_queue_validation.json，实际绝对路径由queue artifact引用为准；不把stat存在等同新hash核验。

## Open Questions And Risks
- HAP正规方程平方条件数，FP32退化/default pinv cutoff须实测，禁止加ridge/改精度/调阈值绕过失败。rank(D)<=min(3,nchild−1)，单child/零D给parent-only；≤4仿射独立时detail=Hchild−mean，不能声称每组独特几何过滤。
- fine/mid末层constant bias梯度可为0，须观测非恒定child及parent路径。组token均值=parent非pointmass守恒；可能抹高阶语义/粗截距伤小目标。小3x3不免费，native数值/资源/收益待测。
- MDC固定轴旋转、跨coarse parent及fine-ID空洞边界保持；CGCA模糊/场景偏置未知。不能按首轮验证扫参、换seed或宣称最终有效。

## Last Tick
- 最新直接人类“gpu1可以使用”已记录GPU1恢复授权，GPU0 M205保留、server3/server6仍禁用。manual_ops/20261021_gpu1_reenable_152505保存所有beforeimages/strictSSH双UUID/空闲/固定checkpointSHA/原source验证/独立入口复核。
- 原M206同ID已改waiting/GPU1，双resume proof新绑GPU1且引用原CPU完整state检查及新实测相同SHA；checkpointepoch8/next9，无当前activePID/launch_verifiedfalse。旧GPU0-only证明保留，未改历史artifact。
- 初始GPU1空闲、M205原PID3842306/cwd/argv/starttime保持；当前ready不等于已恢复，立即新foreground tick走既有gated monitor派发及native进度证明。科学目标/seed/schedule/nativeYAML/源码/bans/调度不变，未重开旧hold。
- HAPnative仍UNKNOWN，原GPU0计划不动，M206resume优先；GPU1授权允许未来fresh正确绑定的检查，不复用旧lease或混卡UUID。
- 新tick需实际begin/current snapshot/report/finish；不得把手动准备当已训练或伪写PASS。当前无持有foreground lease，待派发后将结果与新receipt留档。
