"""Exercise both shelf entries in a single Streamlit session and check rule provenance."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from tabletalk.answering.agent import answer
from tabletalk.catalog import PANDEMIC
from tabletalk.retrieval.index import RuleIndex
from tabletalk.strategy.coach import advise
from tabletalk.strategy.ollama import CoachError

APP = Path(__file__).resolve().parents[1] / "app.py"


class PandemicRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = RuleIndex("pandemic")

    def test_question_set_and_pages(self):
        for question, topic, page in json.loads(Path(__file__).with_name("pandemic.json").read_text()):
            with self.subTest(question=question):
                result = answer(self.index, question)
                self.assertEqual(result.rule_id, topic)
                if topic:
                    self.assertEqual(self.index.by_id[topic].url, f"{PANDEMIC.pdf}#page={page}")

    @patch("tabletalk.strategy.ollama.generate")
    def test_coach_evidence_belongs_to_the_selected_game(self, generate):
        generate.return_value = dict(kind="advice", move="Discover the blue cure.", reason="You have four blue cards.",
                                     tradeoff="Waiting spends a turn.", sources=["scientist", "win"])
        advise(self.index, "I'm the Scientist at a research station with four blue cards. Treat or cure?")
        (system, user), schema = generate.call_args.args
        self.assertIn("Pandemic", system["content"])
        context = json.loads(user["content"])
        self.assertNotIn("build_menu", context)
        self.assertNotIn("roll_frequencies", context)
        ids = schema["properties"]["sources"]["items"]["enum"]
        self.assertIn("scientist", ids)
        self.assertTrue(all(self.index.by_id[key].game == PANDEMIC for key in ids))
        generate.return_value["sources"] = ["settlement"]
        with self.assertRaises(CoachError):
            advise(self.index, "How should we approach cures?")
        generate.reset_mock()
        self.assertEqual(advise(self.index, "How do I win at CATAN?").kind, "unsupported")
        self.assertEqual(advise(self.index, "Whats needed for basic setup>").kind, "guide")
        generate.assert_not_called()


class TwoGamesAtOneTable(unittest.TestCase):
    def test_same_question_and_separate_histories(self):
        app = AppTest.from_file(str(APP)).run()

        def open_game(key):
            app.button(key=f"pick_{key}").click().run()
            self.assertFalse(app.exception)

        def shelf():
            next(b for b in app.button if "Game shelf" in b.label).click().run()

        def page():
            return " ".join(m.value for m in app.markdown)

        open_game("catan")
        app.chat_input[0].set_value("When does a person win?").run()
        self.assertIn("your own turn", page())
        shelf()
        open_game("pandemic")
        self.assertFalse(app.chat_message)
        app.chat_input[0].set_value("When does a person win?").run()
        self.assertIn("fourth cure", page())
        self.assertIn(f"{PANDEMIC.pdf}#page=7", page())
        self.assertNotIn("catan.com", page())

        for mode in ("Ask a rule", "Strategy"):
            app.segmented_control(key="mode").set_value(mode).run()
            app.chat_input[0].set_value("What's needed for basic setup?").run()
            self.assertIn("Atlanta", page())
            self.assertIn(f"{PANDEMIC.pdf}#page=3", page())

        app.segmented_control(key="mode").set_value("Set us up").run()
        next(b for b in app.button if b.label == "Next step").click().run()
        self.assertIn("nine cities", app.subheader[0].value)
        app.segmented_control(key="mode").set_value("Quick refresher").run()
        self.assertIn("eighth outbreak", page())
        shelf()
        open_game("catan")
        app.segmented_control(key="mode").set_value("Set us up").run()
        self.assertIn("STEP 1", str(app.caption[0].value))
        app.segmented_control(key="mode").set_value("Strategy").run()
        self.assertFalse(app.chat_message)
        app.segmented_control(key="mode").set_value("Ask a rule").run()
        self.assertIn("your own turn", page())
        self.assertNotIn("pandemic.pdf", page())
        self.assertFalse(app.exception)
