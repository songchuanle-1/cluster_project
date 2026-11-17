"""Byte-pinned imports for the future native CPU entrypoint, not a sandbox."""
import hashlib
import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import json
from pathlib import Path, PurePosixPath
import sys


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked_digest(value):
    if (not isinstance(value, str) or len(value) != 64
            or any(c not in "0123456789abcdef" for c in value)):
        raise ValueError("Expected lowercase SHA256")
    return value


def regular_bytes(path):
    path = Path(path).absolute()
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError("Symlink in pinned source path")
    if not path.is_file():
        raise ValueError("Pinned source is not a regular file")
    return path.read_bytes()


class PinnedDiagnosticImports(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Load declared flat producer modules from verified bytes, ignoring pyc.

    Use only in a fresh child process, before any producer imports. Other
    dependencies remain normal imports. Host authorization, native dependency
    provenance and scratch-write enforcement are separate required gates.
    The manifest digest must come from independently pinned orchestration input.
    """

    def __init__(self, bundle, manifest_sha256, required_modules):
        self.bundle = Path(bundle).absolute()
        self.manifest_sha256 = checked_digest(manifest_sha256)
        self.manifest_path = self.bundle / "manifest.json"
        raw = regular_bytes(self.manifest_path)
        if digest(raw) != self.manifest_sha256:
            raise ValueError("Immutable manifest hash differs")
        manifest = json.loads(raw)
        self.files, self.modules, self.loaded = {}, {}, {}
        self.active = False
        for row in manifest["files"]:
            name = row["path"]
            if not isinstance(name, str) or "\\" in name or ":" in name:
                raise ValueError("Noncanonical bundle path")
            relative = PurePosixPath(name)
            if (relative.is_absolute() or str(relative) != name
                    or any(p in ("", ".", "..") for p in name.split("/"))
                    or name in self.files):
                raise ValueError("Noncanonical or duplicate bundle path")
            path = self.bundle.joinpath(*relative.parts)
            self.files[name] = (path, checked_digest(row["sha256"]))
            if relative.suffix == ".py":
                module = relative.stem
                if (not module.isidentifier() or module == "__init__"
                        or module in self.modules):
                    raise ValueError("Require unique flat producer module names")
                self.modules[module] = name
        required = tuple(required_modules)
        if not required or any(name not in self.modules for name in required):
            raise ValueError("Required producer modules absent")
        self.verify()

    def verify(self):
        if digest(regular_bytes(self.manifest_path)) != self.manifest_sha256:
            raise ValueError("Immutable manifest changed")
        for path, expected in self.files.values():
            if digest(regular_bytes(path)) != expected:
                raise ValueError("Pinned source hash differs: " + path.name)
        for name, module in self.loaded.items():
            path, _ = self.files[self.modules[name]]
            if (sys.modules.get(name) is not module
                    or getattr(module, "__file__", None) != str(path)
                    or getattr(module, "__loader__", None) is not self
                    or module.__spec__.loader is not self
                    or module.__spec__.origin != str(path)):
                raise ValueError("Imported producer identity differs: " + name)

    def __enter__(self):
        if self.active:
            raise ValueError("Import boundary already active")
        self.verify()
        basenames = {self.files[name][0].name for name in self.modules.values()}
        for name, module in tuple(sys.modules.items()):
            source = getattr(module, "__file__", None)
            if name != "__main__" and (
                    name in self.modules
                    or (source and Path(source).name in basenames)):
                raise ValueError("Producer already imported; fresh process required")
        self.active = True
        sys.meta_path.insert(0, self)
        return self

    def __exit__(self, exc_type, exc, traceback):
        try:
            if exc_type is None:
                self.verify()
        finally:
            sys.meta_path[:] = [finder for finder in sys.meta_path if finder is not self]
            for name, module in self.loaded.items():
                if sys.modules.get(name) is module:
                    del sys.modules[name]
            self.loaded.clear()
            self.active = False

    def find_spec(self, fullname, path=None, target=None):
        if not self.active or fullname not in self.modules:
            return None
        source, _ = self.files[self.modules[fullname]]
        return importlib.util.spec_from_file_location(fullname, source, loader=self)

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        if not self.active:
            raise ValueError("Import boundary inactive")
        name = module.__spec__.name
        source, expected = self.files[self.modules[name]]
        self.verify()
        raw = regular_bytes(source)
        if digest(raw) != expected:
            raise ValueError("Pinned source changed before compile")
        self.loaded[name] = module
        # Compile the checked bytes directly; neither pyc nor search-path shadow
        # modules participate in this producer import.
        exec(compile(raw, str(source), "exec"), module.__dict__)
        self.verify()


class PreIdentityTorchImports(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Single-use fresh-child Torch loader with explicit dependency provenance.

    Rows are independently supplied {name, path, sha256, is_package} mappings.
    Every newly resolved non-stdlib import needs a row, including Torch's Python
    and extension modules. Pre-existing unlisted bootstrap modules are trusted
    and must be inventoried separately by the caller. This is a trusted-code
    provenance boundary, not an import sandbox,
    ABI check, CUDA side-effect proof, or authorization to execute native work.
    Keep it active through logical-device identity collection, then verify/exit
    before loading the model. Never reuse a failed child: native imports cannot
    be rolled back safely, so modules deliberately remain loaded on exit.
    """

    MODEL_ROOTS = frozenset({
        "pointgroup_ops", "spconv", "pointnet2", "pointnet2_ops", "framework",
        "network", "model", "sample_model", "transformers", "gorilla",
    })

    def __init__(self, modules):
        self.modules, self.loaded, self.extensions = {}, {}, {}
        self.active = self.used = self.failed = False
        self.torch_loaded = False
        for row in modules:
            name, source = row["name"], row["path"]
            if (not isinstance(name, str)
                    or any(not part.isidentifier() for part in name.split("."))
                    or name in self.modules
                    or name.split(".")[0] in self.MODEL_ROOTS
                    or name.split(".")[0] in sys.stdlib_module_names):
                raise ValueError("Invalid, duplicate or forbidden dependency name")
            if (not isinstance(source, str) or not Path(source).is_absolute()
                    or str(Path(source)) != source
                    or type(row["is_package"]) is not bool):
                raise ValueError("Require canonical absolute dependency path and package flag")
            path = Path(source)
            extension = any(source.endswith(suffix)
                            for suffix in importlib.machinery.EXTENSION_SUFFIXES)
            if not extension and path.suffix != ".py":
                raise ValueError("Only Python source or native extension modules supported")
            if row["is_package"] and path.suffix == ".py" and path.name != "__init__.py":
                raise ValueError("Python package must use __init__.py")
            if any(path == entry["path"] for entry in self.modules.values()):
                raise ValueError("Duplicate dependency path")
            self.modules[name] = dict(path=path, sha256=checked_digest(row["sha256"]),
                                      is_package=row["is_package"], extension=extension)
        if "torch" not in self.modules or not self.modules["torch"]["is_package"]:
            raise ValueError("Explicit Torch package required")
        for name, row in self.modules.items():
            if "." in name:
                parent = self.modules.get(name.rsplit(".", 1)[0])
                if parent is None or not parent["is_package"]:
                    raise ValueError("Explicit parent package required")
                if not row["path"].is_relative_to(parent["path"].parent):
                    raise ValueError("Dependency outside declared parent package")
        self.roots = {name.split(".")[0] for name in self.modules}
        self.verify()

    def _bytes(self, name):
        row = self.modules[name]
        raw = regular_bytes(row["path"])
        if digest(raw) != row["sha256"]:
            raise ValueError("Dependency source hash differs: " + name)
        return raw

    def verify(self):
        for name in self.modules:
            self._bytes(name)
        for name, module in self.loaded.items():
            row = self.modules[name]
            spec = getattr(module, "__spec__", None)
            if (sys.modules.get(name) is not module
                    or getattr(module, "__file__", None) != str(row["path"])
                    or getattr(module, "__loader__", None) is not self
                    or spec is None or spec.name != name or spec.loader is not self
                    or spec.origin != str(row["path"])
                    or (row["is_package"]
                        and (list(getattr(module, "__path__", [])) != [str(row["path"].parent)]
                             or list(spec.submodule_search_locations or [])
                             != [str(row["path"].parent)]))):
                raise ValueError("Dependency loaded origin/identity differs: " + name)
        if self.active:
            if sys.path != self.search_path:
                raise ValueError("Dependency changed sys.path")
            if not sys.meta_path or sys.meta_path[0] is not self:
                raise ValueError("Dependency changed import boundary")
            for name in set(sys.modules) - self.initial_modules:
                root = name.split(".")[0]
                if root not in sys.stdlib_module_names and name not in self.loaded:
                    raise ValueError("Untracked dependency module: " + name)

    def __enter__(self):
        if self.used:
            raise ValueError("Fresh child boundary is single-use")
        self.used = True
        self.verify()
        paths = {row["path"] for row in self.modules.values()}
        package_dirs = [row["path"].parent for row in self.modules.values()
                        if row["is_package"]]
        for name, module in tuple(sys.modules.items()):
            source = getattr(module, "__file__", None)
            source_path = Path(source).absolute() if isinstance(source, str) else None
            if (name.split(".")[0] in self.roots | self.MODEL_ROOTS
                    or (source_path is not None
                        and (source_path in paths
                             or any(source_path.is_relative_to(p) for p in package_dirs)))):
                raise ValueError("Dependency/model already imported; fresh child required")
        self.initial_modules = set(sys.modules)
        self.search_path = list(sys.path)
        self.active = True
        sys.meta_path.insert(0, self)
        return self

    def __exit__(self, exc_type, exc, traceback):
        try:
            if exc_type is None:
                self.verify()
                if self.failed:
                    raise ValueError("Failed dependency import; discard child")
        except BaseException:
            self.failed = True
            raise
        finally:
            self.failed = self.failed or exc_type is not None
            sys.meta_path[:] = [finder for finder in sys.meta_path if finder is not self]
            self.active = False

    def find_spec(self, fullname, path=None, target=None):
        if not self.active:
            return None
        if fullname not in self.modules:
            if fullname.split(".")[0] not in sys.stdlib_module_names:
                self.failed = True
                raise ImportError("Undeclared pre-identity dependency: " + fullname)
            return None
        row = self.modules[fullname]
        self._bytes(fullname)
        spec = importlib.util.spec_from_file_location(fullname, row["path"], loader=self)
        if row["is_package"]:
            spec.submodule_search_locations = [str(row["path"].parent)]
        return spec

    def create_module(self, spec):
        row = self.modules[spec.name]
        if not row["extension"]:
            return None
        self._bytes(spec.name)
        loader = importlib.machinery.ExtensionFileLoader(spec.name, str(row["path"]))
        self.extensions[spec.name] = loader
        try:
            module = loader.create_module(spec)
            self._bytes(spec.name)
            return module
        except BaseException:
            self.failed = True
            raise

    def exec_module(self, module):
        name = module.__spec__.name
        if not self.active or self.failed:
            raise ValueError("Inactive or failed dependency boundary")
        row = self.modules[name]
        self.loaded[name] = module
        try:
            raw = self._bytes(name)
            if row["extension"]:
                self.extensions[name].exec_module(module)
            else:
                exec(compile(raw, str(row["path"]), "exec"), module.__dict__)
            self._bytes(name)
        except BaseException:
            self.failed = True
            raise

    def load_torch(self):
        if not self.active or self.failed or self.torch_loaded:
            raise ValueError("Require active, unused Torch loader in fresh child")
        self.torch_loaded = True
        try:
            module = importlib.import_module("torch")
            self.verify()
            if self.failed:
                raise ValueError("Failed dependency import; discard child")
            return module
        except BaseException:
            self.failed = True
            raise
