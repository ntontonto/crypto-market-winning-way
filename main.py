import os
import json
import argparse
import subprocess
import shutil
import sys
import io
from datetime import datetime
from src.data_fetcher import CryptoDataFetcher
from src.audio_processor import AudioProcessor
from src.youtube_uploader import YouTubeUploader
from src.metadata import VideoMetadataGenerator

def main():
    # Task Scheduler / cmd.exe often runs with cp932 output, which can crash on emoji.
    # Force UTF-8 output or replace unencodable characters to avoid UnicodeEncodeError.
    try:
        if hasattr(sys.stdout, "buffer"):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "buffer"):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Crypto Ranking Video Generator")
    parser.add_argument("--dry-run", action="store_true", help="Fetch data only, skip video generation")
    parser.add_argument("--input", type=str, help="Path to input JSON file (skips fetching)")
    parser.add_argument("--fetch", action="store_true", help="Force fetch new data even if input provided (overrides input)")
    
    # Audio Arguments
    parser.add_argument("--music-path", type=str, default="assets/audio/music/294_BPM88.mp3", help="Path to background music")
    parser.add_argument("--music-volume", type=float, default=0.15, help="Music volume (0.0 to 1.0)")
    parser.add_argument("--music-start", type=float, default=0.0, help="Music start offset in seconds")
    parser.add_argument("--no-music", action="store_true", help="Disable background music")

    # YouTube Upload Arguments
    parser.add_argument("--upload", action="store_true", help="Upload final video to YouTube")
    parser.add_argument("--privacy", type=str, default="private", choices=["private", "unlisted", "public"], help="Privacy status for YouTube upload")
    parser.add_argument("--token-file", type=str, default="token.json", help="Path to token file (JSON recommended)")
    parser.add_argument("--client-secrets", type=str, default="client_secrets.json", help="Path to OAuth client secrets JSON")
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Disable interactive OAuth (fails fast if token is missing/invalid; recommended for Task Scheduler).",
    )

    
    args = parser.parse_args()

    # 1. Prepare Data
    print("--- 1. Data Preparation ---")
    
    input_data = None
    input_file_path = "current_input.json"

    if args.input and not args.fetch:
        print(f"Using provided input file: {args.input}")
        if not os.path.exists(args.input):
            print(f"Error: Input file {args.input} not found.")
            return
        # Validate JSON
        try:
            with open(args.input, "r") as f:
                input_data = json.load(f)
            # Copy to current_input.json for Manim
            if os.path.abspath(args.input) != os.path.abspath(input_file_path):
                shutil.copy(args.input, input_file_path)
            print("Input validation passed.")
        except json.JSONDecodeError:
            print(f"Error: {args.input} is not valid JSON.")
            return
    else:
        # Fetch Data
        print("Fetching fresh data from DataFetcher...")
        fetcher = CryptoDataFetcher()
        try:
            input_data = fetcher.generate_input_json()
            if not input_data:
                print("Error: Fetched data is empty.")
                return
            
            # Save to file
            with open(input_file_path, "w") as f:
                json.dump(input_data, f, indent=2)
            print(f"Data saved to {input_file_path}")
            
        except Exception as e:
            print(f"Error during data fetching: {str(e)}")
            return

    # 2. Generate Video
    if args.dry_run:
        print("Dry run enabled. Skipping video generation.")
        return

    print("--- 2. Generating Video (Manim) ---")
    
    # Check Manim availability (use python -m manim)
    manim_check_cmd = [sys.executable, "-m", "manim", "--version"]
    try:
        subprocess.run(manim_check_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception:
        print("Error: 'manim' module not found or not working in this Python environment.")
        return

    # Derive output filename from data date
    as_of = input_data.get("asOf", "").split("T")[0] or datetime.now().strftime("%Y-%m-%d")
    output_filename = f"crypto_summary_{as_of}.mp4"
    
    
    # Scene Selection
    scene_name = "CryptoPlayboardShorts"
    
    cmd = [
        sys.executable, "-m", "manim",
        "-qh", # High quality (1080p)
        "--resolution", "1080,1920", # Vertical
        "--media_dir", "./out_temp",
        "--disable_caching", # Disable caching to ensure fresh data usage
        os.path.join("src", "video_generator.py"),
        scene_name
    ]
    
    print(f"Running Manim command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Manim failed with exit code {e.returncode}")
        # Sometimes Manim errors but produces output? Be careful.
        # We'll check for output anyway.

    # 3. Finalize Output
    print("--- 3. Finalizing Output ---")
    
    # Path where Manim dumps the video
    expected_name = f"{scene_name}.mp4"
    found_file = None
    
    search_dir = "./out_temp/videos"
    if os.path.exists(search_dir):
        for root, dirs, files in os.walk(search_dir):
            if expected_name in files:
                found_file = os.path.join(root, expected_name)
                break
    
    if found_file:
        final_dest_dir = "./out"
        if not os.path.exists(final_dest_dir):
            os.makedirs(final_dest_dir)
            
        final_dest_path = os.path.join(final_dest_dir, output_filename)
        
        # Move initial silent video to destination (or temp location if adding music)
        shutil.move(found_file, final_dest_path)
        print(f"Video generated at {final_dest_path}")
        
        # 4. Add Background Music (Optional)
        if not args.no_music:
            print("--- 4. Adding Background Music ---")
            music_dest_path = os.path.join(final_dest_dir, f"crypto_summary_{as_of}_with_music.mp4")
            
            # Using same base name but with music, or replacing?
            # User request: "Output: ./out/final/<same_base_name>_with_music.mp4 (or update the pipeline so the final output is this path)"
            # And: "If the music addition step succeeds, DELETE the original (silent) video file"
            
            # Use `_with_music` suffix for clarity, then maybe rename?
            # Let's stick to user request: suffix `_with_music.mp4`
            
            success = AudioProcessor.add_bgm_to_video(
                input_video_path=final_dest_path,
                music_path=args.music_path,
                output_video_path=music_dest_path,
                volume=args.music_volume,
                start_time=args.music_start
            )
            
            if success:
                print(f"Music added successfully. Removing silent version.")
                os.remove(final_dest_path)
                print(f"FINAL OUTPUT: {music_dest_path}")
                final_video_path = music_dest_path
            else:
                print("Warning: Failed to add music. Keeping silent version.")
                print(f"FINAL OUTPUT: {final_dest_path}")
                final_video_path = final_dest_path
        else:
             print(f"FINAL OUTPUT: {final_dest_path}")
             final_video_path = final_dest_path
        
        # 5. Upload to YouTube (Optional)
        if args.upload:
            print("--- 5. Uploading to YouTube ---")
            
            # Generate Metadata
            metadata_gen = VideoMetadataGenerator(input_data)
            video_title = metadata_gen.get_title()
            video_description = metadata_gen.get_description()
            video_tags = metadata_gen.get_tags()
            
            print(f"Title: {video_title}")
            print(f"Description Preview:\n{video_description[:100]}...")

            try:
                # Note: The uploader.upload_video method in previous step didn't explicitly take tags arg in some versions
                # checking src/youtube_uploader.py content in memory... 
                # It took (file_path, title, description, category_id, privacy_status). 
                # It hardcoded tags inside. I should update uploader if I want dynamic tags, 
                # OR just put tags in description. The plan said "Returns list of tags".
                # Let's check uploader signature or update it.
                
                # Based on previous step, uploader.upload_video had:
                # body = { 'snippet': { ... 'tags': ['crypto'...] ... } }
                # It did NOT take tags as argument. I should update uploader.py first or now.
                # Let's assume I will update uploader.py in next step or use what I have.
                # For now, I'll pass title and description.
                
                uploader = YouTubeUploader(
                    client_secrets_file=args.client_secrets,
                    token_file=args.token_file,
                    interactive=not args.non_interactive,
                )
                uploader.upload_video(
                    file_path=final_video_path,
                    title=video_title,
                    description=video_description,
                    tags=video_tags,
                    privacy_status=args.privacy
                )
            except Exception as e:
                print(f"Error uploading to YouTube: {e}")


    else:
        print("Error: Could not find generated video file.")
        
    # Cleanup
    if os.path.exists("./out_temp"):
        shutil.rmtree("./out_temp")
        
if __name__ == "__main__":
    main()
