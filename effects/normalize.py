from core.audio import Audio
from effects.registry import register_effect

@register_effect("normalize")
def normalize(audio):
    if not audio.samples:
        return audio

    # if audio.sample_width == 1:
    #     # 8-bit, center is 128
    #     centered = [s - 128 for s in audio.samples]
    #     max_val = max(abs(s) for s in centered)
    #
    #     if max_val == 0:
    #         return audio
    #
    #     target = 127
    #     factor = target / max_val
    #     new_samples = [int(s * factor) + 128 for s in centered]

    # elif audio.sample_width == 2:
    #     # 16-bit
    #     max_val = max(abs(s) for s in audio.samples)
    #
    #     if max_val == 0:
    #         return audio
    #
    #     target = 32767
    #     factor = target / max_val
    #     new_samples = [int(s * factor) for s in audio.samples]

    if audio.sample_width not in (8, 16):
        raise ValueError(f"Invalid sample width: {audio.sample_width}")

    max_val = max(abs(s) for s in audio.samples)

    if max_val == 0:
        return audio

    target = 32767
    factor = target / max_val
    new_samples = [int(s * factor) for s in audio.samples]

    return Audio(new_samples, audio.sample_rate, audio.num_channels, audio.sample_width)