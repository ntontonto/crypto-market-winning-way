# Crypto Market Summary Video Generator

Automatically generates a 60-second YouTube Short (9:16) visualizing:
1.  **Price Growth Race** (Top Gainers/Losers 7-Day)
2.  **Top Movers & "Unusual" Activity** (24h)
3.  **Market Signals** (Heatmap, Mood, Momentum)

## Requirements

*   **System**: macOS (tested on Apple Silicon)
*   **Tools**:
    *   Python 3.9+
    *   [Homebrew](https://brew.sh/)
    *   FFmpeg (installed via brew)
    *   Manim (installed via brew)

## Installation

1.  **Install System Dependencies**:
    ```bash
    brew install manim ffmpeg
    ```

2.  **Setup Python Environment**:
    
    > [!IMPORTANT]
    > We use a **Virtual Environment (venv)** to manage Python dependencies (`requests`, etc.) while relying on the **System Manim** (installed via Brew) for video rendering.

    ```bash
    # Create virtual environment
    python3 -m venv venv

    # Activate it
    source venv/bin/activate

    # Install Python dependencies
    pip install -r requirements.txt
    ```

## Usage

1.  **Activate Environment** (if not active):
    ```bash
    source venv/bin/activate
    ```

2.  **Run Generator**:
    
    **Option A: Fetch Fresh Data (Default)**
    Fetches latest data from CoinGecko (Top 10 ranking history, movers, dominance) and generates video.
    ```bash
    python3 main.py --fetch
    ```
    
    **Option B: Use Specific Input File**
    Generates video from a provided JSON file (skips fetching).
    ```bash
    python3 main.py --input input.sample.json
    ```

    **Output**: Saved to `./out/crypto_summary_YYYY-MM-DD.mp4`.
    
    *   `--dry-run`: Fetch data only, skip video generation.
    *   `--no-music`: Disable background music.
    *   `--music-volume`: Set music volume (default 0.15).

3.  **Automated Daily Pipeline (One-Click)**:
    
    To fetch data, generate video, and **upload to YouTube** (Public) in a single step:
    ```bash
    python run_pipeline.py
    ```
    *   This script is cross-platform (Mac/Windows).
    *   It executes: Fetch -> Generate -> Upload (Public).
    *   **First Run**: A browser window will open to authenticate with your Google Account.
    *   **Subsequent Runs**: Uses cached `token.json` for fully automated uploads.


## Audio / Background Music

The generator automatically adds background music to the final video using FFmpeg.

*   **Default File**: `assets/audio/music/idokay - Fall Down.mp3`
*   **Behavior**:
    *   Music is looped or truncated to match video duration.
    *   Fades in (0.5s) and out (0.8s).
    *   Silent video is deleted upon success; preserved on failure.

**Changing Music**:
Use the `--music-path` argument:
```bash
python main.py --music-path "assets/audio/music/my_song.mp3" --music-volume 0.2
```

**Troubleshooting Audio**:
*   Ensure `ffmpeg` and `ffprobe` are installed/in your PATH.
*   If mixing fails, the silent video remains in `./out`.

## YouTube Configuration

To enable auto-upload, you need:
1.  **`client_secrets.json`**: Place your OAuth 2.0 Desktop Client credentials in the project root.
2.  **`token.json`**: Generated automatically after the first successful login.

**Metadata Generation**:
The system automatically generates:
*   **Title**: `Crypto Ranking {Date}: {TopGainer} (+{Pct}%) 🚀 #Shorts`
*   **Description**: Summary of Top 3 Gainers/Losers (7-day) and hashtags.
*   **Tags**: Dynamic tickers + standard crypto tags.

## Video Layout & Safe Area (YouTube Shorts)

This project targets **YouTube Shorts (9:16, 1080x1920)**.

**Safe Area System**:
To prevent "Tier-A" content (Titles, Tickers, Values) from being hidden by the Shorts UI (Like buttons, Channel Name, Search bar), we enforce strict layout margins:

*   **Left**: 1.0 unit (120px)
*   **Right**: 2.0 units (240px) - *Reserved for Action Buttons*
*   **Top**: 1.83 units (220px) - *Reserved for Search/Back*
*   **Bottom**: 2.4 units (288px) - *Reserved for Titles/Desc*

**Debug Overlay**:
You can visualize the safe area by setting `DEBUG_SAFE = True` in `src/video_generator.py`. A red rectangle will appear, indicating the usable canvas.


## Input JSON Specification

The generator accepts a JSON file with the following structure:

```json
{
  "asOf": "2026-01-02T00:00:00Z",
  "currency": "usd",
  "top10_7d": [
    {
      "date": "2025-12-27",
      "items": [
        {"id":"bitcoin","symbol":"BTC","name":"Bitcoin","market_cap": 123456789},
        ... (10 items)
      ]
    },
    ... (7 days)
  ],
  "today_top_movers": {
    "gainers": [ {"id":"sol","symbol":"SOL","change_24h_pct": 9.87, "price": 123.45, ...} ],
    "losers": [ ... ]
  },
  "dominance": {
    "series": [
      {"date":"2025-12-27","btc_pct": 49.1, "eth_pct": 17.2, "stable_pct": 8.4},
      ...
    ]
  }
}
```

3.  **Clean Up**:
    Remove temporary files, cache, or generated videos.

3.  **Clean Up**:
    Remove temporary files, cache, or generated videos.
    *   **Default**: Removes `media/`, `out_temp/`, `videos/`, `__pycache__`, and intermediate files.
    *   **--cache**: Also removes `./cache/`.
    *   **--output**: Also removes `./out/`.
    *   **--all**: Removes everything.

    ```bash
    # Clean temporary files (default)
    python3 cleanup.py

    # Clean cache and output videos too
    python3 cleanup.py --all
    ```

## Troubleshooting

*   **Manim/FFmpeg errors**: Ensure you installed `manim` via `brew install manim`. Pip-installed manim often has conflicts with system FFmpeg on macOS.
*   **Timeouts**: CoinGecko API has rate limits. If it fails, the script will try to use the latest cached data.

## Dependency Implementation Notes

**Why usage of Homebrew Manim + Python Venv?**

During development, we encountered a known compatibility issue on macOS (Apple Silicon):
1.  **Pip-installed Manim** (`pip install manim`) depends on the `av` library.
2.  The `av` library often fails to build against the latest **System FFmpeg** (v7.x) installed via Homebrew.
3.  Manim requires an older version of `av` (<14.0.0), which is completely incompatible with modern FFmpeg headers.

**Solution**:
We use the **System Manim** (`brew install manim`). Homebrew manages the binary compatibility between Manim, its dependencies (Cairo, Pango), and FFmpeg.
We still use a **Python Venv** for our own logic (`requests`, independent scripts), but we carefully exclude `manim` from `requirements.txt` to avoid reinstalling the broken Pip version.

## License
MIT