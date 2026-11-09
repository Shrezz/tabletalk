"""Exercise the coach boundary without needing a model for the regression suite."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from tabletalk.retrieval.index import RuleIndex
from tabletalk.strategy.coach import advise
from tabletalk.strategy.hand import build_plans
from tabletalk.strategy.ollama import CoachError

APP = Path(__file__).resolve().parents[1] / "app.py"


def local_response(messages, schema):
    context = json.loads(messages[-1]["content"])
    ids = [card["id"] for card in context["sources"]]
    assert "city" in ids and "settlement" in ids
    assert schema["properties"]["sources"]["items"]["enum"] == ids
    return {"kind": "advice", "move": "Upgrade the productive settlement to increase income.",
            "reason": "The city produces more from the same intersections.",
            "tradeoff": "Expand first if the open site is about to be taken.", "sources": ["city", "settlement"]}


class StrategyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = RuleIndex()

    def test_budget_only_uses_an_explicit_complete_hand(self):
        self.assertIsNone(build_plans("I have 3 ore. Should I build a city?", []))
        self.assertIsNone(build_plans("My hand is 2 ore and some other cards.", []))
        q = "My entire hand is 3 ore and 2 wheat. City or settlement?"
        options = build_plans(q, [])
        self.assertIn("covers the cost", options["city"])
        self.assertIn("1 brick, 1 lumber, 1 wool", options["settlement"])
        self.assertIsNone(build_plans("I traded for more cards.", [(q, None)]))

    @patch("tabletalk.strategy.ollama.generate")
    def test_unaffordable_build_is_a_saving_plan(self, generate):
        # The model can select a goal, but cannot tell the app that an unaffordable build is payable.
        generate.return_value = {"kind": "advice", "move": "Build immediately.", "choice": "settlement",
                                 "reason": "A new site gives access to brick.", "tradeoff": "A city earns more income.",
                                 "sources": ["settlement", "city"]}
        tip = advise(self.index, "My entire hand is 3 ore and 2 grain. City or settlement?")
        self.assertNotIn("immediately", tip.move)
        self.assertIn("1 brick, 1 lumber, 1 wool", tip.move)
        self.assertIn("settlement", tip.sources)

    @patch("tabletalk.strategy.ollama.generate", side_effect=local_response)
    def test_comparison_and_followup(self, generate):
        question = "Should I upgrade to a city or build another settlement?"
        tip = advise(self.index, question)
        advise(self.index, "What if my opponent can get there first?", [(question, tip)])
        self.assertEqual(generate.call_count, 2)
        payload = json.loads(generate.call_args.args[0][-1]["content"])
        self.assertEqual(payload["recent_turns"][0]["player"], question)
        self.assertEqual(tip.sources, ("city", "settlement"))

    @patch("tabletalk.strategy.ollama.generate")
    def test_unsupported_variant_never_calls_llm(self, generate):
        self.assertEqual(advise(self.index, "How should I win at Seafarers?").kind, "unsupported")
        generate.assert_not_called()

    @patch("tabletalk.strategy.ollama.generate")
    def test_no_advice_with_unusable_citations(self, generate):
        for ids in ([], ["fake-rule"]):
            with self.subTest(ids=ids):
                generate.return_value = {"kind": "advice", "move": "Build a city.",
                                         "reason": "Increase production.", "tradeoff": "It costs resources.", "sources": ids}
                with self.assertRaises(CoachError):
                    advise(self.index, "Should I build a city?")

    @patch("tabletalk.strategy.ollama.generate", side_effect=local_response)
    def test_coach_ui_is_separate_from_rules(self, generate):
        app = AppTest.from_file(str(APP), default_timeout=10).run()
        app.button(key="pick_catan").click().run()
        app.chat_input[0].set_value("When do I win?").run()
        generate.assert_not_called()
        app.segmented_control(key="mode").set_value("Strategy").run()
        app.chat_input[0].set_value("Should I upgrade to a city or build another settlement?").run()
        self.assertIn("Rules behind this advice", [x.label for x in app.expander])
        self.assertIn("#page=5", " ".join(x.value for x in app.markdown))
        app.run()
        generate.assert_called_once()
        generate.side_effect = CoachError("The local coach didn’t respond.")
        app.chat_input[0].set_value("What if I have no more room?").run()
        self.assertEqual(len(app.error), 1)
        app.segmented_control(key="mode").set_value("Ask a rule").run()
        self.assertIn("your own turn", " ".join(x.value for x in app.markdown))
        self.assertFalse(app.exception)
