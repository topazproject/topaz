import os

from fabric.api import local
from fabric.context_managers import lcd


class BaseTest(object):
    def download_mspec(self):
        if not os.path.isdir("../mspec"):
            with lcd(".."):
                local("git clone --depth=100 --quiet https://github.com/rubyspec/mspec")

    def download_rubyspec(self):
        if not os.path.isdir("../rubyspec"):
            with lcd(".."):
                local("git clone --depth=100 --quiet https://github.com/rubyspec/rubyspec")
