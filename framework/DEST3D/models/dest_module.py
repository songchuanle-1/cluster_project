# Copyright (c) 2024, Tri Dao, Albert Gu.
import math
import copy
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor
from timm.models.layers import DropPath
from typing import Optional
from einops import rearrange, repeat
from issm_triton.issm_combined import ISSM_chunk_scan_combined
from issm_triton.layernorm_gated import RMSNorm as RMSNormGated
from models.multi_head_attention import MultiheadAttention

def _get_activation_fn(activation):
    """Return an activation function given a string"""
    if activation == "relu":
        return F.relu
    if activation == "gelu":
        return F.gelu
    if activation == "glu":
        return F.glu
    raise RuntimeError(F"activation should be relu/gelu, not {activation}.")

def convert_corners_camera2lidar(corners_camera):
    corners_lidar = corners_camera
    corners_lidar[..., 1] *= -1 # X, -Z, Y
    corners_lidar[..., [0, 1, 2]] = corners_lidar[..., [0, 2, 1]]
    return corners_lidar

def flip_axis_to_camera_tensor(pc):
    """Flip X-right,Y-forward,Z-up to X-right,Y-down,Z-forward
    Input and output are both (N,3) array
    """
    pc2 = torch.clone(pc)
    pc2[..., [0, 1, 2]] = pc2[..., [0, 2, 1]]  # cam X,Y,Z = depth X,-Z,Y
    pc2[..., 1] *= -1
    return pc2

def get_3d_box_batch_tensor(box_size, angle, center):
    assert isinstance(box_size, torch.Tensor) # 512, 3
    assert isinstance(angle, torch.Tensor) # 512
    assert isinstance(center, torch.Tensor) # 512, 3

    reshape_final = False
    if angle.ndim == 2:
        assert box_size.ndim == 3
        assert center.ndim == 3
        bsize = box_size.shape[0]
        nprop = box_size.shape[1]
        box_size = box_size.reshape(-1, box_size.shape[-1])
        angle = angle.reshape(-1)
        center = center.reshape(-1, 3)
        reshape_final = True

    input_shape = angle.shape
    R = roty_batch_tensor(angle) # I
    l = torch.unsqueeze(box_size[..., 0], -1)  #dx lidar->dx_camara
    w = torch.unsqueeze(box_size[..., 1], -1)  #dy lidar->dz_camara
    h = torch.unsqueeze(box_size[..., 2], -1)  #dz lidar->-dy_camara
    corners_3d = torch.zeros(
        tuple(list(input_shape) + [8, 3]), device=box_size.device, dtype=torch.float32
    ) # 512, 8, 3
    corners_3d[..., :, 0] = torch.cat(
        (l / 2, l / 2, -l / 2, -l / 2, l / 2, l / 2, -l / 2, -l / 2), -1
    )
    corners_3d[..., :, 1] = torch.cat(
        (h / 2, h / 2, h / 2, h / 2, -h / 2, -h / 2, -h / 2, -h / 2), -1
    )
    corners_3d[..., :, 2] = torch.cat(
        (w / 2, -w / 2, -w / 2, w / 2, w / 2, -w / 2, -w / 2, w / 2), -1
    )
    tlist = [i for i in range(len(input_shape))] # [0]
    tlist += [len(input_shape) + 1, len(input_shape)] # [0, 2, 1]
    corners_3d = torch.matmul(corners_3d, R.permute(tlist)) # .T
    corners_3d += torch.unsqueeze(center, -2)
    if reshape_final:
        corners_3d = corners_3d.reshape(bsize, nprop, 8, 3)
    return corners_3d

def roty_batch_tensor(t):
    input_shape = t.shape
    output = torch.zeros(
        tuple(list(input_shape) + [3, 3]), dtype=torch.float32, device=t.device
    )
    c = torch.cos(t)
    s = torch.sin(t)
    output[..., 0, 0] = c
    output[..., 0, 2] = s
    output[..., 1, 1] = 1
    output[..., 2, 0] = -s
    output[..., 2, 2] = c
    return output

def get_clones(module, N):
    return nn.ModuleList([copy.deepcopy(module) for i in range(N)])

def box_parametrization_to_corners(box_center_unnorm, box_size, box_angle):
    box_center_upright = flip_axis_to_camera_tensor(box_center_unnorm)
    boxes = get_3d_box_batch_tensor(box_size, box_angle, box_center_upright)
    boxes = convert_corners_camera2lidar(boxes)
    return boxes

