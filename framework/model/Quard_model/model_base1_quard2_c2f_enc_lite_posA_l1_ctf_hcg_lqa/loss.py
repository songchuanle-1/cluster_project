import gorilla
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional
from torch.nn.utils.rnn import pad_sequence
from typing import Union
from scipy.optimize import linear_sum_assignment
import torch.distributed as dist
from torch_scatter import scatter_max, scatter_mean
import numpy as np
def is_dist_avail_and_initialized():
    if not dist.is_available():
        return False
    if not dist.is_initialized():
        return False
    return True

def get_iou(inputs: torch.Tensor, targets: torch.Tensor, pad_mask: Union[torch.Tensor, None]=None):
    '''
    padding modified
    '''
    if pad_mask is not None:
        inputs = inputs.sigmoid()*pad_mask
    else:
        inputs = inputs.sigmoid()
    # thresholding
    binarized_inputs = (inputs >= 0.5)#.float()
    targets = (targets > 0.5).float()
    intersection = (binarized_inputs * targets).sum(-1)
    union = targets.sum(-1) + binarized_inputs.sum(-1) - intersection
    score = intersection / (union + 1e-6)
    return score

@torch.jit.script
def dice_loss(
    inputs: torch.Tensor,
    targets: torch.Tensor,
    pad_mask: Union[torch.Tensor, None]=None
):
    """
    padding modified
    Compute the DICE loss, similar to generalized IOU for masks
    Args:
        inputs: A float tensor of arbitrary shape.
                The predictions for each example.
        targets: A float tensor with the same shape as inputs. Stores the binary
                 classification label for each element in inputs
                (0 for the negative class and 1 for the positive class).
        pad_mask: A float tensor with the same shape as inputs. Stores the binary, 0 for padding, 1 for non-padding.
    """
    if pad_mask is not None:
        inputs = inputs.sigmoid()*pad_mask
    else:
        inputs = inputs.sigmoid()
    numerator = 2 * (inputs * targets).sum(-1)
    denominator = inputs.sum(-1) + targets.sum(-1)
    loss = 1 - (numerator + 1) / (denominator + 1)  # why+1？
    return loss.mean()

