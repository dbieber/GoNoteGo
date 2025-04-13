"""API server for the settings module.

This server provides API endpoints for the settings UI to interact with the settings
backend. It handles fetching and setting settings.
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

# Add the parent directory to sys.path to be able to import the main module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from gonotego.settings import settings, secure_settings

# Define server port
PORT = 8001

# Define sensitive keys that should be masked
SENSITIVE_KEYS = [
    'ROAM_PASSWORD',
    'REMNOTE_API_KEY',
    'IDEAFLOW_PASSWORD',
    'MEM_API_KEY',
    'NOTION_INTEGRATION_TOKEN',
    'TWITTER_API_KEY',
    'TWITTER_API_SECRET',
    'TWITTER_ACCESS_TOKEN',
    'TWITTER_ACCESS_TOKEN_SECRET',
    'EMAIL_PASSWORD',
    'DROPBOX_ACCESS_TOKEN',
    'OPENAI_API_KEY',
]

class SettingsAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for settings API."""

    def _set_response_headers(self, status_code=200, content_type="application/json"):
        """Set common response headers including CORS headers."""
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        # Allow cross-origin requests from the settings UI
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight."""
        self._set_response_headers()

    def do_GET(self):
        """Handle GET requests to fetch settings."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/api/settings":
            try:
                # Get all available settings from secure_settings and mask sensitive values
                all_settings = {}
                for key in dir(secure_settings):
                    if key.isupper() and not key.startswith("__"):
                        try:
                            # Try to get value from Redis first (user-set values)
                            value = settings.get(key)
                            
                            # Mask sensitive information
                            if key in SENSITIVE_KEYS and value:
                                # Indicate that a value exists but don't send the actual value
                                value = "●●●●●●●●"
                            
                            all_settings[key] = value
                        except Exception as e:
                            print(f"Error getting setting {key}: {e}")
                
                self._set_response_headers()
                self.wfile.write(json.dumps(all_settings).encode("utf-8"))
            except Exception as e:
                print(f"Error handling GET request: {e}")
                self._set_response_headers(status_code=500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self._set_response_headers(status_code=404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode("utf-8"))

    def do_POST(self):
        """Handle POST requests to update settings."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/api/settings":
            try:
                # Read the request body
                content_length = int(self.headers["Content-Length"])
                post_data = self.rfile.read(content_length).decode("utf-8")
                settings_data = json.loads(post_data)
                
                # Update settings
                for key, value in settings_data.items():
                    # Skip masked values - we don't want to overwrite with placeholder text
                    if key in SENSITIVE_KEYS and value == "●●●●●●●●":
                        continue
                        
                    # Skip non-settings keys
                    if not key.isupper() or key.startswith("__"):
                        continue
                        
                    try:
                        # Special handling for CUSTOM_COMMAND_PATHS which is a list
                        if isinstance(value, list):
                            settings.set(key, value)
                        # Handle other values
                        else:
                            settings.set(key, value)
                    except Exception as e:
                        print(f"Error setting {key}: {e}")
                
                self._set_response_headers()
                self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
            except Exception as e:
                print(f"Error handling POST request: {e}")
                self._set_response_headers(status_code=500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self._set_response_headers(status_code=404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode("utf-8"))

def run_server():
    """Run the settings API server."""
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, SettingsAPIHandler)
    print(f"Starting settings API server on port {PORT}")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()