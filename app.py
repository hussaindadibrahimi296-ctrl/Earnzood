from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return "EarnZood Backend is Running!"


@app.route("/api/test")
def test():
    return jsonify({
        "success": True,
        "message": "EarnZood API is working"
    })


if __name__ == "__main__":
    app.run()
