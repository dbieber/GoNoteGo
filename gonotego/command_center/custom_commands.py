import importlib
import os
import sys

from gonotego.settings import secure_settings


def register_custom_commands(paths):
  for path in paths:
    if os.path.exists(path) and path.endswith('.py'):
      module_name = os.path.splitext(os.path.basename(path))[0]

      spec = importlib.util.spec_from_file_location(module_name, path)
      module = importlib.util.module_from_spec(spec)

      if module_name not in sys.modules:
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        print(f"Module '{module_name}' has been imported from '{path}'.")
      else:
        print(f"Module '{module_name}' is already imported.")
    else:
      print(f"Path '{path}' is not a valid Python file.")
  sys.stdout.flush()

register_custom_commands(secure_settings.CUSTOM_COMMAND_PATHS)
