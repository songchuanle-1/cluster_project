# Codex Research Memory

## Goal And Phase
- owner01a159c5-29ab-7a22-ba7f-e79174757253实际环境/execution_mode一致。前轮8bec58e9 FINALIZED/lease released及headless lock/pending消失已核验。当前008137b428f54f20a65fe71e999f13dc DESIGN，上海10-22 00:03:27快照/原deadline01:03:27（UTC16:03:27.572736/17:03:27.572736）；begin后M205真实terminal，HAP本轮native/准入/启动已完成。
- GoalSHA0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85；ScanRefer目标.5100，M95champion.5020/gap.0080，baseline.4894；Phase1 hierarchy→inst_feats→query/masks主线，辅助supervision不取代主线。seed1999/epochs50/maxiters70/default10G不变，禁止调参/门系/语言路由/大QKV/禁用route/残差系及历史重开，Phase2仍需确认。
- Standing pipeline/authorizations/experiment_first_20261021.json SHA2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8授权本项目代码/YAML/真实检查/版本/安全同步/入队训练，不重复确认常规操作；不解除历史修订、禁用项、数据/seed/schedule及资源边界。
- 最新直接人类“gpu1可以使用”覆盖此前GPU0-only对server4GPU1的限制，当前server4[0,1]每卡1任务；新grant pipeline/authorizations/server4_gpu1_reenabled_20261021_gpu1_reenable_152505.json SHA30f17c5bcb66782a255d7eed4bb00277e807bfea4e64a48a499ab749fadd2fa7。server3/server6仍allowed[]/dispatchfalse，不恢复旧fallback。Windows Pipeline-cluster_project仍Disabled，调度/goal/科学门槛未改。

## Champion And Baseline
- M205-MDC native自行earlystop：原日志明确epoch26/no-improve10/best.4872；比M95 .5020低.0148、比baseline .4894低.0022。精确PID3842306消失及GPU0无context实测，canonical可恢复archive已完成，state=done_earlystop/stage=complete；这是该实现负训练结果，不是整条hierarchy机制被证伪。
- M206-CGCA已在GPU1从固定epoch8 full checkpoint恢复，原optimizer/scheduler/best.4751223027706146/no_improve0加载在新launch日志明确。00:22:59原PID732137/starttime21298582/--resume argv保持，native10/50步骤2524→2525；最新验证Best未在本轮额外读取，不能把恢复历史Best冒充新收益。
- M207-HAP native两步+配对资源通过且正式GPU0训练；00:22:59 native1/50步骤346→347，新PID979955/starttime21613920。验证准确率/完整训练稳定性UNKNOWN，不从smoke loss选择机制或宣称gain。
- HAP标准计数9.762944066G vsM95 9.762532428G；同bs1/lang1/warmup20/repeat100/input/原3fvcore文件：median46.254797 vs43.596659ms(+6.097%)，P9064.774761 vs60.729895ms(+6.660%)，参数均157484090。预测peak936769536 vs936763392bytes(+.000656%)；TRAIN同2批peak7426868224 vs7418928128bytes(+.1070%)，非full-run worst-case保证。
- HAP pinv2/index_add等unsupported完整披露，标准计数不是完整算子成本；资源mode无spy，实际计时/显存包含执行。GPU1有M206并行，不能横比旧M205 idle-host绝对延迟。旧M2059.7331723G及M2069.764703308G等原资源证据仍保留。

