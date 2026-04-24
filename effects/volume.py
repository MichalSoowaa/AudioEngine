from effects.registry import register_effect

@register_effect("volume")
def volume(audio, factor: float = 1.0):
    new_samples = []

    for sample in audio.samples:
        new_samples.append(int(sample * factor))

    return audio.__class__(new_samples, audio.sample_rate, audio.num_channels, audio.sample_width)