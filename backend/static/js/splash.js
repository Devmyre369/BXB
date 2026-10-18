
document.addEventListener("DOMContentLoaded", function () {
    const splash = document.getElementById("bxb-splash");

    // Stop if the splash markup is missing.
    if (!splash) return;

    let shouldShow = true;

    // Show the splash only once per browser tab session.
    try {
        shouldShow = !sessionStorage.getItem("bxb-splash-shown");

        if (shouldShow) {
            sessionStorage.setItem("bxb-splash-shown", "1");
        }
    } catch (error) {
        // Continue if sessionStorage is unavailable.
    }

    // Remove the splash immediately on subsequent page visits.
    if (!shouldShow) {
        splash.remove();
        return;
    }

    // Keep the splash visible briefly, then fade it out.
    window.setTimeout(function () {
        splash.classList.add("splash-hidden");

        // Remove it from the page after the fade animation.
        window.setTimeout(function () {
            splash.remove();
        }, 500);
    }, 1200);
});
