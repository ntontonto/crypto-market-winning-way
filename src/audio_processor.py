
import os
import subprocess
import shutil

class AudioProcessor:
    @staticmethod
    def get_video_duration(video_path):
        """
        Returns the duration of the video in seconds using ffprobe.
        Returns None if failed.
        """
        cmd = [
            "ffprobe", 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            video_path
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            return None

    @staticmethod
    def check_ffmpeg():
        """Returns True if ffmpeg and ffprobe are available."""
        return shutil.which("ffmpeg") and shutil.which("ffprobe")

    @staticmethod
    def add_bgm_to_video(input_video_path, music_path, output_video_path, volume=0.15, fade_in=0.5, fade_out=0.8, start_time=0.0):
        """
        Mixes background music into the video.
        - start_time: Start position in the music file (in seconds).
        - Loops music if shorter than video.
        - Truncates music if longer.
        - Applies volume and fade in/out.
        """
        if not AudioProcessor.check_ffmpeg():
            print("Error: FFmpeg/ffprobe not found.")
            return False

        if not os.path.exists(input_video_path):
            print(f"Error: Input video not found: {input_video_path}")
            return False

        if not os.path.exists(music_path):
            print(f"Error: Music file not found: {music_path}")
            return False

        duration = AudioProcessor.get_video_duration(input_video_path)
        if duration is None:
            print("Error: Could not determine video duration.")
            return False

        # Ensure output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_video_path)), exist_ok=True)

        # Filter Graph Description:
        # 1. [1:a]aloop=loop=-1:size=2e9[looped]  -> Loop infinitely (input is already sought)
        # 2. [looped]atrim=0:{duration},asetpts=PTS-STARTPTS[trimmed] -> Cut to video length
        
        # Calculate fade out start time
        fade_out_start = max(0, duration - fade_out)

        filter_complex = (
            f"[1:a]aloop=loop=-1:size=2e9[looped];"
            f"[looped]atrim=0:{duration},asetpts=PTS-STARTPTS[trimmed];"
            f"[trimmed]volume={volume}[vol];"
            f"[vol]afade=t=in:st=0:d={fade_in},afade=t=out:st={fade_out_start}:d={fade_out}[outa]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", input_video_path,
            "-ss", str(start_time), "-i", music_path, # Input seeking
            "-filter_complex", filter_complex,
            "-map", "0:v",       # Use video from input 0
            "-map", "[outa]",    # Use processed audio
            "-c:v", "copy",      # Copy video stream (fast)
            "-c:a", "aac",       # Encode audio
            "-b:a", "192k",
            "-shortest",         # Ensure output stops with shortest stream (video)
            output_video_path
        ]

        print(f"Adding background music...")
        # print("CMD:", " ".join(cmd)) 

        try:
            subprocess.run(cmd, check=True, stderr=subprocess.PIPE, text=True)
            print(f"Successfully created: {output_video_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg failed with error:\n{e.stderr}")
            return False
