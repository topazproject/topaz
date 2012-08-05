import glob
import os

from fabric.api import task, local, lcd


@task
def download_pypy():
    local("wget https://bitbucket.org/pypy/pypy/get/default.tar.bz2 -O `pwd`/../pypy.tar.bz2")
    local("bunzip2 `pwd`/../pypy.tar.bz2")
    local("tar -xf `pwd`/../pypy.tar -C `pwd`/../")
    [path_name] = glob.glob("../pypy-pypy*")
    path_name = os.path.abspath(path_name)
    with open("pypy_marker", "w") as f:
        f.write(path_name)


@task
def run_tests():
    with open("pypy_marker") as f:
        path_name = f.read()
    TEST_TYPES[os.environ["TEST_TYPE"]]({"pypy_path": path_name})


def run_own_tests(env):
    local("PYTHONPATH=%(pypy_path)s:$PYTHONPATH py.test" % env)


def run_translate_tests(env):
    local("PYTHONPATH=%(pypy_path)s:$PYTHONPATH %(pypy_path)s/pypy/translator/goal/translate.py --batch -Ojit targetrupypy.py" % env)

def run_docs_tests(env):
    with lcd("docs"):
        local("sphinx-build -W -b html")

TEST_TYPES = {
    "own": run_own_tests,
    "translate": run_translate_tests,
    "docs": run_docs_tests,
}
