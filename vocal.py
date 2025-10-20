import requests
import pathlib
from PIL import Image, ImageTk
import cv2
import tkinter as tk
from tkinter import filedialog, Label, Button, Toplevel, Text, Scrollbar, RIGHT, Y, OptionMenu, StringVar, Frame, messagebox
from gtts import gTTS
import threading
import tempfile
import os
import platform
import logging
from google import genai
from google.genai import types
from googletrans import Translator
import subprocess

# Gemini API setup
MODEL_ID = "gemini-2.0-flash-exp"
API_KEY = "api key"  # Replace with your actual API key
client = genai.Client(api_key=API_KEY)

# Translator
translator = Translator()

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Global variables
cap = None
root = None

# Function to process the image with Gemini API
def process_image_with_gemini(image, instruction="Extract the text from the image"):
    try:
        image.thumbnail([512, 512])  # Resize image for consistent processing
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[image, instruction]
        )
        text = response.text
        if not text:
            raise Exception("No text extracted from the image.")
        return text
    except Exception as e:
        logging.error(f"Gemini API Error: {e}")
        return f"Error processing image with Gemini: {e}"

# Text-to-speech function
def text_to_speech(text, lang):
    try:
        tts = gTTS(text=text, lang=lang)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmpfile:
            tts.save(tmpfile.name)
            temp_file_path = tmpfile.name

        # Play the audio file based on OS
        if platform.system() == "Windows":
            subprocess.Popen(['start', temp_file_path], shell=True)
        elif platform.system() == "Darwin":
            subprocess.Popen(['open', temp_file_path])
        elif platform.system() == "Linux":
            subprocess.Popen(['xdg-open', temp_file_path])

        # Schedule deletion of the temp file
        def delete_tmp_file():
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        threading.Timer(10, delete_tmp_file).start()
    except Exception as e:
        logging.error(f"Error in text_to_speech: {e}")

# Update the displayed camera frame
def update_frame():
    if cap and cap.isOpened():
        ret, frame = cap.read()
        if ret:
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            imgtk = ImageTk.PhotoImage(image=img_pil)
            lbl_image.imgtk = imgtk
            lbl_image.configure(image=imgtk)
    lbl_image.after(33, update_frame)

# Capture and process a frame from the camera
def capture_and_convert():
    if cap and cap.isOpened():
        ret, frame = cap.read()
        if ret:
            status_label.config(text="Processing...")
            root.update()

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)

            extracted_text = process_image_with_gemini(pil_image)

            target_lang = lang_var.get()
            translated_text = translator.translate(extracted_text, dest=target_lang).text

            threading.Thread(target=text_to_speech, args=(translated_text, target_lang)).start()
            display_text_window(extracted_text, translated_text, frame)

            status_label.config(text="Ready")

# Upload and process an image file
def upload_and_convert():
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
    if file_path:
        try:
            status_label.config(text="Processing...")
            root.update()

            pil_image = Image.open(file_path)
            extracted_text = process_image_with_gemini(pil_image)

            target_lang = lang_var.get()
            translated_text = translator.translate(extracted_text, dest=target_lang).text

            threading.Thread(target=text_to_speech, args=(translated_text, target_lang)).start()
            display_text_window(extracted_text, translated_text, cv2.imread(file_path))

            status_label.config(text="Ready")
        except Exception as e:
            logging.error(f"Error processing uploaded image: {e}")
            messagebox.showerror("Error", f"Error processing uploaded image: {e}")
            status_label.config(text="Ready")

# Display extracted and translated text in a new window
def display_text_window(original_text, translated_text, frame):
    new_window = Toplevel(root)
    new_window.title("Extracted Text")
    new_window.geometry("1600x600")

    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)
    imgtk = ImageTk.PhotoImage(image=img_pil)

    lbl_img = Label(new_window, image=imgtk)
    lbl_img.image = imgtk
    lbl_img.pack()

    text_frame = Frame(new_window)
    text_frame.pack(expand=True, fill="both")

    scrollbar1 = Scrollbar(text_frame)
    scrollbar1.pack(side=RIGHT, fill=Y)

    text_box_original = Text(text_frame, wrap="word", yscrollcommand=scrollbar1.set, height=15, width=80)
    text_box_original.insert("1.0", original_text)
    text_box_original.pack(side="left", expand=True, fill="both")

    scrollbar2 = Scrollbar(text_frame)
    scrollbar2.pack(side=RIGHT, fill=Y)

    text_box_translated = Text(text_frame, wrap="word", yscrollcommand=scrollbar2.set, height=15, width=80)
    text_box_translated.insert("1.0", translated_text)
    text_box_translated.pack(side="right", expand=True, fill="both")

    scrollbar1.config(command=text_box_original.yview)
    scrollbar2.config(command=text_box_translated.yview)


# Start the camera feed
def start_camera():
    global cap
    if cap is None:
        cap = cv2.VideoCapture(1)  # Set camera index to 1
        if not cap.isOpened():
            logging.error("Unable to open camera.")
            messagebox.showerror("Error", "Unable to open camera. Check your camera connection.")
            return
        update_frame()


# Clean up resources on closing
def on_closing():
    global cap
    if cap and cap.isOpened():
        cap.release()
    root.destroy()

# Setup the application UI
def setup_ui():
    global root, lbl_image, lang_var, start_button, capture_button, upload_button, status_label

    root = tk.Tk()
    root.title("Real-Time OCR and Translation App")
    root.geometry("800x600")

    lbl_image = Label(root)
    lbl_image.pack()

    start_button = Button(root, text="Start Camera", command=start_camera)
    start_button.pack(pady=5)

    capture_button = Button(root, text="Capture Image", command=capture_and_convert)
    capture_button.pack(pady=5)

    upload_button = Button(root, text="Upload Image", command=upload_and_convert)
    upload_button.pack(pady=5)

    lang_options = ["en", "es", "fr", "de", "zh-cn", "hi", "ml"]
    lang_var = StringVar(root)
    lang_var.set("en")

    lang_label = Label(root, text="Select Language:")
    lang_label.pack(pady=5)

    lang_menu = OptionMenu(root, lang_var, *lang_options)
    lang_menu.pack(pady=5)

    status_label = Label(root, text="Ready", fg="green")
    status_label.pack(pady=5)

    root.protocol("WM_DELETE_WINDOW", on_closing)

# Main application loop
if __name__ == "__main__":
    setup_ui()
    root.mainloop()
