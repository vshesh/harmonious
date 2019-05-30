from harmonious.music import note_midi, chord

roots = {
  24: note_midi('C', 3),   25: note_midi('C#', 3),  26: note_midi('D', 3),
  27: note_midi('D#', 3),  28: note_midi('E', 3),   29: note_midi('F', 3),
  30: note_midi('F#', 3),  31: note_midi('G', 3),   32: note_midi('G#', 3),
  33: note_midi('A', 2),   34: note_midi('A#', 2),  35: note_midi('B', 2),
}

layers = {
  # prebuilt chord types for diatonic chords
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
  (7, False):  '*',

  (8, True):  '=',
  (8, False): '@',
  (9, True):   '9',
  (9, False):  '9',
  (10, True):  '<',
  (10, False): '>',
  (11, True):  '~',
  (11, False): '!',
}

def fiducial_chord(fiducial_map):
  # look for roots
  roots = list(t.filter(None, t.get(list(fiducial_map.keys()), roots, None)))
  if len(roots) == 0: return []
  # look for layers and qualities
  quality = ''.join(set(''.join(t.filter(None, t.get([(k, not (2 <= fiducial_map[k][1] <= 5)) for k in fiducial_map], layers, None)))))
  if quality == '': return [roots[0]]
  return chord(roots[0], layers)
