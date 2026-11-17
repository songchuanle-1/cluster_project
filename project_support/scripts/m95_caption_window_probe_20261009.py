"""Execute the native text tokenization contract on whole frozen TRAIN."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    root = args.root.resolve()
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "" or args.output.exists():
        raise ValueError("CPU-only and fresh output required")
    if not args.output.resolve().is_relative_to(root.parent / "pipeline"):
        raise ValueError("Output must be in this project")
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      TOKENIZERS_PARALLELISM="false")
    import torch
    from transformers import RobertaTokenizerFast
    data = Path("/data3/songcl/data/data_cluster")
    annotation = data / "scanrefer/ScanRefer_train_new.json"
    graphs = data / "scanrefer/scene_graphs_new_train.json"
    dataset = root / "framework/dataset/scannetv2.py"
    if sha(annotation) != "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d":
        raise ValueError("Frozen TRAIN annotations differ")
    if sha(graphs) != "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08":
        raise ValueError("Frozen TRAIN graphs differ")
    if sha(dataset) != "2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d":
        raise ValueError("Frozen dataset source differs")
    collator = next(n for n in ast.walk(ast.parse(dataset.read_text()))
                    if isinstance(n, ast.FunctionDef) and n.name == "collate_fn")
    calls = [n for n in ast.walk(collator) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute) and n.func.attr == "batch_encode_plus"]
    if len(calls) != 1:
        raise ValueError("Native collator call ambiguous")
    kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in calls[0].keywords}
    tokenizer = RobertaTokenizerFast.from_pretrained(str(data / "roberta-base"),
                                                     local_files_only=True)
    rows = json.loads(annotation.read_text())
    graph = json.loads(graphs.read_text())
    records, retained, over78, over256, max_len = [], 0, 0, 0, 0
    for offset in range(0, len(rows), 64):
        selected = rows[offset:offset + 64]
        text = [(" ".join(graph[r["scene_id"]][str(r["ann_id"])]["utterance"]
                         .replace(",", " ,").split()) + " . not mentioned") for r in selected]
        native = tokenizer.batch_encode_plus(text, **kwargs)
        independent = tokenizer.batch_encode_plus(text, padding=False, truncation=False)
        control = tokenizer.batch_encode_plus(text, padding=False,
                                              truncation=True, max_length=78)
        for i, r in enumerate(selected):
            tokens = native["input_ids"][i][native["attention_mask"][i].bool()].tolist()
            full = independent["input_ids"][i]
            same = tokens == full
            retained += int(same)
            over78 += int(len(full) > 78)
            over256 += int(len(full) > 256)
            max_len = max(max_len, len(full))
            if len(full) > 78 or not same:
                records.append(dict(scene=r["scene_id"], ann_id=int(r["ann_id"]),
                                    token_count=len(full), native_token_count=len(tokens),
                                    control_token_count=len(control["input_ids"][i]),
                                    original_retained=same,
                                    beyond78_sha256=hashlib.sha256(
                                        json.dumps(full[78:]).encode()).hexdigest()))
        if offset % 4096 == 0:
            print(json.dumps({"processed": min(offset + 64, len(rows)),
                              "total": len(rows)}), flush=True)
    result = dict(contract="m95_native_caption_window_v1", admission=False,
                  script_sha256=sha(__file__), annotation_sha256=sha(annotation),
                  graph_sha256=sha(graphs), dataset_sha256=sha(dataset),
                  actual_native_tokenizer_kwargs=kwargs, records=records,
                  summary=dict(expressions=len(rows), original_token_stream_retained=retained,
                               over78=over78, over256=over256, max_tokens=max_len,
                               native_truncation78_deficit=len(rows) - retained),
                  cuda_initialized=torch.cuda.is_initialized(),
                  training_started=False, optimizer_created=False)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({"summary": result["summary"], "sha256": sha(args.output)}), flush=True)


if __name__ == "__main__":
    main()
