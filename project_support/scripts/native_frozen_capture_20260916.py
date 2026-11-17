"""Versioned M95 capture preserving native inputs and checkpoint identity."""
import argparse
from pathlib import Path

from frozen_capture_contract_20260916 import file_sha256, fingerprint
from native_endpoint_capture_20260916 import EndpointDataset, enrich_row
from native_support_capture_v2_20260916 import main


class FrozenDataset(EndpointDataset):
    checkpoint_sha256 = None

    def __getitem__(self, index):
        item, axes = super().__getitem__(index)
        identity = fingerprint(item)
        if not self.checkpoint_sha256:
            raise ValueError("Checkpoint identity must be frozen before capture")
        for axis in axes:
            axis.update(native_input_sha256=identity,
                        checkpoint_sha256=self.checkpoint_sha256)
        return item, axes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--checkpoint", required=True)
    args, _ = parser.parse_known_args()
    FrozenDataset.checkpoint_sha256 = file_sha256(args.checkpoint)
    directory = Path(__file__).parent
    sources = [directory / name for name in (
        "native_frozen_capture_20260916.py", "frozen_capture_contract_20260916.py",
        "hierarchical_partition_contract_20260916.py",
        "native_endpoint_capture_20260916.py", "native_support_capture_v2_20260916.py",
        "capture_support_20260916.py", "physical_mask_endpoints_20260916.py")]
    main(dataset_class=FrozenDataset, enrich_row=enrich_row, producer_files=sources)
