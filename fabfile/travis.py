import glob
import os

from fabric.api import task, local


class Test(object):
    def __init__(self, func, deps=[], needs_pypy=True):
        self.func = func
        self.deps = deps
        self.needs_pypy = needs_pypy

    def install_deps(self):
        local("pip install {}".format(" ".join(self.deps)))

    def download_pypy(self):
        local("wget https://bitbucket.org/pypy/pypy/get/default.tar.bz2 -O `pwd`/../pypy.tar.bz2")
        local("bunzip2 `pwd`/../pypy.tar.bz2")
        local("tar -xf `pwd`/../pypy.tar -C `pwd`/../")
        [path_name] = glob.glob("../pypy-pypy*")
        path_name = os.path.abspath(path_name)
        with open("pypy_marker", "w") as f:
            f.write(path_name)

    def run_tests(self):
        env = {}
        if self.needs_pypy:
            with open("pypy_marker") as f:
                env["pypy_path"] = f.read()
        self.func(env)


@task
def install_requirements():
    t = TEST_TYPES[os.environ["TEST_TYPE"]]
    if t.deps:
        t.install_deps()
    if t.needs_pypy:
        t.download_pypy()


@task
def run_tests():
    t = TEST_TYPES[os.environ["TEST_TYPE"]]
    t.run_tests()


def run_own_tests(env):
    local("PYTHONPATH={pypy_path}:$PYTHONPATH py.test".format(**env))


def run_translate_tests(env):
    local("PYTHONPATH={pypy_path}:$PYTHONPATH {pypy_path}/pypy/translator/goal/translate.py --batch -Ojit targetrupypy.py".format(**env))


def run_docs_tests(env):
    local("sphinx-build -W -b html docs/ docs/_build/")

TEST_TYPES = {
    "own": Test(run_own_tests, deps=["pytest"]),
    "translate": Test(run_translate_tests),
    "docs": Test(run_docs_tests, deps=["sphinx"], needs_pypy=False),
}
