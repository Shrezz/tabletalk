"""Exercise the actual Streamlit flow rather than calling UI helper functions."""
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


class TableFlow(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(APP), default_timeout=15).run()
        self.app.button(key="pick_catan").click().run()

    def test_ruling_citation_and_scope(self):
        self.app.chat_input[0].set_value("When does a person win?").run()
        text = " ".join(x.value for x in self.app.markdown)
        self.assertIn("your own turn", text)
        self.assertIn("#page=5", text)
        self.app.chat_input[0].set_value("Can I build a ship in Seafarers?").run()
        self.assertIn("don’t have a source", self.app.markdown[-1].value)
        self.assertFalse(self.app.exception)

    @patch("tabletalk.strategy.ollama.generate", side_effect=AssertionError("Setup needs no LLM"))
    def test_basic_setup_in_both_chats(self, generate):
        for mode in ("Ask a rule", "Strategy"):
            with self.subTest(mode=mode):
                self.app.segmented_control(key="mode").set_value(mode).run()
                self.app.chat_input[0].set_value("Whats needed for basic setup>").run()
                text = " ".join(m.value for m in self.app.markdown)
                for part in ("19 terrain hexes", "2 roads", "robber on the desert",
                             "oldest player", "#page=3", "#page=12"):
                    self.assertIn(part, text)
                self.assertFalse(self.app.exception)
        generate.assert_not_called()

    def test_setup_and_refresher(self):
        self.app.segmented_control(key="mode").set_value("Set us up").run()
        self.assertIn("#page=3", self.app.markdown[-1].value)
        for label in ("Place the starting pieces", "Prepare the supply",
                      "Take starting resources", "A turn in three steps"):
            next(b for b in self.app.button if b.label == "Next step").click().run()
            self.assertEqual(self.app.subheader[0].value, label)
        self.app.segmented_control(key="mode").set_value("Quick refresher").run()
        self.assertEqual(len(self.app.subheader), 4)
        self.assertFalse(self.app.exception)


if __name__ == "__main__":
    unittest.main()
