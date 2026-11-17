# Codex Research Memory

## Goal And Phase
- 实际owner01a159c5-29ab-7a22-ba7f-e79174757253已核验。最新人类“gpu1可以使用”恢复server4GPU1授权，覆盖此前GPU0-only对GPU1的限制；server3/server6仍禁用。前轮f8150790 FINALIZED/released，无旧lease。手动事务manual_ops/20261021_gpu1_reenable_152505已在.pipeline.lock下完成授权/白名单/同M206GPU1双proof/队列重绑。
- 当前8bec58e9525645d49e7b8deeabd6b93c DESIGN，上海23:28:12快照、原deadline10-22 00:28:12；capacity2/running2/waiting0、reserve0/creation0，experiment_first不凑配额。最新GPU1授权和M206 native full resume已核验；goalSHA0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85及科学目标/数据/seed/schedule/bans保持。
- Standing experiment_first_20261021.json SHA2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8继续。最新GPU1授权pipeline/authorizations/server4_gpu1_reenabled_20261021_gpu1_reenable_152505.json SHA30f17c5bcb66782a255d7eed4bb00277e807bfea4e64a48a499ab749fadd2fa7，允许server4[0,1]每卡1任务。复用原full-resume授权，新增GPU1绑定双proof，禁止冷启动/驱逐/扩大到其他服务器或历史重开。
- 最新SERVERS.server4 allowed[0,1]/max1card，GPU0 M205保留、GPU1优先原M206full resume；server3 allowed[]/dispatchfalse、server6仍禁用。旧授权/资源清单beforeimage保留，goal/科学门槛/环境/调度不变，WindowsPipeline-cluster_project保持Disabled。

## Champion And Baseline
- 上海2026-10-21 23:27 monitor：M205 Best=.4872、26/50、no_improve9/10，仍按原patience10；23:29:03原PID/cwd/argv/starttime保持。M206已GPU1 native从epoch9续训，步骤102→103/4686；日志恢复epoch8 checkpoint的best .4751223027706146/no_improve0并载入optimizer/scheduler。此Best为恢复历史值，未作新验证收益宣称。
- M205已测9.7331723G vs M95 9.762532428G；bs1 warmup20/repeat100 median34.374782/P9037.903044ms vs35.384447/36.352109；原idle host测量。M206在M205并行时配对9.764703308G vs9.762532428G、median88.502825/P90100.298061ms vs86.694451/99.899674。不能跨主机占用横比绝对延迟；unsupported ops保留。
- M206配对原TRAIN两步peak7421422080 vs7418908672bytes(+.0339%)，非全训练worstcase保证。其余旧测明细见tick_899d59f1及本轮codex_memory.before.md。
- M207-HAP原生数值/梯度/FLOPs/延迟/显存/准确率全UNKNOWN；静态PASS不是预算或native PASS。

## Active Hypotheses
- M205-MDC（hierarchy-middle-directional-token-convolution）GPU0正式训练，commit59013e132241322054f1906e771aa78b81c48da6。middle自身+六方向近邻depthwise/pointwise替代middleFFN；fine/coarse FFNs、CSORT raw bank/HCG/末尾inst_feats路径保持。原生两步/资源/准入/启动已核验，收益待测。
- M206-CGCA（hierarchy-coarse-conditioned-fine-channel-attention）已按新GPU1授权恢复同实验，GPU1新PID732137、exact --resume argv、native9/50步数递增及原optimizer/scheduler/best/patience恢复均实测。原898ff/admission/YAML/epoch8固定checkpoint不变，stage=training/training_status=running_resumed；旧暂停/原GPU1 PID3873690及GPU0待跑历史保留。
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

- 8旧hold于22:05历史快照再次due，有界独立只读复核见tick_f8150790/due_hold_readonly_review.json对照tick_d33fef56：4辅助scope/2数值测量实现hold/PCE3次与RSTR2次耗尽均无实质变化、新解锁授权或保门修复，指定wake文件仍不存在。未重开/改记录；同输入FP32差1.907e-6>1e-6不是机制反证，timer不授权。

