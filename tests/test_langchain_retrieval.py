"""Check the LangChain boundary that both rules and strategy use."""
import unittest

from langchain_core.documents import Document

from tabletalk.retrieval.index import RuleIndex


class LangChainRetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catan = RuleIndex("catan")
        cls.pandemic = RuleIndex("pandemic")

    def test_documents_carry_the_reviewed_text_and_actual_source(self):
        for index, question, key, pages in (
            (self.catan, "Can five people use just the base box?", "players", [0]),
            (self.pandemic, "How many cards does the Scientist need for a cure?", "scientist", [8, 4]),
        ):
            with self.subTest(game=index.game.id):
                doc = index.retrieve(question, k=1)[0]
                rule = index.by_id[key]
                self.assertIsInstance(doc, Document)
                self.assertEqual((doc.id, doc.page_content), (f"{index.game.id}:{key}", rule.answer))
                self.assertEqual(doc.metadata["source"], rule.url)
                self.assertEqual([doc.metadata["page"], *doc.metadata["extra_pages"]], pages)

    def test_result_limits_are_independent_on_the_same_index(self):
        question = "What makes it a win for our table?"
        short = self.pandemic.as_retriever(k=2)
        long = self.pandemic.as_retriever(k=4)
        docs = long.invoke(question)
        self.assertEqual(len(docs), 4)
        self.assertEqual(short.invoke(question), docs[:2])
        direct = self.pandemic.search(question, k=4)
        self.assertEqual(
            [(d.metadata["rule_id"], d.metadata["score"], d.metadata["dense"],
              d.metadata["coverage"], d.metadata["unfamiliar"]) for d in docs],
            [(h.rule.id, h.score, h.dense, h.coverage, h.unfamiliar) for h in direct],
        )
        self.assertEqual(len(self.pandemic.retrieve(question)), 3)
        self.assertEqual(short.invoke(""), [])
