# Experiment Design - cluster_project

## 1. Motivation
- 主源为上游动机审查及相同goal哈希；主线是真实点特征更新，不以空槽证明创新或准入。
- 本轮00:11快照design，active1/target3、candidate预算2、reserve准备2。先登记一个稳定diagnosis，再执行最小区分性测试。

## 2. Current Best Results
| ID | 状态 | best mIoU | Acc@50 | spmIoU | 进度 |
|---|---|---|---|---|---|
| model_base1 | 历史 | 0.4894 | 未知 | 未知 | 历史 |
| M95 | 历史最佳 | 0.5020 | 未知 | 未知 | 22/50 earlystop |
| M204-CPA | 监控运行 | 约0.4993 | 未知 | 未知 | 21/50；原生进度另核实 |

## 3. Analysis & Direction
- 重编号保持信息和支持数，但重新生成几何支持，与只置换固定maps不同。原生最近中心方法可在CPU执行，FPS必须使用实际安装的原始引擎，不能手写替代。
- CPU中心仅取固定前256个物理点作为条件对照，不称其为原生FPS中心。完整FPS/层级结果仍须原生GPU。
- first seed的源码若仅委托二进制则未知；第一物理种子不同也不证明最终共成员、mask或精度变化。

## 4. Experiment Plan
| ID | 配置 | 测试 | 预注册判定 | 依赖 |
|---|---|---|---|---|
| hierarchy-native-superpoint-relabeling-audit | 原生M95几何模块，不建新模型 | 4个固定TRAIN场景，原生CPU固定中心身份/重编号；再原生FPS、组合层级、逆置换、无标签编号依赖的共成员比较 | identity不一致则不确定；真实物理支持改变只说明几何路径敏感，不等于训练损伤 | 原源/原生数据、实际CUDA引擎、授权独占GPU |
| hierarchy-native-batch-minimum-resolution | 原冻结协议 | 续做4对固定query点路径 | 原1e-6及小同伴负对照不放宽 | GPU实际空闲 |
- 新几何cohort为原普查字典序的前4大场景scene0000/0001/0002/0003_00，seed1999、原TRAIN变换；不按结果挑样。
- 原生GPU测试只比较物理共成员集合，簇标签置换不是失败。checkpoint权重、mask与backward不在几何测试中执行，不写其PASS。

## 5. GPU Allocation Plan
| 服务器 | GPU | 用途/状态 | 限制 |
|---|---|---|---|
| server4 | 0 | 保留M204训练 | 不停、不重启、不迁移 |
| server4 | 1 | 已授权但0:22仍外部占用 | 新鲜UUID、空闲和三独占锁通过后才CUDA |
| server3 | 1 | 连接失败 | 占用未知，不推断空闲 |
- 非GPU诊断仅在server4原生环境CPU，CUDA显式不可见；不读密码、不操作其他项目。

## 6. Implementation Checklist
- [x] 稳定候选、源绑定协议和具体对照已登记。
- [ ] 执行原生CPU固定中心控制及几何捕获。
- [ ] 冻结原生GPU引擎调用、身份/逆置换/共成员代码与manifest。
- [ ] 只在合法实际空闲时运行，否则保存真实资源证据及具体恢复条件。
- 不创建模型/config、提交/推送/入队/训练；科学准入六gate均不由准备或语法通过替代。

## 7. Risk Assessment
- 固定中心CPU控制不代表FPS；源码不可见就未知。全层几何变化不是任务损失，不能据此包装canonical-index修补为贡献。
- 使用原始数据/引擎，不手写FPS、调阈值、调cap/seed或重试到通过。原失败和不确定性保留。

## 8. Smell Check
- 无训练结构/超参数变化，纯诊断；Phase1禁调参、资源门槛、既有ban及所有科学gate不变。文献新颖性、效果与噪声底限均未证实。
