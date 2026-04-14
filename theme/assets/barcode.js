// ZXing Scanner for Anvil Works
(() => {
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/@zxing/library@latest/umd/index.min.js";
    script.onload = () => {
        console.log("ZXing loaded");

        let codeReader = null;
        const videoContainer = document.getElementById("video-container");
        const scanLine = document.getElementById("scan-line");
        const messageBox = document.getElementById("message-box");

        // --- UI Helpers ---
        function showMessage(msg, isError = false) {
            if (!messageBox) return;
            messageBox.textContent = msg;
            messageBox.classList.remove("error", "info");
            messageBox.classList.add(isError ? "error" : "info");
            messageBox.style.display = "block";
        }

        function hideMessage() {
            if (messageBox) messageBox.style.display = "none";
        }

        // --- Play beep sound ---
        function playBeep() {
            try {
                const audio = new Audio("_/theme/scanner-beep.mp3");
                audio.play().catch(err => console.warn("Audio play blocked:", err));
            } catch (e) {
                console.error("Error playing beep:", e);
            }
        }

        // --- Scanner Logic ---
        async function startScanner() {
            hideMessage();
            try {
                codeReader = new ZXing.BrowserMultiFormatReader();

                const videoInputDevices = await codeReader.listVideoInputDevices();
                if (videoInputDevices.length < 1) {
                    showMessage("No camera found.", true);
                    return;
                }

                // Prefer back camera if available
                const selectedDeviceId = videoInputDevices.length > 1
                    ? videoInputDevices.find((d) => 
                        d.label.toLowerCase().includes("back") || 
                        d.label.toLowerCase().includes("rear") ||
                        d.label.toLowerCase().includes("environment")
                                            )?.deviceId || videoInputDevices[0].deviceId
                    : videoInputDevices[0].deviceId;

                // Enhanced video constraints for better quality
                const constraints = {
                    video: {
                        deviceId: selectedDeviceId,
                        width: { ideal: 1920, min: 640 },
                        height: { ideal: 1080, min: 480 },
                        facingMode: { ideal: "environment" },
                        focusMode: { ideal: "continuous" },
                        // Enable autofocus if supported
                        advanced: [{ focusMode: "continuous" }]
                    }
                };

                videoContainer.style.display = "block";
                scanLine.style.display = "block";

                codeReader.decodeFromVideoDevice(selectedDeviceId, "video", (result, err) => {
                    if (result) {
                        console.log("Scan result:", result.text);

                        // Play beep sound
                        playBeep();

                        // Call into Python (StockTake sets window.display_result)
                        if (window.display_result) {
                            window.display_result(result.text);
                        }
                        stopScanner();
                    }
                    if (err && !(err instanceof ZXing.NotFoundException)) {
                        console.error(err);
                        showMessage(`Scanning Error: ${err.message}`, true);
                        stopScanner();
                    }
                });
            } catch (error) {
                console.error("Error initializing scanner:", error);
                showMessage(`Initialization Error: ${error.message}`, true);
                stopScanner();
            }
        }

        function stopScanner() {
            if (codeReader) {
                codeReader.reset();
            }
            videoContainer.style.display = "none";
            scanLine.style.display = "none";
        }

        // Expose for Anvil
        window.startScanner = startScanner;
        window.stopScanner = stopScanner;
    };
    document.head.appendChild(script);
})();
