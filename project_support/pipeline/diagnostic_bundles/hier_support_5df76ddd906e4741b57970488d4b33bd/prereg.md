# 原型控制预注册

本次用户授权设计；显存仅作参考，不是唯一方向。同一主线稳定ID，不新建候选/训练队列。
先保存本文件、动机审查和exp_design，再执行隔离构造CPU测试；输出不代表原生数据、全模型backward、训练增益或新颖性。

- 固定seed1999、C256/head8/dropout0；主构造树16/4/2有53个有效点及3个padding行；附加64/16/4树有131个有效点及3个padding行，使三个支持集都包含多个key。两组均为构造数据，另做空中/粗支持的单节点退化控制；此补充在任何结果执行前冻结。
- 点到fine及fine->middle->coarse索引先固定，绝不由VAL/预测或测试结果选择。
- 每点S0为自身middle下fine；S1为自身coarse下其他middle；S2为其他coarse。只纳入实际叶子的祖先。验证叶子覆盖每次且仅一次。
- 独立稠密参考使用全token布尔mask；实际原型用分组支持索引和PyTorch SDPA。float32 forward/all-input gradients绝对阈值1e-6；独立float64阈值1e-10；不取代历史CPU跨形状FAIL，不为通过改变seed/fixture/容差。
- chunk1/5/全段、checkpoint开关为算子等价控制，不是性能/训练超参搜索。固定loss为输出平方均值加固定query logits平方均值；query用固定构造tensor，绝不拟合效益。
- padding有效点不变、padding输出0、全空/单节点无NaN；支持内value干预须影响路径，指定排除coarse的干预在指定点应无效，断路mask readout应0变化。
- 记录torch版本、CUDA未初始化、实际断言数、每个delta、saved_tensor CPU存储统计。存储统计只描述本次CPU算子，不是GPU峰值或全模型节省。
- 原生TRAIN组0/60/101/124及checkpoint/资源守卫沿用已有冻结协议。当前GPU阻塞不解除，也不覆盖原生缺证据。
