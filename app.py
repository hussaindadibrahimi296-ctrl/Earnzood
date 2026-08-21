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

# ==========================================
# CORS
# ==========================================

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": "*"
        }
    }
)


# ==========================================
# Database
# ==========================================

init_db()


# ==========================================
# Telegram Mini App Security
# ==========================================

def validate_telegram_init_data(init_data):

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")

    if not bot_token:
        print("ERROR: TELEGRAM_BOT_TOKEN is not configured")
        return None

    if not init_data:
        print("ERROR: Telegram initData is empty")
        return None

    try:

        # تبدیل query string به لیست
        parsed_items = parse_qsl(
            init_data,
            keep_blank_values=True
        )

        # تبدیل به dictionary
        parsed_data = dict(parsed_items)

        # hash اصلی Telegram
        received_hash = parsed_data.get("hash")

        if not received_hash:
            print("ERROR: Telegram hash is missing")
            return None

        # حذف hash برای ساخت data-check-string
        data_check_data = {
            key: value
            for key, value in parsed_data.items()
            if key != "hash"
        }

        # ساخت data-check-string
        data_check_string = "\n".join(
            f"{key}={data_check_data[key]}"
            for key in sorted(data_check_data.keys())
        )

        # ساخت secret key طبق Telegram Mini Apps
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=bot_token.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()

        # محاسبه hash
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode("utf-8"),
            digestmod=hashlib.sha256
        ).hexdigest()

        # مقایسه امن
        if not hmac.compare_digest(
            calculated_hash,
            received_hash
        ):

            print("Telegram initData hash is invalid")

            return None


        # ======================================
        # بررسی زمان
        # ======================================

        auth_date = data_check_data.get("auth_date")

        if not auth_date:

            print("ERROR: auth_date is missing")

            return None

        try:

            auth_time = int(auth_date)

        except (ValueError, TypeError):

            print("ERROR: invalid auth_date")

            return None


        current_time = int(time.time())

        # جلوگیری از داده‌های خیلی قدیمی
        if current_time - auth_time > 86400:

            print("Telegram initData has expired")

            return None


        # جلوگیری از timestamp آینده غیرعادی
        if auth_time - current_time > 300:

            print("Telegram initData timestamp is invalid")

            return None


        # ======================================
        # دریافت Telegram user
        # ======================================

        user_json = data_check_data.get("user")

        if not user_json:

            print("ERROR: Telegram user is missing")

            return None

        try:

            user = json.loads(user_json)

        except json.JSONDecodeError:

            print("ERROR: Telegram user JSON is invalid")

            return None


        telegram_id = user.get("id")

        if not telegram_id:

            print("ERROR: Telegram user ID is missing")

            return None


        return user


    except Exception as error:

        print(
            "Telegram validation error:",
            error
        )

        return None


# ==========================================
# Home
# ==========================================

@app.route("/")
def home():

    return "EarnZood Backend is running successfully 🚀"


# ==========================================
# API Test
# ==========================================

@app.route("/api/test")
def test():

    return jsonify({

        "success": True,

        "message":
        "EarnZood API is working",

        "telegram_token":
        bool(
            os.environ.get(
                "TELEGRAM_BOT_TOKEN"
            )
        )

    })


# ==========================================
# User API
# ==========================================

@app.route(
    "/api/user",
    methods=["POST"]
)
def register_user():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({

            "success": False,

            "message":
            "اطلاعاتی دریافت نشد"

        }), 400


    # ======================================
    # دریافت Telegram initData
    # ======================================

    init_data = data.get(
        "initData"
    )

    if not init_data:

        return jsonify({

            "success": False,

            "message":
            "Telegram initData دریافت نشد"

        }), 401


    # ======================================
    # اعتبارسنجی Telegram
    # ======================================

    telegram_user = (
        validate_telegram_init_data(
            init_data
        )
    )

    if not telegram_user:

        return jsonify({

            "success": False,

            "message":
            "هویت Telegram معتبر نیست"

        }), 403


    # ======================================
    # اطلاعات تأییدشده Telegram
    # ======================================

    telegram_id = telegram_user.get(
        "id"
    )

    username = telegram_user.get(
        "username",
        ""
    )

    first_name = telegram_user.get(
        "first_name",
        ""
    )


    try:

        # ==================================
        # ایجاد کاربر
        # ==================================

        create_user(

            telegram_id,

            username,

            first_name

        )


        # ==================================
        # دریافت کاربر از دیتابیس
        # ==================================

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

        """, (
            telegram_id,
        )).fetchone()

        conn.close()


        if not user:

            return jsonify({

                "success": False,

                "message":
                "کاربر در دیتابیس پیدا نشد"

            }), 404


        # ==================================
        # پاسخ موفق
        # ==================================

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

            "message":
            "خطا در ثبت کاربر"

        }), 500


# ==========================================
# Run
# ==========================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(

        host="0.0.0.0",

        port=port

        )
