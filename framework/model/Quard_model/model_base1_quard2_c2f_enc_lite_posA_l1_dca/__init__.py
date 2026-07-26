# DCA variant: Dual-branch Cluster Aggregation (mean+max→concat→project).
# Pure YAML config change (cluster_pool_type=dual) — reuses champion model code,
# with dual-branch support added to SharedClusterBank in champion's hier_postprocess.py.
from framework.model.Quard_model.model_base1_quard2_c2f_enc_lite_posA_l1 import Network

__all__ = ["Network"]
