"""
PosA-L1: PosA ordering with cluster refinement only in encoder layer 6.

在 c2f_enc_lite 基础上，将 cluster attention 从 lia 之前移到 lia 之后、ila 之前：
  原: lla → [cluster] → lia → ila → FFN
  改: lla → lia → [cluster] → ila → FFN

动机: 让 lia 先将 inst 信息注入 lang，cluster 基于「已语言化」的 inst_feats
      做聚类注意力，routing 更精准。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from .sample_model import SamplingModule
import framework.torch.nn.functional as framework_F
from framework.torch.nn import MultiheadAttention
from .hier_postprocess import (
    Cluster_Attn,
    C2F_ClusterAttn_TrueRoute,
    C2F_ClusterAttn_DRP,
    C2F_ClusterAttn_CTF,
    C2F_ClusterAttn_CTF_HCG,
    MultiScale_Gather,
    SharedClusterBank,
    batch2flatten,
)


# ============================================================================
# 辅助模块
# ============================================================================

class ThreeLayerMLP(nn.Module):
    def __init__(self, dim, out_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(dim, dim, 1, bias=False),
            nn.BatchNorm1d(dim), nn.ReLU(), nn.Dropout(0.3),
            nn.Conv1d(dim, dim, 1, bias=False),
            nn.BatchNorm1d(dim), nn.ReLU(), nn.Dropout(0.3),
            nn.Conv1d(dim, out_dim, 1),
        )

    def forward(self, x):
        return self.net(x)


class CrossAttentionLayer(nn.Module):
    def __init__(self, d_model=256, nhead=8, dropout=0.0):
        super().__init__()
        self.attn = MultiheadAttention(d_model, nhead, dropout=dropout, batch_first=True)
        self.norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
        self.nhead = nhead
        self._reset_parameters()

    def _reset_parameters(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def with_pos_embed(self, tensor, pos):
        return tensor if pos is None else tensor + pos

    def forward(self, source, query, batch_mask=None, attn_mask=None, pe=None, att_weights=None):
        B = query.shape[0]
        query = self.with_pos_embed(query, pe)
        k = v = source
        if attn_mask is not None:
            attn_mask = attn_mask.unsqueeze(1).repeat(1, self.nhead, 1, 1).view(
                B * self.nhead, query.shape[1], k.shape[1])
            output, output_weight, src_weight = self.attn(
                query, k, v, key_padding_mask=batch_mask, attn_mask=attn_mask, att_weights=att_weights)
        else:
            output, output_weight, src_weight = self.attn(
                query, k, v, key_padding_mask=batch_mask, att_weights=att_weights)
        output = self.dropout(output) + query
        if self.norm is not None:
            output = self.norm(output)
        return output, output_weight, src_weight


class SelfAttentionLayer(nn.Module):
    def __init__(self, d_model=256, nhead=8, dropout=0.0, glu=False):
        super().__init__()
        self.attn = MultiheadAttention(d_model, nhead, dropout=dropout, batch_first=True)
        self.nhead = nhead
        self.norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
        self.glu = glu
        if glu:
            self.glu_p = nn.Linear(d_model, d_model)
            self.glu_g = nn.Linear(d_model, d_model)

    def with_pos_embed(self, tensor, pos):
        return tensor if pos is None else tensor + pos

    def forward(self, x, x_mask=None, attn_mask=None, pe=None, norm=True, att_weights=None):
        B = x.shape[0]
        q = k = self.with_pos_embed(x, pe)
        if attn_mask is not None:
            attn_mask = attn_mask.unsqueeze(1).repeat(1, self.nhead, 1, 1).view(
                B * self.nhead, q.shape[1], k.shape[1])
            output, output_weight, src_weight = self.attn(
                q, k, x, key_padding_mask=x_mask, attn_mask=attn_mask, att_weights=att_weights)
        else:
            output, output_weight, src_weight = self.attn(
                q, k, x, key_padding_mask=x_mask, att_weights=att_weights)
        if self.glu:
            output = self.glu_p(output) * (self.glu_g(output).sigmoid())
        output = self.dropout(output) + x
        if self.norm is not None:
            output = self.norm(output)
        return output


class FFN(nn.Module):
    def __init__(self, d_model, hidden_dim, dropout=0.0, activation_fn='relu'):
        super().__init__()
        act = nn.ReLU if activation_fn == 'relu' else nn.GELU
        self.net = nn.Sequential(
            nn.Linear(d_model, hidden_dim), act(), nn.Dropout(dropout),
            nn.Linear(hidden_dim, d_model), nn.Dropout(dropout),
        )
        self.norm = nn.LayerNorm(d_model)

    def forward(self, x, norm=True):
        output = self.net(x) + x
        if norm:
            output = self.norm(output)
        return output


class MLP(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, num_layers):
        super().__init__()
        self.num_layers = num_layers
        h = [hidden_dim] * (num_layers - 1)
        self.layers = nn.ModuleList(
            nn.Linear(n, k) for n, k in zip([input_dim] + h, h + [output_dim]))

    def forward(self, x):
        for i, layer in enumerate(self.layers):
            x = F.relu(layer(x)) if i < self.num_layers - 1 else layer(x)
        return x


# ============================================================================
# Encoder_layer — 优化 B+D: 后 N 层使用, sigmoid gate, 不修改 query
# ============================================================================
class Encoder_layer(nn.Module):
    def __init__(self, d_model=256, nhead=8, hidden_dim=1024, dropout=0.0,
                 activation_fn='relu', gamma=0.3,
                 cluster_att=None, cluster_bank=None,
                 layer_idx=0, num_layer=6, cluster_att_num_layers=2,
                 cluster_att_init=0.0, cluster_gate_type='sigmoid',
                 cluster_message_type='context'):
        super().__init__()
        self.lla = SelfAttentionLayer(d_model, nhead, dropout)
        self.lia = CrossAttentionLayer(d_model, nhead, dropout)
        self.ila = CrossAttentionLayer(d_model, nhead, dropout)
        self.lia_ffn = FFN(d_model, hidden_dim, dropout, activation_fn)
        self.cluster_att = cluster_att
        self.cluster_bank = cluster_bank
        self.layer_idx = layer_idx
        self.cluster_gate_type = cluster_gate_type
        self.cluster_message_type = cluster_message_type
        if cluster_gate_type not in ('sigmoid', 'layerscale'):
            raise ValueError(f'Unknown cluster_gate_type: {cluster_gate_type}')
        if cluster_message_type not in ('context', 'detail'):
            raise ValueError(f'Unknown cluster_message_type: {cluster_message_type}')
        # ★ 优化 D: 仅在后 N 层使用 cluster attention
        self.use_cluster = (cluster_att is not None
                            and layer_idx >= (num_layer - cluster_att_num_layers))
        if self.use_cluster:
            self.cluster_att_gate = nn.Parameter(torch.tensor(float(cluster_att_init)))

    def forward(self, lang_feats, lang_masks, inst_feats, batch_mask,
                query, sp_pos, query_pos,
                batch_offsets=None):
        lang_feats = self.lla(lang_feats, lang_masks)
        # ★ posA: lia 先做，让 cluster 基于「已语言化」的 inst_feats 做聚类注意力
        lang_feats, _, _ = self.lia(inst_feats, lang_feats, batch_mask, None)
        if self.use_cluster and batch_offsets is not None:
            if self.cluster_gate_type == 'sigmoid':
                gate = torch.sigmoid(self.cluster_att_gate)
            else:
                gate = self.cluster_att_gate
            cluster_feats_list = self.cluster_bank.build_cluster_feats(
                batch2flatten(inst_feats, batch_mask), batch_offsets)
            cluster_outputs = self.cluster_att(
                inst_feats, query, batch_mask,
                cluster_feats_list, self.cluster_bank.child_cluster_maps,
                self.cluster_bank.cluster_ids_list)
            cluster_message = cluster_outputs['point']
            if self.cluster_message_type == 'detail':
                cluster_message = F.layer_norm(
                    inst_feats - cluster_message, (inst_feats.shape[-1],))
                cluster_message = cluster_message.masked_fill(
                    batch_mask.unsqueeze(-1), 0)
            inst_feats = inst_feats + gate * cluster_message
        inst_feats, _, _ = self.ila(lang_feats, inst_feats, lang_masks, None)
        lang_feats = self.lia_ffn(lang_feats)
        return lang_feats, inst_feats


# ============================================================================
# Decoder_layer — 不变
# ============================================================================
class Decoder_layer(nn.Module):
    _shared_modules_initialized = False

    @classmethod
    def _initialize_shared_modules(cls, d_model, nhead, hidden_dim, dropout,
                                   activation_fn, contrastive_align_loss,
                                   num_proposal_fine, gamma):
        if not cls._shared_modules_initialized:
            cls.share_indi_embedding = nn.Sequential(
                nn.Linear(d_model, d_model), nn.ReLU(),
                nn.Linear(d_model, 2), nn.Linear(2, 2))
            if contrastive_align_loss:
                cls.share_contrastive_align_projection_vision = nn.Sequential(
                    nn.Linear(d_model, d_model), nn.ReLU(),
                    nn.Linear(d_model, d_model), nn.ReLU(),
                    nn.Linear(d_model, 64))
                cls.share_contrastive_align_projection_text = nn.Sequential(
                    nn.Linear(d_model, d_model), nn.ReLU(),
                    nn.Linear(d_model, d_model), nn.ReLU(),
                    nn.Linear(d_model, 64))
            cls.share_norm_qqa = nn.LayerNorm(d_model)
            cls.share_out_norm = nn.LayerNorm(d_model)
            cls.share_out_score = nn.Sequential(
                nn.Linear(d_model, d_model), nn.ReLU(), nn.Linear(d_model, 1))
            cls._shared_modules_initialized = True

    def __init__(self, d_model=256, nhead=8, hidden_dim=1024, dropout=0.0,
                 activation_fn='relu', contrastive_align_loss=False,
                 num_proposal_fine=512, gamma=0.3):
        super().__init__()
        self.qia = CrossAttentionLayer(d_model, nhead, dropout)
        self.qla = CrossAttentionLayer(d_model, nhead, dropout)
        self.qqa = SelfAttentionLayer(d_model, nhead, dropout)
        self.qqa_ffn = FFN(d_model, hidden_dim, dropout, activation_fn)
        self.contrastive_align_loss = contrastive_align_loss
        self.gamma = gamma
        self.num_proposal_fine = num_proposal_fine

        Decoder_layer._initialize_shared_modules(
            d_model, nhead, hidden_dim, dropout, activation_fn,
            contrastive_align_loss, num_proposal_fine, gamma)

        self.indi_embedding = nn.Sequential(nn.Linear(d_model, d_model), nn.ReLU(), nn.Linear(d_model, 2), nn.Linear(2, 2))
        if contrastive_align_loss:
            self.contrastive_align_projection_vision = nn.Sequential(nn.Linear(d_model, d_model), nn.ReLU(), nn.Linear(d_model, d_model), nn.ReLU(), nn.Linear(d_model, 64))
            self.contrastive_align_projection_text = nn.Sequential(nn.Linear(d_model, d_model), nn.ReLU(), nn.Linear(d_model, d_model), nn.ReLU(), nn.Linear(d_model, 64))
        else:
            self.contrastive_align_projection_vision = None
            self.contrastive_align_projection_text = None
        self.norm_qqa = nn.LayerNorm(d_model)
        self.out_norm = nn.LayerNorm(d_model)
        self.out_score = nn.Sequential(nn.Linear(d_model, d_model), nn.ReLU(), nn.Linear(d_model, 1))

    def prediction_head(self, query, mask_feats, batch_mask):
        query = self.out_norm(query)
        pred_scores = self.out_score(query)
        pred_masks = torch.einsum('bnd,bmd->bnm', query, mask_feats)
        return pred_scores, pred_masks

    def get_scg_weight(self, pos_q, pos_k=None, k_mask=None, k=None):
        if pos_k is None:
            pos_k = pos_q
        dis = ((pos_q.unsqueeze(2) - pos_k.unsqueeze(1)) ** 2).sum(-1)
        if k_mask is not None:
            dis = torch.masked_fill(dis, k_mask.unsqueeze(1).repeat(1, pos_q.shape[1], 1), 1000000.0)
        scg_weight = torch.exp(-self.gamma * dis)
        B, N_q, _ = pos_q.shape
        scg_mask = torch.zeros((B, N_q, pos_k.shape[1]), device=pos_q.device, dtype=torch.bool)
        if k is not None:
            ind = torch.topk(dis, k, dim=-1, largest=False)[1]
            i_idx = torch.arange(B, device=dis.device)[:, None, None].expand(-1, N_q, k)
            j_idx = torch.arange(N_q, device=dis.device)[None, :, None].expand(B, -1, k)
            scg_mask[i_idx, j_idx, ind] = True
        else:
            scg_mask = None
        return scg_weight, scg_mask

    def forward(self, lang_feats, lang_masks, inst_feats, batch_mask,
                query, sp_pos, query_pos, k):
        query_qia, coarse_att, _ = self.qia(inst_feats, query, batch_mask)
        query_qla, _, _ = self.qla(lang_feats, query_qia, lang_masks)
        query_self = self.qqa(query_qla)
        query = self.norm_qqa(query_qla + query_self)
        query = self.qqa_ffn(query)

        pred_scores, pred_masks = self.prediction_head(query, inst_feats, batch_mask)
        pred_indis = self.indi_embedding(query)

        if self.contrastive_align_loss:
            proj_query = F.normalize(self.contrastive_align_projection_vision(query), p=2, dim=-1)
            proj_token = F.normalize(self.contrastive_align_projection_text(lang_feats), p=2, dim=-1)
        else:
            proj_query = None
            proj_token = None

        return query, pred_scores, pred_masks, pred_indis, proj_query, proj_token


# ============================================================================
# DEC（主模块）— 优化 D: 传递 num_layer 给 Encoder_layer
# ============================================================================
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
        cluster_att_num_layers=2,
        cluster_att_init=0.0,
        cluster_mode='legacy',
        cluster_gate_type='sigmoid',
        cluster_message_type='context',
        cluster_pool_type='mean',
    ):
        super().__init__()
        self.num_layer = num_layer
        self.d_model = d_model

        if num_proposal_query_inst is None:
            num_proposal_query_inst = [128, 64, 32, 16, 8, 4]
        if cluster_layer_nums is None:
            cluster_layer_nums = [256, 64, 8]
        if per_layer_topk_list is None:
            per_layer_topk_list = [32, 16, 8]

        self.num_proposal_query_inst = num_proposal_query_inst
        self.num_proposal_fine = num_proposal_fine
        self.iter_pred = iter_pred

        # 输入投影
        self.input_proj = nn.Sequential(nn.Linear(in_channel, d_model), nn.LayerNorm(d_model), nn.ReLU())
        self.input_proj_2d = nn.Sequential(
            nn.Linear(1024, d_model * 2), nn.ReLU(),
            nn.Linear(d_model * 2, d_model), nn.ReLU(),
            nn.Linear(d_model, d_model))
        self.sum_norm = nn.LayerNorm(d_model)

        # 语言投影
        self.lang_proj = nn.Linear(768, d_model)
        self.lang_norm = nn.LayerNorm(d_model)

        # 采样模块
        if sampling_module is not None:
            self.sampling_module = SamplingModule(**sampling_module)
        else:
            self.sampling_module = None

        self.query_generator = nn.Sequential(
            nn.Linear(d_model, d_model), nn.ReLU(),
            nn.Linear(d_model, d_model), nn.ReLU(),
            nn.Linear(d_model, d_model))

        self.scg_head = SelfAttentionLayer(d_model, nhead, dropout=0, glu=True)

        # ── 共享 Cluster_Attn（仅一个实例）──
        self.cluster_att_num_layers = min(cluster_att_num_layers, num_layer)
        self.cluster_bank = SharedClusterBank(cluster_layer_nums=cluster_layer_nums, cluster_pool_type=cluster_pool_type, d_model=d_model)
        cluster_att_classes = {
            'legacy': Cluster_Attn,
            'noroute': MultiScale_Gather,
            'true_route': C2F_ClusterAttn_TrueRoute,
            'drp': C2F_ClusterAttn_DRP,
            'ctf': C2F_ClusterAttn_CTF,
            'ctf_hcg': C2F_ClusterAttn_CTF_HCG,
        }
        if cluster_mode not in cluster_att_classes:
            raise ValueError(
                f'Unknown cluster_mode: {cluster_mode}. '
                f'Expected one of {tuple(cluster_att_classes)}')
        self.cluster_mode = cluster_mode
        self.cluster_att = cluster_att_classes[cluster_mode](
            d_model=d_model, nhead=nhead,
            cluster_layer_nums=cluster_layer_nums,
            per_layer_topk_list=per_layer_topk_list,
            dropout=dropout)

        # ★ 优化 D: 传递 num_layer, 让 Encoder_layer 知道总层数以计算后 N 层
        self.encoder_layers = nn.ModuleList([
            Encoder_layer(d_model, nhead, hidden_dim, dropout, activation_fn, gamma,
                          cluster_att=self.cluster_att,
                          cluster_bank=self.cluster_bank,
                          layer_idx=i,
                          num_layer=num_layer,
                          cluster_att_num_layers=self.cluster_att_num_layers,
                          cluster_att_init=cluster_att_init,
                          cluster_gate_type=cluster_gate_type,
                          cluster_message_type=cluster_message_type)
            for i in range(num_layer)])
        self.decoder_layers = nn.ModuleList([
            Decoder_layer(d_model, nhead, hidden_dim, dropout, activation_fn,
                          contrastive_align_loss, num_proposal_fine, gamma)
            for _ in range(num_layer)])

    def get_batches(self, x, batch_offsets):
        B = len(batch_offsets) - 1
        max_len = max(batch_offsets[1:] - batch_offsets[:-1])
        if torch.is_tensor(max_len):
            max_len = max_len.item()
        new_feats = torch.zeros(B, max_len, x.shape[1], device=x.device, dtype=x.dtype)
        mask = torch.ones(B, max_len, dtype=torch.bool, device=x.device)
        for i in range(B):
            s, e = batch_offsets[i].item(), batch_offsets[i + 1].item()
            cur = e - s
            new_feats[i, :cur] = x[s:e]
            mask[i, :cur] = False
        return new_feats, mask

    def forward_iter_pred(self, x, fps_seed_sp, batch_offsets,
                          lang_feats=None, lang_masks=None,
                          sp_pos=None, feats_2d=None):
        lang_feats = self.lang_proj(lang_feats)
        lang_feats = self.lang_norm(lang_feats)
        lang_masks = ~(lang_masks.bool())
        inst_feats = self.input_proj(x)

        if feats_2d is not None:
            inst_feats_2d = self.input_proj_2d(feats_2d)
            inst_feats = self.sum_norm(inst_feats + inst_feats_2d)

        inst_feats, batch_mask = self.get_batches(inst_feats, batch_offsets)

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

        prediction_masks, prediction_scores = [], []
        prediction_indis, proj_queries, proj_tokens = [], [], []

        for layer_i, layer in enumerate(self.encoder_layers):
            lang_feats, inst_feats = layer(
                lang_feats, lang_masks, inst_feats, batch_mask,
                query, sp_pos, query_pos,
                batch_offsets=batch_offsets)

            query, pred_scores, pred_masks, pred_indis, proj_query, proj_token = \
                self.decoder_layers[layer_i](
                    lang_feats, lang_masks, inst_feats, batch_mask,
                    query, sp_pos, query_pos, self.num_proposal_query_inst[layer_i])

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
            'aux_outputs': [{
                'masks': a, 'scores': b,
                'proj_queries': c, 'indis': d, 'proj_tokens': e,
            } for a, b, c, d, e in zip(
                prediction_masks[:-1], prediction_scores[:-1],
                proj_queries[:-1], prediction_indis[:-1], proj_tokens[:-1])],
        }

    def forward(self, x, fps_seed_sp, batch_offsets,
                lang_feats=None, lang_masks=None, sp_pos=None, feats_2d=None):
        if self.iter_pred or True:
            return self.forward_iter_pred(x, fps_seed_sp, batch_offsets,
                                          lang_feats, lang_masks, sp_pos, feats_2d)
        else:
            raise NotImplementedError
