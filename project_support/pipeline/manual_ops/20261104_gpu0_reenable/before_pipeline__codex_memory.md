# Codex Research Memory

## Goal And Phase
- 最新直接用户指令“先暂停这两个实验 停止使用”（2026-11-01）：WFC/LFT均人工暂停，server4 allowed_gpus=[]/dispatch_enabled=false；GPU0/1停止使用，后续显式授权前禁止自动恢复、替补训练、GPU诊断或迁移。历史双卡授权已被本次暂停覆盖。
- 最近研究owner25fc0b57已于2026-11-01T02:13:17Z释放；本次人工操作无active研究租约。真实root thread01a159c5-29ab-7a22-ba7f-e79174757253与foreground target一致。
- Phase1目标mIoU .5100；冠军M95 .5020/baseline .4894/gap .0080。原YAML/data/pretrain/loss/optimizer/precision/seed1999/50epochs/maxiters70/patience10、10G/原conditional15%/bans不变，Phase2人工。
- 目前无GPU使用授权：server4两卡停止使用，其他服务器新dispatch仍禁用；goal0441/closure2993及历史科学协议不变，旧SERVERS19b3和GPU1grant6529仅为历史，Pipeline-cluster_project仍Disabled。

## Champion And Baseline
- 冠军不换。旧SFC .49663493037223816@20/epoch30、ELC .5015384554862976@21/epoch31正常早停，archive2816/c437及精确校正018c保持；本轮无新正式终态。
- generic归档stdout舍入/空log路径局限不改，终态须核完整native日志/远端SHA；原CSV换行失败与binary atomic仅两行修复保留。旧AOC .500072062/b132、FCB stopped_unknown/be337和PES clip_grad_norm原失败/partial .4211保持，不重开。
- 上轮9b3167ef实际FINALIZED/PASS/context_committed/released于2026-11-01T00:12:55.763045+00:00；只说明轮询审计完成，不代表科学收益。

## Active Hypotheses
- M226-WFC：原无序楔机制、原数据/seed/schedule/patience不变。M226-WFC 原PID2085005/start105948793/source94c4fe61b38f46f321a7ee84236fea70ade04d9b/GPU0；2026-11-01T02:10:51.472499+00:00→2026-11-01T02:10:54.487610+00:00 TRAIN[24, 1831]→[24, 1836]，log+1320B；23次已完native val best 0.49711745977401733/noimp3，最近0.48659926652908325，均为部分验证。
- M227-LFT：原P/U三角分析→3packedFFN→逆合成、原协议不变。M227-LFT 原PID2685912/start106767833/source4457a46f9075f61e83340aa0f0af87d5bf4e986c/GPU1；2026-11-01T02:10:54.517459+00:00→2026-11-01T02:10:57.532613+00:00 TRAIN[20, 1509]→[20, 1515]，log+1584B；19次已完native val best 0.4977978467941284/noimp2，最近0.4934862554073334，均为部分验证。
- LFT旧四臂db71/34bc/0625/7bf1/b06c、receiptad0f/dispatch0b56与5931/4457历史保持；原资源9.781406796G、allocated937816064 vs936763392B、median88.3758 vs87.1037ms，无新latency/FP32门，效力/novelty/pureTRAIN峰未知。
- M228-NEC：节点h/边e双持久状态按真forest直径2/4交替组合；原7592/17ba/8cdc不变。94c2轮source6bc(parent4457)/proof8745/peer26db，native6c52/op53fe/48软件核dc8d/根NOPd92e/peer2b23均历史有效，本轮字节不动；native/resources NOT_RUN。
- M229-MIC：真fine祖先路径八顶点Möbius混合差分；实际单共享Linear/GELU处理8F，八slice七带符号运算含减phi0，同q分别按finepath直接mean回mid/coarse，原三层写回。原346a/a507/8dd/源审0a67与NULL母包不改。
- MIC e265轮已另存source041b(parent4457)，proof966a/源审8929；nativec887(24map)/worker5bdaa/runtime8867/templateba73/op4027(8map)合审1823。43软件检查首PASS a377，根默认NOP跨包集成81d0通过；两包DRAFTTrue/10activeNULL/notready，native/resources NOT_RUN。

