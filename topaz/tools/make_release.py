import os
import sys
import tarfile


PROJECT_ROOT = os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir)


def main(argv):
    target = argv[0]
    t = tarfile.open(target, mode="w:bz2")
    for name in [
        "bin/topaz.exe" if sys.platform == "win32" else "bin/topaz",
        "lib-ruby",
        "lib-topaz",
        "AUTHORS.rst",
        "LICENSE",
        "README.rst"
    ]:
        t.add(os.path.join(PROJECT_ROOT, name), arcname="topaz/%s" % name)
    t.add(
        os.path.join(PROJECT_ROOT, "docs"), "topaz/docs",
        filter=lambda info: info if "_build" not in info.name else None
    )
    t.close()


if __name__ == "__main__":
    main(sys.argv[1:])
