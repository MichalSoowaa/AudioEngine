from core.audio import Audio
from core.preprocess import EffectContext
from effects.registry import register_effect

@register_effect("reverse")
def reverse(audio: Audio, context: EffectContext=None):
    return Audio(
        audio.samples[::-1],
        audio.sample_rate,
        audio.num_channels,
        audio.sample_width
    )