## Running And Queue
- server4 pinned192.168.1.115/dl04-MS-7E06，当前allowed[0,1]/每卡1任务；GPU0 UUID958e741a、GPU1 UUID7f82edb9，均精确核验。root=/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1仍精确HEAD898ff，无源码sync/YAML改动。
- M206旧PID3873690暂停证明保留，当前新PID732137在GPU1 UUID7f82edb9约11252MiB；M205同PID3842306在GPU0 UUID958e741a约18590MiB，两卡context映射实测匹配。23:29两卡总显存分别18645/11277MiB，均占用，不是HAP空槽。
- 三账一致：queue M205 running/GPU0，M206 running/GPU1/newPID732137/launch_verifiedtrue；running[server4]为0=M205、1=M206；M206experiment新gpu1双proof/历史/实际native launch proof一致。勿重复启动或把旧paused PID当活跃。
- HAP原GPU0 prepared计划继续等待实际空槽；新GPU1授权已解除旧GPU0-only禁令，但M206已准入resume优先。后续fresh lease/stage必须使用reviewed worker_v2/精确f51823bb/YAML/assets，按选定授权卡同步UUID/query/locks/env，真实native两步+配对资源PASS才准入。
- server3旧GPU1历史授权保留记录但当前allowed[]/dispatchfalse，不作当前容量；server3外部任务未触碰、server6仍禁用。旧root dirty YAML/diff保持，无reset/clean/stash/force/sudo/密码操作。

- canonical cluster_resume.py最小支持server4GPU0/1，当前白名单/任务gpu/双hash proof必须精确一致；human/fullstate/source/checkpoint/no-cold-fallback全保留。116相关离线回归、独立22专门测试和只读复核PASS；closure/monitor未改。实际M206新GPU1 native resume启动已核验，无sync/YAML改变，Popen前重hash且唯一--resume。

- M206固定checkpoint副本/data/songcl/Project/Cluster_project/pipeline/resume_snapshots/20261021_gpu0_resume_031718_r2/20261021_051530/last.pth，SHA2e11ea38ba81b657301a34efc11483455fb1f9eeb83a5f4d52fbc40ffb4669d7，最新手动事务新重hash匹配并在启动前再核；原CPU完整model/optimizer642states5groups/scheduler/meta证据保留原timestamp，新GPU1绑定proof见manual_ops/20261021_gpu1_reenable_152505/checkpoint_evidence_gpu1.json。实际路径旧gpu0命名不改变其字节或GPU1续训身份。

## Open Questions And Risks
- HAP正规方程平方条件数，FP32退化/default pinv cutoff须实测，禁止加ridge/改精度/调阈值绕过失败。rank(D)<=min(3,nchild−1)，单child/零D给parent-only；≤4仿射独立时detail=Hchild−mean，不能声称每组独特几何过滤。
- fine/mid末层constant bias梯度可为0，须观测非恒定child及parent路径。组token均值=parent非pointmass守恒；可能抹高阶语义/粗截距伤小目标。小3x3不免费，native数值/资源/收益待测。
- MDC固定轴旋转、跨coarse parent及fine-ID空洞边界保持；CGCA模糊/场景偏置未知。不能按首轮验证扫参、换seed或宣称最终有效。

## Last Tick
- 人类最新gpu1可以使用已完成：server4[0,1]每卡1任务，GPU0 M205保留、GPU1同M206 full native resume已恢复；server3/server6仍禁用。manual_ops/20261021_gpu1_reenable_152505存beforeimages/新grant/新GPU1双proof/固定SHA/精确898ffsource/116+独立22tests/独立复核及手动决策20261021-232709。
- 当前tick_8bec58e9/native_resume_launch_proof实测：23:29:03 GPU1新PID732137 exact --resume/原cwd、native9/50步骤102→103；日志明确start_epoch9/best.4751223027706146/no_improve0和optimizer/scheduler载入。GPU0 M205原PID3842306/starttime保持。三账与M206 stage=training/running_resumed对齐。
- tick_attempt绑定当前2026-10-21T15:28:12.135717Z、M206 implementation_test/passed及真实native证据。1已有任务resume、0新队列ID/0新模型候选/0新准入；reserve/creation0，HAP native仍UNKNOWN，双卡busy，旧hold/修订/科学协议不变。
- 后续监控M205原patience10及M206原训练；实际卡空闲后HAP使用fresh匹配GPU/UUID/locks/env/lease、reviewed worker_v2及f51823bb原源YAML做native检查。GPU1授权不解锁PCE/RSTR额外修订或旧监督主线，不改调度。
- report/memory在finish前留档，实际收尾以tick_receipts/8bec58e9525645d49e7b8deeabd6b93c.json及命令为准，不预写PASS；核验FINALIZED/lease released/headless lock与pending消失，释放后不写项目。
