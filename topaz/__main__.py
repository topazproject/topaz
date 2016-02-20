import sys

import py
# This must be run before we import from RPython, otherwise logs spew out
py.log.setconsumer("platform", None)  # noqa

from rpython.config.translationoption import get_combined_translation_config

from topaz.main import create_entry_point, get_topaz_config_options


entry_point = create_entry_point(get_combined_translation_config(
    overrides=get_topaz_config_options(),
))
sys.exit(entry_point(sys.argv))
