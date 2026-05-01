from effects.registry import get_effect
from processing.parallel import apply_effect_parallel

def apply_effect(audio, effect, parallel=True, **user_params):
    effect_data = get_effect(effect)

    if not effect_data:
        raise ValueError(f"Effect '{effect}' not found")

    if not parallel:
        func = effect_data["func"]
        preprocess = effect_data["preprocess"]
        effect_context = None

        if preprocess:
            effect_context = preprocess(audio, **user_params)

        return func(audio, effect_context, **user_params)

    return apply_effect_parallel(audio, effect_data, **user_params)

def apply_chain(audio, chain, parallel=True):
    """
    chain = [
        ("volume", {"factor": 2.0}),
        ("echo", {"delay_ms": 200, "decay": 0.4})
    ]
    """

    result = audio

    for effect, user_params in chain:
        result = apply_effect(result, effect, parallel, **user_params)

    return result