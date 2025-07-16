
import os
import openai
from pathlib import Path

# Directories
TRANSCRIPT_DIR = Path("transcripts")
SUMMARY_DIR = Path("summaries")

def summarize_transcript(transcript_path: Path, video_title: str):
    """
    Summarizes a transcript using OpenAI GPT-3.5/4.
    """
    try:
        with open(transcript_path, "r") as f:
            transcript_text = f.read()

        # Truncate to 12,000 tokens (approx. 4000 words)
        if len(transcript_text.split()) > 4000:
            transcript_text = " ".join(transcript_text.split()[:4000])

        client = openai.OpenAI()

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert summarization agent. "
                        "Your goal is to create a clear, concise, and professional summary of a video transcript."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Please generate a summary for the video titled '{video_title}'.\n\n"
                        "The summary should include:\n"
                        "1. A short, engaging title.\n"
                        "2. A 2-3 sentence overview of the video's main topic.\n"
                        "3. A bulleted list of the 3-5 most important key takeaways.\n\n"
                        f"Here is the transcript:\n\n{transcript_text}"
                    )
                }
            ]
        )

        summary = response.choices[0].message.content

        # 4. File Output
        summary_path = SUMMARY_DIR / f"{video_title}.md"
        with open(summary_path, "w") as f:
            f.write(summary)

        print(f"Summary for {video_title} created successfully.")

    except Exception as e:
        print(f"Error summarizing {video_title}: {e}")
