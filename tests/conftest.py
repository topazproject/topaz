import copy

from rpython.config.translationoption import get_combined_translation_config


def pytest_funcarg__space(request):
    # Inside the function so various intitialization stuff isn't seen until
    # coverage is setup.
    from topaz.main import get_topaz_config_options
    from topaz.objspace import ObjectSpace

    # Building a space is exceptionally expensive, so we create one once, and
    # then just deepcopy it.  Note that deepcopying is still fairly expensive
    # (at the time of writing about 1/3 of total test time), but significantly
    # less so than building a new space.
    space = request.cached_setup(
        setup=lambda: ObjectSpace(get_combined_translation_config(
            overrides=get_topaz_config_options(),
        )),
        scope="session",
    )
    return copy.deepcopy(space)
