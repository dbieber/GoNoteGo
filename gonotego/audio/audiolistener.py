import numpy as np
import sounddevice as sd
import soundfile as sf

SILENCE_THRESHOLD = 0.10


def get_max_volume(samples):
  return np.max(np.abs(samples))


class AudioListener:

  def __init__(self):
    self.samplerate = sd.default.samplerate = 44100
    self.channels = sd.default.channels = 1

    self.recording = False
    self.stream = None
    self.file = None

  def record(self, filepath):
    self.recording = True

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
        # print(f'Loud frame ({frame_max_volume} / {self.max_volume}, {frame_max_volume / self.max_volume})')
        self.consecutive_loud += 1
        self.consecutive_loud_frames += frames
        if self.consecutive_loud > 20:
          self.consecutive_quiet = 0
          self.consecutive_quiet_frames = 0
      else:
        # print(f'Quiet frame ({frame_max_volume}  / {self.max_volume}) {frame_max_volume / self.max_volume}')
        self.consecutive_quiet += 1
        self.consecutive_quiet_frames += frames
        if self.consecutive_quiet > 20:
          self.consecutive_loud = 0
          self.consecutive_loud_frames = 0

      self.max_volume = max(self.max_volume, frame_max_volume)
      self.file.write(indata.copy())

    assert self.stream is None
    self.stream = sd.InputStream(callback=record_callback)
    self.stream.start()

  def silence_length(self):
    return self.consecutive_quiet_frames / self.samplerate

  def stop(self):
    self.recording = False
    self.stream.stop()
    self.stream.close()
    self.file.flush()
    self.file.close()
    self.stream = None


def main():
  listener = AudioListener()
  listener.record('tmp.wav')
  time.sleep(3)
  listener.stop()
