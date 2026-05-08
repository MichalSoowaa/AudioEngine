from core.audio import Audio, clamp
from core.preprocess import EffectContext
from effects.registry import register_effect
from core.enums import ProcessingMode

@register_effect("volume", mode=ProcessingMode.PARALLEL)
def volume(audio: Audio, context: EffectContext=None, factor: float = 1.0):
    new_samples = []

    for sample in audio.samples:
        new_samples.append(clamp(sample * factor))

    return Audio(new_samples, audio.sample_rate, audio.num_channels, audio.sample_width)