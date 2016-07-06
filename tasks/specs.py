import invoke

from .base import BaseTest


class Rubyspecs(BaseTest):
    def __init__(self, files, options, untranslated=False):
        super(Rubyspecs, self).__init__()
        self.exe = "`pwd`/bin/%s" % ("topaz_untranslated.py" if untranslated else "topaz")
        self.files = files
        self.options = options
        self.download_mspec()
        self.download_rubyspec()

    def mspec(self, args):
        invoke.run("../mspec/bin/mspec %s -t %s --config=topaz.mspec %s" % (args, self.exe, self.files), echo=True)

    def run(self):
        self.mspec("run -G fails %s" % self.options)

    def tag(self):
        self.mspec("tag --add fails -G fails -f spec %s" % self.options)

    def untag(self):
        self.mspec("tag --del fails -g fails -f spec %s" % self.options)


def generate_spectask(taskname):
    def spectask(ctx, files="", options="", untranslated=False):
        runner = Rubyspecs(files, options, untranslated=untranslated)
        getattr(runner, taskname)()
    spectask.__name__ = taskname
    return invoke.task(spectask)


run = generate_spectask("run")
tag = generate_spectask("tag")
untag = generate_spectask("untag")
