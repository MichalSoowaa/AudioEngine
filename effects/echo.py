from dataclasses import dataclass
from core.audio import Audio, clamp
from core.enums import ProcessingMode
from core.preprocess import EffectContext
from effects.registry import register_effect

@dataclass
class EchoContext(EffectContext):
    pass
    #overlap: int = 0

# def compute_overlap(audio, delay_ms=300, **kwargs):
#     return EchoContext(overlap=int(audio.sample_rate * delay_ms / 1000))

@register_effect("echo", mode=ProcessingMode.NORMAL)
def echo(audio: Audio, context: EchoContext=None, delay_ms: int=300, decay: float=0.5):
    delay_samples = int(audio.sample_rate * delay_ms / 1000)

    new_samples  = audio.samples.copy()

    for i in range(delay_samples, len(audio.samples)):
        new_samples[i] = clamp(audio.samples[i] + int(decay * new_samples[i - delay_samples]))

    return Audio(new_samples, audio.sample_rate, audio.num_channels, audio.sample_width)