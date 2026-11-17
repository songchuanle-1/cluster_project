"""Pair exogenous FPS support without conditioning on learned query selection."""
from frozen_capture_contract_20260916 import strict_paired_summary
from hierarchical_partition_contract_20260916 import validate_hierarchical_row
from paired_capture_evaluation_20260916 import index_rows


def sampling_paired_summary(left, right, **kwargs):
    lhs, rhs = index_rows(left), index_rows(right)
    if lhs.keys() != rhs.keys():
        raise ValueError("Paired expression manifest differs")
    for key, row in lhs.items():
        other = rhs[key]
        for observation in (row, other):
            fps = observation.get("fps_superpoints")
            selected = observation.get("sampled_seed_indices")
            n = len(observation["original_superpoint_ids"])
            if not isinstance(fps, list) or not fps or any(
                    type(x) is not int or not 0 <= x < n for x in fps):
                raise ValueError("Missing or invalid FPS support")
            if not isinstance(selected, list) or len(selected) != len(observation["scores"]):
                raise ValueError("Missing query-to-FPS binding")
            if any(type(x) is not int or not 0 <= x < len(fps) for x in selected):
                raise ValueError("Invalid query-to-FPS index")
            validate_hierarchical_row(observation)
        if row["fps_superpoints"] != other["fps_superpoints"]:
            raise ValueError("Exogenous FPS support or order differs")
        if (row["hierarchical_partition_sha256"]
                != other["hierarchical_partition_sha256"]):
            raise ValueError("Exogenous hierarchical partition differs")
    result = strict_paired_summary(left, right, **kwargs)
    result["fps_support_verified"] = True
    result["hierarchical_partition_verified"] = True
    result["query_selection_conditioned"] = False
    result["limitations"] = [
        "Recorded FPS geometry does not certify all internal randomness.",
        "Learned sampled_seed_indices may differ: they are not a matching criterion.",
        "Native model/config binding and predefined sample remain required.",
        "Static checks are not native validation or evidence of mechanism efficacy."]
    return result
