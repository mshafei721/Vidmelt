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
- `ffmpeg` installed and available in your system's PATH.
  - **On Ubuntu/Debian:** `sudo apt update && sudo apt install ffmpeg`
  - **On macOS (using Homebrew):** `brew install ffmpeg`
  - **On Windows (using Chocolatey):** `choco install ffmpeg`
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

1.  **Add Videos**: Place your `.mp4` video files into the `videos/` directory.

2.  **Run the script**: Execute the main script from the project's root directory.
    ```bash
    python3 main.py
    ```

3.  **View Summaries**: The script will process each video and generate a corresponding Markdown file in the `summaries/` directory.

## Folder Structure

```
video-ai-agent/
├── videos/              # Input videos (.mp4)
├── audio_files/         # Extracted audio files (.wav)
├── transcripts/         # Whisper transcript output (.txt)
├── summaries/           # Final .md files with summaries
├── summarize.py         # GPT summarization script
├── main.py              # Main workflow orchestration
```