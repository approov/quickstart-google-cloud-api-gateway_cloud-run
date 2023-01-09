# @link https://cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-service#writing

import os

from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def hello_world():
    return jsonify({"message": "Hello, World!"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
