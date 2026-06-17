#!/usr/bin/env python
# File name   : Buzzer_Alive.py
# Song        : Modotek - Alive (voldo87)
# Generated from MIDI file: Modotek_-_Alive__voldo87_20111126085413.mid
from gpiozero import TonalBuzzer
import time
import threading

tb = TonalBuzzer(18)

class Player(threading.Thread):
    def __init__(self, *args, **kwargs):
        self.ALIVE = [
            ['C5', 0.052],
            ['rest', 0.061],
            ['C5', 0.108],
            ['rest', 0.569],
            ['C5', 0.183],
            ['rest', 0.042],
            ['D5', 0.146],
            ['rest', 0.08],
            ['Eb5', 0.108],
            ['F5', 0.221],
            ['F4', 0.089],
            ['rest', 0.023],
            ['F4', 0.108],
            ['Ab4', 0.089],
            ['rest', 0.023],
            ['Ab4', 0.108],
            ['rest', 0.456],
            ['G4', 0.07],
            ['rest', 0.042],
            ['G4', 0.108],
            ['rest', 0.117],
            ['G4', 0.169],
            ['rest', 0.056],
            ['G4', 0.108],
            ['rest', 0.235],
            ['Eb5', 0.108],
            ['C5', 0.07],
            ['rest', 0.042],
            ['C5', 0.108],
            ['rest', 0.569],
            ['C5', 0.183],
            ['rest', 0.042],
            ['D5', 0.146],
            ['rest', 0.08],
            ['Eb5', 0.108],
            ['F5', 0.221],
            ['F4', 0.089],
            ['rest', 0.023],
            ['F4', 0.108],
            ['Ab4', 0.089],
            ['rest', 0.023],
            ['Ab4', 0.108],
            ['rest', 0.456],
            ['G4', 0.07],
            ['rest', 0.042],
            ['G4', 0.108],
            ['rest', 0.117],
            ['G4', 0.169],
            ['rest', 0.056],
            ['G4', 0.108],
            ['rest', 0.235],
            ['Eb5', 0.108],
        ]

        self.__flag = threading.Event()
        self.__flag.clear()
        self.MusicMode = 0
        super(Player, self).__init__(*args, **kwargs)

    def play(self, tune):
        for note, duration in tune:
            if self.MusicMode == 0:
                break
            if note == "rest":
                tb.stop()
            else:
                tb.play(note)
            time.sleep(float(duration))
        tb.stop()

    def start_playing(self):
        self.MusicMode = 1
        self.resume()

    def pause(self):
        self.__flag.clear()
        tb.stop()
        self.MusicMode = 0

    def resume(self):
        self.__flag.set()

    def run(self):
        while True:
            self.__flag.wait()
            try:
                self.play(self.ALIVE)
            except KeyboardInterrupt:
                self.pause()
                print("Program terminated by user.")

if __name__ == "__main__":
    player = Player()
    player.daemon = True
    player.start()
    player.start_playing()
    time.sleep(12)
    player.pause()