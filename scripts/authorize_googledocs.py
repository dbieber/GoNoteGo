#!/usr/bin/env python3
"""One-time authorization for the Google Docs uploader.

Run this on a machine with a web browser. Whoever signs in during the consent
screen is the Google user the notes will be written as, and the monthly docs
will live in that user's own Drive, owned by them.

Setup:
  1. In Google Cloud, enable the Google Docs API and Google Drive API, and
     create an OAuth 2.0 Client ID of type "Desktop app"; download its JSON.
  2. On the OAuth consent screen (External / Testing), add the Google account
     that will sign in here as a Test user.
  3. pip install google-auth-oauthlib

Usage:
  python authorize_googledocs.py CLIENT_SECRET.json OUTPUT_TOKEN.json

Then copy OUTPUT_TOKEN.json to the device and set GOOGLE_DOCS_CREDENTIALS to its
path (and NOTE_TAKING_SYSTEM=googledocs).
"""
import sys

# Must match the scopes the uploader requests (see googledocs_api.SCOPES).
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.file',
]


def main():
  if len(sys.argv) < 2:
    print(__doc__)
    sys.exit(1)
  client_secret = sys.argv[1]
  out = sys.argv[2] if len(sys.argv) > 2 else 'gdocs-token.json'

  from google_auth_oauthlib.flow import InstalledAppFlow
  flow = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES)
  # access_type=offline + prompt=consent guarantees a refresh_token comes back.
  credentials = flow.run_local_server(
      port=0, access_type='offline', prompt='consent')
  with open(out, 'w') as f:
    f.write(credentials.to_json())
  print(f'\nWrote {out}. Signed in as the account you chose in the browser.')
  print('Copy it to the device and set GOOGLE_DOCS_CREDENTIALS to its path.')


if __name__ == '__main__':
  main()
