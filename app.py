import os
from flask import Flask, render_template, request, jsonify, send_file, after_this_request
from PIL import Image
from gtts import gTTS
from google import genai
import time  # For cache-busting

# Constants
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
MODEL_ID = "gemini-2.0-flash-exp"

# GenAI Client Setup
client = genai.Client(api_key="api key")  # Replace with your actual API key

# Flask App Initialization
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process-image", methods=["POST"])
def process_image():
    if "file" not in request.files or "language" not in request.form:
        return jsonify({"error": "File or language not provided"}), 400

    file = request.files["file"]
    target_language = request.form["language"]

    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    # Save the file
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(file_path)

    try:
        # Load and process the image
        image = Image.open(file_path)
        image.thumbnail([512, 512])  # Resize for compatibility

        # Extract text using GenAI
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[image, "extract the text from the image"]
        )
        extracted_text = response.text.strip()

        if not extracted_text:
            return jsonify({"error": "No text detected in the image"}), 400

        # Handle Malayalam translation using GenAI
        if target_language == "ml":
            translate_prompt = f"Translate the following text into Malayalam: {extracted_text}. only return single output , introduction and conclusion not needed"
            translate_response = client.models.generate_content(
                model=MODEL_ID,
                contents=[translate_prompt]
            )
            translated_text = translate_response.text.strip()

            if not translated_text or "Please provide" in translated_text:
                return jsonify({"error": "Malayalam translation failed"}), 400

            # Generate audio for Malayalam using GenAI translated text
            try:
                timestamp = int(time.time())  # Unique timestamp for cache-busting
                audio_filename = f"output_{timestamp}.mp3"
                audio_path = os.path.join(app.config["UPLOAD_FOLDER"], audio_filename)
                tts = gTTS(text=translated_text, lang="ml")
                tts.save(audio_path)
            except Exception as e:
                return jsonify({"error": f"Malayalam Text-to-speech conversion failed: {str(e)}"}), 500
        else:
            # Translate the text for other languages
            translate_prompt = f"Translate the following text into {target_language}: {extracted_text}. return only one response , introduction and conclusion not needed"
            translate_response = client.models.generate_content(
                model=MODEL_ID,
                contents=[translate_prompt]
            )
            translated_text = translate_response.text.strip()

            if not translated_text or "Please provide" in translated_text:
                return jsonify({"error": "Translation failed or returned invalid text"}), 400

            # Generate audio for other languages
            try:
                timestamp = int(time.time())  # Unique timestamp for cache-busting
                audio_filename = f"output_{timestamp}.mp3"
                audio_path = os.path.join(app.config["UPLOAD_FOLDER"], audio_filename)
                tts = gTTS(text=translated_text, lang=target_language)
                tts.save(audio_path)
            except Exception as e:
                return jsonify({"error": f"Text-to-speech conversion failed: {str(e)}"}), 500

        # Return results
        return jsonify({
            "extracted_text": extracted_text,
            "translated_text": translated_text,
            "audio_url": f"/serve-audio?file={audio_filename}&t={timestamp}"  # Cache-busting
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/serve-audio")
def serve_audio():
    """
    Stream the audio file and delete it after serving.
    """
    file_name = request.args.get("file")
    if not file_name:
        return jsonify({"error": "No file specified"}), 400

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], file_name)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    @after_this_request
    def delete_file(response):
        try:
            os.remove(file_path)
        except Exception as e:
            app.logger.error(f"Error deleting file {file_path}: {e}")
        return response

    return send_file(file_path, as_attachment=False, mimetype="audio/mpeg")

if __name__ == "__main__":
    app.run(debug=True)
