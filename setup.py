import setuptools

DEPENDENCIES = [
    'absl-py',
    'adafruit-circuitpython-dotstar',
    'adafruit-circuitpython-motor',
    'adafruit-circuitpython-bmp280',
    'apscheduler',
    'dropbox',
    'fire>=0.4.0',
    'keyboard',
    'google-cloud-speech',
    'numpy',
    'parsedatetime',
    'redis',
    'selenium',
    'sounddevice',
    'soundfile',
    'supervisor',
]

packages = [
    'gonotego',
    'gonotego.audio',
    'gonotego.command_center',
    'gonotego.common',
    'gonotego.leds',
    'gonotego.settings',
    'gonotego.text',
    'gonotego.transcription',
    'gonotego.uploader',
    'gonotego.uploader.blob',
    'gonotego.uploader.browser',
    'gonotego.uploader.ideaflow',
    'gonotego.uploader.mem',
    'gonotego.uploader.notion',
    'gonotego.uploader.remnote',
    'gonotego.uploader.roam',
]
setuptools.setup(
    name='GoNoteGo',
    version='1.0.0',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    packages=packages,
    package_dir={d: d.replace('.', '/') for d in packages},
    python_requires='>=3.7',
    install_requires=DEPENDENCIES,
)
