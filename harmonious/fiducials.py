from harmonious.music import note_midi, chord
import toolz as t
import toolz.curried as tc

roots = {
  # individual roots - not to be used with any other chord description.
  24: note_midi('C', 3),   25: note_midi('C#', 3),  26: note_midi('D', 3),
  27: note_midi('D#', 3),  28: note_midi('E', 3),   29: note_midi('F', 3),
  30: note_midi('F#', 3),  31: note_midi('G', 3),   32: note_midi('G#', 3),
  33: note_midi('A', 2),   34: note_midi('A#', 2),  35: note_midi('B', 2),

  # Roots of main towers 1-7.
  (1, True):  note_midi("C", 3),   (4, False): note_midi("F", 3),
  (1, False): note_midi("C", 3),   (5, True):  note_midi("G", 3),
  (2, True):  note_midi("D", 3),   (5, False): note_midi("G", 3),
  (2, False): note_midi("D", 3),   (6, True):  note_midi("A", 3),
  (3, True):  note_midi("E", 3),   (6, False): note_midi("A", 3),
  (3, False): note_midi("E", 3),   (7, True):  note_midi("B", 3),
  (4, True):  note_midi("F", 3),   (7, False): note_midi("B", 3),
}

layers = {
  # prebuilt chord types for diatonic chords 1-7
  (1, True):  '5∆8', (4, True):  '5∆8', (5, True):  '5∆*', (7, True): "o-8",
  (1, False): '5∆8', (4, False): '5∆8', (5, False): '5∆*', (7, False): 'o-8',
  (6, True):  '5-8', (2, True):  '5-8', (3, True):  '5-8',
  (6, False): '5-8', (2, False): '5-8', (3, False): '5-8',
  
  
  #individual layers to play with
  (43, True):   '∆',   (45, True):   '5',   (47, True):   '?',   (49, True):   '9',
  (43, False):  '-',   (45, False):  '5',   (47, False):  '*',   (49, False):  '9',
  (44, True):   '^',   (46, True):   'o',   (48, True):   '=',   (50, True):  '<',
  (44, False):  '_',   (46, False):  '+',   (48, False):  '@',   (50, False): '>',
  
  (51, True):  '~',
  (51, False): '!',
  
  #individual layers to play with - second copy because not enough fiducials printed
  (53, True):   '∆',   (55, True):   '5',   (57, True):   '?',   (59, True):   '9',
  (53, False):  '-',   (55, False):  '5',   (57, False):  '*',   (59, False):  '9',
  (54, True):   '^',   (56, True):   'o',   (58, True):   '=',   (60, True):  '<',
  (54, False):  '_',   (56, False):  '+',   (58, False):  '@',   (60, False): '>',
  
  (61, True):  '~',
  (61, False): '!',
  
  #individual layers to play with - second copy because not enough fiducials printed
  (63, True):   '∆',   (65, True):   '5',   (67, True):   '?',   (69, True):   '9',
  (63, False):  '-',   (65, False):  '5',   (67, False):  '*',   (69, False):  '9',
  (64, True):   '^',   (66, True):   'o',   (68, True):   '=',   (70, True):   '<',
  (64, False):  '_',   (66, False):  '+',   (68, False):  '@',   (70, False):  '>',
  
  (71, True):  '~',
  (71, False): '!',

  # can keep going and adding more copies if you want...
}

def make_fiducial_chord_builder(roots, layers):
  def fiducial_chord(fiducial_map):
    """
    
    """
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

  return fiducial_chord

fiducial_chord = make_fiducial_chord_builder(roots, layers)
