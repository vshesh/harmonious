from bidict import bidict
import sys
import regex as re
import toolz as t
import simplejson as json
import time

note_value = {
  'C': 0,
  'C#':1,
  'Db':1,
  'D': 2,
  'D#':3,
  'Eb':3,
  'E': 4,
  'Fb':4,
  'E#':5,
  'F': 5,
  'F#':6,
  'Gb':6,
  'G': 7,
  'G#':8,
  'Ab':8,
  'A': 9,
  'A#':10,
  'Bb':10,
  'B': 11,
  'B#':12,
  'Cb':11
}

def note_midi(note, octave = None):
  if octave is not None:
    return note_value[note] + 12*(octave+1)
  elif re.match('[A-G][#b]?[0-6]', root):
    return note_value[note[:-1]] + 12*(int(note[-1]) + 1)
  else:
    return None

# chord naming scheme
# unlike regular chord names which are deviations from a major chord,
# these are based on 'layer' presence or absences

# 1 - blank
# 5 (b5 #5)   5 o +
# b3 3 (2 4)  - ∆ 2 4
# b7 7        * !
# 9 (b9 #9)   9 < >
# 11 #11      ~ ?
# b13 13      @ =

interval_layer = bidict({
  0: '',
  2: '_',
  3: '-',
  4: '∆',
  5: '^',
  6: 'o',
  7: '5',
  8: '+',
  9: '6',
  10:'*',
  11:'?',
  12:'8',
  13:'<',
  14:'9',
  15:'>',
#  16:'∆',
  17:'~',
  18:'!',
#  19:'5',
  20:'@',
  21:'='
})


symbol_layers = {
  #major
  ''     : '5∆8',
  'M'    : '5∆8',
  'M7'   : '5∆?',
  'M9'   : '5∆?9',
  '6/9'  : '5∆69',
  'M11'  : '∆^8',
  'M#11' : '5∆?9!',
  'M13'  : '5∆?9=',
  # dominant
  '7'    : '5∆*',
  '9'    : '5∆*9',
  '7b9'  : '5∆*<',
  '7#9'  : '5∆*>',
  '7#11' : '5∆*9!',
  '13'   : '5∆*9=',
  '7b13' : '5∆*9@',
  # minor
  'm'    : '5-8',
  'm7'   : '5-*',
  'm9'   : '5-*9',
  'm11'  : '5-*9~',
  'mM7'  : '5-?',
  # sus4
  'sus'  : '5^',
  'sus4' : '5^',
  'M7sus': '5^?',
  'M9sus': '_5^',
  '6sus' : '5^6',
  '6/9sus': '5^69',
  '7sus' : '5^*',
  '9sus' : '5^*9',
}

"""
Single Layer Format:
10: '5' (id 10, any angle)
(11, True): 'o' (11, right side up)
(11, False): '+' (11, upside down)

Chord Quality Format
12: '5∆?' <- maps fiducial id to layers
"""

fiducial_roots = {
  20: note_midi('C', 3),
  21: note_midi('D', 3),
  22: note_midi('E', 3),
  23: note_midi('F', 3),
  24: note_midi('G', 3),
  25: note_midi('A', 2),
  26: note_midi('B', 2),
}

fiducial = {
  (5, True): '5',
  (5, False): '5',
  (50, True): 'o',
  (50, False): '+',
  (3, True): '∆',
  (3, False): '-',
  (4, True): '^',
  (4, False): '_',
  (7, True): '?',
  (7, False): '!',
  (9, True): '9',
  (9, False): '9',
  (90, True): '<',
  (90, False): '>',
  (11, True): '~',
  (11, False): '!',
  (13, True): '=',
  (13, False): '@'
}

def default_voicing(symbol: str):
  """
  Takes a list of layer symbols (values of interval_to_symbol) and creates a default closed voicing.
  In general, it will be better to use custom voicings, especially for complex chords.
  
  :param symbol: a string, where each character reflects an interval in the chord.
  """
  return [interval_layer.inv[x] for x in symbol]

def play_note(value):
  return f"noteon 0 {value} 100"

def end_note(value):
  return f"noteoff 0 {value}"

def play_chord(values):
  return '\n'.join(play_note(x) for x in values)

def stop_chord(values):
  return '\n'.join(end_note(x) for x in values)

def build_chord(voicing, root):
  return list(map(lambda v: root+v, voicing))

import socket

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 8000         # The port used by the server

def send(msg):
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

def chord(root, layers):
  return build_chord(
    [0, *default_voicing(layers)],
    int(root)
    if isinstance(root, int) or root.isnumeric()
    else note_midi(root) or 48)

def fiducial_chord(fiducial_map):
  # look for roots
  roots = list(t.filter(None, t.get(list(fiducial_map.keys()), fiducial_roots, None)))
  if len(roots) == 0: return []
  # look for layers and qualities
  layers = ''.join(set(''.join(t.filter(None, t.get([(k, not (2 <= fiducial_map[k][1] <= 5)) for k in fiducial_map], fiducial, None)))))
  if layers == '': return [roots[0]]
  return chord(roots[0], layers)

from multiprocessing import Process, Lock, Manager

def poller(notes):
  print('poller is active')
  while True:
    send(play_chord(notes))
    time.sleep(1)


def setter(notes):
  stdin = open(0)
  state = {}
  print('setter is active')
  for line in stdin:
    print('line: ', line)
    state = t.merge(state, json.loads(line, object_hook=lambda d: {int(k) if k.lstrip('-').isdigit() else k: v for k, v in d.items()}))
    print('state = ', state)
    notes[:] = fiducial_chord(state[0])
    print('notes = ', notes)


if __name__ == '__main__':
  manager = Manager()
  notes = manager.list([])
  p1 = Process(target = poller, args=(notes,))
  p2 = Process(target = setter, args=(notes,))
  p1.start()
  p2.start()
  p2.join()
