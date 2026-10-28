"""Parsing and checking AI output before it is stored.

The AI's answer is untrusted. It must be valid JSON in the requested shape,
text is length-limited, unknown fact references are removed, and claims that
the confirmed facts do not support are flagged for the user to check:
numbers (prices, percentages, years, quantities) and words that usually
signal unsupported claims ("best", "award", "guarantee", "bora zaidi",
"tuzo", "uhakika", ...). Flags do not block a draft; they must be
acknowledged before it can be approved.
"""

import json
import re

MAX_CONCEPTS = 3
MAX_SCENES = 10
TEXT_LIMITS = {
    "title": 120, "angle": 300, "key_message": 300, "why_it_fits": 300,
    "voiceover": 400, "on_screen_text": 80, "visual": 300,
    "headline": 120, "caption": 800, "call_to_action": 200, "hashtag": 40,
}

NUMBER_PATTERN = re.compile(r"\d[\d,.\s]*\d|\d")
RISKY_PHRASES = [
    # English
    "best", "number one", "#1", "no. 1", "leading", "award", "winner", "winning", "certified",
    "certificate", "accredited", "guarantee", "guaranteed", "cheapest", "lowest price", "free",
    "discount", "% off", "offer", "sale", "years of experience", "trusted by", "customers say",
    "rated", "five-star", "5-star", "official", "approved by", "only", "fastest", "100%",
    # Kiswahili
    "bora zaidi", "namba moja", "nambari moja", "tuzo", "mshindi", "cheti", "imethibitishwa",
    "uhakika", "hakikisho", "bei nafuu zaidi", "bure", "punguzo", "ofa", "miaka ya uzoefu",
    "wateja wanasema", "pekee", "haraka zaidi", "rasmi",
]


class InvalidOutput(ValueError):
    pass


def parse_json_object(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise InvalidOutput("not valid JSON") from exc
    if not isinstance(data, dict):
        raise InvalidOutput("not a JSON object")
    return data


def _text(value, limit_key, required=True):
    if not isinstance(value, str) or not value.strip():
        if required:
            raise InvalidOutput(f"missing {limit_key}")
        return ""
    return " ".join(value.split())[: TEXT_LIMITS[limit_key]]


def _fact_ids(value, known_refs, warnings):
    refs = []
    for ref in value if isinstance(value, list) else []:
        if not isinstance(ref, str):
            continue
        if ref not in known_refs:
            warnings.append(ref)
        elif ref not in refs:
            refs.append(ref)
    return refs


def clean_concepts(data, known_refs):
    concepts = data.get("concepts")
    if not isinstance(concepts, list) or not concepts:
        raise InvalidOutput("no concepts")
    unknown = []
    cleaned = []
    for item in concepts[:MAX_CONCEPTS]:
        if not isinstance(item, dict):
            raise InvalidOutput("concept is not an object")
        cleaned.append({
            "title": _text(item.get("title"), "title"),
            "angle": _text(item.get("angle"), "angle"),
            "key_message": _text(item.get("key_message"), "key_message"),
            "why_it_fits": _text(item.get("why_it_fits"), "why_it_fits", required=False),
            "fact_ids": _fact_ids(item.get("fact_ids"), known_refs, unknown),
        })
    return cleaned, unknown


def clean_script(data, known_refs):
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise InvalidOutput("no scenes")
    unknown = []
    cleaned_scenes = []
    for scene in scenes[:MAX_SCENES]:
        if not isinstance(scene, dict):
            raise InvalidOutput("scene is not an object")
        duration = scene.get("duration_seconds")
        cleaned_scenes.append({
            "voiceover": _text(scene.get("voiceover"), "voiceover", required=False),
            "on_screen_text": _text(scene.get("on_screen_text"), "on_screen_text", required=False),
            "visual": _text(scene.get("visual"), "visual", required=False),
            "duration_seconds": duration if isinstance(duration, int) and 1 <= duration <= 30 else 5,
            "fact_ids": _fact_ids(scene.get("fact_ids"), known_refs, unknown),
        })
    if not any(s["voiceover"] or s["on_screen_text"] for s in cleaned_scenes):
        raise InvalidOutput("scenes have no text")
    hashtags = []
    for tag in data.get("hashtags") if isinstance(data.get("hashtags"), list) else []:
        if isinstance(tag, str):
            tag = re.sub(r"[^\w]", "", tag.lstrip("#"))[: TEXT_LIMITS["hashtag"]]
            if tag and tag not in hashtags:
                hashtags.append(tag)
    script = {
        "title": _text(data.get("title"), "title"),
        "scenes": cleaned_scenes,
        "headline": _text(data.get("headline"), "headline", required=False),
        "caption": _text(data.get("caption"), "caption", required=False),
        "call_to_action": _text(data.get("call_to_action"), "call_to_action", required=False),
        "hashtags": hashtags[:10],
        "fact_ids": _fact_ids(data.get("fact_ids"), known_refs, unknown),
    }
    return script, unknown


def script_texts(script):
    """Yield (location, text) pairs for every user-visible text in a script."""
    for name in ("title", "headline", "caption", "call_to_action"):
        if script.get(name):
            yield name, script[name]
    for number, scene in enumerate(script.get("scenes", []), start=1):
        for name in ("voiceover", "on_screen_text"):
            if scene.get(name):
                yield f"scene {number} {name}", scene[name]
    for tag in script.get("hashtags", []):
        yield "hashtags", tag


def concept_texts(concept):
    for name in ("title", "angle", "key_message"):
        if concept.get(name):
            yield name, concept[name]


def _digits(text):
    return re.sub(r"\D", "", text)


def find_unsupported_claims(texts, facts):
    """Return flags for numbers and risky phrases not supported by the facts."""
    fact_text = " ".join(f["value"] for f in facts).casefold()
    # Numbers are read from each fact separately so that numbers from two
    # different facts are never joined together.
    fact_digits = {_digits(n) for f in facts for n in NUMBER_PATTERN.findall(f["value"])}
    fact_digits.discard("")
    flags = []
    seen = set()
    for location, text in texts:
        lowered = text.casefold()
        for number in NUMBER_PATTERN.findall(text):
            digits = _digits(number)
            # Exact match only: "15" must not pass because a fact says "15000".
            if digits and digits not in fact_digits:
                key = ("number", digits)
                if key not in seen:
                    seen.add(key)
                    flags.append({
                        "code": "unsupported_number",
                        "location": location,
                        "text": number.strip(),
                        "message": f"The number “{number.strip()}” is not in your confirmed information.",
                    })
        for phrase in RISKY_PHRASES:
            pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)" if phrase[0].isalnum() else re.escape(phrase)
            if re.search(pattern, lowered) and phrase not in fact_text:
                key = ("phrase", phrase)
                if key not in seen:
                    seen.add(key)
                    flags.append({
                        "code": "unsupported_claim",
                        "location": location,
                        "text": phrase,
                        "message": f"“{phrase}” may be a claim that is not in your confirmed information.",
                    })
    return flags
