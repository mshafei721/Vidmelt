import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from summarize import summarize_transcript

# Directories
VIDEO_DIR = Path("videos")
AUDIO_DIR = Path("audio_files")
TRANSCRIPT_DIR = Path("transcripts")
SUMMARY_DIR = Path("summaries")

def convert_video_to_audio(video_path: Path, audio_path: Path):
    """Converts a video file to a WAV audio file using ffmpeg."""
    print(f"Converting {video_path.name} to audio...")
    try:
        subprocess.run([
            "ffmpeg",
            "-i", str(video_path),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(audio_path)
        ], check=True, capture_output=True, text=True)
        print(f"Successfully converted {video_path.name} to {audio_path.name}.")
    except subprocess.CalledProcessError as e:
        print(f"Error converting {video_path.name} to audio.")
        print(f"FFmpeg stderr: {e.stderr}")
        raise

def transcribe_audio(audio_path: Path, video_name: str):
    """Transcribes an audio file using OpenAI Whisper."""
    print(f"Transcribing {video_name}...")
    try:
        # Note: The whisper CLI automatically appends .txt to the output file name.
        subprocess.run([
            "whisper",
            str(audio_path),
            "--model", "base",
            "--language", "en",
            "--output_dir", str(TRANSCRIPT_DIR)
        ], check=True, capture_output=True, text=True)
        print(f"Successfully transcribed {video_name}.")
    except subprocess.CalledProcessError as e:
        print(f"Error transcribing {video_name}.")
        print(f"Whisper stderr: {e.stderr}")
        raise

def process_video(video_path: Path):
    """
    Processes a single video file: converts to audio, transcribes, and summarizes.
    """
    video_name = video_path.stem
    audio_path = AUDIO_DIR / f"{video_name}.wav"
    transcript_path = TRANSCRIPT_DIR / f"{video_name}.txt"
    summary_path = SUMMARY_DIR / f"{video_name}.md"

    # 1. Skip if summary already exists
    if summary_path.exists():
        print(f"Skipping '{video_name}': Summary already exists.")
        return

    try:
        # 2. Convert video to audio
        if not audio_path.exists():
            convert_video_to_audio(video_path, audio_path)

        # 3. Transcribe audio to text
        if not transcript_path.exists():
            transcribe_audio(audio_path, video_name)
        
        # 4. Summarize transcript
        print(f"Summarizing transcript for {video_name}...")
        summarize_transcript(transcript_path, video_name)

    except Exception as e:
        print(f"Failed to process '{video_name}'. Reason: {e}")





def main():
    """
    Main function to orchestrate the video processing workflow.
    """
    load_dotenv()
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in .env file.")
        print("Please create a .env file and add your OpenAI API key.")
        return

    # Create directories if they don't exist
    for directory in [VIDEO_DIR, AUDIO_DIR, TRANSCRIPT_DIR, SUMMARY_DIR]:
        directory.mkdir(exist_ok=True)

    # Find video files to process
    video_files = list(VIDEO_DIR.glob("*.mp4"))
    if not video_files:
        print(f"No .mp4 videos found in the '{VIDEO_DIR}' directory.")
        print("Please add video files to this directory and run the script again.")
        return

    print(f"Found {len(video_files)} video(s) to process.")

    # Process each video file
    for video_path in video_files:
        process_video(video_path)

    print("\nWorkflow complete.")

if __name__ == "__main__":
    main()