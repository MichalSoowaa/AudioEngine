from core.audio import Audio
from effects.registry import register_effect

@register_effect("volume", mode="parallel")
def volume(audio, factor: float = 1.0):
    new_samples = []

    for sample in audio.samples:
        new_samples.append(int(sample * factor))

    return Audio(new_samples, audio.sample_rate, audio.num_channels, audio.sample_width)