class RGBlock(nn.Module):
    def __init__(self, in_features, hidden_features=None, out_features=None, act_layer=nn.GELU, drop=0.,
                 channels_first=False, kernel_size=7, padding=3, use_dwconv=False):
        super().__init__()
        out_features = out_features or in_features
        hidden_features = hidden_features or in_features
        self.use_dwconv = use_dwconv
        self.fc1 = nn.Conv1d(in_features, hidden_features * 2, kernel_size=1)
        if use_dwconv:
            self.dwconv = nn.Conv1d(hidden_features, hidden_features, kernel_size=kernel_size, stride=1, padding=padding, bias=True,
                                groups=hidden_features)
        self.act = act_layer()
        self.fc2 = nn.Conv1d(hidden_features, out_features, kernel_size=1)
        self.drop = nn.Dropout(drop)

    def forward(self, x):
        x, v = self.fc1(x).chunk(2, dim=1)
        if self.use_dwconv:
            x = self.act(self.dwconv(x) + x) * v
        else:
            x = self.act(x) * v
        x = self.drop(x)
        x = self.fc2(x)
        x = self.drop(x)
        return x

class FFNBlock(nn.Module):
    def __init__(self, in_features, hidden_features=None, out_features=None, act_layer=nn.ReLU, drop=0.):
        super().__init__()
        out_features = out_features or in_features
        hidden_features = hidden_features or in_features
        
        self.fc1 = nn.Conv1d(in_features, hidden_features, kernel_size=1)
        self.act = act_layer()
        self.fc2 = nn.Conv1d(hidden_features, out_features, kernel_size=1)
        self.drop = nn.Dropout(drop)
        
    def forward(self, x):
        x = self.drop(self.act(self.fc1(x)))
        x = self.drop(self.fc2(x))
        return x

class BoxDistFun(nn.Module):
    def __init__(
            self,
            log_scale:int = 512,
            rpe_quant:str = 'bilinear_4_10',
            out_dim:int = 4,
            rpe_dim:int = 128,
            max_query_chunk:int = 64,
            max_key_chunk:int = 2048,
            use_half:bool = True,
            ):
        super().__init__()
        self.log_scale = log_scale
        self.interp_method, max_value, num_points = rpe_quant.split('_')
        max_value, num_points = float(max_value), int(num_points)
        relative_coords_table = torch.stack(torch.meshgrid(
            torch.linspace(-max_value, max_value, num_points, dtype=torch.float32),
            torch.linspace(-max_value, max_value, num_points, dtype=torch.float32),
            torch.linspace(-max_value, max_value, num_points, dtype=torch.float32),
        ), dim=-1).unsqueeze(0)
        self.register_buffer("relative_coords_table", relative_coords_table)
        self.max_value = max_value
        self.cpb_mlps = self.build_cpb_mlp(3, rpe_dim, out_dim)
        self.max_query_chunk = max_query_chunk
        self.max_key_chunk = max_key_chunk
        self.use_half = use_half

    def build_cpb_mlp(self, in_dim, hidden_dim, out_dim):
        cpb_mlp = nn.Sequential(nn.Linear(in_dim, hidden_dim, bias=True),
                                nn.ReLU(inplace=False),
                                nn.Linear(hidden_dim, out_dim, bias=False))
        return cpb_mlp

    def forward(self, key_xyz, query_xyz, query_size, query_angle):
        B, nQ = query_xyz.shape[:2]
        nP = key_xyz.shape[1]
        device = key_xyz.device
        # Precompute rpe table (optionally half precision)
        rpe_table = self.cpb_mlps(self.relative_coords_table).permute(0, 4, 1, 2, 3)  # (1, out_dim, 10,10,10)
        if self.use_half and key_xyz.dtype == torch.float32:
            rpe_table = rpe_table.to(torch.float16)
        out_dim = rpe_table.shape[1]

        chunk = max(1, self.max_query_chunk)
        results = []
        for start in range(0, nQ, chunk):
            end = min(nQ, start + chunk)
            q_xyz_chunk = query_xyz[:, start:end]
            q_size_chunk = query_size[:, start:end]
            q_angle_chunk = query_angle[:, start:end]

            # 8 corners per box chunk
            query_corners = box_parametrization_to_corners(q_xyz_chunk, q_size_chunk, q_angle_chunk)
            # shape (B, nQc, 8, 3)
            # Rotation matrices per corner
            R = roty_batch_tensor(q_angle_chunk.repeat((1, 8)))  # (B, nQc*8, 3, 3)

            key_chunks = []
            for kp in range(0, nP, self.max_key_chunk):
                kp_end = min(nP, kp + self.max_key_chunk)
                key_xyz_chunk = key_xyz[:, kp:kp_end, :]

                deltas = query_corners.reshape(B, -1, 3)[:, :, None, :] - key_xyz_chunk[:, None, :, :]  # (B, nQc*8, nPk, 3)
                deltas[..., 2] *= -1
                deltas[..., [0, 1, 2]] = deltas[..., [0, 2, 1]]
                deltas = torch.matmul(deltas, R)
                deltas[..., 1] *= -1
                deltas[..., [0, 1, 2]] = deltas[..., [0, 2, 1]]

                deltas = torch.sign(deltas) * torch.log2(torch.abs(deltas) * self.log_scale + 1.0) / np.log2(8)
                delta = deltas / self.max_value  # (B, nQc*8, nPk, 3)

                grid = delta.view(1, 1, 1, -1, 3).to(rpe_table.dtype)
                rpe_part = F.grid_sample(rpe_table, grid, mode=self.interp_method, align_corners=False)
                rpe_part = rpe_part.reshape(out_dim, B, end - start, 8, kp_end - kp)  # (out_dim, B, nQc, 8, nPk)
                dist_part = rpe_part.sum(dim=-2).permute(1, 3, 2, 0)  # (B, nPk, nQc, out_dim)
                key_chunks.append(dist_part)

            dist_chunk = torch.cat(key_chunks, dim=1)  # (B, nP, nQc, out_dim)
            results.append(dist_chunk)

        dist = torch.cat(results, dim=2)  # (B, nP, nQ, out_dim)
        # 保持返回 dtype 与输入一致，避免后续 Linear 发生 Half/Float 不匹配
        if dist.dtype != key_xyz.dtype:
            dist = dist.to(key_xyz.dtype)
        return dist


