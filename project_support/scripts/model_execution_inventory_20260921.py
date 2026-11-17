"""Static model-side requirements for the existing saved diagnostic, not a gate."""
import ast
import hashlib
from pathlib import Path

from native_geometry_runtime_20260919 import MODEL_CLASS
from saved_dependency_inventory_20260921 import source_requirements


PACKAGE = "framework/model/Quard_model/" + MODEL_CLASS
SOURCES = tuple(PACKAGE + "/" + name for name in (
    "__init__.py", "network.py", "backbone.py", "dec.py", "hier_postprocess.py",
    "loss.py", "sample_model.py")) + (
    "framework/utils/__init__.py", "framework/torch/nn/__init__.py")
CONFIG = "configs/Quard/ctf_hcg_csort/" + MODEL_CLASS + ".yaml"
BOUNDARY_SOURCES = tuple("framework/utils/" + name + ".py" for name in (
    "checkpoint", "logger", "mask_encoder", "structure", "utils", "meters", "dist"
)) + tuple("framework/torch/nn/" + name + ".py" for name in (
    "modules/__init__", "modules/module", "modules/linear", "modules/activation",
    "modules/lazy", "functional", "parameter", "init", "utils/__init__"
)) + ("framework/torch/utils/hooks.py",)


def boundary_inventory(root):
    """Expand only explicit imports from the previous model inventory."""
    root = Path(root).absolute()
    records = []
    for name in BOUNDARY_SOURCES:
        raw = checked_bytes(root / name)
        records.append(dict(
            path=name, sha256=hashlib.sha256(raw).hexdigest(),
            **source_requirements(raw, name)))
    for row in records:
        if hashlib.sha256(checked_bytes(root / row["path"])).hexdigest() != row["sha256"]:
            raise ValueError("Boundary source changed during audit")
    return dict(
        sources=records,
        absolute_import_roots=sorted({
            row["module"].split(".")[0] for source in records
            for row in source["imports"] if not row["level"] and row["module"]}),
        pointnet2=dict(
            imported_module="pointnet2.pointnet2_utils",
            inspected_paths=[
                dict(path=name, exists=(root / name).exists())
                for name in ("lib/pointnet2/pointnet2_utils.py", "lib/pointnet2/__init__.py")],
            actual_loaded_path_verified=False),
        transitive_closure_complete=False, native_environment_verified=False,
        limitations=[
            "Seventeen explicit dependency files, not exhaustive import closure.",
            "Vendored framework.torch uses private Torch APIs; ABI compatibility unverified.",
            "Missing local PointNet2 paths do not prove the host lacks an installed package.",
            "Remaining relative imports, installed distributions and shared libraries "
            "require separate pinned resolution on the authorized host."])


def checked_bytes(path):
    if (path.is_symlink() or any(p.is_symlink() for p in path.parents)
            or not path.is_file()):
        raise ValueError("Missing or redirected model audit source: " + str(path))
    return path.read_bytes()


