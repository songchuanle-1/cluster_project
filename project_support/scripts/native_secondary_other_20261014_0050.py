"""Secondary/OTHER direct native directions, unchanged full frozen cohort."""
import ast
import hashlib
from pathlib import Path

SOURCE = Path("/data3/songcl/Project/Cluster_project/pipeline/"
              "native_role_direction_v2_20261014_0010.py")
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == (
    "c5a9c1157421bd9cc386a2da160ac1cf0ae376948ddff5b7f0c6808be690d749")
module = ast.parse(SOURCE.read_text())
overlaps = 0
for node in ast.walk(module):
    if (isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "overlap" for target in node.targets)):
        node.value = ast.parse(
            "((target['modify_positive_map'][ti]>0) | (target['pron_positive_map'][ti]>0)"
            " | (target['rel_positive_map'][ti]>0)) & (target['other_entity_map'][ti]>0)",
            mode="eval").body
        overlaps += 1
    if isinstance(node, ast.Dict):
        for index, key in enumerate(node.keys):
            if isinstance(key, ast.Constant) and key.value == "relation_other":
                key.value = "secondary_other"
                node.values[index] = ast.parse(
                    "((modifier>0) | (pronoun>0) | (relation>0)) & (other>0)",
                    mode="eval").body
            if isinstance(key, ast.Constant) and key.value == "d_loss_d_logit":
                node.keys.append(ast.Constant(value="role_mass"))
                node.values.append(ast.parse(
                    "{'modifier': float(modifier[token]), 'pronoun': float(pronoun[token]),"
                    " 'relation': float(relation[token]), 'other': float(other[token])}",
                    mode="eval").body)
                break
    if (isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
            and any(isinstance(value, ast.Constant) and value.value == "remove_relation_overlap"
                    for value in node.test.comparators)):
        node.body[:0] = ast.parse(
            "target['modify_positive_map'][ti, overlap] = 0\n"
            "target['pron_positive_map'][ti, overlap] = 0").body
assert overlaps == 1
for node in ast.walk(module):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        node.value = node.value.replace("native_role_direction_v2_", "native_secondary_other_")
        if node.value == "remove_other_overlap":
            node.value = "remove_other_secondary_overlap"
        elif node.value == "remove_relation_overlap":
            node.value = "remove_secondary_overlap"
namespace = {"__name__": "__main__", "__file__": __file__}
exec(compile(ast.fix_missing_locations(module), str(SOURCE), "exec"), namespace)
