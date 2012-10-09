"""Filename globbing utility."""

import sys
import os
from rupypy.utils.re import re_rffi as re
from rupypy.utils import fnmatch


__all__ = ["glob", "iglob"]

# as os.path is mostly not RPython, we redefine some methods
# up here. We could push some of those implementations into 
# pypy.rlib.rpath to enhance pypy.

if os.name == "posix":
    
    def split(p):
        """Split a pathname.  Returns tuple "(head, tail)" where "tail" is
        everything after the final slash.  Either part may be empty."""
        i = p.rfind('/') + 1
        assert i >= 0
        head, tail = p[:i], p[i:]
        if head and head != '/'*len(head):
            head = head.rstrip('/')
        return head, tail
        
    def lexists(path):
        """Test whether a path exists.  Returns True for broken symbolic links"""
        try:
            os.lstat(path)
        except os.error:
            return False
        return True
        
elif os.name == "nt":
    
    lexists = os.path.lexists
    
    def splitdrive(p):
        """Split a pathname into drive and path specifiers. Returns a 2-tuple
    "(drive,path)";  either part may be empty"""
        if p[1:2] == ':':
            return p[0:2], p[2:]
        return '', p
    
    def split(p):
        """Split a pathname.

        Return tuple (head, tail) where tail is everything after the final slash.
        Either part may be empty."""

        d, p = splitdrive(p)
        # set i to index beyond p's last slash
        i = len(p)
        while i and p[i-1] not in '/\\':
            i = i - 1
        assert i >= 0
        head, tail = p[:i], p[i:]  # now tail has no slashes
        # remove trailing slashes from head, unless it's all slashes
        head2 = head
        while head2 and head2[-1] in '/\\':
            head2 = head2[:-1]
        head = head2 or head
        return d + head, tail
        
else:
    raise ImportError('Unsupported os: %s' % os.name)

def glob(pathname):
    """Return a list of paths matching a pathname pattern.

    The pattern may contain simple shell-style wildcards a la fnmatch.

    """
    return iglob(pathname)


def iglob(pathname):
    """Return an iterator which yields the paths matching a pathname pattern.

    The pattern may contain simple shell-style wildcards a la fnmatch.

    """
    if not has_magic(pathname):
        res = []
        if lexists(pathname):
            res.append(pathname)
        return res
    dirname, basename = split(pathname)
    if not dirname:
        return glob1(os.curdir, basename)
    if has_magic(dirname):
        dirs = []
        for each in iglob(dirname):
            dirs.append(each) 
    else:
        dirs = [dirname]
    if has_magic(basename):
        glob_in_dir = glob1
    else:
        glob_in_dir = glob0
    for dirname in dirs:
        res = []
        for name in glob0(dirname, basename):
            res.append(os.path.join(dirname, name))
            return res

# These 2 helper functions non-recursively glob inside a literal directory.
# They return a list of basenames. `glob1` accepts a pattern while `glob0`
# takes a literal basename (so it only has to check for its existence).

def not_hidden(x):
    return x[0] != '.'

def glob1(dirname, pattern):
    if not dirname:
        dirname = os.curdir
    if isinstance(pattern, unicode) and not isinstance(dirname, unicode):
        dirname = unicode(dirname, sys.getfilesystemencoding() or
                                   sys.getdefaultencoding())
    try:
        names = os.listdir(dirname)
    except os.error:
        return []
    if pattern[0] != '.':
        # RPython does not seem to like filter()
        filtered_names = []
        for name in names:
            if not_hidden(name):
               filtered_names.append(name) 
        names = filtered_names
    return fnmatch.filter(names, pattern)

def glob0(dirname, basename):
    if basename == '':
        # `os.path.split()` returns an empty basename for paths ending with a
        # directory separator.  'q*x/' should match only directories.
        if os.path.isdir(dirname):
            return [basename]
    else:
        if os.path.lexists(os.path.join(dirname, basename)):
            return [basename]
    return []

def has_magic(s):
    return re.compile('[\*\?\[]').search(s) is not None
