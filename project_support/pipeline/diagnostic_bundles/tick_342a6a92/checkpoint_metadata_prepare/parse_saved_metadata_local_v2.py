"""Default NOP. Parse captured local pickle prefixes without executing pickle."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import math
import pickletools
import struct

HERE = Path(__file__).resolve().parent
TICK = HERE.parent
ACTUAL_SHA = "124f90ba0bc7ba99f364b17f4b606f2a5930f418aed3fbbd8f42f1d6bd62105e"
CAPTURE_SHA = "52c0903da88335db0cb2d0fea992cdecd40b9faed42a0596abe4882cad61ad79"
PREFIXES = {
    "last.pth": "da22a551532431a6ffba13035d8e08d3b5c1833a38269de33019334eabb47641",
    "best.pth": "91ecbebe02490c464c39f217f858881cf311fa1156867957bbfa3a95526d89a5",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parse_metadata(raw):
    assert len(raw) <= 65536
    operations = pickletools.genops(raw)
    trace = []
    ignored = {"PROTO", "FRAME", "BINPUT", "LONG_BINPUT", "PUT", "MEMOIZE"}
    strings = {"BINUNICODE", "SHORT_BINUNICODE", "BINUNICODE8", "UNICODE"}
    integers = {"BININT", "BININT1", "BININT2", "INT", "LONG", "LONG1", "LONG4"}

    def take():
        for operation, argument, position in operations:
            assert len(trace) < 200
            trace.append({"op": operation.name, "arg": repr(argument)[:180], "pos": position})
            if operation.name not in ignored:
                return operation.name, argument
        raise ValueError("Incomplete captured prefix")

    def expect(name, argument=None):
        operation, value = take()
        assert operation == name, (name, operation)
        if argument is not None:
            assert value == argument, (name, argument, value)
        return value

    def text(expected=None):
        operation, value = take()
        assert operation in strings and type(value) is str and len(value) <= 256
        if expected is not None:
            assert value == expected, (expected, value)
        return value

    def integer(expected=None):
        operation, value = take()
        assert operation in integers and type(value) is int
        if expected is not None:
            assert value == expected
        return value

    expect("EMPTY_DICT")
    expect("MARK")
    text("meta")
    expect("EMPTY_DICT")
    expect("MARK")
    text("epoch")
    epoch = integer()
    text("best_miou")
    expect("GLOBAL", "numpy.core.multiarray scalar")
    expect("GLOBAL", "numpy dtype")
    descriptor = text()
    assert descriptor in ("f4", "f8")
    expect("NEWFALSE")
    expect("NEWTRUE")
    expect("TUPLE3")
    expect("REDUCE")  # Only validate the token; never invoke a callable.
    expect("MARK")
    integer(3)
    byteorder = text()
    assert byteorder in ("<", ">")
    for _ in range(3):
        expect("NONE")
    integer(-1)
    integer(-1)
    integer(0)
    expect("TUPLE")
    expect("BUILD")  # Only validate the serialized dtype-state grammar.
    expect("GLOBAL", "_codecs encode")
    encoded_scalar = text()
    text("latin1")
    expect("TUPLE2")
    expect("REDUCE")
    expect("TUPLE2")
    expect("REDUCE")
    scalar_bytes = encoded_scalar.encode("latin1")
    assert len(scalar_bytes) == {"f4": 4, "f8": 8}[descriptor]
    struct_format = byteorder + {"f4": "f", "f8": "d"}[descriptor]
    best_miou = struct.unpack(struct_format, scalar_bytes)[0]
    assert math.isfinite(best_miou) and 0 <= best_miou <= 1 and epoch >= 0
    text("epochs_no_improve")
    no_improve = integer()
    assert no_improve >= 0
    text("time")
    saved_time = text()
    expect("SETITEMS")
    return {
        "meta": {"epoch": epoch, "best_miou": best_miou,
                 "epochs_no_improve": no_improve, "time": saved_time},
        "scalar_encoding": {"numpy_descriptor": descriptor, "byteorder": byteorder,
                            "raw_hex": scalar_bytes.hex(), "struct_format": struct_format},
        "metadata_opcode_trace": trace, "stopped_after_metadata_SETITEMS": True,
        "pickle_globals_imported_or_called": False, "pickle_code_executed": False,
        "tensor_storage_parsed": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parse-local", action="store_true")
    args = parser.parse_args()
    if not args.parse_local:
        print(json.dumps({"status": "DEFAULT_NOP_LOCAL_CAPTURED_METADATA_ONLY"}))
        return
    actual_path = TICK / "checkpoint_metadata.actual.json"
    assert sha(actual_path) == ACTUAL_SHA
    actual = json.loads(actual_path.read_text(encoding="utf-8"))
    owner = actual["owner"]
    assert owner["token"] == "342a6a92a2c645fdb64f7806feec102f"
    assert actual["returncode"] == 0 and actual["certainty"] == "terminal"
    capture_paths = [p for p in TICK.glob("*.json") if sha(p) == CAPTURE_SHA]
    assert len(capture_paths) == 1
    capture = json.loads(capture_paths[0].read_text(encoding="utf-8"))
    assert capture["owner"] == owner and capture["returncode"] == 0 and capture["certainty"] == "terminal"
    old_rows = {Path(row["path"]).name: row for row in actual["observation"]["checkpoints"]}
    rows = []
    for filename, expected in PREFIXES.items():
        prefix = TICK / (filename + ".data.pkl.prefix")
        assert prefix.stat().st_size == 65536 and sha(prefix) == expected
        assert old_rows[filename]["metadata_prefix_sha256"] == expected
        rows.append({"checkpoint": old_rows[filename]["path"],
                     "checkpoint_bytes": old_rows[filename]["bytes"],
                     "checkpoint_mtime_ns": old_rows[filename]["mtime_ns"],
                     "prefix_source": {"path": str(prefix), "sha256": expected},
                     **parse_metadata(prefix.read_bytes())})
    result = {
        "owner": owner, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "kind": "ACTUAL_LOCAL_CAPTURED_PREFIX_NUMPY_FLOAT_METADATA_PARSE",
        "passed": True, "certainty": "terminal", "checkpoints": rows,
        "metadata_observation": {"path": str(actual_path), "sha256": ACTUAL_SHA},
        "prefix_capture_observation": {"path": str(capture_paths[0]), "sha256": CAPTURE_SHA},
        "parser": {"path": str(Path(__file__).resolve()), "sha256": sha(__file__)},
        "Torch_or_NumPy_imported": False, "unpickling_or_pickle_callable_execution": False,
        "SSH_or_GPU_or_checkpoint_file_read": False,
        "limitations": [
            "Only checkpoint metadata prefix is parsed; tensor/optimizer/checkpoint contents are not validated.",
            "Saved epoch and running best do not establish completed training, efficacy or novelty.",
            "Current partial epoch2 completion must be determined from separate terminal evidence.",
        ],
    }
    output = TICK / "checkpoint_metadata.local_parse_v2.actual.json"
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"path": str(output), "sha256": sha(output),
                      "saved_metadata": [row["meta"] for row in rows]}))


if __name__ == "__main__":
    main()
