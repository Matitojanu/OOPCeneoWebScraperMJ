import os
import json
import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator


class Opinion:
    selectors = {
        "opinion_id": (None, "data-entry-id"),
        "author": ("span.user-post__author-name",),
        "recommendation": ("span.user-post__author-recomendation > em",),
        "score": ("span.user-post__score-count",),
        "content": ("div.user-post__text",),
        "pros": ("div.review-feature__title--positives ~ div.review-feature__item", None, True),
        "cons": ("div.review-feature__title--negatives ~ div.review-feature__item", None, True),
        "helpful": ("button.vote-yes > span",),
        "unhelpful": ("button.vote-no > span",),
        "publish_date": ("span.user-post__published > time:nth-child(1)", "datetime"),
        "purchase_date": ("span.user-post__published > time:nth-child(2)", "datetime"),
    }

    transformations = {
        "recommendation": lambda r: True if r == "Polecam" else False if r == "Nie polecam" else None,
        "score": lambda score: float(score.split("/")[0].replace(",", ".")) / float(score.split("/")[1]),
        "helpful": int,
        "unhelpful": int,
        "content": lambda text: Opinion.translate(text),
        "pros": lambda text: Opinion.translate(text),
        "cons": lambda text: Opinion.translate(text)
    }

    def __init__(self, raw_opinion):
        self.raw_opinion = raw_opinion
        self.opinion = self.transform()

    def extract_content(self, ancestor, selector=None, attribute=None, return_list=False):
        if selector:
            if return_list:
                if attribute:
                    return [tag[attribute].strip() for tag in ancestor.select(selector)]
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

    def translate(text, lang_from="pl", lang_to="en"):
        if isinstance(text, list):
            return [GoogleTranslator(source=lang_from, target=lang_to).translate(t) for t in text]
        return GoogleTranslator(source=lang_from, target=lang_to).translate(text)

    def transform(self):
        transformed_opinion = {
            key: self.extract_content(self.raw_opinion, *value)
            for key, value in self.selectors.items()
        }
        for key, value in self.transformations.items():
            transformed_opinion[key] = value(transformed_opinion[key])
        return transformed_opinion

    def get_opinion(self):
        return self.opinion

class Scraper:
    BASE_URL = "https://www.ceneo.pl/"

    def __init__(self, product_id):
        self.product_id = product_id
        self.opinions = []
        self.product_name = None

    def fetch_page(self, url):
        response = requests.get(url)
        if response.status_code == requests.codes['ok']:
            return BeautifulSoup(response.text, "html.parser")
        return None

    def scrape_product_name(self):
        url = f"{self.BASE_URL}{self.product_id}"
        page_dom = self.fetch_page(url)
        if page_dom:
            self.product_name = page_dom.select_one("h1").text.strip()

    def scrape_opinions(self):
        url = f"{self.BASE_URL}{self.product_id}#tab=reviews"
        while url:
            page_dom = self.fetch_page(url)
            if page_dom is None:
                break
            opinions = page_dom.select('div.js_product-review')
            for opinion in opinions:
                opinion_instance = Opinion(opinion)
                self.opinions.append(opinion_instance.get_opinion())

            try:
                url = self.BASE_URL + page_dom.select_one("a.pagination__next")['href']
            except TypeError:
                url = None

    def get_opinions(self):
        self.scrape_product_name()
        self.scrape_opinions()
        return self.opinions, self.product_name

class Product:
    def __init__(self, product_id):
        self.product_id = product_id
        self.scraper = Scraper(product_id)
        self.opinions = []
        self.product_name = None

    def extract_opinions(self):
        self.opinions, self.product_name = self.scraper.get_opinions()
        if not self.opinions:
            return False  # Indicate failure if no opinions are found
        self.save_opinions()
        self.save_statistics()
        return True  # Indicate success if opinions are extracted and saved

    def save_opinions(self):
        if not os.path.exists("app/data/opinions"):
            os.makedirs("app/data/opinions")
        with open(f"app/data/opinions/{self.product_id}.json", "w", encoding="UTF-8") as jf:
            json.dump(self.opinions, jf, indent=4, ensure_ascii=False)

    def save_statistics(self):
        MAX_SCORE = 5
        opinions_df = pd.DataFrame.from_dict(self.opinions)
        opinions_df['score'] = opinions_df['score'].apply(lambda s: round(s * MAX_SCORE, 1))

        statistics = {
            'product_id': self.product_id,
            'product_name': self.product_name,
            'opinions_count': len(self.opinions),
            'pros_count': int(opinions_df.pros.astype(bool).sum()),
            'cons_count': int(opinions_df.cons.astype(bool).sum()),
            'average_score': opinions_df.score.mean().round(3),
            'score_distribution': opinions_df.score.value_counts().reindex(np.arange(0.5, 5.5, 0.5)).to_dict(),
            'recommendation_distribution': opinions_df.recommendation.value_counts(dropna=False).reindex([1, np.nan, 0]).to_dict()
        }

        if not os.path.exists("app/data/statistics"):
            os.makedirs("app/data/statistics")

        with open(f"app/data/statistics/{self.product_id}.json", "w", encoding="UTF-8") as jf:
            json.dump(statistics, jf, indent=4, ensure_ascii=False)

    def list_products():
        products_list = [filename.split(".")[0] for filename in os.listdir("app/data/statistics")]
        products = []
        for product_id in products_list:
            with open(f"app/data/statistics/{product_id}.json", "r", encoding="UTF-8") as jf:
                statistics = json.load(jf)
                products.append(statistics)
        return products

    def get_product_opinions(product_id):
        filepath = f"app/data/opinions/{product_id}.json"
        if os.path.exists(filepath):
            return pd.read_json(filepath)
        return None