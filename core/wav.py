from core.audio import Audio
import wave
import numpy as np

SCALE = {
    1: 128.0,
    2: 32768.0,
    3: 8388608.0,
    4: 2147483648.0
}

def load_wav(path: str) -> Audio:
    with wave.open(path, 'rb') as w:
        num_channels = w.getnchannels()
        sample_width = w.getsampwidth()
        sample_rate = w.getframerate()
        num_frames = w.getnframes()

        raw_data = w.readframes(num_frames)

        if sample_width not in SCALE:
            raise ValueError(f"Unsupported sample format: {sample_width}")

        scale = SCALE[sample_width]

        if sample_width == 1:
            arr = np.frombuffer(raw_data, dtype=np.int8).astype(np.float32)
            # iterating bytes object yields ints directly in Python3
            samples = ((arr - scale) / scale).tolist()
        elif sample_width == 2:
            arr = np.frombuffer(raw_data, dtype='<i2').astype(np.float32)
            samples = (arr / scale).tolist()
        elif sample_width == 3:
            # numpy has no 24-bit type - unpack manually
            raw = np.frombuffer(raw_data, dtype=np.uint8).reshape(-1, 3)
            padded = np.zeros((len(raw), 4), dtype=np.uint8)
            padded[:, :3] = raw

            arr = (padded[:, 0].astype(np.int32) |
                   (padded[:, 1].astype(np.int32) << 8) |
                   (padded[:, 2].astype(np.int32) << 16))

            arr = arr.astype(np.int32)
            arr[arr >= 0x800000] -= 0x1000000
            samples = (arr.astype(np.float32) / 8388608.0).tolist()
        elif sample_width == 4:
            arr = np.frombuffer(raw_data, dtype='<i4').astype(np.float32)
            samples = (arr / scale).tolist()

        return Audio(samples, sample_rate, num_channels, sample_width)

def save_wav(path: str, audio: Audio):
    if audio.sample_width not in SCALE:
        raise ValueError(f"Unsupported sample format: {audio.sample_width}")

    scale = SCALE[audio.sample_width]

    with wave.open(path, 'wb') as w:
        w.setnchannels(audio.num_channels)
        w.setsampwidth(audio.sample_width)
        w.setframerate(audio.sample_rate)

        arr = np.array(audio.samples, dtype=np.float32)
        arr = np.clip(arr, -1.0, 1.0)

        if audio.sample_width == 1:
            converted = ((arr * (scale - 1)) + scale).astype(np.uint8)
            raw_data = converted.tobytes()
        elif audio.sample_width == 2:
            converted = (arr * (scale - 1)).astype('<i2')
            raw_data = converted.tobytes()
        elif audio.sample_width == 3:
            ints = (arr * (scale - 1)).astype(np.int32)
            raw_data = bytearray()

            for val in ints:
                raw_data += int(val).to_bytes(3, byteorder='little', signed=True)
        elif audio.sample_width == 4:
            converted = (arr * (scale - 1)).astype('<i4')
            raw_data = converted.tobytes()

        w.writeframes(raw_data)
