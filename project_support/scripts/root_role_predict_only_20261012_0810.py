"""Native prediction invariance to the TRAIN-only role catalog."""
import hashlib
import importlib.util
import json
import logging
import os
from pathlib import Path
import sys

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPE = ROOT.parent / "pipeline"
STAGE = PIPE / "tmr_validation_20261012_0810"
NAME = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_tmr"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert os.environ["CUDA_VISIBLE_DEVICES"] == "7"
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT / "scripts"), str(ROOT), str(ROOT / "framework/lib")]
    import torch
    import gorilla
    from torch.utils.data import DataLoader
    from framework.dataset import build_dataset
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.4)
    manifest = json.loads((STAGE / "root_role_static_v2_20261012_0810.json").read_text())
    package = STAGE / NAME
    for record in manifest["files"]:
        assert sha(package / record["filename"]) == record["sha256"]
    config = STAGE / (NAME + ".yaml")
    assert sha(config) == manifest["config_sha256"]
    spec = importlib.util.spec_from_file_location(
        "tmr_predict_control", package / "__init__.py",
        submodule_search_locations=[str(package)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("tmr-controls"))
    model = module.Network(**cfg.model)
    checkpoint = PIPE / "scm_admission_20260914/best.pth"
    assert sha(checkpoint) == "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)["model"]
    for key in ("text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"):
        state.pop(key, None)
    model.load_state_dict(state, strict=True)
    model.cuda().eval()

    def batch():
        gorilla.set_random_seed(1999)
        loader = DataLoader(torch.utils.data.Subset(dataset, [8672]),
                            batch_size=1, shuffle=False, num_workers=0,
                            collate_fn=dataset.collate_fn)
        return next(iter(loader))

    native = batch()
    roles = model.target_mention_roles
    maps = native["dense_maps"]
    rebound, changed = roles.rebind(native["ann_ids"], native["scan_ids"],
                                   native["scenes_len"], native["object_idss"], maps)
    assert len(changed) == 1
    changed_index = changed[0]
    assert torch.equal(rebound[changed_index]["positive_map"][0] > 0,
                       torch.tensor([i in (2, 3) for i in range(256)]))
    wrong_ids = [list(v) for v in native["object_idss"]]
    wrong_ids[changed_index] = [-999]
    bypass, empty = roles.rebind(native["ann_ids"], native["scan_ids"],
                                native["scenes_len"], wrong_ids, maps)
    assert not empty and all(a is b for a, b in zip(bypass, maps))
    catalog = roles.catalog
    calls = []
    original_rebind = roles.rebind

    def count_calls(*args, **kwargs):
        calls.append(True)
        return original_rebind(*args, **kwargs)

    roles.rebind = count_calls
    with torch.no_grad():
        first = model(batch(), mode="predict")
        roles.catalog = {}
        second = model(batch(), mode="predict")
    roles.catalog = catalog
    assert not calls
    deltas, leaves = [], []

    def compare(left, right, path="prediction"):
        if torch.is_tensor(left):
            assert left.shape == right.shape
            assert bool(torch.isfinite(left).all()) and bool(torch.isfinite(right).all())
            delta = float((left.to(torch.float64) - right.to(torch.float64)).abs().max()) if left.numel() else 0.0
            deltas.append(delta)
            leaves.append(path)
        elif isinstance(left, dict):
            assert left.keys() == right.keys()
            for key in left:
                compare(left[key], right[key], path + "." + key)
        elif isinstance(left, (tuple, list)):
            assert len(left) == len(right)
            for index, (a, b) in enumerate(zip(left, right)):
                compare(a, b, path + "." + str(index))
        else:
            assert left == right

    compare(first, second)
    assert deltas and max(deltas) == 0.0
    result = {
        "contract": "target_role_native_predict_catalog_invariance_v1",
        "source_manifest": manifest, "checkpoint_sha256": sha(checkpoint),
        "script_sha256": sha(Path(__file__)), "seed": 1999,
        "native_group": 8672, "expression_count": len(native["ann_ids"]),
        "catalog_entries": len(catalog), "changed_index": changed_index,
        "literal_positive_tokens": [2, 3], "wrong_identity_bypass_exact": True,
        "prediction_rebind_calls": len(calls), "compared_tensor_fields": leaves,
        "prediction_max_delta": max(deltas), "admission": False,
        "limitations": "One frozen native batch; no trained efficacy or population identity certification.",
    }
    output = PIPE / "root_role_predict_controls_20261012_0810.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
