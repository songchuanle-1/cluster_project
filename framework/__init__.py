import importlib
import os

### Quard
# Default model: lazily loaded only when auto-resolution fails
_DEFAULT_MODEL = 'framework.model.Quard_model.model_base1_quard2_c2f_enc_lite_posA_l1'

_network = None


def _get_default_network():
    global _network
    if _network is None:
        mod = importlib.import_module(_DEFAULT_MODEL)
        _network = mod.Network
    return _network


def resolve_network(config_path: str):
    """
    Auto-resolve Network class from YAML config filename.
    e.g. 'configs/Quard/model_base2_quard_bottleneck.yaml'
      → framework.model.Quard_model.model_base2_quard_bottleneck.Network

    变体独立性规则: 每个模型变体必须有独立的 model 包目录 (即使代码与父模型一致,
    仅 config 参数不同也要复制一份), 且 config basename 与 model 包名一一对应.
    这样 kill/PID/log 目录按 basename 天然区分, 不会互相冲突.

    Falls back to _DEFAULT_MODEL if resolution fails.
    """
    basename = os.path.splitext(os.path.basename(config_path))[0]
    module_path = f'framework.model.Quard_model.{basename}'
    try:
        mod = importlib.import_module(module_path)
        return mod.Network
    except (ImportError, AttributeError):
        return _get_default_network()
