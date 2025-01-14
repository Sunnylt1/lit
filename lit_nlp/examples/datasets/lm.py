"""Language modeling datasets."""

import glob
from typing import Optional

from lit_nlp.api import dataset as lit_dataset
from lit_nlp.api import types as lit_types
import tensorflow_datasets as tfds


class PlaintextSents(lit_dataset.Dataset):
  """Load sentences from a flat text file."""

  def __init__(
      self,
      path_or_glob: str,
      skiplines: int = 0,
      max_examples: Optional[int] = None,
  ):
    self._examples = self.load_datapoints(path_or_glob, skiplines=skiplines)[
        :max_examples
    ]

  @classmethod
  def init_spec(cls) -> lit_types.Spec:
    default_path = ''

    return {
        'path_or_glob': lit_types.String(
            default=default_path, required=False
        ),
        'skiplines': lit_types.Integer(default=0, max_val=25),
        'max_examples': lit_types.Integer(
            default=1000, min_val=0, max_val=10_000, required=False
        ),
    }

  def load_datapoints(self, path_or_glob: str, skiplines: int = 0):
    examples = []
    for path in glob.glob(path_or_glob):
      with open(path) as fd:
        for i, line in enumerate(fd):
          if i < skiplines:  # skip header lines, if necessary
            continue
          line = line.strip()
          if line:  # skip blank lines, these are usually document breaks
            examples.append({'text': line})
    return examples

  def load(self, path: str):
    return lit_dataset.Dataset(base=self, examples=self.load_datapoints(path))

  def spec(self) -> lit_types.Spec:
    """Should match MLM's input_spec()."""
    return {'text': lit_types.TextSegment()}


class BillionWordBenchmark(lit_dataset.Dataset):
  """Billion Word Benchmark (lm1b); see http://www.statmt.org/lm-benchmark/."""

  AVAILABLE_SPLITS = ['test', 'train']

  def __init__(self, split: str = 'train', max_examples: Optional[int] = None):
    ds = tfds.load('lm1b', split=split)
    if max_examples is not None:
      # Normally we can just slice the resulting dataset, but lm1b is very large
      # so we can use ds.take() to only load a portion of it.
      ds = ds.take(max_examples)
    raw_examples = list(tfds.as_numpy(ds))
    self._examples = [{
        'text': ex['text'].decode('utf-8')
    } for ex in raw_examples]

  @classmethod
  def init_spec(cls) -> lit_types.Spec:
    return {
        'split': lit_types.CategoryLabel(vocab=cls.AVAILABLE_SPLITS),
        'max_examples': lit_types.Integer(
            default=1000, min_val=0, max_val=10_000, required=False
        ),
    }

  def spec(self) -> lit_types.Spec:
    return {'text': lit_types.TextSegment()}
