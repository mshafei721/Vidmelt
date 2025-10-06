import redis
from flask import Flask, render_template, request, redirect, send_from_directory
import os
from pathlib import Path
from dotenv import load_dotenv
import threading

from vidmelt import pipeline
from vidmelt.events import build_event_bus

# Load environment variables
load_dotenv()
print(f"DEBUG: OPENAI_API_KEY loaded: {bool(os.getenv('OPENAI_API_KEY'))}")

app = Flask(__name__)
app.config["REDIS_URL"] = "redis://localhost:6379/0"
EVENT_BUS = build_event_bus(app)

# Directories (shared with pipeline module)
UPLOAD_FOLDER = pipeline.UPLOAD_FOLDER
SUMMARY_DIR = pipeline.SUMMARY_DIR
TRANSCRIPT_DIR = pipeline.TRANSCRIPT_DIR

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'video' not in request.files:
        return redirect(request.url)
    file = request.files['video']
    if file.filename == '':
        return redirect(request.url)
    if file:
        video_path = UPLOAD_FOLDER / file.filename
        file.save(video_path)
        EVENT_BUS.publish({"message": f"File uploaded: {file.filename} - Let the magic begin! ✨", "icon": "⬆️"}, "update")
        
        transcription_model = request.form.get('transcription_model', 'whisper-base')
        print(f"DEBUG: Selected transcription model from form: {transcription_model}")

        # Start processing in a new thread to avoid blocking the Flask app
        threading.Thread(target=process_video_web, args=(video_path, transcription_model,)).start()
        return "Upload successful, processing started."

def process_video_web(video_path: Path, transcription_model: str):
    with app.app_context():
        print(f"DEBUG: Processing video: {video_path.name} with transcription model: {transcription_model}")
        pipeline.process_video(video_path, transcription_model, publish=EVENT_BUS.publish)

@app.route('/summaries/<filename>')
def download_summary(filename):
    return send_from_directory(SUMMARY_DIR, filename, as_attachment=True)


@app.route('/transcripts/<filename>')
def download_transcript(filename):
    return send_from_directory(TRANSCRIPT_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in .env file.")
        print("Please create a .env file and add your OpenAI API key.")
    else:
        try:
            # Test Redis connection
            r = redis.from_url(app.config["REDIS_URL"])
            r.ping()
            print("DEBUG: Successfully connected to Redis.")
            app.run(debug=True)
        except redis.exceptions.ConnectionError as e:
            print(f"Error: Could not connect to Redis at {app.config["REDIS_URL"]}. Please ensure Redis is running. Error: {e}")
