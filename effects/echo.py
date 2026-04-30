from core.audio import Audio
from effects.registry import register_effect

def compute_overlap(audio, delay_ms=300, **kwargs):
    return {"overlap": int(audio.sample_rate * delay_ms / 1000)}

@register_effect("echo", mode="overlap", overlap=0, preprocess=compute_overlap)
def echo(audio, delay_ms: int=300, decay: float=0.5):
    delay_samples = int(audio.sample_rate * delay_ms / 1000)

    new_samples  = audio.samples.copy()

    for i in range(delay_samples, len(audio.samples)):
        new_samples[i] += int(decay * audio.samples[i - delay_samples])
        new_samples[i] = max(-32768, min(32767, new_samples[i]))

    return Audio(new_samples, audio.sample_rate, audio.num_channels, audio.sample_width)