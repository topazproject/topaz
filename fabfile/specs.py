from fabric.api import task, local

from fabfile.travis import Test


class Rubyspecs(Test):
    def __init__(self, files, options, translated=True):
        self.exe = "`pwd`/bin/%s" % ("topaz" if translated else "topaz_untranslated.py")
        self.files = files
        self.options = options
        self.download_mspec()
        self.download_rubyspec()

    def mspec(self, args):
        local("../mspec/bin/mspec %s -t %s --config=topaz.mspec %s" % (args, self.exe, self.files))

    def run(self):
        self.mspec("run -G fails %s" % self.options)

    def tag(self):
        self.mspec("tag --add fails -G fails -f spec %s" % self.options)

    def untag(self):
        self.mspec("tag --del fails -g fails -f spec %s" % self.options)


def generate_spectask(taskname):
    def spectask(files="", options="", translated=True):
        runner = Rubyspecs(files, options, translated=(translated != "False"))
        getattr(runner, taskname)()
    spectask.__name__ = taskname
    globals()[taskname] = task(spectask)


for taskname in ["run", "tag", "untag"]:
    generate_spectask(taskname)
