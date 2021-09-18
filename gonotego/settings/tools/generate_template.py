#!/usr/bin/python
"""Generates secure_settings_template.py from secure_settings.py."""

import re

SETTING_RE = r"""(\w*) = (['"]).*\2"""
SETTING_TEMPLATE = r"\1 = '<\1>'"


def main():
  with open('settings/secure_settings.py', 'r') as secure_settings_file:
    with open('settings/secure_settings_template.py', 'w') as secure_settings_template_file:
      secure_settings = secure_settings_file.read()
      secure_settings_template = secure_settings

      secure_settings_template = re.sub(
          SETTING_RE,
          SETTING_TEMPLATE,
          secure_settings
      )

      secure_settings_template_file.write(secure_settings_template)


if __name__ == '__main__':
  main()
