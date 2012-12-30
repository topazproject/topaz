import sys

import py
py.log.setconsumer("platform", None)

from pypy.config.translationoption import get_combined_translation_config

from rupypy.main import create_entry_point, get_topaz_config_options

sys.exit(entry_point(sys.argv))
