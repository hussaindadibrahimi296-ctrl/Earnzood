import os
import json
import time
import hmac
import hashlib
from urllib.parse import parse_qsl
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

from database import init_db, create_user, get_db


app = Flask(__name__)

CORS(app)


# ==========================================
# تنظیمات EarnZood
# ==========================================

ADS_REWARD = 100
TASK_REWARD = 100

# فعلاً هر نوع پاداش یک بار در 24 ساعت
# بعداً از پنل مدیریت قابل تغییر می‌کنیم.
REWARD_COOLDOWN = 86400


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


        data_check_string = "\n".join(
            f"{key}={value}"
            for key, value in sorted(
                parsed_data.items()
            )
        )


        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256
        ).digest()


        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()


        if not hmac.compare_digest(
            calculated_hash,
            received_hash
        ):

            print(
                "Telegram initData hash is invalid"
            )

            return None


        # ======================================
        # بررسی زمان Telegram initData
        # ======================================

        auth_date = parsed_data.get(
            "auth_date"
        )

        if auth_date:

            try:

                auth_time = int(auth_date)

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
        # User
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
# Home
# ==========================================

@app.route("/")
def home():

    return (
        "بخش پشتیبانی EarnZood "
        "در حال اجرا است!"
    )


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
# Register / Get User
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


    init_data = data.get(
        "initData"
    )


    if not init_data:

        return jsonify({

            "success": False,

            "message":
                "اطلاعات Telegram دریافت نشد"

        }), 401


    telegram_user = \
        validate_telegram_init_data(
            init_data
        )


    if not telegram_user:

        return jsonify({

            "success": False,

            "message":
                "هویت کاربر Telegram معتبر نیست"

        }), 403


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

        create_user(
            telegram_id,
            username,
            first_name
        )


        conn = get_db()


        # به‌روزرسانی آخرین فعالیت
        conn.execute(
            """
            UPDATE users
            SET last_active = ?
            WHERE telegram_id = ?
            """,
            (
                datetime.utcnow().isoformat(),
                telegram_id
            )
        )


        conn.commit()


        user = conn.execute(
            """
            SELECT
                telegram_id,
                username,
                first_name,
                balance,
                referral_count
            FROM users
            WHERE telegram_id = ?
            """,
            (
                telegram_id,
            )
        ).fetchone()


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
# بررسی آخرین پاداش
# ==========================================

def get_last_reward(
    conn,
    telegram_id,
    reward_type
):

    row = conn.execute(
        """
        SELECT created_at
        FROM transactions
        WHERE telegram_id = ?
        AND type = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (
            telegram_id,
            reward_type
        )
    ).fetchone()


    if not row:
        return None


    try:

        return datetime.fromisoformat(
            row["created_at"]
        ).timestamp()

    except Exception:

        return None


# ==========================================
# Reward API
# ==========================================

@app.route(
    "/api/reward",
    methods=["POST"]
)
def reward_user():

    data = request.get_json(
        silent=True
    )


    if not data:

        return jsonify({

            "success": False,

            "message":
                "اطلاعاتی دریافت نشد"

        }), 400


    init_data = data.get(
        "initData"
    )


    reward_type = data.get(
        "type"
    )


    # فقط این دو نوع مجاز هستند
    if reward_type not in (
        "ads",
        "task"
    ):

        return jsonify({

            "success": False,

            "message":
                "نوع پاداش نامعتبر است"

        }), 400


    # ======================================
    # Telegram validation
    # ======================================

    telegram_user = \
        validate_telegram_init_data(
            init_data
        )


    if not telegram_user:

        return jsonify({

            "success": False,

            "message":
                "هویت Telegram معتبر نیست"

        }), 403


    telegram_id = telegram_user.get(
        "id"
    )


    # ======================================
    # انتخاب مقدار پاداش
    # ======================================

    if reward_type == "ads":

        reward_amount = ADS_REWARD

        transaction_type = \
            "ads_reward"

        description = \
            "پاداش مشاهده تبلیغ AdsGram"


    else:

        reward_amount = TASK_REWARD

        transaction_type = \
            "task_reward"

        description = \
            "پاداش انجام تسک AdsGram"


    conn = None


    try:

        conn = get_db()


        # ==================================
        # بررسی وجود کاربر
        # ==================================

        user = conn.execute(
            """
            SELECT
                telegram_id,
                balance,
                is_blocked
            FROM users
            WHERE telegram_id = ?
            """,
            (
                telegram_id,
            )
        ).fetchone()


        if not user:

            conn.close()

            return jsonify({

                "success": False,

                "message":
                    "کاربر پیدا نشد"

            }), 404


        # ==================================
        # بررسی Block
        # ==================================

        if user["is_blocked"]:

            conn.close()

            return jsonify({

                "success": False,

                "message":
                    "حساب کاربری مسدود است"

            }), 403


        # ==================================
        # جلوگیری از پاداش تکراری
        # ==================================

        last_reward = get_last_reward(
            conn,
            telegram_id,
            transaction_type
        )


        if last_reward:

            elapsed = (
                time.time()
                - last_reward
            )


            if elapsed < REWARD_COOLDOWN:

                remaining = int(
                    REWARD_COOLDOWN
                    - elapsed
                )


                hours = remaining // 3600

                minutes = (
                    remaining % 3600
                ) // 60


                conn.close()


                return jsonify({

                    "success": False,

                    "cooldown": True,

                    "message":
                        f"پاداش بعدی حدود "
                        f"{hours} ساعت و "
                        f"{minutes} دقیقه دیگر",

                    "remaining":
                        remaining

                }), 429


        # ==================================
        # افزایش موجودی
        # ==================================

        new_balance = (
            user["balance"]
            + reward_amount
        )


        conn.execute(
            """
            UPDATE users
            SET
                balance = ?,
                last_active = ?
            WHERE telegram_id = ?
            """,
            (
                new_balance,
                datetime.utcnow().isoformat(),
                telegram_id
            )
        )


        # ==================================
        # ثبت تراکنش
        # ==================================

        conn.execute(
            """
            INSERT INTO transactions
            (
                telegram_id,
                type,
                amount,
                description,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                telegram_id,
                transaction_type,
                reward_amount,
                description,
                datetime.utcnow().isoformat()
            )
        )


        conn.commit()


        # ==================================
        # پاسخ
        # ==================================

        return jsonify({

            "success": True,

            "reward":
                reward_amount,

            "type":
                reward_type,

            "user": {

                "telegram_id":
                    telegram_id,

                "balance":
                    new_balance

            }

        })


    except Exception as error:

        if conn:

            conn.rollback()


        print(
            "REWARD ERROR:",
            error
        )


        return jsonify({

            "success": False,

            "message":
                "خطا در ثبت پاداش"

        }), 500


    finally:

        if conn:

            conn.close()


# ==========================================
# Run
# ==========================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
        )
