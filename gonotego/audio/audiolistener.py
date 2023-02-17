import subprocess

import numpy as np
import sounddevice as sd
import soundfile as sf

from gonotego.common import status
from gonotego.leds import indicators

Status = status.Status

SILENCE_THRESHOLD = 0.10


def get_max_volume(samples):
  return np.max(np.abs(samples))


def set_audio_recording_status(recording):
  status.set(Status.AUDIO_RECORDING, recording)
  if recording:
    indicators.set(state=1)
    if status.get(Status.VOLUME_SETTING) != 'off':
      subprocess.call(['aplay', 'gonotego/assets/beep_hi.wav'])

  else:
    indicators.set(state=0)
    if status.get(Status.VOLUME_SETTING) != 'off':
      subprocess.call(['aplay', 'gonotego/assets/beep_lo.wav'])


class AudioListener:

  def __init__(self):
    self.samplerate = sd.default.samplerate = 44100
    self.channels = sd.default.channels = 1

    self.recording = False
    self.stream = None
    self.file = None

  def record(self, filepath):
    self.recording = True
    set_audio_recording_status(self.recording)

    self.file = sf.SoundFile(
        filepath,
        mode='x',  # 'x' raises an error if the file already exists.
        samplerate=self.samplerate,
        channels=self.channels,
        # subtype='PCM_24',
    )

    # Keep track of how much silence there is to allow for early stopping.
    self.max_volume = 0.001
    self.consecutive_loud = 0
    self.consecutive_quiet = 0
    self.consecutive_loud_frames = 0
    self.consecutive_quiet_frames = 0

    def record_callback(indata, frames, time, status):
      frame_max_volume = get_max_volume(indata)
      if frame_max_volume / self.max_volume > SILENCE_THRESHOLD:
        # Loud frame.
        self.consecutive_loud += 1
        self.consecutive_loud_frames += frames
        if self.consecutive_loud > 20:
          self.consecutive_quiet = 0
          self.consecutive_quiet_frames = 0
      else:
        # Quiet frame.
        self.consecutive_quiet += 1
        self.consecutive_quiet_frames += frames
        if self.consecutive_quiet > 20:
          self.consecutive_loud = 0
          self.consecutive_loud_frames = 0

      self.max_volume = max(self.max_volume, frame_max_volume)
      self.file.write(indata.copy())

    assert self.stream is None
    try:
      self.stream = sd.InputStream(callback=record_callback)
      self.stream.start()
    except sounddevice.PortAudioError:
      self.recording = False
      self.stream = None
      set_audio_recording_status(self.recording)

  def silence_length(self):
    return self.consecutive_quiet_frames / self.samplerate

  def stop(self):
    self.recording = False
    set_audio_recording_status(self.recording)
    self.stream.stop()
    self.stream.close()
    self.file.flush()
    self.file.close()
    self.stream = None
