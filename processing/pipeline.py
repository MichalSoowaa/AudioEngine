from effects.registry import get_effect
from processing.parallel import apply_effect_parallel

def apply_effect(audio, effect, parallel = False, **params):
    if parallel:
        return apply_effect_parallel(audio, effect, **params)

    effect = get_effect(effect)

    if not effect:
        raise ValueError(f"Effect '{effect}' not found")

    return effect(audio, **params)

def apply_chain(audio, chain, parallel = False):
    """
    chain = [
        ("volume", {"factor": 2.0}),
        ("echo", {"delay_ms": 200, "decay": 0.4})
    ]
    """

    result = audio

    for effect, params in chain:
        result = apply_effect(result, effect, parallel, **params)

    return result