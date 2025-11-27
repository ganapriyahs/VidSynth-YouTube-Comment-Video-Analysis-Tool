from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    parsed_url = urlparse(url)
    if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query)['v'][0]
    elif parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    return None

def map_speaker_language(speaker):
    """
    'Speaker' was manually assigned when forming test set and part of meta data.
    used to request precice languge based on speaker, instead of
    iterating through many

    """
    map = {
        "English female":"en",
        "English male": "en",
        "English but accent": "en",
        "English Jamaican accent": "en",
        "Hindi": "hi",
        "Spanish": "es",
        "Arabic": "ar",
        "French": "fr",
        "German": "de",
        "Japanese": "ja"
    }
    return map[speaker]

def fetch_transcript(video_url, speaker):
    # Extract video ID from URL
    video_id = extract_video_id(video_url)
    if not video_id:
        print("Error: Invalid YouTube URL")
        return None
    
    ytt_api = YouTubeTranscriptApi()

    language = map_speaker_language(speaker)
    
    fetched_trans = ytt_api.fetch(video_id, languages=[language]) #'en', 'hi', 'es', 'ar', 'fr', 'de', 'ja'
    transcript_text = " ".join([item.text for item in fetched_trans])
    print(f"Succesfully retrieved transcript for {video_id}, and with language {language}\n")
    return transcript_text


