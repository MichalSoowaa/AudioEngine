from dataclasses import dataclass

import numpy as np

from core.audio import Audio
from core.enums import ProcessingMode
from core.preprocess import EffectContext
from effects.registry import register_effect


@dataclass
class SpectralGateContext(EffectContext):
    sample_rate: int
    frame_size: int = 4096
    hop_size: int = 2048

    def reconstruct(self, frames):
        return overlap_add(frames, self.frame_size, self.hop_size)

def spectral_gate_preprocess(audio: Audio, **kwargs):
    return SpectralGateContext(sample_rate=audio.sample_rate, frame_size=2048, hop_size=512)

def overlap_add(frames, frame_size, hop_size):
    if not frames:
        return np.zeros(0)

    last_start, _ = frames[-1]
    output_length = last_start + frame_size
    output = np.zeros(output_length)
    norm = np.zeros(output_length)
    window = np.hanning(frame_size)

    for start, frame in frames:
        end = start + frame_size
        output[start:end] += window * frame
        norm[start:end] += window ** 2

    norm = np.where(norm < 1e-8, 1.0, norm)

    return output / norm

@register_effect("spectral_gate", mode=ProcessingMode.FRAMES, preprocess=spectral_gate_preprocess)
def spectral_gate(frames, context: SpectralGateContext, threshold: float=0.02, reduction: float=0.05):
    processed = []
    window = np.hanning(context.frame_size)

    for start, frame in frames:
        padded = np.zeros(context.frame_size)
        padded[:len(frame)] = frame
        windowed = padded * window
        spectrum = np.fft.rfft(windowed)
        magnitude = np.abs(spectrum)
        phase = np.angle(spectrum)
        mask = magnitude >= threshold
        gated_magnitude = np.where(mask, magnitude, magnitude * reduction)
        reconstructed = (gated_magnitude * np.exp(1j * phase))
        output = np.fft.irfft(reconstructed, n=context.frame_size)
        output *= window
        processed.append((start, output))

    return processed