## Closed Or Failed Directions
- 10旧holds、PCE2+extra1/RSTR2已尽预算、已消费HAP旧grant不变；M206-CGCA仍waiting/user_paused/dispatch_hold/noPID，GPU1授权不恢复它、M201或旧FCB。
- 旧APF/HPC/CTS/BFC negative/unknown及PES根因UNKNOWN保留，不能借MIC/NEC声称修复或改名重开。

## Running And Queue
- 最新手动操作20261101_dual_user_pause：WFC PID2085005/start105948793及LFT PID2685912/start106767833与12个同身份worker已通过pidfd SIGTERM停止，无SIGKILL；CUDA contexts已清空，两卡不再给本项目派发。
- queue/experiment为waiting + paused_by_user/user_paused，保留paused_run，清当前PID/running映射；resume_authorized=false且dispatch_hold生效。M206原暂停及其他153候选保持。
- M226-WFC：原日志及last/best保留，last CPU完整model/optimizer/scheduler核验通过，meta epoch=25、best_miou=0.49711745977401733；当前半轮未另存。
- M227-LFT：原日志及last/best保留，last CPU完整model/optimizer/scheduler核验通过，meta epoch=22、best_miou=0.4977978467941284；当前半轮未另存。
- NEC/MIC仍validation，native/resources NOT_RUN，未入队；不能作为替补启动。两运行历史source9/receipt/launch证据保留，不记作模型失败或完成，不改冠军。

## Open Questions And Risks
- WFC 0.4971/LFT 0.4978仍是部分验证，低于冠军.5020；不调参/改seed/重启/额外早停。NEC/MIC效力/novelty/预算未知，原whole新core聚合有限非零梯度与真实更新门保持，个别map/row/column/bias零合法。
- 两个原生包均需在真实空卡后另存受审active副本、绑定当轮owner/deadline/source/runtime/UUID及三锁；这是已有项目授权，不是新人工审批。草案意向GPU1，若0先空闲做受审元数据端口，不扩大白名单；不可补签10NULL或重放旧请求。
- MIC observer_block.py.txt是WIP组装模板，未含最终worker后加mean_active/CTX透传与finite捕获；合审已说明限制，最终冻结worker5bdaa才是权威。未来复制其真bytes，勿盲重跑模板组装器生成另一worker冒充通过审查。
- 原资源函数/handlers/unsupported/20warm100与原YAML保持；不用FP32消零/对称/finite-difference残差/Jacobian新门。仅python -B/dontwrite1、key+strictknownhost/hostname先核dl04/.115，无密码/旧.137/sudo/驱逐/全局skill或调度改动。

- 9b3167ef轮留档v1只匹配无leading0小数，遇0.x时在任何共享写入前assert；后续缺notes报告也在写前失败。原件/保护SHA证明与修复在tick_9b3167ef/local_persistence_failure_and_repair.json；仅私有格式v2支持0.x/.x，今后复用persist_routine_wait_v2.py，不盲用该轮v1。模型/运行/账均未受影响。

## Last Tick
- 最近研究tick25fc0b57已FINALIZED/PASS/released；本次是后续直接人工暂停操作，未创建研究tick/租约、不改调度、不启动新实验。
- 所属thread核对一致，canonical project monitor锁内先落禁用资源和dispatch_hold，再核hostname/dl04、原PID/start/UID/cwd/argv/stdout/source9/物理UUID，向14个精确原进程发SIGTERM，确认全退出及CUDA contexts清空。
- 停止后只用CPU检查完整已保存last与SHA、保留best及日志；不声称保存暂停瞬间半轮，后续恢复需显式用户指令与当时源码/检查点/资源再核。
- 原证据及停止/检查点回执：pipeline/manual_ops/20261101_dual_user_pause；SERVERS只改server4 allowed[]/dispatchfalse，GPU0/1停止使用。
