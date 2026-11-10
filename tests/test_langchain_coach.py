"""Run the real prompt, ChatOllama and parser; replace only the HTTP transport."""
import json
import unittest
from unittest.mock import patch

import httpx

from tabletalk.retrieval.index import RuleIndex
from tabletalk.strategy.coach import advise
from tabletalk.strategy.ollama import CoachError


class LangChainCoachTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = RuleIndex("pandemic")

    @staticmethod
    def response(content, reason="stop"):
        return httpx.Response(200, json={"model": "gemma4:12b", "done": True, "done_reason": reason,
                                         "message": {"role": "assistant", "content": content}})

    @patch("httpx.HTTPTransport.handle_request", autospec=True)
    def test_one_local_request_with_game_evidence_and_scoped_schema(self, transport):
        tip = {"kind": "advice", "move": "Discover the cure.", "reason": "It is the fourth cure.",
               "tradeoff": "Treating delays the win.", "sources": ["win", "scientist"]}
        transport.return_value = self.response(json.dumps(tip))
        question = "I'm the Scientist at a station, holding four blue cards. Blue is the final cure. Treat or cure?"
        self.assertEqual(advise(self.index, question).sources, ("win", "scientist"))
        transport.assert_called_once()
        _, request = transport.call_args.args
        self.assertEqual(str(request.url), "http://127.0.0.1:11434/api/chat")
        body = json.loads(request.content)
        system, user = body["messages"]
        self.assertEqual((system["role"], user["role"]), ("system", "user"))
        self.assertIn("Pandemic", system["content"])
        evidence = json.loads(user["content"])
        self.assertEqual(evidence["latest_question"], question)
        self.assertEqual(body["format"]["properties"]["sources"]["items"]["enum"],
                         [r["id"] for r in evidence["sources"]])

    @patch("httpx.HTTPTransport.handle_request", autospec=True)
    def test_report_unavailable_model_or_unusable_output(self, transport):
        for response, error in ((httpx.Response(404, json={"error": "model missing"}), "couldn’t find"),
                                (self.response("{}", "length"), "ran out of space"),
                                (self.response("not JSON"), "unreadable")):
            with self.subTest(error=error):
                transport.return_value = response
                with self.assertRaisesRegex(CoachError, error):
                    advise(self.index, "Should we treat or discover a cure?")
