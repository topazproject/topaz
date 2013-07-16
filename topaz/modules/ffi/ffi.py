from __future__ import absolute_import

from topaz.module import ModuleDef, ClassDef
from topaz.objects.objectobject import W_Object
from topaz.objects.exceptionobject import W_StandardError, new_exception_allocate
from topaz.modules.ffi.type import (native_types, ffi_types,
                                    W_TypeObject)
from topaz.modules.ffi.function import W_FunctionObject
from topaz.modules.ffi.dynamic_library import W_DynamicLibraryObject
from topaz.modules.ffi.pointer import W_PointerObject
from topaz.modules.ffi.memory_pointer import W_MemoryPointerObject
from topaz.modules.ffi.buffer import W_BufferObject
from topaz.modules.ffi.data_converter import DataConverter

from rpython.rtyper.lltypesystem import rffi

class FFI(object):
    moduledef = ModuleDef("FFI")

    @moduledef.setup_module
    def setup_module(space, w_mod):
        # setup type constants
        for typename in ffi_types:
            w_new_type = W_TypeObject(space, typename)
            space.set_const(w_mod, 'TYPE_' + typename, w_new_type)

        # setup NativeType
        w_native_type = space.newmodule('NativeType')
        for typename in ffi_types:
            w_new_type = W_TypeObject(space, typename)
            space.set_const(w_native_type, typename, w_new_type)
        space.set_const(w_mod, 'NativeType', w_native_type)

        ## setup modules from other files
        space.set_const(w_mod, 'Type', space.getclassfor(W_TypeObject))
        space.set_const(w_mod, 'DynamicLibrary',
                        space.getclassfor(W_DynamicLibraryObject))
        space.set_const(w_mod, 'Function', space.getclassfor(W_FunctionObject))
        space.set_const(w_mod, 'Pointer',
                        space.getclassfor(W_PointerObject))
        space.set_const(w_mod, 'DataConverter',
                        space.getmoduleobject(DataConverter.moduledef))
        space.set_const(w_mod, 'Buffer', space.getclassfor(W_BufferObject))
        space.set_const(w_mod, 'MemoryPointer',
                        space.getclassfor(W_MemoryPointerObject))

        # setup Platform
        w_platform = space.newmodule('Platform', None)
        space.set_const(w_platform, 'INT8_SIZE',
                        space.newint(rffi.sizeof(rffi.CHAR)))
        space.set_const(w_platform, 'INT16_SIZE',
                        space.newint(rffi.sizeof(rffi.SHORT)))
        space.set_const(w_platform, 'INT32_SIZE',
                        space.newint(rffi.sizeof(rffi.INT)))
        space.set_const(w_platform, 'INT64_SIZE',
                        space.newint(rffi.sizeof(rffi.LONGLONG)))
        space.set_const(w_platform, 'LONG_SIZE',
                        space.newint(rffi.sizeof(rffi.LONG)))
        space.set_const(w_platform, 'FLOAT_SIZE',
                        space.newint(rffi.sizeof(rffi.FLOAT)))
        space.set_const(w_platform, 'DOUBLE_SIZE',
                        space.newint(rffi.sizeof(rffi.DOUBLE)))
        space.set_const(w_platform, 'ADDRESS_SIZE',
                        space.newint(rffi.sizeof(rffi.VOIDP)))
        space.set_const(w_mod, 'Platform', w_platform)

        # setup StructLayout
        w_struct_layout = space.newclass('StructLayout', None)
        space.set_const(w_struct_layout, 'Field', space.w_nil)
        space.set_const(w_mod, 'StructLayout', w_struct_layout)

        # setup StructByReference
        w_struct_by_reference = space.newclass('StructByValue', None)
        space.set_const(w_mod, 'StructByReference', w_struct_by_reference)
