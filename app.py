import redis
import openai
import sys
import shutil
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, Response
from flask_sse import sse
import os
from pathlib import Path
import subprocess
from dotenv import load_dotenv
import time
import threading
from urllib.parse import urlparse

# Load environment variables
load_dotenv()
print(f"DEBUG: OPENAI_API_KEY loaded: {bool(os.getenv('OPENAI_API_KEY'))}")

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

# DB
from db import init_db, add_history, list_history
init_db()

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
        sse.publish({"message": f"File uploaded: {file.filename} - Let the magic begin! ✨", "icon": "⬆️"}, type='update')
        
        transcription_model = request.form.get('transcription_model', 'whisper-base')
        print(f"DEBUG: Selected transcription model from form: {transcription_model}")

        # Start processing in a new thread to avoid blocking the Flask app
        threading.Thread(target=process_video_web, args=(video_path, transcription_model, None, None,)).start()
        return "Upload successful, processing started."

@app.route('/submit_url', methods=['POST'])
def submit_url():
    data = request.form or request.json or {}
    url = data.get('url')
    transcription_model = data.get('transcription_model', 'whisper-base')
    if not url:
        return jsonify({"error": "url is required"}), 400
    threading.Thread(target=process_url_web, args=(url, transcription_model)).start()
    return "URL received, processing started."


