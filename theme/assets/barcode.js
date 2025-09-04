// ZXing library
import "https://unpkg.com/@zxing/library@latest";

(() => {
    let codeReader = null;
    let videoElement = null;
    let scanLine = null;

    window.startScanner = async function() {
        console.log("startScanner called");  // debug
        try {
            videoElement = document.getElementById("video");
            scanLine = document.getElementById("scan-line");
            const resultContainer = document.getElementById("result-container");
            const resultElement = document.getElementById("result");

            if (!videoElement) {
                alert("Video element not found");
                return;
            }

            if (!codeReader) {
                codeReader = new ZXing.BrowserMultiFormatReader();
            }

            if (resultContainer) resultContainer.style.display = "none";
            if (resultElement) resultElement.textContent = "";
            videoElement.style.display = "block";
            if (scanLine) scanLine.style.display = "block";

            const devices = await codeReader.listVideoInputDevices();
            if (devices.length < 1) {
                alert("No camera found");
                return;
            }
            const selectedDeviceId = devices[0].deviceId;

            codeReader.decodeFromVideoDevice(selectedDeviceId, videoElement, (result, err) => {
                if (result) {
                    if (resultElement) resultElement.textContent = result.text;
                    if (resultContainer) resultContainer.style.display = "block";
                    if (window.display_result) window.display_result(result.text);
                    window.stopScanner();
                }
                if (err && !(err instanceof ZXing.NotFoundException)) {
                    console.error("Scanning error:", err);
                }
            });
        } catch (err) {
            console.error("Error starting scanner:", err);
            alert("Error starting scanner. See console.");
        }
    };

    window.stopScanner = function() {
        console.log("stopScanner called");  // debug
        try {
            if (codeReader) codeReader.reset();
            if (scanLine) scanLine.style.display = "none";
            if (videoElement) videoElement.style.display = "none";
        } catch (err) {
            console.error("Error stopping scanner:", err);
        }
    };
})();
