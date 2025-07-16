import sys
import shutil
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sse import sse
import os
from pathlib import Path
import subprocess
from dotenv import load_dotenv
import time
import threading

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config["REDIS_URL"] = "redis://localhost:6379/0" # Required for flask-sse
app.register_blueprint(sse, url_prefix='/stream')

# Directories
UPLOAD_FOLDER = Path("videos")
AUDIO_DIR = Path("audio_files")
TRANSCRIPT_DIR = Path("transcripts")
SUMMARY_DIR = Path("summaries")

# Ensure directories exist
for directory in [UPLOAD_FOLDER, AUDIO_DIR, TRANSCRIPT_DIR, SUMMARY_DIR]:
    directory.mkdir(exist_ok=True)

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
        sse.publish({"message": f"File uploaded: {file.filename}"}, type='update')
        
        # Start processing in a new thread to avoid blocking the Flask app
        threading.Thread(target=process_video_web, args=(video_path,)).start()
        return "Upload successful, processing started."

def process_video_web(video_path: Path):
    with app.app_context():
        # Check if ffmpeg is installed
        if shutil.which("ffmpeg") is None:
            error_message = "Error: ffmpeg is not installed or not in your PATH. Please install it and try again."
            sse.publish({"message": error_message}, type='error')
            print(error_message)
            return

        video_name = video_path.stem
        audio_path = AUDIO_DIR / f"{video_name}.wav"
        transcript_path = TRANSCRIPT_DIR / f"{video_name}.txt"
        summary_path = SUMMARY_DIR / f"{video_name}.md"

        try:
            # 1. Convert video to audio
            if not audio_path.exists():
                sse.publish({"message": f"Extracting audio from {video_name}..."}, type='update')
                subprocess.run([
                    "ffmpeg",
                    "-i", str(video_path),
                    "-vn",
                    "-acodec", "pcm_s16le",
                    "-ar", "16000",
                    "-ac", "1",
                    str(audio_path)
                ], check=True, capture_output=True, text=True)
                sse.publish({"message": f"Audio extracted: {audio_path.name}"}, type='update')

            # 2. Transcribe audio to text
            if not transcript_path.exists():
                sse.publish({"message": f"Transcribing audio for {video_name}..."}, type='update')
                subprocess.run([
                    sys.executable, "-m", "whisper",
                    str(audio_path),
                    "--model", "base",
                    "--language", "en",
                    "--output_dir", str(TRANSCRIPT_DIR)
                ], check=True, capture_output=True, text=True)
                sse.publish({"message": f"Audio transcribed: {transcript_path.name}"}, type='update')
            
            # 3. Summarize transcript
            sse.publish({"message": f"Summarizing transcript for {video_name}..."}, type='update')
            # Import summarize_transcript here to avoid circular dependency if summarize.py imports app.py
            from summarize import summarize_transcript 
            summarize_transcript(transcript_path, video_name)
            sse.publish({"message": f"Summary created for {video_name}."}, type='update')
            sse.publish({"message": f"Completed! <a href='/summaries/{video_name}.md' target='_blank'>Download Summary</a>"}, type='complete')

        except subprocess.CalledProcessError as e:
            error_message = f"Error processing {video_name}: {e.stderr}"
            sse.publish({"message": error_message}, type='error')
            print(error_message)
        except Exception as e:
            error_message = f"An unexpected error occurred: {e}"
            sse.publish({"message": error_message}, type='error')
            print(error_message)

@app.route('/summaries/<filename>')
def download_summary(filename):
    return send_from_directory(SUMMARY_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in .env file.")
        print("Please create a .env file and add your OpenAI API key.")
    else:
        app.run(debug=True)