## Active Hypotheses
- M207-HAP stable hierarchy-affine-coarse-to-fine-prolongation，commitf51823bbddf0f8095a9a5813bf1f8169e3d7edb0，原8独立源+nativeYAML内容不变。3原FFNs后coarse→middle→fine：D=occupied child centers−组均值，A=pinv(D.TD,hermitian=True)@(D.T@原refined child)，新child=更新parent+DA，返回fine/middle、coarse外部保持。新operator0参数、无learned gate/child residual/QKV/seed扫参，原FPS/featurepool/CSORT/HCG/末尾inst_feats路径保持。
- occupied由真实point沿原ids向上传播，排除padding/空ID；几何FP32 detached、特征RHS/detail在autograd。训练首次真实4scene/16expression同两批与M95指纹匹配；HAP losses9.6735115/13.9038401，对照9.5291233/13.9095869，无效果推断。
- native原train.train+原loader两步完成：每步618个observed gradient tensors全部finite，3FFNs均非零weight grad且逐级初末hash改变。新operator两次forward/backward，3输入/2输出及fine/mid非恒定、coarseparent梯度实测非零finite，32次actual G/pinv输入返回全finite、原调用恰1次/default tolerances/hermitianTrue/原函数finally恢复、observer完整。
- 当前fresh材料tick_008137b4/hap_prepare，reviewed worker_v2 SHAffb2e09a53f3e860b398b435674ca0800b9641f5e48391d1af0d3098b8698a73逐字节未改；native_runtime/manifest/execution_lease绑定本轮token/原deadline/物理GPU0 UUID958e741a/3flocks/双空闲检查，核验后才importtorch。独立mdc_review/pce_audit均静态及实测只读复核，无技术门阻断。
- HAP收据pipeline/admissions/M207-HAP.json SHA61aded24398cb95d2296c3fc3fffeeb6e2960e6e9646fffc2d18c466ea564c59，四门native/resources/constraints/independence及standing授权真实绑定，效益UNKNOWN。stage=training/training_status=running；首筛保持原数据/pretrain/seed/50epochs/maxiters70，未从trainedM95全模初始化。
- M206-CGCA stable hierarchy-coarse-conditioned-fine-channel-attention，原898ff63a2cf63d3895a9e86c0ee3d1e5b672b335/admission不变、stage=training/running_resumed；coarseGram→fine channel算子0新参数，旧GPU1 PID3873690暂停/GPU0 waiting/最新GPU1恢复历史完整保留。

## Closed Or Failed Directions
- M205-MDC（hierarchy-middle-directional-token-convolution）已complete/done_earlystop .4872@native26/50，保留59013e132241322054f1906e771aa78b81c48da6原准入/launch proof及负结果。精确原run35MB日志经remoteSHA匹配拉至Checkpoints/server_4/exact_m205_20261021_050739；调用canonical finalize_task归档，不kill、不人为增加deathwatch计数、不改阈值。terminal日志不意味着last.pth保存到该epoch，checkpoint留远端。
- 8旧hold保持：4supervision辅助scope、2measurement实现/未定hold（同输入FP32差1.907e-6>1e-6，不是机制反证），PCE默认2+额外1已耗尽/2.861e-6失败与13.86x延迟，RSTR默认2已耗尽/committed R2 mean1.027033878e-6>1e-6。旧passed或独立重算9.536743e-7不清最终RSTR失败，PCE不自动R4/RSTR不R3；RSTR授权9文件localcommit36b59daa不是新修订。M201不自动恢复。
- 最近有界旧hold复核tick_f8150790/due_hold_readonly_review.json，无指定新授权wake或保门修复；本轮资源开放不解除科学/scope/修订hold。旧complete历史SERVERS引用冻结到同SHA60cba26a的tick_899d59f1/SERVERS.before.yaml，不重写原结果或验证器。
- 本轮有界备用方案审查未形成足够独立候选：换M205邻居/核近调参后继，moment/coarse-to-fine与HAP/FLE/PCE/M206重叠，pair关系token缺独立任务证据且近既拒readback。0新candidate，留空储备；不是全局路线穷尽或新假设被证伪。
- 首次HAP派发被错误queued候选标签阻止（未sync/启动）；纠正为canonical deployment后同原gate通过。首次额外只读部署YAML比较忽略允许work_dir映射而失败；确认唯一该差别后新proof通过。两个原错误证据保留，无模型修改/重训/门槛放宽/实现修订消耗。

