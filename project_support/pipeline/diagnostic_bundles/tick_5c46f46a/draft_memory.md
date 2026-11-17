# Codex Research Memory

## Goal And Phase
- 当前foreground token5c46f46a17514a6f984ad08364f0c7cc，owner01a159c5-29ab-7a22-ba7f-e79174757253；generated UTC2026-10-22 04:11:20.228657、原deadline05:11:20.228657。仍active，尚未finish，不预写FINALIZED/PASS。
- GoalSHA0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85；ScanRefer目标.5100，M95champion.5020/gap.0080，baseline.4894。Phase1 hierarchy→inst_feats→query/masks主线，supervision辅助不取代主线；Phase2仍需确认。
- 原生seed1999/epochs50/maxiters70/default10G保持；禁调参/新gate/语言routing/大QKV/pointN²/重复注入/新残差系/纯分布缩放/历史rejected改名重开。静态与CPU合成检查非native准入证据。
- Standing experiment_first_20261021.json SHA2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8覆盖常规实现/检查/版本/安全同步/准入训练，仍保留历史修订/数据/资源/原生resume显式授权合同。
- 最新人类“GPU1可以先暂停训练了 给别人腾出来一张卡”：仅server4 physical GPU0/max1，grant server4_gpu0_only_20261022_gpu1_pause_105409.json SHA1871f8c9777c548acfda87b9e91b72c2d5fc94ac78920430c52bdceea1cbd51e；GPU1无native/训练权限，M206不自动迁移/恢复，server3/server6与Windows Pipeline-cluster_project仍禁用，不改调度。

## Champion And Baseline
- M205-MDC已canonical complete/done_earlystop，epoch26/noimprove10/best.4872，较M95低.0148、baseline低.0022；保留此实现负训练结果，不泛化整条层级机制失败。
- M207-HAP在epoch19/50 step3665/4686遭DataLoader worker1 AttributeError，原PID979955消失；04:25:35UTC canonical finalize_task已按crashed归档，非earlystop/机制反证。原log SHA794be0ab616954c28ec8b120f57309c6443f7ba87133c983e2f506887ad84a59已精确拉本地，原准入/launch历史保留。
- HAP last snapshot于04:19:50UTC CPU核全：meta18/best.4975287616252899/noimprove0，model+optimizer642states/5groups+scheduler非空、allCPU/CUDA未初始化；epoch19部分进度未保存，非精确minibatch/RNG续接。
- HAP历史标准资源9.762944066G vsM95 9.762532428G，同bs1/lang1/warm20/repeat100，median46.254797vs43.596659ms/P9064.774761vs60.729895ms，参数157484090；unsupported pinv/index_add原样披露，标准计数非完整成本，不以中途best挑参。
- M206-CGCA仍user-paused/humanhold：完整snapshot meta24/best.4952535927295685/noimprove7、SHAe9b42b2632762dae5ca49d80b3272889809b1ffe3ec30dd377690af8cb2e8e9d。暂停非失败，不自动GPU0迁移；HAP授权不覆盖M206恢复。

