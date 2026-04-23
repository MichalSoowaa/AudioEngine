import wave
import struct
from core.audio import Audio

def load_wav(path: str) -> Audio:
    with wave.open(path, 'rb') as w:
        num_channels = w.getnchannels()
        sample_width = w.getsampwidth()
        sample_rate = w.getframerate()
        num_frames = w.getnframes()

        raw_data = w.readframes(num_frames)

        if sample_width == 1:
            fmt = f"{num_frames * num_channels}B"
        elif sample_width == 2:
            fmt = f"{num_frames * num_channels}h"
        else:
            raise ValueError(f"Unsupported sample format: {sample_width}")

        samples = list(struct.unpack(fmt, raw_data))

        return Audio(samples, sample_rate, num_channels, sample_width)

def save_wav(path: str, audio: Audio):
    with wave.open(path, 'wb') as w:
        w.setnchannels(audio.num_channels)
        w.setsampwidth(audio.sample_width)
        w.setframerate(audio.sample_rate)

        samples = audio.samples

        if audio.sample_width == 1:
            fmt = f"{len(samples)}B"
        elif audio.sample_width == 2:
            fmt = f"{len(samples)}h"
        else:
            raise ValueError("Unsupported sample format")

        raw_data = struct.pack(fmt, *samples)
        w.writeframes(raw_data)
