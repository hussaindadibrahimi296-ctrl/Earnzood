// EarnZood Mini App

const tg = window.Telegram?.WebApp;

if (tg) {
    tg.ready();
    tg.expand();
}

// فعلاً فقط برای تست
console.log("EarnZood Mini App loaded");
