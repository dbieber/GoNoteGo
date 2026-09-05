"""Shared pytest configuration.

secure_settings.py holds per-device secrets and is not checked in. Modules
that import gonotego.settings.settings need it to exist, so when it is absent
the tests get an empty stand-in module instead.
"""
import importlib
import sys
import types

try:
  importlib.import_module('gonotego.settings.secure_settings')
except ImportError:
  stub = types.ModuleType('gonotego.settings.secure_settings')
  sys.modules['gonotego.settings.secure_settings'] = stub
  import gonotego.settings
  gonotego.settings.secure_settings = stub
