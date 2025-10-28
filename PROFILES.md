# Go Note Go Profiles

Profiles allow you to quickly switch between different Go Note Go configurations. Each profile stores a complete snapshot of all settings, plus a name and optional numeric shortcut.

## Quick Start

### Create Your First Profile

Set up your settings the way you want them, then save as a profile with a shortcut:

```
:profile save roam 1
```

This creates a profile named "roam" with shortcut `:1`.

### Switch Between Profiles

Use the numeric shortcuts you've configured:
```
:1    # Switch to profile with shortcut 1
:2    # Switch to profile with shortcut 2
:3    # Switch to profile with shortcut 3
:4    # Switch to profile with shortcut 4
```

Or use the full command:
```
:profile load roam
```

## Commands

### Save a Profile
```
:profile save <name>              # Save without shortcut
:profile save <name> <number>     # Save with numeric shortcut
```

Examples:
```
:profile save roam 1              # Save as "roam" with shortcut :1
:profile save work 2              # Save as "work" with shortcut :2
:profile save temp                # Save as "temp" with no shortcut
```

### Load a Profile
```
:profile load <name>              # Load by name
:<number>                         # Load by shortcut (if configured)
```

Your current settings are automatically backed up to the `backup` profile before loading.

### List Profiles
```
:profile list
```
Shows all saved profiles with their shortcuts (if any).

Example output: `Profiles: backup, roam (:1), temp, work (:2)`

### Current Profile
```
:profile current
```
Shows which profile is currently active.

### Delete a Profile
```
:profile delete <name>
```
Deletes a saved profile and removes its shortcut mapping.

## Example Use Cases

### Personal vs Work
```
:profile save personal 1          # Personal Roam graph
:profile save work 2               # Work note-taking system
```

Then switch with `:1` or `:2`

### Different Assistants
```
:profile save assistant 3          # Connected to personal assistant
:profile save guest 4               # Safe settings for demos
```

### Different Upload Destinations
Switch between Roam, RemNote, Notion, etc. with a single command.

## How It Works

- Each profile stores all settings from `secure_settings.py` as JSON in Redis
- Profile metadata (name, shortcut) is stored with the settings
- Shortcuts are mapped dynamically in Redis (no hardcoded values)
- When you load a profile, current settings are backed up to `backup`
- The `backup` profile always contains your most recent settings

## Safety

- Your current settings are always backed up to `backup` before loading a new profile
- The secure_settings.py file is never modified - profiles only affect Redis settings
- You can always revert: `:profile load backup`
- Deleting a profile also removes its shortcut mapping

## Configuration

Profiles are completely user-configurable:
- Choose your own profile names
- Assign any numeric shortcuts you want
- No hardcoded profile names in the codebase
- Works for any Go Note Go user
