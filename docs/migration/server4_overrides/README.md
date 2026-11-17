# server-4 四份 YAML 原字节归档

本目录是 2026-11-17 的只读导出；未改远端文件、未启动训练或 GPU 计算。连接前只读核验了 SSH 配置中的 `server-4 -> songcl@192.168.1.115` 与密钥方式，连接使用 `BatchMode=yes`、`StrictHostKeyChecking=yes`，再核验远端 hostname `dl04-MS-7E06`、uid1001、runtime HEAD `5413102c57b526035f3920b5e7a81f3b58ad764d`。

- `working_tree/`：远端四份实际 YAML 的原始字节。
- `head_5413102/`：同路径对应的 HEAD git blob 原始字节。
- `server4_paths.patch`：`git diff --binary HEAD -- <四路径>` 的原始输出。
- `packet.actual.json`：远端只读导出结果，含 base64 原字节与 SHA-256。
- `summary.actual.json`：本地逐文件哈希复验与 YAML 语义比较结果。

四份配置属于 NDE、NSD、RVEC、SINC。语义上仅 `work_dir` 从 `/home/songcl/3dres/project/cluster_project/Checkpoints` 改为 `/data/songcl/Project/Cluster_project/Cluster_checkpoints`；原始 patch 还保留列表、布尔值、注释和空行等序列化差异。不要把这些工作树文件误称为原提交里的字节，也不要自动将此 patch 应用到新机器。

本次没有核验数据目录和 checkpoint 的当前内容，也没有重新开展原生模型或资源测试。当前 GPU 可用性不能由这一源码归档推导。
