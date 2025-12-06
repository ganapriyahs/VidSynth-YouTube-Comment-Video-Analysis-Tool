# For bias changes
# Import necessary libraries
from googleapiclient.discovery import build  
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled  
import config  
import logging  

# basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YouTubeClient:
    def __init__(self):
        """
        Initializes the clients for the YouTube Data API (for comments and video metadata)
        and the YouTube Transcript API when a new instance is created.
        """
        try:
            self.youtube_api = build('youtube', 'v3', developerKey=config.YOUTUBE_API_KEY)
            logger.info("YouTube Data API client built successfully.")
        except Exception as e:
            logger.error(f"Failed to build YouTube API client: {e}", exc_info=True)
            self.youtube_api = None

        # instance of the YouTubeTranscriptApi client
        self.transcript_api_client = YouTubeTranscriptApi() 

    def get_video_data(self, video_id: str) -> dict:
        """
        Fetches the transcript, comments, and video title for a given video_id.
        Returns a dictionary containing the fetched data.
        """
        transcript = self._get_transcript(video_id)
        comments = self._get_comments(video_id)
        video_title = self._get_video_title(video_id)
        
        return {
            "transcript": transcript, 
            "comments": comments,
            "video_title": video_title
        }

    def _get_transcript(self, video_id: str) -> str:
        """
        Fetches the transcript using the .fetch() method.
        Returns the full transcript as a single string, or an empty string on failure.
        """
        logger.info(f"Fetching transcript for video_id: {video_id}")
        try:
            fetched_transcript = self.transcript_api_client.fetch(video_id)
            transcript_text = " ".join([item.text for item in fetched_transcript])
            logger.info(f"Successfully fetched transcript for video_id: {video_id}")
            return transcript_text

        except NoTranscriptFound:
            logger.warning(f"NoTranscriptFound for video_id: {video_id}")
            return ""
        except TranscriptsDisabled:
            logger.warning(f"TranscriptsDisabled for video_id: {video_id}")
            return ""
        except Exception as e:
            logger.error(f"Error fetching transcript for video_id {video_id}: {e}", exc_info=True)
            return ""

    def _get_comments(self, video_id: str, max_results=25) -> str:
        """
        Fetches the top comments for a given video_id using the YouTube Data API.
        Returns the comments joined by newline characters, or an empty string on failure.
        """
        if not self.youtube_api:
            logger.error("YouTube Data API client not initialized. Cannot fetch comments.")
            return ""
        
        logger.info(f"Fetching comments for video_id: {video_id}")
        try:
            request = self.youtube_api.commentThreads().list(
                part="snippet",  
                videoId=video_id,  
                maxResults=max_results,  
                order="relevance"  
            )
            response = request.execute()

            comments = [
                item['snippet']['topLevelComment']['snippet']['textDisplay'] 
                for item in response.get('items', [])
            ]

            logger.info(f"Successfully fetched {len(comments)} comments for video_id: {video_id}")
            return "\n".join(comments)

        except Exception as e:
            logger.error(f"Error fetching comments for {video_id}: {e}", exc_info=True)
            return ""

    def _get_video_title(self, video_id: str) -> str:
        """
        Fetches the video title for a given video_id using the YouTube Data API.
        Returns the video title as a string, or "Unknown Title" on failure.
        """
        if not self.youtube_api:
            logger.error("YouTube Data API client not initialized. Cannot fetch video title.")
            return "Unknown Title"
        
        logger.info(f"Fetching video title for video_id: {video_id}")
        try:
            request = self.youtube_api.videos().list(
                part="snippet",
                id=video_id
            )
            response = request.execute()
            
            items = response.get('items', [])
            if items:
                title = items[0]['snippet']['title']
                logger.info(f"Successfully fetched video title: '{title}'")
                return title
            else:
                logger.warning(f"No video found for video_id: {video_id}")
                return "Unknown Title"
        
        except Exception as e:
            logger.error(f"Error fetching video title for {video_id}: {e}", exc_info=True)
            return "Unknown Title"

youtube_client = YouTubeClient()
