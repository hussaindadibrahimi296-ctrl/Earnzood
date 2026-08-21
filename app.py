from flask import Flask, jsonify, request
from flask_cors import CORS
from database import init_db, create_user, get_db

app = Flask(__name__)

# فعال‌سازی CORS برای اتصال GitHub Pages به Backend
CORS(app)

# ساخت جدول‌های دیتابیس هنگام اجرای برنامه
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

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "اطلاعاتی دریافت نشد"
        }), 400

    telegram_id = data.get("telegram_id")
    username = data.get("username", "")
    first_name = data.get("first_name", "")

    if not telegram_id:
        return jsonify({
            "success": False,
            "message": "Telegram ID موجود نیست"
        }), 400

    try:

        create_user(
            telegram_id,
            username,
            first_name
        )

        conn = get_db()

        user = conn.execute("""
            SELECT
                telegram_id,
                username,
                first_name,
                balance,
                referral_count
            FROM users
            WHERE telegram_id = ?
        """, (telegram_id,)).fetchone()

        conn.close()

        if not user:
            return jsonify({
                "success": False,
                "message": "کاربر در دیتابیس پیدا نشد"
            }), 404

        return jsonify({
            "success": True,
            "user": dict(user)
        })

    except Exception as error:

        print("DATABASE ERROR:", error)

        return jsonify({
            "success": False,
            "message": "خطا در ثبت کاربر"
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
