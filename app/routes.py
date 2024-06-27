from app import app
from flask import render_template, request, redirect, url_for, send_file
import io
import pandas as pd
from app.model import Product

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/extract', methods=['POST', 'GET'])
def extract():
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        product = Product(product_id)
        if product.extract_opinions():
            return redirect(url_for('product', product_id=product_id))
        return render_template("extract.html", error="Product has no opinions or does not exist")
    return render_template("extract.html")

@app.route('/products')
def products():
    products = Product.list_products()
    return render_template("products.html", products=products)

@app.route('/author')
def author():
    return render_template("author.html")

@app.route('/product/<product_id>')
def product(product_id):
    opinions = Product.get_product_opinions(product_id)
    if opinions is not None:
        return render_template("product.html", product_id=product_id, opinions=opinions.to_html(classes="table table-warning table-striped"), table_id="opinions", index=False)
    return redirect(url_for('extract'))

@app.route('/charts/<product_id>')
def charts(product_id):
    return render_template('charts.html', product_id=product_id)

@app.route('/download_json/<product_id>')
def download_json(product_id):
    return send_file(f"./data/opinions/{product_id}.json", "text/json", as_attachment=True)

@app.route('/download_csv/<product_id>')
def download_csv(product_id):
    opinions = Product.get_product_opinions(product_id)
    buffer = io.BytesIO(opinions.to_csv(index=False).encode())
    return send_file(buffer, "text/csv", as_attachment=True, download_name=f"{product_id}.csv")

@app.route('/download_xlsx/<product_id>')
def download_xlsx(product_id):
    opinions = Product.get_product_opinions(product_id)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer) as writer:
        opinions.to_excel(writer, index=False)
    buffer.seek(0)
    return send_file(buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name=f"{product_id}.xlsx")
