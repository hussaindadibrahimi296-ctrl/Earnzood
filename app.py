import os
import json
import time
import hmac
import hashlib
from urllib.parse import parse_qsl

from flask import Flask, jsonify, request
from flask_cors import CORS

from database import init_db, create_user, get_db


# ==========================================
# App
# ==========================================

app = Flask(__name__)

CORS(app)


# ==========================================
# تنظیمات موقت EarnZood
# بعداً از Admin Panel قابل تغییر می‌شود
# ==========================================

AD_REWARD = 100
TASK_REWARD = 100

AD_DAILY_LIMIT = 5
TASK_DAILY_LIMIT = 1


# AdsGram Block IDs

ADS_BLOCK_ID = "43856"
TASK_BLOCK_ID = "task-43858"


# ==========================================
# Database
# ==========================================

init_db()


# ==========================================
# Telegram WebApp Security
# ==========================================

def validate_telegram_init_data(init_data):

    bot_token = os.environ.get(
        "TELEGRAM_BOT_TOKEN"
    )

    if not bot_token:

        print(
            "ERROR: TELEGRAM_BOT_TOKEN is not configured"
        )

        return None


    if not init_data:

        return None


    try:

        parsed_data = dict(
            parse_qsl(
                init_data,
                keep_blank_values=True
            )
        )


        received_hash = parsed_data.pop(
            "hash",
            None
        )


        if not received_hash:

            return None


        # Telegram data-check-string

        data_check_string = "\n".join(
            f"{key}={value}"
            for key, value
            in sorted(parsed_data.items())
        )


        # Telegram secret key

        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256
        ).digest()


        # Calculate hash

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()


        # Secure comparison

        if not hmac.compare_digest(
            calculated_hash,
            received_hash
        ):

            print(
                "Telegram initData hash is invalid"
            )

            return None


        # ======================================
        # بررسی تاریخ
        # ======================================

        auth_date = parsed_data.get(
            "auth_date"
        )


        if auth_date:

            try:

                auth_time = int(
                    auth_date
                )


                if (
                    time.time() - auth_time
                    > 86400
                ):

                    print(
                        "Telegram initData has expired"
                    )

                    return None


            except ValueError:

                return None


        # ======================================
        # Telegram User
        # ======================================

        user_json = parsed_data.get(
            "user"
        )


        if not user_json:

            return None


        user = json.loads(
            user_json
        )


        if not user.get("id"):

            return None


        return user


    except Exception as error:

        print(
            "Telegram validation error:",
            error
        )

        return None


# ==========================================
# دریافت کاربر معتبر
# ==========================================

def get_telegram_user():

    data = request.get_json(
        silent=True
    )


    if not data:

        return None, jsonify({
            "success": False,
            "message": "اطلاعاتی دریافت نشد"
        }), 400


    init_data = data.get(
        "initData"
    )


    if not init_data:

        return None, jsonify({
            "success": False,
            "message": "اطلاعات Telegram دریافت نشد"
        }), 401


    telegram_user = validate_telegram_init_data(
        init_data
    )


    if not telegram_user:

        return None, jsonify({
            "success": False,
            "message": "هویت کاربر Telegram معتبر نیست"
        }), 403


    return telegram_user, None, None


# ==========================================
# Home
# ==========================================

@app.route("/")
def home():

    return jsonify({

        "success": True,

        "app": "EarnZood",

        "status": "online"

    })


# ==========================================
# API Test
# ==========================================

@app.route("/api/test")
def test():

    return jsonify({

        "success": True,

        "message":
            "رابط برنامه‌نویسی EarnZood در حال کار است"

    })


# ==========================================
# AdsGram Settings
# ==========================================

@app.route(
    "/api/ads/settings",
    methods=["GET"]
)
def ads_settings():

    return jsonify({

        "success": True,

        "ads": {

            "block_id": ADS_BLOCK_ID,

            "reward": AD_REWARD,

            "daily_limit": AD_DAILY_LIMIT

        },

        "task": {

            "block_id": TASK_BLOCK_ID,

            "reward": TASK_REWARD,

            "daily_limit": TASK_DAILY_LIMIT

        }

    })


# ==========================================
# Register / Get User
# ==========================================

@app.route(
    "/api/user",
    methods=["POST"]
)
def register_user():

    telegram_user, error_response, status = \
        get_telegram_user()


    if error_response:

        return error_response, status


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

        # ساخت کاربر در صورت جدید بودن

        create_user(
            telegram_id,
            username,
            first_name
        )


        # دریافت کاربر

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
# دریافت موجودی
# ==========================================

def get_user_balance(
    telegram_id
):

    conn = get_db()


    user = conn.execute("""
        SELECT balance
        FROM users
        WHERE telegram_id = ?
    """, (
        telegram_id,
    )).fetchone()


    conn.close()


    if not user:

        return None


    return user["balance"]


# ==========================================
# افزایش موجودی
# ==========================================

def add_balance(
    telegram_id,
    amount
):

    conn = get_db()


    conn.execute("""
        UPDATE users
        SET balance = balance + ?
        WHERE telegram_id = ?
    """, (
        amount,
        telegram_id
    ))


    conn.commit()


    user = conn.execute("""
        SELECT
            balance,
            referral_count
        FROM users
        WHERE telegram_id = ?
    """, (
        telegram_id,
    )).fetchone()


    conn.close()


    return user


