from core.audio import Audio
from core.enums import ProcessingMode
from core.preprocess import EffectContext
from effects.registry import register_effect

@register_effect("reverse", mode=ProcessingMode.NORMAL)
def reverse(audio: Audio, context: EffectContext=None):
    return Audio(
        audio.samples[::-1],
        audio.sample_rate,
        audio.num_channels,
        audio.sample_width
    )