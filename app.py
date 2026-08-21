from flask import Flask, jsonify, request
from database import init_db, create_user, get_db
from datetime import datetime

app = Flask(__name__)

# ساخت دیتابیس هنگام اجرای برنامه
init_db()


@app.route("/")
def home():
    return "بخش پشتیبانی EarnZood در حال اجرا است!"


@app.route("/api/test")
def test():
    return jsonify({
        "success": True,
        "message": "رابط برنامه‌نویسی EarnZood در حال کار است"
    })


@app.route("/api/user", methods=["POST"])
def register_user():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "اطلاعاتی دریافت نشد"
        }), 400

    telegram_id = data.get("telegram_id")
    username = data.get("username")
    first_name = data.get("first_name")

    if not telegram_id:
        return jsonify({
            "success": False,
            "message": "Telegram ID موجود نیست"
        }), 400

    create_user(
        telegram_id,
        username,
        first_name
    )

    conn = get_db()

    user = conn.execute("""
        SELECT telegram_id, username, first_name, balance, referral_count
        FROM users
        WHERE telegram_id = ?
    """, (telegram_id,)).fetchone()

    conn.close()

    return jsonify({
        "success": True,
        "user": dict(user)
    })


if __name__ == "__main__":
    app.run()
