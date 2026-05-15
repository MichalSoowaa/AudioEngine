class ProcessingStrategy:
    def make_tasks(self):
        pass

    def process(self):
        pass

    def merge(self):
        pass

    @staticmethod
    def apply(audio, effect_func, context, parallel, user_params):
        raise NotImplementedError()