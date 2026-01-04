import argparse
import io
import json
import os
import sys

from src.metadata import VideoMetadataGenerator
from src.youtube_uploader import YouTubeUploader


def main() -> int:
    # Task Scheduler / cmd.exe often runs with cp932 output, which can crash on emoji.
    # Force UTF-8 output or replace unencodable characters to avoid UnicodeEncodeError.
    try:
        if hasattr(sys.stdout, "buffer"):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "buffer"):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Upload video to YouTube")
    parser.add_argument("--video", type=str, required=True, help="Path to video file to upload")
    parser.add_argument("--input-json", type=str, default="current_input.json", help="Path to input JSON file for metadata")
    parser.add_argument("--privacy", type=str, default="private", choices=["private", "unlisted", "public"], help="Privacy status")
    parser.add_argument("--token-file", type=str, default="token.json", help="Path to token file (JSON recommended)")
    parser.add_argument("--client-secrets", type=str, default="client_secrets.json", help="Path to OAuth client secrets JSON")
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Disable interactive OAuth (fails fast if token is missing/invalid; recommended for Task Scheduler).",
    )
    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"Error: Video file not found: {args.video}")
        return 1

    if not os.path.exists(args.input_json):
        print(f"Error: Input JSON file not found: {args.input_json}")
        return 1

    with open(args.input_json, "r", encoding="utf-8") as f:
        input_data = json.load(f)

    metadata_gen = VideoMetadataGenerator(input_data)
    video_title = metadata_gen.get_title()
    video_description = metadata_gen.get_description()
    video_tags = metadata_gen.get_tags()

    print(f"Uploading: {args.video}")
    print(f"Title: {video_title}")
    print(f"Privacy: {args.privacy}")
    print(f"Description Preview:\n{video_description[:100]}...")

    uploader = YouTubeUploader(
        client_secrets_file=args.client_secrets,
        token_file=args.token_file,
        interactive=not args.non_interactive,
    )
    uploader.upload_video(
        file_path=args.video,
        title=video_title,
        description=video_description,
        tags=video_tags,
        privacy_status=args.privacy,
    )
    print("Upload completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

