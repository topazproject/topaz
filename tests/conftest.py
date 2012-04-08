from rupypy.objspace import ObjectSpace


def pytest_funcarg__space(request):
    return ObjectSpace()