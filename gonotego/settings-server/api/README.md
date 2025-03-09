# Settings Server API

The Settings Server API provides a REST interface for the settings server frontend to communicate with the backend settings storage.

## API Endpoints

### GET /api/settings

Retrieves all settings from the backend.

**Response:**
```json
{
  "HOTKEY": "Esc",
  "NOTE_TAKING_SYSTEM": "Roam Research",
  "WIFI_SSID": "MyNetwork",
  ...
}
```

### POST /api/settings

Updates settings in the backend.

**Request:**
```json
{
  "HOTKEY": "Esc",
  "NOTE_TAKING_SYSTEM": "Roam Research", 
  "WIFI_SSID": "MyNetwork",
  "WIFI_PASSWORD": "my_secure_password"
}
```

**Response:**
```json
{
  "success": true
}
```

## WiFi Configuration

The settings server now supports WiFi configuration through the following settings:

- `WIFI_SSID`: The name of the WiFi network to connect to
- `WIFI_PASSWORD`: The password for the WiFi network

After updating these settings, use the command `:wifi connect` to apply the changes and connect to the specified network.

You can check the current WiFi connection status with the command `:wifi status`.

## Implementation Details

The API server runs on port 8001 and is managed by supervisord. It uses the same settings backend as the command-line interface, ensuring consistency between the different methods of changing settings.