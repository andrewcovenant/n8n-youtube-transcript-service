"""
YouTube Transcript Microservice
A lightweight FastAPI service to extract YouTube video transcripts
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    InvalidVideoId
)
from youtube_transcript_api.proxies import WebshareProxyConfig
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="YouTube Transcript Service",
    description="Microservice for extracting YouTube video transcripts",
    version="1.0.0"
)

# Request/Response Models
class TranscriptRequest(BaseModel):
    video_id: str
    language: Optional[str] = "en"


class TranscriptSegment(BaseModel):
    text: str
    start: float
    duration: float


class DetailedTranscriptResponse(BaseModel):
    success: bool
    videoId: str
    transcript: Optional[str]
    raw: Optional[List[TranscriptSegment]]
    language: Optional[str]


class SimpleTranscriptResponse(BaseModel):
    success: bool
    videoId: str
    transcript: Optional[str]
    hasTranscript: bool


class TimestampedSegment(BaseModel):
    text: str
    start: float
    end: float
    startFormatted: str
    endFormatted: str


class TimestampedTranscriptResponse(BaseModel):
    success: bool
    videoId: str
    segments: Optional[List[TimestampedSegment]]
    language: Optional[str]


# Proxy configuration (optional - set via environment variables)
PROXY_USERNAME = os.getenv("WEBSHARE_PROXY_USERNAME", "")
PROXY_PASSWORD = os.getenv("WEBSHARE_PROXY_PASSWORD", "")
PROXY_LOCATIONS = os.getenv("PROXY_LOCATIONS", "")  # Comma-separated country codes like "us,de"


def get_api_instance():
    """
    Create YouTubeTranscriptApi instance with optional proxy configuration
    """
    # Check if Webshare proxy credentials are provided
    if PROXY_USERNAME and PROXY_PASSWORD:
        logger.info("Using Webshare rotating residential proxies")
        
        # Parse location filter if provided
        filter_locations = None
        if PROXY_LOCATIONS:
            filter_locations = [loc.strip().lower() for loc in PROXY_LOCATIONS.split(",")]
            logger.info(f"Filtering proxy IPs to locations: {filter_locations}")
        
        # Create proxy config
        proxy_config = WebshareProxyConfig(
            proxy_username=PROXY_USERNAME,
            proxy_password=PROXY_PASSWORD,
            filter_ip_locations=filter_locations if filter_locations else None
        )
        
        return YouTubeTranscriptApi(proxy_config=proxy_config)
    else:
        logger.info("Using direct connection (no proxy)")
        return YouTubeTranscriptApi()


# Helper Functions
def format_timestamp(seconds: float) -> str:
    """
    Convert seconds to HH:MM:SS.mmm format
    
    Args:
        seconds: Time in seconds
    
    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def extract_transcript(video_id: str, language: str = "en") -> tuple[bool, Optional[str], Optional[List[Dict[str, Any]]]]:
    """
    Extract transcript from YouTube video
    
    Args:
        video_id: YouTube video ID
        language: Language code (default: "en")
    
    Returns:
        Tuple of (success, transcript_text, raw_segments)
    """
    try:
        # Create API instance with optional proxy support
        api = get_api_instance()
        fetched_transcript = api.fetch(video_id, languages=[language])
        
        # Extract the transcript list from the FetchedTranscript object
        transcript_list = fetched_transcript.to_raw_data()
        
        # Combine text segments
        transcript_text = " ".join([segment["text"] for segment in transcript_list])
        
        return True, transcript_text, transcript_list
    
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable, InvalidVideoId) as e:
        logger.warning(f"Could not fetch transcript for video {video_id}: {str(e)}")
        return False, None, None
    
    except Exception as e:
        # Catch all other exceptions (including XML parsing errors from YouTube API)
        logger.warning(f"Error fetching transcript for video {video_id}: {str(e)}")
        return False, None, None


# API Endpoints

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify service is running
    """
    return {"status": "healthy"}


@app.get("/transcript/{video_id}", response_model=SimpleTranscriptResponse)
async def get_transcript_simple(
    video_id: str,
    lang: Optional[str] = Query("en", description="Language code for transcript")
):
    """
    Get YouTube video transcript (simple format)
    
    Args:
        video_id: YouTube video ID
        lang: Language code (default: "en")
    
    Returns:
        Simple transcript response with combined text
    """
    success, transcript_text, _ = extract_transcript(video_id, lang)
    
    if success:
        return SimpleTranscriptResponse(
            success=True,
            videoId=video_id,
            transcript=transcript_text,
            hasTranscript=True
        )
    else:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "videoId": video_id,
                "transcript": None,
                "hasTranscript": False
            }
        )


@app.post("/transcript", response_model=DetailedTranscriptResponse)
async def get_transcript_detailed(request: TranscriptRequest):
    """
    Get YouTube video transcript (detailed format)
    
    Args:
        request: TranscriptRequest with video_id and language
    
    Returns:
        Detailed transcript response with raw segments and timing information
    """
    success, transcript_text, raw_segments = extract_transcript(
        request.video_id,
        request.language or "en"
    )
    
    if success:
        # Convert raw segments to proper format
        formatted_segments = [
            TranscriptSegment(
                text=seg["text"],
                start=seg["start"],
                duration=seg["duration"]
            )
            for seg in raw_segments
        ]
        
        return DetailedTranscriptResponse(
            success=True,
            videoId=request.video_id,
            transcript=transcript_text,
            raw=formatted_segments,
            language=request.language or "en"
        )
    else:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "videoId": request.video_id,
                "transcript": None,
                "raw": None,
                "language": request.language or "en"
            }
        )


@app.get("/transcript/{video_id}/timestamps", response_model=TimestampedTranscriptResponse)
async def get_transcript_with_timestamps(
    video_id: str,
    lang: Optional[str] = Query("en", description="Language code for transcript")
):
    """
    Get YouTube video transcript with formatted timestamps
    
    Args:
        video_id: YouTube video ID
        lang: Language code (default: "en")
    
    Returns:
        Transcript segments with start/end times in both seconds and formatted strings (HH:MM:SS.mmm)
    """
    success, _, raw_segments = extract_transcript(video_id, lang)
    
    if success:
        # Convert raw segments to timestamped format
        timestamped_segments = [
            TimestampedSegment(
                text=seg["text"],
                start=seg["start"],
                end=seg["start"] + seg["duration"],
                startFormatted=format_timestamp(seg["start"]),
                endFormatted=format_timestamp(seg["start"] + seg["duration"])
            )
            for seg in raw_segments
        ]
        
        return TimestampedTranscriptResponse(
            success=True,
            videoId=video_id,
            segments=timestamped_segments,
            language=lang
        )
    else:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "videoId": video_id,
                "segments": None,
                "language": lang
            }
        )


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with service information
    """
    return {
        "service": "YouTube Transcript Microservice",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "simple_transcript": "/transcript/{video_id}?lang=en",
            "detailed_transcript": "/transcript (POST)",
            "timestamped_transcript": "/transcript/{video_id}/timestamps?lang=en"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

