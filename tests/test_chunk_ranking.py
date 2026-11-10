"""Check rule ranking separately from the answer shown at the table."""
import unittest

from tests.evaluate_retrieval import run


class ChunkRetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.benchmark = run()
        cls.neighbors = run("neighbors")

    def test_expected_chunk_ranks_first(self):
        for game, report in self.benchmark.items():
            for row in report["lookup"]:
                with self.subTest(game=game, question=row["question"]):
                    self.assertEqual(row["rank"], 1, f"Expected {row['expected']}; got {row['retrieved']}")

    def test_repaired_lookups_give_direct_cited_rulings(self):
        targets = {"catan": {"turn", "broken-road"}, "pandemic": {"researcher"}}
        for game, expected in targets.items():
            rows = [r for r in self.benchmark[game]["lookup"] if expected.intersection(r["expected"])]
            self.assertEqual({r["ruling"] for r in rows}, expected)
            for row in rows:
                with self.subTest(game=game, question=row["question"]):
                    self.assertIn(row["ruling"], row["expected"])

    def test_paraphrases_and_neighboring_rules(self):
        for game, report in self.neighbors.items():
            for row in report["lookup"]:
                with self.subTest(game=game, question=row["question"]):
                    self.assertIsNotNone(row["rank"], f"Expected {row['expected']}; got {row['retrieved']}")
                    if row["ruling"] is not None:
                        self.assertIn(row["ruling"], row["expected"])
            self.assertGreaterEqual(report["metrics"]["hit_at_1"], 4)

    def test_no_ruling_without_support(self):
        for suite in (self.benchmark, self.neighbors):
            for game, report in suite.items():
                for row in report["unanswerable"]:
                    with self.subTest(game=game, question=row["question"]):
                        self.assertIsNone(row["asserted"])

    def test_strategy_prompt_contains_all_required_evidence(self):
        for game, report in self.benchmark.items():
            for row in report["strategy"]:
                with self.subTest(game=game, question=row["question"]):
                    self.assertFalse(row["missing_groups"],
                                     f"Missing {row['missing_groups']}; prompt contained {row['supplied']}")
