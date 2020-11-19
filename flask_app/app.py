from flask import Flask, request, render_template, jsonify, url_for
import json 
from recommend import recommend
import os
import pandas as pd

app = Flask(__name__, template_folder='templates')

df = pd.read_csv("static/data/appdata.csv")
usernames = df["name"].values.tolist()
df = df.set_index("name")

@app.route("/")
def index():
    return render_template('index.html', data=json.dumps(usernames))

def unique(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

@app.route('/', methods=['POST'])
def my_form_post():
    text = request.form['tags']
    follows = [x.strip() for x in text.split(",") if x.strip() in usernames]
    follows = unique(follows)
    recs = recommend(follows, N=9)
    rec_data = df.loc[recs].reset_index().values.tolist()
    rec_data = enumerate(rec_data, start=1)
    return render_template('results.html', data=json.dumps(usernames), recs=rec_data)

if __name__ == "__main__":
    app.run(debug=True)