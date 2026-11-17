# BFC 可审恢复计划（未授权执行）

原M213-BFC在epoch20、3832/4686处发生共享CPU DataLoader `get_sp_label → scatter_mean → scatter_add_` overlap异常；该原因尚未复现，不是BFC结构科学否决。原失败、原归档和receipt保留。

此次仅SSH key/BatchMode/strictknownhost，先断言dl04-MS-7E06；原同配置唯一run为20261026_003527。CPU可用内存188976467968bytes，CPU读取峰值RSS1717047296bytes。未查询GPU、调用CUDA API、导入模型或恢复训练。

固定完整checkpoint：`/data/songcl/Project/Cluster_project/Cluster_checkpoints/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bfc/20261026_003527/last.pth`，926798744bytes，SHA256 `24b3424f0cdc3a6f004bf20ff49b1799e75b92382214b2590d90486192883777`；读取前后hash/stat稳定。实际meta为epoch19、best_miou0.4992169439792633、epochs_no_improve4。若另外取得人类授权并满足canonical全部门，原生 `--resume` 会从epoch20开始，不是3833步；未承诺恢复epoch20已做的部分更新或RNG/loader轨迹。

已遍历1151个CPU model tensor全部keys/shapes/dtype，均finite；原native记录1149keys全部存在，另有text_encoder.embeddings.position_ids/token_type_ids两个buffer。原installed gorilla serializer故意不筛nonpersistent buffers，解释了最初过严exact-key拒绝。没有更改load规则。完整独立shape参考未记录，也没有构建模型来实际load；该限制保留。optimizer为640state/5group/646param IDs，moment形状互相一致且全CPU finite，最大step89034=19×4686；scheduler.last_epoch19，lr2.817659725114537e-05。best原类型numpy.float32，JSON已归一float并保留原type。

后续顺序：

1. 保留此固定checkpoint/原run-config/log/receipt/source48fc链；仅在明确BFC续训人类授权后制作匹配id/config/commit/server/GPU/root/path/SHA的resume_authorization与CPU完整状态evidence。不能借M206、HAP或资源grant。
2. 先用原失败输入和同env torch_scatter源码定位overlap；原始Tensor/instance/sample未捕获，现阶段没有验证过的clone修复。若只原样resume，存在重复崩溃风险；禁止跳样本、换seed/worker、改0.5或静默改公共dataset。
3. 当前八BFC源码+train/dataset均与48fc Git blob相同、原run配置与mappedYAML相同。真正续训前仍必须canonical原admission、全仓source_integrity、exactremoteHEAD、资源白名单/空槽/三锁/防重、launch前checkpoint复hash。若CTS/BEC推进main，不能假定48fc旧任务可在新HEAD直接resume；若修dataset形成新commit，必须解决独立版本/测试与原准入身份，不改标签冒充原48fc。
4. 仅在上述均真实通过后，root可评审原native CLI追加固定`--resume <上述last.pth>`。此文档不执行、不选择GPU、不排队、不发信号、无cold fallback。当前CTS/BEC独立实验不被此恢复计划阻断。

完整CPU证据：bfc_checkpoint_readonly_evidence_r2.json SHA `9b957f1021c29ba866875a2ee07ad1b607da1d279af6924f2d79261653de7c76`；汇总SHA另由root引用。第一轮严格key断言失败及serializer注释检查修正均保留，是诊断harness修正，不是模型修订或checkpoint损坏结论。
