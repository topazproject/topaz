import invoke
import os


class Rubyspecs:
    def __init__(self, files, options, untranslated=False):
        self.exe = "`pwd`/bin/%s" % (
            "topaz_untranslated.py" if untranslated else "topaz")
        self.files = files
        self.options = options

    def mspec(self, args):
        invoke.run(
            "spec/mspec/bin/mspec %s -t %s --config=topaz.mspec %s" % (
                args, self.exe, self.files), echo=True, warn=True)

    def run(self):
        self.mspec("run -G fails %s" % self.options)

    def tag(self):
        self.mspec("tag --add fails -G fails -f spec %s" % self.options)

    def untag(self):
        self.mspec("tag --del fails -g fails -f spec %s" % self.options)

    def retag(self):
        assert len(self.files) == 0, "retag task mustn't get a file list"
        for d in ["core", "command_line", "language", "library"]:
            for dirname, subdirlist, files in os.walk(
                    "spec/rubyspec/%s/" % d):
                for f in files:
                    if f.endswith("_spec.rb"):
                        self.files = dirname
                        self.untag()
                        self.tag()
                        break


def generate_spectask(taskname):
    def spectask(ctx, files="", options="", untranslated=False):
        runner = Rubyspecs(files, options, untranslated=untranslated)
        getattr(runner, taskname)()
    spectask.__name__ = taskname
    return invoke.task(spectask)


run = generate_spectask("run")
tag = generate_spectask("tag")
untag = generate_spectask("untag")
retag = generate_spectask("retag")
