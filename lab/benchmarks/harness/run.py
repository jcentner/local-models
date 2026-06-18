"""Run a benchmark dataset against a local model and score it.

Usage (from ``lab/benchmarks/``):

    python -m harness.run --benchmark ../../benchmarks/<name> --model <ollama-tag> \\
        --k 1 --temperature 1.0 --top-p 0.95 --num-ctx 32768 --seed 0

Reads ``benchmarks/<name>/{bench.json,prompts.jsonl,answer_key.jsonl,rubric.md}``,
samples ``k`` completions per prompt, scores via the method declared in
``bench.json`` (equivalence | code_tests | llm_judge), prints pass@k / avg, appends
a row to ``results.csv``, and saves raw completions under ``runs/`` (git-ignored).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import platform
import socket
import sys
from pathlib import Path

# Allow running both as ``-m harness.run`` and as a direct script.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from harness.client import ChatClient, SamplingConfig
    from harness.scorers import code_exec, equivalence, llm_judge
else:
    from .client import ChatClient, SamplingConfig
    from .scorers import code_exec, equivalence, llm_judge

HERE = Path(__file__).resolve().parent          # lab/benchmarks/harness
LAB_BENCH = HERE.parent                          # lab/benchmarks


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_benchmark(bench_dir: Path) -> dict:
    manifest = json.loads((bench_dir / "bench.json").read_text())
    prompts = _read_jsonl(bench_dir / "prompts.jsonl")
    key = {row["id"]: row for row in _read_jsonl(bench_dir / "answer_key.jsonl")}
    rubric_path = bench_dir / "rubric.md"
    manifest["_prompts"] = prompts
    manifest["_key"] = key
    manifest["_rubric"] = rubric_path.read_text() if rubric_path.exists() else ""
    return manifest


def score_one(method: str, manifest: dict, item: dict, completion: str, judge=None) -> dict:
    key = manifest["_key"].get(item["id"], {})
    if method == "equivalence":
        return equivalence.score(completion, key.get("answer", ""))
    if method == "code_tests":
        return code_exec.score(completion, key.get("tests", ""))
    if method == "llm_judge":
        if judge is None:
            raise SystemExit("llm_judge benchmark needs --judge-model")
        return llm_judge.score(item["prompt"], completion, manifest["_rubric"], judge,
                               pass_threshold=manifest.get("judge", {}).get("pass_threshold", 6.0))
    raise SystemExit(f"unknown scoring method: {method}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run a benchmark against a local model.")
    ap.add_argument("--benchmark", required=True, help="path to benchmarks/<name>/ dir")
    ap.add_argument("--model", required=True, help="Ollama model tag under test")
    ap.add_argument("--k", type=int, default=1, help="samples per prompt (pass@k)")
    ap.add_argument("--limit", type=int, default=0, help="limit number of prompts (0 = all)")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--top-p", type=float, default=0.95)
    ap.add_argument("--top-k", type=int, default=0)
    ap.add_argument("--num-predict", type=int, default=4096)
    ap.add_argument("--num-ctx", type=int, default=8192)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--base-url", default="http://localhost:11434")
    ap.add_argument("--judge-model", default=None, help="model tag for llm_judge")
    ap.add_argument("--judge-base-url", default="http://localhost:11434")
    ap.add_argument("--results", default=str(LAB_BENCH / "results.csv"))
    ap.add_argument("--dry-run", action="store_true", help="print config + first prompt, don't call the model")
    args = ap.parse_args(argv)

    bench_dir = Path(args.benchmark).resolve()
    manifest = load_benchmark(bench_dir)
    method = manifest["scoring"]
    prompts = manifest["_prompts"]
    if args.limit:
        prompts = prompts[: args.limit]

    sampling = SamplingConfig(
        temperature=args.temperature, top_p=args.top_p, top_k=args.top_k,
        num_predict=args.num_predict, num_ctx=args.num_ctx, seed=args.seed,
    )
    client = ChatClient(model=args.model, base_url=args.base_url, sampling=sampling)
    judge = None
    if args.judge_model:
        judge = ChatClient(model=args.judge_model, base_url=args.judge_base_url,
                           sampling=SamplingConfig(temperature=0.0, num_predict=1024))

    print(f"benchmark={manifest['name']} v{manifest.get('version','?')} method={method} "
          f"items={len(prompts)} k={args.k}")
    print(f"model={args.model} sampling={sampling.to_options()}")
    if args.dry_run:
        if prompts:
            print("\n--- first prompt ---\n" + prompts[0]["prompt"][:500])
        return 0

    runs_dir = LAB_BENCH / "runs"
    runs_dir.mkdir(exist_ok=True)
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    raw_path = runs_dir / f"{manifest['name']}-{args.model.replace(':', '_')}-{ts}.jsonl"

    item_pass = 0          # items with >=1 correct sample (pass@k)
    sample_correct = 0     # total correct samples (for avg)
    total_samples = 0
    tok_s_sum = 0.0
    with raw_path.open("w") as raw:
        for item in prompts:
            any_correct = False
            for _ in range(args.k):
                comp = client.complete([{"role": "user", "content": item["prompt"]}],
                                       system=manifest.get("system"))
                res = score_one(method, manifest, item, comp.text, judge)
                total_samples += 1
                tok_s_sum += comp.gen_tok_per_s
                if res.get("correct"):
                    sample_correct += 1
                    any_correct = True
                raw.write(json.dumps({"id": item["id"], "result": res,
                                      "completion": comp.text,
                                      "gen_tok_per_s": comp.gen_tok_per_s}) + "\n")
            if any_correct:
                item_pass += 1
            mark = "OK " if any_correct else "XX "
            print(f"  {mark}{item['id']}")

    n = len(prompts) or 1
    pass_at_k = item_pass / n
    avg_correct = sample_correct / (total_samples or 1)
    mean_tok_s = round(tok_s_sum / (total_samples or 1), 2)
    print(f"\npass@{args.k}={pass_at_k:.3f}  avg_correct={avg_correct:.3f}  "
          f"mean_gen_tok/s={mean_tok_s}  raw={raw_path.name}")

    row = {
        "date": dt.date.today().isoformat(),
        "machine": socket.gethostname(),
        "model": args.model,
        "runner": "ollama (harness)",
        "benchmark": f"{manifest['name']} v{manifest.get('version','?')}",
        "scoring": method,
        "num_ctx": args.num_ctx,
        "sampling": f"t={args.temperature},top_p={args.top_p},top_k={args.top_k}",
        "seed": args.seed,
        "k": args.k,
        "n_items": len(prompts),
        f"pass_at_k": round(pass_at_k, 4),
        "avg_correct": round(avg_correct, 4),
        "mean_gen_tok_s": mean_tok_s,
        "judge": args.judge_model or "",
        "platform": platform.platform(),
    }
    results_path = Path(args.results)
    write_header = not results_path.exists()
    with results_path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            w.writeheader()
        w.writerow(row)
    print(f"appended -> {results_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
