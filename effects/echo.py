from effects.registry import register_effect

@register_effect("echo")
def echo(audio, delay_ms: int = 300, decay: float = 0.5):
    delay_samples = int(audio.sample_rate * delay_ms / 1000)

    new_samples  = audio.samples.copy()

    for i in range(delay_samples, len(audio.samples)):
        new_samples[i] += int(decay * audio.samples[i - delay_samples])