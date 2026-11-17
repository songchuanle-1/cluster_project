"""Identity-safe description attribution for shuffled native scene batches."""


def manifest_index(manifest):
    index = {}
    for group in manifest:
        for row in group["selected"]:
            key = (group["scene"], int(row["ann_id"]))
            if key in index:
                raise ValueError(f"Duplicate annotation identity: {key}")
            index[key] = (int(row["object_id"]), row["description"])
    return index


def attach_description(row, index):
    key = (row["scene"], int(row["ann_id"]))
    target, text = index[key]
    if tuple(map(int, row["target_ids"])) != (target,):
        raise ValueError(f"Target mismatch: {key}")
    return dict(row, utterance=text)


def same_target_donors(object_ids, scene_lengths):
    """Cyclic diagnostic donors within each augmentation group; singletons stay."""
    donors = list(range(len(object_ids)))
    offset = 0
    for length in scene_lengths:
        length = int(length)
        if length <= 0 or offset + length > len(donors):
            raise ValueError("Invalid scene segment")
        groups = {}
        for i in range(offset, offset + length):
            target = tuple(sorted(map(int, object_ids[i])))
            if len(target) == 1:
                groups.setdefault(target, []).append(i)
        for members in groups.values():
            for i, j in zip(members, members[1:] + members[:1]):
                donors[i] = j
        offset += length
    if offset != len(donors):
        raise ValueError("Scene lengths do not cover expressions")
    return donors
