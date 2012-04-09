import sys


SEND_EFFECT = 0xFF

# Name, number of arguments, stack effect
BYTECODES = [
    ("LOAD_CONST", 1, +1),

    ("SEND", 2, SEND_EFFECT),

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
