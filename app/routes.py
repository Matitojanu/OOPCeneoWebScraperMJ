from app import app

@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"

@app.route('/hello')
@app.route('/hello/<name>')
def hello(name="Anonymous"):
    return f"Hello, {name}!"