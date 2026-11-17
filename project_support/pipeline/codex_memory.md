# Codex Research Memory

## Goal And Phase
- 仅cluster_project；server4物理GPU0/UUIDGPU-958e741a-e5cf-127e-ffe8-9b984e1f404c；共享允许，max_tasks_per_gpu1/启动实际directfree>=20000MiB/原training-diagnostic-exclusive三锁。无空卡/零context/低util要求。
- GPU1/其他服务器禁用，M206/M227独立人工暂停；不驱逐、信号、重启、迁移，不改目标、数据、seed1999、epochs50/max_iters70、原loss/optimizer、10G及条件15%显存门槛、bans或调度。
- Pipeline-cluster_project Disabled；ownerthread01a159c5-29ab-7a22-ba7f-e79174757253；canonical foreground/python-B/PROJECT_ROOT=D:/project。

## Champion And Baseline
- 原目标.5100，M95冠军.5020/baseline.4894保持；技术准入/partial不作效力或novelty证明。
- WFC完整epoch30 best.49711745977401733；NEC完整epoch23 best.49454113841056824；MIC完整epoch26 best.49881425499916077。均不重启。

## Active Hypotheses
- M236-CSO本轮actual sourceaf457(parentd214)/私有runtimeb1；两自然TRAIN loss9.573954582214355/13.908418655395508、common841完全相等、九core有限非零梯度/每步更新及HCG/inst/ILA/mask实际路径均独审通过。不重跑旧CPU21。
- 同原固定样本/bs1/lang1/warm20/repeat100资源9.645764684G FLOPs/allocated934827520B/median35.407514544ms/P9036.583361775ms独审通过；历史M95非同时，不声称结构加速；整optimizer训练峰值和无cluster delta未知。
- 既有integration5413102(parentb1)与af457 source9逐字节版本关联另存并独审，原NULL/owner不补签；技术准入receipt pipeline/admissions/M236-CSO.json SHA07b56b16948f7f7e1a4a0682fd6abc81d3eda586e05ae4424f89d16005d8be09。

## Closed Or Failed Directions
- M235-SINC crashed archiveb75c9152d7fd4ecea9af538101d777d4/sourceb1，partialepoch2/1870of4686，完整saved metadata仅epoch1；原Adam list.grad根因UNKNOWN，未修复、不自动恢复。
- NSD M232 partial1/1961无完整验证/pth；HVD M230 partial5/1449/saved4；PSC M231 partial2/984/saved1。旧CPU/短测不代表长期修复。
- 全部旧scope/numerical holds、已消费授权、失败/原NULL保留；不改名重开bans；M206/M227保持人工暂停。

## Running And Queue
- 当前无项目训练；M236已准入/入队waiting并真实safe_sync b1→5413。启动前directfree10848MiB<20000拒绝；无dispatch intent/原生训练/新prod marker，外部任务未触碰。
- 新生产runtime/cso_path_prod_c1fe2178_v2已安装且未消费；source/collect/render独审通过。该owner有时限，未来owner必须另存绑定/stage/lease，不能沿旧owner重用；task专属资源/执行rebind hold保留。
- 主SERVERS仍旧已消费rvec入口；未来派发必须复用已审v2逻辑建立新scoped server-copy/source resolver，禁止直接调用原consumed shim。实际runtime HEAD5413，不重复sync b1。

## Open Questions And Risks
- 模型native及测量resources已PASS，当前是显存分配拒绝，不能改写为模型失败；精度/novelty仍UNKNOWN，未正式训练。原Torch/Adam长期故障未以两步PASS宣称修复。
- generator v1 batch schema错误另存v2修正/独审；生产v1 collect因text=True把CRLF归一化而已知终态拒绝，无Torch/GPU；只读reconcile后新v2以raw git_blob修正，旧失败/FROZEN/intent/stage保持。
- 新native/production直接memory.free，生产锁内source/cap1/free/deadline后才marker，解释器-B/原三FD继承；不续旧lease、不补NULL、不盲重放。strictkey仅pinned songcl@192.168.1.115/dl04，不读密码/旧IP/假设sudo。

## Last Tick
- c1fe2178：起初GPU0 directfree32016可用，完成最近M236真实缺项与独审，一项技术准入/入队、既有5413的真实safe_sync和新生产v2安装/collect/render均完成。
- 正式dispatch prelaunch因新外部任务占用、actualfree10848<20000拒绝；未写dispatch intent/消耗marker/启动。已新实际reconcile和独审，仅M236保留资源+新owner绑定hold，1h复查；有效native/resource证据复用。
- goal/SERVERS/主HEAD0747/index/dirty37、其他161候选及M206/M227保持。证据pipeline/diagnostic_bundles/tick_c1fe2178；后续只在真实槽位和新绑定核验后启动并确认步数增长。
