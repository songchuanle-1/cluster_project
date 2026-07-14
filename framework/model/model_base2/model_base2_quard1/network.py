from ..model_base2_quard.network import Network as BaseNetwork

from .dec import DEC


class Network(BaseNetwork):
    def __init__(
        self,
        data_root='',
        input_channel=6,
        blocks=5,
        block_reps=2,
        media=32,
        normalize_before=True,
        return_blocks=True,
        pool='mean',
        sampling_module=None,
        dec=None,
        criterion=None,
        test_cfg=None,
        norm_eval=False,
        infer_mode='pos',
        fps_num=512,
        fix_module=None,
        task_type='res',
    ):
        if fix_module is None:
            fix_module = []
        dec_for_super = dict(dec) if dec is not None else {}
        cluster_layer_nums = dec_for_super.get('cluster_layer_nums')
        per_layer_topk_list = dec_for_super.get('per_layer_topk_list')
        if cluster_layer_nums is not None and per_layer_topk_list is not None:
            if len(per_layer_topk_list) == len(cluster_layer_nums):
                dec_for_super['per_layer_topk_list'] = list(per_layer_topk_list) + [per_layer_topk_list[-1]]
        super().__init__(
            data_root=data_root,
            input_channel=input_channel,
            blocks=blocks,
            block_reps=block_reps,
            media=media,
            normalize_before=normalize_before,
            return_blocks=return_blocks,
            pool=pool,
            sampling_module=sampling_module,
            dec=dec_for_super,
            criterion=criterion,
            test_cfg=test_cfg,
            norm_eval=norm_eval,
            infer_mode=infer_mode,
            fps_num=fps_num,
            fix_module=fix_module,
            task_type=task_type,
        )
        self.dec = DEC(**dec, sampling_module=sampling_module, in_channel=media)
