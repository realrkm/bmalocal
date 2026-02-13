(() => {
    const canvas = document.getElementById("signatureCanvas");
    const ctx = canvas.getContext("2d");
    const messageBox = document.getElementById("message");
    const previewContainer = document.getElementById("previewContainer");
    const signaturePreview = document.getElementById("signaturePreview");

    let isDrawing = false;
    let signatureData = "";

    // Restore previous signature if available
    window.addEventListener("DOMContentLoaded", () => {
        const savedData = localStorage.getItem("signatureData");
        if (savedData) {
            signatureData = savedData;
            const img = new Image();
            img.onload = () => ctx.drawImage(img, 0, 0);
            img.src = savedData;
        }
    });

    function resizeCanvas() {
        const parent = canvas.parentElement;
        const dpi = window.devicePixelRatio || 1;
        canvas.width = parent.clientWidth * dpi;
        canvas.height = parent.clientHeight * dpi;
        canvas.style.width = parent.clientWidth + "px";
        canvas.style.height = parent.clientHeight + "px";
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.scale(dpi, dpi);
        ctx.lineWidth = 2;
        ctx.lineCap = "round";
        ctx.strokeStyle = "#000";

        if (signatureData) {
            const img = new Image();
            img.src = signatureData;
            img.onload = () => ctx.drawImage(img, 0, 0, canvas.width / dpi, canvas.height / dpi);
        }
    }

    function getCoordinates(e) {
        const rect = canvas.getBoundingClientRect();
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        return {
            x: clientX - rect.left,
            y: clientY - rect.top,
        };
    }

    function startDrawing(e) {
        e.preventDefault();
        isDrawing = true;
        const { x, y } = getCoordinates(e);
        ctx.beginPath();
        ctx.moveTo(x, y);
    }

    function draw(e) {
        if (!isDrawing) return;
        e.preventDefault();
        const { x, y } = getCoordinates(e);
        ctx.lineTo(x, y);
        ctx.stroke();
    }

    function stopDrawing() {
        if (isDrawing) {
            isDrawing = false;
            ctx.closePath();
            signatureData = canvas.toDataURL("image/png");
        }
    }

    function showMessage(msg) {
        messageBox.innerText = msg;
        messageBox.classList.remove("hidden");
        setTimeout(() => messageBox.classList.add("hidden"), 3000);
    }

    document.getElementById("clearButton").addEventListener("click", () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        signatureData = "";
        signaturePreview.src = "";
        previewContainer.classList.add("hidden");
        localStorage.removeItem("signatureData");
        showMessage("Signature cleared!");
    });

    document.getElementById("saveButton").addEventListener("click", () => {
        if (!signatureData || isCanvasBlank()) {
            showMessage("Please sign before preview.");
            return;
        }

        signaturePreview.src = signatureData;
        previewContainer.classList.remove("hidden");
        //localStorage.setItem("signatureData", signatureData);

        // Expose to Anvil
        window.getSignatureData = () => signatureData;
    });

    function isCanvasBlank() {
        const blank = document.createElement("canvas");
        blank.width = canvas.width;
        blank.height = canvas.height;
        return canvas.toDataURL() === blank.toDataURL();
    }

    // Attach drawing event listeners
    canvas.addEventListener("mousedown", startDrawing);
    canvas.addEventListener("mousemove", draw);
    canvas.addEventListener("mouseup", stopDrawing);
    canvas.addEventListener("mouseout", stopDrawing);
    canvas.addEventListener("touchstart", startDrawing);
    canvas.addEventListener("touchmove", draw);
    canvas.addEventListener("touchend", stopDrawing);
    canvas.addEventListener("touchcancel", stopDrawing);

    // Resize on load and on window change
    window.addEventListener("resize", resizeCanvas);
    resizeCanvas();

    // Expose globally
    window.getSignatureData = () => signatureData;
})();
