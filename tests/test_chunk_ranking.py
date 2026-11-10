"""Regression gates on real retrieval; run tests.evaluate_retrieval for full diagnostics."""
import unittest

from tests.evaluate_retrieval import run

# Baseline misses are visible in the report. Do not fail an improvement to this case.
KNOWN_TOP3_MISS = ("catan", "What comes first on my turn: swapping cards or putting down a road?")


class ChunkRetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = run()

    def test_expected_chunks_remain_in_top_three(self):
        for game, report in self.results.items():
            for row in report["lookup"]:
                if (game, row["question"]) == KNOWN_TOP3_MISS:
                    continue
                with self.subTest(game=game, question=row["question"]):
                    self.assertIsNotNone(row["rank"], f"Expected {row['expected']}; retrieved {row['retrieved']}")

    def test_first_choice_does_not_regress_per_game(self):
        for game, (hits, total) in {"catan": (10, 12), "pandemic": (11, 12)}.items():
            with self.subTest(game=game):
                metrics = self.results[game]["metrics"]
                misses = [(r["question"], r["expected"], r["retrieved"][:1])
                          for r in self.results[game]["lookup"] if r["rank"] != 1]
                self.assertGreaterEqual(metrics["hit_at_1"] / metrics["questions"], hits / total, misses)

    def test_no_ruling_without_support(self):
        for game, report in self.results.items():
            for row in report["unanswerable"]:
                with self.subTest(game=game, question=row["question"]):
                    self.assertIsNone(row["asserted"])

    def test_strategy_prompt_contains_all_required_evidence(self):
        for game, report in self.results.items():
            for row in report["strategy"]:
                with self.subTest(game=game, question=row["question"]):
                    self.assertFalse(row["missing_groups"],
                                     f"Missing {row['missing_groups']}; prompt contained {row['supplied']}")
