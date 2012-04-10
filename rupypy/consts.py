import sys

from pypy.rlib.unroll import unrolling_iterable


SEND_EFFECT = 0xFF

# Name, number of arguments, stack effect
BYTECODES = [
    ("LOAD_SELF", 0, +1),
    ("LOAD_CONST", 1, +1),

    ("LOAD_LOCAL", 1, +1),
    ("STORE_LOCAL", 1, 0),

    ("SEND", 2, SEND_EFFECT),

    ("JUMP", 1, 0),
    ("JUMP_IF_FALSE", 1, -1),

    ("DISCARD_TOP", 0, -1),

    ("RETURN", 0, -1),
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