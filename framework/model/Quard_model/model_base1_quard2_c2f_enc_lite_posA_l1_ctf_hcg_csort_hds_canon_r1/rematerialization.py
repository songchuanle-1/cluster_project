"""Rematerialize only pure pre-cluster encoder/decoder pairs."""
from functools import wraps
import torch
from torch.utils.checkpoint import checkpoint


def _wrap_forward(module):
    original = module.forward

    @wraps(original)
    def forward(*args, **kwargs):
        if not module.training or not torch.is_grad_enabled():
            return original(*args, **kwargs)

        def invoke(*values):
            return original(*values, **kwargs)

        return checkpoint(invoke, *args, use_reentrant=False,
                          preserve_rng_state=True)

    module.forward = forward


def install_prefix_rematerialization(decoder):
    if getattr(decoder, '_prefix_rematerialization_installed', False):
        raise RuntimeError('Prefix rematerialization is already installed.')
    indices = [i for i, layer in enumerate(decoder.encoder_layers)
               if not layer.use_cluster]
    if not indices or indices != list(range(len(indices))):
        raise ValueError('Expected a nonempty contiguous pure prefix.')
    if len(indices) == len(decoder.encoder_layers):
        raise ValueError('The cluster-bearing final layer must remain outside.')
    names = []
    for index in indices:
        _wrap_forward(decoder.encoder_layers[index])
        _wrap_forward(decoder.decoder_layers[index])
        names.extend(['encoder_layers.' + str(index),
                      'decoder_layers.' + str(index)])
    decoder._prefix_rematerialization_installed = True
    return names
