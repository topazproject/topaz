import glob
import os

from fabric.api import task, local
from fabric.context_managers import lcd


class Test(object):
    def __init__(self, func, deps=[], needs_pypy=True, needs_rubyspec=False):
        self.func = func
        self.deps = deps
        self.needs_pypy = needs_pypy
        self.needs_rubyspec = needs_rubyspec

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

    def download_mspec(self):
        with lcd(".."):
            local("git clone --depth=100 --quiet https://github.com/rubyspec/mspec")

    def download_rubyspec(self):
        with lcd(".."):
            local("git clone --depth=100 --quiet https://github.com/rubyspec/rubyspec")

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
    if t.needs_rubyspec:
        t.download_mspec()
        t.download_rubyspec()


@task
def run_tests():
    t = TEST_TYPES[os.environ["TEST_TYPE"]]
    t.run_tests()


def run_own_tests(env):
    local("PYTHONPATH=$PYTHONPATH:{pypy_path} py.test".format(**env))


def run_translate_tests(env):
    # TODO: this list is temporary until we have all the machinery necessary to
    # run the full rubyspec directory (including the tagging feature)
    rubyspec_tests = [
        "language/and_spec.rb",
        "language/not_spec.rb",
        "language/order_spec.rb",
        "language/unless_spec.rb",

        "core/false/and_spec.rb",
        "core/false/inspect_spec.rb",
        "core/false/or_spec.rb",
        "core/false/to_s_spec.rb",
        "core/false/xor_spec.rb",

        "core/fixnum/comparison_spec.rb",
        "core/fixnum/even_spec.rb",
        "core/fixnum/hash_spec.rb",
        "core/fixnum/odd_spec.rb",
        "core/fixnum/to_f_spec.rb",
        "core/fixnum/zero_spec.rb",

        "core/true/and_spec.rb",
        "core/true/inspect_spec.rb",
        "core/true/or_spec.rb",
        "core/true/to_s_spec.rb",
        "core/true/xor_spec.rb",
    ]
    local("PYTHONPATH={pypy_path}:$PYTHONPATH python {pypy_path}/pypy/translator/goal/translate.py --batch -Ojit targetrupypy.py".format(**env))
    spec_files = " ".join(os.path.join("../rubyspec", p) for p in rubyspec_tests)
    # TODO: this should be reenabled after we can run mspec unmodified (right
    # now it requires two small patches)
    # local("../mspec/bin/mspec -t `pwd`/topaz-c {spec_files}".format(spec_files=spec_files))


def run_docs_tests(env):
    local("sphinx-build -W -b html docs/ docs/_build/")

RPLY_URL = "-e git+https://github.com/alex/rply#egg=rply"

TEST_TYPES = {
    "own": Test(run_own_tests, deps=["pytest", RPLY_URL]),
    "translate": Test(run_translate_tests, deps=[RPLY_URL], needs_rubyspec=True),
    "docs": Test(run_docs_tests, deps=["sphinx"], needs_pypy=False),
}
