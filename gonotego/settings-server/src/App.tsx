import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Eye, EyeOff, Save, Plus, Trash2, Info } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";

const SettingsUI = () => {
  const NOTE_TAKING_SYSTEMS = [
    'Roam Research',
    'RemNote',
    'IdeaFlow',
    'Mem',
    'Notion',
    'Twitter',
    'Email'
  ];

  const [settings, setSettings] = useState({
    HOTKEY: '',
    NOTE_TAKING_SYSTEM: '',
    BLOB_STORAGE_SYSTEM: '',
    ROAM_GRAPH: '',
    ROAM_USER: '',
    ROAM_PASSWORD: '',
    REMNOTE_USER_ID: '',
    REMNOTE_API_KEY: '',
    REMNOTE_ROOT_REM: '',
    IDEAFLOW_USER: '',
    IDEAFLOW_PASSWORD: '',
    MEM_API_KEY: '',
    NOTION_INTEGRATION_TOKEN: '',
    NOTION_DATABASE_ID: '',
    TWITTER_API_KEY: '',
    TWITTER_API_SECRET: '',
    TWITTER_ACCESS_TOKEN: '',
    TWITTER_ACCESS_TOKEN_SECRET: '',
    EMAIL: '',
    EMAIL_USER: '',
    EMAIL_PASSWORD: '',
    EMAIL_SERVER: '',
    DROPBOX_ACCESS_TOKEN: '',
    OPENAI_API_KEY: '',
    WIFI_COUNTRY: '',
    WIFI_NETWORKS: [],
    CUSTOM_COMMAND_PATHS: [],
  });
  
  const [newWifiNetwork, setNewWifiNetwork] = useState({
    ssid: '',
    psk: ''
  });

  const [showPasswords, setShowPasswords] = useState({});
  const [saveStatus, setSaveStatus] = useState(null);
  const [loadingSettings, setLoadingSettings] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [customPath, setCustomPath] = useState('');

  // Fetch settings when component mounts
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        setLoadingSettings(true);
        setLoadError(false);

        const response = await fetch('/api/settings');

        if (!response.ok) {
          throw new Error('Failed to fetch settings');
        }

        const data = await response.json();

        // Process the received settings
        const validSettings = Object.entries(data).reduce((acc, [key, value]) => {
          // Always include the value, even if it's empty
          // This ensures we show empty strings and other falsy values correctly
          acc[key] = value;
          return acc;
        }, {});

        // Update settings state with fetched data
        setSettings(prev => ({
          ...prev,
          ...validSettings
        }));
      } catch (error) {
        console.error('Error fetching settings:', error);
        setLoadError(true);
      } finally {
        setLoadingSettings(false);
      }
    };

    fetchSettings();
  }, []);

  const handleChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const togglePasswordVisibility = (field) => {
    setShowPasswords(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  const handleSave = async () => {
    setSaveStatus('saving');
    try {
      const response = await fetch('/api/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });

      if (!response.ok) {
        throw new Error('Failed to save settings');
      }

      setSaveStatus('saved');
      setTimeout(() => setSaveStatus(null), 2000);
    } catch (error) {
      console.error('Error saving settings:', error);
      setSaveStatus('error');
      setTimeout(() => setSaveStatus(null), 2000);
    }
  };

  const addCustomPath = () => {
    if (customPath.trim()) {
      setSettings(prev => ({
        ...prev,
        CUSTOM_COMMAND_PATHS: [...prev.CUSTOM_COMMAND_PATHS, customPath.trim()]
      }));
      setCustomPath('');
    }
  };

  const removeCustomPath = (index) => {
    setSettings(prev => ({
      ...prev,
      CUSTOM_COMMAND_PATHS: prev.CUSTOM_COMMAND_PATHS.filter((_, i) => i !== index)
    }));
  };

  const renderSettingGroup = (title, description, fields, visible = true) => {
    if (!visible) return null;

    return (
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-xl">{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          {fields.map(({ key, label, type = 'text', placeholder = '', tooltip }) => (
            <div key={key} className="grid gap-2">
              <div className="flex items-center gap-2">
                <label className="text-sm font-medium">{label || key}</label>
                {tooltip && (
                  <HoverCard>
                    <HoverCardTrigger>
                      <Info className="h-4 w-4 text-muted-foreground hover:text-foreground transition-colors cursor-help" />
                    </HoverCardTrigger>
                    <HoverCardContent className="w-80">
                      {tooltip}
                    </HoverCardContent>
                  </HoverCard>
                )}
              </div>
              <div className="relative">
                <Input
                  type={type === 'password' && !showPasswords[key] ? 'password' : 'text'}
                  value={settings[key]}
                  onChange={(e) => handleChange(key, e.target.value)}
                  placeholder={placeholder}
                  className="w-full pr-10"
                />
                {type === 'password' && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                    onClick={() => togglePasswordVisibility(key)}
                  >
                    {showPasswords[key] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                )}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    );
  };

  const shouldShowSection = (section) => {
    const system = settings.NOTE_TAKING_SYSTEM;
    switch (section) {
      case 'roam':
        return system === 'Roam Research';
      case 'remnote':
        return system === 'RemNote';
      case 'ideaflow':
        return system === 'IdeaFlow';
      case 'mem':
        return system === 'Mem';
      case 'notion':
        return system === 'Notion';
      case 'twitter':
        return system === 'Twitter';
      default:
        return true;
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold mb-8">Go Note Go Settings</h1>

      {loadingSettings && (
        <div className="text-center py-8">
          <p className="text-gray-500">Loading settings...</p>
        </div>
      )}

      {loadError && (
        <Alert className="mb-6 bg-red-100 text-red-800 border-red-200">
          <AlertDescription>
            Error loading settings. The settings API server might not be running.
            <div className="mt-2">
              <Button
                variant="outline"
                className="text-red-800 border-red-300 hover:bg-red-50"
                onClick={() => window.location.reload()}
              >
                Retry
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {!loadingSettings && !loadError && (
      <>
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-xl">Core Settings</CardTitle>
          <CardDescription>Essential configuration options</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="grid gap-2">
            <label className="text-sm font-medium">Note Taking System</label>
            <Select
              value={settings.NOTE_TAKING_SYSTEM}
              onValueChange={(value) => handleChange('NOTE_TAKING_SYSTEM', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a note-taking system" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {NOTE_TAKING_SYSTEMS.map(system => (
                    <SelectItem key={system} value={system}>
                      {system}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-2">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Audio Hotkey</label>
              <HoverCard>
                <HoverCardTrigger>
                  <Info className="h-4 w-4 text-muted-foreground hover:text-foreground transition-colors cursor-help" />
                </HoverCardTrigger>
                <HoverCardContent className="w-80">
                  <p className="text-sm space-y-2">
                    <ul className="list-none space-y-2">
                      <li><span className="font-medium">Single press</span> → Start recording</li>
                      <li><span className="font-medium">Single press again</span> → Stop recording</li>
                      <li><span className="font-medium">Double press</span> → Cancel recording</li>
                      <li><span className="font-medium">Hold 1 second</span> → Play previous recording</li>
                      <li className="text-muted-foreground text-xs mt-2">Recording also stops after 3 seconds of silence</li>
                    </ul>
                  </p>
                </HoverCardContent>
              </HoverCard>
            </div>
            <Input
              value={settings.HOTKEY}
              onChange={(e) => handleChange('HOTKEY', e.target.value)}
              placeholder="e.g., Esc"
            />
          </div>
          <div className="grid gap-2">
            <label className="text-sm font-medium">Blob Storage System</label>
            <Input
              value={settings.BLOB_STORAGE_SYSTEM}
              onChange={(e) => handleChange('BLOB_STORAGE_SYSTEM', e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      {renderSettingGroup('Essential Integrations', 'Required API keys and configurations', [
        {
          key: 'OPENAI_API_KEY',
          label: 'OpenAI API Key',
          type: 'password',
          tooltip: (
            <div className="space-y-2">
              <p>Required for audio transcription and language model features.</p>
              <p>
                Get your API key at:{' '}
              </p>
              <a
                href="https://platform.openai.com/api-keys"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 underline hover:text-blue-700"
              >
                platform.openai.com/api-keys
              </a>
            </div>
          )
        },
        {
          key: 'DROPBOX_ACCESS_TOKEN',
          label: 'Dropbox Access Token',
          type: 'password',
          tooltip: (
            <div className="space-y-2">
              <p>Used for storing audio recordings in Dropbox.</p>
              <p>
                Get your access token at:{' '}
              </p>
              <a
                href="https://www.dropbox.com/developers/apps"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 underline hover:text-blue-700"
              >
                dropbox.com/developers/apps
              </a>
            </div>
          )
        },
      ])}
      
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center gap-2">
            <CardTitle className="text-xl">WiFi Configuration</CardTitle>
            <HoverCard>
              <HoverCardTrigger>
                <Info className="h-4 w-4 text-muted-foreground hover:text-foreground transition-colors cursor-help" />
              </HoverCardTrigger>
              <HoverCardContent className="w-80">
                <div className="space-y-3">
                  <p>Configure WiFi settings for your device.</p>
                  <p className="text-sm text-muted-foreground">
                    Changes will apply after saving and restarting the network service.
                  </p>
                </div>
              </HoverCardContent>
            </HoverCard>
          </div>
          <CardDescription>Manage wireless network connections</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-2">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Country Code</label>
              <HoverCard>
                <HoverCardTrigger>
                  <Info className="h-4 w-4 text-muted-foreground hover:text-foreground transition-colors cursor-help" />
                </HoverCardTrigger>
                <HoverCardContent className="w-80">
                  <p className="text-sm">
                    Two-letter country code (e.g., US, GB, DE) to ensure compliance with local regulations.
                  </p>
                </HoverCardContent>
              </HoverCard>
            </div>
            <Input
              value={settings.WIFI_COUNTRY}
              onChange={(e) => handleChange('WIFI_COUNTRY', e.target.value)}
              placeholder="US"
              maxLength={2}
            />
          </div>
          
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-medium">WiFi Networks</h3>
              <HoverCard>
                <HoverCardTrigger>
                  <Info className="h-4 w-4 text-muted-foreground hover:text-foreground transition-colors cursor-help" />
                </HoverCardTrigger>
                <HoverCardContent className="w-80">
                  <p className="text-sm">
                    Add multiple WiFi networks. Your device will automatically connect to the strongest available network.
                  </p>
                </HoverCardContent>
              </HoverCard>
            </div>
            
            {/* List of saved networks */}
            <div className="space-y-2">
              {settings.WIFI_NETWORKS && settings.WIFI_NETWORKS.length > 0 ? (
                settings.WIFI_NETWORKS.map((network, index) => (
                  <div key={index} className="flex items-center justify-between bg-secondary/20 p-3 rounded">
                    <div className="flex-1">
                      <div className="font-medium">{network.ssid}</div>
                      <div className="text-sm text-muted-foreground">
                        {network.psk ? 'Secured (WPA)' : 'Open Network'}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => {
                        setSettings(prev => ({
                          ...prev,
                          WIFI_NETWORKS: prev.WIFI_NETWORKS.filter((_, i) => i !== index)
                        }));
                      }}
                      className="h-8 w-8"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))
              ) : (
                <div className="text-center text-muted-foreground py-4">
                  No WiFi networks configured
                </div>
              )}
            </div>
            
            {/* Add new network form */}
            <div className="space-y-3 border rounded p-3 border-dashed">
              <h4 className="text-sm font-medium">Add New Network</h4>
              
              <div className="grid gap-2">
                <label className="text-sm font-medium">Network Name (SSID)</label>
                <Input
                  value={newWifiNetwork.ssid}
                  onChange={(e) => setNewWifiNetwork(prev => ({ ...prev, ssid: e.target.value }))}
                  placeholder="WiFi network name"
                />
              </div>
              
              <div className="grid gap-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">Password</label>
                  <span className="text-xs text-muted-foreground">Leave empty for open networks</span>
                </div>
                <div className="relative">
                  <Input
                    type={showPasswords.newWifiPassword ? 'text' : 'password'}
                    value={newWifiNetwork.psk}
                    onChange={(e) => setNewWifiNetwork(prev => ({ ...prev, psk: e.target.value }))}
                    placeholder="WiFi password"
                    className="pr-10"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                    onClick={() => togglePasswordVisibility('newWifiPassword')}
                  >
                    {showPasswords.newWifiPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
              
              <Button
                onClick={() => {
                  if (newWifiNetwork.ssid.trim()) {
                    const newNetwork = {
                      ssid: newWifiNetwork.ssid.trim(),
                      ...(newWifiNetwork.psk ? { psk: newWifiNetwork.psk } : {})
                    };
                    
                    // Add to settings
                    setSettings(prev => ({
                      ...prev,
                      WIFI_NETWORKS: [...(prev.WIFI_NETWORKS || []), newNetwork]
                    }));
                    
                    // Reset form
                    setNewWifiNetwork({ ssid: '', psk: '' });
                  }
                }}
                className="w-full"
                disabled={!newWifiNetwork.ssid.trim()}
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Network
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center gap-2">
            <CardTitle className="text-xl">Email Configuration</CardTitle>
            <HoverCard>
              <HoverCardTrigger>
                <Info className="h-4 w-4 text-muted-foreground hover:text-foreground transition-colors cursor-help" />
              </HoverCardTrigger>
              <HoverCardContent className="w-80">
                <div className="space-y-3">
                  <p className="font-medium">When are emails sent?</p>
                  <div className="space-y-2">
                    <div className="flex items-start gap-2">
                      <span className="font-medium">1.</span>
                      <span>When <span className="font-medium">Email</span> is your note-taking system</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="font-medium">2.</span>
                      <div>
                        <span>When using the email command:</span>
                        <code className="block mt-1 px-2 py-1 bg-muted rounded text-xs">:email recipient@example.com "Email Subject" "Email Body"</code>
                      </div>
                    </div>
                  </div>
                </div>
              </HoverCardContent>
            </HoverCard>
          </div>
          <CardDescription>Configure email delivery settings</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="grid gap-2">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Recipient Email</label>
              <HoverCard>
                <HoverCardTrigger>
                  <Info className="h-4 w-4 text-muted-foreground hover:text-foreground transition-colors cursor-help" />
                </HoverCardTrigger>
                <HoverCardContent className="w-80">
                  <div className="text-sm space-y-2">
                    <p>This email address is only used when <span className="font-medium">Email</span> is selected as your note-taking system.</p>
                    <p className="text-muted-foreground">When using the :email command, specify the recipient in the command itself.</p>
                  </div>
                </HoverCardContent>
              </HoverCard>
            </div>
            <Input
              value={settings.EMAIL}
              onChange={(e) => handleChange('EMAIL', e.target.value)}
              placeholder="you@example.com"
            />
          </div>

          <div className="grid gap-2">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Sender Email</label>
              <HoverCard>
                <HoverCardTrigger>
                  <Info className="h-4 w-4 text-muted-foreground hover:text-foreground transition-colors cursor-help" />
                </HoverCardTrigger>
                <HoverCardContent className="w-80">
                  <p className="text-sm">
                    The email address that will be used to send your notes. This should be the address associated with your SMTP server account.
                  </p>
                </HoverCardContent>
              </HoverCard>
            </div>
            <Input
              value={settings.EMAIL_USER}
              onChange={(e) => handleChange('EMAIL_USER', e.target.value)}
              placeholder="your-sender@gmail.com"
            />
          </div>

          <div className="grid gap-2">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Email Password</label>
              <HoverCard>
                <HoverCardTrigger>
                  <Info className="h-4 w-4 text-muted-foreground hover:text-foreground transition-colors cursor-help" />
                </HoverCardTrigger>
                <HoverCardContent className="w-80">
                  <p className="text-sm">
                    For Gmail, use an App Password generated from your Google Account settings. Regular password won't work with 2FA enabled.
                  </p>
                </HoverCardContent>
              </HoverCard>
            </div>
            <div className="relative">
              <Input
                type={showPasswords.EMAIL_PASSWORD ? 'text' : 'password'}
                value={settings.EMAIL_PASSWORD}
                onChange={(e) => handleChange('EMAIL_PASSWORD', e.target.value)}
                placeholder="Your email password or app password"
                className="pr-10"
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                onClick={() => togglePasswordVisibility('EMAIL_PASSWORD')}
              >
                {showPasswords.EMAIL_PASSWORD ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            </div>
          </div>

          <div className="grid gap-2">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">SMTP Server</label>
              <HoverCard>
                <HoverCardTrigger>
                  <Info className="h-4 w-4 text-muted-foreground hover:text-foreground transition-colors cursor-help" />
                </HoverCardTrigger>
                <HoverCardContent className="w-80">
                  <p className="text-sm space-y-2">
                    <ul className="list-none space-y-2">
                      <li><span className="font-medium">Gmail:</span> smtp.gmail.com</li>
                      <li><span className="font-medium">Outlook:</span> smtp.office365.com</li>
                      <li><span className="font-medium">Yahoo:</span> smtp.mail.yahoo.com</li>
                    </ul>
                  </p>
                </HoverCardContent>
              </HoverCard>
            </div>
            <Input
              value={settings.EMAIL_SERVER}
              onChange={(e) => handleChange('EMAIL_SERVER', e.target.value)}
              placeholder="smtp.gmail.com"
            />
          </div>
        </CardContent>
      </Card>

      {/* Conditional Settings based on Note Taking System */}
      {renderSettingGroup('Roam Research', 'Roam Research integration settings', [
        { key: 'ROAM_GRAPH', label: 'Graph Name' },
        { key: 'ROAM_USER', label: 'Username' },
        { key: 'ROAM_PASSWORD', label: 'Password', type: 'password' },
      ], shouldShowSection('roam'))}

      {renderSettingGroup('RemNote', 'RemNote integration settings', [
        { key: 'REMNOTE_USER_ID', label: 'User ID' },
        { key: 'REMNOTE_API_KEY', label: 'API Key', type: 'password' },
        { key: 'REMNOTE_ROOT_REM', label: 'Root Rem' },
      ], shouldShowSection('remnote'))}

      {renderSettingGroup('IdeaFlow', 'IdeaFlow integration settings', [
        { key: 'IDEAFLOW_USER', label: 'Username' },
        { key: 'IDEAFLOW_PASSWORD', label: 'Password', type: 'password' },
      ], shouldShowSection('ideaflow'))}

      {renderSettingGroup('Mem', 'Mem integration settings', [
        { key: 'MEM_API_KEY', label: 'API Key', type: 'password' },
      ], shouldShowSection('mem'))}

      {renderSettingGroup('Notion', 'Notion integration settings', [
        { key: 'NOTION_INTEGRATION_TOKEN', label: 'Integration Token', type: 'password' },
        { key: 'NOTION_DATABASE_ID', label: 'Database ID' },
      ], shouldShowSection('notion'))}

      {renderSettingGroup('Twitter API', 'Twitter API credentials', [
        { key: 'TWITTER_API_KEY', label: 'API Key', type: 'password' },
        { key: 'TWITTER_API_SECRET', label: 'API Secret', type: 'password' },
        { key: 'TWITTER_ACCESS_TOKEN', label: 'Access Token', type: 'password' },
        { key: 'TWITTER_ACCESS_TOKEN_SECRET', label: 'Access Token Secret', type: 'password' },
      ], shouldShowSection('twitter'))}

      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-xl">Custom Command Paths</CardTitle>
          <CardDescription>Add custom command paths for extended functionality</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              value={customPath}
              onChange={(e) => setCustomPath(e.target.value)}
              placeholder="Enter custom command path"
              className="flex-1"
            />
            <Button onClick={addCustomPath} className="whitespace-nowrap">
              <Plus className="h-4 w-4 mr-2" />
              Add Path
            </Button>
          </div>
          <div className="space-y-2">
            {settings.CUSTOM_COMMAND_PATHS.map((path, index) => (
              <div key={index} className="flex items-center justify-between bg-secondary/20 p-2 rounded">
                <span className="text-sm">{path}</span>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => removeCustomPath(index)}
                  className="h-8 w-8"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="sticky bottom-6">
        <div className="flex flex-col items-end gap-4">
          {saveStatus === 'saved' && (
            <Alert className="w-72">
              <AlertDescription>Settings saved successfully!</AlertDescription>
            </Alert>
          )}
          {saveStatus === 'error' && (
            <Alert className="w-72 bg-red-100 text-red-800 border-red-200">
              <AlertDescription>Error saving settings. Please try again.</AlertDescription>
            </Alert>
          )}
          <Button
            onClick={handleSave}
            className="w-32"
            disabled={saveStatus === 'saving'}
          >
            {saveStatus === 'saving' ? (
              'Saving...'
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Save
              </>
            )}
          </Button>
        </div>
      </div>
      </>
      )}
    </div>
  );
};

function App() {
  return (
    <div className="min-h-screen w-screen">
      <div className="container w-full max-w-4xl mx-auto p-6 space-y-6">
        <SettingsUI />
      </div>
    </div>
  );
}

export default App;
