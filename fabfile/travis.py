import glob
import os

from fabric.api import task, local, prefix


@task
def download_pypy():
    local("wget https://bitbucket.org/pypy/pypy/get/default.tar.bz2 -O ../pypy.tar.bz2")
    local("tar -xf ../pypy.tar.bz2 ../")
    [path_name] = glob.glob("../pypy-pypy*")
    path_name = os.path.abspath(path_name)
    with open("pypy_marker", "w") as f:
        f.write(path_name)


@task
def run_tests():
    with open("pypy_marker") as f:
        path_name = f.read()
    with prefix("PYTHONPATH=%s:$PYTHONPATH" % path_name):
        local("py.test")
