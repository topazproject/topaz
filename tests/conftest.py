def pytest_funcarg__space(request):
    # Inside the function so various intitialization stuff isn't seen until
    # coverage is setup.
    from rupypy.objspace import ObjectSpace

    return ObjectSpace()