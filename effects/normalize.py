from core.audio import Audio
from effects.registry import register_effect

def normalize_preprocess(audio, **kwargs):
    if not audio.samples:
        raise ValueError(f"This audio has no samples: {audio.samples}")

    if audio.sample_width not in (1, 2):
        raise ValueError(f"Invalid sample width: {audio.sample_width}")

    max_val = max(abs(s) for s in audio.samples)
    target = 32767

    return {"factor": target / max_val if max_val != 0 else 1}

@register_effect("normalize", mode="parallel", preprocess=normalize_preprocess)
def normalize(audio, factor=1.0):
    new_samples = [max(-32768, min(32767, int(s * factor))) for s in audio.samples]
    return Audio(new_samples, audio.sample_rate, audio.num_channels, audio.sample_width)