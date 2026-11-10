"""Normalize table language in both questions and source text before retrieval."""
import re

STOP = set("""
a an and are as at be been being but by can catan could did do does during for from
game get gets had happen happens has have how i if in into is it its me might my of
on or our play please rule rules should still than that the their them there these
this those to us use was we were what when which who will with would you your
""".split())

OTHER_OWNER = re.compile(r"\b(?:somebody else|someone else|an opponent|another person)['’]s\b", re.I)


def semantic_text(text: str) -> str:
    """Use natural wording for MiniLM, preserving the actor and roll/turn distinction."""
    text = OTHER_OWNER.sub("another player's", text)
    return re.sub(r"(another player['’]s) dice roll\b", r"\1 roll", text, flags=re.I)


# Multiword expressions carry more meaning together. Keep them intact for BM25.
PHRASES = {
    "offturn roll": r"another player['’]s (?:dice )?roll",
    "offturn turn": r"another player['’]s turn|not (?:my|your) turn|between turns",
    "shortage": r"too few|not enough|(?:isn['’]t|aren['’]t) enough|run(?:s|ning)? (?:short|out)|short supply|can(?:not|['’]t) pay everyone",
    "distance": r"(?:far|close) (?:apart|together)|(?:minimum|required) (?:gap|spacing)|next to (?:one )?another",
    "beginner": r"(?:fixed|recommended|starter|printed) (?:board|layout|map)",
    "variable": r"(?:random(?:ized)?|custom|shuffled) (?:board|layout|map|island)",
}

FAMILIES = {
    "player": "players people person friends folks",
    "harbor": "port ports harbors harbours harbour",
    "generic": "regular ordinary generic nonspecialized",
    "color": "colour colours colors",
    "settlement": "settlements village villages house houses",
    "city": "cities town towns",
    "lumber": "wood", "wool": "sheep", "grain": "wheat", "ore": "stone",
    "7": "seven", "10": "ten", "2": "two", "3": "three", "4": "four",
    "5": "five", "6": "six", "9": "nine",
    "win": "winning winner", "trade": "swap swaps swapped swapping exchange exchanges traded trading trades",
    "roll": "rolling rolled rolls", "build": "building builds built",
    "produce": "production produces produced producing yield yields",
    "collect": "collects collected collecting receive receives received take takes pickup",
    "hex": "hexes tile tiles", "distance": "spacing spaced separation",
    "owed": "due entitled", "order": "sequence phases",
    "identical": "matching identical", "resource": "resources",
}
CANONICAL = {v: root for root, forms in FAMILIES.items() for v in forms.split()}
EXPRESSIONS = [(re.compile(rf"\b(?:{pattern})\b"), root) for root, pattern in PHRASES.items()]


PANDEMIC_FAMILIES = {
    "player": "players people person friends teammates", "win": "wins winning victory",
    "lose": "losing loss loses lost", "disease": "diseases", "city": "cities",
    "epidemic": "epidemics", "outbreak": "outbreaks", "treat": "treated treating treatment",
    "cure": "cures cured curing", "eradicate": "eradicated eradicating eradication",
    "color": "colour colours colors", "hand": "hands", "draw": "drawing drew",
}
PANDEMIC_WORDS = {v: root for root, forms in PANDEMIC_FAMILIES.items() for v in forms.split()}


def words(text: str, game_id: str = "catan") -> list[str]:
    text = semantic_text(text).casefold()
    catan = game_id == "catan"
    families = CANONICAL if catan else PANDEMIC_WORDS
    for pattern, root in (EXPRESSIONS if catan else ()):
        text = pattern.sub(root, text)
    tokens = re.findall(r"[a-z0-9]+", text)
    result = []
    for token in tokens:
        if token in STOP or token == game_id or len(token) == 1 and not token.isdigit():
            continue
        default = token[:-1] if len(token) > 3 and token.endswith("s") and not token.endswith("ss") else token
        result.append(families.get(token, default))
    return result
