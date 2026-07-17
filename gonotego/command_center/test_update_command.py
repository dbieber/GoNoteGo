"""Tests for the ':update' command and its update script."""
import os
import subprocess
from unittest import mock

from gonotego.command_center import system_commands


def test_update_script_exists_and_is_valid_bash():
  script = os.path.join(system_commands.get_repo_dir(), 'scripts', 'update.sh')
  assert os.path.exists(script)
  # Syntax check only.
  result = subprocess.run(['bash', '-n', script], capture_output=True, text=True)
  assert result.returncode == 0, result.stderr


def test_update_command_launches_script_detached():
  with mock.patch.object(system_commands, 'shell') as shell:
    system_commands.update()
  command = shell.call_args[0][0]
  assert 'nohup' in command
  assert 'scripts/update.sh' in command
  assert command.strip().endswith('&')


def test_update_command_registered():
  from gonotego.command_center import registry
  patterns = {command.regex.pattern for command in registry.COMMANDS}
  assert '^update$' in patterns


def test_supervisord_conf_parses_and_lists_all_programs():
  """The same parse the update script relies on for pre-restart verification."""
  import configparser
  conf_path = os.path.join(system_commands.get_repo_dir(), 'gonotego', 'supervisord.conf')
  parser = configparser.ConfigParser(strict=False)
  assert parser.read(conf_path)
  programs = {section for section in parser.sections() if section.startswith('program:')}
  assert 'program:GoNoteGo-command-center' in programs
  assert 'program:GoNoteGo-network' in programs
  assert 'program:GoNoteGo-uploader' in programs
