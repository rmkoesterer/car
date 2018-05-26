#!/bin/bash

STRING=$1
NAME=$2

gtts-cli -l en-uk "$STRING" --output tts/${NAME}.mp3

