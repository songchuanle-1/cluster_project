# Codex Research Memory

## Goal And Phase
- 实际owner01a159c5-29ab-7a22-ba7f-e79174757253与环境/execution_mode匹配。本轮73e1f420ae624c0d8c0b9c7ed5c9e546 DESIGN，上海2026-10-21 08:09:37开始，原deadline09:09:37不变。前轮5c5688ff FINALIZED、lease released且lock/pending消失已核验；不复用旧token。
- snapshot experiment_first.enabled=true，waiting_target2/max_new2/actionable_limit4；一次真实有证据检查可收尾，不凑配额。GoalSHA0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85；目标.5100、历史M95 .5020、gap.0080、baseline.4894。hierarchy→inst_feats→query/masks主线，seed1999/50epochs/maxiters70/default10G/Phase1及bans不变。
- Standing授权pipeline/authorizations/experiment_first_20261021.json SHA2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8涵盖项目内代码/YAML/检查/版本/安全同步/入队/训练；不重复询问常规操作。最新“使用server4 两张卡”见tick_899d59f1/user_server4_request.json，GPU0/1一独立单卡实验/卡。无DDP转换、资源扩张、驱逐或历史重开授权。
- goal/SERVERS.yaml/资源边界/环境/调度本轮未改；Windows Pipeline-cluster_project确认Disabled。

## Champion And Baseline
- 上海2026-10-21 08:09本轮begin canonical monitor：M205-MDC Best=.4370、5/50（新增.4370）；M206-CGCA Best=.4208、5/50（新增.4165/.4208），均no_improve0/10。是持续早期训练，最终收益/失败未知；原验证/早停协议不变。
- M205已测9.7331723G vs M95 9.762532428G；bs1 warmup20/repeat100 median34.374782/P9037.903044ms vs35.384447/36.352109；原idle host测量。M206在M205并行时配对9.764703308G vs9.762532428G、median88.502825/P90100.298061ms vs86.694451/99.899674。不能跨主机占用横比绝对延迟；unsupported ops保留。
- M206配对原TRAIN两步peak7421422080 vs7418908672bytes(+.0339%)，非全训练worstcase保证。其余旧测明细见tick_899d59f1及本轮codex_memory.before.md。
- M207-HAP原生数值/梯度/FLOPs/延迟/显存/准确率全UNKNOWN；静态PASS不是预算或native PASS。

## Active Hypotheses
- M205-MDC（hierarchy-middle-directional-token-convolution）GPU0正式训练，commit59013e132241322054f1906e771aa78b81c48da6。middle自身+六方向近邻depthwise/pointwise替代middleFFN；fine/coarse FFNs、CSORT raw bank/HCG/末尾inst_feats路径保持。原生两步/资源/准入/启动已核验，收益待测。
- M206-CGCA（hierarchy-coarse-conditioned-fine-channel-attention）GPU1正式训练，commit898ff63a2cf63d3895a9e86c0ee3d1e5b672b335。occupied coarse Gram生成8组32通道矩阵A，fine自身values@A.T；零新增参数、真实coarse→operator→fine图。原生两步及资源等已通过，收益待测。
- M207-HAP（hierarchy-affine-coarse-to-fine-prolongation）validation/native_status=pending_resource，本地f51823bbddf0f8095a9a5813bf1f8169e3d7edb0未推送。8独立源+1原YAML值不变；原三FFNs先执行，coarse→middle→fine：D=occupied child centers−组均值；A=pinv(D.TD,hermitian=True)@(D.T@原refined child)；新child=已更新parent+DA。算子返回fine/mid，coarse外部保持。无新gate/residual/QKV/seed/扫参。
- HAP真实occupied沿原ids从point向上传播，排除空ID/padding；原FPS/featurepool/CSORT保持。几何FP32 detached，特征RHS/斜率/detail在autograd。原AST/compile/import/YAML等值/基线hash检查通过，无本地torch/model/合成/原生行为运行。
- 前轮tick_a5a8c4f2准备hap_native_worker.py、hap_smoke_function.py，Python3.10 AST/compile及独立只读复核无阻断问题，PREPARED_UNEXECUTED。检查三输入/两输出backward、三FFN weight梯度/独立hash更新、原train.train+loader两步/numel1有限loss、真实G/pinv观测。resources AST与已执行CGCA相同，不安装spy。
- spy仅smoke原pinv调用一次、透传args/kwargs、返回原Tensor、finally恢复；额外matrix_rank不是pinv内部保留秩。旧worker原pinv抛错前G未留存/谱异常不单列的缺口保留于旧证据，当前新v2已改善异常留档，不自动否定HAP。
- 前轮tick_5c5688ff已补齐fresh native_runtime/manifest/lease/原worker/8HAP源/YAML共13文件并远端私有stage静态编译/hash验证；NAME原M95，candidate_name_hap，GPU0/UUID0/query/locks/env一致，经独立只读复核。实际acquire-only probe在busy首查拒绝，torch/gorilla/worker/setup均未进入，0forward/0optimizer/持有锁0，无自身CUDA context。native数据/backward/资源仍未执行。

