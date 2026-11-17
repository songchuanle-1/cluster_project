"""Run the frozen relation diagnostic with the current owning token."""
import argparse
import hashlib
from pathlib import Path
import runpy

parser = argparse.ArgumentParser()
parser.add_argument("--token", required=True)
options = parser.parse_args()
source = Path("/data3/songcl/Project/Cluster_project/pipeline/"
              "relation_gradient_native_20261013_0707.py")
assert hashlib.sha256(source.read_bytes()).hexdigest() == (
    "63e9d86ae227ef82a84152b9fdca77aa886b6f2860e9cd781acb84dbdb320381")
namespace = runpy.run_path(str(source), run_name="frozen_relation_diagnostic")
namespace["main"].__globals__["TOKEN"] = options.token
namespace["main"]()
