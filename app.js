// ==========================================
// EarnZood - Telegram Mini App
// AdsGram Rewarded + Tasks
// ==========================================

const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();


// ==========================================
// تنظیمات
// ==========================================

const API_URL = "https://earnzood-0m9k.onrender.com";

const ADS_BLOCK_ID = "43856";
const TASK_BLOCK_ID = "task-43858";


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


// ==========================================
// Telegram User
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
                "welcomeMessage"
            );

        if (!oldWelcome) {

            const welcome =
                document.createElement("p");

            welcome.id =
                "welcomeMessage";

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

            header.appendChild(
                welcome
            );
        }
    }
}


// ==========================================
// بررسی Telegram
// ==========================================

function checkTelegram() {

    if (!tg.initData) {

        console.error(
            "Telegram initData پیدا نشد."
        );

        tg.showAlert(
            "این برنامه باید از داخل Telegram باز شود."
        );

        return false;
    }

    return true;
}


// ==========================================
// نمایش موجودی
// ==========================================

function updateBalance(balance) {

    if (!balanceElement) {
        return;
    }

    balanceElement.textContent =
        Number(balance).toLocaleString() +
        " 🪙";
}


// ==========================================
// درخواست API
// ==========================================

async function apiRequest(
    endpoint,
    extraData = {}
) {

    if (!checkTelegram()) {
        return null;
    }

    try {

        const response =
            await fetch(
                API_URL + endpoint,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        initData:
                            tg.initData,

                        ...extraData
                    })
                }
            );


        const data =
            await response.json();


        console.log(
            "EarnZood API:",
            endpoint,
            data
        );


        return {
            response,
            data
        };


    } catch (error) {

        console.error(
            "API Error:",
            error
        );


        tg.showAlert(
            "خطا در اتصال به سرور EarnZood."
        );


        return null;
    }
}


// ==========================================
// ثبت / دریافت کاربر
// ==========================================

async function registerUser() {

    const result =
        await apiRequest(
            "/api/user"
        );


    if (!result) {
        return;
    }


    const {
        response,
        data
    } = result;


    if (
        response.ok &&
        data.success &&
        data.user
    ) {

        updateBalance(
            data.user.balance
        );


        console.log(
            "کاربر با موفقیت ثبت شد:",
            data.user
        );


    } else {

        console.error(
            "ثبت کاربر موفق نبود:",
            data
        );


        if (
            data.message
        ) {

            console.error(
                data.message
            );
        }
    }
}


// ==========================================
// AdsGram Rewarded
// ==========================================

let AdController = null;


function initializeAdsGram() {

    if (
        typeof window.Adsgram ===
        "undefined"
    ) {

        console.error(
            "AdsGram SDK پیدا نشد."
        );

        return false;
    }


    try {

        AdController =
            window.Adsgram.init({
                blockId:
                    ADS_BLOCK_ID
            });


        console.log(
            "AdsGram Rewarded آماده شد."
        );


        return true;


    } catch (error) {

        console.error(
            "AdsGram initialization error:",
            error
        );


        return false;
    }
}


// ==========================================
// دکمه مشاهده تبلیغ
// ==========================================

async function showRewardedAd() {

    if (!checkTelegram()) {
        return;
    }


    if (!AdController) {

        const initialized =
            initializeAdsGram();


        if (!initialized) {

            tg.showAlert(
                "سیستم تبلیغات فعلاً در دسترس نیست."
            );

            return;
        }
    }


    if (adsButton) {

        adsButton.disabled = true;

        adsButton.style.opacity =
            "0.6";
    }


    try {

        console.log(
            "در حال نمایش تبلیغ..."
        );


        const result =
            await AdController.show();


        console.log(
            "AdsGram Result:",
            result
        );


        /*
         * طبق مستندات AdsGram:
         *
         * در Rewarded فقط وقتی تبلیغ
         * کامل مشاهده شده باشد پاداش می‌دهیم.
         */


        if (
            result &&
            result.done === true
        ) {

            console.log(
                "تبلیغ کامل مشاهده شد."
            );


            const rewardResult =
                await apiRequest(
                    "/api/ad/reward"
                );


            if (!rewardResult) {
                return;
            }


            const {
                response,
                data
            } = rewardResult;


            if (
                response.ok &&
                data.success
            ) {

                updateBalance(
                    data.user.balance
                );


                tg.showAlert(
                    `🎉 ${Number(data.reward).toLocaleString()} سکه دریافت کردی!`
                );


            } else {

                console.error(
                    "Ad reward error:",
                    data
                );


                tg.showAlert(
                    data.message ||
                    "پاداش تبلیغ دریافت نشد."
                );
            }


        } else {

            console.log(
                "تبلیغ کامل مشاهده نشد."
            );
        }


    } catch (error) {

        console.error(
            "AdsGram show error:",
            error
        );


        /*
         * اگر کاربر تبلیغ را نبینید
         * یا AdsGram خطا بدهد،
         * پاداش داده نمی‌شود.
         */


    } finally {

        if (adsButton) {

            adsButton.disabled = false;

            adsButton.style.opacity =
                "1";
        }
    }
}