class ISSMDecoderLayer(nn.Module):
    def __init__(self, d_model, nhead, dim_feedforward=2048, dropout=0.1, activation="relu",
                 self_posembed=None, issm_posembed=None, num_proposal=256, use_biscan=False, last_layer=False):
        super().__init__()
        self.last_layer = last_layer
        self.in_proj_key = nn.Sequential(
            nn.Conv1d(d_model, d_model, kernel_size=1, stride=1, padding=0, bias=False),
            nn.BatchNorm1d(d_model),
            nn.SiLU()
        )
        self.self_attn = MultiheadAttention(d_model, nhead, dropout=dropout)
        self.norm_scan_key = nn.LayerNorm(d_model)
        self.norm_scan_query = nn.LayerNorm(d_model)
        self.spatial_dist = BoxDistFun(out_dim=16)
        self.ISSM_scan = MultiHeadISSMScan(d_model=d_model, d_state=num_proposal, d_dist=16, chunk_size=num_proposal, nheads=nhead, ngroups=1, expand=1, use_biscan=use_biscan)
        
        if not self.last_layer:
            self.norm_ffn_key = nn.LayerNorm(d_model)
            self.mlp_key = RGBlock(d_model, d_model, d_model, drop=dropout, kernel_size=7, padding=3, use_dwconv=True)
            self.norm_out_key = nn.BatchNorm1d(d_model)

        self.drop_path = DropPath(dropout) if dropout > 0. else nn.Identity()
        self.norm_ffn_query = nn.LayerNorm(d_model)
        self.mlp_query = RGBlock(d_model, dim_feedforward, d_model, drop=dropout, kernel_size=1, padding=0)
        self.norm_out_query = nn.BatchNorm1d(d_model)
        self.weight_dist = nn.Parameter(torch.ones(1) * 15).cuda()

        self.self_posembed = self_posembed
        self.issm_posembed = issm_posembed

    def with_pos_embed(self, tensor, pos_embed: Optional[Tensor]):
        return tensor if pos_embed is None else tensor + pos_embed

    def local_mask(self, key_xyz, query_pos, dist=None):
        query_xyz = query_pos[:, :, :3]
        query_radius = query_pos[:, :, 3:].max(dim=-1)[0].clamp_min(0.64)

        if dist is None:
            dist = torch.cdist(key_xyz, query_xyz, p=2)
        # entries that are True in the mask do not contribute to self-attention
        # so points outside the radius are not considered
        mask = dist >= query_radius.unsqueeze(1)
        return mask, dist
    
    def local_weight(self, key_xyz, query_pos, dist=None):
        query_xyz = query_pos[:, :, :3]
        query_radius = torch.sqrt(torch.sum(query_pos[:, :, 3:] ** 2, dim=-1)).clamp_min(0.64)

        if dist is None:
            dist = torch.cdist(key_xyz, query_xyz, p=2)
        # entries that are True in the mask do not contribute to self-attention
        # so points outside the radius are not considered
        weights = torch.exp(self.weight_dist * ((query_radius.unsqueeze(1) - dist).clamp_max(0.0)))
        return weights

    def forward(self, query, key, query_pos, key_pos):
        """
        :param query: B C Pq
        :param key: B C Pk
        :param query_pos: B Pq 3/6
        :param key_pos: B Pk 3/6
        :param value_pos: [B Pq 3/6]

        :return:
        """
        # NxCxP to PxNxC
        if self.self_posembed is not None:
            query_pos_embed = self.self_posembed(query_pos).permute(0, 2, 1)
        else:
            query_pos_embed = None
        if self.issm_posembed is not None:
            key_pos_embed = self.issm_posembed(key_pos).permute(0, 2, 1)
        else:
            key_pos_embed = None

        # local conv for scene points
        # Ensure key has shape (B, C, Pk) for Conv1d; if (B, Pk, C) swap last two dims
        if key.dim() == 3 and key.shape[1] != self.in_proj_key[0].in_channels and key.shape[2] == self.in_proj_key[0].in_channels:
            key = key.permute(0, 2, 1)
        key = self.in_proj_key(key)
        # key1 = self.LS_conv(key, key_pos.permute(0, 2, 1))
        key1 = key
        
        # global attention for query points
        # Accept either (B, C, Pq) or (B, Pq, C); normalize to (B, Pq, C)
        if query.dim() == 3:
            embed_dim_expected = self.self_attn.embed_dim
            if query.shape[1] == embed_dim_expected and query.shape[2] != embed_dim_expected:
                # format (B, C, Pq) -> (B, Pq, C)
                query = query.permute(0, 2, 1)
            # if already (B, Pq, C) leave unchanged
        q = k = v = self.with_pos_embed(query, query_pos_embed)
        query2 = self.self_attn(q.transpose(0,1), k.transpose(0,1), value=v.transpose(0,1))[0].transpose(0,1)
        query = query + self.drop_path(query2)
        key_norm = self.norm_scan_key(key1.permute(0, 2, 1))
        query_norm = self.norm_scan_query(query)

        # mask, _ = self.local_mask(key_pos, query_pos)
        weights = self.local_weight(key_pos, query_pos)
        # Handle query_pos that may only contain xyz (no size). If size missing, create default.
        if query_pos.shape[-1] >= 6:
            query_xyz = query_pos[..., :3]
            query_size = query_pos[..., 3:6]
        else:
            query_xyz = query_pos[..., :3]
            # default size heuristic: use median radius 0.5
            query_size = torch.full_like(query_xyz, 0.5)
        query_angle = torch.zeros_like(query_xyz[..., 0])
        dist = self.spatial_dist(key_pos, query_xyz, query_size, query_angle)
        key2, query2 = self.ISSM_scan(
            in_key=self.with_pos_embed(key_norm, key_pos_embed), 
            in_query=self.with_pos_embed(query_norm, query_pos_embed), 
            dist=dist, 
            key_xyz=key_pos, 
            mask=weights)
        
        if not self.last_layer:
            key = key + self.drop_path(key2.permute(0, 2, 1))
            key_norm = self.norm_ffn_key(key.permute(0, 2, 1)).permute(0, 2, 1)
            key = key + self.drop_path(self.mlp_key(key_norm))  # FFN
            key = self.norm_out_key(key)
        
        query = query_norm + self.drop_path(query2)
        query_norm = self.norm_ffn_query(query).permute(0, 2, 1)
        query = query.permute(0, 2, 1) + self.drop_path(self.mlp_query(query_norm))  # FFN
        query = self.norm_out_query(query)
        return query, key


