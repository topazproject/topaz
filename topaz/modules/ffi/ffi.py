from __future__ import absolute_import

from topaz.module import ModuleDef, ClassDef
from topaz.objects.objectobject import W_Object
from topaz.objects.exceptionobject import W_StandardError, new_exception_allocate
from topaz.modules.ffi.type import W_TypeObject
from topaz.modules.ffi.dynamic_library import W_DynamicLibraryObject
from topaz.modules.ffi.pointer import W_PointerObject
from topaz.modules.ffi.data_converter import DataConverter

from rpython.rtyper.lltypesystem import rffi

class FFI(object):
    moduledef = ModuleDef("FFI")

    sizes = {'INT8': rffi.sizeof(rffi.CHAR),
             'INT16': rffi.sizeof(rffi.SHORT),
             'INT32': rffi.sizeof(rffi.INT),
             'INT64': rffi.sizeof(rffi.LONGLONG),
             'LONG': rffi.sizeof(rffi.LONG),
             'FLOAT': rffi.sizeof(rffi.FLOAT),
             'DOUBLE': rffi.sizeof(rffi.DOUBLE),
             'ADDRESS': rffi.sizeof(rffi.VOIDP)}

    @moduledef.setup_module
    def setup_module(space, w_mod):
        # setup type constants
        space.set_const(w_mod, 'TypeDefs', space.newhash())
        space.set_const(w_mod, 'Types', space.newhash())
        for typename in W_TypeObject.basics:
            space.set_const(w_mod, 'TYPE_' + typename, space.w_nil)

        # setup NativeType
        w_native_type = space.newmodule('NativeType')
        for typename in W_TypeObject.basics:
            space.set_const(w_native_type, typename, space.w_nil)
        space.set_const(w_mod, 'NativeType', w_native_type)

        space.set_const(w_mod, 'Type', space.getclassfor(W_TypeObject))

        space.set_const(w_mod, 'DataConverter',
                        space.getmoduleobject(DataConverter.moduledef))

        space.set_const(w_mod, 'DynamicLibrary',
                        space.getclassfor(W_DynamicLibraryObject))

        space.set_const(w_mod, 'Pointer',
                        space.getclassfor(W_PointerObject))

        # setup Platform
        w_platform = space.newmodule('Platform', None)
        for name in FFI.sizes:
            space.set_const(w_platform, name + '_SIZE',
                            space.newint(FFI.sizes[name]))
        space.set_const(w_mod, 'Platform', w_platform)

        # setup StructLayout
        w_struct_layout = space.newclass('StructLayout', None)
        space.set_const(w_struct_layout, 'Field', space.w_nil)
        space.set_const(w_mod, 'StructLayout', w_struct_layout)

        # setup StructByReference
        w_struct_by_reference = space.newclass('StructByValue', None)
        space.set_const(w_mod, 'StructByReference', w_struct_by_reference)
