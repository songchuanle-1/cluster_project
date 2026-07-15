"""PosA encoder ordering with cluster refinement on the final layer only.

The implementation is shared with the PosA model.  The corresponding config
sets ``cluster_att_num_layers`` to 1, which is the only intended difference.
"""

from ..model_base1_quard2_c2f_enc_lite_posA import Network

__all__ = ["Network"]
