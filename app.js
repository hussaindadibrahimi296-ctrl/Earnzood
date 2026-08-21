const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();

const user = tg.initDataUnsafe?.user;


// نمایش نام کاربر بدون وابستگی به API
if (user) {

    const header = document.querySelector("header");

    const welcome = document.createElement("p");

    welcome.textContent = `سلام ${user.first_name || "کاربر"} 👋`;

    welcome.style.marginTop = "10px";
    welcome.style.color = "#ffd54a";
    welcome.style.fontSize = "15px";
    welcome.style.fontWeight = "bold";

    header.appendChild(welcome);
}


// اتصال به Backend
async function registerUser() {

    if (!user) {
        console.log("Telegram user پیدا نشد");
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
                    telegram_id: user.id,
                    username: user.username || "",
                    first_name: user.first_name || ""
                })
            }
        );


        const data = await response.json();

        console.log("EarnZood API:", data);


        if (data.success && data.user) {

            const balanceElement =
                document.getElementById("balance");

            balanceElement.textContent =
                Number(data.user.balance).toLocaleString() + " 🪙";

        } else {

            console.error("ثبت کاربر موفق نبود:", data);

        }

    } catch (error) {

        console.error("خطا در اتصال به EarnZood API:", error);

    }
}


registerUser();
