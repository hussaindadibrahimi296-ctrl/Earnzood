import os
import json
import time
import hmac
import hashlib
from urllib.parse import parse_qsl

from flask import Flask, jsonify, request
from flask_cors import CORS

from database import init_db, create_user, get_db


app = Flask(__name__)

# اجازه اتصال GitHub Pages به Backend
CORS(app)


# ساخت دیتابیس
init_db()


# ==========================================
# Telegram WebApp Security
# ==========================================

def validate_telegram_init_data(init_data):
    """
    اعتبارسنجی initData رسمی Telegram Mini App
    """

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")

    if not bot_token:
        print("ERROR: TELEGRAM_BOT_TOKEN is not configured")
        return None

    if not init_data:
        return None

    try:
        parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))

        received_hash = parsed_data.pop("hash", None)

        if not received_hash:
            return None

        # ساخت data-check-string
        data_check_string = "\n".join(
            f"{key}={value}"
            for key, value in sorted(parsed_data.items())
        )

        # Telegram WebApp secret key
        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256
        ).digest()

        # محاسبه hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        # مقایسه امن
        if not hmac.compare_digest(
            calculated_hash,
            received_hash
        ):
            print("Telegram initData hash is invalid")
            return None

        # بررسی زمان initData
        auth_date = parsed_data.get("auth_date")

        if auth_date:
            try:
                auth_time = int(auth_date)

                # اعتبار تا 24 ساعت
                if time.time() - auth_time > 86400:
                    print("Telegram initData has expired")
                    return None

            except ValueError:
                return None

        # دریافت اطلاعات کاربر
        user_json = parsed_data.get("user")

        if not user_json:
            return None

        user = json.loads(user_json)

        if not user.get("id"):
            return None

        return user

    except Exception as error:
        print("Telegram validation error:", error)
        return None


# ==========================================
# Home
# ==========================================

@app.route("/")
def home():
    return "بخش پشتیبانی EarnZood در حال اجرا است!"


# ==========================================
# API Test
# ==========================================

@app.route("/api/test")
def test():

    return jsonify({
        "success": True,
        "message": "رابط برنامه‌نویسی EarnZood در حال کار است"
    })


# ==========================================
# Register / Get User
# ==========================================

@app.route("/api/user", methods=["POST"])
def register_user():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "اطلاعاتی دریافت نشد"
        }), 400


    # دریافت initData واقعی Telegram
    init_data = data.get("initData")

    if not init_data:
        return jsonify({
            "success": False,
            "message": "اطلاعات Telegram دریافت نشد"
        }), 401


    # اعتبارسنجی Telegram
    telegram_user = validate_telegram_init_data(init_data)

    if not telegram_user:

        return jsonify({
            "success": False,
            "message": "هویت کاربر Telegram معتبر نیست"
        }), 403


    # اطلاعات معتبر کاربر
    telegram_id = telegram_user.get("id")

    username = telegram_user.get(
        "username",
        ""
    )

    first_name = telegram_user.get(
        "first_name",
        ""
    )


    try:

        # ساخت کاربر در صورت جدید بودن
        create_user(
            telegram_id,
            username,
            first_name
        )


        # دریافت اطلاعات کاربر
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

        print(
            "DATABASE ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "message": "خطا در ثبت کاربر"

        }), 500


# ==========================================
# Run
# ==========================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
)
