import torch
import torch.nn as nn
import torch.nn.functional as F

from ..model_base2_quard.dec import Decoder_layer, Encoder_layer, SelfAttentionLayer
from ..model_base2_quard.sample_model import SamplingModule
from .hier_postprocess import Cluster_Attn, SharedClusterBank, batch2flatten


class DEC(nn.Module):
    def __init__(
        self,
        num_layer=6,
        num_class=256,
        in_channel=32,
        d_model=256,
        nhead=8,
        hidden_dim=1024,
        dropout=0.0,
        activation_fn='relu',
        iter_pred=False,
        sampling_module=None,
        contrastive_align_loss=False,
        num_proposal_fine=512,
        gamma=0.3,
        num_proposal_query_inst=None,
        cluster_layer_nums=None,
        per_layer_topk_list=None,
        cluster_att_num_layers=6,
        cluster_att_init=0.0,
    ):
        super().__init__()
        if num_proposal_query_inst is None:
            num_proposal_query_inst = [128, 64, 32, 16, 8, 4]
        if cluster_layer_nums is None:
            cluster_layer_nums = [256, 64, 8]
        if per_layer_topk_list is None:
            per_layer_topk_list = [32, 16, 8]

        self.num_layer = num_layer
        self.num_class = num_class
        self.d_model = d_model
        self.input_proj = nn.Sequential(nn.Linear(in_channel, d_model), nn.LayerNorm(d_model), nn.ReLU())
        self.input_proj_2d = nn.Sequential(
            nn.Linear(1024, d_model * 2),
            nn.ReLU(),
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Linear(d_model, d_model),
        )
        self.sum_norm = nn.LayerNorm(d_model)
        self.num_proposal_query_inst = num_proposal_query_inst

        H = 768
        self.lang_proj = nn.Linear(H, d_model)
        self.lang_norm = nn.LayerNorm(d_model)

        if sampling_module is not None:
            self.sampling_module = SamplingModule(**sampling_module)
        else:
            self.sampling_module = None
        self.num_proposal_fine = num_proposal_fine
        self.query_generator = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.ReLU(),
            nn.Linear(d_model, d_model),
            nn.ReLU(),
            nn.Linear(d_model, d_model),
        )

        self.scg_head = SelfAttentionLayer(d_model, nhead, dropout=0, glu=True)
        self.iter_pred = iter_pred
        self.cluster_att_num_layers = min(cluster_att_num_layers, num_layer)

        # 几何层级划分只算一份，六层共享。
        self.cluster_bank = SharedClusterBank(cluster_layer_nums=cluster_layer_nums)
        # 但每一层都有自己独立的 query/point 更新参数。
        self.cluster_atts = nn.ModuleList(
            [
                Cluster_Attn(
                    d_model=d_model,
                    nhead=nhead,
                    cluster_layer_nums=cluster_layer_nums,
                    per_layer_topk_list=per_layer_topk_list,
                    dropout=dropout,
                )
                for _ in range(self.cluster_att_num_layers)
            ]
        )
        self.cluster_att_gates = nn.Parameter(torch.full((num_layer,), float(cluster_att_init)))
        # 单独控制 cluster-guided masks 融合强度，初始化得比特征残差更积极一些。
        self.cluster_mask_fuse_logits = nn.Parameter(torch.full((num_layer,), 1.0))

        self.encoder_layers = nn.ModuleList(
            [Encoder_layer(d_model, nhead, hidden_dim, dropout, activation_fn, gamma) for _ in range(num_layer)]
        )
        self.decoder_layers = nn.ModuleList(
            [
                Decoder_layer(
                    d_model,
                    nhead,
                    hidden_dim,
                    dropout,
                    activation_fn,
                    contrastive_align_loss,
                    num_proposal_fine,
                    gamma,
                )
                for _ in range(num_layer)
            ]
        )

    def get_batches(self, x, batch_offsets):
        B = len(batch_offsets) - 1
        max_len = max(batch_offsets[1:] - batch_offsets[:-1])
        if torch.is_tensor(max_len):
            max_len = max_len.item()
        new_feats = torch.zeros(B, max_len, x.shape[1], device=x.device, dtype=x.dtype)
        mask = torch.ones(B, max_len, dtype=torch.bool, device=x.device)
        for i in range(B):
            start_idx = batch_offsets[i]
            end_idx = batch_offsets[i + 1]
            cur_len = end_idx - start_idx
            new_feats[i, :cur_len] = x[start_idx:end_idx]
            mask[i, :cur_len] = False
        return new_feats, mask

    def forward_iter_pred(self, x, fps_seed_sp, batch_offsets, lang_feats=None, lang_masks=None, sp_pos=None, feats_2d=None):
        lang_feats = self.lang_proj(lang_feats)
        lang_feats = self.lang_norm(lang_feats)
        lang_masks = ~(lang_masks.bool())
        inst_feats = self.input_proj(x)

        inst_feats_2d = self.input_proj_2d(feats_2d)
        inst_feats = self.sum_norm(inst_feats + inst_feats_2d)

        inst_feats, batch_mask = self.get_batches(inst_feats, batch_offsets)

        # 位置划分只做一次，后面六层反复复用。
        self.cluster_bank.get_cluster(sp_pos, batch_offsets)

        sp_pos, _ = self.get_batches(sp_pos, batch_offsets)

        seed_sp = inst_feats.gather(dim=1, index=fps_seed_sp.long().unsqueeze(-1).repeat(1, 1, inst_feats.size(-1)))
        seed_sp_pos = sp_pos.gather(dim=1, index=fps_seed_sp.long().unsqueeze(-1).repeat(1, 1, sp_pos.size(-1)))

        scg_weights, _ = self.decoder_layers[0].get_scg_weight(seed_sp_pos)
        seed_sp = self.scg_head(seed_sp, att_weights=scg_weights)

        if hasattr(self, 'sampling_module') and self.sampling_module is not None:
            sample_inds, ref_scores = self.sampling_module(seed_sp, lang_feats, None, lang_masks)
            sample_inds = sample_inds.long()
            sampled_seed = seed_sp.gather(dim=1, index=sample_inds.unsqueeze(-1).repeat(1, 1, seed_sp.size(-1)))
            query_pos = seed_sp_pos.gather(dim=1, index=sample_inds.unsqueeze(-1).repeat(1, 1, seed_sp_pos.size(-1)))
            query = self.query_generator(sampled_seed)
        else:
            query = self.query_generator(seed_sp)
            query_pos = seed_sp_pos

        prediction_masks, prediction_scores, prediction_indis, proj_queries, proj_tokens = [], [], [], [], []

        for layer_i, layer in enumerate(self.encoder_layers):
            lang_feats, inst_feats = layer(lang_feats, lang_masks, inst_feats, batch_mask, query, sp_pos, query_pos)

            query, pred_scores, pred_masks, pred_indis, proj_query, proj_token = self.decoder_layers[layer_i](
                lang_feats,
                lang_masks,
                inst_feats,
                batch_mask,
                query,
                sp_pos,
                query_pos,
                self.num_proposal_query_inst[layer_i],
            )

            if layer_i < self.cluster_att_num_layers:
                gate = torch.tanh(self.cluster_att_gates[layer_i])
                mask_fuse = F.softplus(self.cluster_mask_fuse_logits[layer_i])
                # 先用当前层更新后的点特征重新聚合 cluster token。
                cluster_feats_list = self.cluster_bank.build_cluster_feats(batch2flatten(inst_feats, batch_mask), batch_offsets)
                # 再用当前层 decoder 产出的 query 做 routing。
                cluster_outputs = self.cluster_atts[layer_i](inst_feats, query, batch_mask, cluster_feats_list)
                # 这一支继续负责更新下一层要用到的 point/query 表征。
                inst_feats = inst_feats + gate * cluster_outputs['point']
                query = query + gate * cluster_outputs['query']
                # 用单独生成的一条 cluster-guided masks 分支与原始 masks 显式融合。
                pred_masks = pred_masks + mask_fuse * cluster_outputs['matching_masks']

            prediction_scores.append(pred_scores)
            prediction_masks.append(pred_masks)
            prediction_indis.append(pred_indis)
            proj_queries.append(proj_query)
            proj_tokens.append(proj_token)

        return {
            'masks': pred_masks,
            'batch_mask': batch_mask,
            'scores': pred_scores,
            'indis': pred_indis,
            'proj_queries': proj_queries[-1],
            'proj_tokens': proj_tokens[-1],
            'sample_inds': sample_inds,
            'ref_scores': ref_scores,
            'aux_outputs': [
                {
                    'masks': a,
                    'scores': b,
                    'proj_queries': c,
                    'indis': d,
                    'proj_tokens': e,
                }
                for a, b, c, d, e in zip(
                    prediction_masks[:-1],
                    prediction_scores[:-1],
                    proj_queries[:-1],
                    prediction_indis[:-1],
                    proj_tokens[:-1],
                )
            ],
        }

    def forward(self, x, fps_seed_sp, batch_offsets, lang_feats=None, lang_masks=None, sp_pos=None, feats_2d=None):
        if self.iter_pred:
            return self.forward_iter_pred(x, fps_seed_sp, batch_offsets, lang_feats, lang_masks, sp_pos, feats_2d)
        raise NotImplementedError
