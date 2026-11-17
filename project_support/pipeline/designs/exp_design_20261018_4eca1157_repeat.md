# Experiment Design - Native Repeatability

## 1. Motivation
cluster: 面向 ScanRefer 三维语言定位，回归用户最初的点云特征更新主线，研究不同层级承担不同注意力/信息交互作用的轻量结构机制，目标 mIoU ≥ 0.51。核心路径是分层信息交互真实更新点云/超点 inst_feats，再与 query 特征共同生成 mask；不能把仅修改监督损失、沿用已有层级骨架或无效路由计算称为该主线创新。以多尺度 context-only 和 M95 为既有对照，先诊断层级互补性、局部细节及跨层信息是否真正进入 mask 特征，再依据证据选择一个可推导、可证伪的结构机制。监督与关系绑定仅作辅助诊断/匹配对照，不再取代主线。覆盖机制对照、泛化稳健性和同口径效率验证；已有收益不证明新的分层注意力有效，也不自动重开历史失败或禁止的路线。
Avoid attributingnativeprefixnoise to pointupdate mechanism.

## 2. Current Best Results
M95historical.5020,FLEcached.4885315597;no newtrainedresult.

## 3. Analysis & Direction
Two originalprocesses percounterpart distinguish repeatability from referencechanges.

## 4. Experiment Plan
Same4originalnative.train/backward/clip,saveprefix/RNGstate,rawcomparison;nooptimizer.

## 5. GPU Allocation Plan
Onlyserver4physicalGPU0,oneprocess atatime,fresh3locks.

## 6. Implementation Checklist
Sourceboundsharedsmoke,2repeats/model,rawdataanalysispending. No productionchanges/queue/VAL.

## 7. Risk Assessment
Twofreshprocesses do not estimate generaltrainingseednoise;do not loosen1e-6gates,claimarchitecturegain or chaseexactmatches.
