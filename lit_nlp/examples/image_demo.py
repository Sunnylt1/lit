"""LIT demo for image model.

To run:
  python -m lit_nlp.examples.image_demo --port=5432

Then navigate to localhost:5432 to access the demo UI.
"""

from collections.abc import Sequence
import sys
from typing import Optional

from absl import app
from absl import flags
from absl import logging
from lit_nlp import dev_server
from lit_nlp import server_flags
from lit_nlp.api import layout
from lit_nlp.components import classification_results
from lit_nlp.components import image_gradient_maps
from lit_nlp.examples.datasets import imagenette
from lit_nlp.examples.models import mobilenet


FLAGS = flags.FLAGS

FLAGS.set_default('development_demo', True)
FLAGS.set_default('warm_start', 1)
FLAGS.set_default('page_title', 'LIT Image Demo')

_MAX_EXAMPLES = flags.DEFINE_integer(
    'max_examples',
    None,
    (
        'Maximum number of examples to load into LIT. '
        'Set --max_examples=200 for a quick start.'
    ),
)


def get_wsgi_app():
  """Returns a LitApp instance for consumption by gunicorn."""
  FLAGS.set_default('server_type', 'external')
  FLAGS.set_default('demo_mode', True)
  # Parse flags without calling app.run(main), to avoid conflict with
  # gunicorn command line flags.
  unused = flags.FLAGS(sys.argv, known_only=True)
  if unused:
    logging.info('image_demo:get_wsgi_app() called with unused args: %s',
                 unused)
  return main([])

# Custom frontend layout; see api/layout.py
modules = layout.LitModuleName
DEMO_LAYOUT = layout.LitCanonicalLayout(
    upper={
        'Main': [modules.DataTableModule, modules.DatapointEditorModule],
    },
    lower={
        'Predictions': [modules.ClassificationModule, modules.ScalarModule],
        'Explanations': [
            modules.ClassificationModule,
            modules.SalienceMapModule,
        ],
    },
    description='Basic layout for image demo',
)


def main(argv: Sequence[str]) -> Optional[dev_server.LitServerType]:
  if len(argv) > 1:
    raise app.UsageError('Too many command-line arguments.')

  datasets = {'imagenette': imagenette.ImagenetteDataset()}
  # Truncate datasets if --max_examples is set.
  if _MAX_EXAMPLES.value is not None:
    for name in datasets:
      logging.info("Dataset: '%s' with %d examples", name, len(datasets[name]))
      datasets[name] = datasets[name].slice[: _MAX_EXAMPLES.value]
      logging.info('  truncated to %d examples', len(datasets[name]))

  models = {'mobilenet': mobilenet.MobileNet()}
  interpreters = {
      'classification': classification_results.ClassificationInterpreter(),
  } | image_gradient_maps.all_interpreters()

  lit_demo = dev_server.Server(
      models,
      datasets,
      interpreters=interpreters,
      generators={},
      layouts={'default': DEMO_LAYOUT},
      **server_flags.get_flags())
  return lit_demo.serve()


if __name__ == '__main__':
  app.run(main)
