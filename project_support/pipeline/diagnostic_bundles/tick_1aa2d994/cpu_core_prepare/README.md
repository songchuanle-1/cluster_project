# SINC CPU 核心测试，仅准备未执行

当前owner1aa2d994；新私有远端stage cpu_core_1aa2d994。默认NOP，作者只做AST/哈希核验，未导入准备模块、未执行测试/SSH/GPU。精确冻结simplex_incidence.py字节不改。仅CPU Torch/numpy/scipy；CUDA_VISIBLE_DEVICES为空，无torch.cuda API，CPU generator直接seed1999，CPU参数/张量。无framework/native模型/dataset/checkpoint读取或runtime写入；不调用任何旧生产shim。approved immutable base conda activation后使用固定project_cluster真实python及SHA。

固定测试：8组float64（singleton/coincident/collinear/planar/tetrahedron/Delaunay/duplicates/padded multiscene）加1组float32 Delaunay。实际forward与源码forward_reference输出、输入及全部7参数梯度比较，own_only同样比较；沿用RVE公差float64 atol2e-10 rtol2e-8，float32 atol5e-5 rtol5e-4。rank/repeated graph/crossleaf incidence/padding output与梯度为0/联合置换及leaf重标/scene与leaf隔离。实际CPU autograd+SGD(lr0.01)要求七参数有限非零梯度及每个真实更新。SGD只用于synthetic核心实现测试，与原native AdamW训练不同；不能替代native TRAIN2/task loss/common-init或资源门槛。

own_only保留同参数与factor incidence，切断nonself内容；检查所有nonself输入梯度精确0，原核心同leaf非self梯度与donor扰动响应非零、跨leaf/scene梯度0。参数使用原源码初始化，无fixture权重改写。Python/TorchCPU/numpy RNG恢复并记录；dtype/device/版本和源SHA记录。任何真实失败原样保存；不搜索/有利重跑。

root须当前owner独立review JSON，含owner,passed:true,material_concerns:[],reviewer_thread_id（与owner/作者不同）,FROZEN_sha256,producer_sha256,transport_sha256,source_sha256。使用python -B，GIT_OPTIONAL_LOCKS=0，匹配CODEX_THREAD_ID，运行run_cpu_once.py --execute-root --review ABS_REVIEW --review-sha256 SHA。保存本地exclusive intent/actual/captures；远端新stage存在则停止，不复用或重播。严格host-key/BatchMode/禁密码SSH、host/UID/python哈希绑定。本地剩余租约>180s，远端>150s；CPU软预算100s、远端观察110s、SSH观察120s。超时记录PID/保留输出、不给信号/不自动重试。

输出始终native_TRAIN/resources=NOT_RUN，efficacy/novelty UNKNOWN，admission_granted=false。当前GPU0实际free<20GB阻止native启动；本CPU测试不改变GPU0-only/cap1/原三锁/20GB门槛，不接管外部PID。root执行后需独立actual审查，不将测试包存在当PASS。

本轮只重绑执行owner与私有stage；旧包/旧review仍保留原owner，不能代替当前独审。旧CPU intent/actual/captures均本地不存在；该检查不声称远端状态已查询。作者未执行SSH、测试、默认NOP或共享写入。
