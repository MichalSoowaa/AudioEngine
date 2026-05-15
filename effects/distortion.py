from core.audio import Audio, clamp
from core.enums import ProcessingMode
from core.preprocess import EffectContext
from effects.registry import register_effect

@register_effect("distortion", mode=ProcessingMode.PARALLEL)
def distortion(audio: Audio, context: EffectContext, drive: float=2.0, mix: float=1.0, output_gain: float=1.0, hard_clip: bool=False):
    new_samples = []

    for sample in audio.samples:
        driven = sample * drive

        if hard_clip:
            distorted = clamp(driven)
        else:
            raw = driven / (1.0 + abs(driven))
            max_possible = drive / (1.0 + drive)
            distorted = raw / max_possible

        output = (sample * (1.0 - mix) + distorted * mix) * output_gain
        new_samples.append(clamp(output))

    return Audio(new_samples, audio.sample_rate, audio.num_channels, audio.sample_width)
