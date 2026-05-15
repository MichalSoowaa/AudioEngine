from dataclasses import dataclass
from core.audio import Audio
from core.enums import ProcessingMode
from core.preprocess import EffectContext
from effects.registry import register_effect
import numpy as np

@dataclass
class EqualizerContext(EffectContext):
    sample_rate: int = 44100
    frame_size: int = 2048
    hop_size: int = 512
    total_length: int = 0

    def reconstruct(self, frames):
        return overlap_add(frames, self.total_length, self.frame_size)

def equalizer_preprocess(audio: Audio, **kwargs):
    return EqualizerContext(sample_rate=audio.sample_rate, frame_size=2048, hop_size=512, total_length=len(audio.samples))

def apply_eq_to_frame(frame, gains, sample_rate, frame_size):
    window = np.hanning(len(frame))
    windowed = frame * window
    spectrum = np.fft.rfft(windowed, n=frame_size)
    freqs = np.fft.rfftfreq(frame_size, d=1 / sample_rate)
    gain_array = np.ones(len(spectrum))

    for low, high, gain in gains:
        mask = (freqs >= low) & (freqs < high)
        gain_array[mask] = gain

    spectrum *= gain_array
    return np.fft.irfft(spectrum, n=frame_size)

def overlap_add(frames, total_length, frame_size):
    output = np.zeros(total_length)
    norm = np.zeros(total_length)
    window = np.hanning(frame_size)

    for start, frame in frames:
        end = min(start + frame_size, total_length)
        length = end - start
        output[start:end] += frame[:length]
        norm[start:end] += window[:length]

    norm = np.where(norm < 1e-8, 1.0, norm)
    output /= norm
    return output

@register_effect("equalizer", mode=ProcessingMode.FRAMES, preprocess=equalizer_preprocess)
def equalizer(frames, context: EqualizerContext,
              sub_bass: float = 1.0,
              bass: float = 1.0,
              low_mid: float = 1.0,
              mid: float = 1.0,
              high_mid: float = 1.0,
              presence: float = 1.0,
              brilliance: float = 1.0):

    gains = [
        (20, 60, sub_bass),
        (60, 250, bass),
        (250, 500, low_mid),
        (500, 2000, mid),
        (2000, 4000, high_mid),
        (4000, 8000, presence),
        (8000, 20000, brilliance),
    ]

    processed = []

    for start, frame in frames:
        processed_frame = apply_eq_to_frame(frame, gains, context.sample_rate, frame_size=len(frame))
        processed.append((start, processed_frame))

    return processed