import sys

import py
py.log.setconsumer("platform", None)

from rpython.config.translationoption import get_combined_translation_config

from topaz.main import create_entry_point, get_topaz_config_options


entry_point = create_entry_point(get_combined_translation_config(
    overrides=get_topaz_config_options(),
))
sys.exit(entry_point(sys.argv))
