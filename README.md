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

-   **Windows (Recommended: WSL2)**:
    The most reliable way to run Redis on Windows is via Windows Subsystem for Linux 2 (WSL2).
    1.  **Install WSL2**: Open PowerShell or Command Prompt as Administrator and run:
        ```bash
        wsl --install
        ```
        Restart your computer when prompted.
    2.  **Install a Linux Distribution**: By default, Ubuntu is installed. You can open the Ubuntu app from your Start Menu.
    3.  **Install Redis within WSL2**: Once in your WSL2 Linux terminal (e.g., Ubuntu):
        ```bash
        sudo apt update
        sudo apt install redis-server
        sudo systemctl enable redis-server # Enable Redis to start on boot
        sudo systemctl start redis-server # Start the Redis service
        ```
    *Alternatively (Less Recommended for Production): Use Scoop (if installed):*
    ```bash
    scoop install redis
    ```
    *After Scoop installation, start the Redis server from PowerShell/CMD:*
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
This command installs the core runtime (Flask, SSE, Redis client) together with `openai`, `ffmpeg-python`, `openai-whisper`, and pinned `numpy/numba` versions that keep Whisper CLI working.

### 3. Verify Your Environment

Before launching the web app, run the built-in doctor to confirm FFmpeg, Redis, Whisper, and your OpenAI credentials are ready:

```bash
python -m vidmelt.doctor
```

Any failing check will be listed with remediation hints; fix them before continuing.

### 4. Configure Your OpenAI API Key 🔑

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
-   Once processing is complete, a link to download the summary Markdown and the raw transcript will appear.
-   Visit `/jobs` to review recent processing history and re-download summaries.

### Optional: Batch Mode (CLI)

To process an entire folder of `.mp4` files without launching the web UI:

```bash
python -m vidmelt.batch /path/to/videos --model whisper-base
```

Add `--dry-run` to preview the work queue. The CLI reuses the core pipeline and skips videos that already have a Markdown summary in `summaries/`.

### Optional: Redis-less Events

By default Vidmelt streams progress using Redis. To run without Redis (useful on single-node or WSL setups), set:

```bash
export VIDMELT_EVENT_STRATEGY=in-memory
```

This enables an in-process Server-Sent Events channel. Limit usage to one Flask instance per machine because events are kept in-memory.

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
├── logs/                 # 🪵 FFmpeg/Whisper diagnostic logs per video
└── templates/            # 🖥️ HTML templates for the web interface
    └── index.html
```
