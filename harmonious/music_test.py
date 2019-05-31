from hypothesis import given
import hypothesis.strategies as st
from harmonious.music import LayerInterval, normalize_layers

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
