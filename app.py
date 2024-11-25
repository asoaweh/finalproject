from flask import Flask
from flask import render_template

app = Flask(__name__)

data = {'term':'Flask', 'option1':'webserver', 'option2':'plot'}

@app.route("/")
def hello_world():
    return render_template('hello.html', msg=data)