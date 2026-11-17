# 用户暂停 WFC/LFT 并停止两卡使用

## 结论
直接用户要求已执行：两个原训练与其已核身份worker停止，CUDA contexts清空；两卡后续派发禁用。

## 实验进展
这是操作暂停，不是科学终态；原协议、源码、冠军和已有部分验证保持。

## 本轮执行
核对真实thread、持项目锁，先落server4 allowed_gpus=[]和dispatch_enabled=false及两task hold；hostname/PID/start/UID/cwd/argv/stdout/source/UUID核验后精确pidfd SIGTERM，无SIGKILL。

## 结果证据
stop_confirmation.json记录14个原进程退出及context释放；checkpoint_confirmation.json记录CPU完整last和last/best SHA及原日志存在。

## 限制与风险
训练入口无SIGTERM临时保存handler，当前半轮未保存；可用完整保存轮见检查点meta。暂停不证明机制有效或失败。

## 下一步
等待显式恢复/资源授权，不自动恢复WFC/LFT/M206，不启动NEC/MIC替补，不运行GPU诊断，不变更调度。
