"""CPU native geometry equivariance and exact invocation-isolation controls."""
import argparse
import copy
from datetime import datetime, timezone
import importlib.util
import json
import logging
import os
from pathlib import Path
import socket
import sys

from bps_runtime_20261014_0424 import PIPE, ROOT, DATA, TOKEN, PREVIOUS, sha


def load_catalog_class(stage, name):
    source = stage / "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bps/between_support.py"
    spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.BetweenSupportCatalog


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    assert args.token == TOKEN and socket.gethostname() == "das"
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    import torch
    import gorilla
    from framework.dataset import build_dataset
    from bps_runtime_20261014_0424 import get_batch, fingerprint
    torch.set_num_threads(1)
    original_config = PIPE / "majority_erasure_original_config_20261012_0910.yaml"
    assert sha(original_config) == "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a"
    cfg = gorilla.Config.fromfile(str(original_config))
    cfg.data.train.data_root = str(DATA) + "/"
    gorilla.set_random_seed(1999)
    dataset = build_dataset(copy.deepcopy(cfg.data.train), logging.getLogger("bps-geometry"))
    catalog = PIPE / ("bps_catalog_" + PREVIOUS + ".json")
    catalog_sha = "9ddcddeff3629c50c50054a9eaadb0828f5dfcb8541defd16705341c0dc567f2"
    assert sha(catalog) == catalog_sha
    v3stage = PIPE / ("bps_staging_" + TOKEN + "_v3")
    v2stage = PIPE / ("bps_staging_" + PREVIOUS + "_v2")
    original = load_catalog_class(v2stage, "bps_geometry_original")(str(catalog), catalog_sha)
    optimized = load_catalog_class(v3stage, "bps_geometry_optimized")(str(catalog), catalog_sha)
    frozen = json.loads((PIPE / "between_pair_typed_66fa1e81aec94d5eb10265ea533669ac.manifest.json").read_text())["frozen"]
    cases = [[r["native_group"]] for r in frozen]
    cases += [[5743], [7787], [0], [0, 44], [0, 452]]
    rows = []
    def prepare(operator, batch, coords):
        return operator.prepare(batch["ann_ids"], batch["scan_ids"], batch["scenes_len"],
                                batch["object_idss"], batch["superpoints"], coords,
                                batch["batch_offsets"], batch["sp_ins_labels"])
    def max_cost_delta(left, right):
        assert len(left) == len(right)
        delta = 0.
        for a, b in zip(left, right):
            assert len(a["costs"]) == len(b["costs"])
            for x, y in zip(a["costs"], b["costs"]):
                assert x.shape == y.shape
                assert bool(torch.isfinite(x).all()) and bool(torch.isfinite(y).all())
                if x.numel():
                    delta = max(delta, float((x - y).abs().max()))
        return delta
    for groups in cases:
        batch = get_batch(torch, gorilla, dataset, groups)
        assert batch["coords_float"].device.type == "cpu"
        coords = batch["coords_float"].double()
        reference = prepare(optimized, batch, coords)
        readout = copy.deepcopy(optimized.last_readout)
        baseline_hash = fingerprint(reference)
        transforms = {"reflection": coords * coords.new_tensor([-1., 1., 1.]),
                      "permutation": coords[:, [2, 0, 1]],
                      "uniform_scale": coords * 2.,
                      "translation": coords + coords.new_tensor([1., -2., 4.])}
        for name, changed in transforms.items():
            full = prepare(original, batch, changed)
            fast = prepare(optimized, batch, changed)
            transformed_readout_exact = original.last_readout == optimized.last_readout == readout
            implementation_delta = max_cost_delta(full, fast)
            invariant_delta = max_cost_delta(reference, fast)
            restored = prepare(optimized, batch, coords)
            restoration_exact = baseline_hash == fingerprint(restored) and optimized.last_readout == readout
            row = {"groups": groups, "transform": name, "input_sha256": fingerprint(batch),
                   "implementation_max_abs_delta": implementation_delta,
                   "invariance_max_abs_delta": invariant_delta,
                   "readout_exact": transformed_readout_exact,
                   "restoration_exact": restoration_exact,
                   "implementation_pass1e6": implementation_delta <= 1e-6,
                   "invariance_pass1e6": invariant_delta <= 1e-6}
            rows.append(row)
        print(json.dumps({"groups": groups, "implementation_pass": all(r["implementation_pass1e6"] for r in rows[-4:]),
                          "invariance_max_delta": max(r["invariance_max_abs_delta"] for r in rows[-4:]),
                          "restoration_exact": all(r["restoration_exact"] for r in rows[-4:])}), flush=True)
    result = {"tick_token": TOKEN, "observed_at": datetime.now(timezone.utc).isoformat(),
              "script_sha256": sha(Path(__file__)), "rows": rows, "groups": len(cases),
              "source_manifest_sha256": sha(v3stage / "source_manifest.json"),
              "catalog_sha256": catalog_sha, "optimizer_steps": 0, "cuda_forward_count": 0,
              "scope": "Native CPU geometry transformation and cross-invocation cache isolation, not full-model invariance or efficacy."}
    output = PIPE / ("bps_geometry_" + TOKEN + ".json")
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"result": str(output), "sha256": sha(output),
                      "all_pass": all(r["implementation_pass1e6"] and r["invariance_pass1e6"]
                                      and r["readout_exact"] and r["restoration_exact"] for r in rows)}), flush=True)


if __name__ == "__main__":
    main()
