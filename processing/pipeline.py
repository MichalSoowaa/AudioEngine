from effects.registry import get_effect
from core.audio import Audio, split_channels, merge_channels
from processing.strategies import PROCESSING_STRATEGIES

def apply_effect(audio, effect, parallel=True, **user_params):
    effect_data = get_effect(effect)

    if not effect_data:
        raise ValueError(f"Effect '{effect}' not found")

    # if not parallel:
    #     func = effect_data["func"]
    #     preprocess = effect_data["preprocess"]
    #     effect_context = None
    #
    #     if preprocess:
    #         effect_context = preprocess(audio, **user_params)
    #
    #     return func(audio, effect_context, **user_params)

    channels = split_channels(audio)
    processed_channels = []

    for samples in channels:
        ch_audio = Audio(samples, audio.sample_rate, 1, audio.sample_width)
        processed = apply_effect_single_channel(ch_audio, effect_data, parallel, **user_params)
        processed_channels.append(processed.samples)

    merged = merge_channels(processed_channels)

    return Audio(merged, audio.sample_rate, audio.num_channels, audio.sample_width)

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

def apply_effect_single_channel(audio, effect_data, parallel, **user_params):
    mode = effect_data["mode"]
    func = effect_data["func"]
    preprocess = effect_data["preprocess"]

    context = None

    if preprocess:
        context = preprocess(audio, **user_params)

    strategy = PROCESSING_STRATEGIES[mode]

    return strategy.apply(audio, func, context, parallel, user_params)