import logging
import random
import os
import yt_dlp
from googleapiclient.discovery import build

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("YouTubeClient")

class YouTubeClient:
    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        
        try:
            self.youtube_api = build('youtube', 'v3', developerKey=self.api_key)
            logger.info("✅ YouTube Data API client built successfully.")
        except Exception as e:
            logger.error(f"Failed to build YouTube API client: {e}")
            self.youtube_api = None

        # Proxy List
        self.proxy_list = [
            "http://studatgk:46cqfat5md5k@142.111.48.253:7030",
            "http://studatgk:46cqfat5md5k@31.59.20.176:6754",
            "http://studatgk:46cqfat5md5k@23.95.150.145:6114",
            "http://studatgk:46cqfat5md5k@198.23.239.134:6540",
            "http://studatgk:46cqfat5md5k@107.172.163.27:6543",
            "http://studatgk:46cqfat5md5k@198.105.121.200:6462",
            "http://studatgk:46cqfat5md5k@64.137.96.74:6641",
            "http://studatgk:46cqfat5md5k@84.247.60.125:6095",
            "http://studatgk:46cqfat5md5k@216.10.27.159:6837",
            "http://studatgk:46cqfat5md5k@142.111.67.146:5611",
        ]

    def get_video_data(self, video_id: str) -> dict:
        return {
            "transcript": self._get_transcript(video_id),
            "comments": self._get_comments(video_id),
            "video_title": self._get_video_title(video_id)
        }

    def _get_transcript(self, video_id: str) -> str:
        logger.info(f"🚀 Fetching transcript for {video_id} via yt-dlp...")
        url = f"https://www.youtube.com/watch?v={video_id}"
        

        proxies = self.proxy_list.copy()
        random.shuffle(proxies)
        proxies.append(None) 

        for proxy_url in proxies:
            safe_ip = proxy_url.split('@')[-1] if proxy_url else "Direct"
            logger.info(f"🔄 Trying: {safe_ip}")
            
            ydl_opts = {
                'skip_download': True,    
                'writesubtitles': True,    
                'writeautomaticsub': True,  
                'subtitleslangs': ['en'],   
                'quiet': True,             
                'logger': None,            
            }
            if proxy_url:
                ydl_opts['proxy'] = proxy_url

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    if 'subtitles' in info and 'en' in info['subtitles']:
                        logger.info(f"✅ Found Manual English Captions via {safe_ip}")
                        return self._download_subs_text(info['subtitles']['en'])

                    if 'automatic_captions' in info and 'en' in info['automatic_captions']:
                        logger.info(f"⚠️ Found Auto-Generated Captions via {safe_ip}")
                        return self._download_subs_text(info['automatic_captions']['en'])
                    
                    logger.warning(f"❌ Connected, but no English captions found via {safe_ip}")
                    return ""

            except Exception as e:
                logger.warning(f"⚠️ Proxy {safe_ip} error: {str(e)[:100]}")
                continue
        
        return ""

    def _download_subs_text(self, sub_list):
        """Helper to download and parse the subtitle JSON"""
        import requests
        json_url = next((item['url'] for item in sub_list if item['ext'] == 'json3'), None)
        
        if json_url:
            try:
                r = requests.get(json_url)
                data = r.json()
                text_parts = []
                for event in data.get('events', []):
                    if 'segs' in event:
                        text_parts.append("".join([s['utf8'] for s in event['segs'] if 'utf8' in s]))
                return " ".join(text_parts)
            except:
                pass
        
        # Fallback to VTT text
        try:
            return requests.get(sub_list[0]['url']).text
        except:
            return ""

    def _get_comments(self, video_id: str) -> str:
        if not self.youtube_api: return ""
        try:
            req = self.youtube_api.commentThreads().list(
                part="snippet", videoId=video_id, maxResults=25, order="relevance"
            )
            resp = req.execute()
            comments = [item['snippet']['topLevelComment']['snippet']['textDisplay'] for item in resp.get('items', [])]
            return "\n".join(comments)
        except Exception:
            return ""

    def _get_video_title(self, video_id: str) -> str:
        if not self.youtube_api: return "Unknown"
        try:
            resp = self.youtube_api.videos().list(part="snippet", id=video_id).execute()
            return resp['items'][0]['snippet']['title'] if resp.get('items') else "Unknown"
        except Exception:
            return "Unknown"

youtube_client = YouTubeClient()