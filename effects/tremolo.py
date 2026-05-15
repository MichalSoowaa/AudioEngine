from core.audio import Audio, clamp
from core.enums import ProcessingMode
from core.preprocess import EffectContext
from effects.registry import register_effect
import math

@register_effect("tremolo", mode=ProcessingMode.PARALLEL)
def tremolo(
    audio: Audio, context: EffectContext=None, frequency: float=5.0, depth: float=0.5, phase: float=0.0
) -> Audio:
    new_samples = []

    for i, sample in enumerate(audio.samples):
        # convert interleaved sample index to frame index
        frame = i // audio.num_channels

        # time in seconds
        t = frame / audio.sample_rate

        # low-frequency oscillator (LFO)
        lfo = (math.sin(2.0 * math.pi * frequency * t + phase) + 1.0) / 2.0

        # modulation amount
        modulation = 1.0 + depth * (lfo - 0.5)

        output = sample * modulation
        new_samples.append(clamp(output))

    return Audio(new_samples, audio.sample_rate, audio.num_channels, audio.sample_width)