def inventory(root):
    """Read nine explicit sources and one config without importing model code."""
    root = Path(root).absolute()
    records = []
    for name in SOURCES:
        raw = checked_bytes(root / name)
        parsed = source_requirements(raw, name)
        calls = []
        for node in ast.walk(ast.parse(raw, filename=name)):
            if isinstance(node, ast.Call):
                function = ast.unparse(node.func)
                if function.endswith((".from_pretrained", ".cuda", ".load_state_dict")):
                    calls.append(dict(line=node.lineno, expression=ast.unparse(node),
                                      runtime_reachability_verified=False))
        records.append(dict(path=name, sha256=hashlib.sha256(raw).hexdigest(),
                            calls=calls, **parsed))
    config = dict(path=CONFIG, sha256=hashlib.sha256(
        checked_bytes(root / CONFIG)).hexdigest())
    for row in records + [config]:
        if hashlib.sha256(checked_bytes(root / row["path"])).hexdigest() != row["sha256"]:
            raise ValueError("Model audit source changed")
    packages = sorted({
        row["module"].split(".")[0] for source in records for row in source["imports"]
        if not row["level"] and row["module"]
    })
    return dict(
        contract="saved-model-static-requirements-v1", sources=records, config=config,
        absolute_import_roots=packages,
        constructor_requirements=[
            "Network constructs RobertaModel.from_pretrained(data_root/roberta-base) "
            "before loading the full M95 checkpoint; tokenizer files alone are insufficient.",
            "Verify actual local model config and weight files selected by the installed "
            "Transformers loader, including any index/shards; no guessed filename approval.",
            "Preserve original Network constructor and strict checkpoint load; do not replace "
            "from_pretrained with from_config merely to bypass a missing asset.",
            "Original saved driver removes only position_ids and token_type_ids buffers "
            "before strict model state loading; compare actual keys/shapes/dtypes on host.",
            "The diagnostic loads archived M95 best.pth, not train.pretrain backbone "
            "or M197 last.pth. M197 recovery is a separate optimizer/epoch contract."],
        dependency_requirements=[
            "Add spconv and pointnet2 to the existing CPU collation inventory.",
            "Resolve loaded pointgroup_ops, pointnet2, torch_scatter and spconv "
            "native binaries; verify Python/Torch/CUDA ABI and GPU execution on server-4.",
            "framework.utils and framework.torch imports leave the bound model package. "
            "Resolve and hash their actual transitive sources before model import.",
            "Direct AST imports do not establish installed distributions or runtime reachability."],
        execution_validator_contract=[
            dict(stage="before_deserialization", required=[
                "Observe Linux server-4 interface/user/project_cluster interpreter directly.",
                "Verify goal and SERVERS allocation, exact imported sources and destination bytes.",
                "Verify saved receipt/full31/indices and trusted checkpoint provenance.",
                "Verify offline model assets and the actual dependency/native extension inventory."]),
            dict(stage="before_model_allocation", required=[
                "Fresh dedicated child exposes only selected physical GPU0 or GPU1 as logical0.",
                "Map device UUID to physical allocation; default-device cuda calls require logical0.",
                "Hold coordinated slot through synchronization and model teardown.",
                "Use existing check_server4_capacity with real fresh observations and measured "
                "memory requirement; never copy legacy GPU7 fraction0.15.",
                "CPU validate_runtime requires CUDA hidden and is not a GPU validator."]),
            dict(stage="after_capture", required=[
                "Synchronize GPU and verify finite native losses and exact requested item count.",
                "Rehash sources, input receipts and checkpoint; publish no success on drift.",
                "No training admission from eval/no_grad capture: native backward, matched "
                "resources and scientific diagnosis remain separate gates."])],
        native_environment_verified=False, native_execution_completed=False,
        production_execution_validator_implemented=False, admission=False,
        limitations=[
            "Nine sources and one config only; no transitive dependency closure.",
            "AST includes dead branches and __main__ examples; calls are evidence, not traces.",
            "No checkpoint deserialization, native packages, data, GPU or remote assets inspected.",
            "This contract specifies checks but implements no runtime authorization."])


def import_phase_events(raw, filename):
    """Separate eager definition expressions from deferred bodies, without execution."""
    events = []

    class Visitor(ast.NodeVisitor):
        phase = "import_time_possible"

        def record(self, node, kind, expression):
            events.append(dict(line=node.lineno, column=node.col_offset,
                               phase=self.phase, kind=kind, expression=expression))

        def visit_Import(self, node):
            self.record(node, "import", ast.unparse(node))

        visit_ImportFrom = visit_Import

        def visit_Call(self, node):
            self.record(node, "call", ast.unparse(node.func))
            self.generic_visit(node)

        def deferred(self, nodes):
            old = self.phase
            self.phase = "deferred_body"
            for node in nodes:
                self.visit(node)
            self.phase = old

        def visit_FunctionDef(self, node):
            # Defaults, annotations and decorators can run while defining a
            # function. The body itself is not traversed as import-time code.
            for decorator in node.decorator_list:
                self.record(decorator, "decorator_application", ast.unparse(decorator))
                self.visit(decorator)
            self.visit(node.args)
            if node.returns is not None:
                self.visit(node.returns)
            for parameter in getattr(node, "type_params", []):
                self.visit(parameter)
            self.deferred(node.body)

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Lambda(self, node):
            self.visit(node.args)
            self.deferred([node.body])

        def visit_ClassDef(self, node):
            for decorator in node.decorator_list:
                self.record(decorator, "decorator_application", ast.unparse(decorator))
                self.visit(decorator)
            for child in [*node.bases, *node.keywords,
                          *getattr(node, "type_params", []), *node.body]:
                self.visit(child)

        def visit_GeneratorExp(self, node):
            # Only the outermost iterable is evaluated when creating a generator.
            self.visit(node.generators[0].iter)
            remaining = [node.elt, node.generators[0].target,
                         *node.generators[0].ifs, *node.generators[1:]]
            self.deferred(remaining)

    Visitor().visit(ast.parse(raw, filename=filename))
    return sorted(events, key=lambda row: (row["line"], row["column"], row["kind"]))


