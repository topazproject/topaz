from tests.base import BaseTopazTest

class BaseFFITest(BaseTopazTest):
    def ask(self, space, question):
        w_answer = space.execute(question)
        return self.unwrap(space, w_answer)
