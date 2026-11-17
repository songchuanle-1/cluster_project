"""Frozen TRAIN grouping-language incidence, distinct from region/state."""
import argparse
import json
from pathlib import Path

from m95_region_language_screen_20260926 import (
    MANIFEST_SHA, OUTCOME_SHA, SOURCE_SHA, analyze, sha,
)

GROUP_WORDS = frozenset(("row", "line", "stack", "stacked", "group", "pair"))


def main():
    p = argparse.ArgumentParser()
    for name in ("manifest", "outcomes", "source", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Output exists")
    for name, expected in (("manifest", MANIFEST_SHA),
                           ("outcomes", OUTCOME_SHA), ("source", SOURCE_SHA)):
        if sha(getattr(a, name)) != expected:
            raise ValueError(name + " hash differs")
    result = analyze(
        json.loads(a.manifest.read_text(encoding="utf-8")),
        json.loads(a.outcomes.read_text(encoding="utf-8")),
        json.loads(a.source.read_text(encoding="utf-8")),
        GROUP_WORDS,
    )
    result.update(contract="m95_group_topology_screen_v1",
                  manifest_sha256=MANIFEST_SHA, outcome_sha256=OUTCOME_SHA,
                  source_sha256=SOURCE_SHA, admission=False)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
