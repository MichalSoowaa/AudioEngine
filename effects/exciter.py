import numpy as np

from core.audio import Audio
from core.enums import ProcessingMode
from core.preprocess import EffectContext
from effects.registry import register_effect

def highpass(signal, cutoff, sample_rate):
    rc = 1.0 / (2 * np.pi * cutoff)
    dt = 1.0 / sample_rate
    alpha = rc / (rc + dt)
    output = np.zeros_like(signal)

    prev_y = 0.0
    prev_x = signal[0]

    for i in range(1, len(signal)):
        output[i] = alpha * (prev_y + signal[i] - prev_x)

        prev_y = output[i]
        prev_x = signal[i]

    return output

@register_effect("exciter", mode=ProcessingMode.PARALLEL)
def exciter(audio: Audio, context: EffectContext=None, cutoff: float=4000.0, drive: float=3.0, mix: float=0.3):
    x = np.array(audio.samples, dtype=np.float32)

    highs = highpass(x, cutoff, audio.sample_rate)
    harmonics = np.tanh(highs * drive)
    output = (x * (1.0 - mix) + (x + harmonics) * mix)

    return Audio(np.clip(output, -1.0, 1.0).tolist(), audio.sample_rate, audio.num_channels, audio.sample_width)