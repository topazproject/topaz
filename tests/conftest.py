import copy

from rpython.config.translationoption import get_combined_translation_config


def pytest_funcarg__space(request):
    # Inside the function so various initialization stuff isn't seen until
    # coverage is setup.
    import topaz
    from topaz.main import get_topaz_config_options
    from topaz.objspace import ObjectSpace

    # Building a space is exceptionally expensive, so we create one once, and
    # then just deepcopy it.  Note that deepcopying is still fairly expensive
    # (at the time of writing about 1/3 of total test time), but significantly
    # less so than building a new space.
    def build_space():
        space = ObjectSpace(get_combined_translation_config(
            overrides=get_topaz_config_options(),
        ))
        space.setup(topaz.__file__)
        return space

    space = request.cached_setup(
        setup=build_space,
        scope="session",
    )
    return copy.deepcopy(space)
