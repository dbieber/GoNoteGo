# Go Note Go

_Go Note Go is a note-taking system for when you're on the go, with a focus on driving and camping._

[Read about it here.](https://davidbieber.com/projects/go-note-go/)

## Features

* Take notes using audio or text
* Take notes offline
* Automatically export notes to your favorite note-taking systems when internet becomes available
* Automatic transcription from voice to text
* No monitor. No distractions. Audio notes are safe for driving.
* Free and open source software, inexpensive hardware
* Add custom voice and text commands
* Lots of built in commands

## Supported Note-taking Systems

* [Roam Research](https://roamresearch.com/)
* [RemNote](https://www.remnote.com/)
* [IdeaFlow](https://ideaflow.app/)
* [Mem](https://mem.ai/)
* [Notion](https://www.notion.so/)
* [Twitter](https://www.twitter.com/)
* [Email](https://en.wikipedia.org/wiki/Email)

Want to contribute a new note-taking system?

## Built in commands

Have a look at [command_center/commands.py](gonotego/command_center/commands.py) to see the currently supported commands.

Some ideas for commands include:

* Reading back old notes
* Spaced Repetition
* Perfect Pitch Practice
* Reminders
* Calculator
* Sending messages
* Setting alarms
* Programming with Codex
* Question answering
* Hearing the Time

## Hardware Parts

Go Note Go is designed to run on a [Raspberry Pi 400](https://www.raspberrypi.com/products/raspberry-pi-400/).

Recommended additional hardware:

* 1 USB speaker
* 1 USB microphone

Recommended hardware to install Go Note Go in your car, to truly take Go Note Go on the go:

* Velcro
* 10000 mAh battery
* 3 ft USB - USB C cable
* 6 in USB - USB C cable

See the [hardware guide](hardware.md) to know exactly what to buy.

## Installation

See the [installation instructions](installation.md) to get started.

## CI/CD

The GitHub Action workflow caches the Raspberry Pi image to save build time. However, these images are large and can cause "No space left on device" errors in the GitHub Actions environment. If you encounter these errors, consider clearing the cache or optimizing the image storage strategy.

## History

[Learn about Go Note Go's predecessor "Shh Shell" here.](https://davidbieber.com/projects/shh-shell/)

[Hear Go Note Go's origin story here.](https://davidbieber.com/post/2022-12-30-go-note-go-story/)
