import os
import subprocess
import torch
import whisper
import uuid
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
TRANSCRIPT_FOLDER = "transcripts"
ALLOWED_EXTENSIONS = {"mp4", "mov"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["TRANSCRIPT_FOLDER"] = TRANSCRIPT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRANSCRIPT_FOLDER, exist_ok=True)

def extract_audio(video_path, audio_path):
    """Extract audio from video using ffmpeg."""
    print("[INFO] Extracting audio from video...")
    command = f'ffmpeg -i "{video_path}" -vn -acodec libmp3lame -q:a 0 -map a "{audio_path}" -y'
    subprocess.run(command, shell=True, check=True)
    print("[SUCCESS] Audio extraction completed.")

def transcribe_audio(audio_path):
    """Transcribe audio using Whisper with high accuracy."""
    print("[INFO] Loading Whisper model...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model("large-v2").to(device)
    print("[SUCCESS] Whisper model loaded.")

    print("[INFO] Starting transcription...")
    result = model.transcribe(audio_path, fp16=False, temperature=0.0, language="en")
    print("[SUCCESS] Transcription completed.")

    return result.get("text", "")

def save_transcript(text, filename):
    """Save transcript as a text file with a unique identifier."""
    unique_id = f"{filename}_{uuid.uuid4().hex[:8]}"
    transcript_path = os.path.join(TRANSCRIPT_FOLDER, f"{unique_id}.txt")
    
    with open(transcript_path, "w", encoding="utf-8") as file:
        file.write(text)
    
    print(f"[SUCCESS] Transcript saved: {transcript_path}")
    return unique_id

@app.route("/upload", methods=["POST"])
def upload_video():
    """Handle video upload, extract audio, transcribe, and return transcript."""
    file = request.files.get("file")
    
    if not file or file.filename.rsplit(".", 1)[1].lower() not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Invalid file"}), 400

    filename = secure_filename(file.filename).rsplit(".", 1)[0]
    video_path = os.path.join(UPLOAD_FOLDER, file.filename)
    audio_path = os.path.join(UPLOAD_FOLDER, f"{filename}.mp3")

    print(f"[INFO] Received file: {file.filename}")
    file.save(video_path)
    print("[SUCCESS] File uploaded successfully.")

    extract_audio(video_path, audio_path)
    transcript_text = transcribe_audio(audio_path)
    
    unique_id = save_transcript(transcript_text, filename)
    transcript_filename = f"{unique_id}.txt"

    try:
        os.remove(video_path)
        os.remove(audio_path)
        print("[SUCCESS] Deleted video and audio files after transcription.")
    except Exception as e:
        print(f"[ERROR] Could not delete files: {e}")

    return jsonify({
        "transcript": transcript_text, 
        "word_count": len(transcript_text.split()), 
        "download_link": transcript_filename  # Just return the unique file name here
    })

@app.route("/download/<filename>", methods=["GET"])
def download_transcript(filename):
    """Download the transcript file."""
    transcript_path = os.path.join(TRANSCRIPT_FOLDER, filename)

    if not os.path.exists(transcript_path):
        print(f"[ERROR] File not found: {transcript_path}")
        return jsonify({"error": "File not found"}), 404

    return send_file(transcript_path, as_attachment=True, download_name="transcript.txt")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
