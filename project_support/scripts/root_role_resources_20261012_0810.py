"""Use the existing uniform predict protocol for three clean-process targets."""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
STAGE = PIPE / "tmr_validation_20261012_0810"
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_tmr"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=("baseline", "champion", "target_role"))
    args = parser.parse_args()
    sys.path[:0] = [str(STAGE), str(ROOT / "scripts")]
    import pdc_predict_resource_protocol_20261009 as protocol
    if args.target == "target_role":
        static = json.loads((STAGE / "root_role_static_20261012_0810.json").read_text())
        package = STAGE / NAME
        digest = hashlib.sha256()
        for source in static["files"]:
            path = package / source["filename"]
            assert sha(path) == source["sha256"]
            relative, payload = source["filename"].encode("ascii"), path.read_bytes()
            digest.update(len(relative).to_bytes(4, "big"))
            digest.update(relative)
            digest.update(len(payload).to_bytes(8, "big"))
            digest.update(payload)
        package_hash = digest.hexdigest()
        protocol.TARGETS[args.target] = {
            "name": NAME,
            "config": "../pipeline/tmr_validation_20261012_0810/" + NAME + ".yaml",
            "config_sha256": static["config_sha256"],
            "model_source_sha256": package_hash,
        }
        original_hash = protocol._model_package_sha256
        protocol._model_package_sha256 = lambda root, name: (
            package_hash if name == NAME else original_hash(root, name))
        original_import = protocol.importlib.import_module

        def isolated_import(name, *other, **kwargs):
            if name != "framework.model.Quard_model." + NAME:
                return original_import(name, *other, **kwargs)
            spec = importlib.util.spec_from_file_location(
                "tmr_resource_validation", package / "__init__.py",
                submodule_search_locations=[str(package)])
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            return module

        protocol.importlib.import_module = isolated_import
    output = PIPE / ("root_role_resources_" + args.target + "_20261012_0810.json")
    protocol._measure_target(args.target, ROOT, "/data3/songcl/data/data_cluster", output)
    result = json.loads(output.read_text())
    print(json.dumps({
        "target": args.target, "output_sha256": sha(output),
        "result_keys": sorted(result),
        "metrics": result.get("metrics", result.get("measurement", {})),
    }), flush=True)


if __name__ == "__main__":
    main()
