import py


def pytest_addoption(parser):
    group = parser.getgroup("Topaz JIT tests")
    group.addoption(
        "--topaz",
        dest="topaz",
        default=None,
        help="Path to a compiled topaz binary"
    )


def pytest_funcarg__topaz(request):
    return py.path.local(request.config.getvalueorskip("topaz"))
