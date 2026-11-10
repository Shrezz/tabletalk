"""Score the shipped indexes and the strategy prompt without running a generative model."""
import argparse
import json
from pathlib import Path
from statistics import mean
from unittest.mock import patch

from tabletalk.answering.agent import answer
from tabletalk.retrieval.index import RuleIndex
from tabletalk.strategy.coach import advise

SUITES = {"benchmark": "retrieval_cases.json", "neighbors": "retrieval_neighbors.json"}


def reference(rule):
    # Page 0 denotes publisher metadata rather than a PDF page.
    return {"id": rule.id, "pages": [rule.page, *rule.extra_pages]}


def relevant(ref, acceptable):
    return ref["id"] in acceptable and acceptable[ref["id"]] in ref["pages"]


def lookup(index, question, acceptable):
    hits = index.search(question, k=3)
    if any(h.rule.game != index.game for h in hits):
        raise AssertionError(f"Wrong game returned for {question!r}")
    ranked = [dict(reference(h.rule), score=round(h.score, 4)) for h in hits]
    rank = next((n for n, ref in enumerate(ranked, 1) if relevant(ref, acceptable)), None)
    shown = answer(index, question)
    return {"question": question, "expected": acceptable, "rank": rank, "retrieved": ranked,
            "ruling": shown.rule_id, "suggestions": list(shown.suggestions)}


def strategy(index, question, needs):
    # Capture the real model input, including evidence added after the initial search.
    stub = dict(kind="unsupported", move="", reason="", tradeoff="", sources=[])
    with patch("tabletalk.strategy.ollama.generate", return_value=stub) as generate:
        advise(index, question)
    cards = []
    if generate.called:
        messages, _schema = generate.call_args.args
        for source in json.loads(messages[-1]["content"])["sources"]:
            rule = index.by_id[source["id"]]
            if source["text"] != rule.answer:
                raise AssertionError(f"Unexpected evidence text for {rule.id}")
            cards.append(reference(rule))
    missing = [need for need in needs if not any(relevant(ref, need) for ref in cards)]
    return {"question": question, "required_groups": needs, "missing_groups": missing, "supplied": cards}


def evaluate(game, cases):
    index = RuleIndex(game)
    # Catch stale labels even if the retriever never returns the mislabeled topic.
    groups = [targets for _, targets in cases["lookup"]]
    groups += [group for _, needs in cases["strategy"] for group in needs]
    for group in groups:
        if not group or not all(relevant(reference(index.by_id[key]), {key: page}) for key, page in group.items()):
            raise ValueError(f"Unknown source or page for {game}: {group}")
    ranked = [lookup(index, q, targets) for q, targets in cases["lookup"]]
    negatives = []
    for q in cases["unanswerable"]:
        reply = answer(index, q)
        negatives.append({"question": q, "asserted": reply.rule_id or list(reply.guide_sources) or None,
                          "suggestions": list(reply.suggestions)})
    prompts = [strategy(index, q, needs) for q, needs in cases["strategy"]]
    ranks = [row["rank"] for row in ranked]
    metrics = {"questions": len(ranks), "hit_at_1": ranks.count(1), "hit_at_3": sum(r is not None for r in ranks),
               "mrr_at_3": mean(1 / r if r else 0 for r in ranks),
               "no_ruling": sum(row["asserted"] is None for row in negatives), "negatives": len(negatives),
               "all_strategy_evidence": sum(not row["missing_groups"] for row in prompts), "strategies": len(prompts)}
    metrics["correct_direct"] = sum(row["ruling"] in row["expected"] for row in ranked)
    metrics["wrong_direct"] = sum(row["ruling"] is not None and row["ruling"] not in row["expected"] for row in ranked)
    return {"metrics": metrics, "lookup": ranked, "unanswerable": negatives, "strategy": prompts}


def run(suite="benchmark"):
    path = Path(__file__).with_name(SUITES[suite])
    return {game: evaluate(game, cases) for game, cases in json.loads(path.read_text()).items()}


def print_report(results, verbose=False):
    for game, details in results.items():
        m = details["metrics"]
        strategy = (f" | Complete strategy evidence: {m['all_strategy_evidence']}/{m['strategies']}"
                    if m['strategies'] else "")
        print(f"{game.upper()} | Top 1: {m['hit_at_1']}/{m['questions']} | Top 3: {m['hit_at_3']}/{m['questions']}"
              f" | MRR@3: {m['mrr_at_3']:.3f} | No unsupported ruling: {m['no_ruling']}/{m['negatives']}"
              f" | Direct: {m['correct_direct']} correct, {m['wrong_direct']} wrong{strategy}")
        for row in details["lookup"]:
            if verbose or row["rank"] != 1:
                hits = ", ".join(f"{ref['id']} {ref['pages']} ({ref['score']})" for ref in row["retrieved"])
                print(f"  rank {row['rank'] or '>3'}: {row['question']}\n    expected {row['expected']}; got {hits}"
                      f"\n    shown: {row['ruling'] or row['suggestions'] or 'no ruling'}")
        for row in details["unanswerable"]:
            if verbose or row["asserted"]:
                print(f"  no source: {row['question']} → {row['asserted'] or 'no ruling'}")
        for row in details["strategy"]:
            if verbose or row["missing_groups"]:
                print(f"  strategy: {row['question']} → missing {row['missing_groups']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=SUITES, default="benchmark")
    parser.add_argument("--verbose", action="store_true", help="include successful cases as well as misses")
    parser.add_argument("--json", action="store_true", help="print machine-readable scores and results for every case")
    args = parser.parse_args()
    results = run(args.suite)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_report(results, args.verbose)