- 本轮tick_73e1f420/worker_v2.py（SHAffb2e09a53f3e860b398b435674ca0800b9641f5e48391d1af0d3098b8698a73）在全新文件修复pinv前G留档、原异常保留及observer异常延后独立检查；原训练调用/setup/resources/main AST不变，模型f51823bb/YAML未改。独立只读源审无阻断，服务器5个纯Python非tensor哨兵控制测试通过（异常/单次调用/原返回对象），0torch/model/data/GPU。未staging此v2、未执行原生数值/backward/resource。后续fresh stage须采用此worker并重绑hash。
- observer_readout_complete只表示字段完整且无异常，不保证额外谱值全finite。G/Gplus真实finite门保留，JSON非finite转null不可当0/PASS；worker私有diagnostic_observer异常归档ledger时映射implementation，当前candidate scope/修订预算未变。

## Closed Or Failed Directions
- 8旧held及负证据/修订限制保持，RSTR/PCE/FLE/HDS/CPA/M201未重开。RSTR明确授权9文件本地commit36b59daa保留，2修订耗尽、R2 mean1.027033878e-6>1e-6 FAIL；早先PASS/独立重算9.536743e-7不清hold。PCE额外修订已用，不自动R4。
- 旧M205 harness序列化/0D loss错误保留，原Criterion单元素shape[1]合法；当前numel1+finite。CGCA baseline一次0forward/0GPU前置资源拒绝非模型失败。
- 有限历史CCP(child+parent)、GEO(centroid/radius→Linear残差)与HAP未见完全等价/明确ban，非全面新颖性证明。HAP不是child+parent+DA，没有RSTR点质量守恒宣称。
- 前轮2个complete历史SERVERS证据仅冻结到同SHA60cba26a的tick_899d59f1/SERVERS.before.yaml；原结果/修订不变，不是科研进展，未改验证器/门槛。

## Running And Queue
- server4 pinned192.168.1.115/dl04-MS-7E06，GPU0 UUID958e741a、GPU1 UUID7f82edb9；allowed[0,1]/max1card。root=/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1、remoteHEAD898ff63a；本轮未推送HAP。
- 上海08:10:22 GPU0 PID3842306约18639MiB、GPU1 PID3873690约19751MiB仍有CUDA contexts，均非idle；GPU0 util0不能当空卡。原PID与canonical monitor持续进展一致。本轮只读NVML/锁状态，不重复已验证busy guard或staging，无torch/模型/数据/CUDA行为。
- 本轮canonical monitor继续至M205/M206均5/50；原正式训练进程持续，两项launch_verified，未重启/迁移/修改。waiting0，无终态/运维问题；新增准入/入队/启动0。
- HAP等待真实server4空卡、无其他CUDA context且取得必要locks；下一owned tick新token/原deadline/fresh lease及新私有stage，沿用精确f51823bb代码/原YAML/资产再核验，不重放旧stage lease。实际TRAIN两步+配对资源PASS才准入/安全同步/启动。retry_after2026-10-21T01:10:22.442766+00:00是1小时resource wake，非idle证明或授权。
- server3旧GPU1授权保留但外部任务不动，本轮未用；server6禁用。旧root Cluster_m201_bps_f8457d3b dirty YAML和diffSHAb79ba6017a1f624b70bc223526482626949f2f3a9ea6357e8b9e981379cfc8bd保持。本轮无reset/clean/stash/force/sudo/密码操作。

## Open Questions And Risks
- HAP正规方程平方条件数，FP32退化/default pinv cutoff须实测，禁止加ridge/改精度/调阈值绕过失败。rank(D)<=min(3,nchild−1)，单child/零D给parent-only；≤4仿射独立时detail=Hchild−mean，不能声称每组独特几何过滤。
- fine/mid末层constant bias梯度可为0，须观测非恒定child及parent路径。组token均值=parent非pointmass守恒；可能抹高阶语义/粗截距伤小目标。小3x3不免费，native数值/资源/收益待测。
- MDC固定轴旋转、跨coarse parent及fine-ID空洞边界保持；CGCA模糊/场景偏置未知。不能按首轮验证扫参、换seed或宣称最终有效。

## Last Tick
- 本轮bundle pipeline/diagnostic_bundles/tick_73e1f420：initial_resources、observer_v2_preparation/worker_v2、observer_control_check/execution、independent_observer_v2_review、report_notes_final/tick_result_final；初期tick_result/report_notes保留时间点记录。两项正式训练健康均5/50，无终态/运维变化或用户动作。
- 实际0新候选/0模型源提交/0原生执行/0准入/0队列/0启动；诊断worker v2只修异常留档，经静态+5个非tensor控制测试，不是native PASS。tick_attempt仍绑定本轮真实resource_check/blocked及新资源证据，GPU0 util0但context/显存未释放非空卡。
- 下轮空卡优先HAP实际native，fresh stage使用新reviewed worker_v2并重绑hash/lease；原模型/YAML保持。无新的训练结论、资源开放或用户动作，按通知约定静默；不因内部准备工作自动通知。
- memory/最终中文notes于finish前留档，收尾以tick_receipts/73e1f420ae624c0d8c0b9c7ed5c9e546.json及实际命令为准，不预写PASS。必须验证FINALIZED、lease released及owned lock/pending消失；释放后不写项目。
