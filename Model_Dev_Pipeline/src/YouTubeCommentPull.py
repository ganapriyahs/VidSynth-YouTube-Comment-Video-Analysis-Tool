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

    # print(f"Video ID: {video_id}")
    # print(f"Fetching up to {max_results} comments...\n")
    
    # YouTube API endpoint for commentThreads
    base_url = "https://www.googleapis.com/youtube/v3/commentThreads"
    
    comments_data = []
   
    params = {
        'part': 'snippet,replies', # remove 'replies' if we do not want to use them
        'videoId': video_id,
        'key': api_key,
        'maxResults': max_results,
        # for larger requests (other version of code):
        #'maxResults': min(100, max_results - len(comments_data)),  # API max is 100 per request
        'order': 'relevance',  # Get top/most relevant comments
        'textFormat': 'plainText'
    }
    
    ### NO next page token needed because 2 - 50 comments can be retieved in a single API request
    # if next_page_token:
    #     params['pageToken'] = next_page_token
    
    # Make the API request
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        
        # Extract comments from response
        if 'items' in data:
            comments_data.extend(data['items'])
            
            # Check if there are more pages
            # next_page_token = data.get('nextPageToken')
            # if not next_page_token:
            #     #break
            #     pass 
        else:
            print("No comments found in response")
            pass
            
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        if response.status_code == 403:
            print("403 Error: Check if your API key is valid and has YouTube Data API v3 enabled")
        elif response.status_code == 404:
            print("404 Error: Video not found or comments are disabled")
        return None
    

    print(f"\nTotal comments retrieved: {len(comments_data)}")
    
    onlyCommentText = []
    for i, item in enumerate(comments_data, 1):
       snippet = item['snippet']['topLevelComment']['snippet']
       onlyCommentText.append(f"Comment {i}: " + snippet['textDisplay'] + "\n")
    
    return onlyCommentText













        