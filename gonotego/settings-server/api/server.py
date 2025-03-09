"""Settings API server 

This server provides a REST API for the settings server frontend to interact with 
the settings backend. It handles retrieving and updating settings.
"""
import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

# Add the parent directory to the path so we can import settings
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from gonotego.settings import settings
from gonotego.settings import secure_settings

class SettingsHandler(BaseHTTPRequestHandler):
    def _set_response(self, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        # Handle preflight requests for CORS
        self._set_response()
        
    def do_GET(self):
        if self.path == '/api/settings':
            # Get all settings
            try:
                # Get all available settings from secure_settings
                all_settings = {}
                for attr in dir(secure_settings):
                    if not attr.startswith('_'):  # Skip private attributes
                        try:
                            # First try to get from Redis (user settings)
                            all_settings[attr] = settings.get(attr)
                        except Exception:
                            # Fall back to secure_settings
                            all_settings[attr] = getattr(secure_settings, attr)
                
                # Convert custom command paths list to a serializable format
                if 'CUSTOM_COMMAND_PATHS' in all_settings and isinstance(all_settings['CUSTOM_COMMAND_PATHS'], list):
                    all_settings['CUSTOM_COMMAND_PATHS'] = list(all_settings['CUSTOM_COMMAND_PATHS'])
                
                self._set_response()
                self.wfile.write(json.dumps(all_settings).encode('utf-8'))
            except Exception as e:
                self._set_response(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self._set_response(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode('utf-8'))

    def do_POST(self):
        if self.path == '/api/settings':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            try:
                settings_data = json.loads(post_data)
                
                # Update settings in Redis
                for key, value in settings_data.items():
                    if key not in dir(secure_settings):
                        continue  # Skip settings that don't exist in secure_settings
                    
                    # Handle special cases
                    if key == 'CUSTOM_COMMAND_PATHS' and isinstance(value, list):
                        settings.set(key, value)
                    else:
                        settings.set(key, value)
                
                self._set_response()
                self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
            except Exception as e:
                self._set_response(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self._set_response(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode('utf-8'))

def run_server(port=8001):
    server_address = ('', port)
    httpd = HTTPServer(server_address, SettingsHandler)
    print(f'Starting settings API server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()