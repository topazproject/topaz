import os

from invoke import run


class BaseTest(object):
    def download_mspec(self):
        if not os.path.isdir("../mspec"):
            run("cd .. && git clone --depth=100 --quiet https://github.com/ruby/mspec")
            run("cd ../mspec && git checkout v1.6.0")

    def download_rubyspec(self):
        if not os.path.isdir("../rubyspec"):
            run("cd .. && git clone --depth=100  --quiet https://github.com/ruby/spec")
            run("mv spec rubyspec")
