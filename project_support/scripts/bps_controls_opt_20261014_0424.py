"""Run the unchanged matched controls in a clean optimized-package process."""
import os
from pathlib import Path

import bps_controls_20261014_0424 as controls
from bps_runtime_20261014_0424 import PIPE, TOKEN


class OutputPaths:
    def __truediv__(self, filename):
        if filename.startswith("bps_controls_current_" + TOKEN):
            filename = filename.replace("bps_controls_current_", "bps_controls_opt_", 1)
        return PIPE / filename


if __name__ == "__main__":
    os.environ["BPS_PACKAGE_STAGE"] = str(PIPE / ("bps_staging_" + TOKEN + "_v3"))
    controls.PIPE = OutputPaths()
    controls.main()
