import json
################
# File useful to clear an output from validate_summaries.py if it is necessary to 
# re-run the test. 
################


# Load the file
with open('videoList.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# reset the fields related to testing
for video in data['videoList']:
    # video.pop('eval_score', None)
    # video.pop('eval_reason', None)
    video['comment_array'] = []
    video['transcript'] = None
    video['comment_eval_score'] = None
    video['comment_eval_reason'] = None
    video['trans_eval_score'] = None
    video['trans_eval_reason'] = None

with open('videoList.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

