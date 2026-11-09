"""A direct ruling must resolve the question and cite the expected edition and page."""
import json
import unittest
from pathlib import Path

from tabletalk.answering.agent import answer
from tabletalk.retrieval.index import RuleIndex


class RetrievalContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = RuleIndex()

    def test_original_questions_and_citations(self):
        path = Path(__file__).with_name("questions.json")
        for question, topic, page in json.loads(path.read_text()):
            with self.subTest(question=question):
                reply = answer(self.index, question)
                self.assertEqual(reply.rule_id, topic)
                if topic:
                    self.assertEqual(self.index.by_id[topic].page, page)

    def test_new_phrasings_may_clarify_but_must_not_misrule(self):
        for suite in ("transfer", "holdout"):
            cases = json.loads(Path(__file__).with_name(f"{suite}.json").read_text())
            for question, topic, page in cases:
                with self.subTest(question=question):
                    reply = answer(self.index, question)
                    if reply.rule_id:
                        self.assertEqual(reply.rule_id, topic)
                        self.assertEqual(self.index.by_id[reply.rule_id].page, page)

    def test_setup_overview_does_not_swallow_specific_rules(self):
        for q in ("What’s needed for basic set-up?", "How do we set up CATAN?"):
            self.assertTrue(answer(self.index, q).guide_sources)
        for q in ("Where does the robber start during setup?", "How do I set up Seafarers?",
                  "What is needed for variable setup?", "How do I set up for 6 players?"):
            self.assertFalse(answer(self.index, q).guide_sources)

    def test_starting_player_depends_on_setup(self):
        unknown = answer(self.index, "Who starts?")
        self.assertIsNone(unknown.rule_id)
        self.assertEqual(set(unknown.suggestions), {"starting-hand", "opening"})
        for question, topic in (
            ("Who gets the first roll on the beginner board?", "starting-hand"),
            ("Who starts placement on a random board?", "opening"),
        ):
            with self.subTest(question=question):
                self.assertEqual(answer(self.index, question).rule_id, topic)
