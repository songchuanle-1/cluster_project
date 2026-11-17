"""Frozen TRAIN explicit-state incidence, separate from room-region language."""
import argparse
import json
from pathlib import Path

from m95_region_language_screen_20260926 import (
    MANIFEST_SHA, OUTCOME_SHA, SOURCE_SHA, analyze, sha,
)

STATE_WORDS = frozenset(("open", "opened", "closed", "empty", "full"))


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
        STATE_WORDS,
    )
    result.update(contract="m95_object_state_screen_v1",
                  manifest_sha256=MANIFEST_SHA, outcome_sha256=OUTCOME_SHA,
                  source_sha256=SOURCE_SHA, admission=False)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
