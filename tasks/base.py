import os

from invoke import run


class BaseTest(object):
    def download_mspec(self):
        if not os.path.isdir("../mspec"):
            run("cd .. && git clone --depth=100 --quiet https://github.com/ruby/mspec")
            run("cd ../mspec && git checkout v1.8.0")

    def download_rubyspec(self):
        if not os.path.isdir("../rubyspec"):
            run("cd .. && git clone --depth=100  --quiet https://github.com/ruby/rubyspec")
            run("cd ../rubyspec && git checkout c9cc7ae354cb5eb284be7591945e6ecfe4872d8d")
