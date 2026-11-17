"""Bounded primary arXiv metadata search for boundary conditional assignment."""
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

queries = [
    'all:"recursive cardinality"',
    'all:"conditional Bernoulli" AND all:"segmentation"',
    'all:"segmentation" AND all:"cardinality" AND all:"loss"',
    'all:"boundary" AND all:"structured" AND all:"segmentation"',
    'all:"3D grounding" AND all:"boundary"',
]
ns={"a":"http://www.w3.org/2005/Atom"}
result=[]
for q in queries:
    url="https://export.arxiv.org/api/query?"+urllib.parse.urlencode(
        dict(search_query=q,start=0,max_results=6,sortBy="relevance"))
    try:
        raw=urllib.request.urlopen(url,timeout=35).read()
        tree=ET.fromstring(raw)
        entries=[{k:" ".join(e.find("a:"+k,ns).text.split())
                  for k in ("title","id","summary","published")}
                 for e in tree.findall("a:entry",ns)]
        result.append(dict(query=q,url=url,entries=entries))
        print(json.dumps(result[-1]),flush=True)
    except Exception as e:
        result.append(dict(query=q,url=url,error=repr(e)))
        print(repr(e),flush=True)
    time.sleep(3)
path=Path("D:/project/cluster_project/pipeline/reports/boundary_literature_20260914.json")
path.write_text(json.dumps(result,indent=2))