class SigmoidFocalClassificationLoss(nn.Module):
    """
    Sigmoid focal cross entropy loss.
    """

    def __init__(self, gamma: float = 2.0, alpha: float = 0.25):
        """
        Args:
            gamma: Weighting parameter to balance loss for hard and easy examples.
            alpha: Weighting parameter to balance loss for positive and negative examples.
        """
        super(SigmoidFocalClassificationLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma

    @staticmethod
    def sigmoid_cross_entropy_with_logits(input: torch.Tensor, target: torch.Tensor):
        """ PyTorch Implementation for tf.nn.sigmoid_cross_entropy_with_logits:
            max(x, 0) - x * z + log(1 + exp(-abs(x))) in
            https://www.tensorflow.org/api_docs/python/tf/nn/sigmoid_cross_entropy_with_logits

        Args:
            input: (B, #proposals, #classes) float tensor.
                Predicted logits for each class
            target: (B, #proposals, #classes) float tensor.
                One-hot encoded classification targets

        Returns:
            loss: (B, #proposals, #classes) float tensor.
                Sigmoid cross entropy loss without reduction
        """
        loss = torch.clamp(input, min=0) - input * target + \
               torch.log1p(torch.exp(-torch.abs(input)))
        return loss

    def forward(self, input: torch.Tensor, target: torch.Tensor, weights: torch.Tensor):
        """
        Args:
            input: (B, #proposals, #classes) float tensor.
                Predicted logits for each class
            target: (B, #proposals, #classes) float tensor.
                One-hot encoded classification targets
            weights: (B, #proposals) float tensor.
                Anchor-wise weights.

        Returns:
            weighted_loss: (B, #proposals, #classes) float tensor after weighting.
        """
        pred_sigmoid = torch.sigmoid(input)
        alpha_weight = target * self.alpha + (1 - target) * (1 - self.alpha)
        pt = target * (1.0 - pred_sigmoid) + (1.0 - target) * pred_sigmoid
        focal_weight = alpha_weight * torch.pow(pt, self.gamma)

        bce_loss = self.sigmoid_cross_entropy_with_logits(input, target)

        loss = focal_weight * bce_loss

        weights = weights.unsqueeze(-1)
        assert weights.shape.__len__() == loss.shape.__len__()

        return loss * weights

@gorilla.LOSSES.register_module()
class Criterion(nn.Module):
    def __init__(
        self,
        loss_weight=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        loss_fun='focal',
        eos_coef=0.1, temperature=0.07,
        cost_weight=[1.0, 1.0, 0.5],
        match_last_layer=False,
        layer_differ_weight=False,
        one_mask=False,
        cluster_inst_align_weight=0.0,
        cluster_inst_align_temperature=0.1,
        cluster_objg_weight=0.0,
        cluster_lqa_weight=0.0,
        cluster_lqa_temperature=0.1,
    ):
        super().__init__()
        self.loss_fun = loss_fun
        loss_weight = torch.tensor(loss_weight)
        self.register_buffer('loss_weight', loss_weight)
        self.eos_coef = eos_coef
        self.temperature = temperature
        self.match_last_layer = match_last_layer
        self.layer_differ_weight = layer_differ_weight
        self.cluster_inst_align_weight = cluster_inst_align_weight
        self.cluster_inst_align_temperature = cluster_inst_align_temperature
        self.cluster_objg_weight = cluster_objg_weight
        self.cluster_lqa_weight = cluster_lqa_weight
        self.cluster_lqa_temperature = cluster_lqa_temperature
        if cluster_objg_weight > 0:
            self.cluster_objg_head = nn.Sequential(
                nn.Linear(256, 128),
                nn.ReLU(),
                nn.Linear(128, 1),
            )
        if cluster_lqa_weight > 0:
            self.cluster_lqa_head = nn.Linear(256, 64)

    def _get_src_permutation_idx(self, indices):
        # permute predictions following indices
        batch_idx = torch.cat([torch.full_like(src, i) for i, (src, _) in enumerate(indices)])
        src_idx = torch.cat([src for (src, _) in indices])
        return batch_idx, src_idx

    def loss_masks(self, pred_masks, pred_scores, targets, indices, num_boxes):
        '''Compute bce & dice & score loss for the masks'''
        # score loss
        score_loss = torch.tensor([0.0], device=pred_masks[0].device)
        # mask loss
        mask_bce_loss = torch.tensor([0.0], device=pred_masks[0].device)
        mask_dice_loss = torch.tensor([0.0], device=pred_masks[0].device)
        for mask, score, tgt, (idx_q, idx_gt) in zip(pred_masks, pred_scores, targets, indices):
            if tgt['masks'] is None:
                continue
            pred_score = score[idx_q]
            pred_mask = mask[idx_q]  # (num_inst, N)
            tgt_mask = tgt['masks'][idx_gt] # (num_inst, N)
            with torch.no_grad():
                tgt_score = get_iou(pred_mask, tgt_mask).unsqueeze(1)

            filter_id, _ = torch.where(tgt_score > 0.5)
            if filter_id.numel():
                tgt_score = tgt_score[filter_id]
                pred_score = pred_score[filter_id]
                score_loss += F.mse_loss(pred_score, tgt_score)
            mask_bce_loss += F.binary_cross_entropy_with_logits(pred_mask, tgt_mask.float())
            mask_dice_loss += dice_loss(pred_mask, tgt_mask.float())
        score_loss = score_loss / num_boxes
        mask_bce_loss = mask_bce_loss / num_boxes
        mask_dice_loss = mask_dice_loss / num_boxes
        # score_loss = score_loss / len(pred_masks)
        # mask_bce_loss = mask_bce_loss / len(pred_masks)
        # mask_dice_loss = mask_dice_loss / len(pred_masks)

        return mask_bce_loss, mask_dice_loss, score_loss

    def loss_indi(self, pred_indis, targets, indices, num_boxes):
        logits = pred_indis.log_softmax(-1) # [B, Q, 2]

        # Trick to get target indices across batches
        src_idx = self._get_src_permutation_idx(indices)

        # positive: [0, 1]
        pos_mask = torch.tensor([0, 1], dtype=torch.float, device=logits.device)
        target_mask = torch.zeros_like(logits) # [B, Q, 2]
        target_mask[:, :, 0] = 1
        target_mask[src_idx] = pos_mask

        target_sim = torch.zeros_like(logits)
        target_sim[:, :, 0] = 1
        target_sim[src_idx] = pos_mask

        # STEP Compute entropy
        entropy = torch.log(target_sim + 1e-6) * target_sim
        loss_ce = (entropy - logits * target_sim).sum(-1)

        # Weight less 'no_object'
        eos_coef = torch.full(
            loss_ce.shape, self.eos_coef,
            device=target_sim.device
        )
        eos_coef[src_idx] = 1
        loss_ce = loss_ce * eos_coef

        loss_ce = loss_ce.sum() / num_boxes

        return loss_ce

    ############################
    # BRIEF semantic alignment #
    ############################
    def loss_sem_align(self, proj_tokens, proj_queries, lang_masks, targets, indices, num_boxes):
        # step 1. Contrastive logits
        norm_text_emb = proj_tokens  # B, num_tokens=L, dim=64
        norm_img_emb = proj_queries  # B, num_queries=256, dim=64
        logits = (
            torch.matmul(norm_img_emb, norm_text_emb.transpose(-1, -2))
            / self.temperature
        )  # [[B, num_queries, num_tokens]

        # step 2. positive map
        # construct a map such that positive_map[k, i, j] = True
        # if query i is associated to token j in batch item k
        positive_map = torch.zeros(logits.shape, device=logits.device)  # ([B, 256, L])
        # handle 'not mentioned'
        inds = lang_masks.sum(1) - 1
        positive_map[torch.arange(len(inds)), :, inds] = 0.5
        positive_map[torch.arange(len(inds)), :, inds - 1] = 0.5
        # handle true mentions
        pmap = torch.cat([
            t['positive_map'][i] for t, (_, i) in zip(targets, indices)
        ], dim=0)[..., :logits.shape[-1]]
        idx = self._get_src_permutation_idx(indices)
        positive_map[idx] = pmap
        positive_map = positive_map > 0

        modi_positive_map = torch.zeros(logits.shape, device=logits.device)
        pron_positive_map = torch.zeros(logits.shape, device=logits.device)
        other_positive_map = torch.zeros(logits.shape, device=logits.device)
        rel_positive_map = torch.zeros(logits.shape, device=logits.device)
        # [positive, 256] --> [positive, L]
        pmap_modi = torch.cat([
            t['modify_positive_map'][i] for t, (_, i) in zip(targets, indices)
        ], dim=0)[..., :logits.shape[-1]]
        pmap_pron = torch.cat([
            t['pron_positive_map'][i] for t, (_, i) in zip(targets, indices)
        ], dim=0)[..., :logits.shape[-1]]
        pmap_other = torch.cat([
            t['other_entity_map'][i] for t, (_, i) in zip(targets, indices)
        ], dim=0)[..., :logits.shape[-1]]
        pmap_rel = torch.cat([
            t['rel_positive_map'][i] for t, (_, i) in zip(targets, indices)
        ], dim=0)[..., :logits.shape[-1]]
        modi_positive_map[idx] = pmap_modi
        pron_positive_map[idx] = pmap_pron
        other_positive_map[idx] = pmap_other
        rel_positive_map[idx] = pmap_rel

        # step object mask
        # Mask for matches <> 'not mentioned'
        mask = torch.full(
            logits.shape[:2],
            self.eos_coef,
            dtype=torch.float32, device=logits.device
        )
        mask[idx] = 1.0

        # step text mask
        # Token mask for matches <> 'not mentioned'
        tmask = torch.full(
            (len(logits), logits.shape[-1]),
            self.eos_coef,
            dtype=torch.float32, device=logits.device
        )   # [B, L]
        tmask[torch.arange(len(inds)), inds] = 1.0

        # Positive logits are those who correspond to a match
        positive_logits = -logits.masked_fill(~positive_map, 0)
        negative_logits = logits
        other_entity_neg_term = negative_logits.masked_fill(~(other_positive_map>0), 0)

        modi_positive_logits = -logits.masked_fill(~(modi_positive_map>0), 0)
        pron_positive_logits = -logits.masked_fill(~(pron_positive_map>0), 0)
        rel_positive_logits = -logits.masked_fill(~(rel_positive_map>0), 0)

        pos_modi_term = modi_positive_logits.sum(2)
        pos_pron_term = pron_positive_logits.sum(2)
        pos_rel_term = rel_positive_logits.sum(2)

        # number of the token
        nb_modi_pos_token = (modi_positive_map>0).sum(2) + 1e-6
        nb_pron_pos_token = (pron_positive_map>0).sum(2) + 1e-6
        nb_rel_pos_token = (rel_positive_map>0).sum(2) + 1e-6

        ###############################
        # NOTE loss1: object --> text #
        ###############################
        boxes_with_pos = positive_map.any(2)
        pos_term = positive_logits.sum(2)
        # note negative term
        neg_term = (negative_logits+other_entity_neg_term).logsumexp(2)
        nb_pos_token = positive_map.sum(2) + 1e-6
        entropy = -torch.log(nb_pos_token+1e-6) / nb_pos_token
        box_to_token_loss_ = (
            pos_term/nb_pos_token \
            + 0.2*pos_modi_term/nb_modi_pos_token \
            + 0.2*pos_pron_term/nb_pron_pos_token \
            + 0.1*pos_rel_term/nb_rel_pos_token \
            + neg_term
        ).masked_fill(~boxes_with_pos, 0)
        box_to_token_loss = (box_to_token_loss_ * mask).sum()

        ###############################
        # NOTE loss2: text --> object #
        ###############################
        tokens_with_pos = (positive_map + (modi_positive_map>0) + (pron_positive_map>0) + (rel_positive_map>0)).any(1)
        tmask[positive_map.any(1)] = 1.0
        tmask[(modi_positive_map>0).any(1)] = 0.2
        tmask[(pron_positive_map>0).any(1)] = 0.2
        tmask[(rel_positive_map>0).any(1)] = 0.1
        tmask[torch.arange(len(inds)), inds-1] = 0.1

        pos_term = positive_logits.sum(1)
        pos_modi_term = modi_positive_logits.sum(1)
        pos_pron_term = pron_positive_logits.sum(1)
        pos_rel_term = rel_positive_logits.sum(1)
        # note
        pos_term = pos_term + pos_modi_term + pos_pron_term + pos_rel_term

        neg_term = negative_logits.logsumexp(1)
        nb_pos_obj = positive_map.sum(1) + modi_positive_map.sum(1) + pron_positive_map.sum(1) \
             + rel_positive_map.sum(1) + 1e-6

        entropy = -torch.log(nb_pos_obj+1e-6) / nb_pos_obj
        token_to_box_loss = (
            (entropy + pos_term / nb_pos_obj + neg_term)
        ).masked_fill(~tokens_with_pos, 0)
        token_to_box_loss = (token_to_box_loss * tmask).sum()

        # total loss
        tot_loss = (box_to_token_loss + token_to_box_loss) / 2
        return tot_loss / num_boxes


    ####################################
    # CLICA: cluster-instance contrastive alignment #
    ####################################
    def loss_cluster_inst_align(self, cluster_feats_list, cluster_ids_list,
                                sp_ins_labels, object_idss, batch_offsets,
                                temperature=0.1):
        """给 cluster token 加实例判别性监督 — InfoNCE 按 GT 实例分组。

        瓶颈假设: cluster token 由 mean-pool 聚合, 丢失实例判别性 → 回写 context
        通用化。对比损失直接优化 cluster token 的实例判别性, 突破信息瓶颈。
        对每尺度每 batch: 点→簇 id 多数投票得簇的实例标签 (仅在 GT 实例点内),
        归一化 cluster token, 同实例簇为 positive, 其余为 negative。
        """
        if cluster_feats_list is None or cluster_ids_list is None:
            return torch.tensor(0.0, device=cluster_feats_list[0].device
                                if cluster_feats_list is not None else torch.device('cpu'))
        device = cluster_feats_list[0].device
        B = len(batch_offsets) - 1
        num_scales = len(cluster_feats_list)
        total_loss = torch.tensor(0.0, device=device)
        total_terms = 0

        for lvl in range(num_scales):
            cf = cluster_feats_list[lvl]  # [B, max_K, C] padded
            for b in range(B):
                obj_ids = set(object_idss[b])
                if not obj_ids:
                    continue
                cids = cluster_ids_list[lvl][b].long()  # [N_b] local cluster ids
                lbls = sp_ins_labels[b]                  # [N_b] per-point instance label
                n_b = cids.shape[0]
                if n_b == 0:
                    continue
                # 有效点 = 属于任一 GT 实例
                in_inst = torch.tensor(
                    [l in obj_ids for l in lbls.tolist()], dtype=torch.bool, device=device)
                if not in_inst.any():
                    continue
                cids_v = cids[in_inst]
                lbls_v = lbls[in_inst]
                K_b = int(cids.max().item()) + 1
                # 簇→实例标签: 对每实例做指示向量 scatter 到簇, 取 argmax
                uniq = lbls_v.unique()
                lbl_idx = (lbls_v.unsqueeze(-1) == uniq.unsqueeze(0)).long()  # [Nv, U]
                counts = torch.zeros(K_b, uniq.shape[0], device=device, dtype=torch.long)
                idx = cids_v.unsqueeze(-1).expand_as(lbl_idx)
                counts.scatter_add_(0, idx, lbl_idx)  # [K_b, U]
                clu_lbl = uniq[counts.argmax(-1)]     # [K_b] 多数投票实例标签
                clu_cnt = counts.sum(-1)              # [K_b] 有效点数
                valid_clu = (clu_cnt > 0) & (cids_v.new_tensor(True))  # 有 GT 点即有效
                # 取前 K_b 行 (真实簇), 后行为 pad
                feats = cf[b][:K_b]                    # [K_b, C]
                feats = feats[valid_clu]               # [Kv, C]
                clu_lbl_v = clu_lbl[valid_clu]         # [Kv]
                if feats.shape[0] < 2:
                    continue
                feats_n = F.normalize(feats, p=2, dim=-1)
                S = torch.matmul(feats_n, feats_n.t()) / temperature  # [Kv, Kv]
                Kv = feats_n.shape[0]
                eye = torch.eye(Kv, dtype=torch.bool, device=device)
                pos_mask = (clu_lbl_v[:, None] == clu_lbl_v[None, :]) & ~eye
                if not pos_mask.any():
                    continue
                neg_all = torch.logsumexp(S, dim=-1)   # [Kv] 所有簇 (含自身)
                pos_logits = S.masked_fill(~pos_mask, float('-inf'))
                pos_lse = torch.logsumexp(pos_logits, dim=-1)  # [Kv]
                has_pos = pos_mask.any(-1)
                if not has_pos.any():
                    continue
                info_nce = -(pos_lse - neg_all)
                total_loss = total_loss + info_nce[has_pos].mean()
                total_terms += 1

        if total_terms == 0:
            return torch.tensor(0.0, device=device)
        return total_loss / total_terms

    ####################################
    # OBJG: cluster-token 目标对象感知 #
    ####################################
    def loss_cluster_objg(self, cluster_feats_list, cluster_ids_list,
                          sp_ins_labels, object_idss, sp_ref_masks, batch_offsets):
        """给含 GT 实例点的有效簇加目标对象感知 BCE。

        瓶颈假设: cluster token 由 mean-pool 聚合, 不知道哪个簇属于语言指定的
        目标对象 → context 回写对目标区域无偏重。监督簇 token 预测"主导实例是否
        为查询目标", 让回写 context 直接强化目标簇 → decoder 定位更准。
        目标 id 从 sp_ref_masks (查询目标 GT mask) 多数投票派生; 有效簇 =
        含任一 GT 实例点; 标签 = 簇主导实例 == 目标 id (0/1)。
        """
        if cluster_feats_list is None or cluster_ids_list is None:
            return torch.tensor(0.0, device=cluster_feats_list[0].device
                                if cluster_feats_list is not None else torch.device('cpu'))
        device = cluster_feats_list[0].device
        B = len(batch_offsets) - 1
        num_scales = len(cluster_feats_list)
        total_loss = torch.tensor(0.0, device=device)
        total_terms = 0

        for lvl in range(num_scales):
            cf = cluster_feats_list[lvl]  # [B, max_K, C] padded
            for b in range(B):
                ref = sp_ref_masks[b]
                if ref is None or ref.numel() == 0 or float(ref.max()) < 0.6:
                    continue
                lbls = sp_ins_labels[b]                  # [N_b] per-superpoint instance label
                cids = cluster_ids_list[lvl][b].long()   # [N_b] superpoint→cluster mapping
                n_b = cids.shape[0]
                if n_b == 0 or lbls.shape[0] != n_b:
                    continue
                obj_ids = set(object_idss[b])
                if not obj_ids:
                    continue
                # 目标实例 id: target-dominant 超点中多数投票的实例标签
                ref_tgt = ref > 0.6
                ref_lbls = lbls[ref_tgt]
                if ref_lbls.numel() == 0:
                    continue
                in_obj_ref = torch.tensor(
                    [l in obj_ids for l in ref_lbls.tolist()], dtype=torch.bool, device=device)
                if not in_obj_ref.any():
                    continue
                target_id = ref_lbls[in_obj_ref].mode(dim=0).values.item()
                # 有效点 = 属于任一 GT 实例
                in_inst = torch.tensor(
                    [l in obj_ids for l in lbls.tolist()], dtype=torch.bool, device=device)
                if not in_inst.any():
                    continue
                cids_v = cids[in_inst]
                lbls_v = lbls[in_inst]
                K_b = int(cids.max().item()) + 1
                # 簇→实例标签: 多数投票
                uniq = lbls_v.unique()
                lbl_idx = (lbls_v.unsqueeze(-1) == uniq.unsqueeze(0)).long()  # [Nv, U]
                counts = torch.zeros(K_b, uniq.shape[0], device=device, dtype=torch.long)
                idx = cids_v.unsqueeze(-1).expand_as(lbl_idx)
                counts.scatter_add_(0, idx, lbl_idx)  # [K_b, U]
                clu_lbl = uniq[counts.argmax(-1)]     # [K_b] 多数投票实例标签
                clu_cnt = counts.sum(-1)              # [K_b] 有效点数
                valid_clu = clu_cnt > 0
                if not valid_clu.any():
                    continue
                feats = cf[b][:K_b]                    # [K_b, C]
                feats = feats[valid_clu]               # [Kv, C]
                clu_lbl_v = clu_lbl[valid_clu]         # [Kv]
                if feats.shape[0] < 2:
                    continue
                # 目标感知标签: 主导实例 == 目标 id → 1
                objg_target = (clu_lbl_v == target_id).float()  # [Kv]
                logits = self.cluster_objg_head(feats).squeeze(-1)  # [Kv]
                loss_b = F.binary_cross_entropy_with_logits(logits, objg_target)
                total_loss = total_loss + loss_b
                total_terms += 1

        if total_terms == 0:
            return torch.tensor(0.0, device=device)
        return total_loss / total_terms

    def loss_cluster_lqa(self, cluster_feats_list, cluster_ids_list, lang_emb,
                         sp_ins_labels, object_idss, sp_ref_masks, batch_offsets,
                         temperature=0.1):
        """给 cluster token 加语言查询语义对齐监督 — InfoNCE 目标簇为正样本。

        瓶颈假设: cluster token 由 mean-pool 聚合, 不知道查询语言的语义内容
        (如 "red chair near the table" 的属性/关系) → context 回写对目标区域无
        语义偏重。LQA 用语言查询嵌入监督: 目标簇 (主导实例==目标) 的 token 经
        head 投影后与 lang_emb 的相似度应高于非目标簇。与 OBJG (二值目标身份)
        不同, LQA 携带查询语义方向, 让回写 context 语义定向。
        目标 id 从 sp_ref_masks 多数投票派生 (同 OBJG); lang_emb = proj_tokens
        按 lang_masks 取有效 token 的均值。
        """
        if cluster_feats_list is None or cluster_ids_list is None:
            return torch.tensor(0.0, device=cluster_feats_list[0].device
                                if cluster_feats_list is not None else torch.device('cpu'))
        if lang_emb is None:
            return torch.tensor(0.0, device=cluster_feats_list[0].device)
        device = cluster_feats_list[0].device
        B = len(batch_offsets) - 1
        num_scales = len(cluster_feats_list)
        total_loss = torch.tensor(0.0, device=device)
        total_terms = 0

        for lvl in range(num_scales):
            cf = cluster_feats_list[lvl]  # [B, max_K, C] padded
            for b in range(B):
                ref = sp_ref_masks[b]
                if ref is None or ref.numel() == 0 or float(ref.max()) < 0.6:
                    continue
                lbls = sp_ins_labels[b]                  # [N_b] per-superpoint instance label
                cids = cluster_ids_list[lvl][b].long()   # [N_b] superpoint→cluster mapping
                n_b = cids.shape[0]
                if n_b == 0 or lbls.shape[0] != n_b:
                    continue
                obj_ids = set(object_idss[b])
                if not obj_ids:
                    continue
                # 目标实例 id: target-dominant 超点中多数投票的实例标签 (同 OBJG)
                ref_tgt = ref > 0.6
                ref_lbls = lbls[ref_tgt]
                if ref_lbls.numel() == 0:
                    continue
                in_obj_ref = torch.tensor(
                    [l in obj_ids for l in ref_lbls.tolist()], dtype=torch.bool, device=device)
                if not in_obj_ref.any():
                    continue
                target_id = ref_lbls[in_obj_ref].mode(dim=0).values.item()
                # 有效点 = 属于任一 GT 实例
                in_inst = torch.tensor(
                    [l in obj_ids for l in lbls.tolist()], dtype=torch.bool, device=device)
                if not in_inst.any():
                    continue
                cids_v = cids[in_inst]
                lbls_v = lbls[in_inst]
                K_b = int(cids.max().item()) + 1
                # 簇→实例标签: 多数投票
                uniq = lbls_v.unique()
                lbl_idx = (lbls_v.unsqueeze(-1) == uniq.unsqueeze(0)).long()  # [Nv, U]
                counts = torch.zeros(K_b, uniq.shape[0], device=device, dtype=torch.long)
                idx = cids_v.unsqueeze(-1).expand_as(lbl_idx)
                counts.scatter_add_(0, idx, lbl_idx)  # [K_b, U]
                clu_lbl = uniq[counts.argmax(-1)]     # [K_b] 多数投票实例标签
                clu_cnt = counts.sum(-1)              # [K_b] 有效点数
                valid_clu = clu_cnt > 0
                if not valid_clu.any():
                    continue
                feats = cf[b][:K_b]                    # [K_b, C]
                feats = feats[valid_clu]               # [Kv, C]
                clu_lbl_v = clu_lbl[valid_clu]         # [Kv]
                if feats.shape[0] < 2:
                    continue
                # 语言嵌入: 单 batch 向量 [D_lang] (proj_tokens 池化已在 forward 完成)
                le = lang_emb[b]                       # [D_lang]
                if le.numel() == 0:
                    continue
                # 目标簇为正样本, 其余簇为负样本
                tgt_mask = (clu_lbl_v == target_id)    # [Kv]
                if not tgt_mask.any():
                    continue
                proj = self.cluster_lqa_head(feats)    # [Kv, 64]
                proj_n = F.normalize(proj, p=2, dim=-1)
                le_n = F.normalize(le.unsqueeze(0), p=2, dim=-1)  # [1, 64]
                logits = torch.matmul(proj_n, le_n.t()).squeeze(-1) / temperature  # [Kv]
                log_softmax = F.log_softmax(logits, dim=-1)      # [Kv]
                tgt_idx = tgt_mask.nonzero(as_tuple=True)[0]     # 全部目标簇
                if tgt_idx.numel() == 0:
                    continue
                loss_b = -log_softmax[tgt_idx].mean()
                total_loss = total_loss + loss_b
                total_terms += 1

        if total_terms == 0:
            return torch.tensor(0.0, device=device)
        return total_loss / total_terms

    def match_sampled_ins(self, sampled_ins_lbl, obj_ids, sampled_pos, obj_pos):
        '''
        params:
            sampled_ins_lbl: [N_query,]
            obj_ids: list [N_gt]
            sampled_pos: [N_query, 3]
            obj_pos: [N_gt, 3]
        return:
            top1_ids: [N_gt,]
            in_obj_ids: list [N_gt,]
            matched_inds: list[(q_ids, tgt_ids)]
            tgt_counts: [N_gt,]
        '''
        matched_inds = []
        # compute the distance matrix
        dist_mat = torch.cdist(sampled_pos, obj_pos, p=2) # [N_query, N_gt]
        # top1 for each gt
        topk_inds = torch.topk(dist_mat, k=1, dim=0, largest=False, sorted=True)[1].squeeze(0) # [N_gt,]

        matched_inds.extend([(q_id[None], torch.tensor([tgt_id], dtype=torch.int64, device=sampled_pos.device)) for tgt_id, q_id in enumerate(topk_inds)])

        in_obj_ids = []
        for tgt_id, obj_id in enumerate(obj_ids):
            in_obj_id = (sampled_ins_lbl==obj_id).nonzero().squeeze(1) # tensor [N_query,]
            in_obj_id = in_obj_id[~np.isin(in_obj_id.cpu(),topk_inds.cpu())]
            in_obj_ids.append(in_obj_id)
            if in_obj_id.numel() == 0: continue
            else:
                matched_inds.extend([(q_id[None], torch.tensor([tgt_id], dtype=torch.int64, device=sampled_pos.device)) for q_id in in_obj_id])

        # matched_inds: [(q_id, tgt_id), ...]
        matched_inds_np = np.array([(matched_inds[i][0][0].cpu(),matched_inds[i][1][0].cpu()) for i in range(len(matched_inds))])
        tgt_ids = matched_inds_np[:, 1]
        _, tgt_counts = np.unique(tgt_ids, return_counts=True)

        matched_inds = torch.from_numpy(matched_inds_np).transpose(0,1).to(sampled_pos.device)
        matched_inds = (matched_inds[0], matched_inds[1])
        return topk_inds, in_obj_ids, matched_inds, tgt_counts


    def get_layer_loss(self, layer, aux_outputs, pad_masks, target, indices=None, lang_masks=None):
        loss_out = {}

        pred_scores = aux_outputs['scores']
        pred_masks = aux_outputs['masks']
        proj_queries = aux_outputs['proj_queries']
        proj_tokens = aux_outputs['proj_tokens']
        pred_indis = aux_outputs['indis']

        if self.match_last_layer:
            pred_masks_nopadding = []
            for pred_mask, mask in zip(pred_masks, pad_masks):
                pred_masks_nopadding.append(pred_mask.masked_select(mask.unsqueeze(0)).view(pred_mask.shape[0], -1))
            pred_masks = pred_masks_nopadding
        # pred_masks: List[Tensor (n_query, M)]
        # target_masks: List[Tensor (n_tgt, N)] （None if n_tgt==0)

        num_insts = sum(len(inds[1]) for inds in indices)
        num_insts = torch.as_tensor(
            [num_insts], dtype=torch.float,
            device=pred_masks[0].device
        )
        if is_dist_avail_and_initialized():
            torch.distributed.all_reduce(num_insts)

        indi_loss = self.loss_indi(pred_indis, target, indices, num_insts)

        mask_bce_loss, mask_dice_loss, score_loss = self.loss_masks(pred_masks, pred_scores, target, indices, num_insts)

        if proj_tokens is not None:
            sem_loss = self.loss_sem_align(proj_tokens, proj_queries, lang_masks, target, indices, num_insts)
        else:
            sem_loss = torch.tensor([0.0], device=pred_masks[0].device)

        loss_out['score_loss'] = score_loss
        loss_out['mask_bce_loss'] = mask_bce_loss
        loss_out['mask_dice_loss'] = mask_dice_loss
        loss_out['sem_loss'] = sem_loss
        loss_out['indi_loss'] = indi_loss

        loss = (
            self.loss_weight[0] * mask_bce_loss + self.loss_weight[1] * mask_dice_loss +
            self.loss_weight[2] * score_loss + self.loss_weight[4] * indi_loss +
            self.loss_weight[6] * sem_loss)

        loss_out = {f'layer_{layer}_' + k: v for k, v in loss_out.items()}
        return loss, loss_out

    def get_batches(self, x, batch_offsets):
        B = len(batch_offsets) - 1
        max_len = max(batch_offsets[1:] - batch_offsets[:-1])
        new_feats = torch.zeros(B, max_len, x.shape[1]).to(x.device)
        mask = torch.ones(B, max_len, dtype=torch.bool).to(x.device)
        for i in range(B):
            start_idx = batch_offsets[i]
            end_idx = batch_offsets[i + 1]
            cur_len = end_idx - start_idx
            padded_feats = torch.cat([x[start_idx:end_idx], torch.zeros(max_len - cur_len, x.shape[1]).to(x.device)], dim=0)
            new_feats[i] = padded_feats
            mask[i, :cur_len] = False
        mask.detach()
        return new_feats, mask

    def forward(self, pred, gt_spmasks, sp_ref_masks=None, object_idss=None, sp_ins_labels=None, dense_maps=None, lang_masks=None, fps_seed_sp=None, sp_coords_float=None, batch_offsets=None):
        '''
            pred_masks: List[Tensor (1, M)]
            pred_scores: (B, n, 1) or [(B, n, 1)]
            gt_pmasks: List[Tensor (1, N)]
            gt_sp_masks: List[Tensor (M)]
            sp_ref_masks: List[Tensor (M)]
        '''
        loss_out = {}

        pred_scores = pred['scores']
        pred_masks = pred['masks']
        pad_masks = ~pred['batch_mask']
        pred_indis = pred['indis']
        proj_tokens = pred['proj_tokens']
        proj_queries = pred['proj_queries']
        ref_padding = pad_sequence(sp_ref_masks, batch_first=True, padding_value=0)

        ref_scores = pred['ref_scores']
        sample_inds = pred['sample_inds']

        if ref_scores is None:
            raise NotImplementedError
        else:
            pred_masks_nopadding = []
            for pred_mask, mask in zip(pred_masks, pad_masks):
                pred_mask = pred_mask.masked_select(mask.unsqueeze(0)).view(pred_mask.shape[0], -1)
                pred_masks_nopadding.append(pred_mask)
            pred_masks = pred_masks_nopadding

            sp_coords_float = self.get_batches(sp_coords_float, batch_offsets)[0]
            fps_seed_sp = fps_seed_sp.long()
            target = []
            indices = []
            topk_seed_inds = []
            matched_seed_inds = []
            obj_poss = []

            gt_spmasks = pad_sequence(gt_spmasks, batch_first=True, padding_value=0)
            seed_pos = sp_coords_float.gather(1, fps_seed_sp.unsqueeze(-1).repeat(1, 1, 3))
            for b in range(len(object_idss)):
                obj_ids = object_idss[b]
                if len(obj_ids) == 0:
                    indices.append(
                        (torch.as_tensor([], dtype=torch.int64, device=pred_scores.device),
                         torch.as_tensor([], dtype=torch.int64, device=pred_scores.device))
                    )
                    target.append(
                        {
                            'masks': None,
                            'positive_map': dense_maps[b]['positive_map'][:1].repeat(len(object_idss[b]), 1).to(pred_scores.device),
                            'modify_positive_map': dense_maps[b]['modify_positive_map'][:1].repeat(len(object_idss[b]), 1).to(pred_scores.device),
                            'pron_positive_map': dense_maps[b]['pron_positive_map'][:1].repeat(len(object_idss[b]), 1).to(pred_scores.device),
                            'other_entity_map': dense_maps[b]['other_entity_map'][:1].repeat(len(object_idss[b]), 1).to(pred_scores.device),
                            'rel_positive_map': dense_maps[b]['rel_positive_map'][:1].repeat(len(object_idss[b]), 1).to(pred_scores.device),
                        }
                    )
                    topk_seed_inds.append(torch.as_tensor([], dtype=torch.int64, device=pred_scores.device))
                    matched_seed_inds.append(torch.as_tensor([], dtype=torch.int64, device=pred_scores.device))
                    obj_poss.append(torch.as_tensor([], dtype=torch.int64, device=pred_scores.device))
                    continue
                # seed label
                seed_ins_lbl = sp_ins_labels[b][fps_seed_sp[b]]
                # query label
                sampled_ins_lbl = seed_ins_lbl[sample_inds[b]]
                # query pos
                sampled_pos = seed_pos[b][sample_inds[b]]
                # masks
                masks = torch.stack([sp_ins_labels[b]==obj_id for obj_id in obj_ids])
                obj_pos = torch.stack([
                    scatter_mean(sp_coords_float[b].masked_select(pad_masks[b].unsqueeze(1)).view(-1,3),
                                 mask.long(),
                                 dim=0)[1]
                    for mask in masks
                ])
                obj_poss.append(obj_pos)
                # [N_gt,]
                topk_seed, in_obj_seed, matched_seed, tgt_counts_seed= self.match_sampled_ins(seed_ins_lbl, obj_ids, seed_pos[b], obj_pos)
                # [N_gt,], list [N_gt], (q_ids, tgt_ids)
                topk_inds, in_obj_ids, matched_inds, tgt_counts = self.match_sampled_ins(sampled_ins_lbl, obj_ids, sampled_pos, obj_pos)
                # repeat gt according to tgt_counts
                masks = torch.cat([masks[i, None].repeat(tgt_counts[i],1) for i in range(len(masks))], dim=0)
                target.append(
                    {
                        'masks': masks,
                        'positive_map': dense_maps[b]['positive_map'][:1].repeat(len(masks), 1).to(pred_scores.device),
                        'modify_positive_map': dense_maps[b]['modify_positive_map'][:1].repeat(len(masks), 1).to(pred_scores.device),
                        'pron_positive_map': dense_maps[b]['pron_positive_map'][:1].repeat(len(masks), 1).to(pred_scores.device),
                        'other_entity_map': dense_maps[b]['other_entity_map'][:1].repeat(len(masks), 1).to(pred_scores.device),
                        'rel_positive_map': dense_maps[b]['rel_positive_map'][:1].repeat(len(masks), 1).to(pred_scores.device),
                    }
                )
                assert len(matched_inds[0]) == len(masks)
                indices.append(matched_inds)
                topk_seed_inds.append(topk_seed)
                matched_seed_inds.append(matched_seed)

        num_insts = sum(len(inds[1]) for inds in indices)
        num_insts = torch.as_tensor(
            [num_insts], dtype=torch.float,
            device=pred_masks[0].device
        )
        if is_dist_avail_and_initialized():
            torch.distributed.all_reduce(num_insts)

        indi_loss = self.loss_indi(pred_indis, target, indices, num_insts)

        mask_bce_loss, mask_dice_loss, score_loss = self.loss_masks(pred_masks, pred_scores, target, indices, num_insts)

        if proj_tokens is not None:
            sem_loss = self.loss_sem_align(proj_tokens, proj_queries, lang_masks, target, indices, num_insts)
        else:
            sem_loss = torch.tensor([0.0], device=pred_masks[0].device)

        sample_loss = torch.tensor([0.0], device=pred_masks[0].device)
        # sample loss
        if ref_scores is not None:
            # seed
            ref_padding_seed_ = ref_padding.gather(1, fps_seed_sp)
            ref_padding_seed = ref_padding_seed_ * 0.5
            # [B, M]
            for b in range(len(topk_seed_inds)):
                if len(matched_seed_inds[b]) == 0:
                    continue
                dist_seeds = torch.cdist(seed_pos[b], obj_poss[b], p=2)
                weight = torch.exp(-0.5 * ((dist_seeds) / 1) ** 2)
                for idx, obj in zip(matched_seed_inds[b][0], matched_seed_inds[b][1]):
                    ref_padding_seed[b][idx] = weight[idx][obj]
                ref_padding_seed[b][topk_seed_inds[b]] = 1.0

            if self.loss_fun=='focal':
                sample_criterion = SigmoidFocalClassificationLoss()
                seed_pad_masks = pad_masks.gather(1, fps_seed_sp)
                cls_weights = seed_pad_masks.float()
                cls_normalizer = cls_weights.sum(dim=1, keepdim=True).float()
                cls_weights /= torch.clamp(cls_normalizer, min=1.0)
                # focal loss
                sample_loss = sample_criterion(ref_scores.unsqueeze(-1), ref_padding_seed.unsqueeze(-1).float(), weights=cls_weights)
                sample_loss = (sample_loss.squeeze(-1)*seed_pad_masks).sum(-1) # / pad_masks.sum(-1)
                sample_loss = sample_loss.mean()
                sample_loss = sample_loss.unsqueeze(0)
            else:
                raise NotImplementedError

        loss_out['score_loss'] = score_loss
        loss_out['mask_bce_loss'] = mask_bce_loss
        loss_out['mask_dice_loss'] = mask_dice_loss
        loss_out['sem_loss'] = sem_loss
        loss_out['indi_loss'] = indi_loss
        loss_out['sample_loss'] = sample_loss

        if sp_ref_masks is not None:
            loss = (
                self.loss_weight[0] * mask_bce_loss + self.loss_weight[1] * mask_dice_loss +
                self.loss_weight[2] * score_loss + self.loss_weight[3] * sample_loss + self.loss_weight[4] * indi_loss +
                self.loss_weight[6] * sem_loss)
        else:
            loss = (
                self.loss_weight[0] * mask_bce_loss + self.loss_weight[1] * mask_dice_loss +
                self.loss_weight[2] * score_loss + self.loss_weight[4] * indi_loss +
                self.loss_weight[6] * sem_loss)
        if 'aux_outputs' in pred:
            for i, aux_outputs in enumerate(pred['aux_outputs']):
                loss_i, loss_out_i = self.get_layer_loss(i, aux_outputs, pad_masks, target, indices, lang_masks)
                if self.layer_differ_weight:
                    # 1/7, 2/7, 3/7, 4/7, 5/7, 6/7
                    loss += loss_i * ((i+1) / (len(pred['aux_outputs']) + 1))
                else:
                    loss += loss_i
                loss_out.update(loss_out_i)

        # CLICA: cluster-instance 对比对齐 (训练时启用的辅助 loss)
        clica_loss = torch.tensor(0.0, device=pred_masks[0].device)
        if (getattr(self, 'cluster_inst_align_weight', 0.0) > 0
                and pred.get('cluster_feats_list') is not None
                and pred.get('cluster_ids_list') is not None):
            clica_loss = self.loss_cluster_inst_align(
                pred['cluster_feats_list'], pred['cluster_ids_list'],
                sp_ins_labels, object_idss, batch_offsets,
                temperature=self.cluster_inst_align_temperature)
            loss = loss + self.cluster_inst_align_weight * clica_loss
        loss_out['cluster_inst_align_loss'] = clica_loss

        # OBJG: cluster-token 目标对象感知 (训练时启用的辅助 loss)
        objg_loss = torch.tensor(0.0, device=pred_masks[0].device)
        if (getattr(self, 'cluster_objg_weight', 0.0) > 0
                and sp_ref_masks is not None
                and pred.get('cluster_feats_list') is not None
                and pred.get('cluster_ids_list') is not None):
            objg_loss = self.loss_cluster_objg(
                pred['cluster_feats_list'], pred['cluster_ids_list'],
                sp_ins_labels, object_idss, sp_ref_masks, batch_offsets)
            loss = loss + self.cluster_objg_weight * objg_loss
        loss_out['cluster_objg_loss'] = objg_loss

        # LQA: cluster-token 语言查询语义对齐 (训练时启用的辅助 loss)
        lqa_loss = torch.tensor(0.0, device=pred_masks[0].device)
        if (getattr(self, 'cluster_lqa_weight', 0.0) > 0
                and sp_ref_masks is not None
                and pred.get('cluster_feats_list') is not None
                and pred.get('cluster_ids_list') is not None):
            # 语言查询嵌入: proj_tokens [B,L,64] 按 lang_masks 池化 (有效 token 均值)
            lang_emb = None
            proj_tokens = pred.get('proj_tokens')
            if proj_tokens is not None and lang_masks is not None:
                lm = lang_masks.float().unsqueeze(-1)  # [B,L,1]
                length = lang_masks.float().sum(-1, keepdim=True).clamp(min=1)  # [B,1]
                lang_emb = (proj_tokens * lm).sum(1) / length  # [B,64]
            lqa_loss = self.loss_cluster_lqa(
                pred['cluster_feats_list'], pred['cluster_ids_list'], lang_emb,
                sp_ins_labels, object_idss, sp_ref_masks, batch_offsets,
                temperature=self.cluster_lqa_temperature)
            loss = loss + self.cluster_lqa_weight * lqa_loss
        loss_out['cluster_lqa_loss'] = lqa_loss

        loss_out['loss'] = loss

        return loss, loss_out