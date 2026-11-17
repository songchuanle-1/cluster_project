# RSTR：已测代码与试验设计

最终R2只准备一个结构候选。同parent细叶按固定质量可逆传输，真实写入inst_feats；没有训练结果。

完整源图数值控制最大0；实际native loss反向642个梯度有限，新传输输入/输出非零。8场景32表达matched identity0，content-vs-strict均非零；前景较无传输7/8场景变差、较strict错配6/8更好。技术可执行不等于任务有效。

同口径median 34.515→43.241ms（+25.28%）；P90 37.217→45.957ms；计数9.762532428→9.763134540G，推理峰值均936763392bytes，参数不增加。完整optimizer峰值、无cluster baseline资源差和整体新颖性未知。

请求范围仅为以下8个独立模型源文件及1份配置的本地Git提交。尚未获得该操作授权。

| 文件 | SHA256 |
|---|---|
| [__init__.py](<D:/project/cluster_project/Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rstr/__init__.py>) | `83be6cbd3d832529218452ebd21a56e11de651ea66c668477b6b78bffb9f6bd0` |
| [backbone.py](<D:/project/cluster_project/Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rstr/backbone.py>) | `57db8747d3c38136f568837d70e75ceea23e101900679db4931724ecb57665ca` |
| [dec.py](<D:/project/cluster_project/Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rstr/dec.py>) | `38d2853cc5b2c4c2081c0be5f81601bb75ccf5b56c9cddb748f6d2c606996ba2` |
| [hier_postprocess.py](<D:/project/cluster_project/Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rstr/hier_postprocess.py>) | `36a7c70dc656443dbcc4e8d634013cdd10b692537d10b2e29d5867b1eab147cd` |
| [loss.py](<D:/project/cluster_project/Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rstr/loss.py>) | `2d377aadb40c04feee7c04523ef7654d251ed934ed2f923551649ee9ef584869` |
| [network.py](<D:/project/cluster_project/Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rstr/network.py>) | `8f556cd5dd6ad896ae8bf8f6bef28841354670d3ff7ec49ebd388ec4abffa156` |
| [sample_model.py](<D:/project/cluster_project/Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rstr/sample_model.py>) | `525ec4d6fea5f4eaa56b1647a7f06ce1a80c20b651ddcd5ba573876cbc42ee73` |
| [sibling_transport.py](<D:/project/cluster_project/Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rstr/sibling_transport.py>) | `460eaa544075dad2aaf71f6265416a38feff9e599f282292370c10a182f472a1` |
| [model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rstr.yaml](<D:/project/cluster_project/Cluster/configs/Quard/ctf_hcg_csort_rstr/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rstr.yaml>) | `a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a` |

原始R0/R1失败、运行时/对照脚本失败及源快照均保留。训练需完整准入收据和既有安全同步/dispatcher链；此清单不授予push或训练例外。