## Running And Queue
- server4 pinned192.168.1.115/dl04-MS-7E06，allowed[0,1]/max1card；GPU0 UUIDGPU-958e741a-e5cf-127e-ffe8-9b984e1f404c，GPU1 UUIDGPU-7f82edb9-f620-8045-caea-a75232265cd1。root=/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1，现HEADf51823bb，仅ff9个HAP新增文件；common/M206既有源码未改，未传输本地脏RSTR/旧脚本/未跟踪PCE/BCCA文件。
- 三账：M205 done_earlystop已归档不占卡，M207-HAP running/GPU0/PID979955/launch_verifiedtrue，M206-CGCA running/GPU1/PID732137/launch_verifiedtrue；running[server4]0=M207、1=M206。最终原生步数双卡递增；00:22:59显存GPU0约13859MiB/GPU1约19795MiB，无额外context。
- HAP正式config configs/Quard/ctf_hcg_csort_hap/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hap.yaml；新log root/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hap_20261022_001959.log。formal launch仅允许work_dir路径适配，所有其他YAML值与control相同；测试/部署8源hash一致，新训练checkpoint是否已保存UNKNOWN。
- M206 log仍root/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cgca_20261021_232722.log；原fixed resume /data/songcl/Project/Cluster_project/pipeline/resume_snapshots/20261021_gpu0_resume_031718_r2/20261021_051530/last.pth SHA2e11ea38ba81b657301a34efc11483455fb1f9eeb83a5f4d52fbc40ffb4669d7，CPU完整optimizer642states5groups/scheduler/meta保留，latest GPU1绑定proof见manual_ops/20261021_gpu1_reenable_152505。
- canonical cluster_resume.py已严格支持server4GPU0/1（116相关离线+独立22专门tests PASS），当前白名单/任务卡号/双hash人类授权proof/CPU完整state/source/checkpoint均须一致，无cold fallback。M206正跑版本仍898ff，不能因root新HEADf518而改写其身份；若将来再resume，旧exactHEAD合同会阻止直接冒用newHEAD，必须重新核精确admitted source，不能冷启动或放松guard。
- server3/server6仍禁用，旧dirty root/YAML/diff及外部job保持，无reset/clean/stash/force/sudo/密码读取。新tick snapshot beforeM205终态capacity2/running2/waiting0/reserve_budget1/creation1；本轮只完成已备HAP，实际末态仍running2/waiting0，未为填槽造新路线。

## Open Questions And Risks
- HAP实测max|Gplus|1308527.125，max GGplus幂等误差.114782333；finite/native gate不证明条件良好、精确投影、完整期稳定或准确率收益。正规方程平方条件数/defaultFP32cutoff风险保留，禁止为了PASS加ridge/改精度/调阈值；无预注册门不事后捏造失败阈值。诊断matrix_rank0/1/2/3是额外API，不是backend pinv保留秩。
- rank(D)<=min(3,nchild−1)，单child/零D parent-only；≤4仿射独立时detail=Hchild−mean，不能说每组独特几何过滤。组token均值parent不等于pointmass守恒，不套用RSTR声称；可能抹高阶语义/伤小目标。细/中FFN常数bias梯度可0，已按非恒定weight/path观测。
- 保留M205负训练结果，HAP与M206均待正式验证。无新验证挑参/换seed、无历史重开或额外数据/标注授权。下一轮先实际监控两卡/终态，按新快照决定储备；旧tick lease/stage不可重放。

## Last Tick
- 本轮pipeline/diagnostic_bundles/tick_008137b4完整留档：M205真实terminal/精确日志/可恢复archive；HAP fresh stage、2个原TRAIN smoke+2个resource进程、四门/数值风险/独立review/收据/队列/正式launch proof。最终proof_r2 00:22:59 GPU0 HAP1/50 346→347，GPU1 M20610/50 2524→2525。
- tick_attempt绑定当前generated_at2026-10-21T16:03:27.572736Z、HAP native_smoke/passed和新evidence。1既有candidate准入/1新queueID/1正式启动，0新candidate/0实现修订；M205归档1，M206原进程保持。两次操作元数据/观察断言错误保留并具体修复，不当成模型失败。
- 手动next_batch决策pipeline/decisions/20261022-001620_next_batch.md记录M205终态与HAP有风险但现有技术门通过的训练决定；科研效益未预判。报告notes与tick_result.json保存实际动作/结果和UNKNOWN，不把常规计数当成功率。
- 当前前台lease收尾待实际report/finish，以tick_receipts/008137b428f54f20a65fe71e999f13dc.json及命令为准，不预写PASS。须核FINALIZED/lease released及pipeline/headless owned lock/pending消失，释放后不写项目。M205完成+HAP原生准入/启动是实质进展，本轮NOTIFY中文运行/完成/新准备/需处理简报。
