import requests
import json
from urllib.parse import urlparse, parse_qs

def get_youtube_comments(api_key, video_id, max_results=100): # origionally passed in video_url instead
    """
    Retrieve top comments from a YouTube video
    
    Args:
        api_key: Your YouTube Data API v3 key
        video_id: The YouTube video ID (part of URL) 
        max_results: Maximum number of comments to retrieve (default 100)
    """
    

    print(f"Video ID: {video_id}")
    print(f"Fetching up to {max_results} comments...\n")
    
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
    
    # Also print a formatted summary of comments
    print("\n" + "=" * 80)
    print("FORMATTED COMMENT SUMMARY")
    print("=" * 80)
    
    # How to get the top comments, info , and print all out
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
    # id from above url 
    VIDEO_ID = "j6liCsCSUoM"

    if API_KEY == "YOUR_API_KEY_HERE":
        print("Please replace 'YOUR_API_KEY_HERE' with your actual YouTube API key")
        print("Follow the instructions above to obtain an API key from Google Cloud Console")
    else:
        comments = get_youtube_comments(API_KEY, VIDEO_ID, max_results=2)
