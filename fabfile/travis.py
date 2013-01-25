import glob
import os

from fabric.api import task, local
from fabric.context_managers import lcd


class Test(object):
    def __init__(self, func, deps=[], needs_rpython=True, needs_rubyspec=False):
        self.func = func
        self.deps = deps
        self.needs_rpython = needs_rpython
        self.needs_rubyspec = needs_rubyspec

    def install_deps(self):
        local("pip install --use-mirrors {}".format(" ".join(self.deps)))

    def download_rpython(self):
        local("wget https://bitbucket.org/pypy/pypy/get/default.tar.bz2 -O `pwd`/../pypy.tar.bz2")
        local("tar -xf `pwd`/../pypy.tar.bz2 -C `pwd`/../")
        [path_name] = glob.glob("../pypy-pypy*")
        path_name = os.path.abspath(path_name)
        with open("rpython_marker", "w") as f:
            f.write(path_name)

    def download_mspec(self):
        with lcd(".."):
            local("git clone --depth=100 --quiet https://github.com/rubyspec/mspec")

    def download_rubyspec(self):
        with lcd(".."):
            local("git clone --depth=100 --quiet https://github.com/rubyspec/rubyspec")

    def run_tests(self):
        env = {}
        if self.needs_rpython:
            with open("rpython_marker") as f:
                env["rpython_path"] = f.read()
        self.func(env)


@task
def install_requirements():
    t = TEST_TYPES[os.environ["TEST_TYPE"]]
    if t.deps:
        t.install_deps()
    if t.needs_rpython:
        t.download_rpython()
    if t.needs_rubyspec:
        t.download_mspec()
        t.download_rubyspec()


@task
def run_tests():
    t = TEST_TYPES[os.environ["TEST_TYPE"]]
    t.run_tests()


def run_own_tests(env):
    local("PYTHONPATH=$PYTHONPATH:{rpython_path} py.test".format(**env))


def run_rubyspec_untranslated(env):
    run_specs("bin/topaz_untranslated.py", prefix="PYTHONPATH=$PYTHONPATH:{rpython_path} ".format(**env))


def run_translate_tests(env):
    local("PYTHONPATH={rpython_path}:$PYTHONPATH python {rpython_path}/rpython/translator/goal/translate.py --batch -Ojit targettopaz.py".format(**env))
    run_specs("`pwd`/bin/topaz")
    local("PYTHONPATH={rpython_path}:$PYTHONPATH py.test --topaz=bin/topaz tests/jit/".format(**env))


def run_specs(binary, prefix=""):
    # TODO: this list is temporary until we have all the machinery necessary to
    # run the full rubyspec directory (including the tagging feature)
    rubyspec_tests = [
        "language/and_spec.rb",
        "language/array_spec.rb",
        "language/class_variable_spec.rb",
        "language/match_spec.rb",
        "language/metaclass_spec.rb",
        "language/module_spec.rb",
        "language/next_spec.rb",
        "language/not_spec.rb",
        "language/numbers_spec.rb",
        "language/order_spec.rb",
        "language/splat_spec.rb",
        "language/undef_spec.rb",
        "language/unless_spec.rb",
        "language/yield_spec.rb",

        "language/regexp/grouping_spec.rb",
        "language/regexp/repetition_spec.rb",

        "core/array/allocate_spec.rb",
        "core/array/array_spec.rb",
        "core/array/at_spec.rb",
        "core/array/empty_spec.rb",
        "core/array/frozen_spec.rb",
        "core/array/length_spec.rb",
        "core/array/size_spec.rb",

        "core/basicobject/ancestors_spec.rb",
        "core/basicobject/class_spec.rb",
        "core/basicobject/new_spec.rb",
        "core/basicobject/superclass_spec.rb",

        "core/class/superclass_spec.rb",

        "core/comparable/between_spec.rb",

        "core/exception/message_spec.rb",
        "core/exception/standard_error_spec.rb",

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

        "core/hash/empty_spec.rb",
        "core/hash/length_spec.rb",
        "core/hash/size_spec.rb",

        "core/nil/and_spec.rb",
        "core/nil/inspect_spec.rb",
        "core/nil/nil_spec.rb",
        "core/nil/or_spec.rb",
        "core/nil/to_a_spec.rb",
        "core/nil/to_i_spec.rb",
        "core/nil/to_s_spec.rb",
        "core/nil/xor_spec.rb",

        "core/object/clone_spec.rb",
        "core/object/dup_spec.rb",
        "core/object/match_spec.rb",

        "core/process/pid_spec.rb",

        "core/regexp/casefold_spec.rb",
        "core/regexp/source_spec.rb",

        "core/true/and_spec.rb",
        "core/true/inspect_spec.rb",
        "core/true/or_spec.rb",
        "core/true/to_s_spec.rb",
        "core/true/xor_spec.rb",
    ]
    local("{prefix}../mspec/bin/mspec -t {binary} --format=dotted {spec_files}".format(
        prefix=prefix,
        binary=binary,
        spec_files=" ".join(os.path.join("../rubyspec", p) for p in rubyspec_tests),
    ))


def run_docs_tests(env):
    local("sphinx-build -W -b html docs/ docs/_build/")

TEST_TYPES = {
    "own": Test(run_own_tests, deps=["pytest", "-r requirements.txt"]),
    "rubyspec_untranslated": Test(run_rubyspec_untranslated, deps=["-r requirements.txt"], needs_rubyspec=True),
    "translate": Test(run_translate_tests, deps=["-r requirements.txt"], needs_rubyspec=True),
    "docs": Test(run_docs_tests, deps=["sphinx"], needs_rpython=False),
}
