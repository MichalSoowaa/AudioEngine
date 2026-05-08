from dataclasses import dataclass

from core.audio import Audio, clamp
from core.enums import ProcessingMode
from core.preprocess import EffectContext
from effects.registry import register_effect

@dataclass
class NormalizeContext(EffectContext):
    factor: float = 1.0

def normalize_preprocess(audio, **kwargs):
    if not audio.samples:
        raise ValueError(f"This audio has no samples: {audio.samples}")

    max_val = max(abs(s) for s in audio.samples)
    target = 1.0

    return NormalizeContext(factor = target / max_val if max_val != 0 else 1)

@register_effect("normalize", mode=ProcessingMode.PARALLEL, preprocess=normalize_preprocess)
def normalize(audio: Audio, context: NormalizeContext=None):
    new_samples = [clamp(s * context.factor) for s in audio.samples]

    return Audio(new_samples, audio.sample_rate, audio.num_channels, audio.sample_width)