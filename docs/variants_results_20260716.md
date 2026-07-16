# Cluster 项目模型变体与实验结果总览

> 生成时间：2026-07-16
> 数据来源：`cluster_project/Checkpoints/server_4/` 全部训练日志（按 `mIoU: 0.xxxx` 解析，取每个模型 Best mIoU 最高的 run）
> 共 **41 个**产生过验证 mIoU 的模型变体

---

## 1. 全量结果排行（按 Best mIoU 降序）

| # | 模型 | Best mIoU | Best Ep | Final mIoU | #Ep | 状态 |
|---:|---|---:|---:|---:|---:|---|
| 1 | `c2f_enc_lite_posA_l1` | **0.5012** | 19 | 0.4955 | 24 | ✅ 完成 |
| 2 | `c2f_enc_lite_posA` | 0.5009 | 15 | 0.4912 | 24 | ✅ 完成 |
| 3 | `c2f_enc_lite_l1` | 0.5006 | 21 | 0.4890 | 26 | ✅ 完成 |
| 4 | `quard2_nomask` | 0.4997 | 16 | 0.4961 | 20 | ✅ 完成 |
| 5 | `c2f_enc_lite` | 0.4992 | 13 | 0.4876 | 22 | ✅ 完成 |
| 6 | `c2f_enc_lite_l3` | 0.4981 | 18 | 0.4916 | 24 | ✅ 完成 |
| 7 | `c2f_enc_lite_noroute` | 0.4972 | 17 | 0.4812 | 27 | ✅ 完成 |
| 8 | `gbcr_langc2f_scale_l1` | 0.4967 | 16 | 0.4877 | 30 | ✅ 完成 |
| 9 | `c2f_enc_lite_cag` | 0.4962 | 13 | 0.4954 | 18 | ✅ 完成 |
| 10 | `gbcr_adaptive_l1` | 0.4961 | 17 | 0.4868 | 22 | ✅ 完成 |
| 11 | `gbcr_langroute_l1` | 0.4956 | 15 | 0.4867 | 21 | ✅ 完成 |
| 12 | `c2f_enc_lite_posB` | 0.4953 | 13 | 0.4884 | 21 | ✅ 完成 |
| 13 | `gbcr_balanced_l1` | 0.4952 | 20 | 0.4822 | 38 | ✅ 完成 |
| 14 | `c2f_enc_lite_posC` | 0.4952 | 13 | 0.4937 | 16 | ✅ 完成 |
| 15 | `gbcr_langc2f_l1` | 0.4950 | 15 | 0.4855 | 18 | ✅ 完成 |
| 16 | `c2f_enc_lite_init0` | 0.4949 | 19 | 0.4890 | 23 | ✅ 完成 |
| 17 | `gbcr_local_l1` | 0.4943 | 19 | 0.4840 | 33 | ✅ 完成 |
| 18 | `c2f_enc_lite_l4` | 0.4931 | 20 | 0.4889 | 25 | ✅ 完成 |
| 19 | `c2f_enc_lite_posA_l1_layerscale` | 0.4921 | 18 | 0.4818 | 29 | ✅ 完成 |
| 20 | `c2f_enc_lite_cfe` | 0.4901 | 13 | 0.4854 | 15 | ✅ 完成 |
| 21 | **`model_base1`（基线）** | 0.4894 | 15 | 0.4738 | 30 | ✅ 完成 |
| 22 | `c2f_enc` | 0.4891 | 12 | 0.4812 | 15 | ✅ 完成 |
| 23 | `c2f_pq` | 0.4864 | 13 | 0.4805 | 14 | ✅ 完成 |
| 24 | `gbcr_pointgate_l1` | 0.4841 | 11 | 0.4822 | 12 | ✅ 完成 |
| 25 | `c2f_enc_lite_posA_l1_noroute` | 0.4800 | 10 | 0.4800 | 10 | 🔄 **训练中**（07-16） |
| 26 | `topk_c2f_bottleneck_l1` | 0.4794 | 8 | 0.4788 | 9 | ✅ 完成 |
| 27 | `cluster_fixed_ctx_l1_ls` | 0.4790 | 10 | 0.4790 | 10 | ✅ 完成 |
| 28 | `cluster_fixed_ctx_l1` | 0.4760 | 12 | 0.4760 | 12 | ✅ 完成 |
| 29 | `c2f_enc_lite_attnpool` | 0.4711 | 7 | 0.4711 | 7 | ✅ 完成（早期停） |
| 30 | `base2_quard2_c2f` | 0.4690 | 15 | 0.4511 | 46 | ✅ 完成 |
| 31 | `c2f_enc_lite_posenc` | 0.4689 | 7 | 0.4689 | 7 | ✅ 完成（早期停） |
| 32 | `base2_quard2_c2f_enc` | 0.4664 | 12 | 0.4622 | 20 | ✅ 完成 |
| 33 | `base2_quard2_l1` | 0.4655 | 14 | 0.4523 | 34 | ✅ 完成 |
| 34 | `base2_quard2_c2f_enc_gm1` | 0.4652 | 13 | 0.4513 | 16 | ✅ 完成 |
| 35 | `base2_quard2_c2f_pq` | 0.4646 | 12 | 0.4461 | 50 | ✅ 完成 |
| 36 | `model_base2` | 0.4641 | 17 | 0.4580 | 24 | ✅ 完成 |
| 37 | `base2_quard2_nomask` | 0.4633 | 21 | 0.4555 | 30 | ✅ 完成 |
| 38 | `base2_quard2` | 0.4598 | 15 | 0.4598 | 15 | ✅ 完成 |
| 39 | `c2f_enc_lite_posA_l1_true_route` | 0.4468 | 6 | 0.4468 | 6 | 🔄 **训练中**（07-16） |
| 40 | `cluster_hier_add_l1` | 0.4041 | 3 | 0.4041 | 3 | ❌ 早期失败 |
| 41 | `cluster_hier_content_l1` | 0.3659 | 2 | 0.3659 | 2 | ❌ 早期失败 |

