from dataclasses import dataclass

import numpy as np

from core.audio import Audio
from core.enums import ProcessingMode
from core.preprocess import EffectContext
from effects.registry import register_effect


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

@dataclass
class SpectralBlurContext(EffectContext):
    sample_rate: int
    frame_size: int
    hop_size: int

    def reconstruct(self, frames):
        return overlap_add(frames, self.frame_size, self.hop_size)

def spectral_blur_preprocess(audio: Audio, **kwargs):
    return SpectralBlurContext(sample_rate=audio.sample_rate, frame_size=2048, hop_size=512)

def blur_spectrum(magnitude, blue_amount):
    kernel_size = max(1, int(blue_amount))

    if kernel_size <= 1:
        return magnitude

    kernel = np.ones(kernel_size) / kernel_size

    return np.convolve(magnitude, kernel, mode="same")

@register_effect("spectral_blur", mode=ProcessingMode.FRAMES, preprocess=spectral_blur_preprocess)
def spectral_blur(frames, context: SpectralBlurContext, blur_amount: int=8, mix: float=1.0):
    processed = []
    window = np.hanning(context.frame_size)

    for start, frame in frames:
        spectrum = np.fft.rfft(frame * window)
        magnitude = np.abs(spectrum)
        phase = np.angle(spectrum)
        blurred = blur_spectrum(magnitude, blur_amount)
        final_magnitude = (magnitude * (1.0 - mix) + blurred * mix)
        reconstructed = (final_magnitude * np.exp(1j * phase))
        output = np.fft.irfft(reconstructed, n=context.frame_size)

        processed.append((start, output))

    return processed