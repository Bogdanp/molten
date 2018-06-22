from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/")
def index():
    return jsonify({"message": "hello!"})


@app.route("/hello/<name>/<int:age>")
def hello(name, age):
    return jsonify(f"Hi {name}! I hear you're {age} years old.")


@app.route("/echo", methods=["POST"])
def echo():
    return jsonify(request.get_json())
