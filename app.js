// EarnZood Telegram Mini App

function initEarnZood() {

    const tg = window.Telegram.WebApp;

    // آماده‌سازی Telegram Mini App
    tg.ready();
    tg.expand();

    console.log("Telegram WebApp loaded");

    // اطلاعات کاربر
    const user = tg.initDataUnsafe.user;

    console.log("Telegram user:", user);

    if (user && user.first_name) {

        const welcome = document.createElement("div");

        welcome.textContent = "سلام " + user.first_name + " 👋";

        welcome.style.textAlign = "center";
        welcome.style.marginTop = "10px";
        welcome.style.fontSize = "16px";
        welcome.style.fontWeight = "bold";
        welcome.style.color = "#ffd54a";

        const header = document.querySelector("header");

        header.appendChild(welcome);
    }

}

// وقتی صفحه کاملاً آماده شد
window.addEventListener("load", initEarnZood);
