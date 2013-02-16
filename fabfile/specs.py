import os

from fabric.api import task, local
from fabric.context_managers import lcd


def download_mspec():
    with lcd(".."):
        if not os.path.isdir("mspec"):
            local("git clone --depth=100 --quiet https://github.com/rubyspec/mspec")


def download_rubyspec():
    with lcd(".."):
        if not os.path.isdir("rubyspec"):
            local("git clone --depth=100 --quiet https://github.com/rubyspec/rubyspec")


def mspec(options, files):
    local("../mspec/bin/mspec %s -t %s --config=topaz.mspec %s" % (options, "`pwd`/bin/topaz", files))


@task
def run(files="", options=""):
    """Run Rubyspecs. Optionally pass files and options arguments"""
    mspec("run -G fails %s" % options, files)


@task
def tag(files, options=""):
    """Tag failing Rubyspecs. You have to pass a files argument"""
    mspec("tag --add fails -G fails -f spec %s" % options, files)


@task
def untag(files, options=""):
    """Untag Rubyspecs that no longer fail. You have to pass a files argument"""
    mspec("tag --del fails -g fails -f spec %s" % options, files)
