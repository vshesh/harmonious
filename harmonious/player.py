from bidict import bidict
import sys
import regex as re
import toolz as t
import simplejson as json
import time
from typing import List, Iterable, Union
from pythonosc import udp_client


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
  """
  Returns absolute midi value of a note specified as pitch+octave, eg: A3
  
  >>> note_midi('C3')
  48
  >>> note_midi('C4')
  60
  >>> note_midi('C', 3)
  48
  >>> note_midi('C', 4)
  60
  >>> note_midi('A2')
  45
  >>> note_midi('A0')
  21
  """
  if octave is not None:
    return note_value[note] + 12*(octave+1)
  elif re.match('[A-G][#b]?[0-6]', note):
    return note_value[note[:-1]] + 12*(int(note[-1]) + 1)
  else:
    return None

"""
chord naming scheme
unlike regular chord names which are deviations from a major chord,
these are based on 'layer' presence or absences

1 - blank
5 (b5 #5)   5 o +
b3 3 (2 4)  - ∆ 2 4
b7 7        * !
9 (b9 #9)   9 < >
11 #11      ~ ?
b13 13      @ =
"""
interval_layer = bidict({
  0: '1',
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
  'M6'   : '5∆6',
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
  'm6'   : '5-6',
  'm9'   : '5-*9',
  'm6/9' : '5-69',
  'm11'  : '5-*9~',
  'm#11' : '5-*9!',
  'mM7'  : '4.9?',
  # sus4
  'sus2' : '5_8',
  'sus'  : '5^8',
  'sus4' : '5^8',
  'M7sus': '5^?',
  'M9sus': '5^9',
  '6sus' : '5^6',
  '6/9sus': '5^69',
  '7sus' : '5^*',
  '9sus' : '5^*9',
  # diminished
  'o'    : 'o-8',
  'o7'   : 'o-6',
  'om7'  : 'o-*',
  'oM'   : 'o∆',
  'o9'   : 'o∆*9',
  'ob9'  : 'o∆*<',
  #augmented
  '+'    : '+∆8',
  '+7'   : '+∆*',
  '+9'   : '+∆*9',
  '+b9'  : '+∆*<',
  '+m'   : '+-8',
  '++'   : '+∆*9!'
}

def tone_to_voicing(tones: Iterable[Union[int, str]]) -> List[int]:
  """
  Converts a stack of chord tones into a voicing with absolute intervals.
  
  Thinking of voicings as a stack of absolute intervals is difficult -
  is it 24? 25? oh wait, 26 for a 9 an octave higher.
  Musicians tend to think of voicings in chord tones, which are themeselves
  normally expressed as a scale degreeself.
  
  In this system, 'scale degree' is expressed as a 'layer symbol'.
  Rather than think about b3 vs 3, we have single character names for the
  ease of parsing/programming around them.
  
  So, using this function, it's possible to write a voicing as a series of
  chord tones in scale degrees as normal, and to convert that to what the
  computer needs, which is a list of
  
  >>> tone_to_voicing([1, 5, 6, 1, '∆', 5, 9])
  [0, 7, 9, 12, 16, 19, 26]
  >>> tone_to_voicing('1561∆5_')
  [0, 7, 9, 12, 16, 19, 26]
  >>> tone_to_voicing([1, '*', '∆', '='])
  [0, 10, 16, 21]
  
  :param tones: a list of numbers or symbols corresponding to layer symbols (values of interval_layer).
  :return: a list of absolute voicings that can be used by :build_chord:.
  """
  l = []
  for tone in t.get(list(map(str, tones)), interval_layer.inv):
    if len(l) == 0 or tone > l[-1]:
      l.append(tone)
    else:
      l.append( (1+(l[-1] - tone)//12)*12 + tone )
  return l

layers_voicings = {
  '5∆8' : {'default': '151351', 'closed': '1351', 'jazzy': '1513'},
  '5∆?' : '15?351',
  # '5∆?9' : ,
  '5∆69' : '1561∆59',
  # '∆^8' : ,
  # '5∆?9!' : ,
  # '5∆?9=' : ,
  # '5∆*' : ,
  # '5∆*9' : ,
  # '5∆*<' : ,
  # '5∆*>' : ,
  # '5∆*9!' : ,
  # '5∆*9=' : ,
  # '5∆*9@' : ,
  # '5-8' : ,
  # '5-*' : ,
  # '5-*9' : ,
  '5-69' : [1, 5, 6, 1, '-', 5, 9],
  # '5-*9~' : ,
  # '5-*9!' : ,
  # '4.9?' : ,
  # '5_8' : ,
  # '5^8' : ,
  # '5^8' : ,
  # '5^?' : ,
  # '5^9' : ,
  # '5^6' : ,
  #  '5^69' : ,
  # '5^*' : ,
  # '5^*9' : ,
  # 'o-8' : ,
  # 'o-6' : ,
  # 'o-*' : ,
  # 'o∆' : ,
  # 'o∆*9' : ,
  # 'o∆*<' : ,
  # '+∆8' : ,
  # '+∆*' : ,
  # '+∆*9' : ,
  # '+∆*<' : ,
  # '+-8' : ,
  # '+∆*9! : '
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
  24: note_midi('C', 3),
  25: note_midi('C#', 3),
  26: note_midi('D', 3),
  27: note_midi('D#', 3),
  
  28: note_midi('E', 3),
  29: note_midi('F', 3),
  30: note_midi('F#', 3),
  31: note_midi('G', 3),
  
  32: note_midi('G#', 2),
  33: note_midi('A', 2),
  34: note_midi('A#', 2),
  35: note_midi('B', 2),
}

fiducial = {
  # prebuilt chord types
  (0, True):   '5∆8',
  (0, False):  '5∆8',
  (1, True):   '5-8',
  (1, False):  '5-8',
  (2, True):   '5∆*',
  (2, False):  '5∆*',
  
  #individual layers to play with
  (3, True):   '∆',
  (3, False):  '-',
  (4, True):   '^',
  (4, False):  '_',

  (5, True):   '5',
  (5, False):  '5',
  (6, True):   'o',
  (6, False):  '+',

  (7, True):   '?',
  (7, False):  '!',

  (8, True):  '=',
  (8, False): '@',
  (9, True):   '9',
  (9, False):  '9',
  (10, True):  '<',
  (10, False): '>',
  (11, True):  '~',
  (11, False): '!',
}

def default_voicing(layers: str):
  """
  Takes a list of layer symbols (values of interval_to_symbol) and creates a default closed voicing.
  In general, it will be better to use custom voicings, especially for complex chords.
  
  :param symbol: a string, where each character reflects an interval in the chord.
  """
  return [interval_layer.inv[x] for x in layers]

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

def chord(root, layers):
  return build_chord(
    [0, *default_voicing(layers)],
    int(root)
    if isinstance(root, int) or root.isnumeric()
    else note_midi(root) or 48)

def symbol_chord(root, symbol):
  return chord(root, symbol_layers.get(symbol, '5∆8'))

def fiducial_chord(fiducial_map):
  # look for roots
  roots = list(t.filter(None, t.get(list(fiducial_map.keys()), fiducial_roots, None)))
  if len(roots) == 0: return []
  # look for layers and qualities
  layers = ''.join(set(''.join(t.filter(None, t.get([(k, not (2 <= fiducial_map[k][1] <= 5)) for k in fiducial_map], fiducial, None)))))
  if layers == '': return [roots[0]]
  return chord(roots[0], layers)



from multiprocessing import Process, Lock, Manager
import socket

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 8000         # The port used by the server

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


oscsender = udp_client.SimpleUDPClient('127.0.0.1', 3334)


def bar(notes):
  for i in range(2):
    try:
      send(HOST, PORT, play_chord(notes))
    finally:
      time.sleep(1.5)


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
    state = t.merge(state, json.loads(line, object_hook=lambda d: {int(k) if k.lstrip('-').isdigit() else k: v for k, v in d.items()}))
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
