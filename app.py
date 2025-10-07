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
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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


# Helper Functions
def create_browser_session():
    """
    Create a requests session that mimics a real browser
    """
    session = requests.Session()
    
    # Add retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Browser-like headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    })
    
    return session


def extract_transcript(video_id: str, language: str = "en") -> tuple[bool, Optional[str], Optional[List[Dict[str, Any]]]]:
    """
    Extract transcript from YouTube video with browser mimicking
    
    Args:
        video_id: YouTube video ID
        language: Language code (default: "en")
    
    Returns:
        Tuple of (success, transcript_text, raw_segments)
    """
    try:
        # Create a browser-like session
        session = create_browser_session()
        
        # Monkey-patch the session into the YouTubeTranscriptApi
        # This makes all requests look like they're coming from a real browser
        import youtube_transcript_api._api as yt_api
        original_get = requests.get
        
        def patched_get(url, **kwargs):
            kwargs['headers'] = session.headers
            kwargs['timeout'] = kwargs.get('timeout', 10)
            return original_get(url, **kwargs)
        
        # Temporarily replace requests.get with our patched version
        requests.get = patched_get
        
        try:
            # Create API instance and fetch transcript
            api = YouTubeTranscriptApi()
            fetched_transcript = api.fetch(video_id, languages=[language])
            
            # Extract the transcript list from the FetchedTranscript object
            transcript_list = fetched_transcript.to_raw_data()
            
            # Combine text segments
            transcript_text = " ".join([segment["text"] for segment in transcript_list])
            
            return True, transcript_text, transcript_list
        finally:
            # Restore original requests.get
            requests.get = original_get
    
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
            "detailed_transcript": "/transcript (POST)"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

