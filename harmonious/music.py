"""
This file contains all music related information relevant to the Harmonious project.

Harmonious deals with chords, so all the musical information here is about
representing, constructing, and voicing chords. There is no information about
melody (key signatures, scale degrees, etc) or rhythm (mapping musical time to real time).

There are lots of libraries that deal with this information, but none that
use a representation compatible with the towers/pieces we have available in
Harmonious. Normally chords are constructed in the context of a key, so
1,3,5 are mapped to a distinct idea.
Since harmonious uses absolute intervals, we need a separate
system to denote m3 vs ∆3, and all the other ambiguous intervals.
It's preferrable to have a system where each interval type is represented by a
single character to avoid complex parsing logic in every single portion of the
code, and to avoid complex cases like 'C###bbb'.

Some chord symbols are also non-distinct in the harmonious case. For example,
13/b13 chords imply a 9 and 11, but in Harmonious, it's possible to specify
adding a "13" without adding a 9 or an 11, which leads to a few custom mappings
between 'layers' or 'interval stacks' and the chord they represent and the voicing
that is used. For example, 15∆= (= means a 13) is a major chord with an added 6th,
not a 13th.

See :player: for details about how the chords are played.
Progressions are just represented as an array of notes that are to be played
in sequence there.
"""
from aenum import Enum, unique, IntEnum
from bidict import bidict
import sys
import regex as re
import toolz as t
from typing import List, Iterable, Union, Mapping

"""
Simple mapping of note name to MIDI value mod 12.
MIDI 0th octave begins at 12 + this value. (so C0 = 12, A0 = 21, etc)
"""
NoteValue : 'NoteValue' = IntEnum('NoteValue', {
  # note, this order is NOT random
  # raw note names are preferred to enharmonic equivalents
  # flats are preferrable to sharps (jazz musician here)
  'C': 0,  'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11,
  'Db':1,  'Gb':6, 'Ab':8, 'Bb':10, 'Eb': 3,
  'C#':1, 'D#':3, 'G#':8, 'A#':10,  'F#': 6,
  # these are just weird, so they exist only as aliases for B/C E/F respectively.
  'Fb':4,'E#':5,'B#':12, 'Cb':11
})


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
LayerInterval : 'LayerInterval' = IntEnum('LayerInterval', {
  '1': 0,
  '_': 2, '-': 3, '∆': 4, '^': 5, # ∆ is not ascii, but it's from music theory, so it's allowed
  'o': 6, '5': 7, '+': 8,
  '6': 9,
  '*': 10, '?': 11, # could have used 7 for * but it's not clear what maj7 would be
  '8': 12,
  '<': 13, '9': 14, '>': 15, #do we need to distinguish 9 from _? It's a helpful mnemonic for me, but not necessary.
  # These pieces are distinguished from 4/b5 because they serve a separate harmonic function
  # We want students to think about 11/#11 differently than 4/2 sus or b5/#5 .
  '~': 17, '!': 18,
  # TODO consider better symbol options for 13/b13.
  '@': 20, '=': 21, # same question for 13/b13 and 6/+.
})


"""
Maps some common chord names to layer stacks for easy testing of synths.

There are 2**16 = 65536 possible towers. (10 towers, 6 flippable)
There are ~60,000 towers with > 3 pieces
There are (1 x 3 x 4 x 3 x 4 x 3 x 3) = 1296 towers with maximum 1 sound/layer
Maybe 40 of those are listed here.
"""
symbol_layers : Mapping[str, str] = {
  #major                  # dominant               # minor
  ''     : '5∆8',         '7'    : '5∆*',          'm'    : '5-8',
  'M'    : '5∆8',         '9'    : '5∆*9',         'm7'   : '5-*',
  'M6'   : '5∆6',         '7b9'  : '5∆*<',         'm6'   : '5-6',
  'M7'   : '5∆?',         '7#9'  : '5∆*>',         'm9'   : '5-*9',
  'M9'   : '5∆?9',        '7#11' : '5∆*9!',        'm6/9' : '5-69',
  '6/9'  : '5∆69',        '13'   : '5∆*9=',        'm11'  : '5-*9~',
  'M11'  : '∆^8',         '7b13' : '5∆*9@',        'm#11' : '5-*9!',
  'M#11' : '5∆?9!',                                'mM7'  : '5-?',
  'M13'  : '5∆?9=',
  
  # sus4                  # sus4
  'sus'  : '5^8',         'sus'  : '5^8',
  'sus4' : '5^8',         'sus4' : '5^8',
  'M7sus': '5^?',         'M7sus': '5^?',
  'M9sus': '5^9',         'M9sus': '5^9',
  '6sus' : '5^6',         '6sus' : '5^6',
  '6/9sus': '5^69',       '6/9sus': '5^69',
  '7sus' : '5^*',         '7sus' : '5^*',
  '9sus' : '5^*9',        '9sus' : '5^*9',
  
  # diminished            #augmented
  'o'    : 'o-8',         '+'    : '+∆8',
  'o7'   : 'o-6',         '+7'   : '+∆*',
  'om7'  : 'o-*',         '+9'   : '+∆*9',
  'oM'   : 'o∆',          '+b9'  : '+∆*<',
  'o9'   : 'o∆*9',        '+m'   : '+-8',
  'ob9'  : 'o∆*<',        '++'   : '+∆*9!'
}

