from processing.strategies.base import ProcessingStrategy

class NormalStrategy(ProcessingStrategy):
    @staticmethod
    def apply(audio, effect_func, context, parallel, user_params):
        return effect_func(audio, context, **user_params)