"""N1b literature probe: hierarchical / part-based competitor sets for discrimination.

Read-only arXiv API queries, abstract-level screen. Writes a manifest.
No production code, dataset, checkpoint, queue or training change.
"""
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path("D:/project/cluster_project/pipeline/reports/litprobe_hierarchy_20260911-2307")
NS = {"a": "http://www.w3.org/2005/Atom"}
QUERIES = [
    'all:"hierarchical" AND all:"contrastive learning" AND all:"instance"',
    'all:"part-aware" AND all:"3D" AND all:"grounding"',
    'all:"point cloud" AND all:"hierarchical grouping" AND all:"discrimination"',
    'all:"3D visual grounding" AND all:"hierarchy"',
    'all:"hard negative" AND all:"3D" AND all:"grounding"',
    'all:"superpoint" AND all:"contrastive" AND all:"3D"',
]


def query(q, maxr=8):
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode(
        {"search_query": q, "start": 0, "max_results": maxr, "sortBy": "relevance"})
    raw = urllib.request.urlopen(url, timeout=30).read()
    root = ET.fromstring(raw)
    out = []
    for e in root.findall("a:entry", NS):
        out.append({
            "title": " ".join(e.find("a:title", NS).text.split()),
            "arxiv_id": e.find("a:id", NS).text.split("/abs/")[-1],
            "published": e.find("a:published", NS).text[:10],
            "summary": " ".join(e.find("a:summary", NS).text.split())[:700],
        })
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = {}
    for q in QUERIES:
        try:
            results[q] = query(q)
        except Exception as exc:
            results[q] = [{"error": repr(exc)}]
        time.sleep(3)
    (OUT / "arxiv_probe.json").write_text(
        json.dumps({"probe": "n1_hierarchy_litprobe", "queries": results}, indent=2),
        encoding="utf-8")
    for q, hits in results.items():
        print("###", q)
        for h in hits:
            if "error" in h:
                print("  ERR", h["error"])
            else:
                print(" -", h["published"], h["arxiv_id"], h["title"])


if __name__ == "__main__":
    main()