layers_voicings : Mapping[str, Mapping[str, Union[str, List[Union[str, int]]]]] = {
  '5∆8' : {'default': '151351', 'closed': '1351', 'jazzy': '1513'},
  '5∆?' : '15?351',
  '5∆69' : '1561∆59',
  '5-69' : [1, 5, 6, 1, '-', 5, 9],
}



def note_midi(note: str, octave: int = None) -> int:
  """
  Returns absolute midi value of a note specified as pitch+octave, eg: A3
  
  Values are specified by the MIDI spec.
  
  >>> note_midi('C3')
  48
  >>> note_midi('Cb4')
  71
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
    return NoteValue[note] + 12*(octave+1)
  elif re.match('[A-G][#b]?[0-6]', note):
    return NoteValue[note[:-1]] + 12*(int(note[-1]) + 1)
  else:
    return None


def normalize_layers(layers: Union[str, List[LayerInterval]]) -> str:
  """
  Convert the representation of the layers into a sorted string format for looking up voicings.
  
  Rotation is meaningless when using layers, so ∆58 = 8∆5. This function maps
  both to a consistent sorted order of 5∆8 (in order of layer placement on the mat).
  
  Duplication of symbols is also meaningless (we don't have a concept of doubling voices),
  so that is removed as well.
  
  Finally, roots aren't necessary because every chord implicitly has a root, so that
  is removed too.
  
  >>> normalize_layers('∆58')
  '5∆8'
  >>> normalize_layers('8∆5')
  '5∆8'
  >>> normalize_layers('9!∆5_')
  '5_∆9!'
  >>> normalize_layers('9o5+*')
  'o5+*9'
  """
  #first, make a consistent format (str, because the rest is a mess)
  base = (set(LayerInterval(x) for x in layers)
          if not isinstance(layers, str)
          else set(LayerInterval[x] for x in layers))
  #strategy - remove the 1/5, sort the rest, append the 5 in front.
  base.discard(0)
  [has6, has7, has8] = [LayerInterval(x) in base for x in (6,7,8)]
  for x in range(6, 8+1):
    base.discard(x)
  
  return (
    (LayerInterval(6).name if has6 else '') +
    (LayerInterval(7).name if has7 else '') +
    (LayerInterval(8).name if has8 else '') +
    ''.join(x.name for x in sorted(base))
  )
  


def tone_to_voicing(tones: Iterable[Union[int, str]]) -> List[int]:
  """
  Converts a stack of chord tones into a voicing with absolute intervals.
  
  Thinking of voicings as a stack of absolute intervals is difficult -
  is it 24? 25? oh wait, 26 for a 9 an octave higher.
  Musicians tend to think of voicings in chord tones, which are
  normally expressed as a scale degree.
  
  In this system, 'scale degree' is expressed as a 'layer symbol'.
  
  Using this function, it's possible to write a voicing as a series of
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
  for tone in t.get(list(map(str, tones)), LayerInterval):
    if len(l) == 0 or tone > l[-1]:
      l.append(int(tone))
    else:
      l.append( (1+(l[-1] - tone)//12)*12 + tone )
  return l


def default_voicing(layers: str):
  """
  Takes a list of layer symbols (values of interval_to_symbol) and creates a default closed voicing.
  In general, it will be better to use custom voicings, especially for complex chords.
  
  :param symbol: a string, where each character reflects an interval in the chord.
  
  >>> list(map(int, default_voicing('1∆5')))
  [0, 4, 7]
  """
  return [LayerInterval[x] for x in layers]

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
