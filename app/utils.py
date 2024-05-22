from deep_translator import GoogleTranslator

def extract_content(ancestor, selector=None, attribute=None, return_list=False):
    if selector:
        if return_list:
            if attribute:
                return [tag.text.strip() for tag in ancestor.select(selector)]
            return [tag.text.strip() for tag in ancestor.select(selector)]
        if attribute:
            try:
                return ancestor.select_one(selector)[attribute].strip()
            except TypeError:
                return None
        try:
            return ancestor.select_one(selector).text.strip()
        except AttributeError:
            return None
    if attribute:
        return ancestor[attribute]
    return ancestor.text.strip()

def score(score:str) -> float:
    s = score.split("/")
    return float(s[0].replace(",","."))/float(s[1])

def translate(text, lang_from = 'pl', lang_to="en"):
    if isinstance(text, list):
        return [GoogleTranslator(source=lang_from, target=lang_to).translate(t) for t in text]
    return GoogleTranslator(source=lang_from, target=lang_to).translate(text)

selectors = {
    "opinion_id" : (None, "data-entry-id",),
    "author" : ("span.user-post__author-name",),
    "recommendation" : ("span.user-post__author-recomendation > em",),
    "score" : ("span.user-post__score-count",),
    "content" : ("div.user-post__text",),
    "pros" : ("div.review-feature__title--positives ~ div.review-feature__item", None, True),
    "cons" : ("div.review-feature__title--negatives ~ div.review-feature__item", None, True),
    "helpful" : ("button.vote-yes > span",),
    "unhelpful" : ("button.vote-no > span",),
    "publish_date" : ("span.user-post__published > time:nth-child(1)", "datetime"),
    "purchase_date" : ("span.user-post__published > time:nth-child(2)", "datetime"),
}

transformations = {
    "recommendation": lambda r: True if r == "Polecam" else False if r == "Nie polecam" else None,
    "score": score,
    "helpful":int,
    "unhelpful":int,
}