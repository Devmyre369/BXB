
(function () {
    function initializeBxBSplash() {
        document.documentElement.classList.remove("bxb-loading");

        const splash = document.getElementById("bxb-splash");

        if (!splash) {
            console.warn("BxB splash screen element was not found.");
            return;
        }

        if (!document.documentElement.classList.contains("bxb-splash-first-visit")) {
            splash.remove();
            return;
        }

        // Inject splash CSS once.
        if (!document.getElementById("bxb-splash-styles")) {
            const style = document.createElement("style");
            style.id = "bxb-splash-styles";

            style.textContent = `
                #bxb-splash {
                    position: fixed !important;
                    inset: 0 !important;
                    width: 100vw !important;
                    height: 100vh !important;
                    height: 100dvh !important;
                    margin: 0 !important;
                    padding: 0 !important;
                    box-sizing: border-box !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    background: #070a12 !important;
                    color: #ffffff !important;
                    text-align: center;
                    z-index: 2147483647 !important;
                    opacity: 1;
                    visibility: visible;
                    pointer-events: auto;
                    overflow: hidden;
                    transition: opacity 0.5s ease, visibility 0.5s ease;
                }

                #bxb-splash *,
                #bxb-splash *::before,
                #bxb-splash *::after {
                    box-sizing: border-box;
                }

                #bxb-splash.splash-hidden {
                    opacity: 0;
                    visibility: hidden;
                    pointer-events: none;
                }

                #bxb-splash .splash-content {
                    width: min(90%, 380px);
                    padding: 24px;
                    text-align: center;
                }

                #bxb-splash .splash-logo {
                    width: 92px;
                    height: 92px;
                    margin: 0 auto 22px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 27px;
                    background: linear-gradient(135deg, #6d5dfc, #00d4ff);
                    color: #ffffff;
                    font-size: 32px;
                    font-weight: 900;
                    letter-spacing: -1px;
                    box-shadow: 0 0 50px rgba(109, 93, 252, 0.4);
                }

                #bxb-splash .splash-content h1 {
                    margin: 0 0 10px;
                    color: #ffffff;
                    font-size: clamp(26px, 6vw, 34px);
                    font-weight: 800;
                    letter-spacing: -1px;
                }

                #bxb-splash .splash-content p {
                    margin: 0 0 30px;
                    color: #a6b0c5;
                    font-size: 15px;
                }

                #bxb-splash .splash-loader {
                    width: 170px;
                    height: 4px;
                    margin: 0 auto 16px;
                    overflow: hidden;
                    border-radius: 10px;
                    background: #252b3b;
                }

                #bxb-splash .splash-loader span {
                    display: block;
                    width: 40%;
                    height: 100%;
                    border-radius: inherit;
                    background: linear-gradient(90deg, #6d5dfc, #00d4ff);
                    animation: bxb-loading 1.2s ease-in-out infinite;
                }

                #bxb-splash .splash-content small {
                    color: #77839a;
                    font-size: 12px;
                }

                @keyframes bxb-loading {
                    0% { transform: translateX(-110%); }
                    100% { transform: translateX(280%); }
                }

                @media (prefers-reduced-motion: reduce) {
                    #bxb-splash,
                    #bxb-splash .splash-loader span {
                        transition: none;
                        animation: none;
                    }
                }
            `;

            document.head.appendChild(style);
        }

        // Start visible; do not modify body or app-shell visibility.
        splash.classList.remove("splash-hidden");

        // Avoid scheduling multiple timers for the same splash.
        if (splash.dataset.initialized === "true") {
            return;
        }

        splash.dataset.initialized = "true";

        // Fade out, then remove the overlay.
        window.setTimeout(function () {
            if (!splash.isConnected) {
                return;
            }

            splash.classList.add("splash-hidden");

            window.setTimeout(function () {
                if (splash.isConnected) {
                    splash.remove();
                }
            }, 500);
        }, 1500);
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initializeBxBSplash,
            { once: true }
        );
    } else {
        initializeBxBSplash();
    }
})();
