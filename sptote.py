#!/usr/bin/env python3

import os
import sys
import sounddevice
import queue
import json

from vosk import Model, KaldiRecognizer

MAX_LENGTH = 100

q = queue.Queue()
def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

try:
    device_no = 0
    for i, device in enumerate(sounddevice.query_devices()):
        if device["name"] == "default":
            device_no = i
            break
    
    device_info = sounddevice.query_devices(device_no, "input")
    samplerate = int(device_info["default_samplerate"])
    model = Model(lang="en-us")

    with sounddevice.RawInputStream(
            samplerate=samplerate, blocksize=8000, device=device_no, dtype="int16", channels=1, callback=callback):

        rec = KaldiRecognizer(model, samplerate)
        previous = ""
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                text = json.loads(rec.Result())["text"]
                print("\x1B[2K\r\x1B[32;1m{}\x1B[0m".format(text))
                previous = ""
            else:
                text = json.loads(rec.PartialResult())["partial"]
                common_text = os.path.commonprefix([previous, text])
                new_text = text[len(common_text):]
                print("\x1B[2K\r\x1B[33;1m", end="")
                print(common_text, end="")
                print("\x1B[31;1m", end="")
                print(new_text, end="")
                print("\x1B[0m", end="", flush=True)
                previous = text
            

except Exception as e:
    print("\x1B[0m")
    sys.exit(type(e).__name__ + ": " + str(e))