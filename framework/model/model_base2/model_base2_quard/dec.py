import torch
import torch.nn as nn
from .sample_model import SamplingModule
import framework.torch.nn.functional as F
from framework.torch.nn import MultiheadAttention
from hier_postprocess import Cluster_Attn
class ThreeLayerMLP(nn.Module):
    """A 3-layer MLP with normalization and dropout."""

    def __init__(self, dim, out_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(dim, dim, 1, bias=False),
            nn.BatchNorm1d(dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Conv1d(dim, dim, 1, bias=False),
            nn.BatchNorm1d(dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Conv1d(dim, out_dim, 1)
        )

    def forward(self, x):
        """Forward pass, x can be (B, dim, N)."""
        return self.net(x)

class CrossAttentionLayer(nn.Module):

    def __init__(self, d_model=256, nhead=8, dropout=0.0):
        super().__init__()
        self.attn = MultiheadAttention(d_model, nhead, dropout=dropout, batch_first=True)
        self.norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
        self._reset_parameters()
        self.nhead = nhead

    def _reset_parameters(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def with_pos_embed(self, tensor, pos):
        return tensor if pos is None else tensor + pos

    def forward(self, source, query, batch_mask=None, attn_mask=None, pe=None, att_weights=None):
        """
        source (B, N_p, d_model)
        batch_offsets Tensor (b, n_p)
        query Tensor (b, n_q, d_model)
        """
        B = query.shape[0]
        query = self.with_pos_embed(query, pe)
        k = v = source
        if attn_mask is not None:
            attn_mask = attn_mask.unsqueeze(1).repeat(1, self.nhead, 1, 1).view(B*self.nhead, query.shape[1], k.shape[1])
            output, output_weight, src_weight = self.attn(query, k, v, key_padding_mask=batch_mask, attn_mask=attn_mask, att_weights =att_weights)  # (1, 100, d_model)
        else:
            output, output_weight, src_weight = self.attn(query, k, v, key_padding_mask=batch_mask, att_weights =att_weights)
        output = self.dropout(output) + query
        if self.norm is not None: output = self.norm(output)

        return output, output_weight, src_weight # (b, n_q, d_model), (b, n_q, n_v)

class SelfAttentionLayer(nn.Module):

    def __init__(self, d_model=256, nhead=8, dropout=0.0, glu = False):
        super().__init__()
        self.attn = MultiheadAttention(
            d_model,
            nhead,
            dropout=dropout,
            batch_first=True,
        )
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
        """
        x Tensor (b, n_w, c)
        x_mask Tensor (b, n_w)
        """
        B = x.shape[0]
        q = k = self.with_pos_embed(x, pe)
        if attn_mask is not None:
            attn_mask = attn_mask.unsqueeze(1).repeat(1, self.nhead, 1, 1).view(B*self.nhead, q.shape[1], k.shape[1])
            output, output_weight, src_weight = self.attn(q, k, x, key_padding_mask=x_mask, attn_mask=attn_mask, att_weights =att_weights)  # (1, 100, d_model)
        else:
            output, output_weight, src_weight = self.attn(q, k, x, key_padding_mask=x_mask, att_weights =att_weights)
        if self.glu:
            output = self.glu_p(output) * (self.glu_g(output).sigmoid())
        output = self.dropout(output) + x
        if self.norm is not None: output = self.norm(output)
        return output



class AgentAttention(nn.Module):
    def __init__(self, d_model, n_heads,gamma,dropout=0.1):
        super(AgentAttention, self).__init__()
        self.fc_q = nn.Linear(d_model, d_model)
        self.fc_k = nn.Linear(d_model, d_model)
        self.fc_v = nn.Linear(d_model, d_model)
        self.fc_o = nn.Linear(d_model, d_model)
        self.fc_a = nn.Linear(d_model, d_model)
   

        self.norm = nn.LayerNorm(d_model) 
        self.n_heads = n_heads
        self.d_model = d_model
        self.head_dim = d_model // self.n_heads
        self.scale = self.head_dim ** -0.5
        self.softmax = nn.Softmax(dim=-1)
        self.attn_drop = nn.Dropout(dropout)
        self.dropout_output = nn.Dropout(dropout)
        self.gamma=gamma
    #     self.init_weights()


    # def init_weights(self):
    #     nn.init.xavier_uniform_(self.fc_q.weight)
    #     nn.init.xavier_uniform_(self.fc_k.weight)
    #     nn.init.xavier_uniform_(self.fc_v.weight)
    #     nn.init.xavier_uniform_(self.fc_o.weight)
    #     nn.init.constant_(self.fc_q.bias, 0)
    #     nn.init.constant_(self.fc_k.bias, 0)
    #     nn.init.constant_(self.fc_v.bias, 0)
    #     nn.init.constant_(self.fc_o.bias, 0)
    def get_scg_weight(self, pos_q, pos_k=None, k_mask=None, k=None):
        if pos_k == None: pos_k = pos_q
        # dis = torch.cdist(pos_q, pos_k, p=2)
        dis = ((pos_q.unsqueeze(2)-pos_k.unsqueeze(1))**2).sum(-1)
        if k_mask is not None:
            dis = torch.masked_fill(dis, k_mask.unsqueeze(1).repeat(1,pos_q.shape[1],1), 1000000.0)
        gamma = self.gamma  # 可调节参数，控制衰减速度（值越大，权重下降越快）
        scg_weight = torch.exp(-gamma * dis)  # dis越小，att_weights越接近1
        B, N, _ = pos_q.shape
        scg_mask = torch.zeros((pos_q.shape[0],pos_q.shape[1],pos_k.shape[1]),device=pos_q.device).bool()
        if k is not None:
            ind = torch.topk(dis, k, dim=-1, largest=False)[1]
            i_indices = torch.arange(B, device=dis.device)[:, None, None].expand(-1, N, k)
            j_indices = torch.arange(N, device=dis.device)[None, :, None].expand(B, -1, k)
            scg_mask[i_indices, j_indices, ind] = True
        else:
            scg_mask=None
        return scg_weight, scg_mask



    def forward(self, x, agent, attn_mask, x_pos, agent_pos):
        # print(attn_mask.size())
        
        b, n, c = x.shape
        _, an, _  = agent.shape
        attn_mask = attn_mask.unsqueeze(1).repeat(1, self.n_heads, 1).unsqueeze(2).repeat(1, 1, an, 1)

        if attn_mask is not None and attn_mask.dtype == torch.bool:
            new_attn_mask = torch.zeros_like(attn_mask, dtype=torch.float)
            new_attn_mask.masked_fill_(attn_mask, float("-inf"))
            attn_mask = new_attn_mask
     
        agent_K_mask = attn_mask
        Q_agent_mask = attn_mask.permute(0,1,3,2)

        scg_weight, scg_mask = self.get_scg_weight(agent_pos, x_pos)
        scg_weight = scg_weight.unsqueeze(1).expand(-1, self.n_heads, -1, -1)   #bs,h,an,n
        scg_weight_T = scg_weight.permute(0,1,3,2)
        Q = self.fc_q(x).reshape(b, n, self.n_heads, self.head_dim).permute(0, 2, 1, 3)
        K = self.fc_k(x).reshape(b, n, self.n_heads, self.head_dim).permute(0, 2, 1, 3)
        V = self.fc_v(x).reshape(b, n, self.n_heads, self.head_dim).permute(0, 2, 1, 3)
        agent_tokens = self.fc_a(agent).reshape(b, an, self.n_heads, self.head_dim).permute(0, 2, 1, 3)

        
        # 代理向量聚合信息
        agent_attn = (agent_tokens * self.scale) @ K.transpose(-2, -1) ### bs, h, an, n
        agent_attn = agent_attn*scg_weight

        if agent_K_mask is not None:
            agent_attn += agent_K_mask


        agent_attn = self.softmax(agent_attn)  
        agent_attn = self.attn_drop(agent_attn) 
        agent_v = agent_attn @ V

        q_attn = (Q * self.scale) @ agent_tokens.transpose(-2, -1)
        q_attn = q_attn*scg_weight_T
        q_attn = self.softmax(q_attn) ## bs,N,n
        q_attn = self.attn_drop(q_attn)
        output = q_attn @ agent_v
        output = output.transpose(1, 2).reshape(b, n, c)
        output = self.fc_o(output)

        output = self.dropout_output(output) + x
        if self.norm is not None: output = self.norm(output)


        return output


class FFN(nn.Module):

    def __init__(self, d_model, hidden_dim, dropout=0.0, activation_fn='relu'):
        super().__init__()
        if activation_fn == 'relu':
            self.net = nn.Sequential(
                nn.Linear(d_model, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_dim, d_model),
                nn.Dropout(dropout),
            )
        elif activation_fn == 'gelu':
            self.net = nn.Sequential(
                nn.Linear(d_model, hidden_dim),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_dim, d_model),
                nn.Dropout(dropout),
            )
        self.norm = nn.LayerNorm(d_model)

    def forward(self, x, norm=True):
        output = self.net(x)
        output = output + x
        if norm: output = self.norm(output)
        return output

class MLP(nn.Module):
    """ Very simple multi-layer perceptron (also called FFN)"""

    def __init__(self, input_dim, hidden_dim, output_dim, num_layers):
        super().__init__()
        self.num_layers = num_layers
        h = [hidden_dim] * (num_layers - 1)
        self.layers = nn.ModuleList(nn.Linear(n, k) for n, k in zip([input_dim] + h, h + [output_dim]))

    def forward(self, x):
        for i, layer in enumerate(self.layers):
            x = F.relu(layer(x)) if i < self.num_layers - 1 else layer(x)
        return x
    

class Encoder_layer(nn.Module):
    def __init__(
            self,
            d_model=256,
            nhead=8,
            hidden_dim=1024,
            dropout=0.0,  
            activation_fn='relu',
            gamma=0.3
                 ):
        super().__init__()
        self.lla = SelfAttentionLayer(d_model, nhead, dropout)
        self.lia = CrossAttentionLayer(d_model, nhead, dropout)
        # self.ila = CrossAttentionLayer(d_model, nhead, dropout)
        self.lia_ffn = FFN(d_model, hidden_dim, dropout, activation_fn)


    def forward(self, lang_feats, lang_masks, inst_feats, batch_mask, query, sp_pos, query_pos):
        lang_feats = self.lla(lang_feats, lang_masks)
        lang_feats, _, _ = self.lia(inst_feats, lang_feats, batch_mask, None)
        lang_feats = self.lia_ffn(lang_feats)
        return lang_feats, inst_feats


class Decoder_layer(nn.Module):
    # 类级别的共享模块
    _shared_modules_initialized = False
    
    @classmethod
    def _initialize_shared_modules(cls, d_model, nhead, hidden_dim, dropout, activation_fn,contrastive_align_loss,num_proposal_fine,gamma):
        if not cls._shared_modules_initialized:
            # 创建共享模块
            cls.share_indi_embedding = nn.Sequential(nn.Linear(d_model, d_model), nn.ReLU(), nn.Linear(d_model, 2), nn.Linear(2, 2))
            if contrastive_align_loss:
                cls.share_contrastive_align_projection_vision = nn.Sequential(nn.Linear(d_model, d_model),nn.ReLU(),nn.Linear(d_model, d_model),nn.ReLU(),nn.Linear(d_model, 64))
                cls.share_contrastive_align_projection_text = nn.Sequential(nn.Linear(d_model, d_model),nn.ReLU(),nn.Linear(d_model, d_model),nn.ReLU(),nn.Linear(d_model, 64))         
            cls.share_norm_qqa = nn.LayerNorm(d_model)
            cls.share_out_norm = nn.LayerNorm(d_model)
            cls.share_out_score = nn.Sequential(nn.Linear(d_model, d_model), nn.ReLU(), nn.Linear(d_model, 1))
            cls._shared_modules_initialized = True


    def __init__(
            self,
            d_model=256,
            nhead=8,
            hidden_dim=1024,
            dropout=0.0,  
            activation_fn='relu',
            contrastive_align_loss=False,
            num_proposal_fine=512,
            gamma=0.3
                 ):
        super().__init__()
        self.qia = CrossAttentionLayer(d_model, nhead, dropout)
        self.qla = CrossAttentionLayer(d_model, nhead, dropout)
        self.qqa = SelfAttentionLayer(d_model, nhead, dropout)
        self.qqa_ffn = FFN(d_model, hidden_dim, dropout, activation_fn)
        self.contrastive_align_loss = contrastive_align_loss
        self.gamma = gamma

        self.num_proposal_fine = num_proposal_fine

        # 确保共享模块已初始化
        Decoder_layer._initialize_shared_modules(d_model, nhead, hidden_dim, dropout, activation_fn,contrastive_align_loss,num_proposal_fine,gamma)

        # 注册共享模块到当前实例 (关键步骤!)
        self.add_module("indi_embedding", Decoder_layer.share_indi_embedding)
        self.add_module("contrastive_align_projection_vision", Decoder_layer.share_contrastive_align_projection_vision)
        self.add_module("contrastive_align_projection_text", Decoder_layer.share_contrastive_align_projection_text)
        self.add_module("norm_qqa", Decoder_layer.share_norm_qqa)
        self.add_module("out_norm", Decoder_layer.share_out_norm)
        self.add_module("out_score", Decoder_layer.share_out_score)






    def prediction_head(self, query, mask_feats, batch_mask):
        query = self.out_norm(query)
        pred_scores = self.out_score(query)
        pred_masks = torch.einsum('bnd,bmd->bnm', query, mask_feats)
        return pred_scores, pred_masks


    def get_scg_weight(self, pos_q, pos_k=None, k_mask=None, k=None):
        if pos_k == None: pos_k = pos_q
        # dis = torch.cdist(pos_q, pos_k, p=2)
        dis = ((pos_q.unsqueeze(2)-pos_k.unsqueeze(1))**2).sum(-1)
        if k_mask is not None:
            dis = torch.masked_fill(dis, k_mask.unsqueeze(1).repeat(1,pos_q.shape[1],1), 1000000.0)
        gamma = self.gamma  # 可调节参数，控制衰减速度（值越大，权重下降越快）
        scg_weight = torch.exp(-gamma * dis)  # dis越小，att_weights越接近1
        B, N, _ = pos_q.shape
        scg_mask = torch.zeros((pos_q.shape[0],pos_q.shape[1],pos_k.shape[1]),device=pos_q.device).bool()
        if k is not None:
            ind = torch.topk(dis, k, dim=-1, largest=False)[1]
            i_indices = torch.arange(B, device=dis.device)[:, None, None].expand(-1, N, k)
            j_indices = torch.arange(N, device=dis.device)[None, :, None].expand(B, -1, k)
            scg_mask[i_indices, j_indices, ind] = True
        else:
            scg_mask=None
        return scg_weight, scg_mask
    


    def forward(self, lang_feats, lang_masks, inst_feats, batch_mask, query, sp_pos, query_pos, k):
       

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






class DEC(nn.Module):
    """
    in_channels List[int] (4,) [64,96,128,160]
    """
    shared_initialized = False  # 标记是否已经初始化共享模块
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
        num_proposal_query_inst = [128,64,32,16,8,4],
        cluster_layer_nums=[256,64,8],
        per_layer_topk_list=[4,4,4,4],
        cluster_att_num_layers=2,
        cluster_att_init=0.0
    ):
        super().__init__()
        self.num_layer = num_layer
        self.num_class = num_class
        self.d_model = d_model
        self.input_proj = nn.Sequential(nn.Linear(in_channel, d_model), nn.LayerNorm(d_model), nn.ReLU())
        
        self.input_proj_2d = nn.Sequential(nn.Linear(1024, d_model*2),nn.ReLU(),nn.Linear(d_model*2, d_model),nn.ReLU(),nn.Linear(d_model, d_model))#clip
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
        self.query_generator = nn.Sequential(nn.Linear(d_model, d_model),nn.ReLU(),nn.Linear(d_model, d_model),nn.ReLU(),nn.Linear(d_model, d_model))

        
        self.scg_head = SelfAttentionLayer(d_model, nhead, dropout=0, glu=True)
        self.iter_pred = iter_pred
        self.cluster_att_num_layers = min(cluster_att_num_layers, num_layer)
        
        self.cluster_att = Cluster_Attn(d_model=d_model, nhead=nhead, cluster_layer_nums=cluster_layer_nums, per_layer_topk_list=per_layer_topk_list,dropout=dropout)
        self.cluster_att_gates = nn.Parameter(torch.full((num_layer,), float(cluster_att_init)))
        self.norm = nn.LayerNorm(d_model)

        self.encoder_layers = nn.ModuleList([Encoder_layer(d_model, nhead, hidden_dim, dropout, activation_fn,gamma) for i in range(num_layer)])
        self.decoder_layers = nn.ModuleList([Decoder_layer(d_model, nhead, hidden_dim, dropout, activation_fn, contrastive_align_loss, num_proposal_fine, gamma) for i in range(num_layer)])
        



    def forward_iter_pred(self, x, fps_seed_sp, batch_offsets, lang_feats=None, lang_masks=None, sp_pos=None, feats_2d=None):
        """
        x [B*M, inchannel]
        """
        
        lang_feats = self.lang_proj(lang_feats) 
        lang_feats = self.lang_norm(lang_feats)  
        lang_masks = ~(lang_masks.bool())
        inst_feats = self.input_proj(x)
        
        inst_feats_2d = self.input_proj_2d(feats_2d)
        inst_feats = self.sum_norm(inst_feats+inst_feats_2d)
        

        inst_feats, batch_mask = self.get_batches(inst_feats, batch_offsets)
        
        self.cluster_att.get_cluster(sp_pos, batch_offsets)  ## 划分层级

        sp_pos, _ = self.get_batches(sp_pos, batch_offsets)
                
        seed_sp = inst_feats.gather(dim=1, index=fps_seed_sp.long().unsqueeze(-1).repeat(1, 1, inst_feats.size(-1)))
        seed_sp_pos = sp_pos.gather(dim=1, index=fps_seed_sp.long().unsqueeze(-1).repeat(1, 1, sp_pos.size(-1)))
        
        scg_weights, _ = self.decoder_layers[0].get_scg_weight(seed_sp_pos)
        seed_sp = self.scg_head(seed_sp, att_weights = scg_weights)

         # sampling
        if hasattr(self, 'sampling_module') and self.sampling_module is not None:
            sample_inds, ref_scores = self.sampling_module(seed_sp, lang_feats, None, lang_masks)
            sample_inds = sample_inds.long()
            sampled_seed = seed_sp.gather(dim=1, index=sample_inds.unsqueeze(-1).repeat(1, 1, seed_sp.size(-1)))
            query_pos = seed_sp_pos.gather(dim=1, index=sample_inds.unsqueeze(-1).repeat(1, 1, seed_sp_pos.size(-1)))
            query = self.query_generator(sampled_seed)
        else:
            query = self.query_generator(seed_sp)
            query_pos = seed_sp_pos
            

        
        lang_feats_list, inst_feats_list = [], []
        prediction_masks, prediction_scores, prediction_indis, proj_queries, proj_tokens = [], [], [], [], []


        for layer_i, layer in enumerate(self.encoder_layers):
            if layer_i < self.cluster_att_num_layers:
                # Start from a near-zero contribution so the sparse branch does not
                # destabilize the pretrained feature stream at the beginning.
                gate = torch.tanh(self.cluster_att_gates[layer_i])
                inst_feats = inst_feats + gate * self.cluster_att(inst_feats, batch_offsets, batch_mask)

            lang_feats, inst_feats = layer(lang_feats, lang_masks, inst_feats, batch_mask, query, sp_pos, query_pos)
            lang_feats_list.append(lang_feats)
            inst_feats_list.append(inst_feats)

            query, pred_scores, pred_masks, pred_indis, proj_query, proj_token \
                = self.decoder_layers[layer_i](lang_feats, lang_masks, inst_feats, \
                         batch_mask, query, sp_pos, query_pos, self.num_proposal_query_inst[layer_i])

            prediction_scores.append(pred_scores)
            prediction_masks.append(pred_masks)
            prediction_indis.append(pred_indis)
            proj_queries.append(proj_query)
            proj_tokens.append(proj_token)

        
        return {
            'masks': pred_masks,
            'batch_mask': batch_mask,
            'scores': pred_scores,
            'indis': pred_indis, # [B, B_q, 2]
            'proj_queries': proj_queries[-1],
            'proj_tokens': proj_tokens[-1],
            'sample_inds': sample_inds, # [B, K]
            'ref_scores': ref_scores, # [B, M]
            'aux_outputs': [{
                'masks': a,
                'scores': b,
                'proj_queries': c,
                'indis': d,
                'proj_tokens': e,
            } for a, b, c, d, e in zip(
                prediction_masks[:-1],
                prediction_scores[:-1],
                proj_queries[:-1],
                prediction_indis[:-1],
                proj_tokens[:-1],
            )],
        }
        
    def get_batches(self, x, batch_offsets):
        B = len(batch_offsets) - 1
        max_len = max(batch_offsets[1:] - batch_offsets[:-1])
        if torch.is_tensor(max_len):
            max_len = max_len.item()
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
    

    
    def forward(self, x, fps_seed_sp, batch_offsets, lang_feats=None, lang_masks=None, sp_pos=None, feats_2d=None):
        if self.iter_pred:
            return self.forward_iter_pred(x, fps_seed_sp, batch_offsets, lang_feats, lang_masks, sp_pos, feats_2d)
        else:
            raise NotImplementedError
