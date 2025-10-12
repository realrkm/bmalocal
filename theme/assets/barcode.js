// ZXing Scanner for Anvil Works (All Supported Barcode Types)
(() => {
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/@zxing/library@latest/umd/index.min.js";
    script.onload = () => {
        console.log("ZXing loaded");

        let codeReader = null;
        const videoContainer = document.getElementById("video-container");
        const scanLine = document.getElementById("scan-line");
        const messageBox = document.getElementById("message-box");

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

        function playBeep() {
            try {
                const audio = new Audio("_/theme/scanner-beep.mp3");
                audio.play().catch((err) => console.warn("Audio play blocked:", err));
            } catch (e) {
                console.error("Error playing beep:", e);
            }
        }

        async function startScanner() {
            hideMessage();
            try {
                const {
                    BrowserMultiFormatReader,
                    BarcodeFormat,
                    DecodeHintType,
                } = ZXing;

                // Include *all supported barcode formats*
                const formats = [
                    BarcodeFormat.AZTEC,
                    BarcodeFormat.CODABAR,
                    BarcodeFormat.CODE_39,
                    BarcodeFormat.CODE_93,
                    BarcodeFormat.CODE_128,
                    BarcodeFormat.DATA_MATRIX,
                    BarcodeFormat.EAN_8,
                    BarcodeFormat.EAN_13,
                    BarcodeFormat.ITF,
                    BarcodeFormat.MAXICODE,
                    BarcodeFormat.PDF_417,
                    BarcodeFormat.QR_CODE,
                    BarcodeFormat.MICRO_QR_CODE,
                    BarcodeFormat.UPC_A,
                    BarcodeFormat.UPC_E,
                    BarcodeFormat.RSS_14,
                    BarcodeFormat.RSS_EXPANDED,
                ];

                const hints = new Map();
                hints.set(DecodeHintType.POSSIBLE_FORMATS, formats);

                codeReader = new BrowserMultiFormatReader(hints);

                const videoInputDevices = await codeReader.listVideoInputDevices();
                if (videoInputDevices.length < 1) {
                    showMessage("No camera found.", true);
                    return;
                }

                const selectedDeviceId =
                    videoInputDevices.find((d) =>
                        /back|rear|environment/i.test(d.label)
                                          )?.deviceId || videoInputDevices[0].deviceId;

                const constraints = {
                    video: {
                        deviceId: selectedDeviceId,
                        width: { ideal: 1920, min: 640 },
                        height: { ideal: 1080, min: 480 },
                        facingMode: { ideal: "environment" },
                        focusMode: { ideal: "continuous" },
                        advanced: [{ focusMode: "continuous" }],
                    },
                };

                videoContainer.style.display = "block";
                scanLine.style.display = "block";

                codeReader.decodeFromVideoDevice(selectedDeviceId, "video", (result, err) => {
                    if (result) {
                        console.log("Scan result:", result.text, "Format:", result.getBarcodeFormat?.());
                        playBeep();
                        if (window.display_result) window.display_result(result.text);
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

    window.startScanner = startScanner;
    window.stopScanner = stopScanner;
  };
  document.head.appendChild(script);
})();