## Active Hypotheses
- M207-HAP stable hierarchy-affine-coarse-to-fine-prolongation，commitf51823bbddf0f8095a9a5813bf1f8169e3d7edb0；原3FFNs后coarse→middle→fine仿射延拓，0新参数，原rawbanks/FPS/IDs/CSORT/HCG/末次inst路径保持。历史真实TRAIN2/backward+资源已准入，完整期效益未完成筛选。
- HAP现blocked/human_authorization/resume_stage training。hap_resume_plan.json已具体准备same native config/f518/GPU0/fullstate snapshot /data/songcl/Project/Cluster_project/pipeline/resume_snapshots/20261022_hap_crash_5c46f46a/20261022_002007/last.pth，SHA28ad9df5784c0287cc085df81faa10e0efe251cb417126034db1ad24d7e11966；预期从epoch19开始。
- 本次HAP human resume grant当前MISSING；cluster_resume.validate要求Explicit human resume authorization，standing不豁免。root用现成plan一次询问精确同实验续训；获授权仍需fresh空闲GPU0/UUID/锁/source/checkpoint与原生递增进度proof，无cold fallback/改best权重重训。
- M208-HRC stable hierarchy-bottom-up-refined-token-composition，commit9e543af623acd7fa9bd4a3f81ce79c932e98774a；h0FFN→原fixed-row mean_ids1→h1FFN→mean_ids2→h2FFN，仅去batchpadding、内部empty child FFN bias按原等权保留，3原FFN各一次/raw-CSORT/HCG保持。
- HRC nativeprep tick_86e41faa/hrc_native_prepare SHA4754db1a1c550c869596e0ca57cee99834239e8ed78e87ec65f68142f48c812a（worker37782c1…/runtime4737e6f…/templateea756a…）；adapter tick_9b40ab74/hrc_execution_adapter prep1ab29434e5a1e4f0144fd38e22d83f1ae561813973ed0468e64f65aac6c9a568/releasef2b3cdfe7a63cacf65e0d38837c4df1211715a31320f4d808d569c855a9e6d83；candidate外锚/独立审保持，native/resources NOT_RUN。
- M209-PSBR stable hierarchy-parent-segmented-bidirectional-token-state，commit74fcd21df0af9a971792038ffe251af1ffea2604，仅8独立源+原字节YAML；middle真support=ids1[ids0]，原ids2父组内detached原centroid xyz+ID序，共享Wx/无biasWh双向tanh每组归零，Wo拼接逆散原ID替换middle residual FFN；fine/coarse/LN/raw-CSORT/HCG/单inst更新保持。
- PSBR sourceprep SHA f1973052931bb76bb8a4087e1d1aff5d6e5051f2859227d4fbc74a7827020128；nativeprep tick_8fafa3d4/psbr_native_prepare SHA1e1de105f34ce4f6f87fe862bf35ee2c7c0bf26bf7404b0550559534a0e7472e（worker05ab6ac1…/runtimeb6698c77…/templatef90e2662…）；adapter prep9d6c98a4c406d052c5ae1d420053103b0ec08bf71fb0ce5c32de88dd49b5bb4b/releaseb17d424e493bcd49e1858bc6fc4b897d6fab5970a25240cea143e826f40e20d7，adapterc8aee02b…/remote9ea6f90d…；native/resources NOT_RUN。
- HRC/PSBR均blocked/live_external_gpu_occupation/resumevalidation；04:16:26UTC source_and_pause_reuse_check重核source/commit/冻结材料/候选外锚和28dirty保持。真实GPU0空卡优先已有HRC再PSBR，不为配额新建或重开hold。

## Closed Or Failed Directions
- 8旧hold保持：4辅助supervision scope、2measurement实现/未定hold、PCE与RSTR数值失败/修订上限；04:14:36UTC仅有界核同8条canonical记录/655旧证据引用签名，无新reopen/scope/额外revision授权，不重写历史。
- PCE默认2+额外1已耗尽/2.861e-6失败及13.86x延迟；RSTR默认2已耗尽/R2 mean1.027033878e-6>1e-6，旧passed或独立9.536743e-7不清失败。禁止PCE R4/RSTR R3；9文件commit36b59daa授权不是新修订，M201不自动恢复。
- 不重开pair-edge/moment/改MDC邻域或旧CCP/REAG失败路线；HRC/PSBR有限历史核对不代表全历史/文献新颖性或收益。
- HAP此次crashed是共享加载器运行异常，failure_scope实施/环境底因未定；保留19轮中断/.49752876，不标hypothesis rejected、完整50epoch结果或earlystop。

## Running And Queue
- 04:25:35UTC HAP crashed归档后running映射已清HAP，未创建恢复queue/task/grant；M206 waiting/paused_by_user+dispatch_hold/resume_authorizedfalse，不计readywaiting。HRC/PSBR均未准入/入队。
- GPU0最后fresh实观04:19:03UTC：UUID958e741a…、1687MiB/util37/context181902(1638MiB)，此前PID128551已消失；非原HAP，仍busy。陌生进程禁kill/驱逐/共享；GPU1释放且未查询，不因项目running空而推空卡。
- pinned server4 192.168.1.115/dl04-MS-7E06，allowed[0]/max1；root=/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1。04:19:03及04:22:48UTC canonical sourceverify确认remote exactHEADf518、datasetSHA2fb59f…、仅既定路径映射，无sync/checkout/source/环境变更。
- localHEAD74f(parent9e)，HRC9hash及原28dirty/untracked字节/status保持、index空；禁reset/clean/stash/force/sudo/密码读取。旧源/旧workeradapter/旧lease/原失败证据保持，过期lease不可重放。
- M206 snapshot /data/songcl/Project/Cluster_project/pipeline/resume_snapshots/20261022_gpu1_pause_105409/20261021_232736/last.pth，full CPU proof manual_ops/20261022_gpu1_pause_105409/checkpoint_evidence.json SHA8df6674c…；admitted898ff63与remote f518区别保留，未来需专属human grant和精确source/fullstate核。
- cluster_resume虽含server4物理0/1库存支持，仍须currentallowed/任务卡/双hashhuman授权proof/CPU全state/source/checkpoint一致；当前只0，不能从库存map越权GPU1，不互借HAP/M206授权/断点。

