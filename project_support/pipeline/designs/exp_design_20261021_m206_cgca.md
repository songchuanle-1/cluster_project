# M206-CGCA 粗层引导细层通道注意实验

假设：M95 的多尺度 token 独立经过 FFN，fine token 的通道解释缺少由粗层场景内容生成的显式跨通道关系。CGCA 用粗层8个token计算每组32通道的关系，再混合每个 fine token 自身通道值，使粗层信息在原 HCG 回读前影响细层表达。任务效益尚未验证。

对每个原有 head，Z=LayerNorm_C(Tcoarse)；A=softmax(ZᵀZ/√Kcoarse,dim=-1)；Tfine′=Tfine Aᵀ。只使用实际 occupied coarse ID，排除 padding/ID 空洞，Kcoarse 为实际行数。保留中层/粗层、全部原 FFN、CSORT raw-bank 辅助项、HCG 和原最后一层 inst_feats 更新。新增零参数，但新增 coarse→动态非对角 channel operator→fine 的信息边；没有新 gate/residual/QKV、点级 N² 或超参数搜索。8个通道组来自原 nhead，不是扫描值。

独立九文件模型/YAML，不导入或修改 champion 或正在训练的 MDC。数据、seed1999、50epochs、max_iters70、原 AdamW 和学习率均不变。首筛以完整原生训练的验证 mIoU 判断，不以两批 loss 升降或诊断子集选型。

真实原生训练 smoke 已完成两次有限 loss/backward/optimizer step；full_backward_hook 确认本模块 fine/coarse 输入边和输出均有限非零。零参数模块不伪造‘新增参数更新’，观察既有 fine/coarse FFN 的更新。版本与实际执行证据见 cgca_version_native.json/cgca_native_smoke.json。配对 fvcore FLOPs、同样本 bs1/warmup20/repeat100 的延迟/推理峰值显存，以及同原生批次的优化器峰值对照完成后，才生成准入收据并使用 GPU1。

有限历史比对：XCA 是 token 轴拼接注意力；CSF 为 fine Q/coarse K/V 的 token 跨尺度注意力；CGA 是 feature-cosine top8 图与大 QKVO；WCA 为 weighted pooling。未发现完全相同的 coarse-Gram 通道图，但不宣称整体新颖性。风险包括细粒度判别通道被混合抹去、粗层大物体/场景偏置、泛化鲁棒性未知。未恢复旧挂起路线，也未改变数据/资源/训练门槛。
