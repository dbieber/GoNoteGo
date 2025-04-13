"""Settings server for Go Note Go.

This server provides both static file serving for the settings UI and API endpoints
for the settings UI to interact with the settings backend.
"""
import json
import os
import sys
import mimetypes
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

# Import required modules
from gonotego.settings import settings, secure_settings
from gonotego.common import wifi

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
    if path == "/api/reset":
      # Simple endpoint to reset test settings
      try:
        # Clear the CUSTOM_COMMAND_PATHS setting
        settings.clear("CUSTOM_COMMAND_PATHS")
        # You could clear other test settings here

        self._set_response_headers(content_type="application/json")
        self.wfile.write(json.dumps({"success": True, "message": "Settings reset"}).encode("utf-8"))
      except Exception as e:
        print(f"Error resetting settings: {e}")
        self._set_response_headers(status_code=500, content_type="application/json")
        self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
    elif path == "/api/settings":
      try:
        # Get all available settings from secure_settings and mask sensitive values
        all_settings = {}
        # Get all settings keys available in secure_settings
        available_keys = [key for key in dir(secure_settings) if key.isupper() and not key.startswith("__")]

        # Process all available settings
        for key in available_keys:
          try:
            # Get the value using settings.get method (handles Redis + fallback)
            value = settings.get(key)

            # Check if it's a template placeholder like '<KEY>'
            is_template = (isinstance(value, str) and
                         value.startswith('<') and
                         value.endswith('>') and
                         value[1:-1].strip() == key)

            # Always add to response, marking template values clearly
            if is_template:
              # For template values, send an empty string to clear the field
              all_settings[key] = ""
            else:
              # For sensitive values, mask them
              if key in SENSITIVE_KEYS and value:
                all_settings[key] = "●●●●●●●●"
              # For non-sensitive or empty values, return as is
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
        wifi_networks_updated = False
        
        for key, value in settings_data.items():
          # Skip masked values - we don't want to overwrite with placeholder text
          if key in SENSITIVE_KEYS and value == "●●●●●●●●":
            continue

          # Skip non-settings keys
          if not key.isupper() or key.startswith("__"):
            continue

          try:
            # Special handling for WIFI_NETWORKS
            if key == 'WIFI_NETWORKS':
              wifi_networks_updated = True
              settings.set(key, value)
            # Special handling for CUSTOM_COMMAND_PATHS which is a list
            elif isinstance(value, list):
              settings.set(key, value)
            # Handle other values
            else:
              settings.set(key, value)
          except Exception as e:
            print(f"Error setting {key}: {e}")
        
        # If WiFi networks were updated, apply the new configuration
        response_data = {"success": True}
        if wifi_networks_updated:
          try:
            wifi_networks = settings_data.get('WIFI_NETWORKS', [])
            if wifi.configure_from_settings(wifi_networks):
              response_data["wifi_configured"] = True
            else:
              response_data["wifi_configured"] = False
              response_data["wifi_error"] = "Failed to apply WiFi configuration"
          except Exception as e:
            print(f"Error configuring WiFi: {e}")
            response_data["wifi_configured"] = False
            response_data["wifi_error"] = str(e)
        
        self._set_response_headers(content_type="application/json")
        self.wfile.write(json.dumps(response_data).encode("utf-8"))
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