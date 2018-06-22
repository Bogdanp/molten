from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return jsonify({"message": "hello!"})


@app.route("/helllo/<name>/<int:age>")
def hello(name, age):
    return jsonify(f"Hi {name}! I hear you're {age} years old.")
