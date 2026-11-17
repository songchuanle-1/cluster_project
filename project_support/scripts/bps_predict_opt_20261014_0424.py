"""Unchanged predict measurement, with explicitly rebound package/output paths."""
from pathlib import Path

import bps_resources_v2_20261014_0319 as reference

TOKEN = "c9de23ffb1804f1eaa81cf54b94b9d6a"
PIPE = Path("/data3/songcl/Project/Cluster_project/pipeline")


class CurrentPaths:
    def __truediv__(self, filename):
        if filename == "bps_staging_" + TOKEN + "_v2":
            filename = "bps_staging_" + TOKEN + "_v3"
        elif filename.startswith("bps_resources_v2_"):
            filename = filename.replace("bps_resources_v2_", "bps_resources_v3_", 1)
        return PIPE / filename


if __name__ == "__main__":
    reference.TOKEN = TOKEN
    reference.PIPE = CurrentPaths()
    reference.main()