class Serialization(nn.Module):
    def __init__(
        self,
        order=["xyz", "yxz"],
        bit=9,
    ):
        super().__init__()
        self.order = order
        self.bit = bit
        self.hilbert_spatial_size = 2 ** self.bit
        self.template = torch.load(f'utils/hilbert/curve_template_3d_rank_{self.bit}.pth')

    def forward(self, points, depth=None):
        """
        Point Cloud Serialization

        relay on ["grid_coord" or "coord" + "grid_size", "batch", "feat"]
        """
        batch, npoint = points.shape[:2]

        index_list = []
        reversed_index_list = []
        for _order in self.order:
            code = []
            for i in range(batch):
                point = points[i]
                grid_coord = torch.div(point - point.min(0)[0], 1/50, rounding_mode="trunc").int()
                grid_coord[grid_coord >= self.hilbert_spatial_size] = self.hilbert_spatial_size - 1
                code_i = self.encode(grid_coord, order=_order)
                code.append(code_i)
            code = torch.cat(code, dim=0).reshape(batch, npoint)
            order = torch.argsort(code, dim=-1)
            reversed_order = torch.argsort(order, dim=-1)
            index_list.append(order.to(points.device))
            reversed_index_list.append(reversed_order.to(points.device))
        
        self.index_list = index_list
        self.reversed_index_list = reversed_index_list

    def encode(self, grid_coord, order="xyz"):
        if order == "xyz":
            code = self.get_hilbert_index_3d_mamba_lite(grid_coord[:, [0, 1, 2]])
        elif order == "xzy":
            code = self.get_hilbert_index_3d_mamba_lite(grid_coord[:, [0, 2, 1]])
        elif order == "yxz":
            code = self.get_hilbert_index_3d_mamba_lite(grid_coord[:, [1, 0, 2]])
        elif order == "yzx":
            code = self.get_hilbert_index_3d_mamba_lite(grid_coord[:, [1, 2, 0]])
        elif order == "zxy":
            code = self.get_hilbert_index_3d_mamba_lite(grid_coord[:, [2, 0, 1]])
        elif order == "zyx":
            code = self.get_hilbert_index_3d_mamba_lite(grid_coord[:, [2, 1, 0]])
        else:
            raise NotImplementedError
        return code

    def get_hilbert_index_3d_mamba_lite(self, coors):
        '''
        coors: (N, x, y, z)
        shift: (shift_x, shift_y, shift_z)
        hilbert_spatial_size: [x, y, z]
        '''
        # new 3D
        x = coors[:, 0]
        y = coors[:, 1]
        z = coors[:, 2]

        flat_coors = (z * self.hilbert_spatial_size * self.hilbert_spatial_size + y * self.hilbert_spatial_size + x).long()
        hil_inds = self.template[flat_coors].long()
        return hil_inds

    def reorder_points(self, points, id=0):
        if len(self.index_list) == 1:
            pts = self.index_list[0]
            reorder_points = points.gather(dim=1, index=torch.tile(pts.unsqueeze(-1), (1, 1, points.shape[-1])))
        else:
            index = id
            self.index = index
            pts = self.index_list[index]
            reorder_points = points.gather(dim=1, index=torch.tile(pts.unsqueeze(-1), (1, 1, points.shape[-1])))
        return reorder_points

    def reversed_reorder_points(self, points):
        if len(self.reversed_index_list) == 1:
            pts = self.reversed_index_list[0]
            reorder_points = points.gather(dim=1, index=torch.tile(pts.unsqueeze(-1), (1, 1, points.shape[-1])))
        else:
            index = self.index
            pts = self.reversed_index_list[index]
            reorder_points = points.gather(dim=1, index=torch.tile(pts.unsqueeze(-1), (1, 1, points.shape[-1])))
        return reorder_points


