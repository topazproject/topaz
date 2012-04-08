from rupypy.parser import Transformer, _parse


class ObjectSpace(object):
    def __init__(self):
        self.transformer = Transformer()

    def parse(self, source):
        return self.transformer.visit_main(_parse(source + "\n"))