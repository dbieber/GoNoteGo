import setuptools

DEPENDENCIES = [
    'fire>=0.4.0',
    'keyboard',
    'sounddevice',
    'soundfile',
]

packages = [
    'gonotego',
    'gonotego.audio',
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