class PointLiteConv(nn.Module):
    def __init__(self, in_channels:int, out_channels:int):
        """
        Args:
            in_channels (int): Feature dimension of input point
            out_channels (int): Feature dimension of output point
            k (int): The number of neighboring points
        """
        super(PointLiteConv, self).__init__()
        self.dwconv = nn.Conv1d(in_channels, out_channels, kernel_size=7, stride=1, padding=3, bias=True,
                                groups=out_channels)
        self.act = nn.SiLU()

    def forward(self, xyz, feature):
        """
        Args:
            xyz (Tensor): Input point positions, the shape is (B, N, 3).
            feature (Tensor): Input point features, the shape is (B, N, C).
        Returns:
            Tensor: Output features, shape is (B, N, C').
        """
        B, N, _ = xyz.shape
        out = self.act(self.dwconv(feature.transpose(1,2))).transpose(1,2)
        return out


class MultiHeadISSMScan(nn.Module):
    def __init__(
        self,
        d_model: int = 512,        # Input dimension
        d_state: int = 64,         # State dimension
        d_dist: int = 4,           # Distance encoding dimension
        chunk_size: int = 256,     # Chunk size, must be greater than d_state
        nheads: int = 4,           # Number of attention heads
        ngroups: int = 1,          # Number of groups
        expand: int = 2,           # Expansion factor
        use_biscan: bool = True,   # Whether to use bidirectional scan
        A_init_range=(1, 16),      # A matrix initialization range
        dt_min: float = 0.0001,    # Minimum time step
        dt_max: float = 0.1,       # Maximum time step
        dt_init_floor: float = 1e-4,# Time step initialization lower bound
        dt_limit=(0.0, float("inf")),
        layer_idx=None,
        enable_amp: bool = True,   # Enable autocast mixed precision inside forward
    ):
        super().__init__()
        # Basic configuration
        self._init_basic_params(d_model, d_state, d_dist, chunk_size, 
                              nheads, ngroups, expand, use_biscan, dt_limit, layer_idx)
        self._init_projections() # Initialize projection layers
        self._init_dt_params(dt_min, dt_max, dt_init_floor) # Initialize time step parameters
        self._init_state_params(A_init_range) # Initialize state transition parameters
        self._init_output_layers() # Initialize output layers

    def _init_basic_params(self, d_model, d_state, d_dist, chunk_size, 
                          nheads, ngroups, expand, use_biscan, dt_limit, layer_idx):
        """Initialize basic parameters"""
        self.d_model = d_model
        self.d_state = d_state
        self.d_dist = d_dist
        self.chunk_size = chunk_size
        self.nheads = nheads
        self.ngroups = ngroups
        self.expand = expand
        self.use_biscan = use_biscan
        self.d_inner = self.expand * self.d_model
        self.headdim = self.d_inner // self.nheads
        self.dt_limit = dt_limit
        self.layer_idx = layer_idx
        self.enable_amp = True if torch.cuda.is_available() else False

    def _init_projections(self):
        """Initialize input projection layers"""
        # Projection dimensions: [z, x, bct]
        d_in_key_proj = 2 * self.d_inner + 2 * self.ngroups + self.nheads
        self.key_proj = nn.Linear(self.d_model, d_in_key_proj, bias=False)
        
        d_key_conv = self.d_inner + 2 * self.ngroups
        self.key_conv = PointLiteConv(d_key_conv, d_key_conv)
        if self.use_biscan:
            self.key_conv_back = PointLiteConv(d_key_conv, d_key_conv)

        self.query_proj = nn.Linear(self.d_model, self.d_inner, bias=False)
        self.bc_proj = nn.Linear(self.d_dist, 2 * self.ngroups, bias=False) 
        self.dt_proj = nn.Linear(self.d_dist, self.nheads, bias=False)   
    
    def _init_dt_params(self, dt_min, dt_max, dt_init_floor):
        """Initialize time step parameters"""
        dt = torch.exp(
            torch.rand(self.nheads) * (math.log(dt_max) - math.log(dt_min))
            + math.log(dt_min)
        )
        dt = torch.clamp(dt, min=dt_init_floor)
        # Inverse of softplus: https://github.com/pytorch/pytorch/issues/72759
        inv_dt = dt + torch.log(-torch.expm1(-dt))
        self.dt_bias = nn.Parameter(inv_dt)
        self.dt_bias._no_weight_decay = True
    
    def _init_state_params(self, A_init_range):
        """Initialize state transition parameters"""
        assert A_init_range[0] > 0 and A_init_range[1] >= A_init_range[0]
        A = torch.empty((self.nheads), dtype=torch.float32).uniform_(*A_init_range)
        self.A_log = nn.Parameter(torch.log(A))
        self.A_log._no_weight_decay = True
        # D "skip" parameter
        self.D = nn.Parameter(torch.ones(self.nheads))
        self.D._no_weight_decay = True
    
    def _init_output_layers(self):
        """Initialize output layers"""
        # Extra normalization layer right before output projection
        assert RMSNormGated is not None
        self.out_key_proj = nn.Linear(self.d_inner, self.d_model, bias=False)
        self.out_query_proj = nn.Linear(self.d_inner, self.d_model, bias=False)
        self.key_norm = RMSNormGated(self.d_inner, eps=1e-5, norm_before_gate=False)
        self.query_norm = nn.LayerNorm(self.d_inner)

    def forward(self, in_key, in_query, dist, key_xyz, mask=None):
        """
        Forward propagation function
        Args:
            in_key: (B, L, D) - Input sequence
            in_query: (B, K, D) - Query sequence
            dist: (B, L, K, M) - Distance matrix
            mask: (B, L, K) - Mask matrix
        Returns:
            out_key: (B, L, D) - Processed key vector
            out_query: (B, K, D) - Processed query vector
        """
        # 1. Projection transformation (mixed precision region)
        with torch.cuda.amp.autocast(enabled=self.enable_amp):
            zxbcdt = self.key_proj(in_key)
            z, xbc, dt_bias = torch.split(zxbcdt, [self.d_inner, self.d_inner + 2 * self.ngroups, self.nheads], dim=-1)
            xbc = self.key_conv(key_xyz, xbc)
            x, b_bias, c_bias = torch.split(xbc, [self.d_inner, self.ngroups, self.ngroups], dim=-1)
            if self.use_biscan:
                xbc_back = self.key_conv_back(key_xyz, xbc)
                x_back, b_bias_back, c_bias_back = torch.split(xbc_back, [self.d_inner, self.ngroups, self.ngroups], dim=-1)
            initial_states = self.query_proj(in_query)
            initial_states = rearrange(initial_states, "b l (h hd) -> b h hd l", hd=self.headdim)
        # Triton kernels expect fp32; cast tensors to float32 for scan
        x = x.float(); initial_states = initial_states.float();
        b_bias = b_bias.float(); c_bias = c_bias.float();
        if self.use_biscan:
            x_back = x_back.float(); b_bias_back = b_bias_back.float(); c_bias_back = c_bias_back.float()

        # 2. Parameter generation
        # 动态匹配 A 的状态维度为当前 B/C 的最后一维（可能与初始化的 d_state 不同）
        A = -torch.exp(self.A_log)  # (nheads)
        current_dstate = self.bc_proj(dist).shape[-1] // 2  # bc_proj 输出 2*ngroups，再在后续 split 为 ngroups + ngroups
        # B/C 的构造使用 transpose(-1,-2) 得到形状 (B, L, ngroups, K)，其中 K = dist.shape[2]
        # 这里实际期望的 dstate 是 K（查询数量），直接从后续即将构造的 b_base 维度提取更稳健
        # 先根据 dist 推导查询数量 K
        query_count = dist.shape[2]  # K
        A = repeat(A, "h -> h d", d=query_count)
        ### dist (B, L, K, M)
        bc = self.bc_proj(dist) # adaptive bc  ### 变换维度  M->2*ngroups
        b_base, c_base = torch.split(bc, [self.ngroups, self.ngroups], dim=-1)
        B = b_base.transpose(-1,-2) + b_bias.unsqueeze(-1) 
        ## B,L,K, ngroups->B,L,ngroups,K +  B,L,ngroups-> B,L,ngroups,1
        ## ===> B,L,ngroups,K
        C = c_base.transpose(-1,-2) + c_bias.unsqueeze(-1)

        if self.use_biscan:
            B_back = b_base.transpose(-1,-2) + b_bias_back.unsqueeze(-1)
            C_back = c_base.transpose(-1,-2) + c_bias_back.unsqueeze(-1)
        
        dt_base = self.dt_proj(dist) # adaptive dt
        dt = F.softplus(dt_base.transpose(-1,-2) + dt_bias.unsqueeze(-1) + self.dt_bias.reshape((1, 1, -1, 1)))  # (B, L, nheads)
        ## B, L, H, K +  B,L,H,1 +  
        if mask != None:
            if mask.dtype == torch.float32:
                dt = dt * mask.unsqueeze(2)
            else:
                dt[mask.unsqueeze(2).repeat(1, 1, self.nheads, 1)] = 0.0
        
        # 对序列长度进行 padding 到 chunk_size 的整倍数，避免反向阶段要求 (nchunks*chunk_size) 的断言失败
        L = x.shape[1]
        original_len = L
        target_len = math.ceil(L / self.chunk_size) * self.chunk_size
        if target_len > L:
            pad_len = target_len - L
            def pad_seq(t, dim1_size):
                pad_shape = list(t.shape)
                pad_shape[1] = dim1_size
                return torch.cat([t, t.new_zeros(pad_shape)], dim=1)

            # also pad z to match key length for gated norm
            z = pad_seq(z, pad_len)
            x = pad_seq(x, pad_len)
            if self.use_biscan:
                x_back = pad_seq(x_back, pad_len)
            dt = pad_seq(dt, pad_len)
            B = pad_seq(B, pad_len)
            C = pad_seq(C, pad_len)
            if self.use_biscan:
                B_back = pad_seq(B_back, pad_len)
                C_back = pad_seq(C_back, pad_len)

        # Ensure scan inputs are float32 to satisfy Triton kernel dtypes
        A = A.float(); B = B.float(); C = C.float(); dt = dt.float()
        if self.use_biscan:
            B_back = B_back.float(); C_back = C_back.float()

        # 3. Selective scan
        module_kwargs = {} if self.dt_limit == (0.0, float("inf")) else dict(dt_limit=self.dt_limit)
        module_kwargs["return_final_states"] = True
        
        key, last_states = self.scan(x, initial_states, dt, A, B, C, module_kwargs)

        if self.use_biscan:
            x_back = torch.flip(x_back, dims=[1])
            dt_back = torch.flip(dt, dims=[1])
            B_back = torch.flip(B_back, dims=[1])
            C_back = torch.flip(C_back, dims=[1])
            key_back, last_states_back = self.scan(x_back, initial_states, dt_back, A, B_back, C_back, module_kwargs)
            key_back = torch.flip(key_back, dims=[1])
            key = (key + key_back) / 2
            last_states = (last_states + last_states_back) / 2
        
        # remove padding to restore original sequence length
        if key.shape[1] != original_len:
            key = key[:, :original_len]
            if z.shape[1] != original_len:
                z = z[:, :original_len]
        
        # 3. Output processing
        key = rearrange(key, "b l h p -> b l (h p)")
        if z.dtype != key.dtype:
            z = z.to(key.dtype)
        key = self.key_norm(key, z)
        out_key = self.out_key_proj(key)
        last_states = rearrange(last_states, "b h p l -> b l (h p)")
        last_states = self.query_norm(last_states)
        out_query = self.out_query_proj(last_states)
        # 保持输出为 float32 以避免后续 LayerNorm / Linear dtype 不匹配
        if out_key.dtype != in_key.dtype:
            out_key = out_key.to(in_key.dtype)
        if out_query.dtype != in_query.dtype:
            out_query = out_query.to(in_query.dtype)
        return out_key, out_query

    def scan(self, x, initial_states, dt, A, B, C, module_kwargs):
        """
        Perform unidirectional or bidirectional scan
        Args:
            x: (B, L, D) - Input sequence
            initial_states: (B, K, D) - Initial states
            dt: (B, L, nheads) - Time steps
            A, B, C: Parameters for the scan
            module_kwargs: Additional parameters
        Returns: 
            y: (B, K, D) - Output sequence
            last_states: (B, K, D) - Final states
        """
        # 使用固定 self.chunk_size，并确保 x 已经 pad 到其整数倍，避免巨型单块导致 Triton autotune 极慢
        effective_chunk_size = self.chunk_size
        assert x.shape[1] % effective_chunk_size == 0, "Sequence length must be multiple of chunk_size after padding"
        y, last_states = ISSM_chunk_scan_combined(
            rearrange(x, "b l (h p) -> b l h p", p=self.headdim),
            dt,
            A,
            B,
            C,
            chunk_size=effective_chunk_size,
            D=self.D,
            z=None,
            initial_states=initial_states,
            **module_kwargs,
        )
        return y, last_states