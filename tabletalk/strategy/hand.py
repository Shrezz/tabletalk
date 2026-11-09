"""Budget evidence only when the player explicitly lists a complete hand."""
import re

# Base-game build costs, pp. 4–5. Can pay is not the same as legal placement.
COSTS = {"road": {"brick": 1, "lumber": 1},
         "settlement": {"brick": 1, "lumber": 1, "wool": 1, "grain": 1},
         "city": {"ore": 3, "grain": 2},
         "development": {"ore": 1, "wool": 1, "grain": 1}}
NAMES = {"wheat": "grain", "wood": "lumber", "sheep": "wool"}
RESOURCE = r"brick|lumber|wool|grain|ore|wheat|wood|sheep"
ITEM = re.compile(rf"(\d{{1,2}})\s+({RESOURCE})\b", re.I)
HAND = re.compile(r"\b(?:my (?:entire |whole |current )?hand (?:is|contains)|i (?:only have|have only)|all i have is)\s+([^.;?!]+)", re.I)
CHANGE = re.compile(r"\b(traded|drew|spent|bought|built|collected|discarded|received|lost|gained|got|i have|i had|my hand|now have|new (?:turn|game)|next game)\b", re.I)


def complete_hand(question):
    match = HAND.search(question)
    if not match:
        return None
    listing = match[1].lower()
    if not ITEM.search(listing) or re.sub(r"\band\b|[\s,+]", "", ITEM.sub("", listing)):
        return None  # A partial, hypothetical or otherwise ambiguous list is not a budget.
    result = {}
    for count, noun in ITEM.findall(listing):
        key = NAMES.get(noun, noun)
        result[key] = result.get(key, 0) + int(count)
    return result


def build_plans(question, history):
    hand = complete_hand(question)
    from_previous = hand is None
    if hand is None and history and not (HAND.search(question) or CHANGE.search(question)):
        # Only carry a stated hand one turn, and label the assumption explicitly.
        hand = complete_hand(history[-1][0])
    if hand is None:
        return None
    decision = question if not history else history[-1][0] + " " + question
    if re.search(r"\b(initial|opening|setup|free|road building card)\b", decision, re.I):
        return None  # Standard paid-build costs do not apply to every placement.
    names = {"city": ("city|cities|upgrade", "upgrade a settlement to a city"),
             "settlement": ("settlement|settlements|village", "build a new settlement"),
             "road": ("roads?", "build a road"),
             "development": ("development", "buy a development card")}
    plans = {}
    for action, (pattern, label) in names.items():
        if not re.search(rf"\b(?:{pattern})\b", decision, re.I):
            continue
        cost = COSTS[action]
        missing = [f"{n - hand.get(r, 0)} {r}" for r, n in cost.items() if hand.get(r, 0) < n]
        if missing:
            plans[action] = f"Work toward the cards to {label}. With the hand you listed, you still need " + ", ".join(missing) + "."
        else:
            plans[action] = f"If placement and turn timing allow, {label}. Your stated hand covers the cost."
    if plans:
        plans["wait"] = "Keep your cards for now and reconsider after production or a trade."
    if from_previous:
        plans = {key: "Based on your last stated hand: " + text[0].lower() + text[1:]
                 for key, text in plans.items()}
    return plans or None
