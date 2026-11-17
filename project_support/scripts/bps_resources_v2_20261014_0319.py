"""Fresh clean-process targets using the existing uniform predict protocol."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
TOKEN = "1d59938f077948578e91e2cf34fc9d53"
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    parser.add_argument("--target", required=True, choices=("baseline", "champion", "candidate"))
    args = parser.parse_args()
    assert args.token == TOKEN
    stage = PIPE / ("bps_staging_" + args.token + "_v2")
    protocol_path = stage / "pdc_predict_resource_protocol_20261009.py"
    assert sha(protocol_path) == "10b2a09ff117352717d04110432c5d181632b3aebbd8e792eed9f9e69b5bfb76"
    sys.path[:0] = [str(stage), str(ROOT), str(ROOT / "framework/lib")]
    import pdc_predict_resource_protocol_20261009 as protocol
    if args.target == "candidate":
        static = json.loads((stage / "source_manifest.json").read_text())
        package = stage / NAME
        digest = hashlib.sha256()
        for filename, expected in sorted(static["package"].items()):
            path = package / filename
            assert sha(path) == expected
            relative, payload = filename.encode("ascii"), path.read_bytes()
            digest.update(len(relative).to_bytes(4, "big"))
            digest.update(relative)
            digest.update(len(payload).to_bytes(8, "big"))
            digest.update(payload)
        package_hash = digest.hexdigest()
        config = stage / (NAME + ".yaml")
        assert sha(config) == static["config_sha256"]
        protocol.TARGETS["candidate"] = {
            "name": NAME, "config": str(config),
            "config_sha256": static["config_sha256"],
            "model_source_sha256": package_hash}
        original_hash = protocol._model_package_sha256
        protocol._model_package_sha256 = lambda root, name: (
            package_hash if name == NAME else original_hash(root, name))
        original_import = protocol.importlib.import_module
        def isolated_import(name, *other, **kwargs):
            if name != "framework.model.Quard_model." + NAME:
                return original_import(name, *other, **kwargs)
            spec = importlib.util.spec_from_file_location(
                "bps_resource_validation", package / "__init__.py",
                submodule_search_locations=[str(package)])
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            return module
        protocol.importlib.import_module = isolated_import
    output = PIPE / ("bps_resources_v2_" + args.target + "_" + args.token + ".json")
    protocol._measure_target(args.target, ROOT, "/data3/songcl/data/data_cluster", output)
    result = json.loads(output.read_text())
    print(json.dumps({"result": str(output), "sha256": sha(output),
                      "target": args.target, "metrics": {key: result["resources"][key] for key in
                          ("flops_g", "params", "latency_ms_median", "latency_ms_p90", "peak_allocated_mib")},
                      "scope": "Uniform shared-GPU measurement, not exclusive speed or billing."}), flush=True)


if __name__ == "__main__":
    main()
