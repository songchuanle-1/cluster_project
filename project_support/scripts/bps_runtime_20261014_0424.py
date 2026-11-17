"""Read-only native setup with a fresh tick identity and immutable inputs."""
import importlib.util
import json
import os
from pathlib import Path

from bps_native_v2_20261014_0319 import (
    PIPE, ROOT, DATA, NAME, fingerprint, get_batch, parameters, sha)
from bps_native_v2_20261014_0319 import setup as previous_setup

TOKEN = "c9de23ffb1804f1eaa81cf54b94b9d6a"
PREVIOUS = "1d59938f077948578e91e2cf34fc9d53"


def setup(token):
    assert token == TOKEN
    alternate = os.environ.get("BPS_PACKAGE_STAGE")
    if not alternate:
        return previous_setup(PREVIOUS)
    import bps_native_v2_20261014_0319 as original
    original_root = original.PIPE
    class StagePath:
        def __truediv__(self, value):
            if value == "bps_staging_" + PREVIOUS + "_v2":
                return Path(alternate)
            return original_root / value
    original.PIPE = StagePath()
    try:
        return previous_setup(PREVIOUS)
    finally:
        original.PIPE = original_root
