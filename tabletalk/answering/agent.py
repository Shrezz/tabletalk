"""Select a single supported ruling; uncertainty produces topics, not a guessed answer."""
from dataclasses import dataclass
import re

from tabletalk.answering.scope import missing_context, out_of_scope
from tabletalk.catalog import Rule
from tabletalk.guides import is_basic_setup, setup_checklist
from tabletalk.retrieval.index import RuleIndex

REFERENCE = re.compile(r"\b(it|that|those|one of those)\b", re.I)
FOLLOW_UP = re.compile(r"\b(cost|worth|build|buy|play|reveal|move|produce|trade)\b", re.I)


@dataclass(frozen=True)
class Answer:
    text: str
    rule_id: str | None = None
    suggestions: tuple[str, ...] = ()
    guide_sources: tuple[str, ...] = ()


def ruling(rule: Rule) -> Answer:
    return Answer(rule.answer, rule.id)


def answer(index: RuleIndex, question: str, previous: Rule | None = None) -> Answer:
    if out_of_scope(index.game, question):
        return Answer(f"This shelf covers the {index.game.name} base game. I don’t have a source for that edition or variant.")
    if is_basic_setup(question, index.game.id):
        return Answer(setup_checklist(index), guide_sources=index.game.setup)
    query = question
    if previous and previous.game == index.game and REFERENCE.search(question) and FOLLOW_UP.search(question) and len(question.split()) < 10:
        query = f"{previous.title}: {question}"
    docs = index.retrieve(query)
    if docs and index.game.id == "catan" and (clarification := missing_context(question, docs[0].metadata["rule_id"])):
        prompt, topics = clarification
        return Answer(prompt, suggestions=topics)
    best = docs[0].metadata if docs else None
    if not best or best["score"] < .32 or best["coverage"] < .15:
        return Answer("I couldn’t find a rule that answers that in this edition. Try naming a piece, card, or action.")
    close = len(docs) > 1 and best["score"] - docs[1].metadata["score"] < .035
    # Showing a topic is lower risk than asserting that it answers the question.
    weak = best["score"] < .44 or best["coverage"] < .20 or (best["score"] < .48 and best["dense"] < .65)
    if weak or best["unfamiliar"] >= 2 or (close and best["score"] < .65):
        return Answer("These rules look related. Which one would you like to check?",
                      suggestions=tuple(d.metadata["rule_id"] for d in docs))
    return Answer(docs[0].page_content, best["rule_id"])