## Open Questions And Risks
- scannetv2.py430 np.where(boolTensor)→installed _tensor.py1226 self.numpy()报'Tensor'缺has_torch_function_unary；实际已通过global helper guard，不能简单说Python global缺失。dataloader_source_diagnosis.json SHAa9226fb3…，失败样本index/原长期worker状态/根因UNKNOWN。
- 04:21:23UTC真实同conda CPU核torch2.8.0+cu128/NumPy1.26.4，fresh进程1000迭代及4persistentworkers两轮2000合成样本通过，helper可调用/CUDA未初始化。无native数据/失败样本/原长期worker复现，不证明已修复；不改workers/persistent/np.where/环境。
- HAP snapshot无全RNG/loader worker state；resume从meta18+1而非3665步精确续接，epoch19部分重做，best/patience/model/optimizer/scheduler保留。完整log/fullstate/source proof在本轮包；复发仍可能。
- PSBR fork_rng(devices=[])仅隔离新构造CPU RNG，不manual_seed/改默认init；随机序列重用相关/tanh梯度/轴偏置/跨父组受限/串行延迟均待实测，参数delta−262912非资源PASS。实际common参数及两TRAINbatch指纹须真两目标比较。
- HRC TRAIN2/1e-6 mean参考/coarse→fine-mid依赖probe未跑，probe必须隔离.grad/opt/sched/RNG/nativehooks并finally恢复。PSBR offdiagonal/resetstate未实现未测，不新造准入门；含observer/probe smoke峰值非纯TRAIN，pureTRAIN UNKNOWN仅支持项。
- 两adapter仅raw四结果，无标准smoke/resource语义和配对formatter/receipt/queue/dispatch；31mock或raw completed非准入。root先比candidate精确prep/release/source外锚，内部hash自洽非授权；fresh owner/context/pending/goal/allowed[0]/原deadline/UUID/双idle/3flocks后才执行。
- 疑似超时只读核原stage/request/PID/startticks/argv/result，不重放/kill/删现场/续lease；跨tick只读不授权旧mutation。普通waiting/dependency不占槽，running/claiming/launch-uncertain保守保留槽。

## Last Tick
- 当前5c46f46a未finish：04:13:50发现HAP PID消失/epoch19日志；04:19:03实核crash/source与busyGPU0；04:19:50冻结CPU全state；04:21:23小CPU interop；04:22:48canonical sourceverify；04:24:49备精确resume plan；04:25:35canonical crashed archive，均为真实完成动作。
- 本轮保留8hold/28dirty/HRCPSBR冻结外锚，0新模型/0数值修订/0新commit/0sync/0准入/0queue/0launch；1个HAP运行故障已归档，CPU合成检查不算native或机制收益。
- 下一步root审核现成HAP plan并一次询问本次缺失human resume grant；未获不启动，不覆盖M206/GPU1。当前GPU0仍busy，HRC/PSBR真实resourceblocked，尊重所有陌生工作。
- 快照candidate_budget2/research_reserve_budget2是上限，不是造2候选任务；先推进已有HRC/PSBR。真实GPU0空且原deadline余量足够才fresh绑定，原TRAIN2双smoke+bs1/warm20/repeat100资源四进程；核真loss/backward/path/两批/common参数/资源输入handler unsupported后再标准汇总/准入/派发。每run>1020s门不保证四次同tick都完成，不延deadline。
- 本轮report/receipt/finish仍待root，不预写PASS/FINALIZED或锁已释放；这是供root审核的draft_memory，未替换共享memory/改旧证据/模型/环境/调度。
