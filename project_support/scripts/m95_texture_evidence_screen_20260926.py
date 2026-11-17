"""Frozen vocabulary specialization of the exact shape-screen contract."""
import argparse
import json
from pathlib import Path

import m95_shape_evidence_screen_20260926 as screen

TEXTURE = frozenset(("striped", "stripe", "stripes", "patterned", "pattern",
                     "plaid", "dotted", "polka", "spotted", "speckled",
                     "checkered", "checked", "textured", "floral"))


def main():
    p = argparse.ArgumentParser()
    for name in ("capture", "source", "graphs", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Output exists")
    for name, expected in (("capture", screen.CAPTURE_SHA),
                           ("source", screen.SOURCE_SHA),
                           ("graphs", screen.GRAPH_SHA)):
        if screen.sha(getattr(a, name)) != expected:
            raise ValueError("Frozen input differs: " + name)
    screen.WORDS = TEXTURE
    result = screen.analyze(
        json.loads(a.capture.read_text(encoding="utf-8")),
        json.loads(a.source.read_text(encoding="utf-8")),
        json.loads(a.graphs.read_text(encoding="utf-8")))
    result.update(contract="m95_texture_evidence_screen_v1",
                  admission=False, capture_sha256=screen.CAPTURE_SHA,
                  source_sha256=screen.SOURCE_SHA,
                  graph_sha256=screen.GRAPH_SHA,
                  vocabulary=sorted(TEXTURE))
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
