from harmonious.music import note_midi, chord
import toolz as t
import toolz.curried as tc

roots = {
  24: note_midi('C', 3),   25: note_midi('C#', 3),  26: note_midi('D', 3),
  27: note_midi('D#', 3),  28: note_midi('E', 3),   29: note_midi('F', 3),
  30: note_midi('F#', 3),  31: note_midi('G', 3),   32: note_midi('G#', 3),
  33: note_midi('A', 2),   34: note_midi('A#', 2),  35: note_midi('B', 2),
}

layers = {
  # prebuilt chord types for diatonic chords
  (0, True):   '5∆8',   (1, True):   '5-8',   (2, True):   '5∆*',
  (0, False):  '5∆8',   (1, False):  '5-8',   (2, False):  '5∆*',
  # prebuilt chord types for diatonic chords
  (50, True):   '5∆8',   (51, True):   '5-8',   (52, True):   '5∆*',
  (50, False):  '5∆8',   (51, False):  '5-8',   (52, False):  '5∆*',
  # prebuilt chord types for diatonic chords
  (53, True):   '5∆8',   (54, True):   '5-8',   (55, True):   '5∆*',
  (53, False):  '5∆8',   (54, False):  '5-8',   (55, False):  '5∆*',
  
  #individual layers to play with
  (3, True):   '∆',   (5, True):   '5',   (7, True):   '?',  (9, True):   '9',
  (3, False):  '-',   (5, False):  '5',   (7, False):  '*',  (9, False):  '9',
  (4, True):   '^',   (6, True):   'o',   (8, True):  '=',   (10, True):  '<',
  (4, False):  '_',   (6, False):  '+',   (8, False): '@',   (10, False): '>',

  (11, True):  '~',
  (11, False): '!',


  #individual layers to play with - second copy because not enough fiducials printed
  (73, True):   '∆',   (75, True):   '5',   (77, True):   '?',  (79, True):   '9',
  (73, False):  '-',   (75, False):  '5',   (77, False):  '*',  (79, False):  '9',
  (74, True):   '^',   (76, True):   'o',   (78, True):  '=',   (80, True):  '<',
  (74, False):  '_',   (76, False):  '+',   (78, False): '@',   (80, False): '>',

  (81, True):  '~',
  (81, False): '!',
}

def fiducial_chord(fiducial_map):
  # look for roots
  # roots = t.pipe(fiducial_map, tc.keyfilter(lambda k: k in roots), lambda d: {k:(v[1])})
  r = list(t.filter(None, t.get(list(fiducial_map.keys()), roots, None)))
  if len(r) == 0: return []
  # look for layers and qualities
  quality = t.pipe([(k, (2 <= fiducial_map[k][1] <= 5)) for k in fiducial_map],
    lambda _: t.get(_, layers, None),
    lambda _: t.filter(None, _),
    ''.join,
    set,
    ''.join)
  
  if quality == '': return [r[0]]
  return chord(r[0], quality)
