
from flask import Flask, render_template


app = Flask(__name__)


#TODO: add a landing page here
@app.route("/")
def get_landing_page():
    return "cardaviz"


@app.route("/pools/<pool_ticker>")
def get_pool(pool_ticker):
    return render_template('perfchart.html', pool_ticker=pool_ticker)


@app.route("/pools/<pool_ticker>/epochs")
def get_pool_epochs(pool_ticker):
    if len(pool_ticker) < 10:
        pool_json_path = "data/" + pool_ticker.upper() + ".json"
    return open(pool_json_path, "r").read()


