# Import necessary libraries
from googleapiclient.discovery import build  
# We REMOVE the import for youtube_transcript_api
import config  
import logging  
import re # We need the regex library to clean the SRT file format

# basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YouTubeClient:
    def __init__(self):
        """
        Initializes the YouTube Data API client (v3) for both comments and captions.
        """
        try:
            # We use the existing API key to build the authorized client
            self.youtube_api = build('youtube', 'v3', developerKey=config.YOUTUBE_API_KEY)
            logger.info("YouTube Data API client built successfully.")
        except Exception as e:
            logger.error(f"Failed to build YouTube API client: {e}", exc_info=True)
            self.youtube_api = None

    # def get_video_data(self, video_id: str) -> dict:
    #     """
    #     Main entry point: Fetches both captions and comments.
    #     """
    #     transcript = self._get_transcript(video_id)
    #     comments = self._get_comments(video_id)
    #     return {"transcript": transcript, "comments": comments}

    def get_video_data(self, video_id: str) -> dict:
        """
        Main entry point: Fetches ONLY comments.
        """
        # Fresh client each time, fresh connections
        self.youtube_api = build('youtube', 'v3', developerKey=config.YOUTUBE_API_KEY)
        comments = self._get_comments(video_id)
        return {"comments": comments}

    
    # def _get_transcript(self, video_id: str) -> str:
    #     """
    #     Fetches the official caption track using the YouTube Data API.
    #     This method replaces the screen-scraping library.
    #     """
    #     if not self.youtube_api:
    #         logger.error("YouTube Data API client not initialized. Cannot fetch captions.")
    #         return ""

    #     logger.info(f"Fetching captions track list for video_id: {video_id}")
        
    #     try:
    #         # 1. List available caption tracks
    #         list_request = self.youtube_api.captions().list(part="snippet", videoId=video_id)
    #         list_response = list_request.execute()

    #         caption_id = None
            
    #         # 2. Find the BEST track ID (Prioritize non-auto-generated English)
    #         for item in list_response.get('items', []):
    #             # We check for English and ensure it's not the auto-generated one (if possible)
    #             if item['snippet']['language'] == 'en' and not item['snippet'].get('isAutomatic'):
    #                 caption_id = item['id']
    #                 break
            
    #         # 3. Fallback: If no manual English is found, take the first one available
    #         if not caption_id and list_response.get('items'):
    #             caption_id = list_response['items'][0]['id']

    #         if not caption_id:
    #             logger.warning(f"⛔ No official caption track found for video_id: {video_id}.")
    #             return ""
            
    #         # 4. Download the caption track as SRT format
    #         download_request = self.youtube_api.captions().download(
    #             id=caption_id,
    #             tfmt='srt' # Requesting SubRip Text format
    #         )
    #         download_response = download_request.execute() 
            
    #         # 5. Clean up the SRT text using regex
    #         # Regex removes timestamps, sequence numbers, and formatting tags
    #         cleaned_text = re.sub(r'(\d+\s*|\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\s*|\n{2,})', ' ', download_response)
    #         # Remove any remaining HTML tags or extra spaces
    #         cleaned_text = re.sub(r'<[^>]*>', ' ', cleaned_text).strip()
            
    #         logger.info(f"✅ Successfully fetched official captions for video_id: {video_id}")
    #         return cleaned_text

    #     except Exception as e:
    #         # The API will throw an error if captions are restricted or missing entirely
    #         logger.error(f"❌ Error fetching captions via API for {video_id}: {e}", exc_info=True)
    #         return ""

    

    def _get_comments(self, video_id: str, max_results=25) -> str:
        """
        Fetches the top comments (by relevance) for a given video_id using the YouTube Data API.
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

            logger.info(f"✅ Successfully fetched {len(comments)} comments for video_id: {video_id}")
            return "\n".join(comments)

        except Exception as e:
            logger.error(f"❌ Error fetching comments for {video_id}: {e}", exc_info=True)
            return ""

youtube_client = YouTubeClient() # this is run upon importing from main.py