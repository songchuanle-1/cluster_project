"""Reuse the exact outcome-blind roster program with a disjoint fixed slice."""
import ast
from datetime import datetime,timezone
import json
from ops import guard,save,evidence,tick,ROOT,OUT,CID,ssh

guard()
tree=ast.parse((OUT/"prepare_native.py").read_text(encoding="utf-8"))
program=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="program" for t in n.targets))
class ReplicationSlice(ast.NodeTransformer):
    slices=0
    assertions=0
    def visit_Subscript(self,node):
        if isinstance(node.value,ast.Name) and node.value.id=="ordered":
            assert isinstance(node.slice,ast.Slice) and node.slice.lower is None and node.slice.upper.value==8
            node.slice=ast.Slice(lower=ast.Constant(8),upper=ast.Constant(32),step=None);self.slices+=1
        return self.generic_visit(node)
    def visit_Assert(self,node):
        value=node.test
        if isinstance(value,ast.Compare) and isinstance(value.left,ast.Call) and isinstance(value.left.func,ast.Name) and value.left.func.id=="len" and isinstance(value.left.args[0],ast.Name) and value.left.args[0].id=="selected":
            assert value.comparators[0].value==8
            value.comparators[0]=ast.Constant(24);self.assertions+=1
        return self.generic_visit(node)
transform=ReplicationSlice();source=transform.visit(ast.parse(program));assert transform.slices==transform.assertions==1
program=ast.unparse(ast.fix_missing_locations(source))
cohort=ssh(program);save("replication_cohort_precheck.json",cohort)
old=tick.load(OUT/"cohort_resource_precheck.json")
assert cohort["annotation_sha256"]==old["annotation_sha256"] and len(cohort["selected"])==24
assert not {s["scene_id"] for s in cohort["selected"]}.intersection(s["scene_id"] for s in old["selected"])
assert not cohort["contexts"] and all(v=="acquired_and_released" for v in cohort["locks"].values())
manifest=tick.load(OUT/"content_manifest.json")
manifest.update(selected=cohort["selected"],producer_hashes={name:tick.digest(OUT/name) for name in ("native_content_replication.py","matched_control.py")})
save("replication_manifest.json",manifest)
work=tick.load(ROOT/"pipeline/research_work.json");candidate=next(c for c in work["candidates"] if c["id"]==CID)
assert candidate["stage"]=="validation"
candidate["evidence"].extend(evidence(OUT/name) for name in ("content_result.json","content_analysis.json","content_postcheck.json","replication_prereg.md","replication_cohort_precheck.json","replication_manifest.json","native_content_replication.py"))
candidate["next_action"]="Run preregistered next24outcome-blind disjoint TRAIN scenes,24full captures+96same-prefix suffixes; report8pilot/24replication separately and unchanged1e-6 controls. No model/admission."
guard();tick.save(ROOT/"pipeline/research_work.json",work)
print(json.dumps({"frozen_new_scenes":24,"expressions":sum(len(s["identities"]) for s in cohort["selected"]),"pilot_disjoint":True,"gpu":cohort["gpu"],"contexts":cohort["contexts"]},indent=2))
