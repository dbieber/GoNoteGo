from gonotego.command_center import email_commands

DRAFT_FILENAME = 'draft'


def clip(x, a, b):
  """Clips x to be between a and b inclusive."""
  x = max(a, x)
  x = min(x, b)
  return x


class Uploader:

  def __init__(self):
    self.last_indent_level = -1
    self.indent_level = 0

  def upload(self, note_events):
    for note_event in note_events:
      if note_event.action == events.INDENT:
        self.indent_level = clip(self.indent_level + 1, 0, self.last_indent_level + 1)
      elif note_event.action == events.UNINDENT:
        self.indent_level = clip(self.indent_level - 1, 0, self.last_indent_level + 1)
      elif note_event.action == events.CLEAR_EMPTY:
        self.indent_level = 0
      elif note_event.action == events.ENTER_EMPTY:
        # Similar to unindent.
        self.indent_level = clip(self.indent_level - 1, 0, self.last_indent_level + 1)
      elif note_event.action == events.END_SESSION:
        self.end_session()
      elif note_event.action == events.SUBMIT:
        text = note_event.text.strip()
        line = '  ' * self.indent_level + text
        with open(DRAFT_FILENAME, 'a') as f:
          f.write(line + '\n')
        self.last_indent_level = self.indent_level

  def handle_inactivity(self):
    self.end_session()

  def handle_disconnect(self):
    self.end_session()

  def end_session(self):
    # First, send the message.
    with open(DRAFT_FILENAME, 'r') as f:
      text = f.read()
    subject = text.split('\n', 1)[0]
    email_commands.email(to, subject, text)

    # Then reset, the session.
    open(DRAFT_FILENAME, 'w').close()
    self.last_indent_level = -1
    self.indent_level = 0
