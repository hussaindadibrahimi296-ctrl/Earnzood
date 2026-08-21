const tg = window.Telegram?.WebApp;

if (tg) {
    tg.ready();
    tg.expand();

    const user = tg.initDataUnsafe?.user;

    if (user) {
        console.log("Telegram User:", user);

        const header = document.querySelector("header");

        if (user.first_name) {
            const welcome = document.createElement("p");

            welcome.textContent = `سلام ${user.first_name} 👋`;

            welcome.style.marginTop = "10px";
            welcome.style.color = "#ffd54a";
            welcome.style.fontSize = "15px";

            header.appendChild(welcome);
        }
    }
}
