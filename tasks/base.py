import os

from invoke import run


class BaseTest(object):
    def download_mspec(self):
        if not os.path.isdir("../mspec"):
            run("cd .. && git clone --depth=100 --quiet https://github.com/ruby/mspec")
            run("cd ../mspec && git checkout b363f08c6ddfbda5cf868afe9c3cc10122a0b9ab")

    def download_rubyspec(self):
        if not os.path.isdir("../spec"):
            run("cd .. && git clone --depth=100  --quiet https://github.com/ruby/spec")
            run("cd ../spec && git checkout 6c578cd49cb59f858d2724a687c02000e9fdaae2")
