# VocalPen

This project is a real-time OCR and translation application that can extract text from images and translate it into different languages. It also has a text-to-speech feature that can read the translated text aloud.

## Features

- Real-time OCR from a webcam feed.
- OCR from uploaded images.
- Translation to multiple languages.
- Text-to-speech for the translated text.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/vocalpen.git
   ```
2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Web Application

1. Run the application:
   ```bash
   python app.py
   ```
2. Open your web browser and go to `http://127.0.0.1:5000`.

### Desktop Application

1. Run the application:
   ```bash
   python vocal.py
   ```

## Project Structure

- `app.py`: The main Flask application.
- `vocal.py`: A Tkinter-based version of the application.
- `static/`: Static files (CSS, JavaScript, images).
- `templates/`: HTML templates.
- `requirements.txt`: Python dependencies.