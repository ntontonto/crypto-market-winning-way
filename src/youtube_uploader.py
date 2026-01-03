
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class YouTubeUploader:
    def __init__(self, client_secrets_file="client_secrets.json", token_file="token.json"):
        self.client_secrets_file = client_secrets_file
        self.token_file = token_file
        self.api_service_name = "youtube"
        self.api_version = "v3"
        self.scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        self.youtube = None

    def authenticate(self):
        """
        Authenticates the user and creates a YouTube API client.
        Saves credentials to token.json for future use.
        """
        creds = None
        # The file token.json stores the user's access and refresh tokens.
        if os.path.exists(self.token_file):
            print(f"Loading credentials from {self.token_file}...")
            # We use pickle here as google-auth-oauthlib often saves as pickle or json
            # But standard example uses pickle for token.pickle, or different for json.
            # Let's support the standard json format if possible, or pickle.
            # Actually, google example often uses pickle for local scripts.
            # Let's try to load valid creds.
            try:
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            except Exception:
                print("Failed to load existing token, will re-authenticate.")
                creds = None

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing access token...")
                creds.refresh(Request())
            else:
                print("Fetching new tokens...")
                if not os.path.exists(self.client_secrets_file):
                     raise FileNotFoundError(f"Client secrets file '{self.client_secrets_file}' not found.")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, self.scopes
                )
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            print(f"Saving credentials to {self.token_file}...")
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)

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
            tags = ['crypto', 'market cap', 'ranking', 'bitcoin', 'animation', 'manim']

        print(f"Uploading {file_path} to YouTube...")

        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False,
            }
        }

        # Chunk size: 4MB
        media = MediaFileUpload(file_path, chunksize=4*1024*1024, resumable=True)

        request = self.youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )

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
    # Test script
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Video file to upload")
    parser.add_argument("--title", default="Test Video", help="Video title")
    args = parser.parse_args()
    
    if args.file:
        uploader = YouTubeUploader()
        uploader.upload_video(args.file, args.title, "Test description")
