from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

app = FastAPI()

class VideoRequest(BaseModel):
    url: str

class SummaryResponse(BaseModel):
    summary: str

def get_video_id(url: str) -> str:
    """Extract video ID from YouTube URL."""
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    raise ValueError("Invalid YouTube URL")

def get_transcript(video_id: str) -> str:
    """Fetch the transcript of a YouTube video."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([t["text"] for t in transcript])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching transcript: {str(e)}")

@app.post("/summarize", response_model=SummaryResponse)
async def summarize_video(request: VideoRequest):
    try:
        # Extract video ID and fetch transcript
        video_id = get_video_id(request.url)
        transcript = get_transcript(video_id)

        # Call OpenRouter API for summarization
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": os.getenv("YOUR_SITE_URL"),
                "X-Title": os.getenv("YOUR_SITE_NAME"),
            },
            model=os.getenv("MODEL"),
            messages=[
                {
                    "role": "user",
                    "content": f"Summarize this text: {transcript}"
                }
            ]
        )

        # Extract and return the summary
        summary = completion.choices[0].message.content.strip()
        return SummaryResponse(summary=summary)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error summarizing video: {str(e)}")
