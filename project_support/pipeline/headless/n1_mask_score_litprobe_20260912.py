"""N1 literature probe for mask-conditioned candidate scoring.

Read-only arXiv API queries. The output is an abstract-level screening
artifact, not a novelty approval.
"""
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


OUT = Path(
    "D:/project/cluster_project/pipeline/reports/"
    "litprobe_mask_score_20260912-0510"
)
NS = {"a": "http://www.w3.org/2005/Atom"}
QUERIES = [
    'all:"3D visual grounding" AND all:"mask-aware" AND all:"ranking"',
    'all:"3D visual grounding" AND all:"mask scoring"',
    'all:"proposal ranking" AND all:"mask quality" AND all:"instance segmentation"',
    'all:"instance segmentation" AND all:"mask scoring"',
    'all:"3D instance segmentation" AND all:"score refinement"',
    'all:"visual grounding" AND all:"mask-conditioned"',
]


def query(search_query, max_results=8):
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(
        {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
        }
    )
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "cluster-project-n1-literature-probe/1.0 "
                "(read-only research diagnostic)"
            )
        },
    )
    raw = urllib.request.urlopen(request, timeout=45).read()
    root = ET.fromstring(raw)
    results = []
    for entry in root.findall("a:entry", NS):
        results.append(
            {
                "title": " ".join(entry.find("a:title", NS).text.split()),
                "arxiv_id": entry.find("a:id", NS).text.split("/abs/")[-1],
                "published": entry.find("a:published", NS).text[:10],
                "summary": " ".join(
                    entry.find("a:summary", NS).text.split()
                )[:900],
            }
        )
    return results


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = {}
    for search_query in QUERIES:
        for attempt in range(3):
            try:
                results[search_query] = query(search_query)
                break
            except Exception as exc:  # Network failures are recorded as gaps.
                if attempt == 2:
                    results[search_query] = [{"error": repr(exc)}]
                else:
                    time.sleep(5 * (attempt + 1))
        time.sleep(3)

    payload = {
        "probe": "n1_mask_score_litprobe",
        "created": "2026-09-12T05:10:00+08:00",
        "queries": results,
    }
    (OUT / "arxiv_probe.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    for search_query, hits in results.items():
        print("###", search_query)
        for hit in hits:
            if "error" in hit:
                print("  ERR", hit["error"])
            else:
                print(" -", hit["published"], hit["arxiv_id"], hit["title"])


if __name__ == "__main__":
    main()
