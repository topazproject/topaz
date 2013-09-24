from __future__ import absolute_import

from topaz.module import ModuleDef, ClassDef
from topaz.objects.objectobject import W_Object
from topaz.objects.exceptionobject import W_StandardError, new_exception_allocate
from topaz.modules.ffi.type import (POINTER, lltype_sizes, W_TypeObject,
                                    type_names, W_BuiltinType)
from topaz.modules.ffi.function import W_FunctionObject
from topaz.modules.ffi.variadic_invoker import W_VariadicInvokerObject
from topaz.modules.ffi.dynamic_library import W_DynamicLibraryObject
from topaz.modules.ffi.abstract_memory import W_AbstractMemoryObject
from topaz.modules.ffi.pointer import W_PointerObject
from topaz.modules.ffi.memory_pointer import W_MemoryPointerObject
from topaz.modules.ffi.data_converter import DataConverter

from rpython.rtyper.lltypesystem import rffi

class FFI(object):
    moduledef = ModuleDef("FFI")

    @moduledef.setup_module
    def setup_module(space, w_mod):
        # setup modules from other files
        w_type_class = space.getclassfor(W_TypeObject)
        space.set_const(w_mod, 'Type', w_type_class)
        space.set_const(w_type_class, 'Builtin', space.getclassfor(W_BuiltinType))
        space.set_const(w_mod, 'DynamicLibrary',
                        space.getclassfor(W_DynamicLibraryObject))
        space.set_const(w_mod, 'Function', space.getclassfor(W_FunctionObject))
        space.set_const(w_mod, 'VariadicInvoker',
                        space.getclassfor(W_VariadicInvokerObject))
        space.set_const(w_mod, 'AbstractMemory',
                        space.getclassfor(W_AbstractMemoryObject))
        space.set_const(w_mod, 'Pointer',
                        space.getclassfor(W_PointerObject))
        space.set_const(w_mod, 'MemoryPointer',
                        space.getclassfor(W_MemoryPointerObject))
        space.set_const(w_mod, 'DataConverter',
                        space.getmoduleobject(DataConverter.moduledef))

        w_native_type = space.newmodule('NativeType')
        # This assumes that FFI::Type and the type constants already exist
        for typename in type_names:
            w_Type = space.find_const(w_mod, 'Type')
            w_ffi_type = space.find_const(w_Type, typename)
            # setup type constants
            space.set_const(w_mod, 'TYPE_' + typename, w_ffi_type)
            # setup NativeType
            space.set_const(w_native_type, typename, w_ffi_type)
        space.set_const(w_mod, 'NativeType', w_native_type)

        # setup Platform
        w_platform = space.newmodule('Platform', None)
        name_postfix = '_SIZE'
        for name_prefix in ['INT8', 'INT16', 'INT32', 'INT64',
                            'LONG', 'FLOAT', 'DOUBLE']:
            w_type = space.find_const(w_mod, 'Type')
            w_tp = space.find_const(w_type, name_prefix)
            space.set_const(w_platform, name_prefix + name_postfix,
                            space.send(w_tp, 'size'))
        space.set_const(w_platform, 'ADDRESS_SIZE',
                        space.newint(
                            lltype_sizes[POINTER]))
        space.set_const(w_mod, 'Platform', w_platform)

        # setup StructLayout
        w_struct_layout = space.newclass('StructLayout', None)
        space.set_const(w_struct_layout, 'Field', space.w_nil)
        space.set_const(w_mod, 'StructLayout', w_struct_layout)

        # setup StructByReference
        w_struct_by_reference = space.newclass('StructByValue', None)
        space.set_const(w_mod, 'StructByReference', w_struct_by_reference)
