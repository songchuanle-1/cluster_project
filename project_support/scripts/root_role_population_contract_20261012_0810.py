"""CPU native frozen-population role-map contract, no optimizer or inference."""
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
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    sys.path[:0] = [str(ROOT), str(ROOT / "framework/lib")]
    import torch
    import gorilla
    from torch.utils.data import DataLoader
    from framework.dataset import build_dataset
    torch.set_num_threads(1)
    manifest_path = PIPE / "point_detail_population_20261009/result.manifest.json"
    assert sha(manifest_path) == "d2bb6af4286e3587b82dd0745638cfe8868170abf07f6496dda56576d0960932"
    manifest = json.loads(manifest_path.read_text())
    groups = list(dict.fromkeys(int(row["native_group"]) for row in manifest))
    static = json.loads((STAGE / "root_role_static_v2_20261012_0810.json").read_text())
    source = STAGE / NAME / "mention_roles.py"
    record = next(row for row in static["files"] if row["filename"] == source.name)
    assert sha(source) == record["sha256"]
    spec = importlib.util.spec_from_file_location("tmr_population_roles", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    roles = module.TargetMentionRoles("/data3/songcl/data/data_cluster")
    config = STAGE / (NAME + ".yaml")
    assert sha(config) == static["config_sha256"]
    cfg = gorilla.Config.fromfile(str(config))
    cfg.data.train.data_root = "/data3/songcl/data/data_cluster/"
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("tmr-contract"))
    loader = DataLoader(torch.utils.data.Subset(dataset, groups),
                        batch_size=1, num_workers=0, shuffle=False,
                        collate_fn=dataset.collate_fn)
    rows, count, unchanged = [], 0, 0
    for group, batch in zip(groups, loader):
        original = batch["dense_maps"]
        saved = [{key: value.clone() for key, value in item.items()} for item in original]
        rewritten, changed = roles.rebind(
            batch["ann_ids"], batch["scan_ids"], batch["scenes_len"],
            batch["object_idss"], original)
        for index, (old, new) in enumerate(zip(original, rewritten)):
            assert old.keys() == new.keys()
            assert all(torch.equal(value, saved[index][key]) for key, value in old.items())
            if index not in changed:
                assert old is new
                unchanged += 1
                continue
            assert all(torch.equal(value, new[key]) for key, value in old.items()
                       if key not in ("positive_map", "other_entity_map"))
            assert abs(float(new["positive_map"][0].sum()) - 1.0) < 1e-6
            expected = (old["other_entity_map"] + old["positive_map"]).clamp(0, 1)
            expected = expected.masked_fill(new["positive_map"] > 0, 0)
            assert torch.equal(new["other_entity_map"], expected)
            rows.append({
                "scene": batch["scan_ids"][0], "ann_id": int(batch["ann_ids"][index]),
                "native_group": group, "object_ids": list(map(int, batch["object_idss"][index])),
                "old_tokens": torch.where(old["positive_map"][0] > 0)[0].tolist(),
                "new_tokens": torch.where(new["positive_map"][0] > 0)[0].tolist(),
            })
        count += len(original)
    result = {
        "contract": "tmr_native_population_bypass_v1", "script_sha256": sha(Path(__file__)),
        "manifest_sha256": sha(manifest_path), "mention_roles_sha256": sha(source),
        "native_groups": len(groups), "expressions": count,
        "changed": rows, "unchanged_exact": unchanged,
        "all_source_maps_unmodified": True, "other_role_formula_exact": True,
        "other_map_keys_unchanged": True, "seed": 1999, "optimizer_steps": 0,
        "limits": "Implementation effect on fixed TRAIN cohort, not population identity quality or trained efficacy.",
    }
    output = PIPE / "root_role_population_contract_20261012_0810.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