> 表中模型名省略了 `model_base1_` / `model_base2_` 前缀以便阅读。

---

## 2. 按研究主线分组

### 2.1 主线 A：C2F-Enc-Lite（当前主模型候选，base1 架构）

编码顺序、注入位置、轻量化回读是核心变量。基线 `model_base1` = 0.4894。

| 变体 | 关键改动 | Best mIoU | Δ vs base1 |
|---|---|---:|---:|
| `c2f_enc_lite_posA_l1` ★ | PosA 注入 + L1（仅第6层，独立包复现） | **0.5012** | **+0.0118** |
| `c2f_enc_lite_posA` | 注入顺序 `lla→lia→cluster→ila` | 0.5009 | +0.0115 |
| `c2f_enc_lite_l1` | 仅后1层启用 cluster att | 0.5006 | +0.0112 |
| `c2f_enc_lite_l3` | 后3层 | 0.4981 | +0.0087 |
| `c2f_enc_lite_l4` | 后4层 | 0.4931 | +0.0037 |
| `c2f_enc_lite` | 后2层（默认） | 0.4992 | +0.0098 |
| `c2f_enc_lite_init0` | gate 初始化=0 | 0.4949 | +0.0055 |
| `c2f_enc_lite_noroute` | 去 C2F 路由约束 | 0.4972 | +0.0078 |
| `c2f_enc_lite_cag` | cluster-aware gate | 0.4962 | +0.0068 |
| `c2f_enc_lite_cfe` | — | 0.4901 | +0.0007 |
| `c2f_enc_lite_posB` | 注入顺序变体 B | 0.4953 | +0.0059 |
| `c2f_enc_lite_posC` | 注入顺序变体 C | 0.4952 | +0.0058 |
| `c2f_enc_lite_posenc` | 位置编码变体 | 0.4689 | −0.0205 |
| `c2f_enc_lite_attnpool` | attention pooling | 0.4711 | −0.0183 |
| `c2f_enc` | 早期较重版（N×Q 全注意力） | 0.4891 | −0.0003 |

**结论**：PosA + L1（仅最后一层注入）是当前最佳点 0.5012；注入深度 L1 > L3 > L4；PosA 注入顺序最优；posenc/attnpool 明显有害。

### 2.2 PosA-L1 独立变体（07-15 设计，07-16 在跑）

共同约束：编码顺序 `LLA→LIA→Cluster→ILA→FFN`，仅第6层，尺度 `[256,64,8]`，top-k `[32,16,8]`。

| 变体 | 唯一变化 | Best mIoU | 说明 |
|---|---|---:|---|
| `posA_l1` | 对照组，复现 legacy C2F + sigmoid(0.1) gate | **0.5012** | 复现成功，新最佳 |
| `posA_l1_layerscale` | gate 改可正可负 LayerScale(1e-3) | 0.4921 | LayerScale 反而更差 → 正值 sigmoid 门控更好 |
| `posA_l1_noroute` | 删 query Q/K/V + top-k 路由，仅 cluster→point gather | 0.4800 (10ep) | 🔄 训练中，待收敛后判断路由 FLOPs 是否值得 |
| `posA_l1_true_route` | 按 fine top-k 真实路由回写 | 0.4468 (6ep) | 🔄 训练中，当前偏低，疑似改动过大导致初期不稳 |
| `posA_l1_detail`（有目录无日志） | 注入 `LN(point−context)` 保细节 | — | 尚未跑/无验证结果 |
| `posA_l1_cosine/poly50/step`（有目录无日志） | LR schedule 变体 | — | 尚未跑 |

