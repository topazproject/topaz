import sys

from rpython.rlib.unroll import unrolling_iterable


SEND_EFFECT = 0xFF
ARRAY_EFFECT = 0xFE
BLOCK_EFFECT = 0xFD
UNPACK_EFFECT = 0xFC

# Name, number of arguments, stack effect
BYTECODES = [
    ("LOAD_SELF", 0, +1),
    ("LOAD_SCOPE", 0, +1),
    ("LOAD_BLOCK", 0, +1),
    ("LOAD_CODE", 0, +1),
    ("LOAD_CONST", 1, +1),

    ("LOAD_DEREF", 1, +1),
    ("STORE_DEREF", 1, 0),
    ("LOAD_CLOSURE", 1, +1),

    ("LOAD_CONSTANT", 1, 0),
    ("STORE_CONSTANT", 1, 0),
    ("DEFINED_CONSTANT", 1, 0),

    ("LOAD_LOCAL_CONSTANT", 1, +1),
    ("DEFINED_LOCAL_CONSTANT", 1, 0),

    ("LOAD_INSTANCE_VAR", 1, 0),
    ("STORE_INSTANCE_VAR", 1, -1),
    ("DEFINED_INSTANCE_VAR", 1, 0),

    ("LOAD_CLASS_VAR", 1, 0),
    ("STORE_CLASS_VAR", 1, -1),
    ("DEFINED_CLASS_VAR", 1, 0),

    ("LOAD_GLOBAL", 1, +1),
    ("STORE_GLOBAL", 1, 0),
    ("DEFINED_GLOBAL", 1, +1),

    ("BUILD_ARRAY", 1, ARRAY_EFFECT),
    ("BUILD_ARRAY_SPLAT", 1, ARRAY_EFFECT),
    ("BUILD_STRING", 1, ARRAY_EFFECT),
    ("BUILD_HASH", 0, +1),
    ("BUILD_RANGE", 0, -1),
    ("BUILD_RANGE_EXCLUSIVE", 0, -1),
    ("BUILD_FUNCTION", 0, -1),
    ("BUILD_BLOCK", 1, BLOCK_EFFECT),
    ("BUILD_LAMBDA", 0, 0),
    ("BUILD_CLASS", 0, -2),
    ("BUILD_MODULE", 0, -1),
    ("BUILD_REGEXP", 0, -1),

    ("COERCE_ARRAY", 1, 0),
    ("COERCE_BLOCK", 0, 0),
    ("COERCE_STRING", 0, 0),
    ("UNPACK_SEQUENCE", 1, UNPACK_EFFECT),
    ("UNPACK_SEQUENCE_SPLAT", 2, UNPACK_EFFECT),

    ("DEFINE_FUNCTION", 0, -2),
    ("ATTACH_FUNCTION", 0, -2),
    ("EVALUATE_MODULE", 0, -1),
    ("LOAD_SINGLETON_CLASS", 0, 0),

    ("SEND", 2, SEND_EFFECT),
    ("SEND_BLOCK", 2, SEND_EFFECT),
    ("SEND_SPLAT", 2, SEND_EFFECT),
    ("SEND_BLOCK_SPLAT", 2, SEND_EFFECT),
    ("DEFINED_METHOD", 1, 0),

    ("SEND_SUPER_BLOCK", 2, SEND_EFFECT),
    ("SEND_SUPER_BLOCK_SPLAT", 2, SEND_EFFECT),
    ("DEFINED_SUPER", 1, 0),

    ("SETUP_LOOP", 1, 0),
    ("SETUP_EXCEPT", 1, 0),
    ("SETUP_FINALLY", 1, 0),
    ("END_FINALLY", 0, -2),
    ("POP_BLOCK", 0, 0),

    ("JUMP", 1, 0),
    ("JUMP_IF_TRUE", 1, -1),
    ("JUMP_IF_FALSE", 1, -1),

    ("DISCARD_TOP", 0, -1),
    ("DUP_TOP", 0, +1),
    ("DUP_TWO", 0, +2),
    ("ROT_TWO", 0, 0),
    ("ROT_THREE", 0, 0),

    ("YIELD", 1, ARRAY_EFFECT),
    ("YIELD_SPLAT", 1, SEND_EFFECT),
    ("DEFINED_YIELD", 0, +1),

    ("RETURN", 0, -1),
    ("RAISE_RETURN", 0, -1),
    ("CONTINUE_LOOP", 1, -1),
    ("BREAK_LOOP", 0, -1),
    ("RAISE_BREAK", 0, -1),
]

BYTECODE_NAMES = []
BYTECODE_NUM_ARGS = []
BYTECODE_STACK_EFFECT = []

module = sys.modules[__name__]
for i, (name, num_args, stack_effect) in enumerate(BYTECODES):
    setattr(module, name, i)
    BYTECODE_NAMES.append(name)
    BYTECODE_NUM_ARGS.append(num_args)
    BYTECODE_STACK_EFFECT.append(stack_effect)

UNROLLING_BYTECODES = unrolling_iterable(enumerate(BYTECODE_NAMES))