// ==========================================
// AdsGram Task
// ==========================================

function initializeTask() {

    /*
     * Task توسط Web Component
     * <adsgram-task>
     * نمایش داده می‌شود.
     *
     * این تابع فعلاً container را
     * داخل صفحه می‌سازد.
     */


    const existing =
        document.getElementById(
            "adsgramTaskContainer"
        );


    if (existing) {
        return existing;
    }


    const container =
        document.createElement("div");


    container.id =
        "adsgramTaskContainer";


    container.style.marginTop =
        "15px";


    container.style.width =
        "100%";


    container.style.display =
        "none";


    const task =
        document.createElement(
            "adsgram-task"
        );


    task.setAttribute(
        "data-block-id",
        TASK_BLOCK_ID
    );


    task.setAttribute(
        "data-debug",
        "false"
    );


    task.setAttribute(
        "data-debug-console",
        "false"
    );


    task.className =
        "earnzood-adsgram-task";


    container.appendChild(
        task
    );


    /*
     * رویداد Reward
     */

    task.addEventListener(
        "reward",
        async function(event) {

            console.log(
                "AdsGram Task Reward:",
                event
            );


            const rewardResult =
                await apiRequest(
                    "/api/task/reward"
                );


            if (!rewardResult) {
                return;
            }


            const {
                response,
                data
            } = rewardResult;


            if (
                response.ok &&
                data.success
            ) {

                updateBalance(
                    data.user.balance
                );


                tg.showAlert(
                    `🎉 ${Number(data.reward).toLocaleString()} سکه بابت تسک دریافت کردی!`
                );


            } else {

                console.error(
                    "Task reward error:",
                    data
                );


                tg.showAlert(
                    data.message ||
                    "پاداش تسک دریافت نشد."
                );
            }
        }
    );


    /*
     * خطای Task
     */

    task.addEventListener(
        "onError",
        function(event) {

            console.error(
                "AdsGram Task Error:",
                event
            );
        }
    );


    /*
     * هیچ Task موجود نیست
     */

    task.addEventListener(
        "onBannerNotFound",
        function(event) {

            console.log(
                "فعلاً Task تبلیغاتی موجود نیست.",
                event
            );
        }
    );


    /*
     * Session خیلی طولانی شده
     */

    task.addEventListener(
        "onTooLongSession",
        function(event) {

            console.log(
                "AdsGram session too long.",
                event
            );
        }
    );


    document
        .querySelector(".buttons")
        ?.appendChild(
            container
        );


    return container;
}


// ==========================================
// نمایش Task
// ==========================================

function showTasks() {

    if (!checkTelegram()) {
        return;
    }


    const container =
        initializeTask();


    if (!container) {
        return;
    }


    if (
        container.style.display ===
        "none"
    ) {

        container.style.display =
            "block";


        /*
         * اسکرول به سمت Task
         */

        setTimeout(
            function() {

                container.scrollIntoView({
                    behavior:
                        "smooth",
                    block:
                        "center"
                });

            },
            100
        );


    } else {

        container.style.display =
            "none";
    }
}


// ==========================================
// دکمه تبلیغات
// ==========================================

if (adsButton) {

    adsButton.addEventListener(
        "click",
        function() {

            showRewardedAd();

        }
    );
}


// ==========================================
// دکمه Task
// ==========================================

if (tasksButton) {

    tasksButton.addEventListener(
        "click",
        function() {

            showTasks();

        }
    );
}


// ==========================================
// دکمه دعوت دوستان
// ==========================================

if (referralButton) {

    referralButton.addEventListener(
        "click",
        function() {

            tg.showAlert(
                "بخش دعوت دوستان به‌زودی فعال می‌شود."
            );

        }
    );
}


// ==========================================
// دکمه برداشت
// ==========================================

if (withdrawButton) {

    withdrawButton.addEventListener(
        "click",
        function() {

            tg.showAlert(
                "بخش برداشت به‌زودی فعال می‌شود."
            );

        }
    );
}


// ==========================================
// پروفایل
// ==========================================

if (profileButton) {

    profileButton.addEventListener(
        "click",
        function() {

            tg.showAlert(
                "بخش حساب کاربری به‌زودی فعال می‌شود."
            );

        }
    );
}


// ==========================================
// شروع AdsGram
// ==========================================

initializeAdsGram();


// ==========================================
// ثبت کاربر
// ==========================================

registerUser();
