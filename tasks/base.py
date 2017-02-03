import os

from invoke import run


class BaseTest(object):
    def download_mspec(self):
        if not os.path.isdir("../mspec"):
            run("cd .. && git clone --depth=100 --quiet https://github.com/ruby/mspec")
            run("cd ../mspec && git checkout 4bcdee51406abc739ebe2a6be81ec5a93447125e")

    def download_rubyspec(self):
        if not os.path.isdir("../rubyspec"):
            run("cd .. && git clone --depth=100  --quiet https://github.com/ruby/spec")
            run("cd ../spec && git checkout bdfc985bb78015614292b281cf6d2d88d4685354")
