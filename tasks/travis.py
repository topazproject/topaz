import glob
import os
import struct
import sys

import invoke

import requests

from .base import BaseTest


class Test(BaseTest):
    def __init__(self, func, deps=[], needs_rpython=True, needs_rubyspec=False,
                 create_build=False):
        super(Test, self).__init__()
        self.func = func
        self.deps = deps
        self.needs_rpython = needs_rpython
        self.needs_rubyspec = needs_rubyspec
        self.create_build = create_build

    def install_deps(self):
        invoke.run("pip install {}".format(" ".join(self.deps)))

    def download_rpython(self):
        invoke.run("wget https://bitbucket.org/pypy/pypy/get/default.tar.bz2 -O `pwd`/../pypy.tar.bz2 || wget https://bitbucket.org/pypy/pypy/get/default.tar.bz2 -O `pwd`/../pypy.tar.bz2")
        invoke.run("tar -xf `pwd`/../pypy.tar.bz2 -C `pwd`/../")
        [path_name] = glob.glob("../pypy-pypy*")
        path_name = os.path.abspath(path_name)
        with open("rpython_marker", "w") as f:
            f.write(path_name)

    def run_tests(self):
        env = {}
        if self.needs_rpython:
            with open("rpython_marker") as f:
                env["rpython_path"] = f.read()
        self.func(env)

    def upload_build(self):
        if (os.environ["TRAVIS_BRANCH"] == "master" and
            "BUILD_SECRET" in os.environ):

            width = struct.calcsize("P") * 8
            if "linux" in sys.platform:
                platform = "linux{}".format(width)
            elif "darwin" in sys.platform:
                platform = "osx{}".format(width)
            elif "win" in sys.platform:
                platform = "windows{}".format(width)
            else:
                raise ValueError("Don't recognize platform: {!r}".format(sys.platform))
            build_name = "topaz-{platform}-{sha1}.tar.bz2".format(platform=platform, sha1=os.environ["TRAVIS_COMMIT"])
            invoke.run("python topaz/tools/make_release.py {}".format(build_name))
            with open(build_name, "rb") as f:
                response = requests.post("http://www.topazruby.com/builds/create/", {
                    "build_secret": os.environ["BUILD_SECRET"],
                    "sha1": os.environ["TRAVIS_COMMIT"],
                    "platform": platform,
                    "success": "true",
                }, files={"build": (build_name, f)})
                response.raise_for_status()


@invoke.task
def install_requirements():
    t = TEST_TYPES[os.environ["TEST_TYPE"]]
    if t.deps:
        t.install_deps()
    if t.needs_rpython:
        t.download_rpython()
    if t.needs_rubyspec:
        t.download_mspec()
        t.download_rubyspec()


@invoke.task
def run_tests():
    t = TEST_TYPES[os.environ["TEST_TYPE"]]
    t.run_tests()


@invoke.task
def tag_specs(files=""):
    invoke.run("../mspec/bin/mspec tag -t {} -f spec --config=topaz.mspec {}".format("`pwd`/bin/topaz", files))


@invoke.task
def untag_specs(files=""):
    invoke.run("../mspec/bin/mspec tag --del fails -t {} -f spec --config=topaz.mspec {}".format("`pwd`/bin/topaz", files))


@invoke.task
def upload_build():
    t = TEST_TYPES[os.environ["TEST_TYPE"]]
    if t.create_build:
        t.upload_build()


def run_own_tests(env):
    invoke.run("PYTHONPATH=$PYTHONPATH:{rpython_path} py.test".format(**env))


def run_rubyspec_untranslated(env):
    run_specs("bin/topaz_untranslated.py", prefix="PYTHONPATH=$PYTHONPATH:{rpython_path} ".format(**env))


def run_translate_tests(env):
    invoke.run("PYTHONPATH={rpython_path}:$PYTHONPATH python {rpython_path}/rpython/bin/rpython --batch targettopaz.py".format(**env))
    run_specs("`pwd`/bin/topaz")


def run_translate_jit_tests(env):
    invoke.run("PYTHONPATH={rpython_path}:$PYTHONPATH python {rpython_path}/rpython/bin/rpython --batch -Ojit targettopaz.py".format(**env))
    run_specs("`pwd`/bin/topaz")
    invoke.run("PYTHONPATH={rpython_path}:$PYTHONPATH py.test --topaz=bin/topaz tests/jit/".format(**env))


def run_specs(binary, prefix=""):
    invoke.run("{prefix}../mspec/bin/mspec -G fails -t {binary} --format=dotted --config=topaz.mspec".format(
        prefix=prefix,
        binary=binary
    ))


def run_docs_tests(env):
    invoke.run("sphinx-build -W -b html docs/ docs/_build/")


def run_flake8_tests(env):
    # E122 continuation line missing indentation or outdented
    # E124 closing bracket does not match visual indentation
    # E125 continuation line does not distinguish itself from next logical line
    # E126 continuation line over-indented for hanging indent
    # E128 continuation line under-indented for visual indent
    # E501 line too long
    # F811 redefinition of unused
    invoke.run('flake8 . --ignore="E122,E124,E125,E126,E128,E501,F811"')


TEST_TYPES = {
    "own": Test(run_own_tests, deps=["-r requirements.txt"]),
    "rubyspec_untranslated": Test(run_rubyspec_untranslated, deps=["-r requirements.txt"], needs_rubyspec=True),
    "translate": Test(run_translate_tests, deps=["-r requirements.txt"], needs_rubyspec=True),
    "translate-jit": Test(run_translate_jit_tests, deps=["-r requirements.txt"], needs_rubyspec=True, create_build=True),
    "docs": Test(run_docs_tests, deps=["sphinx"], needs_rpython=False),
    "flake8": Test(run_flake8_tests, deps=["flake8"], needs_rpython=False),
}