def import_execution_audit(root):
    """Audit the existing explicit manifests; do not resolve or import packages."""
    from saved_dependency_inventory_20260921 import inventory as dataset_inventory

    root = Path(root).absolute()
    manifests = [dataset_inventory(root), inventory(root), boundary_inventory(root)]
    expected = {}
    for manifest in manifests:
        for row in manifest["sources"]:
            if row["path"] in expected and expected[row["path"]] != row["sha256"]:
                raise ValueError("Inconsistent import source hashes")
            expected[row["path"]] = row["sha256"]
    records = []
    for name, sha256 in expected.items():
        raw = checked_bytes(root / name)
        if hashlib.sha256(raw).hexdigest() != sha256:
            raise ValueError("Import source changed before audit")
        records.append(dict(path=name, sha256=sha256,
                            events=import_phase_events(raw, name)))
    for row in records:
        if hashlib.sha256(checked_bytes(root / row["path"])).hexdigest() != row["sha256"]:
            raise ValueError("Import source changed after audit")
    return dict(
        contract="saved-import-phase-audit-v1", sources=records,
        execution_order_verified=False, transitive_closure_complete=False,
        native_environment_verified=False, native_execution_completed=False,
        production_dependency_loader_implemented=False, admission=False,
        source_findings=[
            dict(path=PACKAGE + "/network.py", lines=[2, 3, 4, 7, 11, 13, 15, 17],
                 finding="Lexically imports pointgroup_ops and spconv before Torch, "
                 "then framework utilities/loss/decoder before PointNet2."),
            dict(path="framework/lib/pointgroup_ops/pointgroup_ops.py", lines=[5],
                 finding="Package import directly loads pointgroup_ops_ext; static "
                 "Python inspection cannot establish binary initialization behavior."),
            dict(path=PACKAGE + "/loss.py", lines=[35, 123],
                 finding="Bare torch.jit.script and registry decorators execute at "
                 "definition time, before any Network construction."),
            dict(path=PACKAGE + "/sample_model.py", lines=[7, 8, 12, 13, 14],
                 finding="Import changes sys.path using __file__ and working directory; "
                 "actual PointNet2 resolution cannot be inferred from its import name."),
            dict(path="framework/utils/utils.py", lines=[4, 7, 12, 17, 19],
                 finding="cuda_cast application defines a wrapper; CUDA conversions "
                 "are in its deferred invocation, not the decorator body itself.")],
        loader_contract=[
            "Hold the authorized server-4 GPU0/1 slot for the whole bounded fresh child.",
            "Before imports: verify host/interpreter, immutable source and installed "
            "dependency manifests, offline assets, allocation and fresh physical UUID.",
            "The identity observer dependency_loader returns only verified Torch, not "
            "the dataset/model package; reject CUDA already initialized by imports.",
            "Static binary provenance/ABI metadata is not a native ABI execution test.",
            "Observe sole logical0 UUID and match physical inventory before importing "
            "pointgroup_ops, torch_scatter, spconv, pointnet2 or model/dataset packages.",
            "After identity: resolve/hash actual loaded extensions and shared libraries; "
            "execute bounded native compatibility tests before saved-data/model use.",
            "Do not invoke legacy CLI, constructors, RNG helpers or torch.cuda calls "
            "inside the pre-identity loader; do not rebuild extensions automatically.",
            "Keep producer pinning separate: PinnedDiagnosticImports does not pin "
            "third-party packages. No production loader or authorization is supplied."],
        limitations=[
            "Per-source lexical order, not an inter-module runtime execution trace.",
            "Conditional branches are overapproximated, including __main__ guards.",
            "Annotations are conservatively eager; target Python/future semantics vary.",
            "Calls may invoke deferred functions indirectly; decorators/metaclasses "
            "and native extension initialization can have unobserved side effects.",
            "No name/alias resolution, call graph or installed transitive source audit.",
            "No absence-of-CUDA-side-effects claim follows from these static events."])
