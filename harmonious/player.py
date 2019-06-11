from typing import List, Iterable, Union
import sys
import time
from multiprocessing import Process, Lock, Manager
import socket

import simplejson as json
from pythonosc import udp_client
import toolz as t

from harmonious.music import note_midi, voicing, symbol_chord, chord
from harmonious.fiducials import fiducial_chord

def play_note(value):
  return f"noteon 0 {value} 100"

def end_note(value):
  return f"noteoff 0 {value}"

def play_chord(values):
  return '\n'.join(play_note(x) for x in values)

def stop_chord(values):
  return '\n'.join(end_note(x) for x in values)


HOST = '127.0.0.1'  # The synth's hostname or IP address
PORT = 8000         # The port used by the synth


def send(HOST, PORT, msg):
  if msg.strip() == '': return
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    s.connect((HOST, PORT))
    totalsent = 0
    while totalsent < len(msg):
      sent = s.send(msg[totalsent:].encode('utf-8'))
      if sent == 0:
        raise RuntimeError("socket connection broken")
      totalsent = totalsent + sent


oscsender = udp_client.SimpleUDPClient('192.168.43.75', 3334)


def bar(notes):
  for i in range(2):
      send(HOST, PORT, play_chord(notes[1:]))
      time.sleep(0.3)
      send(HOST, PORT, play_chord(notes[0:1]))
      time.sleep(0.3)
      send(HOST, PORT, play_chord(notes[1:]))
      time.sleep(0.3)
      send(HOST, PORT, play_chord(notes[0:1]))
      time.sleep(0.3)


def poller(notes):
  print('poller is active')
  i = 0
  while True:
    if i >= len(notes): i = 0
    oscsender.send_message('/light', [i, (i-1) % len(notes)])
    bar(notes[i])
    i += 1


def setter(notes):
  stdin = open(0)
  state = {0: {}}
  print('setter is active')
  for line in stdin:
    state = t.merge(state, json.loads(line,
      object_hook=lambda d: {int(k) if k.lstrip('-').isdigit() else k: v for k, v in d.items()}))
    notes[:] = t.get(list(range(max(state.keys())+1)), t.valmap(fiducial_chord, state), default=[])
    print('notes = ', notes)


def symbol_setter(notes):
  stdin = open(0)
  print('symbol_setter is active')
  for line in stdin:
    notes[:] = [symbol_chord(*line.split())] if len(line.split()) == 2 else [[]]


if __name__ == '__main__':
  manager = Manager()
  notes = manager.list([[]])
  p1 = Process(target = poller, args=(notes,))
  p2 = Process(target = (setter if len(sys.argv) <= 1 else symbol_setter), args=(notes,))
  p1.start()
  p2.start()
  p2.join()
