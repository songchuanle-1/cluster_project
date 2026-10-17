from pathlib import Path
import sys

if (Path(sys.argv[0]).name == "train.py" and any(
        Path(arg).stem == Path(__file__).parent.name for arg in sys.argv[1:])):
    from .startup_guard import acquire
    acquire()

from .network import Network

__all__ = ["Network"]
