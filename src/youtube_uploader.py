import os
import pickle
from pathlib import Path
from typing import Optional, Tuple, Union

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


class YouTubeUploader:
    def __init__(
        self,
        client_secrets_file: Optional[Union[str, os.PathLike]] = "client_secrets.json",
        token_file: Optional[Union[str, os.PathLike]] = "token.json",
        *,
        interactive: bool = True,
    ):
        project_root = Path(__file__).resolve().parents[1]
        self.client_secrets_file = self._resolve_path(project_root, client_secrets_file)
        self.token_file = self._resolve_path(project_root, token_file)
        self.interactive = interactive
        self.api_service_name = "youtube"
        self.api_version = "v3"
        self.scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        self.youtube = None

    @staticmethod
    def _resolve_path(project_root: Path, value: Optional[Union[str, os.PathLike]]) -> Path:
        if value is None:
            raise ValueError("Path value must not be None")
        path = Path(value)
        if path.is_absolute():
            return path
        return project_root / path

    def _load_credentials(self) -> Tuple[Optional[Credentials], Optional[str]]:
        token_path = self.token_file
        if not token_path.exists():
            return None, None

        # Prefer JSON (Google "authorized_user" format), fall back to legacy pickle.
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), self.scopes)
            return creds, "json"
        except Exception:
            pass

        try:
            with open(token_path, "rb") as token_fp:
                creds = pickle.load(token_fp)
            return creds, "pickle"
        except Exception:
            return None, None

    def _save_credentials_json(self, creds: Credentials) -> None:
        token_path = self.token_file
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    def _save_credentials_pickle(self, creds) -> None:
        token_path = self.token_file
        token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(token_path, "wb") as token_fp:
            pickle.dump(creds, token_fp)

    def _save_credentials(self, creds) -> None:
        # If the user explicitly points to a pickle file, keep using pickle.
        if self.token_file.suffix.lower() in {".pickle", ".pkl"}:
            self._save_credentials_pickle(creds)
            return

        # Default: save JSON (works in headless / Task Scheduler scenarios).
        if isinstance(creds, Credentials):
            self._save_credentials_json(creds)
            return

        # Best effort: google-auth credentials usually provide to_json().
        try:
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            self.token_file.write_text(creds.to_json(), encoding="utf-8")
        except Exception:
            self._save_credentials_pickle(creds)

    def authenticate(self) -> None:
        """
        Authenticates the user and creates a YouTube API client.
        Saves credentials to token.json for future use.
        """
        creds = None
        token_format = None

        print(f"Token file: {self.token_file}")
        print(f"Client secrets file: {self.client_secrets_file}")
        print(f"Interactive auth: {self.interactive}")

        creds, token_format = self._load_credentials()
        if creds:
            print(f"Loaded credentials from token ({token_format}).")
            # If token file is named .json but was a legacy pickle, migrate it to JSON.
            if token_format == "pickle" and self.token_file.suffix.lower() == ".json":
                try:
                    self._save_credentials(creds)
                    print("Migrated legacy pickle token to JSON format.")
                except Exception:
                    pass

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing access token...")
                creds.refresh(Request())
            else:
                if not self.interactive:
                    raise RuntimeError(
                        "No valid credentials available and interactive auth is disabled. "
                        "Run once interactively to create/refresh the token, then rerun in non-interactive mode."
                    )
                print("Fetching new tokens...")
                if not self.client_secrets_file.exists():
                    raise FileNotFoundError(f"Client secrets file '{self.client_secrets_file}' not found.")

                flow = InstalledAppFlow.from_client_secrets_file(str(self.client_secrets_file), self.scopes)
                creds = flow.run_local_server(port=0)

            print(f"Saving credentials to {self.token_file}...")
            self._save_credentials(creds)

        self.youtube = build(self.api_service_name, self.api_version, credentials=creds)
        print("YouTube authentication successful.")

    def upload_video(self, file_path, title, description, tags=None, category_id="28", privacy_status="private"):
        """
        Uploads a video to YouTube.
        category_id="28" is 'Science & Technology'.
        """
        if not self.youtube:
            self.authenticate()

        if tags is None:
            tags = ["crypto", "market cap", "ranking", "bitcoin", "animation", "manim"]

        print(f"Uploading {file_path} to YouTube...")

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(file_path, chunksize=4 * 1024 * 1024, resumable=True)
        request = self.youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%")

        print("Upload Complete!")
        print(f"Video ID: {response.get('id')}")
        print(f"Video URL: https://youtu.be/{response.get('id')}")

        return response


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Video file to upload")
    parser.add_argument("--title", default="Test Video", help="Video title")
    args = parser.parse_args()

    if args.file:
        uploader = YouTubeUploader()
        uploader.upload_video(args.file, args.title, "Test description")

