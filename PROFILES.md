# Go Note Go Profiles

Profiles allow you to quickly switch between different Go Note Go configurations. Each profile stores a complete snapshot of all settings.

## Quick Start

### Initialize Default Profiles

First, set up your settings the way you want them, then run:
```
:profile init
```

This creates four default profiles:
- `roam` (shortcut: `:1`)
- `work` (shortcut: `:2`)
- `assistant` (shortcut: `:3`)
- `guest` (shortcut: `:4`)

### Switch Between Profiles

Use the numeric shortcuts:
```
:1    # Switch to roam profile
:2    # Switch to work profile
:3    # Switch to assistant profile
:4    # Switch to guest profile
```

Or use the full command:
```
:profile load roam
```

## Commands

### Save a Profile
```
:profile save <name>
```
Saves your current settings as a named profile.

### Load a Profile
```
:profile load <name>
```
Loads all settings from the specified profile. Your current settings are automatically backed up to the `backup` profile before loading.

### List Profiles
```
:profile list
```
Shows all saved profiles.

### Current Profile
```
:profile current
```
Shows which profile is currently active.

### Delete a Profile
```
:profile delete <name>
```
Deletes a saved profile.

## Example Use Cases

### Personal vs Work
- Profile 1 (roam): Personal Roam graph with your personal account
- Profile 2 (work): Work Roam graph or different note-taking system

### Different Assistants
- Profile 3 (assistant): Connected to your personal assistant
- Profile 4 (guest): Safe settings for letting others try your GNG

### Different Upload Destinations
Switch between different note-taking systems (Roam, RemNote, Notion, etc.) with a single command.

## How It Works

- Each profile is stored as a JSON blob in Redis containing all setting values
- When you load a profile, your current settings are automatically backed up
- The `backup` profile always contains your most recent settings before the last profile switch
- Settings include: uploader type, credentials, custom command paths, API keys, etc.

## Safety

- Your current settings are always backed up to `backup` before loading a new profile
- The secure_settings.py file is never modified - profiles only affect Redis settings
- You can always revert to your previous settings by running `:profile load backup`
