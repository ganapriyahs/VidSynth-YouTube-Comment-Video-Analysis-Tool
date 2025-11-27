import csv
import os
from dotenv import load_dotenv
import json

from YouTubeCommentPull import get_youtube_comments
from YouTubeTranPull import fetch_transcript


if __name__ == "__main__":

    load_dotenv()
    API_KEY = os.getenv("YOUTUBE_API_KEY")

    with open('videos.txt', 'r') as f:
        reader = csv.reader(f, skipinitialspace=True)  # skipinitialspace removes spaces after commas
        # Beging collecting transcripts and comments for each video
        for row in reader:
            if row:  # Skip empty rows
                url, speaker, category, duration = row
                
                # Process your data here
                print(f"Attempting Retrieval for URL: {url}, Speaker: {speaker}, Category: {category}, Duration: {duration}")
                comments = get_youtube_comments(API_KEY, url, max_results=75)
                trans = fetch_transcript(url, speaker)
                
                # creating and populating the JSON format 
                try:
                    with open('videoList.json', 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except FileNotFoundError:
                    data = {"videoList": []}
                
                data["videoList"].append({
                    "video_url": url,
                    "speaker": speaker,
                    "category": category,
                    "duration": duration,
                    "comment_array": comments,
                    "transcript": trans,
                    "comment_summary": None, # will update them in the next step
                    "trans_summary": None,
                    "comment_eval_score": None,
                    "comment_eval_reason": None,
                    "trans_eval_score": None,
                    "trans_eval_reason": None
                })

                with open('videoList.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

