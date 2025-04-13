"""Combined settings server and API.

This server provides both static file serving for the settings UI and API endpoints 
for the settings UI to interact with the settings backend.
"""
import json
import os
import sys
import mimetypes
import importlib
import inspect
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

# Add the parent directory to sys.path to be able to import the main module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from gonotego.settings import settings, secure_settings
from gonotego.common import interprocess

# Print information about imported modules for debugging
secure_settings_path = inspect.getfile(secure_settings)
print(f"Loaded secure_settings from: {secure_settings_path}")
print(f"Available settings: {[attr for attr in dir(secure_settings) if attr.isupper()]}")

# Define server port - use port 8000 (the original settings-server port)
PORT = 8000

# Path to the static files (React build)
STATIC_FILES_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "../settings-server/dist"))

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

class SettingsCombinedHandler(BaseHTTPRequestHandler):
    """HTTP request handler for settings server and API."""

    def _set_response_headers(self, status_code=200, content_type="application/json"):
        """Set common response headers."""
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.end_headers()

    def do_OPTIONS(self):
        """Handle OPTIONS requests."""
        self._set_response_headers()

    def serve_static_file(self, file_path):
        """Serve a static file."""
        try:
            # If path is a directory, serve index.html
            if os.path.isdir(file_path):
                file_path = os.path.join(file_path, "index.html")
            
            # If file doesn't exist, return 404
            if not os.path.exists(file_path):
                self._set_response_headers(status_code=404, content_type="text/plain")
                self.wfile.write(b"404 Not Found")
                return
            
            # Get the file's MIME type
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                content_type = "application/octet-stream"
            
            # Read and serve the file
            with open(file_path, "rb") as f:
                content = f.read()
            
            self._set_response_headers(status_code=200, content_type=content_type)
            self.wfile.write(content)
        except Exception as e:
            print(f"Error serving static file: {e}")
            self._set_response_headers(status_code=500, content_type="text/plain")
            self.wfile.write(b"500 Internal Server Error")

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Handle API requests
        if path == "/api/settings":
            try:
                # Get all available settings from secure_settings and mask sensitive values
                all_settings = {}
                print("Fetching settings...")
                
                # Get all available settings from secure_settings
                for key in dir(secure_settings):
                    if key.isupper() and not key.startswith("__"):
                        try:
                            # Try to get value using the settings.get method which handles 
                            # both Redis values and fallback to secure_settings
                            value = settings.get(key)
                            
                            # Check if it's a template placeholder value like '<KEY>'
                            is_template_value = isinstance(value, str) and value.startswith('<') and value.endswith('>')
                            
                            # Skip template values or empty values
                            if is_template_value or value is None or value == '':
                                continue
                                
                            # Debug info (mask sensitive values in logs)
                            if key in SENSITIVE_KEYS and value:
                                print(f"Setting {key} = [MASKED]")
                            else:
                                print(f"Setting {key} = {value}")
                            
                            # Mask sensitive information in response
                            if key in SENSITIVE_KEYS and value:
                                # Indicate that a value exists but don't send the actual value
                                all_settings[key] = "●●●●●●●●"
                            else:
                                all_settings[key] = value
                                
                        except Exception as e:
                            print(f"Error getting setting {key}: {e}")
                
                self._set_response_headers(content_type="application/json")
                self.wfile.write(json.dumps(all_settings).encode("utf-8"))
            except Exception as e:
                print(f"Error handling GET request: {e}")
                self._set_response_headers(status_code=500, content_type="application/json")
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        # Serve static files
        else:
            # Remove leading slash for file path
            if path == "/":
                file_path = STATIC_FILES_DIR
            else:
                file_path = os.path.join(STATIC_FILES_DIR, path.lstrip("/"))
            
            self.serve_static_file(file_path)

    def do_POST(self):
        """Handle POST requests."""
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
                
                self._set_response_headers(content_type="application/json")
                self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
            except Exception as e:
                print(f"Error handling POST request: {e}")
                self._set_response_headers(status_code=500, content_type="application/json")
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self._set_response_headers(status_code=404, content_type="application/json")
            self.wfile.write(json.dumps({"error": "Not found"}).encode("utf-8"))

def run_server():
    """Run the combined settings server."""
    # Make sure the static files directory exists
    if not os.path.exists(STATIC_FILES_DIR):
        print(f"Error: Static files directory {STATIC_FILES_DIR} does not exist.")
        print("Make sure to build the React app before running the server.")
        sys.exit(1)
        
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, SettingsCombinedHandler)
    print(f"Starting combined settings server on port {PORT}")
    print(f"Serving static files from {STATIC_FILES_DIR}")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()