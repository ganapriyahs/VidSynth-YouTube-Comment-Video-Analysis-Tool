import requests
import json
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

def get_youtube_comments(api_key, video_url, max_results=100):
    """
    Retrieve top comments from a YouTube video
    
    Args:
        api_key: Your YouTube Data API v3 key
        video_url: The YouTube video URL
        max_results: Maximum number of comments to retrieve (default 100)
    """
    
    # Extract video ID from URL
    video_id = extract_video_id(video_url)
    if not video_id:
        print("Error: Invalid YouTube URL")
        return None
    
    print(f"Video ID: {video_id}")
    print(f"Fetching up to {max_results} comments...\n")
    
    # YouTube API endpoint for commentThreads: access google apis version 3, with specific resource "commentThreads"
    base_url = "https://www.googleapis.com/youtube/v3/commentThreads"
    
    comments_data = []
    next_page_token = None
    
    while len(comments_data) < max_results:
        # Parameters for the API request
        params = {
            'part': 'snippet,replies',
            'videoId': video_id,
            'key': api_key,
            'maxResults': min(100, max_results - len(comments_data)),  # API max is 100 per request
            'order': 'relevance',  # Get top/most relevant comments
            'textFormat': 'plainText'
        }
        
        if next_page_token:
            params['pageToken'] = next_page_token
        
        # Make the API request
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Print raw API response
            print(f"API Response (Page {len(comments_data)//100 + 1}):")
            print("=" * 80)
            print(json.dumps(data, indent=2))
            print("=" * 80)
            print()
            
            # Extract comments from response
            if 'items' in data:
                comments_data.extend(data['items'])
                
                # Check if there are more pages
                next_page_token = data.get('nextPageToken')
                if not next_page_token:
                    break
            else:
                print("No comments found in response")
                break
                
        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {e}")
            if response.status_code == 403:
                print("403 Error: Check if your API key is valid and has YouTube Data API v3 enabled")
            elif response.status_code == 404:
                print("404 Error: Video not found or comments are disabled")
            return None
    
    print(f"\nTotal comments retrieved: {len(comments_data)}")
    
    # Also print a formatted summary of comments
    print("\n" + "=" * 80)
    print("FORMATTED COMMENT SUMMARY")
    print("=" * 80)
    
    for i, item in enumerate(comments_data[:max_results], 1):
        snippet = item['snippet']['topLevelComment']['snippet']
        print(f"\nComment #{i}")
        print(f"Author: {snippet['authorDisplayName']}")
        print(f"Likes: {snippet['likeCount']}")
        print(f"Posted: {snippet['publishedAt']}")
        print(f"Text: {snippet['textDisplay'][:200]}..." if len(snippet['textDisplay']) > 200 else f"Text: {snippet['textDisplay']}")
        
        # Check for replies
        if 'replies' in item:
            print(f"Reply count: {item['snippet']['totalReplyCount']}")
    
    return comments_data

# Main execution
if __name__ == "__main__":
    # IMPORTANT: Replace with your actual API key
    API_KEY = "YOUR_API_KEY_HERE"
    VIDEO_URL = "https://www.youtube.com/watch?v=j6liCsCSUoM"
    
    if API_KEY == "YOUR_API_KEY_HERE":
        print("Please replace 'YOUR_API_KEY_HERE' with your actual YouTube API key")
        print("Follow the instructions above to obtain an API key from Google Cloud Console")
    else:
        comments = get_youtube_comments(API_KEY, VIDEO_URL, max_results=10)