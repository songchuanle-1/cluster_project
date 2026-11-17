"""Diagnostic-only fixed backbone/support matched parameter update on server4."""
import ast
from pathlib import Path

base = Path("/tmp/component_full_loss_20260915.py")
text = base.read_text()
text = text.replace("/data3/songcl/Project/Cluster_project/Cluster",
                    "/data/songcl/Project/Cluster_project/Cluster")
text = text.replace("/data3/songcl/data/data_cluster/", "/home/songcl/data/data/")
text = text.replace(
    "/data3/songcl/Project/Cluster_project/pipeline/scm_admission_20260914/best.pth",
    "/data/songcl/Project/Cluster_project/Cluster_checkpoints/"
    "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/20260815_101011/best.pth")
text = text.replace("set_per_process_memory_fraction(.15)",
                    "set_per_process_memory_fraction(.28)")
base.write_text(text)
source = Path("/tmp/component_parameter_step_20260915.py")
tree = ast.parse(source.read_text())
injection = '''
native_extract = model.extract_feat
replay = {}
def extract(*args, **kwargs):
    if "features" not in replay:
        with torch.no_grad():
            replay["features"] = native_extract(*args, **kwargs).detach().clone()
    return replay["features"].clone()
model.extract_feat = extract
def fixed_sampling(module, args, result):
    if "sampling" not in replay:
        replay["sampling"] = result[0].detach().clone()
    return replay["sampling"].clone(), result[1]
sampling_handle = model.dec.sampling_module.register_forward_hook(fixed_sampling)
'''
for node in tree.body:
    if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "out" for t in node.targets):
        node.value = ast.parse('Path("/tmp/component_replay_server4_20260915")', mode="eval").body
    if isinstance(node, ast.For) and isinstance(node.target, ast.Tuple):
        if any(isinstance(t, ast.Name) and t.id == "step" for t in node.target.elts):
            node.body.insert(0, ast.parse("replay.clear()").body[0])
            # Keep original batch IDs; use the predeclared disconnected batch1.
            node.body.insert(0, ast.parse("if step != 1: continue").body[0])
            index = tree.body.index(node)
            tree.body[index:index] = ast.parse(injection).body
            break
ast.fix_missing_locations(tree)
exec(compile(tree, str(source), "exec"), {"__name__": "__main__", "__file__": __file__})
