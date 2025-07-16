# TranscriptAI GPT

TranscriptAI GPT is a local automation agent that converts videos into audio, transcribes speech using OpenAI Whisper, and summarizes the content using OpenAI GPT-3.5/4.

## Features

- **Video Ingestion**: Detects and processes all `.mp4` videos in a specified folder.
- **Audio Extraction**: Converts each video into a `.wav` audio file.
- **Transcription**: Generates text transcripts using OpenAI Whisper.
- **Summarization**: Uses GPT-3.5/4 to create concise, bullet-point summaries.
- **Markdown Output**: Creates a separate Markdown file for each video, containing the title, summary, and full transcript.
- **Reusable**: The script is designed to be re-runnable and will skip any videos that have already been processed.

## Prerequisites

- Python 3.8 or higher
- **`ffmpeg`**: A command-line tool for handling multimedia files. It must be installed and available in your system's PATH.
  - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH, or use Chocolatey: `choco install ffmpeg`
  - **macOS**: `brew install ffmpeg` (using Homebrew)
  - **Linux (Ubuntu/Debian)**: `sudo apt update && sudo apt install ffmpeg`
- **Redis**: An in-memory data structure store used for real-time updates.
  - **Windows**: Download from [github.com/microsoftarchive/redis/releases](https://github.com/microsoftarchive/redis/releases) or use Chocolatey: `choco install redis-64`
  - **macOS**: `brew install redis`
  - **Linux (Ubuntu/Debian)**: `sudo apt install redis-server`
- An OpenAI API key.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/vidmelt.git
    cd vidmelt
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install OpenAI Whisper:**
    ```bash
    pip install git+https://github.com/openai/whisper.git
    ```

4.  **Configure your API Key:**
    Create a `.env` file in the root of the project by copying the example file:
    ```bash
    cp .env.example .env
    ```
    Open the `.env` file and add your OpenAI API key:
    ```
    OPENAI_API_KEY="your-api-key-here"
    ```

## Usage

1.  **Start the Web Application**:
    ```bash
    python3 app.py
    ```
    Open your web browser and navigate to `http://127.0.0.1:5000/` (or the address shown in your terminal).

2.  **Upload Video**: Use the web interface to upload your `.mp4` video file.

3.  **Monitor Progress**: The web interface will provide real-time updates on the processing status.

4.  **View Summaries**: Once completed, a link to download the summary Markdown file will be provided on the web page.

## Folder Structure

```
video-ai-agent/
├── videos/              # Input videos (.mp4)
├── audio_files/         # Extracted audio files (.wav)
├── transcripts/         # Whisper transcript output (.txt)
├── summaries/           # Final .md files with summaries
├── summarize.py         # GPT summarization script
├── app.py               # Flask web application
```