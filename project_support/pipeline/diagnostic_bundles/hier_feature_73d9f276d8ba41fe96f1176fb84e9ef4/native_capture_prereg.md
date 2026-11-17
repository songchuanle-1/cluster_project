# 主线原生特征捕获预注册

## 对象与非目标

稳定候选：m95-hierarchical-mask-feature-path-audit。只诊断既有M95的实际层级特征路径，非新模型或监督候选。
禁止把本轮构造CPU样本当成TRAIN、原生模型backward、泛化收益或独立创新。

## 冻结输入

- 使用既有固定TRAIN group IDs 0、60、101、124，seed1999；逐项保存原生样本指纹、场景、表达式列表和实际分母。
- 不使用VAL选样；不假定四个group一定包含16个表达式；不替换样本以取得有利结果。
- M95原配置与源码，scales256/64/8、最后一层注入、原监督和训练协议不变，仅按已授权服务器适配路径。
- 优先既有M95冻结checkpoint，预期SHA fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e；缺失时记录缺失，不用BPS epoch4/随机权重冒充。

## 资源前提

实际执行前重新检查server-4 hostname/唯一GPU UUID、NVML进程与空闲显存，并实际获得原训练/诊断flock。
保持已有独占守卫：无其他NVML compute进程，idle-equivalent free至少30000MiB；无权驱逐、reset、删锁或改变阈值。
本轮CPU观测不是未来GPU执行许可。资源或正确权重缺失时不分配GPU。

## 捕获与对照

1. 原生同一次forward捕获cluster分支输入inst_feats、point_mask、各层token、映射、模块权重、point message，以及prediction_head的原query/inst_feats。
2. 原样重放与原样重复；固定同一捕获不重做FPS/数据增强，分开报告全模型与模块重放数值误差。
3. 记录各尺度message及其到最终mask_feats的依赖；层级冗余/互补性由真实特征读数判断，不从模块命名或loss推断。
4. padding诊断先用同形状对照：原level_gate logits重放、仅在内存克隆中更换global_mean、保持原logits阻断路径。保留原1e-6判据，不能删除本轮跨形状控制FAIL。
5. 在固定query读出下报告mask logits变化；这只是条件化路径诊断，不是端到端部署预测或训练收益。真正端到端对照须另报。

## 未完成与边界

本轮没有执行原生TRAIN forward/backward、M95 checkpoint下的上述捕获或新模型资源测量。
源码/构造CPU对照只决定下一步诊断，不作为新的结构机制准入。
若真实样本未体现该风险，保留其否定范围，不以改样本、调阈值或换seed补出效果。