def process_url_web(url: str, transcription_model: str):
    """Download a remote video via yt-dlp then process it."""
    parsed = urlparse(url)
    platform = (
        'youtube' if 'youtube' in parsed.netloc or 'youtu.be' in parsed.netloc
        else 'tiktok' if 'tiktok' in parsed.netloc
        else 'remote'
    )
    # Use yt-dlp to download best mp4 into UPLOAD_FOLDER
    output_template = str(UPLOAD_FOLDER / "%(title)s.%(ext)s")
    try:
        sse.publish({"message": f"Fetching video from {platform}...", "icon": "🌐"}, type='update')
        subprocess.run([
            "yt-dlp",
            "-f", "mp4/best",
            "-o", output_template,
            url
        ], check=True, capture_output=True, text=True)
        # Find the newest file in UPLOAD_FOLDER as our download
        candidates = sorted(UPLOAD_FOLDER.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not candidates:
            raise RuntimeError("No downloaded video found")
        video_path = candidates[0]
        process_video_web(video_path, transcription_model, url, platform)
    except subprocess.CalledProcessError as e:
        error_message = f"yt-dlp failed: {e.stderr or e.stdout}"
        sse.publish({"message": error_message, "icon": "❌"}, type='error')
    except Exception as e:
        sse.publish({"message": f"Download error: {e}", "icon": "❌"}, type='error')


def process_video_web(video_path: Path, transcription_model: str, source_url: str | None, platform: str | None):
    with app.app_context():
        print(f"DEBUG: Processing video: {video_path.name} with transcription model: {transcription_model}")
        # Check if ffmpeg is installed
        if shutil.which("ffmpeg") is None:
            error_message = "Oops! FFmpeg is playing hide-and-seek. Please install it and try again! 🕵️‍♂️"
            sse.publish({"message": error_message, "icon": "❌"}, type='error')
            print(error_message)
            return

        video_name = video_path.stem
        audio_path = AUDIO_DIR / f"{video_name}.wav"
        transcript_path = TRANSCRIPT_DIR / f"{video_name}.txt"
        summary_path = SUMMARY_DIR / f"{video_name}.md"

        try:
            # 1. Convert video to audio
            if not audio_path.exists():
                sse.publish({"message": f"Extracting audio from {video_name}... This might take a moment, our digital ears are tuning in! 🎧", "icon": "🎶"}, type='update')
                subprocess.run([
                    "ffmpeg",
                    "-i", str(video_path),
                    "-vn",
                    "-acodec", "pcm_s16le",
                    "-ar", "16000",
                    "-ac", "1",
                    str(audio_path)
                ], check=True, capture_output=True, text=True)
                sse.publish({"message": f"Audio extracted: {audio_path.name} - Success! Our digital ears are happy. 🎉", "icon": "✅"}, type='update')

            # Check if audio file is valid before proceeding with transcription
            if not audio_path.exists() or audio_path.stat().st_size == 0:
                error_message = f"Error: Audio file {audio_path.name} was not created or is empty. Cannot proceed with transcription. 🚫"
                sse.publish({"message": error_message, "icon": "❌"}, type='error')
                print(error_message)
                return

            # 2. Transcribe audio to text
            print(f"DEBUG: Checking if transcript exists: {transcript_path.exists()}")
            # Temporarily removing the 'if not transcript_path.exists():' for debugging
            # if not transcript_path.exists():
            sse.publish({"message": f"Transcribing audio for {video_name}... Our AI is listening intently! 👂", "icon": "✍️"}, type='update')
            
            if transcription_model.startswith('whisper-') and transcription_model != 'whisper-api':
                model_name = transcription_model.split('-')[1] # base, medium, large
                subprocess.run([
                    sys.executable, "-m", "whisper",
                    str(audio_path),
                    "--model", model_name,
                    "--language", "en",
                    "--output_dir", str(TRANSCRIPT_DIR)
                ], check=True, capture_output=True, text=True)
            elif transcription_model == 'whisper-api':
                print("DEBUG: Attempting to call OpenAI Whisper API...")
                client = openai.OpenAI()
                try:
                    with open(audio_path, "rb") as audio_file:
                        transcript_response = client.audio.transcriptions.create(
                            model="whisper-1", 
                            file=audio_file
                        )
                    with open(transcript_path, "w") as f:
                        f.write(transcript_response.text)
                    print("DEBUG: OpenAI Whisper API call successful.")
                except openai.APIError as e:
                    error_message = f"OpenAI API Error during transcription: {e.status_code} - {e.response}"
                    sse.publish({"message": error_message, "icon": "❌"}, type='error')
                    print(error_message)
                    return
            else:
                error_message = f"Invalid transcription model selected: {transcription_model}"
                sse.publish({"message": error_message, "icon": "❌"}, type='error')
                raise ValueError(error_message)
            
            sse.publish({"message": f"Audio transcribed: {transcript_path.name} - Phew, that was a lot of words! 📝", "icon": "✅"}, type='update')
            
            # 3. Summarize transcript
            sse.publish({"message": f"Summarizing transcript for {video_name}... Our AI is brewing some wisdom! 🧠", "icon": "✨"}, type='update')
            # Import summarize_transcript here to avoid circular dependency if summarize.py imports app.py
            from summarize import summarize_transcript 
            summarize_transcript(transcript_path, video_name)
            sse.publish({"message": f"Summary created for {video_name}. - Ta-da! Your insights are ready! 🌟", "icon": "✅"}, type='update')
            # Record history
            try:
                add_history(
                    source_url=source_url,
                    platform=platform,
                    original_filename=video_path.name,
                    video_title=video_name,
                    transcript_path=str(transcript_path),
                    summary_path=str(summary_path),
                )
            except Exception as e:
                print(f"WARN: failed to write history: {e}")

            sse.publish({"message": f"Completed! <a href='/summaries/{video_name}.md' target='_blank'>Download Summary</a> - Mission accomplished! 🚀", "icon": "🎉"}, type='complete')

        except subprocess.CalledProcessError as e:
            error_message = f"Uh oh! A tool ran into trouble! 🛠️\nCommand: {e.cmd}\nReturn Code: {e.returncode}\nStdout: {e.stdout}\nStderr: {e.stderr} 💥"
            sse.publish({"message": error_message, "icon": "❌"}, type='error')
            print(f"Subprocess Error: {e.cmd}\nStdout: {e.stdout}\nStderr: {e.stderr}")
        except Exception as e:
            error_message = f"An unexpected cosmic ray hit our servers! Error: {e} 👽"
            sse.publish({"message": error_message, "icon": "❌"}, type='error')

@app.route('/summaries/<filename>')
def download_summary(filename):
    return send_from_directory(SUMMARY_DIR, filename, as_attachment=True)

@app.route('/transcripts/<filename>')
def download_transcript(filename):
    return send_from_directory(TRANSCRIPT_DIR, filename, as_attachment=True)


@app.route('/api/history')
def api_history():
    return jsonify(list_history())


@app.route('/export')
def export_markdown():
    """Export one or more summaries or transcripts as a single Markdown file.
    Params: ids (comma-separated history ids), kind=summary|transcript
    """
    from db import DB_PATH  # not used directly; kept for future filtering
    ids_param = request.args.get('ids', '')
    kind = request.args.get('kind', 'summary')
    if kind not in ("summary", "transcript"):
        return jsonify({"error": "invalid kind"}), 400
    try:
        ids = [int(i) for i in ids_param.split(',') if i.strip()]
    except ValueError:
        return jsonify({"error": "invalid ids"}), 400

    items = list_history(limit=10000)
    by_id = {it['id']: it for it in items}
    selected = [by_id[i] for i in ids if i in by_id]
    if not selected:
        return jsonify({"error": "no matching items"}), 404

    parts = [f"# Exported {kind.title()}s ({len(selected)})"]
    for it in selected:
        title = it.get('video_title') or it.get('original_filename')
        parts.append(f"\n\n## {title}\n")
        path = it['summary_path'] if kind == 'summary' else it['transcript_path']
        try:
            text = Path(path).read_text(encoding='utf-8', errors='ignore')
        except Exception:
            text = f"[Error reading {path}]"
        parts.append(text)

    body = "\n\n---\n".join(parts)
    filename = f"export-{kind}s-{int(time.time())}.md"
    return Response(
        body,
        mimetype='text/markdown',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )

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
