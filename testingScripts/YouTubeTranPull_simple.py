from youtube_transcript_api import YouTubeTranscriptApi

ytt_api = YouTubeTranscriptApi()
VIDEO_ID = "j6liCsCSUoM"
fetched_transcript = ytt_api.fetch(VIDEO_ID)

# is iterable
for i, snippet in enumerate(fetched_transcript):
    if i < 10:
        print(snippet.text)