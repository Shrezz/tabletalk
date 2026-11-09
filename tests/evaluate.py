"""Run from the project root: python -m tests.evaluate"""
import json
import argparse
from pathlib import Path
from statistics import quantiles
from time import perf_counter

from tabletalk.answering.agent import answer
from tabletalk.retrieval.index import RuleIndex


def evaluate(filename, game="catan"):
    idx = RuleIndex(game)
    idx.search("warm up")
    cases = json.loads(Path(__file__).with_name(filename).read_text())
    known = top3 = correct = answered = safe = refusals = 0
    offered = 0
    times = []
    for q, target, page in cases:
        start = perf_counter()
        result = answer(idx, q)
        times.append((perf_counter() - start) * 1000)
        if target:
            known += 1
            top3 += target in [h.rule.id for h in idx.search(q)]
            offered += target in result.suggestions
            answered += bool(result.rule_id)
            correct += bool(result.rule_id == target and idx.by_id[target].page == page)
        else:
            safe += 1
            refusals += result.rule_id is None
        print(f"{q} | expected: {target or 'no ruling'} | returned: {result.rule_id or ', '.join(result.suggestions) or 'no ruling'}")
    print(f"\nExpected rule in top 3: {top3}/{known}. Correct cited rule: {correct}/{known}.")
    print(f"Answer coverage: {answered}/{known}. Unsupported cases with no ruling: {refusals}/{safe}.")
    print(f"Incorrect direct rulings: {answered - correct + safe - refusals}. Correct topic offered on {offered} further questions.")
    print(f"Warm answer latency p95: {quantiles(times, n=100, method='inclusive')[94]:.1f} ms "
          "(backend only). Inspect answers against the cited pages to assess faithfulness.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=["questions.json", "calibration.json", "transfer.json", "holdout.json", "pandemic.json"])
    args = parser.parse_args()
    suite = args.suite or "questions.json"
    evaluate(suite, "pandemic" if suite == "pandemic.json" else "catan")
