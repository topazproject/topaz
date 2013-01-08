import copy


def pytest_funcarg__space(request):
    # Inside the function so various intitialization stuff isn't seen until
    # coverage is setup.
    from topaz.objspace import ObjectSpace

    # Building a space is exceptionally expensive, so we create one once, and
    # then just deepcopy it.  Note that deepcopying is still fairly expensive
    # (at the time of writing about 1/3 of total test time), but significantly
    # less so than building a new space.
    space = request.cached_setup(
        setup=ObjectSpace,
        scope="session",
    )
    return copy.deepcopy(space)
