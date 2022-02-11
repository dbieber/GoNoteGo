"""
Go Note Go app for Mac.

Puts GNG in the Mac toolbar so you can see if it's active.
Adds a keyboard shortcut for toggling recording on and off.
When active, keystrokes are logged and processed.
When inactive, nothing is recorded.

How does this work?
We store the active/inactive state in redis,
and show the latest value in the toolbar.
The text and audio recording processes use this status to determine whether to record
any notes.

TODOs:
- [x] Add keyboard shortcut for toggling active status.
- [x] Show active status in toolbar.
- [x] Respect active status in text.
- [x] Respect active status in audio.

- [x] On quit, spin down all processes.
- [] Restart subprocesses if they fail.
"""
import multiprocessing

import rumps

from gonotego.audio import runner as audio_runner
from gonotego.command_center import runner as command_center_runner
from gonotego.text import runner as text_runner
from gonotego.transcription import runner as transcription_runner
from gonotego.uploader import runner as uploader_runner

from gonotego.common import status

Status = status.Status


ACTIVE_TITLE = '𝐆'
PAUSED_TITLE = '𝐍𝐆'


class GoNoteGoApp(rumps.App):

  def register_processes(self, processes):
    self.processes = processes

  @rumps.timer(0.1)
  def set_title(self, _):
    paused = status.get(Status.PAUSED)
    old_title = self.title
    if paused and old_title != PAUSED_TITLE:
      self.title = PAUSED_TITLE
    elif not paused and old_title != ACTIVE_TITLE:
      self.title = ACTIVE_TITLE

  @rumps.clicked("Quit")
  def quit(self, sender):
    for process in processes:
      process.kill()
    rumps.quit_application(sender)

if __name__ == '__main__':
  processes = [
      multiprocessing.Process(target=audio_runner.main),
      multiprocessing.Process(target=command_center_runner.main),
      multiprocessing.Process(target=text_runner.main),
      multiprocessing.Process(target=transcription_runner.main),
      multiprocessing.Process(target=uploader_runner.main),
  ]
  for process in processes:
    process.start()

  app = GoNoteGoApp(ACTIVE_TITLE, quit_button=None)
  app.register_processes(processes)
  app.run()
