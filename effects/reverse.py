from effects.registry import register_effect

@register_effect("reverse")
def reverse(audio):
    return audio.__class__(
        audio.samples[::-1],
        audio.sample_rate,
        audio.num_channels,
        audio.sample_width
    )