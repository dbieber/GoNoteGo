import setuptools

DEPENDENCIES = [
    'absl-py',
    'dropbox',
    'fire>=0.4.0',
    'keyboard',
    'google-cloud-speech',
    'redis',
    'sounddevice',
    'soundfile',
    'supervisor',
]

packages = [
    'gonotego',
    'gonotego.audio',
    'gonotego.common',
    'gonotego.text',
    'gonotego.transcription',
]
setuptools.setup(
    name="GoNoteGo",
    version="1.0.0",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    packages=packages,
    package_dir={d: d.replace('.', '/') for d in packages},
    python_requires='>=3.7',
    install_requires=DEPENDENCIES,
)
