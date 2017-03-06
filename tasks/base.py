import os

import invoke


invoke.run = os.system


class BaseTest(object):
    def download_mspec(self):
        if not os.path.isdir("../mspec"):
            invoke.run("cd .. && git clone --depth=100 --quiet https://github.com/ruby/mspec")

    def download_rubyspec(self):
        if not os.path.isdir("../rubyspec"):
            invoke.run("cd .. && git clone --depth=100  --quiet https://github.com/ruby/spec rubyspec")
