
""" Find the initial path for library. Note that is very stripped down logic
from PyPy, where there is link recognition and whatnot. Ideally we would need
all of it
"""

import os, stat
from rpython.rlib import rpath

def checkdir(path):
    try:
        st = os.stat(path)
        if not stat.S_ISDIR(st[0]):
            return False
    except OSError:
        return False
    return True

def find(executable):
    path = rpath.rabspath(executable)
    while path:
        prev_path = path
        path = rpath.rabspath(os.path.join(path, os.path.pardir))
        if path == prev_path:
            return ''
        lib_path = os.path.join(path, 'lib-ruby')
        if checkdir(lib_path):
            return lib_path
    return ''
