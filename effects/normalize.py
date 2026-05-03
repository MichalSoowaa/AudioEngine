from dataclasses import dataclass

from core.audio import Audio
from core.enums import ProcessingMode
from core.preprocess import EffectContext
from effects.registry import register_effect

@dataclass
class NormalizeContext(EffectContext):
    factor: float = 1.0

def normalize_preprocess(audio, **kwargs):
    if not audio.samples:
        raise ValueError(f"This audio has no samples: {audio.samples}")

    if audio.sample_width not in (1, 2):
        raise ValueError(f"Invalid sample width: {audio.sample_width}")

    max_val = max(abs(s) for s in audio.samples)
    target = 32767

    return NormalizeContext(factor = target / max_val if max_val != 0 else 1)

@register_effect("normalize", mode=ProcessingMode.PARALLEL, preprocess=normalize_preprocess)
def normalize(audio: Audio, context: NormalizeContext=None):
    new_samples = [max(-32768, min(32767, int(s * context.factor))) for s in audio.samples]
    return Audio(new_samples, audio.sample_rate, audio.num_channels, audio.sample_width)