const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();

const user = tg.initDataUnsafe?.user;

if (user) {
    const header = document.querySelector("header");

    const welcome = document.createElement("p");

    welcome.textContent = `سلام ${user.first_name} 👋`;

    welcome.style.marginTop = "10px";
    welcome.style.color = "#ffd54a";
    welcome.style.fontSize = "15px";
    welcome.style.fontWeight = "bold";

    header.appendChild(welcome);
}
