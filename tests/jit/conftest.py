def pytest_addoption(parser):
    group = parser.getgroup("Topaz JIT tests")
    group.addoption(
        "--topaz",
        dest="topaz",
        help="Path to a compiled topaz binary"
    )


def pytest_funcarg__topaz(request):
    return request.config.getvalueorskip("topaz")
