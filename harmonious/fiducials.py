from harmonious.music import note_midi, chord
import toolz as t
import toolz.curried as tc

roots = {
  # individual roots - not to be used with any other chord description.
  12: note_midi('C', 3),   13: note_midi('C#', 3),  14: note_midi('D', 3),
  15: note_midi('D#', 3),  16: note_midi('E',  3),  17: note_midi('F', 3),
  18: note_midi('F#', 3),  19: note_midi('G',  3),  20: note_midi('G#', 3),
  21: note_midi('A', 2),   22: note_midi('A#', 2),  23: note_midi('B', 2),

  # Roots of main towers 1-7.
  1: note_midi("C", 3),   4: note_midi("F", 3),
  1: note_midi("C", 3),   5: note_midi("G", 3),
  2: note_midi("D", 3),   5: note_midi("G", 3),
  2: note_midi("D", 3),   6: note_midi("A", 3),
  3: note_midi("E", 3),   6: note_midi("A", 3),
  3: note_midi("E", 3),   7: note_midi("B", 3),
  4: note_midi("F", 3),   7: note_midi("B", 3),
}

layers = {
  # prebuilt chord types for diatonic chords 1-7
  (1, True):  '5∆8', (4, True):  '5∆8', (5, True):  '5∆*', (7, True): "o-8",
  (1, False): '5∆8', (4, False): '5∆8', (5, False): '5∆*', (7, False): 'o-8',
  (6, True):  '5-8', (2, True):  '5-8', (3, True):  '5-8',
  (6, False): '5-8', (2, False): '5-8', (3, False): '5-8',
  
  #individual layers to play with
  (33, True):   '∆',   (25, True):   '5',   (27, True):   '?',   (29, True):   '9',
  (33, False):  '-',   (25, False):  '5',   (27, False):  '*',   (29, False):  '9',
  (24, True):   '^',   (26, True):   'o',   (28, True):   '=',   (30, True):  '<',
  (24, False):  '_',   (26, False):  '+',   (28, False):  '@',   (30, False): '>',
  
  (31, True):  '~',
  (31, False): '!',
}

def make_fiducial_chord_builder(roots, layers):
  def fiducial_chord(fiducial_map):
    """
    
    """
    # look for roots
    # roots = t.pipe(fiducial_map, tc.keyfilter(lambda k: k in roots), lambda d: {k:(v[1])})
    r = [k for k in fiducial_map if k in roots]
    if len(r) == 0: return []
    # look for layers and qualities
    quality = t.pipe([(k, (2 <= fiducial_map[k][1] <= 5)) for k in fiducial_map],
      lambda _: t.get(_, layers, None),
      lambda _: t.filter(None, _),
      ''.join,
      set,
      ''.join)
    
    if quality == '': return [roots[r[0]]]
    return chord(roots[r[0]], quality, 2 <= fiducial_map[r[0]][1] <= 5)

  return fiducial_chord

fiducial_chord = make_fiducial_chord_builder(roots, layers)
