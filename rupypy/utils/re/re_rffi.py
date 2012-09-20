import os
import sys
from pypy.rpython.tool import rffi_platform
from pypy.rpython.lltypesystem.rffi import *
from pypy.rpython.lltypesystem.lltype import *
from pypy.translator.tool.cbuild import ExternalCompilationInfo

E = 2
I = 4
M = 8
N = 16
F = 32
    
def compile(regex, option_flags=0):
    return Regexp(regex, option_flags)

class Regexp(object):
    
    def __init__(self, pattern, flags):
        self.pattern = pattern
        self.flags = flags
        
        # populate information within the corresponding C-struct
        self.re_data = malloc(CConfig.re_data_ptr.TO, flavor='raw', zero=True)
        self.re_data.c_pattern = str2charp(self.pattern)
        self.re_data.c_flags = cast(INT, self.flags)
        help_compile(self.re_data)    
        self.groups = int(self.re_data.c_num_regs) - 1
        
    def search(self, string):
        # TODO: preserve unicode strings
        self.re_data.c_str = str2charp(string)
        if help_search(self.re_data):
            self.groups = int(self.re_data.c_num_regs) - 1
            return Match(self.re_data, string)
        else:
            return None
            
    def encoding(self):
        return charp2str(help_get_encoding(self.re_data))

class Match(object):
    
    def __init__(self, re_data, string):
        self.matches = []
        self.string = string
        for i in range(re_data.c_num_regs):
            beg, end = int(re_data.c_beg[i]), int(re_data.c_end[i])
            if(beg >= 0 and end >= 0):
                self.matches.append(("%s:"%i, 
                                     self.string[beg:end]))
        self.re_data = re_data
        print self.matches
        
    def group(self, index):
        return self.matches[index][1]
    
    def start(self):
        start = int(self.re_data.c_beg[0])
        if start >= 0:
            return start
        else:
            return 0
        
    def end(self):
        end = int(self.re_data.c_end[0])
        if end >= 0:
            return end
        else:
            return 0

######################
# RFFI-related stuff #
######################

# TODO: This initialization only works if we initiate the build within the root
#       directory of the rupypy-project. Change that.

class CConfig:
    includes = ["oniguruma.h", "rffi_helper.h"]

    onig_lib_path = os.getcwd() + "/rupypy/utils/re/onig/.libs"
    onig_path = os.getcwd() + "/rupypy/utils/re/onig" 

    if not os.path.exists(onig_lib_path):
    	#trigger a build of the oniguruma lib
    	old_dir = os.getcwd()
    	os.chdir(onig_path)
    	os.system("/bin/bash ./configure")
    	os.system("make")
    	os.chdir(old_dir)

    eci = ExternalCompilationInfo(
            includes=includes,
            include_dirs=[onig_path,
		 	  os.getcwd() + "/rupypy/utils/re"],
            libraries=["onig"],
	    library_dirs=[onig_lib_path],
            separate_module_files=["rupypy/utils/re/rffi_helper.c"]
    )

    regex_t_ptr = COpaquePtr("regex_t", compilation_info=eci) 
    onig_error_info_ptr = COpaquePtr("OnigErrorInfo", compilation_info=eci)
    onig_region_ptr = COpaquePtr("OnigRegion", compilation_info=eci)

    INTP = lltype.Ptr(lltype.Array(INT, hints={'nolength': True}))

    re_data_ptr = CStructPtr("re_data", ('r', INT), ('pattern', CCHARP),
                                    ('str', CCHARP), ('flags', INT),
                                    ('num_regs', INT), ('beg', INTP),
                                    ('end', INTP), ('reg', regex_t_ptr),
                                    ('einfo', onig_error_info_ptr),
                                    ('region', onig_region_ptr))
    if os.name == "nt":
        calling_conv = "win"
    else:
        calling_conv = "c"                                    
    
help_compile = llexternal(
    "compile",
    [CConfig.re_data_ptr],
    INT,
    compilation_info=CConfig.eci,
    calling_conv=CConfig.calling_conv
)
                                           
help_search = llexternal(
    "search",
    [CConfig.re_data_ptr],
    INT,
    compilation_info=CConfig.eci,
    calling_conv=CConfig.calling_conv
)                                               

help_cleanup = llexternal(
    "cleanup",
    [CConfig.re_data_ptr],
    INT,
    compilation_info=CConfig.eci,
    calling_conv=CConfig.calling_conv
)

help_get_encoding = llexternal(
    "get_encoding",
    [CConfig.re_data_ptr],
    CCHARP,
    compilation_info=CConfig.eci,
    calling_conv=CConfig.calling_conv
)
