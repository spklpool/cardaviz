import time


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
    start = time.time()
    loaded_file = open("data/" + pool_ticker.upper() + ".json", "r").read()
    print(f'Time: {time.time() - start}')
    return loaded_file