# ==========================================
# بررسی پاداش‌های امروز
# ==========================================

def get_today_reward_count(
    telegram_id,
    reward_type
):

    """
    این تابع فعلاً از جدول reward_logs استفاده می‌کند.

    اگر جدول وجود نداشته باشد، آن را ایجاد می‌کند.
    """

    conn = get_db()


    conn.execute("""
        CREATE TABLE IF NOT EXISTS reward_logs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            telegram_id INTEGER NOT NULL,

            reward_type TEXT NOT NULL,

            amount INTEGER NOT NULL,

            created_at INTEGER NOT NULL

        )
    """)


    today_start = int(
        time.time()
        // 86400
        * 86400
    )


    row = conn.execute("""
        SELECT COUNT(*) AS count
        FROM reward_logs
        WHERE telegram_id = ?
        AND reward_type = ?
        AND created_at >= ?
    """, (
        telegram_id,
        reward_type,
        today_start
    )).fetchone()


    conn.commit()

    conn.close()


    return row["count"]


# ==========================================
# ثبت پاداش
# ==========================================

def give_reward(
    telegram_id,
    reward_type,
    amount
):

    conn = get_db()


    conn.execute("""
        CREATE TABLE IF NOT EXISTS reward_logs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            telegram_id INTEGER NOT NULL,

            reward_type TEXT NOT NULL,

            amount INTEGER NOT NULL,

            created_at INTEGER NOT NULL

        )
    """)


    # ثبت پاداش

    conn.execute("""
        INSERT INTO reward_logs
        (
            telegram_id,
            reward_type,
            amount,
            created_at
        )
        VALUES (?, ?, ?, ?)
    """, (
        telegram_id,
        reward_type,
        amount,
        int(time.time())
    ))


    # افزایش موجودی

    conn.execute("""
        UPDATE users
        SET balance = balance + ?
        WHERE telegram_id = ?
    """, (
        amount,
        telegram_id
    ))


    conn.commit()


    user = conn.execute("""
        SELECT
            balance,
            referral_count
        FROM users
        WHERE telegram_id = ?
    """, (
        telegram_id,
    )).fetchone()


    conn.close()


    return user


# ==========================================
# AdsGram Rewarded
# ==========================================

@app.route(
    "/api/ad/reward",
    methods=["POST"]
)
def reward_ad():

    telegram_user, error_response, status = \
        get_telegram_user()


    if error_response:

        return error_response, status


    telegram_id = telegram_user.get(
        "id"
    )


    # ======================================
    # مطمئن شو کاربر در DB وجود دارد
    # ======================================

    create_user(
        telegram_id,
        telegram_user.get(
            "username",
            ""
        ),
        telegram_user.get(
            "first_name",
            ""
        )
    )


    # ======================================
    # محدودیت روزانه
    # ======================================

    count = get_today_reward_count(
        telegram_id,
        "ad"
    )


    if count >= AD_DAILY_LIMIT:

        return jsonify({

            "success": False,

            "message":
                "حداکثر تعداد تبلیغ امروز تکمیل شده است",

            "limit":
                AD_DAILY_LIMIT

        }), 429


    # ======================================
    # دادن پاداش
    # ======================================

    user = give_reward(
        telegram_id,
        "ad",
        AD_REWARD
    )


    if not user:

        return jsonify({

            "success": False,

            "message":
                "کاربر پیدا نشد"

        }), 404


    return jsonify({

        "success": True,

        "reward": AD_REWARD,

        "reward_type": "ad",

        "user": {

            "balance":
                user["balance"],

            "referral_count":
                user["referral_count"]

        }

    })


# ==========================================
# AdsGram Task Reward
# ==========================================

@app.route(
    "/api/task/reward",
    methods=["POST"]
)
def reward_task():

    telegram_user, error_response, status = \
        get_telegram_user()


    if error_response:

        return error_response, status


    telegram_id = telegram_user.get(
        "id"
    )


    # ======================================
    # ساخت کاربر
    # ======================================

    create_user(
        telegram_id,
        telegram_user.get(
            "username",
            ""
        ),
        telegram_user.get(
            "first_name",
            ""
        )
    )


    # ======================================
    # محدودیت روزانه Task
    # ======================================

    count = get_today_reward_count(
        telegram_id,
        "task"
    )


    if count >= TASK_DAILY_LIMIT:

        return jsonify({

            "success": False,

            "message":
                "این تسک امروز قبلاً دریافت شده است",

            "limit":
                TASK_DAILY_LIMIT

        }), 429


    # ======================================
    # پاداش Task
    # ======================================

    user = give_reward(
        telegram_id,
        "task",
        TASK_REWARD
    )


    if not user:

        return jsonify({

            "success": False,

            "message":
                "کاربر پیدا نشد"

        }), 404


    return jsonify({

        "success": True,

        "reward": TASK_REWARD,

        "reward_type": "task",

        "user": {

            "balance":
                user["balance"],

            "referral_count":
                user["referral_count"]

        }

    })


# ==========================================
# Run locally
# ==========================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
            )
