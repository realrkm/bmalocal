// ZXing Scanner for Anvil Works
(() => {
    // Load ZXing dynamically (like your signature script)
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/@zxing/library@latest/umd/index.min.js";
    script.onload = () => {
        console.log("ZXing loaded");

        let codeReader = null;

        // UI element references (assume these are in your Anvil HTML Panel or form template)
        const startButton = document.getElementById("start-scan");
        const videoContainer = document.getElementById("video-container");
        const video = document.getElementById("video");
        const scanLine = document.getElementById("scan-line");
        const resultContainer = document.getElementById("result-container");
        const resultElement = document.getElementById("result");
        const copyButton = document.getElementById("copy-result");
        const scanAgainButton = document.getElementById("scan-again");
        const messageBox = document.getElementById("message-box");

        // --- UI Helpers ---
        function showMessage(msg, isError = false) {
            messageBox.textContent = msg;
            messageBox.classList.remove("error", "info");
            messageBox.classList.add(isError ? "error" : "info");
            messageBox.style.display = "block";
            if (isError && window.anvil) {
                anvil.call("show_error", msg);
            }
        }

        function hideMessage() {
            messageBox.style.display = "none";
        }

        function resetUI() {
            stopScanner();
            resultContainer.style.display = "none";
            startButton.style.display = "block";
            videoContainer.style.display = "none";
            scanLine.style.display = "none";
            hideMessage();
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
                const selectedDeviceId =
                    videoInputDevices.length > 1
                    ? videoInputDevices.find((d) =>
                        d.label.toLowerCase().includes("back")
                                            )?.deviceId || videoInputDevices[0].deviceId
                    : videoInputDevices[0].deviceId;

                startButton.style.display = "none";
                videoContainer.style.display = "block";
                scanLine.style.display = "block";
                resultContainer.style.display = "none";

                // Start decoding
                codeReader.decodeFromVideoDevice(selectedDeviceId, "video", (result, err) => {
                    if (result) {
                        resultElement.textContent = result.text;
                        resultContainer.style.display = "block";
                        if (window.anvil) {
                            anvil.call("display_result", result.text);
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
                resetUI();
            }
        }

        function stopScanner() {
            if (codeReader) {
                codeReader.reset();
            }
            videoContainer.style.display = "none";
            scanLine.style.display = "none";
        }

        // --- Event Listeners ---
        if (startButton) {
            startButton.addEventListener("click", startScanner);
        }
            if (scanAgainButton) {
      scanAgainButton.addEventListener("click", () => {
        resultContainer.style.display = "none";
        startScanner();
      });
    }
    if (copyButton) {
      copyButton.addEventListener("click", () => {
        const textToCopy = resultElement.textContent;
        const textArea = document.createElement("textarea");
        textArea.value = textToCopy;
        document.body.appendChild(textArea);
        textArea.select();
        try {
          document.execCommand("copy");
          copyButton.textContent = "Copied!";
          setTimeout(() => (copyButton.textContent = "Copy"), 2000);
          if (window.anvil) {
            anvil.call("log_copy", textToCopy);
          }
        } catch (err) {
          console.error("Failed to copy text: ", err);
          showMessage("Failed to copy text.", true);
        }
        document.body.removeChild(textArea);
      });
    }

    // Expose for Anvil (optional)
    window.startScanner = startScanner;
    window.stopScanner = stopScanner;
  };
  document.head.appendChild(script);
})();
