const startBtn = document.getElementById("start-btn");
const captureBtn = document.getElementById("capture-btn");
const uploadBtn = document.getElementById("upload-btn");
const languageSelect = document.getElementById("language-select");
const cameraView = document.getElementById("camera-view");
const detectedTextArea = document.getElementById("detected-text");
const translatedTextArea = document.getElementById("translated-text");
const advancedBtn = document.getElementById("advanced-btn");

let videoStream = null;
let capturedImage = null;

// Start the camera
startBtn.addEventListener("click", async () => {
    try {
        videoStream = await navigator.mediaDevices.getUserMedia({ video: true });
        cameraView.srcObject = videoStream;
        alert("Camera started successfully!");
    } catch (error) {
        alert("Unable to access camera: " + error.message);
    }
});

// Capture button
captureBtn.addEventListener("click", () => {
    if (!videoStream) {
        alert("Start the camera first!");
        return;
    }

    const canvas = document.createElement("canvas");
    canvas.width = cameraView.videoWidth;
    canvas.height = cameraView.videoHeight;
    const context = canvas.getContext("2d");
    context.drawImage(cameraView, 0, 0, canvas.width, canvas.height);
    capturedImage = canvas.toDataURL("image/jpeg");

    alert("Image captured successfully!");
});

// Process Image Function
async function processImage(file, language) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("language", language);

    try {
        const response = await fetch("/process-image", {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            alert(`Error: ${error.error}`);
            return;
        }

        const data = await response.json();
        detectedTextArea.value = data.extracted_text; // Update detected text
        translatedTextArea.value = data.translated_text; // Update translated text

        // Play audio
        const audio = new Audio(data.audio_url);
        audio.play();

        alert("Text processed, translated, and played as audio!");
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Upload button
uploadBtn.addEventListener("click", async () => {
    if (!capturedImage) {
        alert("No image captured! Use the Capture button first.");
        return;
    }

    const selectedLanguage = languageSelect.value;
    if (!selectedLanguage) {
        alert("Please select a language!");
        return;
    }

    const blob = await (await fetch(capturedImage)).blob();
    const file = new File([blob], "captured.jpg", { type: "image/jpeg" });

    await processImage(file, selectedLanguage);
});

// Advanced Task button
advancedBtn.addEventListener("click", () => {
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = "image/*";

    fileInput.onchange = async (event) => {
        const file = event.target.files[0];

        if (!file) {
            alert("No file selected!");
            return;
        }

        const selectedLanguage = languageSelect.value;
        if (!selectedLanguage) {
            alert("Please select a language!");
            return;
        }

        await processImage(file, selectedLanguage);
    };

    fileInput.click();
});
