# This (old) app version keeps track of the user's form input by saving their data in
# the Flask session object. The new version, which we think is an improvement,
# does this with dynamic URLs -- i.e. "./like/<username-1>+<username-2>+...".
# The issue with this older version is that you cannot "go back" to a previous 
# recommendation page because you lose the session data -- whereas if it's 
# stored in the URL then it is very easy to go back.

from flask import Flask, request, render_template, url_for, flash, session, redirect, json
from recommend import recommend
from utils import unique
import os
import pandas as pd
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import  ValidationError

# App initialization and configuration
app = Flask(__name__, template_folder='templates')
app.config["SECRET_KEY"] = "MYSECRETKEY" # will set this using environment variable during deployment
app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 10*10**6 # 10Mb limit

# Load global app data
df = pd.read_csv("data/appdata.csv") # streamer name, primary game, secondary game, followers, profile image...
usernames = df["name"].values.tolist() # list of streamer usernames in our database
df = df.set_index("name")

# Form for user input
def validate_form(form, field):
        follows = [x.strip() for x in field.data.split(",") if x.strip() in usernames]
        if len(follows) == 0:
            raise ValidationError("Invalid input syntax")

class UsernamesForm(FlaskForm):
    username_input = StringField("Usernames", validators=[validate_form])

# ------------- ROUTES --------------
@app.route('/', methods=['GET', 'POST'])
def index():
    # initialize FlaskForm from flask_wtf
    if request.method == "GET":
        # make form
        form = UsernamesForm()
        return render_template('index.html', data=json.dumps(usernames), recs=None, form=form)

    if request.method == "POST":
        # make form
        form = UsernamesForm(request.form)

        # validate form input
        if form.validate_on_submit():
            # if valid, get recommendations
            query = form.username_input.data
            session["query"] = query
            return redirect(url_for('results'))

        else:
            # flash error message
            flash('Enter a valid username')

            return redirect(url_for('index'))
    
# Recommendation grid
@app.route('/results', methods=['GET'])
def results():
    if "query" in session:
        query = session["query"]
        follows = [x.strip() for x in query.split(",") if x.strip() in usernames]
        del session["query"] 

        follows = unique(follows)
        recs = recommend(follows, N=9)
        rec_data = df.loc[recs].reset_index().values.tolist()
        rec_data = list(enumerate(rec_data, start=1)) # data to display
    
        return render_template('results.html', data=json.dumps(usernames), recs=rec_data, form=UsernamesForm())
    
    else:
        return redirect(url_for('index'))

# API version -- allows a limit of 20 recommendations
@app.route('/api', methods=['GET'])
def api():
    # parse request arguments
    if "streamers" not in request.args:
        return {"error":"Invalid query."}
    text = request.args["streamers"]
    text = text[:1000] # cap "streamers" argument at 1000 characters
    if "limit" not in request.args:
        N = 10
    else: 
        N = request.args["limit"]
        try: 
            N = int(N)
        except ValueError:
            N = 10
        N = min(N, 20)

    # check for matches
    follows = [x.strip() for x in text.split(",") if x.strip() in usernames]

    # get recommendations
    if len(follows) > 0:
        follows = unique(follows)
        recs = recommend(follows, N=N)
        rec_data = df.loc[recs].reset_index() # reorder columns
        rec_data = json.loads(rec_data.to_json(orient="records"))

        return {"results": rec_data}

    # no matches, return error message
    else:
        return {"results":[], "error":"Query does not match any streamers in our database. " 
        + "Query is case-sensitive and underscores should be replaced with spaces (e.g. Riot_Games -> Riot Games)."}
            
if __name__ == "__main__":
    app.run(debug=False)