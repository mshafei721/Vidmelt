
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
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes video transcripts."
                },
                {
                    "role": "user",
                    "content": f"Summarize the following transcript in bullet points:\n\n{transcript_text}"
                }
            ]
        )

        summary = response.choices[0].message.content

        # 4. File Output
        summary_path = SUMMARY_DIR / f"{video_title}.md"
        with open(summary_path, "w") as f:
            f.write(f"# {video_title}\n\n")
            f.write("## Summary\n")
            f.write(summary)
            f.write("\n\n## Transcript\n")
            f.write(transcript_text)

        print(f"Summary for {video_title} created successfully.")

    except Exception as e:
        print(f"Error summarizing {video_title}: {e}")
