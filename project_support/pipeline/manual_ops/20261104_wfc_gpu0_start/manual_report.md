# WFC 已在 server4 GPU0 全状态续训

## 结论
用户“启动”已落实。WFC PID678134在GPU0真实运行，从完整checkpoint25恢复到第26轮，额外原生步数322→330，LFT/M206继续暂停，GPU1禁用。

## 实验进度
原best_miou .49711745977401733/no-improve5及模型、优化器、调度器恢复，仍是原实验部分结果，不改冠军或协议。暂停当轮和RNG轨迹未完整保存，不承诺逐batch精确恢复。

## 执行
原94独立git worktree满足canonical精确源契约，旧4457目录保持。原source9、train/dataset/annotation/pretrain/checkpoint逐SHA及CPU全状态核验；YAML只原路径映射，ignored pointgroup扩展原SHA。

## 验证
原admission与新human原文“启动”上下文授权、canonical resume.validate/verify_source/safe_launch/verify_progress通过。额外同PID/start/argv/cwd/stdout/physicalUUID及第26轮两个增长采样通过，用户28files/status/index和其他154候选及非目标账保持。

## 启动前拦截
外部GPU0占用时初次dispatch未启动。随后wrapper在native命令前拒绝瞬时context，未产生WFC日志或进程；有可复核的known-prelaunch证据和三次空卡后，唯一真正Popen成功。没有驱逐、重复训练或未知启动盲重放。

## 下一步
监控同一WFC续训的原生验证/早停结果，GPU0仅1任务。LFT/M206保持暂停，GPU1继续禁用；后续候选需遵守当时实际runtime/源/预算和空槽。
