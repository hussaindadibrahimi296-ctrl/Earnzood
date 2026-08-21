const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();

const user = tg.initDataUnsafe?.user;


// ==========================================
// نمایش نام کاربر
// ==========================================

if (user) {

    const header = document.querySelector("header");

    if (header) {

        const welcome = document.createElement("p");

        welcome.textContent =
            `سلام ${user.first_name || "کاربر"} 👋`;

        welcome.style.marginTop = "10px";
        welcome.style.color = "#ffd54a";
        welcome.style.fontSize = "15px";
        welcome.style.fontWeight = "bold";

        header.appendChild(welcome);
    }
}


// ==========================================
// اتصال به Backend
// ==========================================

async function registerUser() {

    // بررسی اینکه Mini App واقعاً داخل Telegram باز شده
    if (!tg.initData) {

        console.error(
            "Telegram initData پیدا نشد"
        );

        return;
    }


    try {

        const response = await fetch(
            "https://earnzood-0m9k.onrender.com/api/user",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    // اطلاعات امنیتی واقعی Telegram
                    initData: tg.initData

                })
            }
        );


        const data = await response.json();


        console.log(
            "EarnZood API:",
            data
        );


        // ======================================
        // کاربر با موفقیت ثبت شد
        // ======================================

        if (
            data.success &&
            data.user
        ) {

            const balanceElement =
                document.getElementById("balance");


            if (balanceElement) {

                balanceElement.textContent =
                    Number(
                        data.user.balance
                    ).toLocaleString() +
                    " 🪙";
            }


            console.log(
                "کاربر با موفقیت ثبت شد:",
                data.user
            );

        } else {

            console.error(
                "ثبت کاربر موفق نبود:",
                data
            );

        }

    } catch (error) {

        console.error(
            "خطا در اتصال به EarnZood API:",
            error
        );

    }
}


// اجرای ثبت کاربر
registerUser();
