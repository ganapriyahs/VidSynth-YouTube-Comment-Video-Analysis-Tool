import json
from pathlib import Path


def main():
    # Folder where this script lives
    base_dir = Path(__file__).parent

    # Input and output paths
    videos_path = base_dir / "videos.txt"
    output_path = base_dir / "videoList.json"

    video_list = []

    # Read each line from videos.txt and create a dummy video entry
    if videos_path.exists():
        with videos_path.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                url = line.strip()
                if not url:
                    continue

                video_list.append(
                    {
                        "id": idx,
                        "video_url": url,
                        "transcript": f"Dummy transcript text for {url}",
                        "comment_array": [
                            f"Dummy comment 1 for {url}",
                            f"Dummy comment 2 for {url}",
                        ],
                        "trans_summary": f"Dummy transcript summary for {url}",
                        "comment_summary": f"Dummy comment summary for {url}",
                        # Evaluation fields that the original script would normally fill
                        "trans_eval_score": None,
                        "trans_eval_reason": "",
                        "comment_eval_score": None,
                        "comment_eval_reason": "",
                    }
                )
    else:
        # Fallback: one dummy entry if videos.txt is missing
        video_list.append(
            {
                "id": 1,
                "video_url": "dummy",
                "transcript": "Dummy transcript text",
                "comment_array": ["Dummy comment 1", "Dummy comment 2"],
                "trans_summary": "Dummy transcript summary",
                "comment_summary": "Dummy comment summary",
                "trans_eval_score": None,
                "trans_eval_reason": "",
                "comment_eval_score": None,
                "comment_eval_reason": "",
            }
        )

    # Wrap it in the same structure the old script expects: {"videoList": [...]}
    video_list_data = {"videoList": video_list}

    # Write everything to videoList.json
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(video_list_data, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(video_list)} dummy entries to {output_path}")


if __name__ == "__main__":
    main()
