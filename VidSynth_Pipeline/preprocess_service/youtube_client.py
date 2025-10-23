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
        Initializes the clients for the YouTube Data API (for comments)
        and the YouTube Transcript API when a new instance is created.
        """
        try:
            self.youtube_api = build('youtube', 'v3', developerKey=config.YOUTUBE_API_KEY)
            logger.info("YouTube Data API client built successfully.")
        except Exception as e:
            logger.error(f"Failed to build YouTube API client: {e}", exc_info=True)
            self.youtube_api = None

        # instance of the YouTubeTranscriptApi client
        # This instance will be used to call the transcript fetching methods
        self.transcript_api_client = YouTubeTranscriptApi() 

    # Method to get both transcript and comments for a given video ID
    def get_video_data(self, video_id: str) -> dict:
        """
        Fetches both the transcript and comments for a given video_id
        by calling the internal helper methods _get_transcript and _get_comments.
        Returns a dictionary containing the fetched data.
        """
        transcript = self._get_transcript(video_id)
        comments = self._get_comments(video_id)
        return {"transcript": transcript, "comments": comments}

    def _get_transcript(self, video_id: str) -> str:
        """
        Fetches the transcript using the .fetch() method, which returns
        a list of transcript segment objects. Accesses text via item.text.
        Returns the full transcript as a single string, or an empty string on failure.
        """
        logger.info(f"Fetching transcript for video_id: {video_id}")
        try:
            fetched_transcript = self.transcript_api_client.fetch(video_id)
            transcript_text = " ".join([item.text for item in fetched_transcript])
            # Log success
            logger.info(f"Successfully fetched transcript for video_id: {video_id}")
            return transcript_text

        except NoTranscriptFound:
            logger.warning(f"NoTranscriptFound: No transcript of any kind found for video_id: {video_id}.")
            return ""
        except TranscriptsDisabled:
            logger.warning(f"TranscriptsDisabled: Transcripts are disabled for video_id: {video_id}.")
            return ""
        except Exception as e:
            logger.error(f"Error fetching transcript for video_id {video_id}: {e}", exc_info=True)
            return ""

    def _get_comments(self, video_id: str, max_results=25) -> str:
        """
        Fetches the top comments (by relevance) for a given video_id using the YouTube Data API.
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

youtube_client = YouTubeClient()

