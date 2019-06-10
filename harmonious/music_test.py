from hypothesis import given
import hypothesis.strategies as st
from harmonious.music import LayerInterval, note_midi, normalize_layers, tone_to_voicing


# notes an octave apart should normalize to the same value when mod by 12.
@given(st.text(alphabet='ABCDEFG', min_size=1, max_size=1),
       st.one_of(st.just(''), st.text(alphabet=('b', '#'), min_size=1, max_size=1)),
       st.integers(min_value=0, max_value=8))
def test_note_midi_octaves_correct(letter, accidental, octave):
  assert note_midi(letter + accidental, -1) == note_midi(letter+accidental, octave) % 12


#rotating the input should not change the output
@given(st.text(alphabet=[x.name for x in LayerInterval]), st.integers(min_value=1))
def test_normalize_layers_rotation(layers, rotation):
  assert normalize_layers(layers) == normalize_layers(layers[rotation:] + layers[:rotation])


# without a 5, this function degenerates to sorting by value
@given(st.text(alphabet=[x.name for x in LayerInterval if x < 6 and x > 8]))
def test_normalize_layers_without_5_is_sorted(layers):
  assert normalize_layers(layers) == ''.join(sorted(layers))


# the three 5s should normalize to a consistent order
@given(st.text(alphabet='5o+'))
def test_normalize_layers_5s_only(layers):
  if '5' not in layers:
    assert normalize_layers(layers) in 'o+'
  else:
    assert normalize_layers(layers) in 'o5+'


# with a 5, o, or +, and a bunch of other stuff, the 5, o, or + comes first.
@given(st.text(alphabet=[x.name for x in LayerInterval if x < 6 and x > 8]))
def test_normalize_layers_with_5(layers):
  assert normalize_layers(layers+'5') == '5'+''.join(sorted(layers))
  assert normalize_layers(layers+'o') == 'o'+''.join(sorted(layers))
  assert normalize_layers(layers+'+') == '+'+''.join(sorted(layers))


@given(st.text(alphabet=[x.name for x in LayerInterval]))
def test_tone_to_voicing_monotonic(tones):
  voicing = tone_to_voicing(tones)
  for i in range(len(voicing)-1):
    assert voicing[i] < voicing[i+1]


@given(st.integers(min_value = 2, max_value=11), st.integers(min_value = 2, max_value = 11))
def test_tone_to_voicing_octave_bumps_up_values(left, right):
  low, high = (LayerInterval(left), LayerInterval(right)) if left < right else (LayerInterval(right) , LayerInterval(left))
  assert tone_to_voicing([low, high])[-1] + (12 if left != right else 0) == tone_to_voicing([low, '1', high])[-1]
  
