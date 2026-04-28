from effects.registry import get_effect

def apply_effect(audio, effect, **params):
    effect = get_effect(effect)

    if not effect:
        raise ValueError(f"Effect '{effect}' not found")

    return effect(audio, **params)

def apply_chain(audio, chain):
    """
    chain = [
        ("volume", {"factor": 2.0}),
        ("echo", {"delay_ms": 200, "decay": 0.4})
    ]
    """

    result = audio

    for effect, params in chain:
        result = apply_effect(result, effect, **params)

    return result