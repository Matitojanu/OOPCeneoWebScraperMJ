from app import app
from flask import render_template, request, redirect, url_for
import os
import json
import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from app.utils import extract_content, score, selectors, transformations, translate

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/extract', methods=['POST', 'GET'])
def extract():
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        url = f"https://www.ceneo.pl/{product_id}"
        response = requests.get(url)
        if response.status_code == requests.codes['ok']:
            page_dom = BeautifulSoup(response.text, "html.parser")
            opinions_count = extract_content(page_dom, 'a.product-review__link > span')
            if opinions_count:
                all_opinions = []
                url = f"https://www.ceneo.pl/{product_id}#tab=reviews"
                while(url):
                    response = requests.get(url)
                    response.status_code
                    page_dom = BeautifulSoup(response.text, "html.parser")
                    opinions = page_dom.select('div.js_product-review')
                    for opinion in opinions:
                        single_opinion = {
                                key: extract_content(opinion, *value)
                                    for key, value in selectors.items()
                        }
                        for key, value in transformations.items():
                            single_opinion[key] = value(single_opinion[key])
                        all_opinions.append(single_opinion)
                    try:    
                        url = "https://www.ceneo.pl"+extract_content(page_dom,"a.pagination__next", "href")
                    except TypeError:
                        url = None   
                if not os.path.exists("app/data"):
                    os.mkdir("app/data")
                if not os.path.exists("app/data/opinions"):
                    os.mkdir("app/data/opinions")
                with open(f"app/data/opinions/{product_id}.json", "w", encoding="UTF-8") as jf:
                    json.dump(all_opinions, jf, indent=4, ensure_ascii=False)
                MAX_SCORE = 5
                opinions = pd.DataFrame.from_dict(all_opinions)
                opinions.score = opinions.score.apply(lambda s: round(s*MAX_SCORE,1))
                statistics = {
                    'product_id' : product_id,
                    'product_name' : extract_content(page_dom, "h1"),
                    'opinions_count' : opinions_count,
                    'pros_count' : int(opinions.pros.astype(bool).sum()),
                    'cons_count' : int(opinions.cons.astype(bool).sum()),
                    'average_score' : opinions.score.mean().round(3),
                    'score_distribution' : opinions.score.value_counts().reindex(np.arange(0.5,5.5,0.5)).to_dict(),
                    'recommendation_distribution' : opinions.recommendation.value_counts(dropna=False).reindex([1,np.nan,0]).to_dict()
                }
                if not os.path.exists("app/data/statistics"):
                    os.mkdir("app/data/statistics")
                with open(f"app/data/statistics/{product_id}.json", "w", encoding="UTF-8") as jf:
                    json.dump(statistics, jf, indent=4, ensure_ascii=False)
                return redirect(url_for('product', product_id=product_id))
            return render_template("extract.html", error = "Product has no opinions")
        return render_template("extract.html", error = "Product does not exist")
    return render_template("extract.html")

@app.route('/products')
def products():
    products_list = [filename.split(".")[0] for filename in os.listdir("app/data/statistics")]
    products = []
    for product_id in products_list:
        with open(f"app/data/statistics/{product_id}.json", "r", encoding="UTF-8") as jf:
            statistics = json.load(jf)
            products.append(statistics)
    return render_template("products.html", products=products)

@app.route('/author')
def author():
    return render_template("author.html")

@app.route('/product/<product_id>')
def product(product_id):
    if os.path.exists("app/data/opinions"):
        with open(f"app/data/opinions/{product_id}.json", "r", encoding="UTF-8") as jf:            
            opinions = json.load(jf)
        return render_template("product.html", product_id = product_id, opinions = opinions)
    return redirect(url_for('extract.html'))