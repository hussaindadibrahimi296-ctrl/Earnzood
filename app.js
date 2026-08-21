// ==========================================
// EarnZood Mini App
// Telegram + AdsGram
// ==========================================

const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();


// ==========================================
// Backend
// ==========================================

const API_URL =
    "https://earnzood-0m9k.onrender.com";


// ==========================================
// AdsGram
// ==========================================

// Rewarded AdsGram Block
const ADSGRAM_BLOCK_ID = "43856";

// AdsGram Task Block
const ADSGRAM_TASK_ID = "task-43858";


// فعلاً پاداش 100 سکه
// بعداً از پنل مدیریت قابل تغییر می‌شود
const DEFAULT_REWARD = 100;


// ==========================================
// عناصر صفحه
// ==========================================

const balanceElement =
    document.getElementById("balance");

const adsButton =
    document.getElementById("adsButton");

const tasksButton =
    document.getElementById("tasksButton");

const referralButton =
    document.getElementById("referralButton");

const withdrawButton =
    document.getElementById("withdrawButton");

const profileButton =
    document.getElementById("profileButton");

const adsStatus =
    document.getElementById("adsStatus");

const tasksStatus =
    document.getElementById("tasksStatus");


// ==========================================
// کاربر Telegram
// ==========================================

const user =
    tg.initDataUnsafe?.user;


// ==========================================
// نمایش نام کاربر
// ==========================================

if (user) {

    const header =
        document.querySelector("header");

    if (header) {

        const oldWelcome =
            document.getElementById(
                "earnzoodWelcome"
            );

        if (!oldWelcome) {

            const welcome =
                document.createElement("p");

            welcome.id =
                "earnzoodWelcome";

            welcome.textContent =
                `سلام ${user.first_name || "کاربر"} 👋`;

            welcome.style.marginTop =
                "10px";

            welcome.style.color =
                "#ffd54a";

            welcome.style.fontSize =
                "15px";

            welcome.style.fontWeight =
                "bold";

            header.appendChild(welcome);
        }
    }
}


// ==========================================
// نمایش موجودی
// ==========================================

function updateBalance(balance) {

    if (!balanceElement) {
        return;
    }

    const amount =
        Number(balance || 0);

    balanceElement.textContent =
        amount.toLocaleString() +
        " 🪙";
}


// ==========================================
// ثبت / دریافت کاربر
// ==========================================

async function registerUser() {

    if (!tg.initData) {

        console.error(
            "Telegram initData پیدا نشد"
        );

        if (balanceElement) {

            balanceElement.textContent =
                "خطا ❌";
        }

        return null;
    }


    try {

        const response =
            await fetch(
                `${API_URL}/api/user`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        initData:
                            tg.initData

                    })
                }
            );


        const text =
            await response.text();


        console.log(
            "User HTTP:",
            response.status
        );

        console.log(
            "User Response:",
            text
        );


        let data;

        try {

            data =
                JSON.parse(text);

        } catch (error) {

            throw new Error(
                "Backend پاسخ JSON معتبر نداد"
            );
        }


        if (
            response.ok &&
            data.success &&
            data.user
        ) {

            updateBalance(
                data.user.balance
            );

            console.log(
                "کاربر ثبت شد:",
                data.user
            );

            return data.user;
        }


        console.error(
            "ثبت کاربر ناموفق:",
            data
        );


        return null;


    } catch (error) {

        console.error(
            "خطای registerUser:",
            error
        );

        return null;
    }
}


// ==========================================
// دریافت پاداش از Backend
// ==========================================

async function claimReward(type) {

    if (!tg.initData) {

        throw new Error(
            "Telegram initData موجود نیست"
        );
    }


    console.log(
        "درخواست پاداش:",
        type
    );


    const response =
        await fetch(
            `${API_URL}/api/reward`,
            {
                method: "POST",

                headers: {

                    "Content-Type":
                        "application/json"

                },

                body: JSON.stringify({

                    initData:
                        tg.initData,

                    type:
                        type

                })
            }
        );


    const text =
        await response.text();


    console.log(
        "Reward HTTP:",
        response.status
    );

    console.log(
        "Reward Response:",
        text
    );


    let data;


    try {

        data =
            JSON.parse(text);

    } catch (error) {

        throw new Error(
            `سرور پاسخ JSON نداد: ${text}`
        );
    }


    if (
        !response.ok ||
        !data.success
    ) {

        throw new Error(
            data.message ||
            `خطای سرور: ${response.status}`
        );
    }


    if (
        data.user &&
        typeof data.user.balance !==
        "undefined"
    ) {

        updateBalance(
            data.user.balance
        );
    }


    return data;
}


// ==========================================
// AdsGram Rewarded
// ==========================================

let AdController =
    null;


try {

    if (
        window.Adsgram &&
        typeof window.Adsgram.init ===
        "function"
    ) {

        AdController =
            window.Adsgram.init({

                blockId:
                    ADSGRAM_BLOCK_ID

            });


        console.log(
            "AdsGram Rewarded آماده شد"
        );

    } else {

        console.error(
            "AdsGram SDK پیدا نشد"
        );
    }


} catch (error) {

    console.error(
        "AdsGram initialization error:",
        error
    );
}


// ==========================================
// مشاهده تبلیغ Rewarded
// ==========================================

if (adsButton) {

    adsButton.addEventListener(
        "click",
        async function () {

            if (!AdController) {

                tg.showAlert(
                    "سیستم تبلیغات فعلاً در دسترس نیست."
                );

                return;
            }


            adsButton.disabled =
                true;


            if (adsStatus) {

                adsStatus.textContent =
                    "در حال بارگذاری تبلیغ...";
            }


            try {

                const result =
                    await AdController.show();


                console.log(
                    "AdsGram Result:",
                    result
                );


                // ==================================
                // فقط تبلیغ کامل = پاداش
                // ==================================

                if (
                    result &&
                    result.done === true
                ) {

                    if (adsStatus) {

                        adsStatus.textContent =
                            "در حال ثبت پاداش...";
                    }


                    try {

                        const reward =
                            await claimReward(
                                "ads"
                            );


                        const amount =
                            reward.reward ||
                            DEFAULT_REWARD;


                        tg.HapticFeedback
                            ?.notificationOccurred(
                                "success"
                            );


                        tg.showAlert(
                            `🎉 تبریک!\n${amount.toLocaleString()} سکه دریافت کردی.`
                        );


                        if (adsStatus) {

                            adsStatus.textContent =
                                `با مشاهده تبلیغ ${DEFAULT_REWARD} سکه بگیر`;
                        }


                    } catch (rewardError) {

                        console.error(
                            "Reward API Error:",
                            rewardError
                        );


                        tg.showAlert(
                            `خطا در دریافت پاداش:\n${rewardError.message}`
                        );


                        if (adsStatus) {

                            adsStatus.textContent =
                                "خطا در ثبت پاداش";
                        }
                    }


                } else {

                    if (adsStatus) {

                        adsStatus.textContent =
                            `با مشاهده تبلیغ ${
