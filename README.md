# 🎬 Vidmelt: AI-Powered Video Transcription & Summarization 🚀

Vidmelt is a local automation agent designed to effortlessly transform your video content into actionable insights. It converts videos into audio, transcribes speech using OpenAI Whisper, and summarizes the content using advanced OpenAI GPT models. All accessible through a simple, real-time web interface!

## ✨ Features

-   **🎥 Video Ingestion**: Easily upload your `.mp4` video files via a user-friendly web interface.
-   **🎧 Audio Extraction**: Automatically converts uploaded videos into high-quality `.wav` audio files.
-   **📝 Accurate Transcription**: Generates precise text transcripts using OpenAI Whisper.
-   **🧠 Intelligent Summarization**: Leverages powerful OpenAI GPT models (like GPT-4o) to create concise, clean, and insightful summaries.
-   **📄 Markdown Output**: Produces well-structured Markdown files for each video, containing the summary.
-   **🔄 Real-time Progress**: Get live updates on the processing status directly in your browser.
-   **🔗 Local Access**: Download your summaries directly from the web interface.

## 🛠️ Prerequisites

Before you get started, ensure you have the following installed on your system:

-   **Python 3.8 or higher**: 🐍 The core language for Vidmelt.
-   **FFmpeg**: 🎬 A powerful command-line tool essential for video and audio processing.
-   **Redis**: 📊 An in-memory data store used for real-time communication (Server-Sent Events).
-   **OpenAI API Key**: 🔑 Required for transcription and summarization services.

---

### Installation Guides for Prerequisites:

#### 1. Python 🐍

If you don't have Python installed, download it from the [official Python website](https://www.python.org/downloads/).

#### 2. FFmpeg 🎬

FFmpeg must be installed and accessible in your system's PATH.

-   **Windows**:
    1.  Download a static build from [ffmpeg.org/download.html](https://ffmpeg.org/download.html).
    2.  Extract the downloaded archive to a directory (e.g., `C:\ffmpeg`).
    3.  Add the `bin` directory (e.g., `C:\ffmpeg\bin`) to your system's PATH environment variable.
    *Alternatively, use Chocolatey (if installed):*
    ```bash
    choco install ffmpeg
    ```

-   **macOS**:
    Using [Homebrew](https://brew.sh/):
    ```bash
    brew install ffmpeg
    ```

-   **Linux (Ubuntu/Debian)**:
    ```bash
    sudo apt update
    sudo apt install ffmpeg
    ```

#### 3. Redis 📊

Redis is used by `flask-sse` for real-time updates.

-   **Windows**:
    1.  Download the MSOpenTech Redis release from [github.com/microsoftarchive/redis/releases](https://github.com/microsoftarchive/redis/releases).
    2.  Run the `.msi` installer.
    *Alternatively, use Chocolatey (if installed):*
    ```bash
    choco install redis-64
    ```
    *After installation, start the Redis server:*
    ```bash
    redis-server
    ```

-   **macOS**:
    Using [Homebrew](https://brew.sh/):
    ```bash
    brew install redis
    brew services start redis # To start Redis automatically on login
    ```
    *To start manually:*
    ```bash
    redis-server
    ```

-   **Linux (Ubuntu/Debian)**:
    ```bash
    sudo apt update
    sudo apt install redis-server
    sudo systemctl enable redis-server # Enable Redis to start on boot
    sudo systemctl start redis-server # Start the Redis service
    ```

#### 4. OpenAI Whisper (Python Library) 🗣️

This will be installed as part of the Python dependencies, but it's good to know what it is!

---

## 🚀 Getting Started

Follow these steps to set up and run Vidmelt:

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/vidmelt.git
cd vidmelt
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```
This command will install all necessary Python libraries, including `openai`, `ffmpeg-python`, `python-dotenv`, `Flask`, and `flask-sse`, and the `openai-whisper` library.

### 3. Configure Your OpenAI API Key 🔑

Create a `.env` file in the root of your project by copying the example:

```bash
cp .env.example .env
```

Open the newly created `.env` file and add your OpenAI API key:

```
OPENAI_API_KEY="your-api-key-here"
```
**Important**: Replace `"your-api-key-here"` with your actual OpenAI API key. Keep this file private and do not commit it to version control!

## 🏃 How to Run

### 1. Start the Redis Server

Ensure your Redis server is running as per the installation instructions above.

### 2. Start the Web Application

From the project's root directory, run:

```bash
python3 app.py
```

### 3. Access the Web Interface

Open your web browser and navigate to `http://127.0.0.1:5000/` (or the address shown in your terminal, usually `http://localhost:5000/`).

### 4. Upload and Process

-   Use the web interface to upload your `.mp4` video file.
-   Monitor the real-time progress updates directly on the page.
-   Once processing is complete, a link to download the summary Markdown file will appear.

## 📂 Project Structure

```
vidmelt/
├── .gitattributes
├── .gitignore
├── .env.example          # Example file for environment variables
├── LICENSE
├── README.md             # This file!
├── app.py                # 🌐 Flask web application (handles uploads, SSE, orchestrates processing)
├── summarize.py          # 🧠 Handles GPT summarization logic
├── requirements.txt      # 📦 Python dependencies
├── videos/               # 📥 Input videos (.mp4 files go here)
│   └── .gitkeep
├── audio_files/          # 🎧 Extracted audio files (.wav)
│   └── .gitkeep
├── transcripts/          # 📝 Whisper transcript output (.txt)
│   └── .gitkeep
├── summaries/            # 📄 Final .md files with summaries
│   └── .gitkeep
└── templates/            # 🖥️ HTML templates for the web interface
    └── index.html
```
