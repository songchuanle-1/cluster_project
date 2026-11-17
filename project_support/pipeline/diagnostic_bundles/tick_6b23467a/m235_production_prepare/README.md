# M235 完整新生产包：root执行，作者未执行

新owner6b23467a；source b1e639b3（runtime原parent d214），现有canonical M235 receipt不改。原entry_factory/lock_core字节复用，controller/receiver整组六字段均已校正。新producer sinc_path_prepare_6b23467a、新production sinc_path_prod_6b23467a；binding包含当前owner/deadline/producer/source/runtime/root/UUID及新entry/marker。旧consumed生产shim/bin绝不执行；只允许immutable server4_conda_4ca73fba.sh为环境base。

现在packet_runtime.py/run_setup_once.py均完整，非计划草稿。A的真实sync接口固定为 ../m235_deployment_execution/sync.actual.json，字段见sync_actual_contract.json。先由root真实canonical safe_sync（A包）产生该文件，peer按independent_review_contract.json审本包，再root依序stage、collect、观察独审、activation、render、生产实际独审。所有动作default NOP且intent/result/request exclusive；不重放不确定动作。

ROOTARGS：--admission D:/project/cluster_project/pipeline/admissions/M235-SINC.json --admission-sha256 RECEIPT_SHA --review ABS_CURRENT_PACKET_REVIEW --review-sha256 REVIEW_SHA --current-verification D:/project/cluster_project/pipeline/diagnostic_bundles/tick_6b23467a/m235_deployment_execution/sync.actual.json --current-verification-sha256 REAL_SYNC_SHA
python -B run_setup_once.py --execute-root --action stage ROOTARGS
python -B run_setup_once.py --execute-root --action collect ROOTARGS
python -B run_setup_once.py --execute-root --action render ROOTARGS --activation ABS_GENUINE_ACTIVATION --observation-review ABS_REAL_COLLECT_REVIEW --observation-review-sha256 REAL_REVIEW_SHA

collect_actual.json是本地wrapper；collect_result.json是远端结果重序列化保存。观察peer字段 actual_observation_sha256 必须用collect_actual.observation.remote_result_sha256，collect_actual_sha256用本地collect_actual.json SHA；生产peer production_result_sha256用本地render_result.json SHA。activation必须decision ALLOW_PRODUCTION_PATH_RENDER、当前owner/source、actual_observation_sha256、admission_receipt_sha256、independent_observation_review_sha256、training_launch_authorized:false；不得使用draft激活。

真实render_result和其独审通过后：python -B clear_m235_hold_once.py --execute-root ROOTARGS --production-result ABS_RENDER_RESULT --production-review ABS_RENDER_REVIEW --production-review-sha256 SHA。它仅清M235 hold，不改SERVERS或立即launch。随后python -B dispatch_m235_once.py --execute-root 同上参数；原canonical _process_queue与safe_sync/safe_launch通过source_resolver.scoped(...,production_shim=NEW_SHIM)读真实worktree与临时server副本；上下文退出恢复loader，SERVERS原SHA不变。

原GPU0/cap1/free>=20000MiB/overlay、三原FLOCK inode、hostUID/UUID、本项目trainer保护、canonical准入/预算/源完整性/进度门槛保持。CPU collect/render不等待GPU空闲；dispatch fresh实际不足则不启动，外部进程不动，无需空卡或零context。未知进程/SSH输出保留到文件，不发送信号/不自动retry。Root唯一执行；完成后仍须真实PID/marker/optimizer步进证明。
