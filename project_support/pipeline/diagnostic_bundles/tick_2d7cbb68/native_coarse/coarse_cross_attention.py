"""Projection-free point queries reading the small coarse semantic bank."""
import math
import torch

def coarse_readback(points,coarse,padding,heads=8,values=None):
    batch,length,channels=points.shape
    if channels%heads or coarse.shape[0]!=batch or coarse.shape[-1]!=channels:
        raise ValueError('Incompatible coarse bank and point channels')
    width=channels//heads
    keys=coarse.reshape(batch,-1,heads,width)
    queries=points.reshape(batch,length,heads,width)
    logits=torch.einsum('bnhd,bkhd->bhnk',queries,keys)/math.sqrt(width)
    weights=logits.softmax(-1)
    value=(coarse if values is None else values).reshape(batch,-1,heads,width)
    output=torch.einsum('bhnk,bkhd->bnhd',weights,value).reshape_as(points)
    return output.masked_fill(padding.unsqueeze(-1),0),weights