### 2.3 主线 B：GBCR（几何路由，base1 架构）

固定预算、local-preserving 的纯几何/语言路由对照。

| 变体 | 路由方式 | Best mIoU |
|---|---|---:|
| `gbcr_langc2f_scale_l1` | 语言粗路由 + scale | 0.4967 |
| `gbcr_adaptive_l1` | 纯几何自适应路由 | 0.4961 |
| `gbcr_langroute_l1` | 语言路由 | 0.4956 |
| `gbcr_balanced_l1` | 平衡路由 | 0.4952 |
| `gbcr_langc2f_l1` | 语言 C2F | 0.4950 |
| `gbcr_local_l1` | local-preserving | 0.4943 |
| `gbcr_pointgate_l1` | point gate | 0.4841 |

**结论**：GBCR 整体落后 PosA 约 0.0048 mIoU；语言路由复杂度未带来 >+0.002 的可靠增益，已停止优先。

### 2.4 主线 C：早期 cluster / top-k 对照

| 变体 | Best mIoU | 说明 |
|---|---:|---|
| `topk_c2f_bottleneck_l1` | 0.4794 | top-k 瓶颈 |
| `cluster_fixed_ctx_l1_ls` | 0.4790 | 固定上下文+ls |
| `cluster_fixed_ctx_l1` | 0.4760 | 固定上下文 |
| `cluster_hier_add_l1` | 0.4041 | ❌ 训练崩塌 |
| `cluster_hier_content_l1` | 0.3659 | ❌ 训练崩塌 |

**结论**：早期/固定上下文注入均不及后层 lite 注入，hier_add/content 路线失败。

### 2.5 base2 架构系列（无 ila，整体弱于 base1）

| 变体 | Best mIoU |
|---|---:|
| `base2_quard2_c2f` | 0.4690 |
| `base2_quard2_c2f_enc` | 0.4664 |
| `base2_quard2_l1` | 0.4655 |
| `base2_quard2_c2f_enc_gm1` | 0.4652 |
| `base2_quard2_c2f_pq` | 0.4646 |
| `model_base2` | 0.4641 |
| `base2_quard2_nomask` | 0.4633 |
| `base2_quard2` | 0.4598 |

**结论**：base2（无 ila）整体比 base1 低约 0.025 mIoU，ila（语言→实例反向注入）是关键组件，已确认 base1 为主线。

---

## 3. 当前研究阶段判断

1. **最佳模型**：`c2f_enc_lite_posA_l1` = 0.5012（07-15 独立包复现 PosA+L1，略高于原 posA 0.5009，可复现性确认）。
2. **效率最优候选**：`c2f_enc_lite_l1` = 0.5006 @ **9.59G FLOPs**（PosA 系约 9.70G）。
3. **稳定上限对照**：`quard2_nomask` = 0.4997 @ Final 0.4961（平台最稳，但 19.91G，2× 计算量，不作主模型）。
4. **筛选标准**已从单点 Best mIoU 转为「收敛平台 + 计算成本 + 机制可证性」三者共同筛选。
5. **待决关键问题**（07-16 在跑的两个实验直接回答）：
   - `posA_l1_noroute` 收敛后若不降 → 证明 legacy C2F query routing 是无效 FLOPs，应改用无路由轻量基线。
   - `posA_l1_true_route` 只有显著优于 noroute → 才能证明 coarse-to-fine query routing 本身有效。当前 6ep=0.4468 偏低，需观察是否只是初期不稳。

---

## 4. 未跑/无验证结果的变体（仅有代码或目录）

`posA_l1_detail`、`posA_l1_cosine`、`posA_l1_poly50`、`posA_l1_step`、`c2f_enc_lite_agg`、`c2f_enc_lite_prune`、`c2f_enc_lite_qcond`、`c2f_enc_lite_multi`、`c2f_enc_lite_posA_l1_cosine`、`hca_c2f_parent_l1`（有日志目录）、`hca_coarse_l1`（有日志目录）、`topk_c2f_cosine_l1`（有日志目录）等。这些需检查日志是否仅 profile 或未完成首次验证。
